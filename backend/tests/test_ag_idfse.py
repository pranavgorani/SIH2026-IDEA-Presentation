import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.ag_idfse import (
    ag_idfse_engine,
    calculate_icao_check_digit,
    format_mrz_date,
    clean_ocr_digits,
    clean_ocr_alpha
)

client = TestClient(app)

def test_icao_check_digit_calculation():
    """Verifies mathematical check-digit calculation with 7-3-1 weights according to ICAO Doc 9303."""
    # Test sample passport from ICAO standard:
    # Doc number: L898902C3 with check digit 6
    doc_num = "L898902C3"
    assert calculate_icao_check_digit(doc_num) == 6

    # Date of birth: 740812 with check digit 2
    dob = "740812"
    assert calculate_icao_check_digit(dob) == 2

    # Expiry date: 120415 with check digit 9
    exp = "120415"
    assert calculate_icao_check_digit(exp) == 9

    # Master composite checksum:
    # Composite data: line2[0:10] + line2[13:20] + line2[21:43]
    # "L898902C36" + "7408122" + "1204159ZE184226B<<<<<1"
    comp_data = "L898902C3674081221204159ZE184226B<<<<<1"
    assert calculate_icao_check_digit(comp_data) == 0


def test_unsupported_document_rejection():
    """Section 2: Rejects unsupported documents immediately with {"status": "REJECTED_UNSUPPORTED_DOCUMENT"}."""
    # Student ID
    res1 = ag_idfse_engine.screen_document(raw_text_override="XYZ UNIVERSITY CAMPUS STUDENT ID CARD 2026")
    assert res1 == {"status": "REJECTED_UNSUPPORTED_DOCUMENT"}

    # Utility bill
    res2 = ag_idfse_engine.screen_document(raw_text_override="ELECTRICITY BILL FOR THE MONTH OF MARCH CONSUMER NO 192837")
    assert res2 == {"status": "REJECTED_UNSUPPORTED_DOCUMENT"}

    # Handwritten note
    res3 = ag_idfse_engine.screen_document(raw_text_override="Dear Sir, please find handwritten memo attached for verification.")
    assert res3 == {"status": "REJECTED_UNSUPPORTED_DOCUMENT"}

    # Non-identity invoice
    res4 = ag_idfse_engine.screen_document(raw_text_override="TAX INVOICE PAYMENT RECEIPT ORDER #99281")
    assert res4 == {"status": "REJECTED_UNSUPPORTED_DOCUMENT"}


def test_passport_screening_schema_and_integrity():
    """Section 6: Full valid ICAO TD3 Passport screening conforming strictly to specification schema."""
    mrz_lines = [
        "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
        "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    ]
    viz = {
        "document_number": "L898902C3",
        "surname": "ERIKSSON",
        "given_names": "ANNA MARIA",
        "nationality": "UTO",
        "issuing_country": "UTO",
        "date_of_birth": "1974-08-12",
        "gender": "F",
        "expiry_date": "2022-04-15"
    }

    result = ag_idfse_engine.screen_document(
        mrz_override=mrz_lines,
        viz_override=viz,
        document_type_hint="PASSPORT"
    )

    # 1. Classification
    assert result["document_classification"]["type"] == "PASSPORT"
    assert result["document_classification"]["standard"] == "ICAO_TD3"
    assert result["document_classification"]["confidence"] >= 0.90

    # 2. Extracted Data
    ext = result["extracted_data"]
    assert ext["document_number"] == "L898902C3"
    assert ext["surname"] == "ERIKSSON"
    assert ext["given_names"] == "ANNA MARIA"
    assert ext["nationality"] == "UTO"
    assert ext["issuing_country"] == "UTO"
    assert ext["date_of_birth"] == "1974-08-12"
    assert ext["gender"] == "F"
    assert ext["expiry_date"] == "2022-04-15"

    # 3. MRZ Integrity
    mrz = result["mrz_integrity"]
    assert mrz["raw_mrz"] == mrz_lines
    assert mrz["check_digit_doc_num_valid"] is True
    assert mrz["check_digit_dob_valid"] is True
    assert mrz["check_digit_expiry_valid"] is True
    assert mrz["composite_checksum_valid"] is True
    assert mrz["viz_mrz_cross_match_passed"] is True

    # 4. Forensic Tampering Analysis
    tamper = result["forensic_tampering_analysis"]
    assert "photo_edge_anomaly_score" in tamper
    assert tamper["photo_replacement_detected"] is False
    assert tamper["typography_inconsistency_detected"] is False

    # 5. Threat Assessment
    threat = result["threat_assessment"]
    assert threat["status"] in ["PASS", "REVIEW"]
    assert any("All ICAO 9303 check digits verified." in r for r in threat["reasons"])
    assert any("VIZ and MRZ fields match perfectly." in r for r in threat["reasons"])


def test_viz_mrz_tampering_mismatch_alert():
    """Rule 2: VIZ vs MRZ mismatch must trigger HIGH_SEVERITY_TAMPERING_ALERT."""
    mrz_lines = [
        "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
        "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
    ]
    # Tampered VIZ: Name altered to "SMITH, JOHN" and birthdate to 1980-01-01
    tampered_viz = {
        "document_number": "L898902C3",
        "surname": "SMITH",
        "given_names": "JOHN",
        "date_of_birth": "1980-01-01",
        "expiry_date": "2022-04-15"
    }

    result = ag_idfse_engine.screen_document(
        mrz_override=mrz_lines,
        viz_override=tampered_viz,
        document_type_hint="PASSPORT"
    )

    assert result["mrz_integrity"]["viz_mrz_cross_match_passed"] is False
    assert result["threat_assessment"]["status"] in ["FLAGGED", "REJECT"]
    assert any("HIGH_SEVERITY_TAMPERING_ALERT" in r for r in result["threat_assessment"]["reasons"])


def test_visa_credential_screening():
    """Category 2: Visas (ICAO MRVA / MRVB) with visa-specific fields."""
    mrz_lines = [
        "V<UTOSMITH<<JOHN<<<<<<<<<<<<<<<<<<<<<<<<<<<<",
        "V1234567<6UTO8505204M2512318<<<<<<<<<<<<<<<0"
    ]
    viz = {
        "document_number": "V1234567",
        "surname": "SMITH",
        "given_names": "JOHN",
        "visa_category": "TOURIST",
        "number_of_entries": "MULTIPLE",
        "duration_of_stay": 90,
        "expiry_date": "2025-12-31"
    }

    result = ag_idfse_engine.screen_document(
        mrz_override=mrz_lines,
        viz_override=viz,
        document_type_hint="VISA"
    )

    assert result["document_classification"]["type"] == "VISA"
    assert result["extracted_data"]["visa_category"] == "TOURIST"
    assert result["extracted_data"]["number_of_entries"] == "MULTIPLE"
    assert result["extracted_data"]["duration_of_stay"] == 90


def test_driver_license_credential_screening():
    """Category 4: Driver's Licenses (ISO/IEC 18013)."""
    viz = {
        "document_number": "DL-9948201",
        "surname": "GARCIA",
        "given_names": "CARLOS",
        "issuing_country": "USA",
        "nationality": "USA",
        "date_of_birth": "1988-06-14",
        "gender": "M",
        "expiry_date": "2028-06-14"
    }

    result = ag_idfse_engine.screen_document(
        raw_text_override="STATE OF CALIFORNIA DRIVER LICENSE DL NO DL-9948201 DOB 1988-06-14 EXP 2028-06-14 CLASS C",
        viz_override=viz,
        document_type_hint="DRIVING_LICENSE"
    )

    assert result["document_classification"]["type"] == "DRIVING_LICENSE"
    assert result["document_classification"]["standard"] == "ISO_18013"
    assert result["extracted_data"]["document_number"] == "DL-9948201"
    assert result["threat_assessment"]["status"] in ["PASS", "REVIEW"]


def test_temporal_validity_expired_document():
    """Rule 3: Expired document flag."""
    past_date = (date.today() - timedelta(days=200)).isoformat()
    result = ag_idfse_engine.screen_document(
        mrz_override=[
            "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
            "L898902C36UTO7408122F1204159ZE184226B<<<<<10"
        ],
        viz_override={"expiry_date": past_date, "surname": "ERIKSSON", "given_names": "ANNA MARIA"},
        document_type_hint="PASSPORT"
    )

    assert any("expired" in r.lower() for r in result["threat_assessment"]["reasons"])


def test_api_endpoint_idfse_screen_valid():
    """FastAPI TestClient verifies POST /api/idfse/screen and /idfse/screen."""
    payload = {
        "document_type_hint": "PASSPORT",
        "raw_mrz": "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<\nL898902C36UTO7408122F1204159ZE184226B<<<<<10",
        "viz_data": '{"document_number": "L898902C3", "surname": "ERIKSSON", "given_names": "ANNA MARIA"}'
    }

    response = client.post("/api/idfse/screen", data=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["document_classification"]["type"] == "PASSPORT"
    assert data["mrz_integrity"]["check_digit_doc_num_valid"] is True


def test_api_endpoint_idfse_screen_rejected():
    """FastAPI TestClient verifies rejection of unsupported documents."""
    payload = {
        "raw_text": "UNIVERSITY STUDENT ID CARD SPRING 2026 ENROLLMENT 883921"
    }

    response = client.post("/api/idfse/screen", data=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "REJECTED_UNSUPPORTED_DOCUMENT"}


def test_strict_section4_json_schema():
    """Section 4: Verifies strict adherence to specified JSON Output Schema."""
    mrz_lines = [
        "P<GBRSMITH<<JOHN<DOE<<<<<<<<<<<<<<<<<<<<<<<",
        "L898902C36GBR8806152M2806148<<<<<<<<<<<<<<0"
    ]
    viz = {
        "document_number": "L898902C3",
        "surname": "SMITH",
        "given_names": "JOHN DOE",
        "nationality": "GBR",
        "issuing_country": "GBR",
        "date_of_birth": "1988-06-15",
        "gender": "M",
        "expiry_date": "2028-06-14"
    }

    result = ag_idfse_engine.screen_document(
        mrz_override=mrz_lines,
        viz_override=viz,
        document_type_hint="PASSPORT"
    )

    # 1. document_classification
    assert "document_classification" in result
    assert result["document_classification"]["type"] == "PASSPORT"
    assert result["document_classification"]["standard"] == "ICAO_TD3"
    assert isinstance(result["document_classification"]["confidence"], float)

    # 2. extracted_identity
    assert "extracted_identity" in result
    ext = result["extracted_identity"]
    assert ext["document_number"] == "L898902C3"
    assert ext["surname"] == "SMITH"
    assert ext["given_names"] == "JOHN DOE"
    assert ext["nationality"] == "GBR"
    assert ext["issuing_country"] == "GBR"
    assert ext["date_of_birth"] == "1988-06-15"
    assert ext["gender"] == "M"
    assert ext["expiry_date"] == "2028-06-14"

    # 3. mrz_validation
    assert "mrz_validation" in result
    mrz = result["mrz_validation"]
    assert mrz["mrz_detected"] is True
    assert mrz["check_digit_doc_number"] in ["PASS", "FAIL"]
    assert mrz["check_digit_dob"] in ["PASS", "FAIL"]
    assert mrz["check_digit_expiry"] in ["PASS", "FAIL"]
    assert mrz["composite_checksum"] in ["PASS", "FAIL"]
    assert isinstance(mrz["viz_mrz_cross_match_score"], float)

    # 4. forensic_analysis
    assert "forensic_analysis" in result
    forensic = result["forensic_analysis"]
    assert isinstance(forensic["ela_tamper_score"], float)
    assert isinstance(forensic["photo_splice_detected"], bool)
    assert isinstance(forensic["typography_anomaly_detected"], bool)
    assert isinstance(forensic["flagged_regions"], list)

    # 5. biometric_verification
    assert "biometric_verification" in result
    bio = result["biometric_verification"]
    assert isinstance(bio["face_match"], bool)
    assert isinstance(bio["similarity_score"], float)
    assert isinstance(bio["liveness_confirmed"], bool)

    # 6. final_decision
    assert "final_decision" in result
    decision = result["final_decision"]
    assert isinstance(decision["risk_score"], int)
    assert decision["status"] in ["CLEARED", "SECONDARY_REVIEW", "DENIED_FRAUD"]
    assert isinstance(decision["reasons"], list)
    assert len(decision["reasons"]) > 0


def test_geometric_rectification_and_zonal_partitioning():
    """Module 1: Geometric Rectification & Zonal Partitioning."""
    import numpy as np
    # Synthetic document image
    img = np.ones((500, 800, 3), dtype=np.uint8) * 220
    warped, was_rectified, corners = ag_idfse_engine.rectify_document(img)
    assert len(corners) == 4

    zones = ag_idfse_engine.partition_zones(img)
    assert "mrz" in zones
    assert "viz" in zones
    assert zones["mrz"].shape[0] == int(500 * 0.25)
    assert zones["viz"].shape[0] == int(500 * 0.80)


def test_threat_scoring_matrix_thresholds():
    """Section 3: Unified Threat Scoring Matrix formula."""
    # Low risk (clean) -> CLEARED (0 - 25)
    score1, dec1 = ag_idfse_engine.calculate_threat_score(
        mrz_fail=0.0, viz_mismatch=0.0, forensic_ela=0.0, biometric_mismatch=0.0
    )
    assert dec1 == "CLEARED"
    assert score1 <= 25

    # Moderate risk (expiry or minor mismatch) -> SECONDARY_REVIEW (26 - 65)
    score2, dec2 = ag_idfse_engine.calculate_threat_score(
        mrz_fail=0.0, viz_mismatch=0.80, forensic_ela=0.40, biometric_mismatch=0.0
    )
    assert dec2 == "SECONDARY_REVIEW"
    assert 26 <= score2 <= 65

    # Severe threat (MRZ fail + splice + biometric mismatch) -> DENIED_FRAUD (66 - 100)
    score3, dec3 = ag_idfse_engine.calculate_threat_score(
        mrz_fail=1.0, viz_mismatch=0.80, forensic_ela=1.0, biometric_mismatch=1.0
    )
    assert dec3 == "DENIED_FRAUD"
    assert score3 >= 66
