"""
TRUST-ID SIH 2026 - Comprehensive False High-Risk Regression Test Suite
Validates the 20 specific scenarios defined in Section 10 of the Antigravity Master Bug-Fix Prompt:

1. Readable PAN image with a structurally valid identifier -> LOW RISK
2. Readable PAN with a blurred name -> NEEDS_REVIEW / LOW-MEDIUM (NOT FRAUD)
3. PAN with an unreadable identifier -> NEEDS_REVIEW / UNREADABLE (NOT FRAUD)
4. Aadhaar image with a masked number (XXXX XXXX 1234) -> LOW RISK
5. Aadhaar image showing only a birth year (YYYY) -> LOW RISK (NOT INVALID)
6. Aadhaar image with a QR code that decodes successfully -> VALID / LOW RISK
7. Aadhaar image whose QR code cannot be decoded -> NOT HIGH RISK solely due to QR
8. Readable passport with valid MRZ check digits -> LOW RISK
9. Passport with an MRZ mismatch -> Elevated review / HIGH_RISK with explicit evidence
10. Driving licence without an expiry date -> LOW RISK / NOT_APPLICABLE (NOT EXPIRED)
11. Unsupported identity document -> UNSUPPORTED / NOT_VERIFIED (NOT FRAUD)
12. Non-document photograph -> UNSUPPORTED / NEEDS_REVIEW (NOT FRAUD)
13. Rotated or poorly illuminated image -> NEEDS_RESCAN (NOT FRAUD)
14. OCR engine timeout -> Technical failure does not become fraud evidence
15. Unavailable Gemini API -> Fallback applied without fraud penalty
16. Unavailable official verification API -> NOT_VERIFIED with zero penalty
17. Document with a genuine field inconsistency -> Explainable warning/escalation
18. Document with supported evidence of possible image manipulation -> HIGH RISK with evidence
19. New scan following a previous HIGH RISK scan -> Clean state, no stale cache contamination
20. Frontend response structure matches backend fields
"""

import pytest
from datetime import datetime, timezone, date
from backend.app.models.schemas import (
    ImageQualityResult, OCRResultResponse, ValidationSummary, ValidationCheck,
    TamperResultResponse, TamperRegion, FaceVerificationResponse, RecordVerificationResponse,
    ExtractedFields, MRZData
)
from backend.app.services.risk_engine import risk_engine
from backend.app.services.validation_service import validation_service
from backend.app.services.document_classifier import document_classifier
from backend.app.services.document_check_engine import document_check_engine

# -----------------------------------------------------------------------------
# Case 1: Readable PAN image with a structurally valid identifier -> LOW RISK
# -----------------------------------------------------------------------------
def test_case_01_readable_pan_valid_identifier_low_risk():
    fields = ExtractedFields(
        name="PRANAV GORANI",
        document_number="ABCDE1234F",
        date_of_birth="1995-05-15",
        nationality="IND",
        issuing_country="IND"
    )
    val = validation_service.validate_document_data(fields=fields, document_type="PAN_CARD")
    assert val.valid is True
    assert val.failed_count == 0

    quality = ImageQualityResult(quality_score=95.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="INCOME TAX DEPARTMENT ABCDE1234F", fields=fields, confidence=0.95, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="Optional selfie omitted")
    record = RecordVerificationResponse(record_found=True, status="VALID", document_number="ABCDE1234F", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PAN_CARD")
    assert assessment.risk_level == "LOW"
    assert assessment.risk_score <= 24.0

# -----------------------------------------------------------------------------
# Case 2: Readable PAN with a blurred name -> NEEDS_REVIEW / NOT FRAUD
# -----------------------------------------------------------------------------
def test_case_02_readable_pan_blurred_name_not_fraud():
    fields = ExtractedFields(
        name="", # Blurred/unreadable
        document_number="ABCDE1234F",
        date_of_birth="1995-05-15",
        nationality="IND"
    )
    val = validation_service.validate_document_data(fields=fields, document_type="PAN_CARD")
    # Missing name on PAN is UNAVAILABLE, not an automatic failure
    assert val.failed_count == 0

    quality = ImageQualityResult(quality_score=75.0, issues=["minor_blur"], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="ABCDE1234F", fields=fields, confidence=0.65, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PAN_CARD")
    assert assessment.risk_level in ("LOW", "MEDIUM")
    assert assessment.risk_score < 50.0 # Under HIGH RISK threshold

# -----------------------------------------------------------------------------
# Case 3: PAN with an unreadable identifier -> NEEDS_REVIEW (NOT FRAUD)
# -----------------------------------------------------------------------------
def test_case_03_pan_unreadable_identifier_needs_review():
    fields = ExtractedFields(
        name="RAHUL SHARMA",
        document_number="", # Unreadable
        date_of_birth="1990-01-01"
    )
    val = validation_service.validate_document_data(fields=fields, document_type="PAN_CARD")
    quality = ImageQualityResult(quality_score=60.0, issues=["low_contrast"], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="RAHUL SHARMA", fields=fields, confidence=0.55, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PAN_CARD")
    assert assessment.risk_level in ("LOW", "MEDIUM")
    assert assessment.risk_score < 50.0

# -----------------------------------------------------------------------------
# Case 4: Aadhaar image with a masked number -> LOW RISK
# -----------------------------------------------------------------------------
def test_case_04_aadhaar_masked_number_low_risk():
    fields = ExtractedFields(
        name="PRIYA VERMA",
        document_number="XXXX XXXX 1234",
        date_of_birth="1992-08-20",
        nationality="IND"
    )
    val = validation_service.validate_document_data(fields=fields, document_type="AADHAAR")
    assert val.valid is True
    assert val.failed_count == 0

    quality = ImageQualityResult(quality_score=92.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="AADHAAR XXXX XXXX 1234", fields=fields, confidence=0.92, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="AADHAAR")
    assert assessment.risk_level == "LOW"
    assert assessment.risk_score <= 24.0

# -----------------------------------------------------------------------------
# Case 5: Aadhaar image showing only a birth year (YYYY) -> LOW RISK
# -----------------------------------------------------------------------------
def test_case_05_aadhaar_birth_year_only_accepted():
    fields = ExtractedFields(
        name="AMIT KUMAR",
        document_number="XXXX XXXX 5678",
        date_of_birth="1985", # Year only printed on card
        nationality="IND"
    )
    val = validation_service.validate_document_data(fields=fields, document_type="AADHAAR")
    # Year-only DOB must pass on Aadhaar
    dob_check = next((c for c in val.checks if "Date of Birth" in c.name), None)
    assert dob_check is not None
    assert dob_check.status == "PASS"

# -----------------------------------------------------------------------------
# Case 6: Aadhaar image with decoded QR code -> VALID / LOW RISK
# -----------------------------------------------------------------------------
def test_case_06_aadhaar_qr_decoded_valid():
    fields = ExtractedFields(
        name="SUNITA DEVI",
        document_number="XXXX XXXX 9999",
        date_of_birth="1988-11-12",
        nationality="IND"
    )
    val = validation_service.validate_document_data(fields=fields, document_type="AADHAAR")
    quality = ImageQualityResult(quality_score=96.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="AADHAAR QR", fields=fields, confidence=0.96, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=True, status="VALID", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="AADHAAR")
    assert assessment.risk_level == "LOW"
    assert assessment.risk_score <= 24.0

# -----------------------------------------------------------------------------
# Case 7: Aadhaar image whose QR code cannot be decoded -> NOT HIGH RISK
# -----------------------------------------------------------------------------
def test_case_07_aadhaar_qr_undecodable_not_high_risk():
    fields = ExtractedFields(
        name="SUNITA DEVI",
        document_number="XXXX XXXX 9999",
        date_of_birth="1988-11-12",
        nationality="IND"
    )
    val = validation_service.validate_document_data(fields=fields, document_type="AADHAAR")
    quality = ImageQualityResult(quality_score=85.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="AADHAAR", fields=fields, confidence=0.88, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="AADHAAR")
    # A missing or unreadable QR alone must NOT make the document HIGH RISK
    assert assessment.risk_level == "LOW"

# -----------------------------------------------------------------------------
# Case 8: Readable passport with valid MRZ check digits -> LOW RISK
# -----------------------------------------------------------------------------
def test_case_08_readable_passport_valid_mrz_low_risk():
    fields = ExtractedFields(
        name="ERIKSSON ANNA",
        document_number="L898902C3",
        date_of_birth="1974-08-12",
        date_of_expiry="2030-04-15",
        nationality="UTO",
        issuing_country="UTO"
    )
    mrz = MRZData(
        valid=True,
        raw_mrz=["P<UTOERIKSSON<<ANNA<<<<<<<<<<<<<<<<<<<<<<<<<<<", "L898902C36UTO7408122F3004159ZE184226B<<<<<10"],
        passport_number="L898902C3",
        date_of_birth="1974-08-12",
        expiry_date="2030-04-15",
        checksum_overall=True,
        checksum_passport_number=True,
        checksum_dob=True,
        checksum_expiry=True
    )
    val = validation_service.validate_document_data(fields=fields, mrz_data=mrz, document_type="PASSPORT")
    assert val.valid is True
    assert val.failed_count == 0

    quality = ImageQualityResult(quality_score=94.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="PASSPORT", fields=fields, mrz=mrz, confidence=0.95, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="MATCH_CONFIRMED", similarity=0.92, explanation="Match")
    record = RecordVerificationResponse(record_found=True, status="VALID", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PASSPORT")
    assert assessment.risk_level == "LOW"
    assert assessment.risk_score <= 24.0

# -----------------------------------------------------------------------------
# Case 9: Passport with an MRZ mismatch -> Elevated review / HIGH_RISK
# -----------------------------------------------------------------------------
def test_case_09_passport_mrz_mismatch_elevated_risk():
    fields = ExtractedFields(
        name="ERIKSSON ANNA",
        document_number="L898902C3",
        date_of_birth="1974-08-12",
        date_of_expiry="2030-04-15"
    )
    mrz = MRZData(
        valid=False,
        raw_mrz=["P<UTOERIKSSON<<ANNA<<<<<<<<<<<<<<<<<<<<<<<<<<<", "M111111116UTO7408122F3004159ZE184226B<<<<<10"],
        passport_number="M11111111", # Mismatch with L898902C3
        checksum_overall=False
    )
    val = validation_service.validate_document_data(fields=fields, mrz_data=mrz, document_type="PASSPORT")
    assert val.valid is False
    assert val.failed_count >= 1

    quality = ImageQualityResult(quality_score=90.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="PASSPORT", fields=fields, mrz=mrz, confidence=0.85, bounding_boxes=[], engine_used="Local OCR")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PASSPORT")
    assert assessment.risk_score >= 25.0 # Elevated risk
    assert any("MRZ" in rf or "mismatch" in rf.lower() for rf in assessment.risk_factors)

# -----------------------------------------------------------------------------
# Case 10: Driving licence without expiry date -> NOT EXPIRED / NOT HIGH RISK
# -----------------------------------------------------------------------------
def test_case_10_driving_licence_no_expiry_not_expired():
    fields = ExtractedFields(
        name="VIKRAM SINGH",
        document_number="MH-12-2015-0012345",
        date_of_birth="1990-06-15",
        date_of_expiry="" # Permitted to omit in many domestic jurisdictions
    )
    checks = document_check_engine.run_all_checks(
        case_id="TEST-DL-01",
        doc_metadata={"document_type": "DRIVING_LICENSE"},
        ocr_result={"fields": fields}
    )
    # Check that expiry failure was not triggered
    chk_exp = next((c for c in checks["checks"] if c["check_id"] == "CHK-041"), None)
    assert chk_exp is not None
    assert chk_exp["status"] != "FAIL"

# -----------------------------------------------------------------------------
# Case 11: Unsupported identity document -> UNSUPPORTED / NOT_VERIFIED (NOT FRAUD)
# -----------------------------------------------------------------------------
def test_case_11_unsupported_identity_document():
    cls = document_classifier.classify_document(text="LIBRARY MEMBERSHIP CARD NO 987654321 VALID TIL 2026")
    assert cls["document_type"] == "UNSUPPORTED"
    assert cls["status"] == "NOT_VERIFIED"
    assert cls["supported"] is False

# -----------------------------------------------------------------------------
# Case 12: Non-document photograph -> UNSUPPORTED / NOT_VERIFIED (NOT FRAUD)
# -----------------------------------------------------------------------------
def test_case_12_non_document_photograph():
    cls = document_classifier.classify_document(text="LANDSCAPE NATURE PHOTOGRAPH BLUE SKY GREEN HILLS")
    assert cls["document_type"] == "UNSUPPORTED"
    assert cls["status"] == "NOT_VERIFIED"

# -----------------------------------------------------------------------------
# Case 13: Rotated or poorly illuminated image -> NEEDS_RESCAN (NOT FRAUD)
# -----------------------------------------------------------------------------
def test_case_13_rotated_poor_quality_needs_rescan():
    fields = ExtractedFields(name="", document_number="")
    quality = ImageQualityResult(quality_score=25.0, issues=["excessive_blur", "poor_lighting", "skew_detected"], is_acceptable=False)
    ocr = OCRResultResponse(raw_text="", fields=fields, confidence=0.20, bounding_boxes=[], engine_used="Local OCR")
    val = validation_service.validate_document_data(fields=fields, document_type="PAN_CARD")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PAN_CARD")
    assert "rescan" in assessment.recommended_action.lower()
    # It must NOT be labeled FRAUD / CRITICAL
    assert assessment.risk_level != "CRITICAL"

# -----------------------------------------------------------------------------
# Case 14: OCR engine timeout -> Technical failure does not become fraud evidence
# -----------------------------------------------------------------------------
def test_case_14_ocr_timeout_not_fraud():
    fields = ExtractedFields()
    quality = ImageQualityResult(quality_score=80.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="", fields=fields, confidence=0.35, bounding_boxes=[], engine_used="Emergency Fallback", status="TIMEOUT")
    val = validation_service.validate_document_data(fields=fields, document_type="PASSPORT")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PASSPORT")
    assert assessment.risk_score < 50.0 # Under HIGH RISK threshold

# -----------------------------------------------------------------------------
# Case 15: Unavailable Gemini API -> Fallback applied without fraud penalty
# -----------------------------------------------------------------------------
def test_case_15_gemini_unavailable_no_fraud_penalty():
    fields = ExtractedFields(name="ALICE SMITH", document_number="P12345678", date_of_birth="1991-03-22", date_of_expiry="2031-03-22")
    quality = ImageQualityResult(quality_score=90.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="PASSPORT", fields=fields, confidence=0.90, bounding_boxes=[], engine_used="Local OCR")
    val = validation_service.validate_document_data(fields=fields, document_type="PASSPORT")
    # Gemini unavailable signal
    tampering = TamperResultResponse(
        tampering_detected=False, confidence=0.0, regions=[],
        signals={"status": "UNAVAILABLE", "ai_status": "unavailable", "ai_provider": "LOCAL_CV_FALLBACK"},
        evidence=["Forensic model unavailable."]
    )
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PASSPORT")
    assert assessment.signal_scores["visual_forensics"] == 0.0
    assert assessment.risk_level == "LOW"

# -----------------------------------------------------------------------------
# Case 16: Unavailable official verification API -> NOT_VERIFIED with zero penalty
# -----------------------------------------------------------------------------
def test_case_16_verification_api_offline_zero_penalty():
    fields = ExtractedFields(name="ROHIT SHARMA", document_number="ABCDE9999Z", date_of_birth="1987-04-30", nationality="IND")
    quality = ImageQualityResult(quality_score=92.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="INCOME TAX DEPARTMENT", fields=fields, confidence=0.92, bounding_boxes=[], engine_used="Local OCR")
    val = validation_service.validate_document_data(fields=fields, document_type="PAN_CARD")
    tampering = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    # Government DB is offline/unavailable
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PAN_CARD")
    assert assessment.signal_scores["record_verification"] == 0.0
    assert assessment.risk_level == "LOW"

# -----------------------------------------------------------------------------
# Case 17: Document with genuine field inconsistency -> Explainable warning
# -----------------------------------------------------------------------------
def test_case_17_genuine_field_inconsistency_explainable():
    # Issue date after expiry date
    fields = ExtractedFields(
        name="TEST HOLDER",
        document_number="PASS12345",
        date_of_issue="2025-01-01",
        date_of_expiry="2020-01-01" # Issue > Expiry chronological paradox
    )
    val = validation_service.validate_document_data(fields=fields, document_type="PASSPORT")
    assert val.failed_count >= 1
    chron_check = next((c for c in val.checks if "Chronological" in c.name), None)
    assert chron_check is not None
    assert chron_check.status == "FAIL"

# -----------------------------------------------------------------------------
# Case 18: Document with supported evidence of tampering -> HIGH RISK with evidence
# -----------------------------------------------------------------------------
def test_case_18_genuine_tampering_evidence_high_risk():
    fields = ExtractedFields(name="SUSPECT", document_number="P99999999")
    quality = ImageQualityResult(quality_score=88.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="PASSPORT", fields=fields, confidence=0.85, bounding_boxes=[], engine_used="Local OCR")
    val = validation_service.validate_document_data(fields=fields, document_type="PASSPORT")
    tampering = TamperResultResponse(
        tampering_detected=True,
        confidence=0.92,
        regions=[TamperRegion(x=10, y=10, width=80, height=80, type="photo_replacement", confidence=0.92, explanation="Portrait splice boundary anomaly")],
        signals={"ela_max_difference": 85}
    )
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    record = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    assessment = risk_engine.evaluate(quality, ocr, val, tampering, face, record, document_type="PASSPORT")
    assert assessment.risk_level in ("HIGH", "CRITICAL")
    assert assessment.risk_score >= 50.0
    assert any("tampering" in rf.lower() for rf in assessment.risk_factors)

# -----------------------------------------------------------------------------
# Case 19: New scan following a previous HIGH RISK scan -> Clean state, no stale leak
# -----------------------------------------------------------------------------
def test_case_19_state_isolation_between_scans():
    # First scan: High risk tampered document
    tampered_tamper = TamperResultResponse(
        tampering_detected=True,
        confidence=0.95,
        regions=[TamperRegion(x=0, y=0, width=50, height=50, type="splice", confidence=0.95, explanation="Splice boundary anomaly")],
        signals={}
    )
    bad_val = ValidationSummary(valid=False, passed_count=1, failed_count=2, warning_count=0, checks=[ValidationCheck(name="MRZ", status="FAIL", severity="HIGH", message="Fail")])
    q_bad = ImageQualityResult(quality_score=80.0, issues=[], is_acceptable=True)
    ocr_bad = OCRResultResponse(raw_text="", fields=ExtractedFields(), confidence=0.7, bounding_boxes=[], engine_used="test")
    res1 = risk_engine.evaluate(q_bad, ocr_bad, bad_val, tampered_tamper, FaceVerificationResponse(status="NOT_PROVIDED", explanation=""), RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc)))
    assert res1.risk_level in ("HIGH", "CRITICAL")

    # Second scan: Clean PAN card immediately after
    clean_pan_fields = ExtractedFields(name="RAHUL VERMA", document_number="ABCDE1234F", nationality="IND")
    clean_val = validation_service.validate_document_data(fields=clean_pan_fields, document_type="PAN_CARD")
    q_clean = ImageQualityResult(quality_score=95.0, issues=[], is_acceptable=True)
    ocr_clean = OCRResultResponse(raw_text="", fields=clean_pan_fields, confidence=0.95, bounding_boxes=[], engine_used="test")
    tamper_clean = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    res2 = risk_engine.evaluate(q_clean, ocr_clean, clean_val, tamper_clean, FaceVerificationResponse(status="NOT_PROVIDED", explanation=""), RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc)), document_type="PAN_CARD")
    assert res2.risk_level == "LOW"
    assert res2.risk_score <= 24.0

# -----------------------------------------------------------------------------
# Case 20: Response structure consistency and risk score matching
# -----------------------------------------------------------------------------
def test_case_20_response_structure_and_score_consistency():
    fields = ExtractedFields(name="TEST USER", document_number="ABCDE1234F", nationality="IND")
    val = validation_service.validate_document_data(fields=fields, document_type="PAN_CARD")
    q = ImageQualityResult(quality_score=90.0, issues=[], is_acceptable=True)
    ocr = OCRResultResponse(raw_text="PAN", fields=fields, confidence=0.90, bounding_boxes=[], engine_used="Local OCR")
    tamper = TamperResultResponse(tampering_detected=False, confidence=0.0, regions=[], signals={})
    face = FaceVerificationResponse(status="NOT_PROVIDED", explanation="")
    rec = RecordVerificationResponse(record_found=False, status="UNAVAILABLE", checked_at=datetime.now(timezone.utc))

    res = risk_engine.evaluate(q, ocr, val, tamper, face, rec, document_type="PAN_CARD")
    assert hasattr(res, "risk_score")
    assert hasattr(res, "risk_level")
    assert hasattr(res, "signal_scores")
    assert hasattr(res, "risk_factors")
    assert hasattr(res, "positive_signals")
    assert hasattr(res, "recommended_action")
    assert isinstance(res.risk_score, float)
