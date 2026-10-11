
import hashlib
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import get_identity_db
from app.database.identity_models import RegistryDocument, RegistryPerson

router = APIRouter(
    prefix="/registry/documents",
    tags=["Registry Document Upload"],
)

# Store uploads outside the public frontend directory.
BACKEND_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BACKEND_DIR / "protected_uploads" / "documents"

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload")
async def upload_document(
    person_code: str,
    document_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    # Check the selected demo person.
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

    if not person.is_active:
        raise HTTPException(
            status_code=400,
            detail="Demo person is inactive",
        )

    # Validate the declared content type.
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Only PDF, JPEG, and PNG files are allowed",
        )

    

    if document_type.upper() not in {
        "PASSPORT",
        "VISA",
        "ID_CARD",
        "AADHAAR",
        "OTHER",
    }:
        raise HTTPException(
            status_code=400,
            detail="Unsupported document_type",
        )


        raise HTTPException(
            status_code=400,
            detail="Unsupported document_type",
        )

    # Read at most 5 MB plus one byte to detect oversized files.
    contents = await file.read(MAX_FILE_SIZE + 1)

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 5 MB",
        )

    # Verify file signature rather than trusting the filename.
    if file.content_type == "application/pdf":
        valid_signature = contents.startswith(b"%PDF-")
    elif file.content_type == "image/jpeg":
        valid_signature = contents.startswith(b"\xff\xd8\xff")
    else:
        valid_signature = (
            contents.startswith(b"\x89PNG\r\n\x1a\n")
        )

    if not valid_signature:
        raise HTTPException(
            status_code=400,
            detail="File content does not match its declared type",
        )

    file_hash = hashlib.sha256(contents).hexdigest()
    extension = ALLOWED_TYPES[file.content_type]

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Use a random filename; never trust the uploaded filename.
    stored_name = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / stored_name

    try:
        # Exclusive creation prevents accidental overwriting.
        with destination.open("xb") as output:
            output.write(contents)

        record = RegistryDocument(
            person_id=person.id,
            document_type=document_type.upper(),
            file_path=str(destination.resolve()),
            file_hash=file_hash,
            demo_status="PENDING_REVIEW",
        )

        db.add(record)
        db.commit()
        db.refresh(record)

    except Exception:
        db.rollback()

        # Remove the saved file if the database insert fails.
        if destination.exists():
            destination.unlink()

        raise HTTPException(
            status_code=500,
            detail="Could not save document metadata",
        )

    finally:
        await file.close()

    return {
        "message": "Document uploaded successfully",
        "document_id": record.id,
        "person_code": person.person_code,
        "document_type": record.document_type,
        "file_hash": file_hash,
        "status": record.demo_status,
    }
