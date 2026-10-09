import hashlib

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit import create_audit_log
from app.auth.dependencies import (
    get_current_admin,
    require_roles,
)
from app.database.connection import get_db
from app.database.models import (
    IdentityDocument,
    Person,
    QR,
)


router = APIRouter(
    prefix="/qr",
    tags=["QR Verification"],
)


class QRVerifyRequest(BaseModel):
    token: str


@router.post("/verify")
def verify_qr(
    qr_data: QRVerifyRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(
    require_roles(
        "ADMIN",
        "SUPER_ADMIN",
    )
),
):
    """
    Authority-side QR verification.

    The authority scans the QR shown by the person
    and submits the token to the backend.

    Raw documents are never returned by this endpoint.
    """

    # =================================================
    # 1. HASH SUBMITTED QR TOKEN
    # =================================================

    submitted_hash = hashlib.sha256(
        qr_data.token.encode("utf-8")
    ).hexdigest()

    # =================================================
    # 2. FIND QR RECORD
    # =================================================

    qr_record = (
        db.query(QR)
        .filter(
            QR.qr_hash == submitted_hash
        )
        .first()
    )

    if not qr_record:
        return {
            "verified": False,
            "status": "FAIL",
            "reason": "Invalid or unrecognized QR token",
        }

    # =================================================
    # 3. FIND REGISTERED PERSON
    # =================================================

    person = (
        db.query(Person)
        .filter(
            Person.id == qr_record.person_id,
            Person.is_active == True,
        )
        .first()
    )

    if not person:
        return {
            "verified": False,
            "status": "FAIL",
            "reason": "Registered identity is unavailable",
        }

    # =================================================
    # 4. CHECK REGISTERED DOCUMENTS
    # =================================================

    documents = (
        db.query(IdentityDocument)
        .filter(
            IdentityDocument.person_id == person.id
        )
        .all()
    )

    document_count = len(documents)

    document_check = document_count > 0

    # =================================================
    # 5. BASIC IDENTITY COMPLETENESS
    # =================================================

    required_fields = [
        person.full_name,
        person.date_of_birth,
        person.gender,
        person.identity_number,
        person.phone,
        person.email,
    ]

    complete_identity = all(
        field is not None
        and str(field).strip() != ""
        for field in required_fields
    )

    # =================================================
    # 6. CALCULATE DEMO RISK SCORE
    # =================================================

    risk_score = 0

    reasons = []

    if not document_check:
        risk_score += 40
        reasons.append(
            "No registered identity document found"
        )

    if not complete_identity:
        risk_score += 30
        reasons.append(
            "Identity record is incomplete"
        )

    # QR itself is valid, therefore no QR risk added.

    if risk_score < 30:
        risk_level = "LOW"
        status = "PASS"

    elif risk_score < 60:
        risk_level = "MEDIUM"
        status = "REVIEW"

    else:
        risk_level = "HIGH"
        status = "FAIL"

    # =================================================
    # 7. RETURN MINIMUM NECESSARY INFORMATION
    # =================================================

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="QR_VERIFICATION",
        details={
            "person_id": person.id,
            "status": status,
            "risk_score": risk_score,
            "risk_level": risk_level,
            },
            )
    
    return {
        "verified": status == "PASS",
        "status": status,
        "person": {
            "id": person.id,
            "full_name": person.full_name,
            "date_of_birth": person.date_of_birth,
            "gender": person.gender,
        },
        "verification": {
            "qr_valid": True,
            "identity_record_found": True,
            "document_check": document_check,
            "registered_document_count": document_count,
            "identity_complete": complete_identity,
        },
        "risk": {
            "score": risk_score,
            "level": risk_level,
            "reasons": reasons,
        },
    }