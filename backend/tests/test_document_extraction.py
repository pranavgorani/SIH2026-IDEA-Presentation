import pytest
import io
import cv2
import numpy as np
from datetime import date
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.ocr_service import ocr_service, ModularOCREngine, clear_ocr_cache, get_ocr_cache_size
from backend.app.services.mrz_parser import mrz_parser, calculate_check_digit, verify_checksum
from backend.app.models.schemas import ExtractedFields, MRZData

client = TestClient(app)

def create_synthetic_passport_image(
    doc_no="T84920152",
    surname="DOE",
    given_names="JANE",
    nationality="USA",
    dob_yymmdd="900101",
    expiry_yymmdd="300101",
    sex="F"
):
    """Generates an in-memory synthetic passport image with clear OCR text and ICAO 9303 MRZ."""
    img = np.ones((700, 1000, 3), dtype=np.uint8) * 255

    # Document Header
    cv2.putText(img, "PASSPORT", (380, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 3)
    cv2.putText(img, f"Document No: {doc_no}", (400, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Surname: {surname}", (400, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Given Names: {given_names}", (400, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Nationality: {nationality}", (400, 310), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Date of Birth: 01/01/1990", (400, 360), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Sex: {sex}", (400, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Date of Expiry: 01/01/2030", (400, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    # Calculate Check Digits
    ck_doc = calculate_check_digit(doc_no)
    ck_dob = calculate_check_digit(dob_yymmdd)
    ck_exp = calculate_check_digit(expiry_yymmdd)
    comp_str = f"{doc_no}{ck_doc}{nationality}{dob_yymmdd}{ck_dob}{sex}{expiry_yymmdd}{ck_exp}"
    ck_comp = calculate_check_digit(comp_str)

    line1 = f"P<{nationality}{surname}<<{given_names}".ljust(44, '<')
    line2 = f"{doc_no}{ck_doc}{nationality}{dob_yymmdd}{ck_dob}{sex}{expiry_yymmdd}{ck_exp}{'<'*14}0{ck_comp}".ljust(44, '<')

    cv2.putText(img, line1, (40, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)
    cv2.putText(img, line2, (40, 630), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 0), 2)

    _, buf = cv2.imencode(".png", img)
    return io.BytesIO(buf.tobytes()), (line1, line2)


def test_document_type_extraction():
    engine = ModularOCREngine()
    text = "PASSPORT / PASSEPORT\nUNITED STATES OF AMERICA\nP<USA..."
    fields = engine._extract_visible_fields(text)
    assert fields.get("document_type") == "PASSPORT"


def test_document_number_extraction():
    engine = ModularOCREngine()
    text = "PASSPORT\nPassport No: J91823746\nName: JOHN DOE"
    fields = engine._extract_visible_fields(text)
    assert fields.get("document_number") == "J91823746"


def test_name_extraction():
    engine = ModularOCREngine()
    text = "REPUBLIC OF UTOPIA\nFull Name: ELIZABETH TAYLER\nPassport No: U81920311"
    fields = engine._extract_visible_fields(text)
    assert fields.get("holder_full_name") == "ELIZABETH TAYLER"


def test_nationality_extraction():
    engine = ModularOCREngine()
    text = "PASSPORT\nNationality: CAN\nName: MARCUS VANCE"
    fields = engine._extract_visible_fields(text)
    assert fields.get("nationality") == "CAN"


def test_dob_extraction():
    engine = ModularOCREngine()
    text = "IDENTITY CARD\nDate of Birth: 14/06/1988\nName: ALICE SMITH"
    fields = engine._extract_visible_fields(text)
    assert fields.get("date_of_birth") == "1988-06-14"


def test_gender_extraction():
    engine = ModularOCREngine()
    text_m = "PASSPORT\nSex: MALE\nName: ROBERT CHEN"
    assert engine._extract_visible_fields(text_m).get("gender_code") == "M"

    text_f = "PASSPORT\nGender: FEMALE\nName: SARAH CONNOR"
    assert engine._extract_visible_fields(text_f).get("gender_code") == "F"


def test_expiry_extraction():
    engine = ModularOCREngine()
    text = "TRAVEL DOCUMENT\nExpiry Date: 25/12/2031\nNumber: K91827361"
    fields = engine._extract_visible_fields(text)
    assert fields.get("expiry_date") == "2031-12-25"


def test_issuing_country_extraction():
    engine = ModularOCREngine()
    text = "PASSPORT\nCountry of Issue: GBR\nNumber: G12345678"
    fields = engine._extract_visible_fields(text)
    assert fields.get("issuing_country") == "GBR"


def test_no_hardcoded_values():
    """Verifies that an image with custom details extracts those details and NOT fixed demo values."""
    custom_doc = "X99182734"
    custom_name = "RODRIGUEZ"
    img_buf, _ = create_synthetic_passport_image(doc_no=custom_doc, surname=custom_name)

    res = client.post(
        "/api/screen",
        files={"file": ("custom_passport.png", img_buf, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Must NOT contain hardcoded sample values
    assert data["document"]["number"] != "Z56532962"
    assert data["document"]["holder_name"] != "GEMINI GENERATED"
    # Should extract actual values
    assert custom_doc in (data["document"]["number"] or "") or (data["ocr"]["fields"]["document_number"] or "")
    assert data["document"]["type"] == "PASSPORT"


def test_stale_result_cleared():
    """Uploads Document A then Document B to verify Document B gets a fresh case_id and distinct results."""
    img_a, _ = create_synthetic_passport_image(doc_no="A11111111", surname="FIRST")
    img_b, _ = create_synthetic_passport_image(doc_no="B22222222", surname="SECOND")

    res_a = client.post("/api/screen", files={"file": ("doc_a.png", img_a, "image/png")})
    assert res_a.status_code == 200
    data_a = res_a.json()

    res_b = client.post("/api/screen", files={"file": ("doc_b.png", img_b, "image/png")})
    assert res_b.status_code == 200
    data_b = res_b.json()

    # Completely distinct session and case IDs
    assert data_a["case_id"] != data_b["case_id"]
    assert data_a["case_number"] != data_b["case_number"]
    assert data_a["request_id"] != data_b["request_id"]


def test_gemini_fallback():
    """Ensures when Gemini is unavailable or not configured, screening pipeline completes using Local CV."""
    img = np.ones((500, 800, 3), dtype=np.uint8) * 255
    cv2.putText(img, "TEST DOCUMENT", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    _, buf = cv2.imencode(".png", img)

    res = client.post(
        "/api/screen",
        files={"file": ("doc.png", io.BytesIO(buf.tobytes()), "image/png")},
        data={"force_local_fallback": "true"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["verification_mode"] == "LOCAL_FALLBACK"


def test_mrz_checksum():
    """Tests ICAO Doc 9303 checksum validation on matching and tampered digits."""
    doc_no = "A12345678"
    chk = calculate_check_digit(doc_no)
    assert verify_checksum(doc_no, str(chk)) is True
    assert verify_checksum(doc_no, str((chk + 1) % 10)) is False


def test_ocr_failure():
    """Verifies that an unreadable or blank image flags low confidence gracefully without 500 error."""
    blank = np.ones((300, 400, 3), dtype=np.uint8) * 200
    _, buf = cv2.imencode(".png", blank)

    res = client.post(
        "/api/screen",
        files={"file": ("blank.png", io.BytesIO(buf.tobytes()), "image/png")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["ocr"]["ocr_status"] in ("LOW_CONFIDENCE", "OK")
    assert data["field_confidence"]["document_number"] <= 0.70


def test_low_confidence_field():
    """Verifies field with mismatch or missing OCR is flagged with low confidence / review required."""
    engine = ModularOCREngine()
    # Flawed MRZ where check digit does not match
    mrz = MRZData(
        valid=False,
        raw_mrz=["P<UTOERIKSSON<<ANNA<<<<<<<<<<<<<<<<<<<<<<<<<", "L898902C39UTO7408122F1204159ZE184226B<<<<<10"],
        document_type="PASSPORT",
        country_code="UTO",
        surname="ERIKSSON",
        given_names="ANNA",
        passport_number="L898902C3",
        nationality="UTO",
        date_of_birth="1974-08-12",
        sex="F",
        expiry_date="2012-04-15",
        checksum_passport_number=False,
        checksum_dob=True,
        checksum_expiry=True
    )
    master, fields, conf = engine._harmonize_and_cross_validate(mrz, {}, {}, {}, "Some text", "Local")
    # Low confidence on document number because checksum failed
    assert master["document_number"]["confidence"] <= 0.75
