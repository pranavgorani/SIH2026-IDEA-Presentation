import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from backend.app.models.database import AuditEvent, generate_uuid, utc_now

GENESIS_HASH = "0" * 64

class AuditService:
    @staticmethod
    def calculate_event_hash(
        sequence_number: int,
        case_id: str,
        actor_id: str,
        action: str,
        timestamp_str: str,
        details: Optional[Dict[str, Any]],
        previous_hash: str
    ) -> str:
        """
        Computes SHA-256 cryptographic hash of event payload and predecessor hash.
        """
        payload = {
            "seq": sequence_number,
            "case_id": case_id,
            "actor_id": actor_id,
            "action": action,
            "timestamp": timestamp_str,
            "details": details or {},
            "previous_hash": previous_hash
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def record_event(
        cls,
        db: Session,
        case_id: str,
        actor_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Appends an immutable tamper-evident event to the case's hash chain.
        """
        last_event = db.query(AuditEvent).filter(
            AuditEvent.case_id == case_id
        ).order_by(AuditEvent.sequence_number.desc()).first()

        if last_event:
            seq = last_event.sequence_number + 1
            prev_hash = last_event.event_hash
        else:
            seq = 1
            prev_hash = GENESIS_HASH

        now_dt = utc_now()
        now_str = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        event_hash = cls.calculate_event_hash(
            sequence_number=seq,
            case_id=case_id,
            actor_id=actor_id,
            action=action,
            timestamp_str=now_str,
            details=details,
            previous_hash=prev_hash
        )

        event = AuditEvent(
            id=generate_uuid(),
            case_id=case_id,
            actor_id=actor_id,
            action=action,
            details=details,
            previous_hash=prev_hash,
            event_hash=event_hash,
            sequence_number=seq,
            timestamp=now_dt
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def verify_case_chain(cls, db: Session, case_id: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """
        Audits cryptographic integrity of the entire event chain for a case.
        Returns (is_valid, status_message, list_of_audit_steps).
        """
        events = db.query(AuditEvent).filter(
            AuditEvent.case_id == case_id
        ).order_by(AuditEvent.sequence_number.asc()).all()

        if not events:
            return True, "No audit events recorded yet.", []

        steps = []
        expected_prev_hash = GENESIS_HASH

        for ev in events:
            # Check previous hash link
            if ev.previous_hash != expected_prev_hash:
                steps.append({
                    "seq": ev.sequence_number,
                    "action": ev.action,
                    "status": "COMPROMISED",
                    "reason": f"Hash chain broken: previous_hash mismatch at block #{ev.sequence_number}"
                })
                return False, "Audit Integrity: MODIFIED / INVALID (Hash chain broken)", steps

            # Recompute event hash
            ts_str = ev.timestamp.strftime("%Y-%m-%dT%H:%M:%SZ") if hasattr(ev.timestamp, "strftime") else str(ev.timestamp)
            recomputed = cls.calculate_event_hash(
                sequence_number=ev.sequence_number,
                case_id=ev.case_id,
                actor_id=ev.actor_id,
                action=ev.action,
                timestamp_str=ts_str,
                details=ev.details,
                previous_hash=ev.previous_hash
            )

            if recomputed != ev.event_hash:
                steps.append({
                    "seq": ev.sequence_number,
                    "action": ev.action,
                    "status": "COMPROMISED",
                    "reason": f"Payload altered: recomputed hash {recomputed[:12]} does not match block hash {ev.event_hash[:12]}"
                })
                return False, "Audit Integrity: MODIFIED / INVALID (Event content altered)", steps

            steps.append({
                "seq": ev.sequence_number,
                "action": ev.action,
                "status": "VERIFIED",
                "hash": ev.event_hash[:16] + "..."
            })
            expected_prev_hash = ev.event_hash

        return True, "Audit Integrity: VERIFIED (Cryptographic SHA-256 hash chain intact)", steps

audit_service = AuditService()
