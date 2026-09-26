import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

from backend.app.models.database import init_db, SessionLocal
from backend.app.api.auth import seed_demo_users_if_needed
from backend.app.services.synthetic_generator import synthetic_generator

init_db()
_db = SessionLocal()
seed_demo_users_if_needed(_db)
_db.close()
synthetic_generator.generate_all_presets()

client = TestClient(app)

def test_health_check_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "ONLINE")
    assert data["service"] == "TRUST-ID"
    assert "services" in data

def test_login_demo_verifier():
    res = client.post("/api/auth/login", json={"username": "verifier", "password": "verifier123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "VERIFIER"

def test_login_invalid_credentials():
    res = client.post("/api/auth/login", json={"username": "wrong", "password": "wrongpassword"})
    assert res.status_code == 401

def test_demo_scenario_execution():
    # Execute CASE-001 (Genuine)
    res = client.post("/api/cases/demo/CASE-001")
    assert res.status_code == 200
    data = res.json()
    assert "case_id" in data
    assert data["risk_level"] == "LOW"

    # Fetch case details
    case_id = data["case_id"]
    det_res = client.get(f"/api/cases/{case_id}")
    assert det_res.status_code == 200
    det = det_res.json()
    assert det["ocr_result"] is not None
    assert det["validation_summary"] is not None
    assert det["tamper_result"] is not None
    assert len(det["audit_events"]) >= 1

def test_demo_expired_scenario():
    # Execute CASE-004 (Expired)
    res = client.post("/api/cases/demo/CASE-004")
    assert res.status_code == 200
    data = res.json()
    assert data["risk_level"] == "HIGH"

def test_human_review_submission():
    # Execute CASE-004 and submit human review
    res = client.post("/api/cases/demo/CASE-004")
    case_id = res.json()["case_id"]

    # Attempt to submit review without substantive reason on high-risk case
    fail_rev = client.post(f"/api/cases/{case_id}/review", json={
        "decision": "ESCALATE",
        "reason": "bad" # Too short for high-risk case safety rule
    })
    assert fail_rev.status_code == 400

    # Submit valid review
    ok_rev = client.post(f"/api/cases/{case_id}/review", json={
        "decision": "ESCALATE",
        "reason": "Document expired in 2022. Escalating to Senior Border Forensics Officer for manual verification."
    })
    assert ok_rev.status_code == 200
    assert ok_rev.json()["decision"] == "ESCALATE"

def test_screen_document_png_upload():
    # Test uploading credential image with Gemini_Generated_Image filename and no live face
    with open("backend/storage/synthetic/CASE-001_doc.png", "rb") as f:
        res = client.post(
            "/api/screen",
            files={"file": ("Gemini_Generated_Image_019283.png", f, "image/png")},
            data={"document_type_hint": "AUTO_DETECT"}
        )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] in ("COMPLETED", "REVIEW_REQUIRED")
    assert "pipeline" in data
    assert len(data["pipeline"]) >= 10
    assert data["identity"]["status"] == "NOT_PROVIDED"
    assert data["risk"]["unavailable_checks"] == ["FACE_VERIFICATION"]

def test_screen_document_pdf_unsupported():
    res = client.post(
        "/api/screen",
        files={"file": ("document.pdf", b"%PDF-1.4 dummy header", "application/pdf")},
        data={"document_type_hint": "AUTO_DETECT"}
    )
    assert res.status_code == 400
    data = res.json()
    assert data["success"] is False
    assert data["stage"] == "UPLOAD"
    assert data["code"] == "PDF_UNSUPPORTED"
    assert "PDF processing is not enabled" in data["message"]

def test_health_ai_endpoint():
    res = client.get("/api/health/ai")
    assert res.status_code == 200
    data = res.json()
    assert "gemini" in data
    assert "local_cv" in data
    assert data["local_cv"]["available"] is True
