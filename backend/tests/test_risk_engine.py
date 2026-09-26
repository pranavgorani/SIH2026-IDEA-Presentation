import pytest
from backend.app.models.schemas import (
    ImageQualityResult, OCRResultResponse, ValidationSummary, ValidationCheck,
    TamperResultResponse, TamperRegion, FaceVerificationResponse, RecordVerificationResponse,
    ExtractedFields
)
from backend.app.services.risk_engine import risk_engine
from datetime import datetime, timezone

def test_clean_document_low_risk():
    quality = ImageQualityResult(quality_score=92.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(
        raw_text="...", fields=ExtractedFields(name="ALICE"), confidence=0.95, bounding_boxes=[], engine_used="test"
    )
    validation = ValidationSummary(valid=True, passed_count=5, failed_count=0, warning_count=0, checks=[])
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.90, regions=[], signals={})
    face = FaceVerificationResponse(
        document_face_detected=True, live_face_detected=True, document_face_quality=0.90,
        live_face_quality=0.88, similarity=0.89, status="MATCH_CONFIRMED", explanation="Match confirmed"
    )
    record = RecordVerificationResponse(
        record_found=True, status="VALID", document_number="K81927361", checked_at=datetime.now(timezone.utc)
    )

    assessment = risk_engine.evaluate(quality, ocr, validation, tampering, face, record)
    assert assessment.risk_level == "LOW"
    assert assessment.risk_score <= 30.0
    assert "Eligible for Standard Verification" in assessment.recommended_action
    assert len(assessment.positive_signals) >= 3

def test_tampered_document_high_risk():
    quality = ImageQualityResult(quality_score=85.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(
        raw_text="...", fields=ExtractedFields(name="TAMPERED"), confidence=0.75, bounding_boxes=[], engine_used="test"
    )
    validation = ValidationSummary(
        valid=False, passed_count=3, failed_count=2, warning_count=0,
        checks=[
            ValidationCheck(name="Expiry", status="FAIL", severity="HIGH", message="Expired"),
            ValidationCheck(name="MRZ", status="FAIL", severity="HIGH", message="Checksum mismatch")
        ]
    )
    tampering = TamperResultResponse(
        tampering_detected=True, confidence=0.92,
        regions=[TamperRegion(x=10, y=10, width=50, height=50, type="photo_replacement", confidence=0.92, explanation="Splice")],
        signals={}
    )
    face = FaceVerificationResponse(
        document_face_detected=True, live_face_detected=False, document_face_quality=0.8,
        live_face_quality=0.0, similarity=0.0, status="UNAVAILABLE", explanation="No live photo"
    )
    record = RecordVerificationResponse(
        record_found=False, status="REVOKED", document_number="TAMPER007", checked_at=datetime.now(timezone.utc)
    )

    assessment = risk_engine.evaluate(quality, ocr, validation, tampering, face, record)
    assert assessment.risk_level == "HIGH"
    assert assessment.risk_score >= 60.0
    assert "Mandatory Human Review" in assessment.recommended_action
    assert len(assessment.risk_factors) >= 3
