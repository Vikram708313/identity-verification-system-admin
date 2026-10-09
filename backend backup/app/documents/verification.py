import re


def normalize(value: str | None) -> str:
    if not value:
        return ""

    return re.sub(
        r"[^a-z0-9]",
        "",
        value.lower(),
    )


def normalize_date(value: str | None) -> str:
    if not value:
        return ""

    value = value.strip()

    match = re.match(
        r"(\d{2})[/-](\d{2})[/-](\d{4})",
        value,
    )

    if match:
        day, month, year = match.groups()
        return f"{year}{month}{day}"

    return re.sub(
        r"[^0-9]",
        "",
        value,
    )

def compare_identity_fields(
    extracted: dict,
    person,
) -> dict:

    extracted_name = normalize(
        extracted.get("name")
    )

    registered_name = normalize(
        person.full_name
    )

    extracted_dob = normalize_date(
        extracted.get("date_of_birth")
    )

    registered_dob = normalize_date(
        person.date_of_birth
    )

    extracted_id = normalize(
        extracted.get("identity_number")
    )

    registered_id = normalize(
        person.identity_number
    )

    name_match = (
        bool(extracted_name)
        and extracted_name == registered_name
    )

    dob_match = (
        bool(extracted_dob)
        and extracted_dob == registered_dob
    )

    identity_number_match = (
        bool(extracted_id)
        and extracted_id == registered_id
    )

    score = 0

    if name_match:
        score += 40

    if dob_match:
        score += 25

    if identity_number_match:
        score += 35

    if score >= 90:
        status = "PASS"
    elif score >= 50:
        status = "REVIEW"
    else:
        status = "FAIL"

    return {
        "document_match_score": score,
        "status": status,
        "name_match": name_match,
        "date_of_birth_match": dob_match,
        "identity_number_match": identity_number_match,
        "extracted": {
            "name": extracted.get("name"),
            "date_of_birth": extracted.get("date_of_birth"),
            "identity_number": extracted.get("identity_number"),
        },
    }