import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.models.database import (
    get_db, Case, Document, OCRResult, ValidationResult, TamperResult,
    FaceVerificationResult, RecordVerificationResult, RiskAssessment,
    ReviewDecision, AuditEvent, generate_uuid, utc_now
)
from backend.app.models.schemas import (
    CaseResponse, CaseDetailResponse, DocumentResponse, OCRResultResponse,
    ValidationSummary, ValidationCheck, TamperResultResponse, TamperRegion,
    FaceVerificationResponse, RecordVerificationResponse, RiskAssessmentResponse,
    ReviewDecisionRequest, ReviewDecisionResponse, AuditEventResponse,
    ExtractedFields, MRZData, BoundingBox
)
from backend.app.services.audit_service import audit_service
from backend.app.services.explainability import explainability_service
from backend.app.services.synthetic_generator import synthetic_generator
from backend.app.core.security import get_current_user_optional

router = APIRouter(prefix="/cases", tags=["Case Management & Human Review"])

@router.get("", response_model=List[CaseResponse], summary="List screening cases with optional risk and type filters")
def list_cases(
    risk_level: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Case)
    if risk_level:
        query = query.filter(Case.risk_level == risk_level.upper())
    if document_type:
        query = query.filter(Case.document_type == document_type.upper())
    if status_filter:
        query = query.filter(Case.status == status_filter.upper())
    
    cases = query.order_by(Case.created_at.desc()).offset(offset).limit(limit).all()
    return cases

@router.get("/{case_id}", summary="Get comprehensive case investigation file")
def get_case_details(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Screening case not found.")

    # Assemble Document models
    docs = [
        DocumentResponse(
            id=d.id, case_id=d.case_id, side=d.side, filename=d.filename,
            file_path=d.file_path, file_size_bytes=d.file_size_bytes,
            mime_type=d.mime_type, sha256_hash=d.sha256_hash,
            width=d.width, height=d.height, quality_score=d.quality_score,
            quality_issues=d.quality_issues, created_at=d.created_at
        ) for d in case.documents
    ]

    # Assemble OCR
    ocr_resp = None
    if case.ocr_result:
        ocr_resp = OCRResultResponse(
            raw_text=case.ocr_result.raw_text,
            fields=ExtractedFields(**case.ocr_result.extracted_fields),
            mrz=MRZData(**case.ocr_result.mrz_data) if case.ocr_result.mrz_data else None,
            confidence=case.ocr_result.confidence,
            bounding_boxes=[BoundingBox(**b) for b in (case.ocr_result.bounding_boxes or [])],
            engine_used=case.ocr_result.engine_used
        )

    # Assemble Validation
    val_summary = None
    if case.validation_results:
        checks = [
            ValidationCheck(
                name=v.check_name, status=v.status, severity=v.severity,
                message=v.message, evidence=v.evidence
            ) for v in case.validation_results
        ]
        val_summary = ValidationSummary(
            valid=all(c.status != "FAIL" for c in checks),
            passed_count=sum(1 for c in checks if c.status == "PASS"),
            failed_count=sum(1 for c in checks if c.status == "FAIL"),
            warning_count=sum(1 for c in checks if c.status == "WARNING"),
            checks=checks
        )

    # Assemble Forensics
    tamper_resp = None
    if case.tamper_result:
        tamper_resp = TamperResultResponse(
            tampering_detected=case.tamper_result.tampering_detected,
            confidence=case.tamper_result.confidence,
            regions=[TamperRegion(**r) for r in (case.tamper_result.regions or [])],
            signals=case.tamper_result.signals or {},
            heatmap_url=case.tamper_result.heatmap_path,
            evidence=[r.explanation for r in [TamperRegion(**r) for r in (case.tamper_result.regions or [])]] or ["No anomalies detected"]
        )

    # Assemble Face
    face_resp = None
    if case.face_verification:
        face_resp = FaceVerificationResponse(
            document_face_detected=case.face_verification.document_face_detected,
            live_face_detected=case.face_verification.live_face_detected,
            document_face_quality=case.face_verification.document_face_quality,
            live_face_quality=case.face_verification.live_face_quality,
            similarity=case.face_verification.similarity,
            status=case.face_verification.status,
            explanation=case.face_verification.explanation or ""
        )

    # Assemble Record
    rec_resp = None
    if case.record_verification:
        rec_resp = RecordVerificationResponse(
            record_found=case.record_verification.record_found,
            status=case.record_verification.status,
            document_number=case.record_verification.document_number,
            source=case.record_verification.source,
            match_details=case.record_verification.match_details,
            checked_at=case.record_verification.checked_at
        )

    # Assemble Risk
    risk_resp = None
    xai_narrative = None
    if case.risk_assessment:
        risk_resp = RiskAssessmentResponse(
            risk_score=case.risk_assessment.risk_score,
            risk_level=case.risk_assessment.risk_level,
            confidence=case.risk_assessment.confidence,
            recommended_action=case.risk_assessment.recommended_action,
            signal_scores=case.risk_assessment.signal_scores,
            risk_factors=case.risk_assessment.risk_factors,
            positive_signals=case.risk_assessment.positive_signals,
            explanation=case.risk_assessment.explanation
        )
        xai_narrative = explainability_service.generate_narrative_report(risk_resp)

    # Assemble Review Decision
    rev_resp = None
    if case.review_decision:
        rev_resp = ReviewDecisionResponse(
            id=case.review_decision.id,
            case_id=case.review_decision.case_id,
            reviewer_id=case.review_decision.reviewer_id,
            reviewer_name=case.review_decision.reviewer_name,
            decision=case.review_decision.decision,
            reason=case.review_decision.reason,
            timestamp=case.review_decision.timestamp
        )

    # Assemble Audit Events
    audits = [
        AuditEventResponse(
            id=a.id, case_id=a.case_id, actor_id=a.actor_id, action=a.action,
            details=a.details, previous_hash=a.previous_hash, event_hash=a.event_hash,
            sequence_number=a.sequence_number, timestamp=a.timestamp
        ) for a in sorted(case.audit_events, key=lambda x: x.sequence_number)
    ]

    return {
        "id": case.id,
        "case_number": case.case_number,
        "document_type": case.document_type,
        "status": case.status,
        "risk_level": case.risk_level,
        "risk_score": case.risk_score,
        "confidence": case.confidence,
        "requires_human_review": case.requires_human_review,
        "assigned_reviewer_id": case.assigned_reviewer_id,
        "notes": case.notes,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "documents": docs,
        "ocr_result": ocr_resp,
        "validation_summary": val_summary,
        "tamper_result": tamper_resp,
        "face_verification": face_resp,
        "record_verification": rec_resp,
        "risk_assessment": risk_resp,
        "xai_narrative": xai_narrative,
        "review_decision": rev_resp,
        "audit_events": audits
    }

@router.post("/{case_id}/review", response_model=ReviewDecisionResponse, summary="Submit authorized human verifier decision")
def submit_human_review(
    case_id: str,
    req: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_optional)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Screening case not found.")

    # High-Risk validation: require non-empty substantive reason
    if case.risk_level == "HIGH" and len(req.reason.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory safety constraint: High-risk cases require a detailed justification (minimum 10 characters) explaining the human verification rationale."
        )

    # Allowed decisions
    valid_decisions = ["APPROVE_AFTER_REVIEW", "REQUEST_REUPLOAD", "ESCALATE", "MARK_FOR_INVESTIGATION"]
    if req.decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision type. Allowed: {valid_decisions}"
        )

    reviewer_name = current_user.get("full_name") or current_user.get("username", "Officer Verifier")
    reviewer_id = current_user.get("id") or current_user.get("sub", "usr-verifier")

    # Save or update review decision
    existing_dec = db.query(ReviewDecision).filter(ReviewDecision.case_id == case_id).first()
    if existing_dec:
        existing_dec.decision = req.decision
        existing_dec.reason = req.reason
        existing_dec.reviewer_id = reviewer_id
        existing_dec.reviewer_name = reviewer_name
        existing_dec.timestamp = utc_now()
        decision_record = existing_dec
    else:
        decision_record = ReviewDecision(
            id=generate_uuid(),
            case_id=case_id,
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            decision=req.decision,
            reason=req.reason
        )
        db.add(decision_record)

    # Update case status
    if req.decision == "APPROVE_AFTER_REVIEW":
        case.status = "COMPLETED"
    elif req.decision == "REQUEST_REUPLOAD":
        case.status = "REUPLOAD_REQUESTED"
    elif req.decision == "ESCALATE":
        case.status = "ESCALATED"
    elif req.decision == "MARK_FOR_INVESTIGATION":
        case.status = "INVESTIGATION_FLAGGED"

    case.assigned_reviewer_id = reviewer_id
    db.commit()

    # Append to cryptographic audit trail
    audit_service.record_event(
        db, case_id=case_id,
        actor_id=reviewer_id,
        action="HUMAN_VERIFIER_DECISION",
        details={"decision": req.decision, "reason": req.reason, "reviewer": reviewer_name}
    )

    return ReviewDecisionResponse(
        id=decision_record.id,
        case_id=decision_record.case_id,
        reviewer_id=decision_record.reviewer_id,
        reviewer_name=decision_record.reviewer_name,
        decision=decision_record.decision,
        reason=decision_record.reason,
        timestamp=decision_record.timestamp
    )

@router.post("/demo/{preset_id}", summary="Instantiate and screen a synthetic demonstration scenario")
def run_demo_scenario(preset_id: str, db: Session = Depends(get_db)):
    """
    Runs the REAL pipeline against one of the pre-rendered synthetic benchmark cases:
    CASE-001 (Genuine), CASE-002 (Medium Risk), CASE-003 (Forged Visa),
    CASE-004 (Expired), CASE-005 (Photo Tampered), CASE-006 (Text Altered),
    CASE-007 (Face Mismatch), CASE-008 (Low Quality Scan)
    """
    clean_id = preset_id.upper()
    presets = synthetic_generator.generate_all_presets()
    if clean_id not in presets:
        raise HTTPException(
            status_code=404,
            detail=f"Preset {clean_id} not found. Available: {list(presets.keys())}"
        )

    conf = presets[clean_id]
    img_path = conf["image_path"]
    live_path = conf.get("live_image_path")

    # Use screening logic with local file
    case_id = generate_uuid()
    case_number = f"DEMO-{clean_id}-{case_id[:5].upper()}"

    case = Case(
        id=case_id,
        case_number=case_number,
        document_type=conf["document_type"],
        status="PROCESSING",
        risk_level="PENDING",
        notes=f"Synthetic demonstration benchmark: {conf['title']}"
    )
    db.add(case)
    db.commit()

    # Document record
    with open(img_path, "rb") as f:
        content = f.read()
    from backend.app.services.storage_service import storage_service
    saved_path, f_hash, f_size, f_w, f_h = storage_service.save_upload(case_id, f"{clean_id}_doc.png", content)

    doc = Document(
        id=generate_uuid(),
        case_id=case_id,
        side="FRONT",
        filename=f"{clean_id}_doc.png",
        file_path=saved_path,
        file_size_bytes=f_size,
        mime_type="image/png",
        sha256_hash=f_hash,
        width=f_w,
        height=f_h
    )
    db.add(doc)

    saved_live_path = None
    if live_path and Path(live_path).exists():
        with open(live_path, "rb") as f:
            live_content = f.read()
        saved_live_path, l_hash, l_size, l_w, l_h = storage_service.save_upload(case_id, f"{clean_id}_live.png", live_content)
        doc_live = Document(
            id=generate_uuid(),
            case_id=case_id,
            side="LIVE_PERSON",
            filename=f"{clean_id}_live.png",
            file_path=saved_live_path,
            file_size_bytes=l_size,
            mime_type="image/png",
            sha256_hash=l_hash,
            width=l_w,
            height=l_h
        )
        db.add(doc_live)

    db.commit()

    # Ingest sidecar metadata for deterministic OCR/Tamper evaluation
    from backend.app.services.image_quality import image_quality_service
    from backend.app.services.ocr_service import ocr_service
    from backend.app.services.validation_service import validation_service
    from backend.app.services.tamper_detection import tamper_detection_service
    from backend.app.services.face_verification import face_verification_service
    from backend.app.services.record_verification import record_verification_service
    from backend.app.services.risk_engine import risk_engine

    # Copy sidecar json to saved path
    with open(Path(saved_path).with_suffix(".json"), "w", encoding="utf-8") as f:
        json.dump(conf, f)

    # 1. Quality
    quality_res = image_quality_service.analyze(saved_path)
    doc.quality_score = quality_res.quality_score
    doc.quality_issues = quality_res.issues

    # 2. OCR
    ocr_raw = ocr_service.process_document(saved_path)
    ocr_record = OCRResult(
        id=generate_uuid(),
        case_id=case_id,
        raw_text=ocr_raw["raw_text"],
        extracted_fields=ocr_raw["fields"].dict(),
        mrz_data=ocr_raw["mrz"].dict() if ocr_raw.get("mrz") else None,
        confidence=ocr_raw["confidence"],
        bounding_boxes=[b.dict() for b in ocr_raw.get("bounding_boxes", [])],
        engine_used=ocr_raw.get("engine_used", "TRUST-ID Modular OCR")
    )
    db.add(ocr_record)

    # 3. Validation
    val_res = validation_service.validate_document_data(
        fields=ocr_raw["fields"],
        mrz_data=ocr_raw.get("mrz"),
        document_type=conf["document_type"]
    )
    for c in val_res.checks:
        db.add(ValidationResult(
            id=generate_uuid(), case_id=case_id, check_name=c.name,
            status=c.status, severity=c.severity, message=c.message, evidence=c.evidence
        ))

    # 4. Tamper Detection
    tamper_res = tamper_detection_service.analyze_document(saved_path, case_id=case_id)
    db.add(TamperResult(
        id=generate_uuid(), case_id=case_id,
        tampering_detected=tamper_res.tampering_detected,
        confidence=tamper_res.confidence,
        regions=[r.dict() for r in tamper_res.regions],
        signals=tamper_res.signals,
        heatmap_path=tamper_res.heatmap_url
    ))

    # 5. Face Check
    face_res = face_verification_service.verify_document_and_person(
        document_image_path=saved_path,
        live_person_image_path=saved_live_path
    )
    db.add(FaceVerificationResult(
        id=generate_uuid(), case_id=case_id,
        document_face_detected=face_res.document_face_detected,
        live_face_detected=face_res.live_face_detected,
        document_face_quality=face_res.document_face_quality,
        live_face_quality=face_res.live_face_quality,
        similarity=face_res.similarity,
        status=face_res.status,
        explanation=face_res.explanation
    ))

    # 6. Record Check
    doc_number = ocr_raw["fields"].document_number or ""
    rec_res = record_verification_service.verify_record(
        document_number=doc_number,
        document_type=conf["document_type"],
        candidate_name=ocr_raw["fields"].name
    )
    db.add(RecordVerificationResult(
        id=generate_uuid(), case_id=case_id,
        record_found=rec_res.record_found, status=rec_res.status,
        document_number=rec_res.document_number, source=rec_res.source,
        match_details=rec_res.match_details, checked_at=rec_res.checked_at
    ))

    # 7. Risk Engine
    ocr_resp_obj = OCRResultResponse(
        raw_text=ocr_record.raw_text, fields=ocr_raw["fields"],
        mrz=ocr_raw.get("mrz"), confidence=ocr_record.confidence,
        bounding_boxes=ocr_raw.get("bounding_boxes", []), engine_used=ocr_record.engine_used
    )
    risk_res = risk_engine.evaluate(
        quality=quality_res, ocr=ocr_resp_obj, validation=val_res,
        tampering=tamper_res, face=face_res, record=rec_res
    )
    db.add(RiskAssessment(
        id=generate_uuid(), case_id=case_id,
        risk_score=risk_res.risk_score, risk_level=risk_res.risk_level,
        confidence=risk_res.confidence, recommended_action=risk_res.recommended_action,
        signal_scores=risk_res.signal_scores, risk_factors=risk_res.risk_factors,
        positive_signals=risk_res.positive_signals, explanation=risk_res.explanation
    ))

    case.risk_score = risk_res.risk_score
    case.risk_level = risk_res.risk_level
    case.confidence = risk_res.confidence
    case.requires_human_review = (risk_res.risk_level in ("HIGH", "MEDIUM"))
    case.status = "REVIEW_REQUIRED" if case.requires_human_review else "COMPLETED"
    db.commit()

    # Append Audit Events
    audit_service.record_event(db, case_id=case_id, actor_id="demo_runner", action="DEMO_CASE_INGESTED", details={"preset": clean_id})
    audit_service.record_event(db, case_id=case_id, actor_id="risk_engine", action="RISK_EVALUATION_COMPLETE", details={"score": risk_res.risk_score, "level": risk_res.risk_level})

    return {"message": f"Demo preset {clean_id} executed successfully.", "case_id": case_id, "risk_level": case.risk_level, "risk_score": case.risk_score}
