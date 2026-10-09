import hashlib
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.documents.ocr import (
    extract_document_text,
    extract_identity_fields,
)

from app.documents.verification import (
    compare_identity_fields,
)

from app.audit import create_audit_log

from app.auth.dependencies import (
    require_roles,
)

from app.database.connection import get_db

from app.database.models import (
    IdentityDocument,
    Person,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ---------------------------------------------------------
# File storage
# ---------------------------------------------------------

UPLOAD_DIR = Path("protected_documents")
UPLOAD_DIR.mkdir(
    exist_ok=True
)


# ---------------------------------------------------------
# Security limits
# ---------------------------------------------------------

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_REGISTER_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


# ---------------------------------------------------------
# File validation helpers
# ---------------------------------------------------------

def validate_file_signature(
    content: bytes,
    content_type: str,
) -> bool:
    """
    Verify that the uploaded bytes match the declared
    document type.
    """

    if content_type == "application/pdf":
        return content.startswith(b"%PDF-")

    if content_type == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")

    if content_type == "image/png":
        return content.startswith(
            b"\x89PNG\r\n\x1a\n"
        )

    return False


def validate_image(content: bytes) -> None:
    """
    Verify that the uploaded image can actually be
    decoded as an image.
    """

    try:
        with Image.open(
            __import__("io").BytesIO(content)
        ) as image:
            image.verify()

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
    ):
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is not a valid image.",
        )


def validate_upload(
    file: UploadFile,
    content: bytes,
    allowed_types: set[str],
) -> str:
    """
    Validate size, content type, extension and
    file signature.
    """

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded document is empty.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Document must be smaller than 10 MB.",
        )

    content_type = (
        file.content_type or ""
    ).lower()

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported document type.",
        )

    extension = Path(
        file.filename or ""
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported document extension.",
        )

    # Make sure extension agrees with MIME type.
    if content_type == "application/pdf":
        if extension != ".pdf":
            raise HTTPException(
                status_code=400,
                detail="PDF content must use a .pdf extension.",
            )

    elif content_type == "image/jpeg":
        if extension not in {".jpg", ".jpeg"}:
            raise HTTPException(
                status_code=400,
                detail="JPEG content must use a .jpg or .jpeg extension.",
            )

    elif content_type == "image/png":
        if extension != ".png":
            raise HTTPException(
                status_code=400,
                detail="PNG content must use a .png extension.",
            )

    # Prevent MIME-type spoofing.
    if not validate_file_signature(
        content,
        content_type,
    ):
        raise HTTPException(
            status_code=400,
            detail="File content does not match its declared type.",
        )

    if content_type in ALLOWED_IMAGE_TYPES:
        validate_image(content)

    return extension


# ---------------------------------------------------------
# Register document
# ---------------------------------------------------------

@router.post("/register")
async def register_document(
    person_id: int = Form(...),
    document_type: str = Form(...),
    document_number: str = Form(...),
    file: UploadFile = File(...),
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
            Person.id == person_id,
            Person.is_active == True,
        )
        .first()
    )

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Person not found.",
        )

    content = await file.read()

    extension = validate_upload(
        file=file,
        content=content,
        allowed_types=ALLOWED_REGISTER_TYPES,
    )

    file_hash = hashlib.sha256(
        content
    ).hexdigest()

    # Hash-based filename prevents unsafe original
    # filenames from becoming filesystem paths.
    stored_name = (
        f"{person_id}_{file_hash}{extension}"
    )

    stored_path = (
        UPLOAD_DIR / stored_name
    )

    stored_path.write_bytes(content)

    document = IdentityDocument(
        person_id=person_id,
        document_type=document_type.strip().upper(),
        document_number=document_number.strip(),
        file_path=str(stored_path),
        file_hash=file_hash,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="DOCUMENT_REGISTERED",
        details={
            "document_id": document.id,
            "person_id": person_id,
            "document_type": document.document_type,
            "document_hash": file_hash,
        },
    )

    return {
        "message": "Document registered successfully",
        "document_id": document.id,
        "person_id": person_id,
        "document_type": document.document_type,
        "document_number": document.document_number,
        "file_hash": file_hash,
        "file_name": file.filename,
    }


# ---------------------------------------------------------
# Verify document
# ---------------------------------------------------------

@router.post("/verify")
async def verify_document(
    person_id: int = Form(...),
    document_type: str = Form(...),
    document_number: str = Form(...),
    file: UploadFile = File(...),
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
            Person.id == person_id,
            Person.is_active == True,
        )
        .first()
    )

    if not person:
        raise HTTPException(
            status_code=404,
            detail="Registered identity not found.",
        )

    content = await file.read()

    validate_upload(
        file=file,
        content=content,
        allowed_types=ALLOWED_IMAGE_TYPES,
    )

    # OCR processing
    try:
        ocr_text = extract_document_text(
            content
        )

        extracted_fields = extract_identity_fields(
            ocr_text
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="OCR processing failed for the uploaded document.",
        )

    uploaded_hash = hashlib.sha256(
        content
    ).hexdigest()

    registered_document = (
        db.query(IdentityDocument)
        .filter(
            IdentityDocument.person_id == person_id,
            IdentityDocument.document_type
            == document_type.strip().upper(),
            IdentityDocument.document_number
            == document_number.strip(),
        )
        .order_by(
            IdentityDocument.id.desc()
        )
        .first()
    )

    if not registered_document:
        create_audit_log(
            db=db,
            username=current_admin.username,
            action="DOCUMENT_VERIFICATION",
            details={
                "person_id": person_id,
                "status": "FAIL",
                "reason": "No matching registered document",
            },
        )

        return {
            "verified": False,
            "status": "FAIL",
            "document_match_score": 0,
            "reason": "No matching registered document found.",
        }

    field_result = compare_identity_fields(
        extracted_fields,
        person,
    )

    verification_status = field_result[
        "status"
    ]

    verified = (
        verification_status == "PASS"
    )

    hash_match = (
        uploaded_hash
        == registered_document.file_hash
    )

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="DOCUMENT_VERIFICATION",
        details={
            "person_id": person_id,
            "document_id": registered_document.id,
            "status": verification_status,
            "document_match_score": field_result[
                "document_match_score"
            ],
            "name_match": field_result[
                "name_match"
            ],
            "date_of_birth_match": field_result[
                "date_of_birth_match"
            ],
            "identity_number_match": field_result[
                "identity_number_match"
            ],
            "hash_match": hash_match,
        },
    )

    return {
        "verified": verified,
        "status": verification_status,
        "document_match_score": field_result[
            "document_match_score"
        ],
        "name_match": field_result[
            "name_match"
        ],
        "date_of_birth_match": field_result[
            "date_of_birth_match"
        ],
        "identity_number_match": field_result[
            "identity_number_match"
        ],
        "extracted": field_result[
            "extracted"
        ],
        "registered_document_id": registered_document.id,
        "hash_match": hash_match,
        "reason": (
            "Document identity fields match the registered person."
            if verified
            else "Document identity fields require review."
        ),
    }