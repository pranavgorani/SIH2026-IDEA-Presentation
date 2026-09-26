import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import hashlib
from backend.app.models.database import (
    get_db, Case, Document, OCRResult, ValidationResult, TamperResult,
    FaceVerificationResult, RecordVerificationResult, RiskAssessment,
    DocumentCheck, Report, generate_uuid, utc_now
)
from backend.app.models.schemas import (
    CaseDetailResponse, CaseResponse, ExtractedFields,
    OCRResultResponse, RiskAssessmentResponse, ValidationSummary,
    TamperResultResponse, FaceVerificationResponse, RecordVerificationResponse
)
from backend.app.services.storage_service import storage_service
from backend.app.services.image_quality import image_quality_service
from backend.app.services.document_classifier import document_classifier
from backend.app.services.ocr_service import ocr_service
from backend.app.services.validation_service import validation_service
from backend.app.services.tamper_detection import tamper_detection_service
from backend.app.services.face_verification import face_verification_service
from backend.app.services.record_verification import record_verification_service
from backend.app.services.risk_engine import risk_engine
from backend.app.services.explainability import explainability_service
from backend.app.services.audit_service import audit_service
from backend.app.services.document_check_engine import document_check_engine
from backend.app.services.report_pdf_service import report_pdf_service
from backend.app.services.report_export_service import ReportExportService
from backend.app.core.security import get_current_user_optional
from backend.app.providers import get_ai_provider

logger = logging.getLogger("trustid.screening")

router = APIRouter(prefix="/screen", tags=["Document Screening Pipeline"])

@router.post("", summary="Upload document and execute full AI screening pipeline")
async def run_screening_pipeline(
    file: Optional[UploadFile] = File(None, description="Front image of identity credential"),
    primary_document: Optional[UploadFile] = File(None, description="Alternative key for front image of identity credential"),
    back_file: Optional[UploadFile] = File(None, description="Optional back side image"),
    live_person_file: Optional[UploadFile] = File(None, description="Optional live portrait of individual"),
    document_type_hint: Optional[str] = Form("AUTO_DETECT"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Executes the 10-stage TRUST-ID screening workflow with stage tracking:
    UPLOAD -> IMAGE_QUALITY -> DOCUMENT_CLASSIFICATION -> OCR -> FIELD_VALIDATION ->
    VISUAL_FORENSICS -> FACE_VERIFICATION -> RECORD_VERIFICATION -> RISK_ASSESSMENT ->
    EXPLANATION -> DATABASE_SAVE -> COMPLETED
    """
    case_id = generate_uuid()
    case_number = f"CASE-{utc_now().strftime('%Y%m%d')}-{case_id[:6].upper()}"
    current_stage = "UPLOAD"
    pipeline_stages: List[Dict[str, Any]] = []

    def log_stage_completion(stage_name: str, details: Optional[Dict[str, Any]] = None):
        pipeline_stages.append({
            "stage": stage_name,
            "status": "COMPLETED",
            "details": details or {}
        })

    def make_error_response(stage: str, code: str, message: str, recoverable: bool = True, http_status: int = 400):
        logger.error(f"SCREENING_ERROR: case_id={case_id} stage={stage} code={code} message={message}")
        pipeline_stages.append({
            "stage": stage,
            "status": "FAILED",
            "code": code,
            "message": message
        })
        return JSONResponse(
            status_code=http_status,
            content={
                "success": False,
                "case_id": case_id,
                "stage": stage,
                "code": code,
                "message": message,
                "recoverable": recoverable,
                "error": {
                    "code": code,
                    "message": message,
                    "stage": stage
                },
                "pipeline": pipeline_stages
            }
        )

    logger.info(f"SCREENING_START: case_id={case_id} hint={document_type_hint}")

    # =========================================================================
    # STAGE 1: UPLOAD & NORMALIZATION
    # =========================================================================
    current_stage = "UPLOAD"
    try:
        primary_file = file or primary_document
        if not primary_file:
            return make_error_response("UPLOAD", "MISSING_FILE", "Front image of credential was not provided.", True, 400)

        front_bytes = await primary_file.read()
        if not front_bytes:
            return make_error_response("UPLOAD", "EMPTY_FILE", "Uploaded document file is empty.")

        front_path, f_hash, f_size, f_w, f_h = storage_service.save_upload(
            case_id, primary_file.filename or "front.png", front_bytes
        )

        live_path = None
        if live_person_file:
            live_bytes = await live_person_file.read()
            if live_bytes:
                live_path, l_hash, l_size, l_w, l_h = storage_service.save_upload(
                    case_id, "live_selfie.png", live_bytes
                )

        log_stage_completion("UPLOAD", {"filename": primary_file.filename, "size_bytes": f_size, "dimensions": f"{f_w}x{f_h}"})
    except ValueError as ve:
        err_msg = str(ve)
        if "PDF processing" in err_msg:
            return make_error_response("UPLOAD", "PDF_UNSUPPORTED", "PDF processing is not enabled in this deployment.", recoverable=False)
        return make_error_response("UPLOAD", "IMAGE_NORMALIZATION_FAILED", err_msg)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return make_error_response("UPLOAD", "STORAGE_ERROR", "Failed to securely save uploaded document.")

    # =========================================================================
    # STAGE 2: IMAGE QUALITY
    # =========================================================================
    current_stage = "IMAGE_QUALITY"
    try:
        quality_res = image_quality_service.analyze(front_path)
        logger.info(f"IMAGE_VALIDATED: score={quality_res.quality_score} acceptable={quality_res.is_acceptable}")
        log_stage_completion("IMAGE_QUALITY", {"score": quality_res.quality_score, "is_acceptable": quality_res.is_acceptable})
    except Exception as e:
        logger.warning(f"Image quality assessment error: {e}")
        from backend.app.models.schemas import ImageQualityResult
        quality_res = ImageQualityResult(
            quality_score=60.0,
            issues=["analysis_partial"],
            is_acceptable=True,
            recommendation="Quality check degraded; proceeding with screening."
        )
        log_stage_completion("IMAGE_QUALITY", {"score": 60.0, "status": "DEGRADED"})

    # =========================================================================
    # STAGE 3: OCR EXTRACTION
    # =========================================================================
    current_stage = "OCR"
    logger.info("OCR_START")
    try:
        ocr_raw_res = ocr_service.process_document(front_path)
        logger.info(f"OCR_COMPLETE: confidence={ocr_raw_res.get('confidence', 0)} engine={ocr_raw_res.get('engine_used')}")
        log_stage_completion("OCR", {
            "confidence": ocr_raw_res.get("confidence", 0.0),
            "status": ocr_raw_res.get("status", "OK"),
            "engine": ocr_raw_res.get("engine_used", "Local OCR")
        })
    except Exception as e:
        logger.error(f"OCR failure: {e}")
        # Multi-layer fallback guarantees OCR object even on degraded state
        ocr_raw_res = {
            "raw_text": "",
            "fields": ExtractedFields(),
            "mrz": None,
            "confidence": 0.35,
            "bounding_boxes": [],
            "engine_used": "Emergency Fallback",
            "status": "LOW_CONFIDENCE",
            "ocr_status": "LOW_CONFIDENCE"
        }
        log_stage_completion("OCR", {"status": "LOW_CONFIDENCE", "confidence": 0.35})

    has_mrz = ocr_raw_res.get("mrz") is not None and getattr(ocr_raw_res["mrz"], "valid", False)

    # =========================================================================
    # STAGE 4: DOCUMENT CLASSIFICATION
    # =========================================================================
    current_stage = "DOCUMENT_CLASSIFICATION"
    try:
        if document_type_hint == "AUTO_DETECT" or not document_type_hint:
            class_res = document_classifier.classify_document(
                text=ocr_raw_res["raw_text"],
                width=f_w,
                height=f_h,
                has_mrz=has_mrz
            )
            detected_doc_type = class_res.get("document_type", "UNKNOWN")
            doc_confidence = class_res.get("confidence", 0.5)
        else:
            detected_doc_type = document_type_hint
            doc_confidence = 0.95
        log_stage_completion("DOCUMENT_CLASSIFICATION", {"type": detected_doc_type, "confidence": doc_confidence})
    except Exception as e:
        logger.warning(f"Classification heuristic degraded: {e}")
        detected_doc_type = "UNKNOWN"
        doc_confidence = 0.35
        log_stage_completion("DOCUMENT_CLASSIFICATION", {"type": "UNKNOWN", "confidence": 0.35})

    # =========================================================================
    # STAGE 5: FIELD & CHRONOLOGICAL VALIDATION
    # =========================================================================
    current_stage = "FIELD_VALIDATION"
    try:
        validation_res = validation_service.validate_document_data(
            fields=ocr_raw_res["fields"],
            mrz_data=ocr_raw_res.get("mrz"),
            document_type=detected_doc_type
        )
        logger.info(f"VALIDATION_COMPLETE: valid={validation_res.valid} passed={validation_res.passed_count}")
        log_stage_completion("FIELD_VALIDATION", {"valid": validation_res.valid, "failed_count": validation_res.failed_count})
    except Exception as e:
        logger.error(f"Validation check error: {e}")
        from backend.app.models.schemas import ValidationSummary, ValidationCheck
        validation_res = ValidationSummary(
            valid=True,
            passed_count=0,
            failed_count=0,
            warning_count=1,
            checks=[ValidationCheck(
                name="Validation Execution Check",
                status="UNAVAILABLE",
                severity="INFO",
                message="Validation logic executed in degraded mode."
            )]
        )
        log_stage_completion("FIELD_VALIDATION", {"status": "DEGRADED"})

    # =========================================================================
    # STAGE 6: VISUAL FORENSICS & AI PROVIDER
    # =========================================================================
    current_stage = "VISUAL_FORENSICS"
    try:
        tamper_res = tamper_detection_service.analyze_document(front_path, case_id=case_id)
        ai_provider = get_ai_provider()
        try:
            ai_assessment = ai_provider.analyze_document(front_path)
            if ai_assessment.get("gemini_insights"):
                tamper_res.signals["gemini_insights"] = ai_assessment["gemini_insights"]
            tamper_res.signals["ai_provider"] = ai_assessment.get("provider", "LOCAL_CV_FALLBACK")
            tamper_res.signals["ai_provider_status"] = ai_assessment.get("provider_status", "ACTIVE")
            if "provider_reason" in ai_assessment:
                tamper_res.signals["ai_provider_reason"] = ai_assessment["provider_reason"]
        except Exception as ai_err:
            logger.info(f"Gemini fallback to Local CV: {ai_err}")
            tamper_res.signals["ai_provider"] = "LOCAL_CV_FALLBACK"
            tamper_res.signals["ai_provider_status"] = "LOCAL_FALLBACK"
            tamper_res.signals["ai_provider_reason"] = "Gemini unavailable"

        logger.info(f"FORENSICS_COMPLETE: tampering={tamper_res.tampering_detected} regions={len(tamper_res.regions)}")
        log_stage_completion("VISUAL_FORENSICS", {
            "tampering_detected": tamper_res.tampering_detected,
            "confidence": tamper_res.confidence,
            "provider": tamper_res.signals.get("ai_provider", "LOCAL_CV_FALLBACK")
        })
    except Exception as e:
        logger.error(f"Forensics model error: {e}")
        tamper_res = TamperResultResponse(
            tampering_detected=False,
            confidence=0.0,
            regions=[],
            signals={"status": "UNAVAILABLE", "confidence": 0, "reason": "Forensic model unavailable"},
            heatmap_url=None,
            evidence=["Forensics model unavailable."]
        )
        log_stage_completion("VISUAL_FORENSICS", {"status": "UNAVAILABLE"})

    # =========================================================================
    # STAGE 7: IDENTITY & FACE VERIFICATION (OPTIONAL PRESENTER CHECK)
    # =========================================================================
    current_stage = "FACE_VERIFICATION"
    try:
        face_res = face_verification_service.verify_document_and_person(
            document_image_path=front_path,
            live_person_image_path=live_path
        )
        logger.info(f"IDENTITY_COMPLETE: status={face_res.status} doc_face={face_res.document_face_detected}")
        log_stage_completion("FACE_VERIFICATION", {"status": face_res.status, "similarity": face_res.similarity})
    except Exception as e:
        logger.warning(f"Face verification non-fatal error: {e}")
        face_res = FaceVerificationResponse(
            document_face_detected=False,
            live_face_detected=False,
            document_face_quality=0.0,
            live_face_quality=0.0,
            similarity=0.0,
            status="NOT_PROVIDED",
            explanation="Biometric face comparison skipped.",
            message="Presenter image was not provided."
        )
        log_stage_completion("FACE_VERIFICATION", {"status": "NOT_PROVIDED"})

    # =========================================================================
    # STAGE 8: CENTRAL RECORD VERIFICATION CROSS-CHECK
    # =========================================================================
    current_stage = "RECORD_VERIFICATION"
    try:
        doc_fields = ocr_raw_res["fields"]
        doc_number = (
            getattr(doc_fields, "document_number", "")
            or (ocr_raw_res["mrz"].passport_number if ocr_raw_res.get("mrz") else "")
        )
        candidate_name = getattr(doc_fields, "name", None)

        record_res = record_verification_service.verify_record(
            document_number=doc_number,
            document_type=detected_doc_type,
            candidate_name=candidate_name
        )
        logger.info(f"RECORD_CHECK_COMPLETE: status={record_res.status}")
        log_stage_completion("RECORD_VERIFICATION", {"status": record_res.status, "found": record_res.record_found})
    except Exception as e:
        logger.warning(f"Record verification non-fatal error: {e}")
        record_res = RecordVerificationResponse(
            record_found=False,
            status="UNAVAILABLE",
            document_number="",
            source="FALLBACK",
            match_details={"status": "UNAVAILABLE"},
            checked_at=utc_now(),
            disclaimer="SIMULATED"
        )
        log_stage_completion("RECORD_VERIFICATION", {"status": "UNAVAILABLE"})

    # =========================================================================
    # STAGE 9: MULTI-SIGNAL RISK FUSION
    # =========================================================================
    current_stage = "RISK_ASSESSMENT"
    try:
        ocr_response_obj = OCRResultResponse(
            raw_text=ocr_raw_res["raw_text"],
            fields=ocr_raw_res["fields"],
            mrz=ocr_raw_res.get("mrz"),
            confidence=ocr_raw_res["confidence"],
            bounding_boxes=ocr_raw_res.get("bounding_boxes", []),
            engine_used=ocr_raw_res.get("engine_used", "TRUST-ID OCR"),
            status=ocr_raw_res.get("status", "OK"),
            ocr_status=ocr_raw_res.get("ocr_status", "OK")
        )

        risk_assessment = risk_engine.evaluate(
            quality=quality_res,
            ocr=ocr_response_obj,
            validation=validation_res,
            tampering=tamper_res,
            face=face_res,
            record=record_res
        )
        logger.info(f"RISK_COMPLETE: score={risk_assessment.risk_score} level={risk_assessment.risk_level}")
        log_stage_completion("RISK_ASSESSMENT", {
            "score": risk_assessment.risk_score,
            "level": risk_assessment.risk_level,
            "confidence": risk_assessment.confidence
        })
    except Exception as e:
        logger.error(f"Risk evaluation error: {e}")
        return make_error_response("RISK_ASSESSMENT", "RISK_ENGINE_ERROR", "Risk engine could not aggregate screening signals.")

    # =========================================================================
    # STAGE 10: EXPLAINABILITY & NARRATIVE
    # =========================================================================
    current_stage = "EXPLANATION"
    try:
        narrative_report = explainability_service.generate_narrative_report(risk_assessment)
        log_stage_completion("EXPLANATION", {"tone": narrative_report.get("summary_tone")})
    except Exception as e:
        logger.warning(f"Narrative generation non-fatal error: {e}")
        narrative_report = {
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level,
            "confidence_percentage": round(risk_assessment.confidence * 100, 1),
            "primary_driver": "Multi-signal evaluation",
            "summary_tone": "conforming" if risk_assessment.risk_level == "LOW" else "concerning",
            "reasons": risk_assessment.risk_factors,
            "positive_signals": risk_assessment.positive_signals,
            "recommended_actions": [risk_assessment.recommended_action],
            "signal_radar": risk_assessment.signal_scores,
            "human_in_the_loop_mandatory": risk_assessment.risk_level == "HIGH"
        }
        log_stage_completion("EXPLANATION", {"status": "DEGRADED"})

    # =========================================================================
    # STAGE 11: DATABASE PERSISTENCE (NON-FATAL)
    # =========================================================================
    current_stage = "DATABASE_SAVE"
    db_save_successful = True
    try:
        # Create Case in DB
        case = Case(
            id=case_id,
            case_number=case_number,
            document_type=detected_doc_type,
            status="REVIEW_REQUIRED" if (risk_assessment.risk_level in ("HIGH", "MEDIUM")) else "COMPLETED",
            risk_level=risk_assessment.risk_level,
            risk_score=risk_assessment.risk_score,
            confidence=risk_assessment.confidence,
            requires_human_review=(risk_assessment.risk_level in ("HIGH", "MEDIUM")),
            notes=notes
        )
        db.add(case)

        # Audit initial event
        actor = (current_user or {}).get("username", "system_screening")
        audit_service.record_event(
            db, case_id=case_id,
            actor_id=actor,
            action="CASE_CREATED",
            details={"case_number": case_number, "hint": document_type_hint}
        )

        # Save Front Document
        doc_front = Document(
            id=generate_uuid(),
            case_id=case_id,
            side="FRONT",
            filename=primary_file.filename or "front.png",
            file_path=front_path,
            file_size_bytes=f_size,
            mime_type=primary_file.content_type or "image/png",
            sha256_hash=f_hash,
            width=f_w,
            height=f_h,
            quality_score=quality_res.quality_score,
            quality_issues=quality_res.issues
        )
        db.add(doc_front)

        # Save Live Document if present
        if live_path:
            doc_live = Document(
                id=generate_uuid(),
                case_id=case_id,
                side="LIVE_PERSON",
                filename="live_selfie.png",
                file_path=live_path,
                file_size_bytes=l_size,
                mime_type="image/png",
                sha256_hash=l_hash,
                width=l_w,
                height=l_h
            )
            db.add(doc_live)

        # Helper for Pydantic dump
        def safe_dump(obj):
            if obj is None:
                return None
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            if hasattr(obj, "dict"):
                return obj.dict()
            return obj

        # Save OCR Result
        ocr_record = OCRResult(
            id=generate_uuid(),
            case_id=case_id,
            raw_text=ocr_raw_res["raw_text"],
            extracted_fields=safe_dump(ocr_raw_res["fields"]),
            mrz_data=safe_dump(ocr_raw_res.get("mrz")),
            confidence=ocr_raw_res["confidence"],
            bounding_boxes=[safe_dump(b) for b in ocr_raw_res.get("bounding_boxes", [])],
            engine_used=ocr_raw_res.get("engine_used", "TRUST-ID OCR")
        )
        db.add(ocr_record)

        # Save Validation Checks
        for c in validation_res.checks:
            val_item = ValidationResult(
                id=generate_uuid(),
                case_id=case_id,
                check_name=c.name,
                status=c.status,
                severity=c.severity,
                message=c.message,
                evidence=c.evidence
            )
            db.add(val_item)

        # Save Tamper Result
        tamper_record = TamperResult(
            id=generate_uuid(),
            case_id=case_id,
            tampering_detected=tamper_res.tampering_detected,
            confidence=tamper_res.confidence,
            regions=[safe_dump(r) for r in tamper_res.regions],
            signals=tamper_res.signals,
            heatmap_path=tamper_res.heatmap_url
        )
        db.add(tamper_record)

        # Save Face Verification Result
        face_record = FaceVerificationResult(
            id=generate_uuid(),
            case_id=case_id,
            document_face_detected=face_res.document_face_detected,
            live_face_detected=face_res.live_face_detected,
            document_face_quality=face_res.document_face_quality,
            live_face_quality=face_res.live_face_quality,
            similarity=face_res.similarity,
            status=face_res.status,
            explanation=face_res.explanation
        )
        db.add(face_record)

        # Save Record Verification Result
        record_db = RecordVerificationResult(
            id=generate_uuid(),
            case_id=case_id,
            record_found=record_res.record_found,
            status=record_res.status,
            document_number=record_res.document_number,
            source=record_res.source,
            match_details=record_res.match_details,
            checked_at=record_res.checked_at
        )
        db.add(record_db)

        # Save Risk Assessment
        risk_db = RiskAssessment(
            id=generate_uuid(),
            case_id=case_id,
            risk_score=risk_assessment.risk_score,
            risk_level=risk_assessment.risk_level,
            confidence=risk_assessment.confidence,
            recommended_action=risk_assessment.recommended_action,
            signal_scores=risk_assessment.signal_scores,
            risk_factors=risk_assessment.risk_factors,
            positive_signals=risk_assessment.positive_signals,
            explanation=risk_assessment.explanation
        )
        db.add(risk_db)

        # =========================================================================
        # 100-POINT DOCUMENT CHECK ENGINE EXECUTION
        # =========================================================================
        doc_meta = {
            "document_type": detected_doc_type,
            "quality_score": getattr(quality_res, "quality_score", 0.95),
            "image_available": True
        }

        forensics_dict = {
            "ela_tamper_score": getattr(tamper_res, "ela_tamper_score", 0.1),
            "copy_move_detected": getattr(tamper_res, "copy_move_detected", False),
            "face_manipulated": getattr(tamper_res, "face_tamper_detected", False),
            "font_inconsistencies": getattr(tamper_res, "font_anomaly_detected", False),
            "tampering_detected": getattr(tamper_res, "tampering_detected", False),
        }

        face_dict = {
            "document_face_detected": getattr(face_res, "document_face_detected", False),
            "doc_face_quality": getattr(face_res, "document_face_quality", 0.8),
            "presenter_face_detected": getattr(face_res, "live_face_detected", False),
            "presenter_face_quality": getattr(face_res, "live_face_quality", 0.8 if getattr(face_res, "live_face_detected", False) else 0.0),
            "match_score": getattr(face_res, "similarity", 0.85 if getattr(face_res, "live_face_detected", False) else 0.0),
            "face_verified": getattr(face_res, "status", "") == "MATCH"
        }

        record_dict = {
            "available": getattr(record_res, "source", None) is not None,
            "found": getattr(record_res, "record_found", False),
            "status_valid": getattr(record_res, "status", "") == "ACTIVE" if getattr(record_res, "record_found", False) else None,
            "number_matches": getattr(record_res, "match_details", {}).get("document_number", False),
            "name_matches": getattr(record_res, "match_details", {}).get("name", False),
            "dob_matches": getattr(record_res, "match_details", {}).get("dob", False),
            "external_consistent": getattr(record_res, "record_found", False)
        }

        risk_dict = {
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level,
            "risk_factors": [{"signal": "RISK", "description": str(f)} for f in risk_assessment.risk_factors],
            "positive_signals": [str(s) for s in risk_assessment.positive_signals]
        }

        checks_data = document_check_engine.run_all_checks(
            case_id=case_id,
            doc_metadata=doc_meta,
            ocr_result=ocr_raw_res,
            forensics_result=forensics_dict,
            face_result=face_dict,
            record_result=record_dict,
            risk_result=risk_dict
        )

        for chk in checks_data["checks"]:
            c_rec = DocumentCheck(
                id=generate_uuid(),
                case_id=case_id,
                check_id=chk["check_id"],
                category=chk["category"],
                name=chk["name"],
                description=chk.get("description", ""),
                status=chk["status"],
                severity=chk["severity"],
                confidence=chk["confidence"],
                evidence=chk.get("evidence", ""),
                value=chk.get("value"),
                expected_value=chk.get("expected_value"),
                message=chk.get("message", "")
            )
            db.add(c_rec)

        # Commit all entities
        db.commit()

        # Log Final Risk Assessment into Audit Trail
        audit_service.record_event(
            db, case_id=case_id,
            actor_id="system_risk_engine",
            action="RISK_ASSESSMENT_FINALIZED",
            details={
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level,
                "document_integrity_score": checks_data["document_integrity_score"],
                "total_checks": 100,
                "passed_checks": checks_data["passed"],
                "failed_checks": checks_data["failed"]
            }
        )
        log_stage_completion("DATABASE_SAVE", {"status": "SUCCESS"})
    except Exception as dbe:
        logger.error(f"Database save error (preserving analysis): {dbe}")
        db_save_successful = False
        log_stage_completion("DATABASE_SAVE", {"status": "FAILED", "reason": "Database connection error"})

    final_status = "COMPLETED" if db_save_successful else "COMPLETED_DATABASE_SAVE_FAILED"
    log_stage_completion("COMPLETED", {"status": final_status})
    logger.info(f"SCREENING_COMPLETE: case_id={case_id} status={final_status}")

    # =========================================================================
    # AUTOMATIC REPORT GENERATION (NON-BLOCKING AS PER SPEC 32)
    # =========================================================================
    pdf_generated = False
    report_hash = hashlib.sha256(f"{case_id}:{case_number}:{risk_assessment.risk_score}".encode()).hexdigest()
    try:
        case_dict_for_export = {
            "id": case_id,
            "case_number": case_number,
            "document_type": detected_doc_type,
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level,
            "decision": "APPROVED" if risk_assessment.risk_level == "LOW" else "PENDING_REVIEW",
            "created_at": utc_now().strftime("%Y-%m-%d %H:%M UTC")
        }
        
        pdf_path = report_pdf_service.generate_pdf_report(
            case=case_dict_for_export,
            checks_data=checks_data,
            ocr_data=ocr_raw_res,
            risk_data=risk_dict,
            audit_event_hash=report_hash
        )
        pdf_generated = bool(pdf_path and os.path.exists(pdf_path))

        # Save Report record into DB
        if db_save_successful:
            try:
                rep_rec = Report(
                    id=generate_uuid(),
                    case_id=case_id,
                    report_type="FULL_SCREENING",
                    pdf_path=f"/api/cases/{case_id}/report/pdf",
                    csv_path=f"/api/cases/{case_id}/report/csv",
                    docx_path=f"/api/cases/{case_id}/report/docx",
                    report_hash=report_hash,
                    created_at=utc_now()
                )
                db.add(rep_rec)
                db.commit()
            except Exception as re:
                logger.warning(f"Could not persist Report metadata: {re}")
                db.rollback()

    except Exception as rep_err:
        logger.warning(f"Non-blocking report generation error: {rep_err}")
        pdf_generated = False

    # Helper for serialization
    def serialize_model(obj):
        if obj is None:
            return None
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return obj

    # =========================================================================
    # UNIFIED RESPONSE CONTRACT (100 CHECKS + EXPORTS + BACKWARD COMPATIBILITY)
    # =========================================================================
    return {
        "success": True,
        "case_id": case_id,
        "case_number": case_number,
        "status": final_status,
        "document": {
            "type": detected_doc_type,
            "confidence": doc_confidence
        },
        "ocr": serialize_model(ocr_response_obj),
        "validation": serialize_model(validation_res),
        "forensics": serialize_model(tamper_res),
        "identity": serialize_model(face_res),
        "records": serialize_model(record_res),
        "risk": serialize_model(risk_assessment),
        "explanation": narrative_report,
        "pipeline": pipeline_stages,

        # 100 Document Checks & Scores
        "document_integrity_score": checks_data["document_integrity_score"],
        "checks_summary": {
            "total_checks": checks_data["total_checks"],
            "passed": checks_data["passed"],
            "failed": checks_data["failed"],
            "warnings": checks_data["warnings"],
            "unavailable": checks_data["unavailable"],
            "not_applicable": checks_data["not_applicable"],
        },
        "category_breakdown": checks_data["category_breakdown"],
        "checks": checks_data["checks"],

        # Reports & Exports URLs
        "report_pdf_url": f"/api/cases/{case_id}/report/pdf",
        "report_csv_url": f"/api/cases/{case_id}/report/csv",
        "report_docx_url": f"/api/cases/{case_id}/report/docx",
        "report_zip_url": f"/api/cases/{case_id}/report/zip",
        "pdf_report_ready": pdf_generated,
        "report_hash": report_hash,

        # Backward compatibility fields for frontend UI
        "document_type": detected_doc_type,
        "risk_level": risk_assessment.risk_level,
        "risk_score": risk_assessment.risk_score,
        "confidence": risk_assessment.confidence,
        "requires_human_review": (risk_assessment.risk_level in ("HIGH", "MEDIUM")),
        "recommendation": risk_assessment.recommended_action,
        "summary": narrative_report
    }

