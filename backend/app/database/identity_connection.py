
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Locate the backend folder.
BACKEND_DIR = Path(__file__).resolve().parents[2]

# Create the data folder if it does not exist.
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Path for the new identity registry database.
DATABASE_PATH = DATA_DIR / "identity_registry.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


# Create a separate database connection.
identity_engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# Create a separate session for the identity database.
IdentitySessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=identity_engine,
)


# Separate model base for the identity database.
IdentityBase = declarative_base()


# Database session dependency.
def get_identity_db():
    db = IdentitySessionLocal()

    try:
        yield db
    finally:
        db.close()

