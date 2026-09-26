import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.database import Base, AuditEvent
from backend.app.services.audit_service import audit_service

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_audit_hash_chain_creation_and_verification(test_db):
    case_id = "test-case-123"

    # Append 3 sequential events
    ev1 = audit_service.record_event(test_db, case_id, "admin", "CASE_CREATED", {"source": "web"})
    ev2 = audit_service.record_event(test_db, case_id, "ocr_engine", "OCR_EXTRACTED", {"fields": 5})
    ev3 = audit_service.record_event(test_db, case_id, "verifier", "CASE_APPROVED", {"rationale": "checked"})

    assert ev1.sequence_number == 1
    assert ev2.sequence_number == 2
    assert ev3.sequence_number == 3

    # Check previous_hash chain linkage
    assert ev2.previous_hash == ev1.event_hash
    assert ev3.previous_hash == ev2.event_hash

    # Verify chain
    is_valid, msg, steps = audit_service.verify_case_chain(test_db, case_id)
    assert is_valid is True
    assert "VERIFIED" in msg
    assert len(steps) == 3

def test_audit_hash_chain_detects_tampering(test_db):
    case_id = "tamper-case-456"

    ev1 = audit_service.record_event(test_db, case_id, "admin", "CASE_CREATED", {})
    ev2 = audit_service.record_event(test_db, case_id, "risk_engine", "RISK_CALCULATED", {"score": 85})

    # Maliciously modify ev2 payload in database without recalculating hash
    ev2.details = {"score": 10} # fraudulent alteration!
    test_db.commit()

    is_valid, msg, steps = audit_service.verify_case_chain(test_db, case_id)
    assert is_valid is False
    assert "INVALID" in msg or "COMPROMISED" in msg
