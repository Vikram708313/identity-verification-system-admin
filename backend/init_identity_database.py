
from app.database.identity_connection import (
    IdentityBase,
    identity_engine,
)
from app.database import identity_models


def main():
    IdentityBase.metadata.create_all(bind=identity_engine)

    print("Identity registry database initialized successfully.")
    print(f"Database location: {identity_engine.url.database}")
    print("Tables created:")

    for table_name in IdentityBase.metadata.tables:
        print(f" - {table_name}")


if __name__ == "__main__":
    main()
