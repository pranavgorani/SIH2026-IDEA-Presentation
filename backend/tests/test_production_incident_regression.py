# ==============================================================================
# TRUST-ID Production Incident Regression Test Suite
# Tests all requirements from Section I of incident investigation
# ==============================================================================
import io
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

# 1. Test authoritative import
from backend.main import app as main_app
from backend.app.main import app as backend_app
from backend.app.core.config import get_default_cors, settings

client = TestClient(main_app)

def test_authoritative_imports():
    """Confirms both backend.main:app and backend.app.main:app point to the same app."""
    assert main_app is backend_app
    assert main_app.title == "TRUST-ID — AI-Powered Identity & Document Screening Platform"

def test_health_liveness_check():
    """GET /health returns 200 with alive: True immediately."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["alive"] is True
    assert data["service"] == "TRUST-ID"

def test_health_readiness_check():
    """GET /api/health and /ready return component breakdown."""
    for path in ["/ready", "/api/health", "/api/backend/health"]:
        res = client.get(path)
        assert res.status_code == 200
        data = res.json()
        assert "services" in data
        assert "ocr" in data["services"]
        assert "opencv" in data["services"]
        assert "storage" in data["services"]
        assert data["services"]["opencv"] == "online"

def test_health_screening_pipeline():
    """GET /health/screening returns pipeline readiness."""
    res = client.get("/health/screening")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["pipeline_stages"] == 10

def test_cors_origin_parsing():
    """Tests that CORS parsing handles JSON arrays, comma strings, whitespace, and brackets."""
    import os
    # Test JSON array format
    os.environ["CORS_ORIGINS"] = '["http://localhost:3000", "http://127.0.0.1:3000"]'
    parsed = get_default_cors()
    assert "http://localhost:3000" in parsed
    assert "http://127.0.0.1:3000" in parsed
    assert "[" not in parsed[0]
    assert '"' not in parsed[0]

    # Test Comma-separated format
    os.environ["CORS_ORIGINS"] = 'http://localhost:3000, https://sih2026.vercel.app'
    parsed2 = get_default_cors()
    assert "http://localhost:3000" in parsed2
    assert "https://sih2026.vercel.app" in parsed2

def test_real_image_ocr_flow():
    """Tests that a real image reaches the OCR engine and extracts text and fields."""
    img = np.full((350, 600, 3), 255, dtype=np.uint8)
    cv2.putText(img, "INCOME TAX DEPARTMENT GOVT OF INDIA", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    cv2.putText(img, "ABCDE1234F", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    cv2.putText(img, "JOHN DOE", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    _, buf = cv2.imencode(".png", img)

    res = client.post(
        "/api/screen",
        files={"file": ("pan.png", buf.tobytes(), "image/png")},
        data={"document_type_hint": "AUTO_DETECT"},
        headers={"X-Correlation-ID": "test-corr-12345"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["document_type"] in ("PAN", "PAN_CARD")
    assert data["document"]["number"] == "ABCDE1234F"
    assert "X-Correlation-ID" in res.headers
    assert res.headers["X-Correlation-ID"] == "test-corr-12345"

def test_ocr_survives_gemini_failure():
    """Forces local fallback and verifies local OCR output is preserved without failure."""
    img = np.full((350, 600, 3), 255, dtype=np.uint8)
    cv2.putText(img, "INCOME TAX DEPARTMENT GOVT OF INDIA", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    cv2.putText(img, "ABCDE1234F", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    _, buf = cv2.imencode(".png", img)

    res = client.post(
        "/api/screen",
        files={"file": ("pan_forced_local.png", buf.tobytes(), "image/png")},
        data={"document_type_hint": "AUTO_DETECT", "force_local_fallback": "true"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["document"]["number"] == "ABCDE1234F"
    assert len(data.get("all_extracted_text", [])) >= 1
    assert data["document_type"] in ("PAN", "PAN_CARD")

def test_unknown_document_preserves_text_without_fraud_assumption():
    """Unknown or unclassified document with text is not marked high-risk fraud."""
    img = np.full((300, 500, 3), 255, dtype=np.uint8)
    cv2.putText(img, "STATE LIBRARY MEMBERSHIP PASS", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
    cv2.putText(img, "MEMBER ID 982132", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
    cv2.putText(img, "VALID UNTIL DEC 2028", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)
    _, buf = cv2.imencode(".png", img)

    res = client.post(
        "/api/screen",
        files={"file": ("membership.png", buf.tobytes(), "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["document_type"] in ("UNKNOWN", "GENERIC_ID")
    assert len(data.get("all_extracted_text", [])) >= 1
    # Check that it did not assert a hardcoded 85.0 fraud score
    assert data.get("risk_score") is None or data.get("risk_score") <= 60.0

def test_corrupted_file_returns_controlled_error():
    """Malformed uploads return structured 400 with CORRUPTED_DOCUMENT error code."""
    res = client.post(
        "/api/screen",
        files={"file": ("corrupt.png", b"this is not an image stream", "image/png")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "CORRUPTED_DOCUMENT"
    assert data["success"] is False
    assert "stage" in data

def test_missing_file_returns_400():
    """Request with no file returns controlled 400 error."""
    res = client.post(
        "/api/screen",
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "MISSING_FILE"

def test_pdf_upload_flow():
    """Ensures a supported multi-page or single-page PDF is converted and OCR-processed."""
    from PIL import Image
    img = np.full((350, 600, 3), 255, dtype=np.uint8)
    cv2.putText(img, "INCOME TAX DEPARTMENT GOVT OF INDIA", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    cv2.putText(img, "ABCDE1234F", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    pdf_buf = io.BytesIO()
    pil_img.save(pdf_buf, format="PDF")

    res = client.post(
        "/api/screen",
        files={"file": ("document.pdf", pdf_buf.getvalue(), "application/pdf")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["document_type"] in ("PAN", "PAN_CARD")
    assert data["document"]["number"] == "ABCDE1234F"

def test_consecutive_uploads_do_not_bleed_state():
    """Verifies that an error upload followed by a valid upload executes cleanly without stale error bleeding."""
    # 1. Trigger controlled 400 failure
    res_bad = client.post(
        "/api/screen",
        files={"file": ("corrupt.png", b"invalid data", "image/png")}
    )
    assert res_bad.status_code == 400

    # 2. Trigger fresh valid upload immediately
    img = np.full((350, 600, 3), 255, dtype=np.uint8)
    cv2.putText(img, "INCOME TAX DEPARTMENT", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    cv2.putText(img, "ABCDE1234F", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    _, buf = cv2.imencode(".png", img)

    res_good = client.post(
        "/api/screen",
        files={"file": ("pan_retry.png", buf.tobytes(), "image/png")}
    )
    assert res_good.status_code == 200
    data = res_good.json()
    assert data["success"] is True
    assert data["document_type"] in ("PAN", "PAN_CARD")
    assert data["document"]["number"] == "ABCDE1234F"

def test_api_response_schema_matches_frontend_contract():
    """Ensures response keys match frontend expectations."""
    img = np.full((350, 600, 3), 255, dtype=np.uint8)
    cv2.putText(img, "INCOME TAX DEPARTMENT", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    cv2.putText(img, "ABCDE1234F", (30, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
    _, buf = cv2.imencode(".png", img)

    res = client.post(
        "/api/screen",
        files={"file": ("pan.png", buf.tobytes(), "image/png")}
    )
    assert res.status_code == 200
    data = res.json()

    # Required contract keys for frontend dashboard
    required_keys = [
        "case_id", "processing_status", "document_type", "document",
        "ocr_status", "validation_status", "field_confidence", "sources",
        "all_extracted_text", "raw_ocr_text", "risk", "final_decision"
    ]
    for key in required_keys:
        assert key in data, f"Missing contract key: {key}"
