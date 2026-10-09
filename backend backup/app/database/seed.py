from app.database.connection import Base, engine, SessionLocal
from app.database.models import Person, Watchlist


def create_tables():
    Base.metadata.create_all(bind=engine)


def seed_data():
    db = SessionLocal()

    try:
        # Prevent duplicate demo data
        existing_person = db.query(Person).first()

        if existing_person:
            print("Synthetic data already exists.")
            return

        # Synthetic demo people
        people = [
            Person(
                full_name="Aarav Sharma",
                date_of_birth="1995-04-12",
                gender="Male",
                address="101 Demo Street, Pune",
                identity_number="SYN-ID-1001",
                phone="9000000001",
                email="aarav@example.test",
            ),
            Person(
                full_name="Diya Patel",
                date_of_birth="1998-08-25",
                gender="Female",
                address="202 Demo Avenue, Pune",
                identity_number="SYN-ID-1002",
                phone="9000000002",
                email="diya@example.test",
            ),
            Person(
                full_name="Rohan Mehta",
                date_of_birth="1992-11-03",
                gender="Male",
                address="303 Demo Road, Mumbai",
                identity_number="SYN-ID-1003",
                phone="9000000003",
                email="rohan@example.test",
            ),
            Person(
                full_name="Ananya Rao",
                date_of_birth="1997-02-18",
                gender="Female",
                address="404 Demo Lane, Bengaluru",
                identity_number="SYN-ID-1004",
                phone="9000000004",
                email="ananya@example.test",
            ),
            Person(
                full_name="Kabir Singh",
                date_of_birth="1990-06-30",
                gender="Male",
                address="505 Demo Park, Delhi",
                identity_number="SYN-ID-1005",
                phone="9000000005",
                email="kabir@example.test",
            ),
        ]

        db.add_all(people)
        db.commit()

        # Synthetic watchlist records
        watchlist_records = [
            Watchlist(
                reference_id="SYN-WL-001",
                name="Vikram Demo",
                reason="Synthetic demonstration watchlist record",
                status="MANUAL_REVIEW",
            ),
            Watchlist(
                reference_id="SYN-WL-002",
                name="Neha Demo",
                reason="Synthetic demonstration watchlist record",
                status="MANUAL_REVIEW",
            ),
        ]

        db.add_all(watchlist_records)
        db.commit()

        print("Synthetic demo data inserted successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_tables()
    seed_data()