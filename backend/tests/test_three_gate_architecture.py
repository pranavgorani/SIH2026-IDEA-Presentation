"""
TRUST-ID SIH 2026 - Comprehensive 3-Gate Deterministic-First Architecture Test Suite
Validates:
1. Step 0: Ingestion & Pre-Flight Normalization (preprocessor.py)
   - Auto-orientation & width standardizing to 1000px preserving aspect ratio
   - Specular laminate glare suppression (LAB CLAHE & HSV V>245, S<15 mask)
   - Zero-Click Auto-Router (Passport, PAN, Aadhaar, Visa)
2. Gate 1: Deterministic Clarity Engine (gate1_validator.py)
   - PAN card format, 4th char entity check, logical DOB
   - Aadhaar 12-digit format, leading digit [2-9], Verhoeff checksum, privacy masking
   - Passport & Visa ICAO 9303 Modulo-10 checksums [7, 3, 1], VIZ-to-MRZ cross-check, chronological dates
   - QR payload cross-verification
   - Structural Trust Baseline calibration flag
3. Gate 2: Differential ROI Forensics & Biometrics (gate2_forensics.py)
   - ROI segmentation (Face, Text, Background)
   - Edge dilation masking & differential Z-score calibration (ΔZ <= 1.8 clean, 1.8-2.6 minor, > 2.6 splicing)
   - Biometric 1:1 face verification & 1:N recycled multi-identity fraud detector
4. Gate 3: Calibrated Multi-Gate Scorer (gate3_scorer.py)
   - Golden Rule 1: Valid documents pass as LOW RISK (0-30, GREEN)
   - Golden Rule 2: Global noise or missing EXIF never triggers HIGH RISK
   - Golden Rule 3: High Risk (66-100, RED) only on Gate 1 or Gate 2 differential failures
   - Review Band (31-65, YELLOW) on borderline anomalies
"""

import pytest
import numpy as np
import cv2
from datetime import date
from backend.app.services.preprocessor import document_preprocessor, DocumentPreprocessor
from backend.app.services.gate1_validator import (
    gate1_validator, validate_verhoeff, compute_verhoeff_check_digit,
    calculate_icao_mod10
)
from backend.app.services.gate2_forensics import gate2_forensics
from backend.app.services.gate3_scorer import gate3_scorer


# =============================================================================
# STEP 0: PREPROCESSOR TESTS
# =============================================================================
class TestStep0Preprocessor:
    def test_aspect_ratio_normalization_to_1000px(self):
        # 1600x1200 image -> normalized width should be 1000px, aspect preserved
        dummy_img = np.ones((1200, 1600, 3), dtype=np.uint8) * 200
        normalized, scale = document_preprocessor.normalize_aspect_and_size(dummy_img)

        assert normalized.shape[1] == 1000
        assert normalized.shape[0] == 750
        assert abs(scale - (1000.0 / 1600.0)) < 1e-4

    def test_specular_glare_masking_and_suppression(self):
        # Image with synthetic laminate glare (V > 245, S < 15 in HSV = bright white glare)
        dummy_img = np.ones((750, 1000, 3), dtype=np.uint8) * 120
        # Inject bright glare patch in center
        dummy_img[300:360, 400:480] = 255

        damped, glare_mask, stats = document_preprocessor.suppress_specular_glare(dummy_img)
        assert stats["glare_detected"] is True
        assert stats["glare_pixel_count"] > 0
        assert glare_mask[320, 420] == 255
        # Background areas should not be flagged as glare
        assert glare_mask[100, 100] == 0

    def test_zero_click_auto_router_passport(self):
        text = "REPUBLIC OF INDIA PASSPORT P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<"
        res = document_preprocessor.auto_route_document(raw_text=text)
        assert res["document_type"] == "PASSPORT"
        assert res["is_supported"] is True
        assert res["requires_mrz"] is True

    def test_zero_click_auto_router_pan(self):
        text = "INCOME TAX DEPARTMENT GOVT OF INDIA PERMANENT ACCOUNT NUMBER ABCDE1234F"
        res = document_preprocessor.auto_route_document(raw_text=text)
        assert res["document_type"] == "PAN"
        assert res["requires_mrz"] is False

    def test_zero_click_auto_router_aadhaar(self):
        text = "GOVERNMENT OF INDIA UNIQUE IDENTIFICATION AUTHORITY OF INDIA 2345 6789 0123"
        res = document_preprocessor.auto_route_document(raw_text=text)
        assert res["document_type"] == "AADHAAR"
        assert res["requires_mrz"] is False

    def test_zero_click_auto_router_visa(self):
        text = "REPUBLIC OF INDIA VISA ENTRY PERMIT TYPE TOURIST"
        res = document_preprocessor.auto_route_document(raw_text=text)
        assert res["document_type"] == "VISA_OR_PERMIT"


# =============================================================================
# GATE 1: DETERMINISTIC CLARITY TESTS
# =============================================================================
class TestGate1DeterministicClarity:
    def test_pan_valid_syntax_and_entity(self):
        # Valid individual PAN (4th char 'P')
        res = gate1_validator.validate_pan("ABCPE1234F", dob_str="1992-06-18")
        assert res["valid"] is True
        assert res["entity_type"] == "P"
        assert res["trust_bonus"] >= 25
        assert len(res["failed_rules"]) == 0

    def test_pan_invalid_syntax(self):
        res = gate1_validator.validate_pan("INVALID_PAN", dob_str="1990-01-01")
        assert res["valid"] is False
        assert any("violates" in r for r in res["failed_rules"])

    def test_pan_future_dob_fails(self):
        future_year = date.today().year + 5
        res = gate1_validator.validate_pan("ABCPE1234F", dob_str=f"{future_year}-01-01")
        assert res["valid"] is False
        assert any("out of realistic range" in r for r in res["failed_rules"])

    def test_aadhaar_verhoeff_algorithm(self):
        # Compute valid Verhoeff 12-digit number
        prefix_11 = "29471829381"
        check_digit = compute_verhoeff_check_digit(prefix_11)
        valid_uid = f"{prefix_11}{check_digit}"

        assert validate_verhoeff(valid_uid) is True
        # Alter last digit -> must fail checksum
        tampered_uid = f"{prefix_11}{(check_digit + 1) % 10}"
        assert validate_verhoeff(tampered_uid) is False

        # Validate through Gate 1 validator
        res = gate1_validator.validate_aadhaar(valid_uid, dob_str="1995-10-20")
        assert res["valid"] is True
        assert res["masked_identifier"] == f"XXXX-XXXX-{valid_uid[-4:]}"
        assert res["trust_bonus"] >= 25

    def test_aadhaar_masked_format_accepted(self):
        res = gate1_validator.validate_aadhaar("XXXX-XXXX-9281", dob_str="1988")
        assert res["valid"] is True
        assert res["is_masked_input"] is True
        assert res["masked_identifier"] == "XXXX-XXXX-9281"

    def test_aadhaar_leading_zero_or_one_rejected(self):
        res = gate1_validator.validate_aadhaar("012345678901")
        assert res["valid"] is False
        assert any("first digit cannot be 0 or 1" in r for r in res["failed_rules"])

    def test_passport_icao_modulo10_check_digits(self):
        # Passport number "L898902C<" -> check digit
        calc_check = calculate_icao_mod10("L898902C<")
        assert 0 <= calc_check <= 9

        dob_check = calculate_icao_mod10("950515")
        exp_check = calculate_icao_mod10("301231")

        # TD3 2 lines MRZ with valid check digits
        mrz_lines = [
            "P<INDGORANI<<PRANAV<<<<<<<<<<<<<<<<<<<<<<<<<",
            f"L898902C<{calc_check}IND950515{dob_check}M301231{exp_check}<<<<<<<<<<<<<<<4"
        ]
        viz_fields = {
            "document_number": "L898902C",
            "name": "PRANAV GORANI",
            "date_of_birth": "1995-05-15"
        }
        res = gate1_validator.validate_passport_mrz(mrz_lines, viz_data=viz_fields)
        assert res["valid"] is True
        assert res["viz_mismatch"] is False
        assert res["trust_bonus"] >= 30

    def test_passport_viz_to_mrz_mismatch_fails(self):
        mrz_lines = [
            "P<INDGORANI<<PRANAV<<<<<<<<<<<<<<<<<<<<<<<<<",
            "L898902C<3IND9505151M3012318<<<<<<<<<<<<<<<4"
        ]
        # Visual number differs from MRZ number -> instant failure
        viz_fields = {
            "document_number": "Z999999A",
            "name": "PRANAV GORANI"
        }
        res = gate1_validator.validate_passport_mrz(mrz_lines, viz_data=viz_fields)
        assert res["valid"] is False
        assert res["viz_mismatch"] is True
        assert any("VIZ-to-MRZ Document Number mismatch" in r for r in res["failed_rules"])

    def test_gate1_establishes_structural_trust_baseline(self):
        # Valid PAN
        pan_fields = {"document_number": "ABCPE1234F", "date_of_birth": "1995-05-15"}
        res = gate1_validator.validate_gate1("PAN", pan_fields)
        assert res["gate1_passed"] is True
        assert res["structural_valid"] is True
        assert res["trust_bonus"] > 0


# =============================================================================
# GATE 2: DIFFERENTIAL ROI FORENSICS & BIOMETRICS TESTS
# =============================================================================
class TestGate2DifferentialForensics:
    def test_uniform_substrate_delta_z_low(self):
        clean_doc = np.ones((750, 1000, 3), dtype=np.uint8) * 220
        noise = np.random.normal(0, 4, clean_doc.shape).astype(np.int16)
        clean_doc = np.clip(clean_doc.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        res = gate2_forensics.execute_gate2(clean_doc, document_number="ABCPE1234F")
        assert res["gate2_passed"] is True
        assert res["splicing_detected"] is False
        assert res["max_delta_z"] <= 1.8
        assert res["total_risk_contribution"] <= 12

    def test_localized_splicing_detected_when_delta_z_high(self):
        spliced_doc = np.ones((750, 1000, 3), dtype=np.uint8) * 220
        rois = gate2_forensics.segment_rois(spliced_doc)
        fx, fy, fw, fh = rois["face_box"]
        spliced_doc[fy:fy+fh, fx:fx+fw] = np.random.randint(50, 200, (fh, fw, 3), dtype=np.uint8)

        res = gate2_forensics.execute_gate2(spliced_doc, document_number="ABCPE1234F")
        assert res["max_delta_z"] > 2.6
        assert res["splicing_detected"] is True
        assert res["gate2_passed"] is False
        assert len(res["flagged_rois"]) > 0
        assert res["total_risk_contribution"] >= 45

    def test_biometrics_1to1_match_and_mismatch(self):
        # Test 1:1 face similarity with identical crop
        face_img = np.zeros((120, 100, 3), dtype=np.uint8)
        # Vertical stripes
        face_img[:, ::4] = 255
        match_res = gate2_forensics.verify_biometrics_1to1(face_img, face_img)
        assert match_res["status"] == "MATCH_CONFIRMED"
        assert match_res["similarity"] > 0.90
        assert match_res["risk_contribution"] == 0

        # Contrast with orthogonal horizontal stripes
        diff_face = np.zeros((120, 100, 3), dtype=np.uint8)
        diff_face[::4, :] = 255
        mismatch_res = gate2_forensics.verify_biometrics_1to1(face_img, diff_face)
        assert mismatch_res["risk_contribution"] >= 25

    def test_biometrics_selfie_none_skips_gracefully(self):
        face_img = np.random.randint(60, 200, (120, 100, 3), dtype=np.uint8)
        res = gate2_forensics.verify_biometrics_1to1(face_img, None)
        assert res["status"] == "SELFIE_NOT_PROVIDED"
        assert res["risk_contribution"] == 0

    def test_recycled_identity_fraud_detection(self):
        gate2_forensics.clear_registry()
        face_img = np.random.randint(80, 180, (100, 100, 3), dtype=np.uint8)
        # Register first under doc number ID-001
        res1 = gate2_forensics.check_recycled_identity_1toN(
            face_img, current_document_number="ID-001", current_name="ALICE SMITH"
        )
        assert res1["recycled_fraud_detected"] is False

        # Attempt to present same face with DIFFERENT document number ID-002
        res2 = gate2_forensics.check_recycled_identity_1toN(
            face_img, current_document_number="ID-002", current_name="BOB JONES"
        )
        assert res2["recycled_fraud_detected"] is True
        assert res2["risk_contribution"] == 70
        assert any("Recycled biometric face match" in ev for ev in res2["evidence"])


# =============================================================================
# GATE 3: CALIBRATED MULTI-GATE SCORER TESTS (THE GOLDEN RULE)
# =============================================================================
class TestGate3CalibratedScorer:
    def test_golden_rule_1_valid_document_is_low_risk(self):
        # Valid Gate 1, Clean Gate 2 (ΔZ <= 1.8), phone-captured blur
        gate1 = {
            "gate1_passed": True,
            "structural_valid": True,
            "trust_bonus": 30,
            "failed_rules": [],
            "passed_rules": ["PAN syntax verified", "4th char entity check verified"]
        }
        gate2 = {
            "gate2_passed": True,
            "splicing_detected": False,
            "max_delta_z": 1.2, # Clean uniform substrate
            "delta_z_face": 1.1,
            "delta_z_text": 1.2,
            "flagged_rois": [],
            "biometrics_1to1": {"status": "MATCH_CONFIRMED", "similarity": 0.88},
            "biometrics_1toN": {"recycled_fraud_detected": False}
        }
        quality = {"quality_score": 75.0, "is_acceptable": True} # Phone capture minor blur
        record = {"status": "VALID", "record_found": True}

        assessment = gate3_scorer.evaluate_multi_gate(gate1, gate2, quality, record)
        assert assessment["risk_level"] == "LOW"
        assert assessment["badge_color"] == "GREEN"
        assert assessment["decision"] == "LOW_RISK"
        assert assessment["risk_score"] <= 30.0

    def test_golden_rule_2_missing_exif_never_triggers_high_risk(self):
        # Missing EXIF + normal WhatsApp compression noise
        gate1 = {"gate1_passed": True, "structural_valid": True, "trust_bonus": 20, "failed_rules": [], "passed_rules": ["Verified"]}
        gate2 = {"gate2_passed": True, "splicing_detected": False, "max_delta_z": 1.5, "delta_z_face": 1.4, "delta_z_text": 1.5, "biometrics_1to1": {}, "biometrics_1toN": {}}
        quality = {"quality_score": 70.0, "issues": ["missing_exif", "whatsapp_compressed"], "is_acceptable": True}

        assessment = gate3_scorer.evaluate_multi_gate(gate1, gate2, quality)
        assert assessment["risk_level"] == "LOW"
        assert assessment["badge_color"] == "GREEN"
        assert assessment["risk_score"] <= 30.0

    def test_golden_rule_3_high_risk_on_deterministic_failure(self):
        # Deterministic check failure in Gate 1 (e.g. Verhoeff checksum mismatch)
        gate1 = {
            "gate1_passed": False,
            "structural_valid": False,
            "trust_bonus": 0,
            "failed_rules": ["Aadhaar Verhoeff checksum calculation failed"],
            "passed_rules": []
        }
        gate2 = {"gate2_passed": True, "splicing_detected": False, "max_delta_z": 1.0, "biometrics_1to1": {}, "biometrics_1toN": {}}

        assessment = gate3_scorer.evaluate_multi_gate(gate1, gate2)
        assert assessment["risk_level"] == "HIGH"
        assert assessment["badge_color"] == "RED"
        assert assessment["risk_score"] >= 66.0

    def test_golden_rule_3_high_risk_on_localized_splicing(self):
        # Gate 1 passed, but Gate 2 proves Face box has ΔZ = 3.2 > 2.6
        gate1 = {"gate1_passed": True, "structural_valid": True, "trust_bonus": 20, "failed_rules": [], "passed_rules": ["Verified"]}
        gate2 = {
            "gate2_passed": False,
            "splicing_detected": True,
            "max_delta_z": 3.2,
            "delta_z_face": 3.2,
            "delta_z_text": 1.2,
            "flagged_rois": [{"region": "FACE_PORTRAIT", "x": 50, "y": 100, "width": 150, "height": 200}],
            "biometrics_1to1": {},
            "biometrics_1toN": {}
        }

        assessment = gate3_scorer.evaluate_multi_gate(gate1, gate2)
        assert assessment["risk_level"] == "HIGH"
        assert assessment["badge_color"] == "RED"
        assert assessment["risk_score"] >= 66.0

    def test_golden_rule_3_high_risk_on_biometric_mismatch(self):
        # Presenter face mismatch (similarity 0.32 < 0.45)
        gate1 = {"gate1_passed": True, "structural_valid": True, "trust_bonus": 20, "failed_rules": [], "passed_rules": ["Verified"]}
        gate2 = {
            "gate2_passed": False,
            "splicing_detected": False,
            "max_delta_z": 1.2,
            "biometrics_1to1": {"status": "MISMATCH_DETECTED", "similarity": 0.32},
            "biometrics_1toN": {"recycled_fraud_detected": False}
        }

        assessment = gate3_scorer.evaluate_multi_gate(gate1, gate2)
        assert assessment["risk_level"] == "HIGH"
        assert assessment["badge_color"] == "RED"
        assert assessment["risk_score"] >= 66.0

    def test_medium_review_band_on_borderline_anomaly(self):
        # Minor lighting disparity (1.8 < ΔZ <= 2.6) -> MEDIUM / YELLOW (Review, NOT Fraud)
        gate1 = {"gate1_passed": True, "structural_valid": True, "trust_bonus": 15, "failed_rules": [], "passed_rules": ["Verified"]}
        gate2 = {
            "gate2_passed": True,
            "splicing_detected": False,
            "max_delta_z": 2.2, # Minor gradient
            "delta_z_face": 2.2,
            "delta_z_text": 1.4,
            "biometrics_1to1": {},
            "biometrics_1toN": {}
        }

        assessment = gate3_scorer.evaluate_multi_gate(gate1, gate2)
        assert assessment["risk_level"] == "MEDIUM"
        assert assessment["badge_color"] == "YELLOW"
        assert assessment["decision"] == "NEEDS_REVIEW"
        assert 25.0 <= assessment["risk_score"] <= 49.0
