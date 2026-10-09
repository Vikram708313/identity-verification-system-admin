from app.auth.security import hash_password
from app.database.connection import SessionLocal
from app.database.models import Admin


def seed_admin():
    db = SessionLocal()

    try:
        existing_admin = (
            db.query(Admin)
            .filter(Admin.username == "admin")
            .first()
        )

        # -------------------------------------------------
        # UPDATE EXISTING ADMIN
        # -------------------------------------------------

        if existing_admin:
            existing_admin.full_name = "System Administrator"
            existing_admin.email = "admin@trustvision.local"
            existing_admin.password_hash = hash_password("Admin@123")
            existing_admin.role = "SUPER_ADMIN"
            existing_admin.is_active = True
            
            db.commit()
            
            print("Admin account updated successfully.")
            return

        # -------------------------------------------------
        # CREATE ADMIN IF IT DOES NOT EXIST
        # -------------------------------------------------

        admin = Admin(
            username="admin",
            full_name="System Administrator",
            email="admin@trustvision.local",
            password_hash=hash_password("Admin@123"),
            role="SUPER_ADMIN",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print("Synthetic admin account created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_admin()