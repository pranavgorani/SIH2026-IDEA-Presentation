import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.models.database import (
    get_db, Case, Document, OCRResult, ValidationResult, TamperResult,
    FaceVerificationResult, RecordVerificationResult, RiskAssessment,
    generate_uuid, utc_now
)
from backend.app.models.schemas import CaseDetailResponse, CaseResponse
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
from backend.app.core.security import get_current_user_optional

router = APIRouter(prefix="/screen", tags=["Document Screening Pipeline"])

@router.post("", summary="Upload document and execute full AI screening pipeline")
async def run_screening_pipeline(
    file: UploadFile = File(..., description="Front image of identity credential"),
    back_file: Optional[UploadFile] = File(None, description="Optional back side image"),
    live_person_file: Optional[UploadFile] = File(None, description="Optional live portrait of individual"),
    document_type_hint: Optional[str] = Form("AUTO_DETECT"),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    """
    Executes the 10-step TRUST-ID screening workflow:
    1. Ingestion & Hashing -> 2. Quality Analysis -> 3. Classification ->
    4. OCR & MRZ Extraction -> 5. Logic Validation -> 6. Visual Forensics (ELA/Heatmap) ->
    7. Biometric Face Verification -> 8. Central Record Cross-Check ->
    9. Multi-Signal Risk Fusion -> 10. Explainable Report & Cryptographic Audit Event
    """
    # Create Case
    case_id = generate_uuid()
    case_number = f"CASE-{utc_now().strftime('%Y%m%d')}-{case_id[:6].upper()}"

    case = Case(
        id=case_id,
        case_number=case_number,
        document_type=document_type_hint if document_type_hint != "AUTO_DETECT" else "UNKNOWN",
        status="PROCESSING",
        risk_level="PENDING",
        notes=notes
    )
    db.add(case)
    db.commit()

    # Log Case Creation to Audit Trail
    audit_service.record_event(
        db, case_id=case_id,
        actor_id=current_user.get("username", "system"),
        action="CASE_CREATED",
        details={"case_number": case_number, "hint": document_type_hint}
    )

    # 1. Save Files
    front_bytes = await file.read()
    front_path, f_hash, f_size, f_w, f_h = storage_service.save_upload(case_id, file.filename or "front.jpg", front_bytes)

    doc_front = Document(
        id=generate_uuid(),
        case_id=case_id,
        side="FRONT",
        filename=file.filename or "front.jpg",
        file_path=front_path,
        file_size_bytes=f_size,
        mime_type=file.content_type or "image/jpeg",
        sha256_hash=f_hash,
        width=f_w,
        height=f_h
    )
    db.add(doc_front)

    live_path = None
    if live_person_file:
        live_bytes = await live_person_file.read()
        live_path, l_hash, l_size, l_w, l_h = storage_service.save_upload(case_id, "live_selfie.jpg", live_bytes)
        doc_live = Document(
            id=generate_uuid(),
            case_id=case_id,
            side="LIVE_PERSON",
            filename="live_selfie.jpg",
            file_path=live_path,
            file_size_bytes=l_size,
            mime_type=live_person_file.content_type or "image/jpeg",
            sha256_hash=l_hash,
            width=l_w,
            height=l_h
        )
        db.add(doc_live)

    db.commit()

    # 2. Image Quality Analysis
    quality_res = image_quality_service.analyze(front_path)
    doc_front.quality_score = quality_res.quality_score
    doc_front.quality_issues = quality_res.issues
    db.commit()

    audit_service.record_event(
        db, case_id=case_id,
        actor_id="system_analyzer",
        action="IMAGE_QUALITY_CHECK",
        details={"score": quality_res.quality_score, "acceptable": quality_res.is_acceptable}
    )

    # 3 & 4. OCR Extraction & Document Classification
    ocr_raw_res = ocr_service.process_document(front_path)
    has_mrz = ocr_raw_res.get("mrz") is not None and ocr_raw_res["mrz"].valid

    if document_type_hint == "AUTO_DETECT" or not document_type_hint:
        class_res = document_classifier.classify_document(
            text=ocr_raw_res["raw_text"],
            width=f_w,
            height=f_h,
            has_mrz=has_mrz
        )
        detected_doc_type = class_res["document_type"]
    else:
        detected_doc_type = document_type_hint

    case.document_type = detected_doc_type
    db.commit()

    # Save OCR DB Record
    ocr_record = OCRResult(
        id=generate_uuid(),
        case_id=case_id,
        raw_text=ocr_raw_res["raw_text"],
        extracted_fields=ocr_raw_res["fields"].dict(),
        mrz_data=ocr_raw_res["mrz"].dict() if ocr_raw_res.get("mrz") else None,
        confidence=ocr_raw_res["confidence"],
        bounding_boxes=[b.dict() for b in ocr_raw_res.get("bounding_boxes", [])],
        engine_used=ocr_raw_res.get("engine_used", "TRUST-ID Multi-Layer OCR")
    )
    db.add(ocr_record)
    db.commit()

    audit_service.record_event(
        db, case_id=case_id,
        actor_id="system_ocr",
        action="OCR_EXTRACTION_COMPLETE",
        details={"fields_extracted": bool(ocr_raw_res["fields"].document_number), "doc_type": detected_doc_type}
    )

    # 5. Field & Chronological Validation
    validation_res = validation_service.validate_document_data(
        fields=ocr_raw_res["fields"],
        mrz_data=ocr_raw_res.get("mrz"),
        document_type=detected_doc_type
    )

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
    db.commit()

    # 6. Visual Forensics & Tamper Detection (ELA, Heatmap)
    tamper_res = tamper_detection_service.analyze_document(front_path, case_id=case_id)
    tamper_record = TamperResult(
        id=generate_uuid(),
        case_id=case_id,
        tampering_detected=tamper_res.tampering_detected,
        confidence=tamper_res.confidence,
        regions=[r.dict() for r in tamper_res.regions],
        signals=tamper_res.signals,
        heatmap_path=tamper_res.heatmap_url
    )
    db.add(tamper_record)
    db.commit()

    audit_service.record_event(
        db, case_id=case_id,
        actor_id="system_forensics",
        action="VISUAL_FORENSICS_COMPLETE",
        details={"tampering_detected": tamper_res.tampering_detected, "flagged_regions": len(tamper_res.regions)}
    )

    # 7. Identity & Biometric Face Verification
    face_res = face_verification_service.verify_document_and_person(
        document_image_path=front_path,
        live_person_image_path=live_path
    )
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
    db.commit()

    # 8. Record Verification Cross-Check
    doc_number = ocr_raw_res["fields"].document_number or (ocr_raw_res["mrz"].passport_number if ocr_raw_res.get("mrz") else "")
    record_res = record_verification_service.verify_record(
        document_number=doc_number,
        document_type=detected_doc_type,
        candidate_name=ocr_raw_res["fields"].name
    )
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
    db.commit()

    # 9 & 10. Multi-Signal Risk Fusion & Explainable AI
    from backend.app.models.schemas import OCRResultResponse
    ocr_response_obj = OCRResultResponse(
        raw_text=ocr_record.raw_text,
        fields=ocr_raw_res["fields"],
        mrz=ocr_raw_res.get("mrz"),
        confidence=ocr_record.confidence,
        bounding_boxes=ocr_raw_res.get("bounding_boxes", []),
        engine_used=ocr_record.engine_used
    )

    risk_assessment = risk_engine.evaluate(
        quality=quality_res,
        ocr=ocr_response_obj,
        validation=validation_res,
        tampering=tamper_res,
        face=face_res,
        record=record_res
    )

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

    # Update Case top-level status
    case.risk_score = risk_assessment.risk_score
    case.risk_level = risk_assessment.risk_level
    case.confidence = risk_assessment.confidence
    case.requires_human_review = (risk_assessment.risk_level in ("HIGH", "MEDIUM"))
    case.status = "REVIEW_REQUIRED" if case.requires_human_review else "COMPLETED"
    db.commit()

    # Log Final Risk Assessment Event into Cryptographic Audit Trail
    audit_service.record_event(
        db, case_id=case_id,
        actor_id="system_risk_engine",
        action="RISK_ASSESSMENT_FINALIZED",
        details={
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level,
            "requires_human_review": case.requires_human_review
        }
    )

    return {
        "case_id": case.id,
        "case_number": case.case_number,
        "document_type": case.document_type,
        "status": case.status,
        "risk_level": case.risk_level,
        "risk_score": case.risk_score,
        "confidence": case.confidence,
        "requires_human_review": case.requires_human_review,
        "recommendation": risk_assessment.recommended_action,
        "summary": explainability_service.generate_narrative_report(risk_assessment)
    }
