import pytest
from backend.app.models.schemas import ExtractedFields, MRZData
from backend.app.services.validation_service import validation_service

def test_expired_document_detected():
    fields = ExtractedFields(
        name="JOHN DOE",
        document_number="A12345678",
        date_of_birth="1980-01-01",
        date_of_issue="2010-01-01",
        date_of_expiry="2020-01-01", # Expired
        nationality="USA"
    )
    res = validation_service.validate_document_data(fields)
    assert res.valid is False
    assert res.failed_count >= 1
    expiry_check = next(c for c in res.checks if "Expiry" in c.name)
    assert expiry_check.status == "FAIL"

def test_chronological_violation_dob_in_future():
    fields = ExtractedFields(
        name="FUTURE PERSON",
        document_number="B98765432",
        date_of_birth="2099-01-01", # Future
        date_of_issue="2025-01-01",
        date_of_expiry="2035-01-01",
        nationality="DEMO"
    )
    res = validation_service.validate_document_data(fields)
    assert res.valid is False
    chrono_check = next(c for c in res.checks if "Chronological" in c.name)
    assert chrono_check.status == "FAIL"
    assert chrono_check.severity == "CRITICAL"

def test_valid_document_passes():
    fields = ExtractedFields(
        name="ALICE WANG",
        document_number="C55443322",
        date_of_birth="1995-05-15",
        date_of_issue="2020-06-01",
        date_of_expiry="2030-05-31",
        nationality="DEMO"
    )
    res = validation_service.validate_document_data(fields)
    assert res.valid is True
    assert res.failed_count == 0
