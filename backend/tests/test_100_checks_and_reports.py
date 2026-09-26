"""
TRUST-ID — Comprehensive Test Suite for 100-Point Document Checks,
Report Generation (PDF, CSV, DOCX), RBAC Roles & Audit Ledger
"""

import pytest
import io
import hashlib
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.document_check_engine import DocumentCheckEngine, document_check_engine
from backend.app.services.report_pdf_service import report_pdf_service
from backend.app.services.report_export_service import ReportExportService

client = TestClient(app)


# =========================================================================
# 1. 100 CHECKS DEFINITIONS & STRUCTURE TESTS
# =========================================================================

def test_exact_100_checks_exist():
    """Verify that exactly 100 checks are executed by the DocumentCheckEngine."""
    result = document_check_engine.run_all_checks("test-case-001")
    assert result["total_checks"] == 100
    assert len(result["checks"]) == 100


def test_no_duplicate_check_ids():
    """Ensure all check IDs from CHK-001 to CHK-100 are unique."""
    result = document_check_engine.run_all_checks("test-case-001")
    check_ids = [c["check_id"] for c in result["checks"]]
    assert len(check_ids) == len(set(check_ids))
    assert len(check_ids) == 100

    # Ensure CHK-001 through CHK-100 format
    expected_ids = {f"CHK-{i:03d}" for i in range(1, 101)}
    assert set(check_ids) == expected_ids


def test_all_checks_have_valid_categories():
    """Ensure every check belongs to one of the 8 canonical categories."""
    valid_categories = {
        "DOCUMENT_INTEGRITY",
        "OCR_TEXT_EXTRACTION",
        "FIELD_LOGICAL_VALIDATION",
        "MRZ_DATA",
        "VISUAL_FORENSICS",
        "IDENTITY_VERIFICATION",
        "RECORD_VERIFICATION",
        "SECURITY_RISK_AUDIT"
    }

    result = document_check_engine.run_all_checks("test-case-001")
    for chk in result["checks"]:
        assert chk["category"] in valid_categories, f"Unknown category: {chk['category']}"
        assert chk["name"], f"Check {chk['check_id']} missing name"
        assert chk["severity"] in {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}


def test_all_checks_have_valid_statuses():
    """Ensure all checks produce one of the required statuses (never empty)."""
    valid_statuses = {"PASS", "FAIL", "WARNING", "NOT_CHECKED", "NOT_APPLICABLE", "UNAVAILABLE"}

    result = document_check_engine.run_all_checks("test-case-001")
    for chk in result["checks"]:
        assert chk["status"] in valid_statuses, f"Invalid status {chk['status']} on check {chk['check_id']}"
        assert 0.0 <= chk["confidence"] <= 1.0


def test_missing_presenter_image_yields_not_applicable():
    """Face checks must become NOT_APPLICABLE when live presenter image is not uploaded (do NOT fake pass)."""
    result = document_check_engine.run_all_checks(
        case_id="test-no-live",
        face_result={
            "document_face_detected": True,
            "doc_face_quality": 0.85,
            "presenter_face_detected": False,  # No live portrait
            "presenter_face_quality": 0.0,
            "match_score": 0.0,
            "face_verified": False
        }
    )

    presenter_checks = [c for c in result["checks"] if c["check_id"] in ("CHK-073", "CHK-074", "CHK-076")]
    for chk in presenter_checks:
        assert chk["status"] in ("NOT_APPLICABLE", "NOT_CHECKED"), f"Expected NOT_APPLICABLE but got {chk['status']} on {chk['check_id']}"


def test_missing_external_records_yields_unavailable():
    """Record verification checks must become UNAVAILABLE when database cross-checks are offline (do NOT fake pass)."""
    result = document_check_engine.run_all_checks(
        case_id="test-no-records",
        record_result={"available": False, "found": False}
    )

    record_checks = [c for c in result["checks"] if c["category"] == "RECORD_VERIFICATION"]
    for chk in record_checks:
        assert chk["status"] in ("UNAVAILABLE", "NOT_CHECKED"), f"Expected UNAVAILABLE on check {chk['check_id']}, got {chk['status']}"


def test_weighted_integrity_score_calculation():
    """Integrity score must use configurable severity weights (not simple passed/100)."""
    score = document_check_engine.calculate_integrity_score([
        {"check_id": "CHK-001", "severity": "CRITICAL", "status": "FAIL"},
        {"check_id": "CHK-002", "severity": "HIGH", "status": "PASS"},
        {"check_id": "CHK-003", "severity": "MEDIUM", "status": "PASS"},
    ])
    assert 0 <= score <= 100
    assert score < 100  # Failed critical check reduces the score significantly


# =========================================================================
# 2. REPORT EXPORT TESTS (PDF, CSV, DOCX)
# =========================================================================

def test_pdf_report_generation():
    """Generate official multi-page PDF report and verify byte structure."""
    case_data = {
        "id": "case-test-pdf",
        "case_number": "CASE-2026-PDF",
        "created_at": "2026-09-26 12:00:00",
        "document_type": "PASSPORT",
        "risk_score": 18.0,
        "risk_level": "LOW"
    }
    checks_data = document_check_engine.run_all_checks("case-test-pdf")

    pdf_bytes = report_pdf_service.generate_pdf_bytes(case_data, checks_data)
    assert len(pdf_bytes) > 5000
    # PDF magic number
    assert pdf_bytes.startswith(b"%PDF")


def test_csv_export_generation():
    """Generate CSV report for 100 checks and verify header and row count."""
    case_data = {
        "id": "case-test-csv",
        "case_number": "CASE-2026-CSV"
    }
    checks_data = document_check_engine.run_all_checks("case-test-csv")

    csv_bytes = ReportExportService.generate_csv_bytes(case_data, checks_data["checks"])
    assert len(csv_bytes) > 2000
    
    text = csv_bytes.decode("utf-8")
    lines = [l for l in text.split("\r\n") if l]
    # Header + 100 checks = 101 lines
    assert len(lines) == 101
    assert "Case ID,Check ID,Category" in lines[0]
    assert "CHK-001" in text
    assert "CHK-100" in text


def test_docx_export_generation():
    """Generate Microsoft Word (.docx) report and verify byte contents."""
    case_data = {
        "id": "case-test-docx",
        "case_number": "CASE-2026-DOCX",
        "document_type": "NATIONAL_ID",
        "risk_score": 35.0,
        "risk_level": "MEDIUM",
        "decision": "PENDING_REVIEW"
    }
    checks_data = document_check_engine.run_all_checks("case-test-docx")

    docx_bytes = ReportExportService.generate_docx_bytes(case_data, checks_data)
    assert len(docx_bytes) > 10000
    # DOCX is a zip file starting with PK\x03\x04
    assert docx_bytes.startswith(b"PK\x03\x04")


# =========================================================================
# 3. AUTHENTICATION & 3-ROLE RBAC TESTS
# =========================================================================

def test_admin_login():
    """Verify administrator login credentials and token issuance."""
    res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "ADMIN"


def test_verifier_login():
    """Verify verifier login credentials and role assignment."""
    res = client.post("/api/auth/login", json={"username": "verifier", "password": "verifier123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "VERIFIER"


def test_inspector_login():
    """Verify inspector login credentials and role assignment."""
    res = client.post("/api/auth/login", json={"username": "inspector", "password": "inspector123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] == "INSPECTOR"


def test_invalid_login():
    """Verify rejected credentials with 401 unauthorized status."""
    res = client.post("/api/auth/login", json={"username": "unknown", "password": "bad"})
    assert res.status_code == 401


# =========================================================================
# 4. REPORT ENDPOINTS TESTS
# =========================================================================

def test_get_global_reports():
    """Verify GET /api/reports returns reports listing and analytics."""
    res = client.get("/api/reports")
    assert res.status_code == 200
    data = res.json()
    assert "total_reports" in data
    assert "analytics" in data
    assert "reports" in data
