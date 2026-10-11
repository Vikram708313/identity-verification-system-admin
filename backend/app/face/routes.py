from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.database.models import Person
from app.database.identity_connection import get_identity_db
from app.database.identity_models import RegistryPerson, PersonImage
from app.face.service import get_face_embedding, detect_liveness_sequence

router = APIRouter(prefix="/face", tags=["Face Verification"])

BACKEND_DIR = Path(__file__).resolve().parents[2]
PROTECTED_FACE_DIR = (BACKEND_DIR / "protected_uploads" / "faces").resolve()
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MIN_MATCH_SCORE = 0.50
MIN_REVIEW_SCORE = 0.35


@router.post("/compare")
async def compare_face_images(
    verification_image: UploadFile = File(...),
    liveness_frames: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    registry_db: Session = Depends(get_identity_db),
    current_admin=Depends(require_roles("ADMIN", "SUPER_ADMIN")),
):
    live_bytes = await verification_image.read()

    if not live_bytes:
        raise HTTPException(400, "Face image is required.")
    if len(live_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "Face image exceeds 5 MB.")
    if len(liveness_frames) < 3:
        raise HTTPException(400, "At least 3 liveness frames are required.")
    if len(liveness_frames) > 10:
        raise HTTPException(400, "A maximum of 10 liveness frames is allowed.")

    frame_bytes = []
    try:
        for frame in liveness_frames:
            data = await frame.read()
            if not data:
                raise HTTPException(400, "A liveness frame is empty.")
            if len(data) > MAX_IMAGE_BYTES:
                raise HTTPException(413, "A liveness frame exceeds 5 MB.")
            frame_bytes.append(data)
    finally:
        await verification_image.close()
        for frame in liveness_frames:
            await frame.close()

    try:
        liveness_verified = bool(detect_liveness_sequence(frame_bytes))
    except Exception:
        liveness_verified = False

    try:
        live_embedding = get_face_embedding(live_bytes)
        live_norm = float(np.linalg.norm(live_embedding))
        if not np.isfinite(live_norm) or live_norm == 0:
            raise ValueError("Invalid face embedding.")
        live_embedding = live_embedding / live_norm
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception:
        raise HTTPException(500, "Face processing failed.")

    reference_rows = (
        registry_db.query(PersonImage, RegistryPerson)
        .join(RegistryPerson, PersonImage.person_id == RegistryPerson.id)
        .filter(
            PersonImage.image_type == "FACE_REFERENCE",
            RegistryPerson.is_active.is_(True),
        )
        .order_by(RegistryPerson.id.asc(), PersonImage.id.asc())
        .all()
    )

    best_registry_person = None
    best_main_person = None
    best_score = 0.0
    reference_count = 0

    for image_record, registry_person in reference_rows:
        try:
            stored_path = Path(image_record.file_path)
            if not stored_path.is_absolute():
                stored_path = BACKEND_DIR / stored_path
            stored_path = stored_path.resolve()

            if not stored_path.is_relative_to(PROTECTED_FACE_DIR):
                continue
            if not stored_path.is_file():
                continue

            reference_embedding = get_face_embedding(stored_path.read_bytes())
            reference_norm = float(np.linalg.norm(reference_embedding))
            if not np.isfinite(reference_norm) or reference_norm == 0:
                continue

            reference_embedding = reference_embedding / reference_norm
            similarity = float(np.dot(live_embedding, reference_embedding))
            similarity = max(0.0, min(1.0, similarity))
            reference_count += 1

            if similarity > best_score:
                best_score = similarity
                best_registry_person = registry_person
                best_main_person = (
                    db.query(Person)
                    .filter(
                        Person.identity_number == (
                            f"TV-DEMO-{registry_person.person_code}"
                        ),
                        Person.is_active.is_(True),
                    )
                    .first()
                )
        except (ValueError, OSError):
            continue

    score = round(best_score * 100, 2)

    if best_registry_person is None or best_score < MIN_REVIEW_SCORE:
        return {
            "verified": False,
            "liveness_verified": liveness_verified,
            "match_score": score,
            "status": "FAIL",
            "person_id": None,
            "person": None,
            "reference_images_checked": reference_count,
            "message": "No registered face matched sufficiently.",
        }

    if best_score < MIN_MATCH_SCORE or not liveness_verified:
        return {
            "verified": False,
            "liveness_verified": liveness_verified,
            "match_score": score,
            "status": "REVIEW",
            "person_id": None,
            "person": None,
            "candidate_code": best_registry_person.person_code,
            "message": (
                "Face match or liveness check requires manual review. "
                "Identity has not been automatically confirmed."
            ),
        }

    if best_main_person is None:
        return {
            "verified": False,
            "liveness_verified": liveness_verified,
            "match_score": score,
            "status": "REVIEW",
            "person_id": None,
            "person": None,
            "candidate_code": best_registry_person.person_code,
            "message": "The matched registry record has no active main database record.",
        }

    return {
        "verified": True,
        "liveness_verified": True,
        "match_score": score,
        "similarity": round(best_score, 4),
        "status": "PASS",
        "person_id": best_main_person.id,
        "person_code": best_registry_person.person_code,
        "person": {
            "id": best_main_person.id,
            "full_name": best_main_person.full_name,
            "identity_number": best_main_person.identity_number,
        },
        "reference_images_checked": reference_count,
        "message": (
            "Prototype face-match and movement-based liveness checks passed."
        ),
    }
