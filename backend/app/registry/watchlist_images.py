import hashlib
import uuid
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import IdentityBase, get_identity_db
from app.database.identity_models import RegistryWatchlist

router = APIRouter(
    prefix="/registry/watchlist-images",
    tags=["Watchlist Reference Images"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
BACKEND_DIR = Path(__file__).resolve().parents[2]
IMAGE_DIR = BACKEND_DIR / "protected_uploads" / "watchlist_faces"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


class RegistryWatchlistImage(IdentityBase):
    __tablename__ = "registry_watchlist_images"

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(
        String(30),
        ForeignKey("registry_watchlist.reference_id"),
        nullable=False,
        unique=True,
        index=True,
    )
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)


@router.post("/upload")
async def upload_watchlist_image(
    reference_id: str = Query(..., min_length=1, max_length=30),
    file: UploadFile = File(...),
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    record = (
        db.query(RegistryWatchlist)
        .filter(RegistryWatchlist.reference_id == reference_id)
        .first()
    )
    if record is None:
        raise HTTPException(404, "Watchlist reference ID not found.")

    content_type = (file.content_type or "").lower()
    extension = Path(file.filename or "").suffix.lower()
    allowed = {
        "image/jpeg": {".jpg", ".jpeg"},
        "image/png": {".png"},
    }

    if content_type not in allowed:
        raise HTTPException(415, "Only JPEG and PNG images are accepted.")
    if extension not in allowed[content_type]:
        raise HTTPException(400, "File extension does not match image type.")

    existing = (
        db.query(RegistryWatchlistImage)
        .filter(RegistryWatchlistImage.reference_id == reference_id)
        .first()
    )
    if existing:
        raise HTTPException(409, "An image is already stored for this watchlist ID.")

    content = await file.read(MAX_FILE_SIZE + 1)
    if not content:
        raise HTTPException(400, "Image is empty.")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Image exceeds the 5 MB limit.")

    try:
        with Image.open(BytesIO(content)) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise HTTPException(415, "Image must be JPEG or PNG.")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(413, "Image dimensions exceed the limit.")
            image.verify()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(400, "Invalid image file.")

    file_hash = hashlib.sha256(content).hexdigest()
    stored_path = IMAGE_DIR / f"{reference_id}_{uuid.uuid4().hex}{extension}"

    try:
        stored_path.write_bytes(content)
        image_record = RegistryWatchlistImage(
            reference_id=reference_id,
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
        raise HTTPException(500, "Could not save watchlist image.")

    return {
        "message": "Watchlist reference image uploaded successfully.",
        "image_record_id": image_record.id,
        "reference_id": record.reference_id,
        "fictional_name": record.fictional_name,
        "risk_level": record.risk_level,
        "sha256": image_record.file_hash,
        "status": "STORED",
    }
