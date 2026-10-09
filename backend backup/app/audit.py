import hashlib
import json

from sqlalchemy.orm import Session

from app.database.models import Audit


def create_audit_log(
    db: Session,
    username: str,
    action: str,
    details: dict,
):
    """
    Create a tamper-evident audit record.

    Each record contains the hash of the previous
    record, creating a SHA-256 hash chain.
    """

    last_record = (
        db.query(Audit)
        .order_by(Audit.id.desc())
        .first()
    )

    previous_hash = (
        last_record.record_hash
        if last_record
        else "GENESIS"
    )

    payload = {
        "username": username,
        "action": action,
        "details": details,
        "previous_hash": previous_hash,
    }

    record_hash = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()

    audit = Audit(
        username=username,
        action=action,
        details=json.dumps(details),
        previous_hash=previous_hash,
        record_hash=record_hash,
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return audit


def verify_audit_chain(db: Session):
    """
    Verify the complete audit hash chain.

    Returns the first broken record if tampering
    or corruption is detected.
    """

    records = (
        db.query(Audit)
        .order_by(Audit.id.asc())
        .all()
    )

    expected_previous_hash = "GENESIS"

    for record in records:

        # Check previous hash linkage
        if record.previous_hash != expected_previous_hash:
            return {
                "valid": False,
                "tampered": True,
                "record_id": record.id,
                "reason": "Previous hash link is broken",
            }

        try:
            details = json.loads(record.details)
        except (TypeError, json.JSONDecodeError):
            details = record.details

        payload = {
            "username": record.username,
            "action": record.action,
            "details": details,
            "previous_hash": record.previous_hash,
        }

        calculated_hash = hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        ).hexdigest()

        # Check record's own hash
        if record.record_hash != calculated_hash:
            return {
                "valid": False,
                "tampered": True,
                "record_id": record.id,
                "reason": "Record hash does not match its contents",
            }

        expected_previous_hash = record.record_hash

    return {
        "valid": True,
        "tampered": False,
        "records_checked": len(records),
        "message": "Audit chain integrity verified",
    }