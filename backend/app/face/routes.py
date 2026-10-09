from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.database.connection import get_db
from app.database.models import Person
from app.face.service import (
    get_face_embedding,
    detect_liveness_sequence,
)

router = APIRouter(prefix="/face", tags=["Face Verification"])

PROTECTED_FACE_DIR = Path("protected_faces")


@router.post("/compare")
async def compare_face_images(
    verification_image: UploadFile = File(...),
    liveness_frames: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("ADMIN", "SUPER_ADMIN")),
):
    live_bytes = await verification_image.read()

    if not live_bytes:
        raise HTTPException(400, "Face image is required.")

    if len(liveness_frames) < 3:
        raise HTTPException(400, "At least 3 liveness frames are required.")

    frames = [await frame.read() for frame in liveness_frames]

    if not detect_liveness_sequence(frames):
        raise HTTPException(
            400,
            "Liveness verification failed. Turn your head slightly left and right, then try again.",
        )

    try:
        live_embedding = get_face_embedding(live_bytes)
        live_embedding = live_embedding / np.linalg.norm(live_embedding)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception:
        raise HTTPException(500, "Face detection failed.")

    people = (
        db.query(Person)
        .filter(Person.is_active == True)
        .order_by(Person.id.asc())
        .all()
    )

    best_person = None
    best_score = 0.0

    for person in people:
        reference_path = PROTECTED_FACE_DIR / f"{person.id}.jpeg"

        if not reference_path.is_file():
            continue

        try:
            reference_embedding = get_face_embedding(
                reference_path.read_bytes()
            )
            reference_embedding = reference_embedding / np.linalg.norm(
                reference_embedding
            )

            similarity = float(np.dot(live_embedding, reference_embedding))
            similarity = max(0.0, min(1.0, similarity))

            if similarity > best_score:
                best_score = similarity
                best_person = person

        except (ValueError, OSError):
            continue

    score = round(best_score * 100, 2)

    if best_person is None or best_score < 0.50:
        return {
            "verified": False,
            "liveness_verified": True,
            "match_score": score,
            "status": "FAIL" if best_score < 0.35 else "REVIEW",
            "person": None,
            "message": "No registered face matched confidently.",
        }

    return {
        "verified": True,
        "liveness_verified": True,
        "match_score": score,
        "similarity": round(best_score, 4),
        "status": "PASS",
        "person_id": best_person.id,
        "person": {
            "id": best_person.id,
            "full_name": best_person.full_name,
            "identity_number": best_person.identity_number,
        },
    }