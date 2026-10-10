
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.identity_connection import IdentityBase


# 1. People registered in the identity registry
class RegistryPerson(IdentityBase):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    person_code: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(80), nullable=False)
    demo_status: Mapped[str] = mapped_column(
        String(40), default="GENUINE_DEMO", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


# 2. Image metadata and SHA-256 hashes
class PersonImage(IdentityBase):
    __tablename__ = "person_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id"), nullable=False, index=True
    )
    image_type: Mapped[str] = mapped_column(String(40), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


# 3. Identity document metadata
class RegistryDocument(IdentityBase):
    __tablename__ = "registry_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id"), nullable=False, index=True
    )
    document_type: Mapped[str] = mapped_column(String(40), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    demo_status: Mapped[str] = mapped_column(
        String(40), default="PENDING_REVIEW", nullable=False
    )


# 4. Fictional watchlist records for demonstration only
class RegistryWatchlist(IdentityBase):
    __tablename__ = "registry_watchlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_id: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False
    )
    fictional_name: Mapped[str] = mapped_column(String(100), nullable=False)
    demo_reason: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(
        String(20), default="MEDIUM", nullable=False
    )


# 5. Verification results and risk assessment
class RegistryVerification(IdentityBase):
    __tablename__ = "registry_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[int] = mapped_column(
        ForeignKey("people.id"), nullable=False, index=True
    )
    face_match_score: Mapped[float] = mapped_column(Float, nullable=True)
    document_match_score: Mapped[float] = mapped_column(Float, nullable=True)
    risk_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(30), default="PENDING", nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )


# 6. Audit log for document review decisions
class RegistryDocumentAudit(IdentityBase):
    __tablename__ = "registry_document_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("registry_documents.id"), nullable=False, index=True
    )
    reviewer_identifier: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Nullable to preserve compatibility with existing audit records.
    audit_hash: Mapped[str] = mapped_column(
        String(64), nullable=True
    )
    previous_hash: Mapped[str] = mapped_column(
        String(64), nullable=True
    )

    # JSON snapshot of OCR evidence used during admin review.
    # Nullable to preserve compatibility with older audit records.
    ocr_evidence: Mapped[str] = mapped_column(
        Text, nullable=True
    )
# 7. Hash-linked ledger blocks for audit integrity
class BlockchainLedgerBlock(IdentityBase):
    __tablename__ = "blockchain_ledger_blocks"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )
    block_index: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False
    )
    audit_id: Mapped[int] = mapped_column(
        ForeignKey("registry_document_audits.id"),
        unique=True,
        nullable=False,
    )
    audit_hash: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    previous_block_hash: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    block_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )