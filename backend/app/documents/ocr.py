from io import BytesIO
import re

from PIL import Image, ImageOps
import pytesseract


def extract_document_text(file_bytes: bytes) -> str:
    image = Image.open(BytesIO(file_bytes))

    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)

    text = pytesseract.image_to_string(
        image,
        config="--psm 6",
    )

    return text


def extract_identity_fields(text: str) -> dict:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    name = ""
    date_of_birth = ""
    identity_number = ""

    for index, line in enumerate(lines):

        if line.lower() == "name" and index + 1 < len(lines):
            name = lines[index + 1]

        if (
            line.lower() in {"date of birth", "dob"}
            and index + 1 < len(lines)
        ):
            date_of_birth = lines[index + 1]

    id_match = re.search(
    r"\b(?:[A-Z]{2,10}-[A-Z0-9]+(?:-[A-Z0-9]+)*)\b",
    text,
)

    if id_match:
        identity_number = id_match.group(0)
    else:
        id_match = re.search(
        r"\b\d{4}\s+\d{4}\s+\d{4}\b",
        text,
    )

    if id_match:
        identity_number = id_match.group(0)

    return {
        "name": name,
        "date_of_birth": date_of_birth,
        "identity_number": identity_number,
    }