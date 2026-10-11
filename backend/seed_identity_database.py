
from app.database.identity_connection import IdentitySessionLocal
from app.database.identity_models import RegistryPerson, RegistryWatchlist


DEMO_PEOPLE = [
    {
        "person_code": "P001",
        "full_name": "Aarav Patil",
        "date_of_birth": "12-04-2002",
        "city": "Pune",
        "demo_status": "GENUINE_DEMO",
    },
    {
        "person_code": "P002",
        "full_name": "Rohan Kulkarni",
        "date_of_birth": "25-08-2001",
        "city": "Mumbai",
        "demo_status": "GENUINE_DEMO",
    },
    {
        "person_code": "P003",
        "full_name": "Aditya Joshi",
        "date_of_birth": "17-01-2003",
        "city": "Nashik",
        "demo_status": "ALTERED_DOB_DEMO",
    },
    {
        "person_code": "P004",
        "full_name": "Omkar Shinde",
        "date_of_birth": "09-11-2002",
        "city": "Kolhapur",
        "demo_status": "GENUINE_DEMO",
    },
    {
        "person_code": "P005",
        "full_name": "Yash Deshmukh",
        "date_of_birth": "21-06-2001",
        "city": "Pune",
        "demo_status": "ALTERED_NAME_DEMO",
    },
    {
        "person_code": "P006",
        "full_name": "Siddhant More",
        "date_of_birth": "03-03-2003",
        "city": "Satara",
        "demo_status": "GENUINE_DEMO",
    },
]

DEMO_WATCHLIST = [
    {
        "reference_id": "WL001",
        "fictional_name": "Vikram Rao",
        "demo_reason": "Fictional identity fraud scenario for testing only",
        "risk_level": "HIGH",
    },
    {
        "reference_id": "WL002",
        "fictional_name": "Rahul Verma",
        "demo_reason": "Fictional document forgery scenario for testing only",
        "risk_level": "HIGH",
    },
    {
        "reference_id": "WL003",
        "fictional_name": "Sameer Khan",
        "demo_reason": "Fictional multiple identity scenario for testing only",
        "risk_level": "MEDIUM",
    },
]


def main():
    db = IdentitySessionLocal()

    try:
        # Insert people without creating duplicates
        for person_data in DEMO_PEOPLE:
            existing = (
                db.query(RegistryPerson)
                .filter_by(person_code=person_data["person_code"])
                .first()
            )

            if existing is None:
                db.add(RegistryPerson(**person_data))

        # Insert fictional watchlist records without duplicates
        for watchlist_data in DEMO_WATCHLIST:
            existing = (
                db.query(RegistryWatchlist)
                .filter_by(reference_id=watchlist_data["reference_id"])
                .first()
            )

            if existing is None:
                db.add(RegistryWatchlist(**watchlist_data))

        db.commit()

        print("Demo data inserted successfully.")
        print(f"People: {db.query(RegistryPerson).count()}")
        print(f"Watchlist records: {db.query(RegistryWatchlist).count()}")
        print("All records are fictional demonstration data.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
