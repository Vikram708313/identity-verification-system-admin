from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_admin,
    require_roles,
)
from app.audit import create_audit_log
from app.database.connection import get_db
from app.database.models import (
    IdentityDocument,
    Person,
    Verification,
)


router = APIRouter(
    prefix="/verification",
    tags=["Verification"],
)


# =====================================================
# REQUEST MODELS
# =====================================================

class VerificationRequest(BaseModel):
    person_id: int

    verification_method: str = Field(
        ...,
        description="document or qr",
    )

    face_match_score: float = Field(
        ...,
        ge=0,
        le=100,
    )

    document_match_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    qr_match_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    completeness_score: float = Field(
        default=100,
        ge=0,
        le=100,
    )

    consistency_score: float = Field(
        default=100,
        ge=0,
        le=100,
    )


class DocumentVerificationRequest(BaseModel):
    person_id: int

    document_type: str = Field(
        ...,
        description="Document type, for example AADHAAR",
    )

    document_number: str = Field(
        ...,
        description="Document number extracted from the presented document",
    )

    full_name: str = Field(
        ...,
        description="Name extracted from the presented document",
    )

    date_of_birth: str = Field(
        ...,
        description="Date of birth extracted from the presented document",
    )


class VerificationDecisionRequest(BaseModel):
    decision: str = Field(
        ...,
        description="APPROVE, REVIEW, or REJECT",
    )


# =====================================================
# RISK CALCULATION
# =====================================================

def calculate_risk(
    face_match_score: float,
    document_match_score: Optional[float],
    qr_match_score: Optional[float],
    completeness_score: float,
    consistency_score: float,
):
    """
    Deterministic prototype risk calculation.

    This is NOT a validated fraud probability.
    Lower risk score means fewer verification inconsistencies.
    """

    secondary_score = (
        document_match_score
        if document_match_score is not None
        else qr_match_score
    )

    if secondary_score is None:
        secondary_score = 0

    face_risk = 100 - face_match_score
    secondary_risk = 100 - secondary_score
    completeness_risk = 100 - completeness_score
    consistency_risk = 100 - consistency_score

    risk_score = (
        face_risk * 0.35
        + secondary_risk * 0.30
        + completeness_risk * 0.20
        + consistency_risk * 0.15
    )

    risk_score = round(
        max(0, min(100, risk_score)),
        2,
    )

    if risk_score < 30:
        risk_level = "LOW"
    elif risk_score < 60:
        risk_level = "MEDIUM"
    else:
        risk_level = "HIGH"

    reasons = []

    if face_match_score < 85:
        reasons.append(
            f"Face match score is {face_match_score:.0f}%."
        )

    if secondary_score < 85:
        reasons.append(
            f"Verification document/QR match score is "
            f"{secondary_score:.0f}%."
        )

    if completeness_score < 90:
        reasons.append(
            f"Identity record completeness is "
            f"{completeness_score:.0f}%."
        )

    if consistency_score < 90:
        reasons.append(
            f"Identity data consistency is "
            f"{consistency_score:.0f}%."
        )

    if not reasons:
        reasons.append(
            "Verification signals are within the configured "
            "prototype thresholds."
        )

    return risk_score, risk_level, reasons


# =====================================================
# IDENTITY COMPLETENESS
# =====================================================

def calculate_identity_completeness(
    person: Person,
) -> float:
    fields = [
        person.full_name,
        person.date_of_birth,
        person.gender,
        person.address,
        person.identity_number,
        person.phone,
        person.email,
    ]

    completed_fields = sum(
        1
        for field in fields
        if field is not None
        and str(field).strip() != ""
    )

    return round(
        (completed_fields / len(fields)) * 100,
        2,
    )


# =====================================================
# REGISTERED DOCUMENT CHECK
# =====================================================

def calculate_document_match(
    person: Person,
    documents: list[IdentityDocument],
) -> float:
    """
    Prototype document consistency score.

    This does not inspect raw document images.
    It verifies that a registered document exists
    and belongs to the identity.
    """

    if not documents:
        return 0.0

    matching_documents = [
        document
        for document in documents
        if document.person_id == person.id
    ]

    if not matching_documents:
        return 0.0

    return 100.0


# =====================================================
# AI / RISK ANALYSIS
# =====================================================

@router.post("/analyze")
def analyze_verification(
    request: VerificationRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(
    require_roles(
        "ADMIN",
        "SUPER_ADMIN",
    )
),
):
    person = (
        db.query(Person)
        .filter(
            Person.id == request.person_id,
            Person.is_active == True,
        )
        .first()
    )

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Active person not found",
        )

    if request.verification_method not in {
        "document",
        "qr",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "verification_method must be "
                "'document' or 'qr'"
            ),
        )

    documents = (
        db.query(IdentityDocument)
        .filter(
            IdentityDocument.person_id == person.id
        )
        .all()
    )

    registered_document_match = calculate_document_match(
        person,
        documents,
    )

    identity_completeness = calculate_identity_completeness(
        person
    )

    document_match_score = (
        request.document_match_score
        if request.document_match_score is not None
        else registered_document_match
    )

    completeness_score = (
        identity_completeness
        if request.completeness_score == 100
        else request.completeness_score
    )

    risk_score, risk_level, reasons = calculate_risk(
        face_match_score=request.face_match_score,
        document_match_score=document_match_score,
        qr_match_score=request.qr_match_score,
        completeness_score=completeness_score,
        consistency_score=request.consistency_score,
    )

    secondary_score = (
        document_match_score
        if document_match_score is not None
        else request.qr_match_score
    )

    verification = Verification(
        person_id=person.id,
        admin_id=current_admin.id,
        verification_method=request.verification_method,
        face_match_score=request.face_match_score,
        document_match_score=document_match_score,
        qr_match_score=request.qr_match_score,
        completeness_score=completeness_score,
        consistency_score=request.consistency_score,
        risk_score=risk_score,
        risk_level=risk_level,
        status="COMPLETED",
        decision=None,
        reason=" ".join(reasons),
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="IDENTITY_VERIFICATION",
        details={
            "verification_id": verification.id,
            "person_id": person.id,
            "verification_method": request.verification_method,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "document_count": len(documents),
        },
    )

    return {
        "verification_id": verification.id,
        "person": {
            "id": person.id,
            "full_name": person.full_name,
            "identity_number": person.identity_number,
        },
        "verification_method": request.verification_method,
        "signals": {
            "face_match_score": request.face_match_score,
            "document_match_score": document_match_score,
            "qr_match_score": request.qr_match_score,
            "secondary_match_score": secondary_score,
            "completeness_score": completeness_score,
            "consistency_score": request.consistency_score,
            "registered_document_count": len(documents),
        },
        "risk": {
            "score": risk_score,
            "level": risk_level,
        },
        "reasons": reasons,
        "decision": None,
        "status": "COMPLETED",
    }


# =====================================================
# DOCUMENT VERIFICATION
# =====================================================

@router.post("/document-check")
def verify_document(
    request: DocumentVerificationRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(
    require_roles(
        "ADMIN",
        "SUPER_ADMIN",
    )
),
):
    """
    Compare presented document information with the
    registered identity record.

    Raw submitted document information is used only
    for this verification request and is not returned
    in the response.
    """

    person = (
        db.query(Person)
        .filter(
            Person.id == request.person_id,
            Person.is_active == True,
        )
        .first()
    )

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Active person not found",
        )

    registered_document = (
        db.query(IdentityDocument)
        .filter(
            IdentityDocument.person_id == person.id,
            IdentityDocument.document_number
            == request.document_number,
        )
        .first()
    )

    checks = {
        "document_number": (
            registered_document is not None
        ),
        "full_name": (
            request.full_name.strip().lower()
            == person.full_name.strip().lower()
        ),
        "date_of_birth": (
            request.date_of_birth.strip()
            == person.date_of_birth.strip()
        ),
    }

    matched_checks = sum(
        1
        for result in checks.values()
        if result
    )

    total_checks = len(checks)

    document_match_score = round(
        (matched_checks / total_checks) * 100,
        2,
    )

    if document_match_score >= 85:
        document_status = "PASS"
    elif document_match_score >= 60:
        document_status = "REVIEW"
    else:
        document_status = "FAIL"

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="DOCUMENT_VERIFICATION",
        details={
            "person_id": person.id,
            "document_type": request.document_type,
            "document_match_score": document_match_score,
            "document_status": document_status,
        },
    )

    return {
        "verified": document_status == "PASS",
        "status": document_status,
        "person_id": person.id,
        "document_type": request.document_type,
        "document_match_score": document_match_score,
        "checks": checks,
        "message": (
            "Document information matches the "
            "registered identity."
            if document_status == "PASS"
            else "Document information requires review."
        ),
    }


# =====================================================
# VERIFICATION DECISION
# =====================================================

@router.post("/{verification_id}/decision")
def set_verification_decision(
    verification_id: int,
    request: VerificationDecisionRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(
    require_roles(
        "ADMIN",
        "SUPER_ADMIN",
    )
),
):
    decision = request.decision.upper()

    if decision not in {
        "APPROVE",
        "REVIEW",
        "REJECT",
    }:
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVE, REVIEW, or REJECT",
        )

    verification = (
        db.query(Verification)
        .filter(
            Verification.id == verification_id
        )
        .first()
    )

    if not verification:
        raise HTTPException(
            status_code=404,
            detail="Verification record not found",
        )

    verification.decision = decision

    db.commit()
    db.refresh(verification)

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="VERIFICATION_DECISION",
        details={
            "verification_id": verification.id,
            "decision": decision,
            "risk_level": verification.risk_level,
        },
    )

    return {
        "verification_id": verification.id,
        "decision": decision,
        "status": "RECORDED",
    }


# =====================================================
# VERIFICATION HISTORY
# =====================================================

@router.get("/history")
def verification_history(
    db: Session = Depends(get_db),
    current_admin=Depends(
    require_roles(
        "ADMIN",
        "SUPER_ADMIN",
    )
),
):
    records = (
        db.query(Verification)
        .order_by(
            Verification.created_at.desc()
        )
        .all()
    )

    result = []

    for record in records:
        person = (
            db.query(Person)
            .filter(
                Person.id == record.person_id
            )
            .first()
        )

        if record.decision == "APPROVE":
            display_status = "APPROVED"
        elif record.decision == "REVIEW":
            display_status = "SENT TO REVIEW"
        elif record.decision == "REJECT":
            display_status = "REJECTED"
        else:
            display_status = "PENDING DECISION"

        result.append(
            {
                "id": record.id,
                "person_id": record.person_id,
                "full_name": (
                    person.full_name
                    if person
                    else "Unknown"
                ),
                "verification_method": (
                    record.verification_method
                ),
                "risk_score": record.risk_score,
                "risk_level": record.risk_level,
                "status": display_status,
                "decision": record.decision,
                "created_at": record.created_at,
            }
        )

    return result