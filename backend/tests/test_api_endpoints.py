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
    assert data["status"] == "ONLINE"
    assert data["service"] == "TRUST-ID"

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
