from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_URL = "sqlite:///./identity_verification.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def initialize_database():
    """
    Create missing tables and apply small schema updates
    required by the current application.
    """

    # Import models so SQLAlchemy knows about all tables.
    from app.database import models  # noqa: F401

    # Create tables that don't exist yet.
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)

    # =====================================================
    # IDENTITY DOCUMENTS
    # Add updated_at if it does not already exist.
    # =====================================================

    if "identity_documents" in inspector.get_table_names():

        columns = inspector.get_columns(
            "identity_documents"
        )

        column_names = {
            column["name"]
            for column in columns
        }

        if "updated_at" not in column_names:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE identity_documents
                        ADD COLUMN updated_at DATETIME
                        """
                    )
                )

                connection.execute(
                    text(
                        """
                        UPDATE identity_documents
                        SET updated_at = created_at
                        WHERE updated_at IS NULL
                        """
                    )
                )


    # =====================================================
    # ADMINS
    # Add full_name and email if they do not already exist.
    # =====================================================

    if "admins" in inspector.get_table_names():

        columns = inspector.get_columns(
            "admins"
        )

        column_names = {
            column["name"]
            for column in columns
        }


        # -----------------------------------------
        # Add full_name
        # -----------------------------------------

        if "full_name" not in column_names:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE admins
                        ADD COLUMN full_name VARCHAR(150)
                        """
                    )
                )


        # -----------------------------------------
        # Add email
        # -----------------------------------------

        if "email" not in column_names:

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        ALTER TABLE admins
                        ADD COLUMN email VARCHAR(150)
                        """
                    )
                )