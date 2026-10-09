import hashlib
import secrets

from app.database.connection import SessionLocal
from app.database.models import Person, QR


def create_demo_qr():
    db = SessionLocal()

    try:
        person = (
            db.query(Person)
            .filter(Person.id == 1)
            .first()
        )

        if not person:
            print("Person with ID 1 was not found.")
            return

        token = secrets.token_urlsafe(32)

        qr_hash = hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

        qr_record = QR(
            person_id=person.id,
            payload=token,
            qr_hash=qr_hash,
        )

        db.add(qr_record)
        db.commit()

        print()
        print("======================================")
        print("DEMO USER QR CREATED")
        print("======================================")
        print()
        print("Person:")
        print(person.full_name)
        print()
        print("QR TOKEN:")
        print(token)
        print()
        print("QR HASH:")
        print(qr_hash)
        print()
        print("======================================")

    finally:
        db.close()


if __name__ == "__main__":
    create_demo_qr()