from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.auth.routes import router as auth_router

from app.database.connection import (
    get_db,
    initialize_database,
)

from app.database.models import (
    Person,
    Watchlist,
    IdentityDocument,
)

from app.verification.routes import (
    router as verification_router,
)


# Initialize database and apply required schema updates
initialize_database()


app = FastAPI(
    title="AI Identity Verification System",
    description="Local synthetic identity verification prototype",
    version="0.4.0",
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------

app.include_router(auth_router)
app.include_router(verification_router)


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Identity Verification System API is running",
        "environment": "local",
        "data_type": "synthetic_demo_data",
    }


# ---------------------------------------------------------
# Health
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# People
# ---------------------------------------------------------

@app.get("/people")
def get_people(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    people = db.query(Person).all()

    return [
        {
            "id": person.id,
            "full_name": person.full_name,
            "identity_number": person.identity_number,
            "date_of_birth": person.date_of_birth,
            "gender": person.gender,
        }
        for person in people
    ]


# ---------------------------------------------------------
# Documents
# ---------------------------------------------------------

@app.get("/documents")
def get_documents(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    documents = db.query(IdentityDocument).all()

    return [
        {
            "id": document.id,
            "person_id": document.person_id,
            "document_type": document.document_type,
            "document_number": document.document_number,
            "file_path": document.file_path,
            "file_hash": document.file_hash,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
        for document in documents
    ]


# ---------------------------------------------------------
# Watchlist
# ---------------------------------------------------------

@app.get("/watchlist")
def get_watchlist(
    db: Session = Depends(get_db),
):
    records = db.query(Watchlist).all()

    return [
        {
            "id": record.id,
            "reference_id": record.reference_id,
            "name": record.name,
            "reason": record.reason,
            "status": record.status,
        }
        for record in records
    ]