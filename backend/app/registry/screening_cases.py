import hashlib
import json
import uuid
from datetime import datetime
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageStat, ImageFilter, UnidentifiedImageError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import (
    IdentityBase,
    identity_engine,
    get_identity_db,
)

router = APIRouter(
    prefix="/registry/screening",
    tags=["Screening Cases"],
)

BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "protected_uploads" / "screening_cases"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 5 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png"}


class ScreeningCase(IdentityBase):
    __tablename__ = "screening_cases"

    id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(500), nullable=False)
    image_hash = Column(String(64), nullable=False)
    face_presence = Column(String(30), nullable=False)
    quality_status = Column(String(30), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING_REVIEW")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ScreeningReviewAudit(IdentityBase):
    __tablename__ = "screening_review_audits"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, nullable=False, index=True)
    reviewer = Column(String(150), nullable=False)
    decision = Column(String(30), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    audit_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=True)


IdentityBase.metadata.create_all(bind=identity_engine)


class ReviewRequest(BaseModel):
    decision: str = Field(
        description="REVIEWED, NEEDS_MORE_INFORMATION, or CLOSED"
    )
    reason: str = Field(min_length=3, max_length=1000)


@router.post("/submit")
async def submit_screening_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "Upload a JPEG or PNG image.")

    data = await file.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(400, "Image is empty or exceeds 5 MB.")

    try:
        with Image.open(BytesIO(data)) as original:
            original.verify()

        with Image.open(BytesIO(data)) as original:
            image = original.convert("RGB")
            width, height = image.size

            if width < 100 or height < 100:
                raise HTTPException(
                    400, "Image must be at least 100x100 pixels."
                )
            if width * height > 20_000_000:
                raise HTTPException(400, "Image dimensions are too large.")

            grayscale = image.convert("L")
            brightness = ImageStat.Stat(grayscale).mean[0]
            edge_image = grayscale.filter(ImageFilter.FIND_EDGES)
            sharpness = ImageStat.Stat(edge_image).mean[0]

            if brightness < 35 or brightness > 225 or sharpness < 3:
                quality_status = "QUALITY_REVIEW_REQUIRED"
            else:
                quality_status = "BASIC_QUALITY_OK"

            stored_path = UPLOAD_DIR / f"{uuid.uuid4().hex}.jpg"
            image.save(stored_path, format="JPEG", quality=95)

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(400, "The uploaded file is not a valid image.")

    face_presence = "NOT_CHECKED"
    image_hash = hashlib.sha256(data).hexdigest()

    case = ScreeningCase(
        image_path=str(stored_path.resolve()),
        image_hash=image_hash,
        face_presence=face_presence,
        quality_status=quality_status,
        status="PENDING_REVIEW",
        created_at=datetime.utcnow(),
    )

    try:
        db.add(case)
        db.commit()
        db.refresh(case)
    except Exception:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise HTTPException(500, "Could not create screening case.")

    return {
        "case_id": case.id,
        "status": case.status,
        "face_presence": case.face_presence,
        "quality_status": case.quality_status,
        "image_sha256": case.image_hash,
        "message": "Image checks completed; authorized admin review is required.",
    }


@router.get("/cases")
def list_screening_cases(
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    cases = db.query(ScreeningCase).order_by(
        ScreeningCase.id.desc()
    ).all()

    return [
        {
            "case_id": case.id,
            "status": case.status,
            "face_presence": case.face_presence,
            "quality_status": case.quality_status,
            "created_at": case.created_at,
        }
        for case in cases
    ]


@router.post("/cases/{case_id}/review")
def review_screening_case(
    case_id: int,
    request: ReviewRequest,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    decision = request.decision.strip().upper()
    allowed = {"REVIEWED", "NEEDS_MORE_INFORMATION", "CLOSED"}

    if decision not in allowed:
        raise HTTPException(
            400,
            "Use REVIEWED, NEEDS_MORE_INFORMATION, or CLOSED.",
        )

    case = db.query(ScreeningCase).filter(
        ScreeningCase.id == case_id
    ).first()

    if case is None:
        raise HTTPException(404, "Screening case not found.")

    reviewer = (
        getattr(current_admin, "username", None)
        or getattr(current_admin, "email", None)
    )
    if not reviewer:
        raise HTTPException(500, "Could not determine reviewer identity.")

    latest = db.query(ScreeningReviewAudit).order_by(
        ScreeningReviewAudit.id.desc()
    ).first()
    previous_hash = latest.audit_hash if latest else None

    reviewed_at = datetime.utcnow()
    reason = request.reason.strip()

    payload = {
        "case_id": case.id,
        "reviewer": reviewer,
        "decision": decision,
        "reason": reason,
        "created_at": reviewed_at.isoformat(),
        "previous_hash": previous_hash,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    audit_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    audit = ScreeningReviewAudit(
        case_id=case.id,
        reviewer=reviewer,
        decision=decision,
        reason=reason,
        created_at=reviewed_at,
        audit_hash=audit_hash,
        previous_hash=previous_hash,
    )

    case.status = decision
    db.add(audit)

    try:
        db.commit()
        db.refresh(audit)
    except Exception:
        db.rollback()
        raise HTTPException(500, "Could not save the review audit.")

    return {
        "case_id": case.id,
        "status": case.status,
        "audit_id": audit.id,
        "reviewer": audit.reviewer,
        "decision": audit.decision,
        "reason": audit.reason,
        "audit_hash": audit.audit_hash,
        "previous_hash": audit.previous_hash,
    }


@router.get("/audit/verify")
def verify_screening_audit_chain(
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    audits = db.query(ScreeningReviewAudit).order_by(
        ScreeningReviewAudit.id.asc()
    ).all()

    issues = []
    expected_previous_hash = None

    for audit in audits:
        if audit.previous_hash != expected_previous_hash:
            issues.append({
                "audit_id": audit.id,
                "problem": "PREVIOUS_HASH_MISMATCH",
            })

        payload = {
            "case_id": audit.case_id,
            "reviewer": audit.reviewer,
            "decision": audit.decision,
            "reason": audit.reason,
            "created_at": audit.created_at.isoformat(),
            "previous_hash": audit.previous_hash,
        }
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        calculated_hash = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

        if calculated_hash != audit.audit_hash:
            issues.append({
                "audit_id": audit.id,
                "problem": "AUDIT_HASH_MISMATCH",
            })

        expected_previous_hash = audit.audit_hash

    return {
        "valid": len(issues) == 0,
        "records_checked": len(audits),
        "issues": issues,
        "message": (
            "Audit chain verification passed."
            if not issues
            else "Audit chain verification failed."
        ),
    }