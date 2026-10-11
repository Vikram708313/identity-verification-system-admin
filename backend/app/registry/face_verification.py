from pathlib import Path

import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import get_identity_db
from app.database.identity_models import PersonImage, RegistryPerson
from app.face.service import get_face_embedding, detect_liveness_sequence

router = APIRouter(
    prefix="/registry/faces",
    tags=["Registry Face Verification"],
)

MAX_IMAGE_SIZE = 5 * 1024 * 1024
BACKEND_DIR = Path(__file__).resolve().parents[2]
PROTECTED_FACE_DIR = (BACKEND_DIR / "protected_uploads" / "faces").resolve()


@router.post("/verify")
async def verify_registry_face(
    person_code: str = Query(..., min_length=4, max_length=20),
    verification_image: UploadFile = File(...),
    liveness_frames: list[UploadFile] = File(...),
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    """Compare a live face only with the selected registry person's reference."""

    person = (
        db.query(RegistryPerson)
        .filter(
            RegistryPerson.person_code == person_code,
            RegistryPerson.is_active == True,
        )
        .first()
    )

    if person is None:
        raise HTTPException(status_code=404, detail="Active registry person not found.")

    reference = (
        db.query(PersonImage)
        .filter(
            PersonImage.person_id == person.id,
            PersonImage.image_type == "FACE_REFERENCE",
        )
        .first()
    )

    if reference is None:
        raise HTTPException(status_code=404, detail="No registered reference face exists.")

    reference_path = Path(reference.file_path).resolve()

    if (
        not reference_path.is_relative_to(PROTECTED_FACE_DIR)
        or not reference_path.is_file()
    ):
        raise HTTPException(status_code=404, detail="Protected reference image is unavailable.")

    live_bytes = await verification_image.read(MAX_IMAGE_SIZE + 1)

    if not live_bytes:
        raise HTTPException(status_code=400, detail="Live face image is required.")

    if len(live_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=413, detail="Live face image exceeds 5 MB.")

    if len(liveness_frames) < 3:
        raise HTTPException(status_code=400, detail="At least 3 liveness frames are required.")

    frames = []
    for frame in liveness_frames:
        content = await frame.read(MAX_IMAGE_SIZE + 1)
        if not content or len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(status_code=400, detail="A liveness frame is empty or exceeds 5 MB.")
        frames.append(content)

    try:
        if not detect_liveness_sequence(frames):
            return {
                "person_code": person.person_code,
                "liveness_verified": False,
                "verified": False,
                "status": "REVIEW",
                "match_score": None,
                "message": "Liveness check failed; manual review is required.",
            }

        live_embedding = get_face_embedding(live_bytes)
        reference_embedding = get_face_embedding(reference_path.read_bytes())

        live_norm = np.linalg.norm(live_embedding)
        reference_norm = np.linalg.norm(reference_embedding)

        if live_norm == 0 or reference_norm == 0:
            raise ValueError("Could not calculate a valid face embedding.")

        live_embedding = live_embedding / live_norm
        reference_embedding = reference_embedding / reference_norm

        similarity = float(np.dot(live_embedding, reference_embedding))
        similarity = max(0.0, min(1.0, similarity))
        score = round(similarity * 100, 2)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Face verification processing failed.")
    finally:
        await verification_image.close()
        for frame in liveness_frames:
            await frame.close()

    if similarity >= 0.50:
        status = "PASS"
    elif similarity >= 0.35:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "person_code": person.person_code,
        "person_name": person.full_name,
        "liveness_verified": True,
        "verified": status == "PASS",
        "match_score": score,
        "similarity": round(similarity, 4),
        "status": status,
        "message": (
            "Face matched the selected registry reference."
            if status == "PASS"
            else "Face match requires further review."
            if status == "REVIEW"
            else "Face did not match the selected registry reference."
        ),
        "note": "Prototype similarity thresholds require validation before operational use.",
    }
