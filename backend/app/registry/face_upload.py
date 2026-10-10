
import hashlib
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import get_identity_db
from app.database.identity_models import PersonImage, RegistryPerson

router = APIRouter(
    prefix="/registry/faces",
    tags=["Registry Face Images"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
ALLOWED_TYPES = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
}

BACKEND_DIR = Path(__file__).resolve().parents[2]
FACE_DIR = BACKEND_DIR / "protected_uploads" / "faces"
FACE_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_reference_face(
    person_code: str = Query(..., min_length=4, max_length=20),
    file: UploadFile = File(...),
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    """Upload one protected synthetic reference face per registry person."""

    person = (
        db.query(RegistryPerson)
        .filter(
            RegistryPerson.person_code == person_code,
            RegistryPerson.is_active == True,
        )
        .first()
    )

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Active registry person not found.",
        )

    content_type = (file.content_type or "").lower()
    extension = Path(file.filename or "").suffix.lower()

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only JPEG and PNG images are accepted.",
        )

    if extension not in ALLOWED_TYPES[content_type]:
        raise HTTPException(
            status_code=400,
            detail="File extension does not match the image type.",
        )

    # Prevent a second reference image from being added accidentally.
    existing = (
        db.query(PersonImage)
        .filter(
            PersonImage.person_id == person.id,
            PersonImage.image_type == "FACE_REFERENCE",
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A reference face already exists for this person. "
                "No new image was saved."
            ),
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(status_code=400, detail="Image is empty.")

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image exceeds the 5 MB size limit.",
        )

    # Check actual image format rather than trusting the filename.
    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise HTTPException(
                    status_code=415,
                    detail="Image content must be JPEG or PNG.",
                )

            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail="Image dimensions exceed the allowed limit.",
                )

            image.verify()

    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid image.",
        )

    file_hash = hashlib.sha256(content).hexdigest()
    stored_name = f"{person.person_code}_{uuid.uuid4().hex}{extension}"
    stored_path = FACE_DIR / stored_name

    try:
        stored_path.write_bytes(content)

        image_record = PersonImage(
            person_id=person.id,
            image_type="FACE_REFERENCE",
            file_path=str(stored_path.resolve()),
            file_hash=file_hash,
        )

        db.add(image_record)
        db.commit()
        db.refresh(image_record)

    except Exception:
        db.rollback()

        if stored_path.exists():
            stored_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Could not save the reference image.",
        )

    return {
        "message": "Reference face uploaded successfully.",
        "image_record_id": image_record.id,
        "person_code": person.person_code,
        "person_name": person.full_name,
        "image_type": image_record.image_type,
        "sha256": image_record.file_hash,
        "status": "STORED",
    }

