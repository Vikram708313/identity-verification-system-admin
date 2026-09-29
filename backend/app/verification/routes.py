from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.connection import get_db
from app.database.models import Person, Verification


router = APIRouter(
    prefix="/verification",
    tags=["Verification"],
)


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

    risk_score = round(max(0, min(100, risk_score)), 2)

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


@router.post("/analyze")
def analyze_verification(
    request: VerificationRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    person = (
        db.query(Person)
        .filter(Person.id == request.person_id)
        .first()
    )

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found",
        )

    if request.verification_method not in {"document", "qr"}:
        raise HTTPException(
            status_code=400,
            detail="verification_method must be 'document' or 'qr'",
        )

    risk_score, risk_level, reasons = calculate_risk(
        face_match_score=request.face_match_score,
        document_match_score=request.document_match_score,
        qr_match_score=request.qr_match_score,
        completeness_score=request.completeness_score,
        consistency_score=request.consistency_score,
    )

    secondary_score = (
        request.document_match_score
        if request.document_match_score is not None
        else request.qr_match_score
    )

    verification = Verification(
        person_id=person.id,
        admin_id=current_admin.id,
        verification_method=request.verification_method,
        face_match_score=request.face_match_score,
        document_match_score=request.document_match_score,
        qr_match_score=request.qr_match_score,
        completeness_score=request.completeness_score,
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
            "secondary_match_score": secondary_score,
            "completeness_score": request.completeness_score,
            "consistency_score": request.consistency_score,
        },
        "risk": {
            "score": risk_score,
            "level": risk_level,
        },
        "reasons": reasons,
        "decision": None,
        "status": "COMPLETED",
    }


@router.get("/history")
def verification_history(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    records = (
        db.query(Verification)
        .order_by(Verification.created_at.desc())
        .all()
    )

    result = []

    for record in records:
        person = (
            db.query(Person)
            .filter(Person.id == record.person_id)
            .first()
        )

        result.append(
            {
                "id": record.id,
                "person_id": record.person_id,
                "full_name": (
                    person.full_name
                    if person
                    else "Unknown"
                ),
                "verification_method": record.verification_method,
                "risk_score": record.risk_score,
                "risk_level": record.risk_level,
                "status": record.status,
                "decision": record.decision,
                "created_at": record.created_at,
            }
        )

    return result