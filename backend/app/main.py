from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env before importing authentication modules
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# =====================================================
# DATABASE
# =====================================================

from app.database.connection import (
    get_db,
    initialize_database,
)

from app.database.models import (
    Person,
    Watchlist,
    IdentityDocument,
    Audit,
)

# =====================================================
# AUTH
# =====================================================

from app.auth.routes import router as auth_router
from app.auth.otp import router as otp_router
from app.auth.dependencies import get_current_admin

# =====================================================
# OTHER ROUTERS
# =====================================================

from app.face.routes import router as face_router
from app.verification.routes import router as verification_router
from app.people.routes import router as people_router
from app.documents.routes import router as documents_router
from app.qr.routes import router as qr_router

# =====================================================
# AUDIT
# =====================================================

from app.audit import verify_audit_chain


# =====================================================
# INITIALIZE DATABASE
# =====================================================

initialize_database()


# =====================================================
# CREATE FASTAPI APP
# =====================================================

app = FastAPI(
    title="AI Identity Verification System",
    description="Local synthetic identity verification prototype",
    version="0.4.0",
)


# =====================================================
# CORS
# =====================================================

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


# =====================================================
# REGISTER ROUTERS
# =====================================================

print("========================================")
print("REGISTERING API ROUTERS")
print("========================================")

app.include_router(auth_router)
print("AUTH ROUTER REGISTERED")

app.include_router(otp_router)
print("OTP ROUTER REGISTERED")

app.include_router(face_router)
print("FACE ROUTER REGISTERED")

app.include_router(verification_router)
print("VERIFICATION ROUTER REGISTERED")

app.include_router(people_router)
print("PEOPLE ROUTER REGISTERED")

app.include_router(documents_router)
print("DOCUMENT ROUTER REGISTERED")

app.include_router(qr_router)
print("QR ROUTER REGISTERED")

print("========================================")
print("ROUTERS REGISTERED")
print("========================================")


# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():
    return {
        "message": "Identity Verification System API is running",
        "environment": "local",
        "data_type": "synthetic_demo_data",
    }


# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =====================================================
# PEOPLE
# =====================================================

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


# =====================================================
# DOCUMENTS
# =====================================================

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
            "file_hash": document.file_hash,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }
        for document in documents
    ]


# =====================================================
# WATCHLIST
# =====================================================

@app.get("/watchlist")
def get_watchlist(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
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


# =====================================================
# AUDIT
# =====================================================

@app.get("/audit")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    records = (
        db.query(Audit)
        .order_by(Audit.id.desc())
        .all()
    )

    return [
        {
            "id": record.id,
            "username": record.username,
            "action": record.action,
            "details": record.details,
            "timestamp": record.timestamp,
            "previous_hash": record.previous_hash,
            "record_hash": record.record_hash,
        }
        for record in records
    ]


# =====================================================
# AUDIT INTEGRITY
# =====================================================

@app.get("/audit/integrity")
def check_audit_integrity(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    return verify_audit_chain(db)


# =====================================================
# PRINT FINAL ROUTES
# =====================================================

print("========================================")
print("FINAL REGISTERED ROUTES")
print("========================================")

for route in app.routes:
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", None)

    if path:
        print(
            f"{methods if methods else ''} {path}"
        )

print("========================================")