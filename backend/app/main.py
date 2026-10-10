
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
# AUTHENTICATION AND OTP
# =====================================================

from app.auth.routes import router as auth_router
from app.auth.otp import router as otp_router
from app.auth.dependencies import get_current_admin

# =====================================================
# EXISTING ROUTERS
# =====================================================

from app.face.routes import router as face_router
from app.verification.routes import router as verification_router
from app.people.routes import router as people_router
from app.documents.routes import router as documents_router
from app.qr.routes import router as qr_router

# =====================================================
# IDENTITY REGISTRY ROUTERS
# =====================================================

from app.registry.routes import router as registry_router
from app.registry.face_verification import (
    router as registry_face_verification_router,
)
from app.registry.document_upload import (
    router as document_upload_router,
)
from app.registry.ocr_verification import (
    router as ocr_verification_router,
)

from app.registry.face_upload import router as face_upload_router
from app.registry.screening_cases import router as screening_cases_router
from app.registry.blockchain_ledger import router as blockchain_ledger_router

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
    title="TrustVision AI - Identity Verification System",
    description="Local synthetic identity verification prototype",
    version="0.6.0",
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
# REGISTER ALL ROUTERS
# =====================================================

print("========================================")
print("REGISTERING API ROUTERS")
print("========================================")

routers = [
    (auth_router, "AUTH"),
    (otp_router, "OTP"),
    (face_router, "FACE"),
    (verification_router, "VERIFICATION"),
    (people_router, "PEOPLE"),
    (documents_router, "DOCUMENT"),
    (qr_router, "QR"),
    (registry_router, "IDENTITY REGISTRY"),
    (document_upload_router, "DOCUMENT UPLOAD"),
    (face_upload_router, "FACE UPLOAD"),
    (
        registry_face_verification_router,
        "REGISTRY FACE VERIFICATION",
    ),
    (ocr_verification_router, "OCR VERIFICATION"),
    (screening_cases_router, "SCREENING CASES"),
    (blockchain_ledger_router, "BLOCKCHAIN LEDGER"),
]

for router, router_name in routers:
    app.include_router(router)
    print(f"{router_name} ROUTER REGISTERED")

print("========================================")
print("ROUTERS REGISTERED")
print("========================================")

# =====================================================
# ROOT ENDPOINT
# =====================================================

@app.get("/")
def root():
    return {
        "message": "TrustVision AI Identity Verification API is running",
        "environment": "local",
        "data_type": "synthetic_demo_data",
    }

# =====================================================
# HEALTH ENDPOINT
# =====================================================

@app.get("/health")
def health():
    return {"status": "healthy"}

# =====================================================
# PEOPLE ENDPOINT
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
# DOCUMENTS ENDPOINT
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
# WATCHLIST ENDPOINT
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
# AUDIT ENDPOINT
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
# AUDIT INTEGRITY ENDPOINT
# =====================================================

@app.get("/audit/integrity")
def check_audit_integrity(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    return verify_audit_chain(db)

# =====================================================
# PRINT REGISTERED ROUTES
# =====================================================

print("========================================")
print("FINAL REGISTERED ROUTES")
print("========================================")

for route in app.routes:
    path = getattr(route, "path", None)
    methods = getattr(route, "methods", None)

    if path:
        print(f"{methods if methods else ''} {path}")

print("========================================")
