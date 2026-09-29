from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    date_of_birth: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    gender: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    address: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    identity_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )


class IdentityDocument(Base):
    __tablename__ = "identity_documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    person_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    document_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class QR(Base):
    __tablename__ = "qr_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    person_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    payload: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    qr_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


class Watchlist(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    reference_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="MANUAL_REVIEW"
    )


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    full_name: Mapped[str] = mapped_column(
        String(150),
        nullable=True
    )

    email: Mapped[str] = mapped_column(
        String(150),
        nullable=True
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )


class Audit(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    details: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )


class Verification(Base):
    __tablename__ = "verifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    person_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )

    admin_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )

    verification_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    face_match_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    document_match_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    qr_match_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    completeness_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    consistency_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )

    risk_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="PENDING"
    )

    decision: Mapped[str] = mapped_column(
        String(30),
        nullable=True
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )