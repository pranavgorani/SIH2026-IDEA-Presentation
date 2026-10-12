import io
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.mrz_parser import mrz_parser, calculate_check_digit, verify_checksum
from backend.app.services.ocr_service import ocr_service, ModularOCREngine, compute_expiry_status

client = TestClient(app)

def create_synthetic_test_image(text_lines=None, width=800, height=520, bg=(245, 245, 245)):
    img = Image.new("RGB", (width, height), color=bg)
    draw = ImageDraw.Draw(img)
    if text_lines:
        y = 40
        for line in text_lines:
            draw.text((40, y), line, fill=(10, 10, 10))
            y += 35
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_passport_mrz_valid_and_invalid_check_digits():
    """Validates ICAO TD3 passport MRZ with correct and tampered check digits."""
    # Valid TD3 MRZ lines (44 characters each)
    line1 = "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<"
    line2 = "Z839102459IND9208142M3105098<<<<<<<<<<<<<<00"
    assert len(line1) == 44
    assert len(line2) == 44

    parsed = mrz_parser.parse([line1, line2])
    assert parsed is not None
    assert parsed.document_type == "PASSPORT"
    assert parsed.passport_number == "Z83910245"
    assert parsed.checksum_passport_number is True
    assert parsed.checksum_dob is True
    assert parsed.checksum_expiry is True
    assert parsed.valid is True

    # Tampered passport number (changed '9' check digit to '5')
    tampered_line2 = "Z839102455IND9208142M3105098<<<<<<<<<<<<<<00"
    tampered_parsed = mrz_parser.parse([line1, tampered_line2])
    assert tampered_parsed is not None
    assert tampered_parsed.checksum_passport_number is False
    assert tampered_parsed.valid is False


def test_mrz_viz_mismatch_detection():
    """Validates that mismatches between visual zone and MRZ are flagged."""
    engine = ModularOCREngine()
    line1 = "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<"
    line2 = "Z839102459IND9208142M3105098<<<<<<<<<<<<<<00"
    mrz = mrz_parser.parse([line1, line2])

    # Visible fields with conflicting passport number and conflicting DOB
    visible_fields = {
        "document_number": "A12345678",
        "date_of_birth": "1995-01-01",
        "name": "RAHUL SHARMA",
        "nationality": "IND",
        "issuing_country": "IND"
    }

    master_fields, _, _ = engine._harmonize_and_cross_validate(
        mrz_data=mrz,
        visible_fields=visible_fields,
        gemini_fields=None,
        known_data={},
        raw_text="Sample text",
        engine_used="Local",
        classification={"document_type": "PASSPORT"}
    )

    assert master_fields["document_number"]["validation"] == "MISMATCH"
    assert master_fields["date_of_birth"]["validation"] == "MISMATCH"


def test_unsupported_document_handling():
    """Validates that an unrecognized document is classified as UNSUPPORTED without fabricated fields."""
    engine = ModularOCREngine()
    empty_master = engine._empty_master_fields()
    assert empty_master["document_type"]["value"] == "UNKNOWN"
    assert empty_master["document_number"]["confidence"] == 0.0

    master_fields, extracted_fields, overall_conf = engine._harmonize_and_cross_validate(
        mrz_data=None,
        visible_fields={},
        gemini_fields=None,
        known_data={},
        raw_text="Lorem ipsum dolor sit amet",
        engine_used="Local",
        classification={"document_type": "UNSUPPORTED"}
    )
    assert master_fields["document_type"]["value"] == "UNSUPPORTED"
    assert overall_conf <= 0.35


def test_driving_licence_and_expiry_validation():
    """Validates Indian driving licence parsing and expiry calculation."""
    engine = ModularOCREngine()
    dl_text = """
    UNION OF INDIA DRIVING LICENCE
    STATE OF MAHARASHTRA
    DL NO: MH1220180012345
    NAME: VIKRAM PATIL
    DOB: 12-05-1988
    VALID TILL: 2038-05-11
    """
    fields = engine._extract_fields(dl_text, None, {}, {})
    assert "MH12" in (fields.document_number or "")
    assert "VIKRAM" in (fields.name or "")

    # Expiry calculations
    assert compute_expiry_status("2038-05-11") == "VALID"
    assert compute_expiry_status("2020-01-01") == "EXPIRED"


def test_visa_without_mrz():
    """Validates visa extraction when no MRZ is present."""
    engine = ModularOCREngine()
    visa_text = """
    REPUBLIC OF INDIA VISA
    VISA NO: V1234567
    TYPE: TOURIST
    ENTRIES: MULTIPLE
    HOLDER: JOHN DOE
    VALID FROM: 01/01/2026
    VALID UNTIL: 01/01/2027
    """
    fields = engine._extract_fields(visa_text, None, {}, {})
    assert fields.document_number == "V1234567"
    assert "JOHN" in (fields.name or "")
    assert fields.date_of_expiry == "2027-01-01"


def test_part1_report_export_endpoints_csv_pdf_docx_zip():
    """Tests Part 1 report export endpoints for CSV, PDF, DOCX, and ZIP with filters."""
    # 1. Export CSV
    res_csv = client.get("/api/reports/export/csv?risk_level=LOW&limit=5")
    assert res_csv.status_code == 200
    assert res_csv.headers["content-type"].startswith("text/csv")
    assert b"Case Number" in res_csv.content
    assert b"Audit Hash" in res_csv.content

    # 2. Export PDF
    res_pdf = client.get("/api/reports/export/pdf?limit=5")
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert res_pdf.content.startswith(b"%PDF")

    # 3. Export DOCX
    res_docx = client.get("/api/reports/export/docx?limit=5")
    assert res_docx.status_code == 200
    assert "wordprocessingml" in res_docx.headers["content-type"]
    assert len(res_docx.content) > 1000

    # 4. Export All (ZIP)
    res_zip = client.get("/api/reports/export/all?limit=5")
    assert res_zip.status_code == 200
    assert res_zip.headers["content-type"] == "application/zip"
    assert res_zip.content.startswith(b"PK")


def test_structured_ocr_response_schema():
    """Tests that the full screening endpoint returns the Part 3 structured OCR schema."""
    buf = create_synthetic_test_image(
        text_lines=[
            "REPUBLIC OF INDIA",
            "PASSPORT",
            "P<INDSHARMA<<RAHUL<<<<<<<<<<<<<<<<<<<<<<<<<<",
            "Z839102459IND9208142M3105098<<<<<<<<<<<<<<00"
        ]
    )
    res = client.post(
        "/api/screen",
        files={"file": ("passport_scan.png", buf, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    # Validate Part 3 schema presence
    assert "structured_ocr" in data
    s_ocr = data["structured_ocr"]
    assert "case_id" in s_ocr
    assert "document_type" in s_ocr
    assert "overall_ocr_confidence" in s_ocr
    assert "extraction_status" in s_ocr
    assert "fields" in s_ocr
    assert "mrz_validation" in s_ocr
    assert "quality_checks" in s_ocr
    assert "validation_results" in s_ocr
    assert "processing_metadata" in s_ocr
    assert s_ocr["processing_metadata"]["ocr_engine"] is not None

    # Check field structure
    fields = s_ocr["fields"]
    assert "document_number" in fields
    assert "status" in fields["document_number"]
    assert fields["document_number"]["status"] in ("MATCHED", "VERIFIED", "REVIEW", "NOT_FOUND", "NOT_PRESENT", "NOT_VERIFIED")
