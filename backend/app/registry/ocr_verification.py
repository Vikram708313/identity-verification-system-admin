
import re
from pathlib import Path

import pytesseract
from fastapi import APIRouter, Depends, HTTPException
from PIL import Image, ImageOps
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.database.identity_connection import get_identity_db
from app.database.identity_models import (
    RegistryDocument,
    RegistryPerson,
    RegistryVerification,
)

router = APIRouter(
    prefix="/registry/documents",
    tags=["OCR Document Verification"],
)

MAX_PDF_PAGES = 10
MAX_TEXT_LENGTH = 100_000
MAX_IMAGE_PIXELS = 20_000_000


def normalize_text(value: str) -> str:
    """Normalize text for a case-insensitive comparison."""
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def extract_pdf_text(file_path: Path) -> str:
    """Extract embedded text from a PDF."""
    try:
        reader = PdfReader(str(file_path))

        if reader.is_encrypted:
            raise HTTPException(
                status_code=400,
                detail="Encrypted PDFs are not supported.",
            )

        if len(reader.pages) > MAX_PDF_PAGES:
            raise HTTPException(
                status_code=413,
                detail="PDF exceeds the 10-page processing limit.",
            )

        parts = []

        for page in reader.pages:
            parts.append(page.extract_text() or "")

        return "\n".join(parts)[:MAX_TEXT_LENGTH]

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read this PDF.",
        )


def extract_image_text(file_path: Path) -> str:
    """Extract text from JPEG or PNG using Tesseract OCR."""
    try:
        with Image.open(file_path) as source:
            image = ImageOps.exif_transpose(source)

            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=413,
                    detail="Image dimensions exceed the processing limit.",
                )

            image.load()
            image = image.convert("RGB")

            return pytesseract.image_to_string(
                image,
                config="--psm 6",
                timeout=20,
            )[:MAX_TEXT_LENGTH]

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not process this image. "
                "Check the image and Tesseract installation."
            ),
        )


def extract_document_text(file_path: Path) -> tuple[str, str]:
    """Extract PDF text or perform OCR on an image."""
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        text = extract_pdf_text(file_path)

        if text.strip():
            return text, "PDF_TEXT_EXTRACTION"

        # Scanned-PDF OCR requires an additional PDF-to-image setup.
        return "", "SCANNED_PDF_OCR_NOT_CONFIGURED"

    if suffix in {".jpg", ".jpeg", ".png"}:
        return extract_image_text(file_path), "IMAGE_OCR"

    raise HTTPException(
        status_code=415,
        detail="Unsupported stored document format.",
    )


def find_field(text: str, labels: list[str]) -> str | None:
    """Find a value following a recognizable field label."""
    for label in labels:
        pattern = rf"(?im)^\s*{label}\s*[:\-]\s*(.*?)\s*$"
        match = re.search(pattern, text)

        if match:
            value = match.group(1).strip()

            if value:
                return value[:200]

    return None


def save_ocr_verification(
    db: Session,
    person: RegistryPerson,
    status: str,
    explanation: str,
) -> None:
    """
    Save a preliminary OCR result in the existing verification table.

    Each successful analysis creates a new row. The document's review
    status is not changed by this function.
    """
    verification = RegistryVerification(
        person_id=person.id,
        face_match_score=None,
        document_match_score=None,
        risk_score=0.0,
        status=status,
        explanation=explanation,
    )

    try:
        db.add(verification)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save the OCR verification result.",
        )


@router.post("/{document_id}/ocr-verify")
def verify_document_with_ocr(
    document_id: int,
    db: Session = Depends(get_identity_db),
    current_admin=Depends(get_current_admin),
):
    """Analyze a pending document and persist its preliminary OCR result."""

    document = (
        db.query(RegistryDocument)
        .filter(RegistryDocument.id == document_id)
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    if document.demo_status != "PENDING_REVIEW":
        raise HTTPException(
            status_code=409,
            detail="Only pending documents can be analyzed.",
        )

    person = (
        db.query(RegistryPerson)
        .filter(RegistryPerson.id == document.person_id)
        .first()
    )

    if person is None:
        raise HTTPException(
            status_code=404,
            detail="Registered person not found.",
        )

    file_path = Path(document.file_path).resolve()

    # Restrict file access to the protected document upload directory.
    protected_dir = (
        Path(__file__).resolve().parents[2]
        / "protected_uploads"
        / "documents"
    ).resolve()

    if (
        not file_path.is_relative_to(protected_dir)
        or not file_path.is_file()
    ):
        raise HTTPException(
            status_code=404,
            detail="Stored document file not found.",
        )

    extracted_text, extraction_method = extract_document_text(
        file_path
    )

    # If no text is available, save an incomplete result as well.
    if not extracted_text.strip():
        status = "INCOMPLETE"

        explanation = (
            f"OCR document ID: {document.id}; "
            f"extraction method: {extraction_method}; "
            "No text could be extracted; manual review required."
        )

        save_ocr_verification(
            db=db,
            person=person,
            status=status,
            explanation=explanation,
        )

        return {
            "document_id": document.id,
            "person_code": person.person_code,
            "extraction_method": extraction_method,
            "ocr_status": "NO_TEXT_EXTRACTED",
            "fields": {
                "full_name": {
                    "extracted": None,
                    "registered": person.full_name,
                    "match": None,
                },
                "date_of_birth": {
                    "extracted": None,
                    "registered": person.date_of_birth,
                    "match": None,
                },
            },
            "mismatches": [],
            "missing_fields": ["FULL_NAME", "DATE_OF_BIRTH"],
            "review_status": "PENDING_REVIEW",
            "message": (
                "No text was extracted. Manual review is required. "
                "This is not evidence that the document is fraudulent."
            ),
        }

    extracted_name = find_field(
        extracted_text,
        [
            r"full name",
            r"applicant name",
            r"demo name",
            r"name",
        ],
    )

    extracted_dob = find_field(
        extracted_text,
        [
            r"date of birth",
            r"demo date of birth",
            r"birth date",
            r"dob",
        ],
    )

    name_match = (
        normalize_text(extracted_name)
        == normalize_text(person.full_name)
        if extracted_name
        else None
    )

    # Normalize common separators without guessing date formats.
    normalized_extracted_dob = (
        re.sub(r"[./]", "-", extracted_dob.strip())
        if extracted_dob
        else None
    )

    normalized_registered_dob = re.sub(
        r"[./]",
        "-",
        person.date_of_birth.strip(),
    )

    dob_match = (
        normalized_extracted_dob.casefold()
        == normalized_registered_dob.casefold()
        if normalized_extracted_dob
        else None
    )

    mismatches = []

    if name_match is False:
        mismatches.append("NAME_MISMATCH")

    if dob_match is False:
        mismatches.append("DATE_OF_BIRTH_MISMATCH")

    missing_fields = []

    if extracted_name is None:
        missing_fields.append("FULL_NAME")

    if extracted_dob is None:
        missing_fields.append("DATE_OF_BIRTH")

    if missing_fields:
        status = "INCOMPLETE"
    elif mismatches:
        status = "MISMATCH_REQUIRES_REVIEW"
    else:
        status = "FIELDS_MATCH_REQUIRES_REVIEW"

    explanation = (
        f"OCR document ID: {document.id}; "
        f"extraction method: {extraction_method}; "
        f"extracted name: {extracted_name}; "
        f"registered name: {person.full_name}; "
        f"name match: {name_match}; "
        f"extracted DOB: {extracted_dob}; "
        f"registered DOB: {person.date_of_birth}; "
        f"DOB match: {dob_match}; "
        f"mismatches: {', '.join(mismatches) or 'NONE'}; "
        f"missing fields: {', '.join(missing_fields) or 'NONE'}; "
        "Preliminary OCR result; manual review required."
    )

    save_ocr_verification(
        db=db,
        person=person,
        status=status,
        explanation=explanation,
    )

    return {
        "document_id": document.id,
        "person_code": person.person_code,
        "document_type": document.document_type,
        "extraction_method": extraction_method,
        "ocr_status": status,
        "fields": {
            "full_name": {
                "extracted": extracted_name,
                "registered": person.full_name,
                "match": name_match,
            },
            "date_of_birth": {
                "extracted": extracted_dob,
                "registered": person.date_of_birth,
                "match": dob_match,
            },
        },
        "mismatches": mismatches,
        "missing_fields": missing_fields,
        "review_status": "PENDING_REVIEW",
        "message": (
            "OCR results are preliminary. An authorized administrator "
            "must review the evidence before deciding the document."
        ),
    }
