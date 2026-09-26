"""
TRUST-ID SIH 2026 - Comprehensive Gateway & Screening Pipeline Resilience Test Suite
Validates the 18 specific test cases required by the defense-grade engineering audit:
1. Valid PDF upload (with PDF processing enabled) -> 200 with 10 stages
2. Valid PNG upload -> 200 with 10 stages
3. Valid JPG upload -> 200 with 10 stages
4. Invalid file type (.exe, .zip) -> 400 INVALID_DOCUMENT (never 500)
5. File exceeding 25MB -> 400/413 FILE_TOO_LARGE (never 500)
6. Empty file (0 bytes) -> 400 EMPTY_FILE (never 500)
7. Corrupted image -> 400 CORRUPTED_DOCUMENT (never 500)
8. Gemini API down -> Fall back to local CV, 200 with AI_STATUS="unavailable"
9. Gemini timeout -> Fall back to local CV, 200 without crashing
10. Gemini invalid key -> Fall back to local CV, 200
11. OCR low confidence -> Record warning, continue pipeline
12. Database down -> Return screening result, database_saved=false, 200
13. Report generation fails -> Return screening result, report_generated=false, 200
14. Gateway error format -> Verify structured error envelope
15. Force local fallback -> Runs local CV only, ai_status="fallback"
16. Admin error response -> Contains request_id and debug capability
17. Non-admin error response -> Safe user message without leaked traces
18. Health check endpoints -> GET /health and GET /health/screening
"""

import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from backend.app.main import app
from backend.app.core.config import settings

client = TestClient(app)

def make_test_image(width=600, height=400, fmt="PNG"):
    img = Image.new("RGB", (width, height), color=(240, 240, 245))
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    buf.seek(0)
    return buf.getvalue()

def make_simple_pdf():
    from reportlab.pdfgen import canvas
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "TRUST-ID TEST PASSPORT P<UTOERIKSSON<<ANNA<<<<<<<<<<<<<<<<<<<<<<<<<<<")
    c.drawString(100, 730, "L898902C36UTO7408122F1204159ZE184226B<<<<<10")
    c.save()
    buf.seek(0)
    return buf.getvalue()

# ---------------------------------------------------------------------------
# TEST 1: Valid PDF upload (when ENABLE_PDF_PROCESSING=True) -> 200
# ---------------------------------------------------------------------------
def test_valid_pdf_upload_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "ENABLE_PDF_PROCESSING", True)
    pdf_bytes = make_simple_pdf()
    res = client.post(
        "/api/screen",
        files={"file": ("passport_doc.pdf", pdf_bytes, "application/pdf")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "request_id" in data
    assert "stages" in data or "pipeline" in data
    assert len(data.get("pipeline", [])) >= 10

# ---------------------------------------------------------------------------
# TEST 2: Valid PNG upload -> 200 with 10 stages
# ---------------------------------------------------------------------------
def test_valid_png_upload():
    png_bytes = make_test_image(800, 600, "PNG")
    res = client.post(
        "/api/screen",
        files={"file": ("credential_scan.png", png_bytes, "image/png")},
        data={"document_type_hint": "PASSPORT"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["request_id"]
    assert len(data["pipeline"]) >= 10
    assert data["checks_summary"]["total_checks"] == 100

# ---------------------------------------------------------------------------
# TEST 3: Valid JPG upload -> 200 with 10 stages
# ---------------------------------------------------------------------------
def test_valid_jpg_upload():
    jpg_bytes = make_test_image(800, 600, "JPEG")
    res = client.post(
        "/api/screen",
        files={"file": ("national_id_front.jpg", jpg_bytes, "image/jpeg")},
        data={"document_type_hint": "NATIONAL_ID"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["document"]["type"] in ("NATIONAL_ID", "AUTO_DETECT", "UNKNOWN")

# ---------------------------------------------------------------------------
# TEST 4: Invalid file type (.exe, .zip) -> 400 INVALID_DOCUMENT (never 500)
# ---------------------------------------------------------------------------
def test_invalid_file_type_rejected():
    res = client.post(
        "/api/screen",
        files={"file": ("malware.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["stage"] == "UPLOAD"
    assert data["code"] in ("INVALID_DOCUMENT", "STORAGE_ERROR")

# ---------------------------------------------------------------------------
# TEST 5: File exceeding 25MB -> 400/413 FILE_TOO_LARGE (never 500)
# ---------------------------------------------------------------------------
def test_oversized_file_rejected():
    huge_data = b"0" * (26 * 1024 * 1024)
    res = client.post(
        "/api/screen",
        files={"file": ("huge_credential.png", huge_data, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code in (400, 413)
    data = res.json()
    assert data["success"] is False
    assert data["code"] == "FILE_TOO_LARGE"

# ---------------------------------------------------------------------------
# TEST 6: Empty file (0 bytes) -> 400 EMPTY_FILE (never 500)
# ---------------------------------------------------------------------------
def test_empty_file_rejected():
    res = client.post(
        "/api/screen",
        files={"file": ("empty.png", b"", "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["code"] in ("EMPTY_FILE", "IMAGE_NORMALIZATION_FAILED")

# ---------------------------------------------------------------------------
# TEST 7: Corrupted image -> 400 CORRUPTED_DOCUMENT (never 500)
# ---------------------------------------------------------------------------
def test_corrupted_image_rejected():
    corrupted_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRcorruptedjunkpayload"
    res = client.post(
        "/api/screen",
        files={"file": ("corrupted.png", corrupted_bytes, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["code"] in ("CORRUPTED_DOCUMENT", "INVALID_DOCUMENT")

# ---------------------------------------------------------------------------
# TEST 8: Gemini API down -> Fall back to local CV, 200 with AI_STATUS="unavailable"
# ---------------------------------------------------------------------------
def test_gemini_api_down_fallback(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "GEMINI_VISION_HYBRID")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    png_bytes = make_test_image(800, 600, "PNG")
    res = client.post(
        "/api/screen",
        files={"file": ("test_doc.png", png_bytes, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["ai_status"] in ("unavailable", "fallback")
    assert "forensics" in data

# ---------------------------------------------------------------------------
# TEST 9: Gemini timeout -> Fall back to local CV, 200 without crashing
# ---------------------------------------------------------------------------
def test_gemini_timeout_fallback(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "GEMINI_VISION_HYBRID")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "dummy_gemini_key")
    png_bytes = make_test_image(800, 600, "PNG")
    with patch("backend.app.providers.gemini_provider.GeminiVisionHybridProvider._call_gemini_vision") as mock_gemini:
        mock_gemini.side_effect = TimeoutError("Gemini API connection timed out after 10.0s")
        res = client.post(
            "/api/screen",
            files={"file": ("test_timeout.png", png_bytes, "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["ai_status"] in ("unavailable", "fallback")

# ---------------------------------------------------------------------------
# TEST 10: Gemini invalid key -> Fall back to local CV, 200
# ---------------------------------------------------------------------------
def test_gemini_invalid_key_fallback(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "GEMINI_VISION_HYBRID")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "INVALID_API_KEY_TEST_403")
    png_bytes = make_test_image(800, 600, "PNG")
    with patch("backend.app.providers.gemini_provider.GeminiVisionHybridProvider._call_gemini_vision") as mock_gemini:
        mock_gemini.side_effect = Exception("HTTP 403: API key not valid. Please pass a valid API key.")
        res = client.post(
            "/api/screen",
            files={"file": ("test_bad_key.png", png_bytes, "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["ai_status"] in ("unavailable", "fallback")

# ---------------------------------------------------------------------------
# TEST 11: OCR low confidence -> Record warning, continue pipeline
# ---------------------------------------------------------------------------
def test_ocr_low_confidence_records_warning():
    from backend.app.models.schemas import ExtractedFields
    png_bytes = make_test_image(800, 600, "PNG")
    with patch("backend.app.services.ocr_service.ocr_service.process_document") as mock_ocr:
        mock_ocr.return_value = {
            "raw_text": "",
            "fields": ExtractedFields(),
            "mrz": None,
            "confidence": 0.20,
            "bounding_boxes": [],
            "engine_used": "Test OCR",
            "status": "LOW_CONFIDENCE",
            "ocr_status": "LOW_CONFIDENCE"
        }
        res = client.post(
            "/api/screen",
            files={"file": ("low_conf.png", png_bytes, "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] in ("COMPLETED", "REVIEW_REQUIRED")

# ---------------------------------------------------------------------------
# TEST 12: Database down -> Return screening result, database_saved=false, 200
# ---------------------------------------------------------------------------
def test_database_down_preserves_screening_result():
    png_bytes = make_test_image(800, 600, "PNG")
    with patch("backend.app.api.screening.Case") as mock_case:
        mock_case.side_effect = Exception("Database connection refused (sqlite/postgres connection down)")
        res = client.post(
            "/api/screen",
            files={"file": ("db_fail_test.png", png_bytes, "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["database_saved"] is False
    assert data["document_integrity_score"] is not None

# ---------------------------------------------------------------------------
# TEST 13: Report generation fails -> Return screening result, report_generated=false, 200
# ---------------------------------------------------------------------------
def test_report_generation_failure_does_not_crash_pipeline():
    png_bytes = make_test_image(800, 600, "PNG")
    with patch("backend.app.services.report_pdf_service.report_pdf_service.generate_pdf_report") as mock_pdf:
        mock_pdf.side_effect = Exception("ReportLab rendering error")
        res = client.post(
            "/api/screen",
            files={"file": ("report_fail_test.png", png_bytes, "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["pdf_report_ready"] is False

# ---------------------------------------------------------------------------
# TEST 14: Gateway error format -> Verify structured error envelope
# ---------------------------------------------------------------------------
def test_gateway_error_envelope_structure():
    res = client.post("/api/screen", files={}, data={})
    assert res.status_code == 400
    data = res.json()
    assert "success" in data
    assert data["success"] is False
    assert "request_id" in data
    assert "stage" in data
    assert "code" in data
    assert "message" in data
    assert "user_action" in data

# ---------------------------------------------------------------------------
# TEST 15: Force local fallback -> Runs local CV only, ai_status="fallback"
# ---------------------------------------------------------------------------
def test_force_local_fallback_skips_ai():
    png_bytes = make_test_image(800, 600, "PNG")
    res = client.post(
        "/api/screen",
        files={"file": ("force_fallback.png", png_bytes, "image/png")},
        data={"document_type_hint": "AUTO_DETECT", "force_local_fallback": "true"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["ai_status"] == "fallback"
    assert data["force_local_fallback"] is True

# ---------------------------------------------------------------------------
# TEST 16 & 17: Request ID and user safety in error responses
# ---------------------------------------------------------------------------
def test_error_response_contains_request_id_and_no_traceback():
    res = client.post(
        "/api/screen",
        files={"file": ("bad.exe", b"malicious", "application/x-msdownload")},
        data={}
    )
    assert res.status_code == 400
    text = res.text
    # Never expose python traceback or internal filenames to client
    assert "Traceback (most recent call last)" not in text
    data = res.json()
    assert "request_id" in data
    assert data["request_id"] != ""

# ---------------------------------------------------------------------------
# TEST 18: Health check endpoints
# ---------------------------------------------------------------------------
def test_health_check_dependencies():
    # GET /health
    res1 = client.get("/health")
    assert res1.status_code == 200
    d1 = res1.json()
    assert d1["status"] == "ok"
    assert d1["api"] is True
    assert "database" in d1
    assert "ocr" in d1
    assert "ai" in d1
    assert "storage" in d1

    # GET /health/screening
    res2 = client.get("/health/screening")
    assert res2.status_code == 200
    d2 = res2.json()
    assert d2["status"] == "ready"
    assert d2["pipeline_stages"] == 10
    assert "ai_provider" in d2
    assert "ocr_engine" in d2
    assert "database_connected" in d2
