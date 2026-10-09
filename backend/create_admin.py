from getpass import getpass

from app.database.connection import SessionLocal
from app.database.models import Admin
from app.auth.security import hash_password


db = SessionLocal()

try:
    username = "admin2"
    admin = (
        db.query(Admin)
        .filter(Admin.username == username)
        .first()
    )

    if not admin:
        print("Admin account not found.")
    else:
        password = getpass("Enter new password (8+ characters): ")
        confirm = getpass("Confirm new password: ")

        if len(password) < 8:
            print("Password must be at least 8 characters.")
        elif password != confirm:
            print("Passwords do not match.")
        else:
            admin.password_hash = hash_password(password)
            admin.is_active = True
            db.commit()
            print("Password reset successfully for admin2.")

except Exception as exc:
    db.rollback()
    print(f"Password reset failed: {exc}")

finally:
    db.close()