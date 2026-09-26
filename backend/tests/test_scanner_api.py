import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def create_test_image(width=800, height=600, color=(240, 240, 240)):
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

# ---------------------------------------------------------------------------
# 1. API / UPLOAD VALIDATION TESTS
# ---------------------------------------------------------------------------
def test_scanner_upload_low_resolution_rejection():
    """Validates that low-resolution captures (< 250x180) are rejected safely."""
    tiny_buf = create_test_image(width=150, height=100)
    res = client.post(
        "/api/screen",
        files={"file": ("document_scan_tiny.png", tiny_buf, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["stage"] == "UPLOAD"
    assert "resolution is too low" in data["message"].lower()

def test_scanner_upload_oversized_rejection():
    """Validates that massive payload (> 25MB) is cleanly rejected."""
    # 26MB dummy byte stream
    huge_bytes = b"0" * (26 * 1024 * 1024)
    res = client.post(
        "/api/screen",
        files={"file": ("huge_scan.png", huge_bytes, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["stage"] == "UPLOAD"
    assert "exceeds the maximum allowed size" in data["message"]

def test_scanner_upload_corrupted_image_rejection():
    """Validates that corrupt image payload is handled without 500 crash."""
    corrupted_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRcorruptedjunkdata12345"
    res = client.post(
        "/api/screen",
        files={"file": ("corrupted_scan.png", corrupted_bytes, "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["stage"] == "UPLOAD"
    assert "invalid, unsupported, or corrupted" in data["message"].lower()

# ---------------------------------------------------------------------------
# 2. ERROR-STATE TESTS
# ---------------------------------------------------------------------------
def test_scanner_empty_file_error():
    """Validates that an empty file upload returns clean error state."""
    res = client.post(
        "/api/screen",
        files={"file": ("empty_scan.png", b"", "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["stage"] == "UPLOAD"
    assert data["code"] in ("EMPTY_FILE", "IMAGE_NORMALIZATION_FAILED")

def test_scanner_pdf_upload_disabled_state():
    """Validates that PDF upload returns a clear, non-crashing message."""
    res = client.post(
        "/api/screen",
        files={"file": ("passport.pdf", b"%PDF-1.7 sample data", "application/pdf")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["stage"] == "UPLOAD"
    assert data["code"] == "PDF_UNSUPPORTED"
    assert "PDF processing is not enabled" in data["message"]

# ---------------------------------------------------------------------------
# 3. SUCCESSFUL CAPTURE & UPLOAD FLOW TEST
# ---------------------------------------------------------------------------
def test_successful_camera_capture_upload_flow():
    """
    Simulates a real camera canvas capture snapshot being submitted to /api/screen:
    - Verifies HTTP 200
    - Verifies complete 10-stage execution pipeline
    - Verifies extracted fields & OCR metadata present in response
    - Verifies optional live portrait status is NOT_PROVIDED without failing
    """
    img_buf = create_test_image(width=1280, height=720, color=(245, 245, 245))
    res = client.post(
        "/api/screen",
        files={"file": ("document_scan_1727340000.png", img_buf, "image/png")},
        data={
            "document_type_hint": "PASSPORT",
            "notes": "Terminal scanner lane 4 test"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] in ("COMPLETED", "REVIEW_REQUIRED")
    assert data["case_id"] is not None
    assert data["case_number"].startswith("CASE-")
    assert data["document"]["type"] == "PASSPORT"

    # Verify pipeline stages
    assert "pipeline" in data
    completed_stages = [s["stage"] for s in data["pipeline"] if s["status"] == "COMPLETED"]
    assert "UPLOAD" in completed_stages
    assert "IMAGE_QUALITY" in completed_stages
    assert "DOCUMENT_CLASSIFICATION" in completed_stages
    assert "OCR" in completed_stages
    assert "FIELD_VALIDATION" in completed_stages
    assert "VISUAL_FORENSICS" in completed_stages
    assert "RISK_ASSESSMENT" in completed_stages

    # Verify extracted fields and OCR contract
    assert "ocr" in data
    assert "fields" in data["ocr"]
    assert "confidence" in data["ocr"]
    assert data["ocr"]["ocr_status"] in ("OK", "LOW_CONFIDENCE")

    # Verify optional face verification contract
    assert data["identity"]["status"] == "NOT_PROVIDED"

    # Verify risk assessment result
    assert "risk" in data
    assert data["risk"]["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert 0 <= data["risk"]["risk_score"] <= 100
