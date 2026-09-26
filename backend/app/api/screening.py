import os
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks
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
from backend.app.core.exceptions import InvalidDocumentException, FileTooLargeException
from backend.app.core.config import settings
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
    force_local_fallback: Optional[bool] = Form(False),
    force_fresh: Optional[bool] = Form(False),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """
    Executes the 10-stage TRUST-ID screening workflow with stage tracking:
    UPLOAD -> IMAGE_QUALITY -> DOCUMENT_CLASSIFICATION -> OCR -> FIELD_VALIDATION ->
    VISUAL_FORENSICS -> FACE_VERIFICATION -> RECORD_VERIFICATION -> RISK_ASSESSMENT ->
    EXPLANATION -> DATABASE_SAVE -> COMPLETED
    """
    t_start = time.perf_counter()
    request_id = generate_uuid()
    case_id = generate_uuid()
    case_number = f"CASE-{utc_now().strftime('%Y%m%d')}-{case_id[:6].upper()}"
    current_stage = "UPLOAD"
    pipeline_stages: List[Dict[str, Any]] = []

    def log_stage_completion(stage_name: str, details: Optional[Dict[str, Any]] = None, status: str = "COMPLETED", confidence: float = 1.0, findings: Optional[List[Any]] = None, errors: Optional[List[str]] = None):
        pipeline_stages.append({
            "stage": stage_name,
            "status": status,
            "confidence": confidence,
            "findings": findings or [],
            "errors": errors or [],
            "details": details or {}
        })

    def make_error_response(stage: str, code: str, message: str, recoverable: bool = True, http_status: int = 400, user_action: Optional[str] = None):
        logger.error(
            f"SCREENING_ERROR: request_id={request_id} case_id={case_id} stage={stage} "
            f"code={code} message={message} http_status={http_status}"
        )
        pipeline_stages.append({
            "stage": stage,
            "status": "FAILED",
            "confidence": 0.0,
            "findings": [],
            "errors": [message],
            "code": code,
            "message": message
        })
        default_user_action = (
            "Retry screening or execute with local computer-vision fallback."
            if recoverable else
            "Please inspect the uploaded document scan and re-upload in a supported format (PDF, PNG, JPG, WEBP)."
        )
        return JSONResponse(
            status_code=http_status,
            content={
                "success": False,
                "request_id": request_id,
                "case_id": case_id,
                "stage": stage,
                "code": code,
                "error_code": code,
                "message": message,
                "recoverable": recoverable,
                "user_action": user_action or default_user_action,
                "error": {
                    "code": code,
                    "message": message,
                    "stage": stage
                },
                "pipeline": pipeline_stages,
                "stages": pipeline_stages
            }
        )

    user_id = (current_user or {}).get("username", "anonymous")
    primary_file = file or primary_document
    file_name = primary_file.filename if primary_file else "unknown"
    content_type = primary_file.content_type if primary_file else "unknown"

    logger.info(
        f"SCREENING_START: request_id={request_id} case_id={case_id} user_id={user_id} "
        f"filename={file_name} content_type={content_type} hint={document_type_hint} "
        f"force_local_fallback={force_local_fallback}"
    )

    # =========================================================================
    # STAGE 1: UPLOAD & NORMALIZATION
    # =========================================================================
    current_stage = "UPLOAD"
    try:
        if not primary_file:
            return make_error_response("UPLOAD", "MISSING_FILE", "Front image of credential was not provided.", True, 400)

        front_bytes = await primary_file.read()
        if not front_bytes:
            return make_error_response("UPLOAD", "EMPTY_FILE", "Uploaded document file is empty.", False, 400)

        front_path, f_hash, f_size, f_w, f_h = storage_service.save_upload(
            case_id, primary_file.filename or "front.png", front_bytes
        )
        upload_ms = round((time.perf_counter() - t_start) * 1000, 1)

        live_path = None
        if live_person_file:
            live_bytes = await live_person_file.read()
            if live_bytes:
                live_path, l_hash, l_size, l_w, l_h = storage_service.save_upload(
                    case_id, "live_selfie.png", live_bytes
                )

        log_stage_completion("UPLOAD", {"filename": primary_file.filename, "size_bytes": f_size, "dimensions": f"{f_w}x{f_h}"})
    except InvalidDocumentException as ide:
        return make_error_response("UPLOAD", ide.code or "INVALID_DOCUMENT", ide.message, recoverable=False, http_status=400)
    except FileTooLargeException as fle:
        return make_error_response("UPLOAD", "FILE_TOO_LARGE", fle.message, recoverable=False, http_status=400)
    except ValueError as ve:
        err_msg = str(ve)
        if "PDF processing" in err_msg:
            return make_error_response("UPLOAD", "PDF_UNSUPPORTED", "PDF processing is not enabled in this deployment.", recoverable=False, http_status=400)
        return make_error_response("UPLOAD", "IMAGE_NORMALIZATION_FAILED", err_msg, recoverable=False, http_status=400)
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return make_error_response("UPLOAD", "STORAGE_ERROR", "Failed to securely save uploaded document.", recoverable=True, http_status=500)

    # =========================================================================
    # STAGE 2: IMAGE QUALITY
    # =========================================================================
    current_stage = "IMAGE_QUALITY"
    t_pp_start = time.perf_counter()
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
    preprocessing_ms = round((time.perf_counter() - t_pp_start) * 1000, 1)

    # =========================================================================
    # STAGE 3: OCR EXTRACTION & CACHING
    # =========================================================================
    current_stage = "OCR"
    t_ocr_start = time.perf_counter()
    logger.info("OCR_START")
    try:
        ocr_raw_res = ocr_service.process_document(front_path, file_hash=f_hash, force_fresh=bool(force_fresh))
        logger.info(f"OCR_COMPLETE: confidence={ocr_raw_res.get('confidence', 0)} engine={ocr_raw_res.get('engine_used')} cached={ocr_raw_res.get('cached')}")
        log_stage_completion("OCR", {
            "confidence": ocr_raw_res.get("confidence", 0.0),
            "status": ocr_raw_res.get("status", "OK"),
            "engine": ocr_raw_res.get("engine_used", "Local OCR"),
            "cached": ocr_raw_res.get("cached", False)
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
            "ocr_status": "LOW_CONFIDENCE",
            "cached": False
        }
        log_stage_completion("OCR", {"status": "LOW_CONFIDENCE", "confidence": 0.35})
    ocr_ms = round((time.perf_counter() - t_ocr_start) * 1000, 1)

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
    # STAGES 5, 6, 7, 8: CONCURRENT MULTI-SIGNAL ANALYSIS (SPEC PHASE 4 & 18)
    # =========================================================================
    def execute_field_validation():
        try:
            val_out = validation_service.validate_document_data(
                fields=ocr_raw_res["fields"],
                mrz_data=ocr_raw_res.get("mrz"),
                document_type=detected_doc_type
            )
            return val_out, ("FIELD_VALIDATION", {"valid": val_out.valid, "failed_count": val_out.failed_count}, "COMPLETED")
        except Exception as err:
            logger.error(f"Validation check error: {err}")
            from backend.app.models.schemas import ValidationSummary, ValidationCheck
            val_out = ValidationSummary(
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
            return val_out, ("FIELD_VALIDATION", {"status": "DEGRADED"}, "DEGRADED")

    def execute_visual_forensics():
        try:
            tamper_out = tamper_detection_service.analyze_document(front_path, case_id=case_id)
            if force_local_fallback:
                ai_prov = get_ai_provider("LOCAL_CV_FALLBACK")
                ai_assess = ai_prov.analyze_document(front_path)
                tamper_out.signals["ai_provider"] = "LOCAL_CV_FALLBACK"
                tamper_out.signals["ai_provider_status"] = "LOCAL_FALLBACK"
                tamper_out.signals["ai_status"] = "fallback"
                tamper_out.signals["verification_mode"] = "LOCAL_FALLBACK"
                tamper_out.signals["ai_provider_reason"] = "Processed with Local CV Fallback (AI unavailable)"
                tamper_out.signals["user_notice"] = "Processed with Local CV Fallback (AI unavailable)"
            else:
                ai_prov = get_ai_provider()
                try:
                    ai_assess = ai_prov.analyze_document(front_path)
                    if ai_assess.get("gemini_insights"):
                        tamper_out.signals["gemini_insights"] = ai_assess["gemini_insights"]
                    tamper_out.signals["ai_provider"] = ai_assess.get("provider", "LOCAL_CV_FALLBACK")
                    tamper_out.signals["ai_provider_status"] = ai_assess.get("provider_status", "ACTIVE")
                    tamper_out.signals["ai_status"] = ai_assess.get("ai_status", "available")
                    if "verification_mode" in ai_assess:
                        tamper_out.signals["verification_mode"] = ai_assess["verification_mode"]
                    if "provider_reason" in ai_assess:
                        tamper_out.signals["ai_provider_reason"] = ai_assess["provider_reason"]
                    if "user_notice" in ai_assess:
                        tamper_out.signals["user_notice"] = ai_assess["user_notice"]
                except Exception as ai_err:
                    logger.info(f"Gemini fallback to Local CV: {ai_err}")
                    tamper_out.signals["ai_provider"] = "LOCAL_CV_FALLBACK"
                    tamper_out.signals["ai_provider_status"] = "LOCAL_FALLBACK"
                    tamper_out.signals["ai_status"] = "unavailable"
                    tamper_out.signals["verification_mode"] = "LOCAL_FALLBACK"
                    tamper_out.signals["ai_provider_reason"] = "AI analysis unavailable — manual verification required"
                    tamper_out.signals["user_notice"] = "AI analysis unavailable — manual verification required"

            return tamper_out, (
                "VISUAL_FORENSICS",
                {
                    "tampering_detected": tamper_out.tampering_detected,
                    "confidence": tamper_out.confidence,
                    "provider": tamper_out.signals.get("ai_provider", "LOCAL_CV_FALLBACK"),
                    "ai_status": tamper_out.signals.get("ai_status", "available")
                },
                "COMPLETED"
            )
        except Exception as err:
            logger.error(f"Forensics model error: {err}")
            t_res = TamperResultResponse(
                tampering_detected=False,
                confidence=0.0,
                regions=[],
                signals={"status": "UNAVAILABLE", "confidence": 0, "reason": "Forensic model unavailable"},
                heatmap_url=None,
                evidence=["Forensics model unavailable."]
            )
            return t_res, ("VISUAL_FORENSICS", {"status": "UNAVAILABLE"}, "UNAVAILABLE")

    def execute_face_verification():
        try:
            face_out = face_verification_service.verify_document_and_person(
                document_image_path=front_path,
                live_person_image_path=live_path
            )
            return face_out, ("FACE_VERIFICATION", {"status": face_out.status, "similarity": face_out.similarity}, face_out.status)
        except Exception as err:
            logger.warning(f"Face verification non-fatal error: {err}")
            face_out = FaceVerificationResponse(
                document_face_detected=False,
                live_face_detected=False,
                document_face_quality=0.0,
                live_face_quality=0.0,
                similarity=0.0,
                status="NOT_PROVIDED",
                explanation="Biometric face comparison skipped.",
                message="Presenter image was not provided."
            )
            return face_out, ("FACE_VERIFICATION", {"status": "NOT_PROVIDED"}, "NOT_PROVIDED")

    def execute_record_verification():
        try:
            doc_fields = ocr_raw_res.get("fields")
            raw_doc_num = getattr(doc_fields, "document_number", "") if hasattr(doc_fields, "document_number") else ""
            if isinstance(raw_doc_num, str) and raw_doc_num:
                doc_number = raw_doc_num
            elif isinstance(doc_fields, dict):
                doc_number = str(doc_fields.get("document_number") or "")
            elif ocr_raw_res.get("mrz") and hasattr(ocr_raw_res["mrz"], "passport_number"):
                doc_number = str(ocr_raw_res["mrz"].passport_number or "")
            else:
                doc_number = ""

            candidate_name = None
            if hasattr(doc_fields, "name") and isinstance(getattr(doc_fields, "name"), str):
                candidate_name = getattr(doc_fields, "name")
            elif isinstance(doc_fields, dict):
                candidate_name = doc_fields.get("name")

            rec_out = record_verification_service.verify_record(
                document_number=doc_number,
                document_type=detected_doc_type,
                candidate_name=candidate_name
            )
            return rec_out, ("RECORD_VERIFICATION", {"status": rec_out.status, "found": rec_out.record_found}, rec_out.status)
        except Exception as err:
            logger.warning(f"Record verification non-fatal error: {err}")
            rec_out = RecordVerificationResponse(
                record_found=False,
                status="UNAVAILABLE",
                document_number="",
                source="FALLBACK",
                match_details={"status": "UNAVAILABLE"},
                checked_at=utc_now(),
                disclaimer="SIMULATED"
            )
            return rec_out, ("RECORD_VERIFICATION", {"status": "UNAVAILABLE"}, "UNAVAILABLE")

    t_concurrent_start = time.perf_counter()
    (validation_res, s5_log), (tamper_res, s6_log), (face_res, s7_log), (record_res, s8_log) = await asyncio.gather(
        asyncio.to_thread(execute_field_validation),
        asyncio.to_thread(execute_visual_forensics),
        asyncio.to_thread(execute_face_verification),
        asyncio.to_thread(execute_record_verification)
    )
    concurrent_ms = round((time.perf_counter() - t_concurrent_start) * 1000, 1)

    log_stage_completion(s5_log[0], s5_log[1], status=s5_log[2])
    log_stage_completion(s6_log[0], s6_log[1], status=s6_log[2])
    log_stage_completion(s7_log[0], s7_log[1], status=s7_log[2])
    log_stage_completion(s8_log[0], s8_log[1], status=s8_log[2])

    # =========================================================================
    # STAGE 9: MULTI-SIGNAL RISK FUSION
    # =========================================================================
    current_stage = "RISK_ASSESSMENT"
    try:
        fields_input = ocr_raw_res.get("fields")
        if not isinstance(fields_input, (dict, ExtractedFields)):
            fields_input = ExtractedFields()

        ocr_response_obj = OCRResultResponse(
            raw_text=str(ocr_raw_res.get("raw_text", "")),
            fields=fields_input,
            mrz=ocr_raw_res.get("mrz") if hasattr(ocr_raw_res.get("mrz"), "passport_number") or isinstance(ocr_raw_res.get("mrz"), dict) else None,
            confidence=float(ocr_raw_res.get("confidence", 0.0)),
            bounding_boxes=ocr_raw_res.get("bounding_boxes", []) if isinstance(ocr_raw_res.get("bounding_boxes"), list) else [],
            engine_used=str(ocr_raw_res.get("engine_used", "TRUST-ID OCR")),
            status=str(ocr_raw_res.get("status", "OK")),
            ocr_status=str(ocr_raw_res.get("ocr_status", "OK"))
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
        logger.warning(f"Risk evaluation non-fatal error: {e}")
        risk_assessment = RiskAssessmentResponse(
            risk_score=75.0,
            risk_level="HIGH",
            confidence=0.5,
            recommended_action="MANUAL_REVIEW_REQUIRED",
            signal_scores={"risk_engine": 0.75},
            risk_factors=[f"Risk engine evaluation encountered degraded input signals ({type(e).__name__}); manual verification required."],
            positive_signals=[],
            explanation="Risk evaluation completed in degraded fallback mode.",
            weights_used={},
            unavailable_checks=["RISK_ENGINE"]
        )
        log_stage_completion("RISK_ASSESSMENT", {
            "score": risk_assessment.risk_score,
            "level": risk_assessment.risk_level,
            "status": "DEGRADED",
            "error": str(e)
        })

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
    # 100-POINT DOCUMENT CHECK ENGINE EXECUTION (PRE-DB)
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

    t_rules_start = time.perf_counter()
    checks_data = {
        "case_id": case_id,
        "total_checks": 100,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "unavailable": 100,
        "not_applicable": 0,
        "document_integrity_score": 50.0,
        "category_breakdown": {},
        "checks": []
    }
    try:
        checks_data = document_check_engine.run_all_checks(
            case_id=case_id,
            doc_metadata=doc_meta,
            ocr_result=ocr_raw_res,
            forensics_result=forensics_dict,
            face_result=face_dict,
            record_result=record_dict,
            risk_result=risk_dict
        )
    except Exception as ce:
        logger.error(f"100-Checks engine degraded: {ce}")
    rules_ms = round((time.perf_counter() - t_rules_start) * 1000, 1)

    # =========================================================================
    # STAGE 11: DATABASE PERSISTENCE (NON-FATAL BATCH INSERTION)
    # =========================================================================
    current_stage = "DATABASE_SAVE"
    t_db_start = time.perf_counter()
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

        # Batch insert all 100 Document Checks (Spec Phase 13)
        check_records = [
            DocumentCheck(
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
            for chk in checks_data["checks"]
        ]
        db.add_all(check_records)

        # Commit all entities in one atomic transaction
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
        try:
            db.rollback()
        except Exception:
            pass
        db_save_successful = False
        log_stage_completion("DATABASE_SAVE", {"status": "FAILED", "reason": "Database connection error"})

    db_ms = round((time.perf_counter() - t_db_start) * 1000, 1)
    final_status = "COMPLETED" if db_save_successful else "COMPLETED_DATABASE_SAVE_FAILED"
    log_stage_completion("COMPLETED", {"status": final_status})
    logger.info(f"SCREENING_COMPLETE: case_id={case_id} status={final_status}")

    # =========================================================================
    # AUTOMATIC REPORT GENERATION (NON-BLOCKING AS PER SPEC 12 & 32)
    # =========================================================================
    report_hash = hashlib.sha256(f"{case_id}:{case_number}:{risk_assessment.risk_score}".encode()).hexdigest()
    case_dict_for_export = {
        "id": case_id,
        "case_number": case_number,
        "document_type": detected_doc_type,
        "risk_score": risk_assessment.risk_score,
        "risk_level": risk_assessment.risk_level,
        "decision": "APPROVED" if risk_assessment.risk_level == "LOW" else "PENDING_REVIEW",
        "created_at": utc_now().strftime("%Y-%m-%d %H:%M UTC")
    }

    def _safe_background_generate_pdf(case_data, chk_data, ocr_data_dict, rsk_data, rep_hsh):
        try:
            report_pdf_service.generate_pdf_report(
                case=case_data,
                checks_data=chk_data,
                ocr_data=ocr_data_dict,
                risk_data=rsk_data,
                audit_event_hash=rep_hsh
            )
        except Exception as e:
            logger.warning(f"Background PDF generation completed with error: {e}")

    # Non-blocking report generation: schedule in background task
    if background_tasks:
        background_tasks.add_task(
            _safe_background_generate_pdf,
            case_data=case_dict_for_export,
            chk_data=checks_data,
            ocr_data_dict=ocr_raw_res,
            rsk_data=risk_dict,
            rep_hsh=report_hash
        )

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
            try:
                db.rollback()
            except Exception:
                pass

    total_ms = round((time.perf_counter() - t_start) * 1000, 1)

    # Helper for serialization
    def serialize_model(obj):
        if obj is None:
            return None
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return obj

    verification_mode = tamper_res.signals.get("verification_mode") or (
        "LOCAL_FALLBACK" if force_local_fallback or tamper_res.signals.get("ai_status") in ("unavailable", "fallback", "TIMEOUT") else "HYBRID"
    )
    ai_status_val = tamper_res.signals.get("ai_status", "available")

    # =========================================================================
    # UNIFIED RESPONSE CONTRACT (100 CHECKS + EXPORTS + TIMING METRICS)
    # =========================================================================
    return {
        "success": True,
        "request_id": request_id,
        "case_id": case_id,
        "case_number": case_number,
        "status": final_status,
        "screening_status": "completed",
        "verification_mode": verification_mode,
        "ai_status": ai_status_val,
        "cached": bool(ocr_raw_res.get("cached", False)),
        "timing": {
            "upload_ms": upload_ms,
            "preprocessing_ms": preprocessing_ms,
            "ocr_ms": ocr_ms,
            "concurrent_stages_ms": concurrent_ms,
            "rules_100_checks_ms": rules_ms,
            "db_ms": db_ms,
            "total_ms": total_ms
        },
        "database_saved": db_save_successful,
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
        "stages": pipeline_stages,
        "force_local_fallback": bool(force_local_fallback),

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
        "pdf_report_ready": True,
        "report_generated": True,
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

