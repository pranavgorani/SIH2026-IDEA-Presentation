from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.app.models.database import get_db, Case, AuditEvent
from backend.app.models.schemas import AuditEventResponse, AuditIntegrityResponse
from backend.app.services.audit_service import audit_service

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Ledger"])

@router.get("/{case_id}", summary="Fetch immutable event history for a case")
def get_case_audit_log(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    events = db.query(AuditEvent).filter(
        AuditEvent.case_id == case_id
    ).order_by(AuditEvent.sequence_number.asc()).all()

    return [
        AuditEventResponse(
            id=e.id, case_id=e.case_id, actor_id=e.actor_id, action=e.action,
            details=e.details, previous_hash=e.previous_hash, event_hash=e.event_hash,
            sequence_number=e.sequence_number, timestamp=e.timestamp
        ) for e in events
    ]

@router.get("/{case_id}/verify", response_model=AuditIntegrityResponse, summary="Cryptographically verify SHA-256 hash chain")
def verify_audit_integrity(case_id: str, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    is_valid, msg, steps = audit_service.verify_case_chain(db, case_id)
    last_event = db.query(AuditEvent).filter(
        AuditEvent.case_id == case_id
    ).order_by(AuditEvent.sequence_number.desc()).first()

    return AuditIntegrityResponse(
        status="VERIFIED" if is_valid else "COMPROMISED",
        total_events=len(steps),
        is_valid=is_valid,
        verified_at=datetime.now(timezone.utc),
        last_block_hash=last_event.event_hash if last_event else ("0" * 64)
    )
