
import hashlib
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import get_identity_db
from app.database.identity_models import (
    RegistryPerson,
    RegistryWatchlist,
    RegistryDocument,
    RegistryDocumentAudit,
    RegistryVerification,
)

router = APIRouter(
    prefix="/registry",
    tags=["Identity Registry"],
)


# 1. Get all registered demo people
@router.get("/people")
def get_registry_people(
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    people = (
        db.query(RegistryPerson)
        .order_by(RegistryPerson.person_code)
        .all()
    )

    return [
        {
            "person_code": person.person_code,
            "full_name": person.full_name,
            "date_of_birth": person.date_of_birth,
            "city": person.city,
            "demo_status": person.demo_status,
            "is_active": person.is_active,
        }
        for person in people
    ]


# 2. Get one person by demo code
@router.get("/people/{person_code}")
def get_registry_person(
    person_code: str,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    person = (
        db.query(RegistryPerson)
        .filter(RegistryPerson.person_code == person_code)
        .first()
    )

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Demo person not found",
        )

    return {
        "person_code": person.person_code,
        "full_name": person.full_name,
        "date_of_birth": person.date_of_birth,
        "city": person.city,
        "demo_status": person.demo_status,
        "is_active": person.is_active,
    }


# 3. Get fictional watchlist records
@router.get("/watchlist")
def get_registry_watchlist(
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    records = (
        db.query(RegistryWatchlist)
        .order_by(RegistryWatchlist.reference_id)
        .all()
    )

    return [
        {
            "reference_id": record.reference_id,
            "fictional_name": record.fictional_name,
            "demo_reason": record.demo_reason,
            "risk_level": record.risk_level,
        }
        for record in records
    ]


# 4. List uploaded identity documents
@router.get("/documents")
def get_registry_documents(
    status: str = None,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    query = (
        db.query(RegistryDocument, RegistryPerson)
        .join(
            RegistryPerson,
            RegistryDocument.person_id == RegistryPerson.id,
        )
    )

    if status:
        status = status.strip().upper()

        if status not in {
            "PENDING_REVIEW",
            "APPROVED",
            "REJECTED",
        }:
            raise HTTPException(
                status_code=400,
                detail="Invalid status filter",
            )

        query = query.filter(
            RegistryDocument.demo_status == status
        )

    results = query.order_by(RegistryDocument.id.desc()).all()
    response = []

    for document, person in results:
        # OCR results are linked through the document ID recorded
        # in the explanation, because the current model stores
        # verification rows against a person rather than a document.
        ocr_result = (
            db.query(RegistryVerification)
            .filter(
                RegistryVerification.person_id == person.id,
                RegistryVerification.explanation.like(
                    f"OCR document ID: {document.id};%"
                ),
            )
            .order_by(
                RegistryVerification.created_at.desc(),
                RegistryVerification.id.desc(),
            )
            .first()
        )

        response.append({
            "document_id": document.id,
            "person_code": person.person_code,
            "full_name": person.full_name,
            "document_type": document.document_type,
            "file_hash": document.file_hash,
            "status": document.demo_status,
            "ocr_available": ocr_result is not None,
            "ocr_status": (
                ocr_result.status if ocr_result else None
            ),
            "ocr_explanation": (
                ocr_result.explanation if ocr_result else None
            ),
            "ocr_analyzed_at": (
                ocr_result.created_at.isoformat()
                if ocr_result and ocr_result.created_at
                else None
            ),
            "manual_review_required": (
                ocr_result is None
                or ocr_result.status != "FIELDS_MATCH_REQUIRES_REVIEW"
            ),
        })

    return response


# Helper: find the latest hashed audit record
def get_latest_hashed_audit(db: Session):
    return (
        db.query(RegistryDocumentAudit)
        .filter(RegistryDocumentAudit.audit_hash.isnot(None))
        .order_by(RegistryDocumentAudit.id.desc())
        .first()
    )


# 5. Admin review with SHA-256 audit logging
@router.put("/documents/{document_id}/review")
def review_registry_document(
    document_id: int,
    decision: str,
    reason: str,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    decision = decision.strip().upper()
    reason = reason.strip()

    if decision not in {"APPROVED", "REJECTED"}:
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVED or REJECTED",
        )

    if not reason:
        raise HTTPException(
            status_code=400,
            detail="A review reason is required",
        )

    document = (
        db.query(RegistryDocument)
        .filter(RegistryDocument.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if document.demo_status != "PENDING_REVIEW":
        raise HTTPException(
            status_code=409,
            detail="Document has already been reviewed",
        )

    # Fetch OCR evidence for this exact document, not merely its person.
    ocr_result = (
        db.query(RegistryVerification)
        .filter(
            RegistryVerification.person_id == document.person_id,
            RegistryVerification.explanation.like(
                f"OCR document ID: {document.id};%"
            ),
        )
        .order_by(
            RegistryVerification.created_at.desc(),
            RegistryVerification.id.desc(),
        )
        .first()
    )

    reviewer = (
        getattr(current_admin, "email", None)
        or getattr(current_admin, "username", None)
        or str(getattr(current_admin, "id", "unknown"))
    )
    reviewer = str(reviewer)

    latest_audit = get_latest_hashed_audit(db)
    previous_hash = (
        latest_audit.audit_hash if latest_audit else None
    )

    reviewed_at = datetime.utcnow()

    # Save the exact OCR evidence snapshot used for this review.
    ocr_evidence = {
        "available": ocr_result is not None,
        "status": ocr_result.status if ocr_result else None,
        "explanation": (
            ocr_result.explanation if ocr_result else None
        ),
        "analyzed_at": (
            ocr_result.created_at.isoformat()
            if ocr_result and ocr_result.created_at
            else None
        ),
        "manual_review_required": True,
    }

    # Hash the review and its OCR evidence deterministically.
    audit_payload = {
        "document_id": document.id,
        "reviewer": reviewer,
        "decision": decision,
        "reason": reason,
        "reviewed_at": reviewed_at.isoformat(),
        "previous_hash": previous_hash,
        "ocr_evidence": ocr_evidence,
    }

    canonical_payload = json.dumps(
        audit_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    audit_hash = hashlib.sha256(
        canonical_payload.encode("utf-8")
    ).hexdigest()

    audit = RegistryDocumentAudit(
        document_id=document.id,
        reviewer_identifier=reviewer,
        decision=decision,
        reason=reason,
        created_at=reviewed_at,
        audit_hash=audit_hash,
        previous_hash=previous_hash,
        ocr_evidence=json.dumps(
            ocr_evidence,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ),
    )

    document.demo_status = decision
    db.add(audit)

    try:
        db.commit()
        db.refresh(document)
        db.refresh(audit)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save review and audit record",
        )

    return {
        "message": "Document review completed",
        "document_id": document.id,
        "previous_status": "PENDING_REVIEW",
        "status": document.demo_status,
        "audit_id": audit.id,
        "reviewer": audit.reviewer_identifier,
        "reason": audit.reason,
        "reviewed_at": audit.created_at,
        "audit_hash": audit.audit_hash,
        "previous_hash": audit.previous_hash,
        "ocr_evidence": ocr_evidence,
    }


# 6. View document review audit history
@router.get("/documents/{document_id}/audit")
def get_document_audit_history(
    document_id: int,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    document = (
        db.query(RegistryDocument)
        .filter(RegistryDocument.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    records = (
        db.query(RegistryDocumentAudit)
        .filter(
            RegistryDocumentAudit.document_id == document_id
        )
        .order_by(RegistryDocumentAudit.id.desc())
        .all()
    )

    return [
        {
            "audit_id": record.id,
            "document_id": record.document_id,
            "reviewer": record.reviewer_identifier,
            "decision": record.decision,
            "reason": record.reason,
            "reviewed_at": record.created_at,
            "audit_hash": record.audit_hash,
            "previous_hash": record.previous_hash,
            "ocr_evidence": (
                json.loads(record.ocr_evidence)
                if record.ocr_evidence
                else None
            ),
        }
        for record in records
    ]

# 7. Verify SHA-256 audit integrity

# 7. Verify SHA-256 audit integrity
@router.get("/audit/integrity/{audit_id}")
def verify_audit_integrity(
    audit_id: int,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    record = (
        db.query(RegistryDocumentAudit)
        .filter(RegistryDocumentAudit.id == audit_id)
        .first()
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Audit record not found",
        )

    # Recreate the original payload used by the review function.
    base_payload = {
        "document_id": record.document_id,
        "reviewer": record.reviewer_identifier,
        "decision": record.decision,
        "reason": record.reason,
        "previous_hash": record.previous_hash,
    }

    # Also check the format that includes the review timestamp.
    timestamp_payload = {
        **base_payload,
        "reviewed_at": record.created_at.isoformat(),
    }

    def calculate_hash(payload):
        canonical_payload = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(
            canonical_payload.encode("utf-8")
        ).hexdigest()

    candidates = [
        ("timestamp_not_included", base_payload),
        ("timestamp_included", timestamp_payload),
    ]

    if record.ocr_evidence:
        try:
            stored_evidence = json.loads(record.ocr_evidence)
        except (TypeError, json.JSONDecodeError):
            stored_evidence = None

        if stored_evidence is not None:
            candidates.append((
                "timestamp_and_ocr_evidence_included",
                {
                    **timestamp_payload,
                    "ocr_evidence": stored_evidence,
                },
            ))

    matched = next(
        (
            (name, calculate_hash(payload))
            for name, payload in candidates
            if calculate_hash(payload) == record.audit_hash
        ),
        None,
    )

    is_valid = matched is not None
    if matched:
        matched_format, recalculated_hash = matched
    else:
        matched_format = None
        recalculated_hash = calculate_hash(timestamp_payload)

    return {
        "audit_id": record.id,
        "document_id": record.document_id,
        "stored_hash": record.audit_hash,
        "recalculated_hash": recalculated_hash,
        "integrity_valid": is_valid,
        "matched_format": matched_format,
        "message": (
            "Audit hash matches the stored review details"
            if is_valid
            else "Audit hash mismatch: investigate the record"
        ),
    }


# 8. Verify the complete SHA-256 audit chain

# 8. Verify hashed audit chain and report legacy records
@router.get("/audit/chain/verify")
def verify_audit_chain(
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    records = (
        db.query(RegistryDocumentAudit)
        .order_by(RegistryDocumentAudit.id.asc())
        .all()
    )

    legacy_records = [
        {
            "audit_id": r.id,
            "document_id": r.document_id,
            "issue": "MISSING_AUDIT_HASH",
        }
        for r in records
        if not r.audit_hash
    ]

    hashed_records = [r for r in records if r.audit_hash]
    issues = []

    def calculate_hash(payload):
        canonical_payload = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(
            canonical_payload.encode("utf-8")
        ).hexdigest()

    for index, record in enumerate(hashed_records):
        base_payload = {
            "document_id": record.document_id,
            "reviewer": record.reviewer_identifier,
            "decision": record.decision,
            "reason": record.reason,
            "previous_hash": record.previous_hash,
        }

        timestamp_payload = {
            **base_payload,
            "reviewed_at": record.created_at.isoformat(),
        }

        accepted_hashes = {
            calculate_hash(base_payload),
            calculate_hash(timestamp_payload),
        }

        if record.ocr_evidence:
            try:
                stored_evidence = json.loads(record.ocr_evidence)
            except (TypeError, json.JSONDecodeError):
                stored_evidence = None

            if stored_evidence is not None:
                evidence_payload = {
                    **timestamp_payload,
                    "ocr_evidence": stored_evidence,
                }
                accepted_hashes.add(
                    calculate_hash(evidence_payload)
                )

        if record.audit_hash not in accepted_hashes:
            issues.append({
                "audit_id": record.id,
                "issue": "AUDIT_HASH_MISMATCH",
            })

        expected_previous_hash = (
            hashed_records[index - 1].audit_hash
            if index > 0
            else None
        )

        if record.previous_hash != expected_previous_hash:
            issues.append({
                "audit_id": record.id,
                "issue": "PREVIOUS_HASH_LINK_MISMATCH",
                "expected_previous_hash": expected_previous_hash,
                "actual_previous_hash": record.previous_hash,
            })

    chain_valid = len(issues) == 0
    complete = chain_valid and len(legacy_records) == 0

    if not records:
        message = "No audit records exist yet."
    elif not chain_valid:
        message = "Hashed audit chain verification failed."
    elif legacy_records:
        message = (
            "Hashed chain passed, but legacy unhashed records "
            "remain unverified."
        )
    else:
        message = "Complete audit chain verification passed."

    return {
        "chain_valid": chain_valid,
        "complete": complete,
        "records_checked": len(records),
        "hashed_records_checked": len(hashed_records),
        "legacy_records": legacy_records,
        "issues": issues,
        "message": message,
    }
