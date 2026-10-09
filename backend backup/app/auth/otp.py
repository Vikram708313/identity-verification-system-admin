import hashlib
import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.security import create_access_token
from app.database.connection import get_db
from app.database.models import Admin, OTPCode


router = APIRouter(
    prefix="/auth",
    tags=["Authentication OTP"],
)


OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5

OTP_REQUEST_COOLDOWN_SECONDS = 60
MAX_OTP_REQUESTS = 5
OTP_REQUEST_WINDOW_MINUTES = 15


class EmailOTPRequest(BaseModel):
    email: str


class EmailOTPVerifyRequest(BaseModel):
    email: str
    otp: str


def hash_otp(otp: str) -> str:
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


@router.post("/request-email-otp")
def request_email_otp(
    data: EmailOTPRequest,
    db: Session = Depends(get_db),
):
    email = data.email.strip().lower()

    admin = (
        db.query(Admin)
        .filter(
            Admin.email == email,
            Admin.is_active == True,
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active admin account found for this email",
        )

    now = datetime.utcnow()

    recent_otps = (
        db.query(OTPCode)
        .filter(
            OTPCode.admin_id == admin.id,
            OTPCode.channel == "email",
            OTPCode.destination == email,
            OTPCode.created_at
            >= now - timedelta(
                minutes=OTP_REQUEST_WINDOW_MINUTES
            ),
        )
        .order_by(OTPCode.created_at.desc())
        .all()
    )

    if recent_otps:
        seconds_since_last_request = (
            now - recent_otps[0].created_at
        ).total_seconds()

        if (
            seconds_since_last_request
            < OTP_REQUEST_COOLDOWN_SECONDS
        ):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Please wait before requesting another OTP"
                ),
            )

    if len(recent_otps) >= MAX_OTP_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many OTP requests. "
                "Please try again later."
            ),
        )

    (
        db.query(OTPCode)
        .filter(
            OTPCode.admin_id == admin.id,
            OTPCode.channel == "email",
            OTPCode.is_used == False,
        )
        .update(
            {
                OTPCode.is_used: True
            },
            synchronize_session=False,
        )
    )

    otp = f"{secrets.randbelow(1000000):06d}"

    otp_record = OTPCode(
        admin_id=admin.id,
        channel="email",
        destination=email,
        otp_hash=hash_otp(otp),
        expires_at=(
            now
            + timedelta(
                minutes=OTP_EXPIRY_MINUTES
            )
        ),
        attempts=0,
        is_used=False,
    )

    db.add(otp_record)
    db.commit()

    print(
        "\n========================================"
    )
    print("DEVELOPMENT EMAIL OTP")
    print(f"Email: {email}")
    print(f"OTP: {otp}")
    print("Expires in: 5 minutes")
    print(
        "========================================\n"
    )

    return {
        "message": "OTP generated successfully",
    }


@router.post("/verify-email-otp")
def verify_email_otp(
    data: EmailOTPVerifyRequest,
    db: Session = Depends(get_db),
):
    email = data.email.strip().lower()
    otp = data.otp.strip()

    if not otp.isdigit() or len(otp) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be a 6-digit number",
        )

    admin = (
        db.query(Admin)
        .filter(
            Admin.email == email,
            Admin.is_active == True,
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    otp_record = (
        db.query(OTPCode)
        .filter(
            OTPCode.admin_id == admin.id,
            OTPCode.channel == "email",
            OTPCode.destination == email,
            OTPCode.is_used == False,
        )
        .order_by(OTPCode.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP",
        )

    if datetime.utcnow() > otp_record.expires_at:
        otp_record.is_used = True
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="OTP has expired",
        )

    if otp_record.attempts >= MAX_OTP_ATTEMPTS:
        otp_record.is_used = True
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many incorrect OTP attempts",
        )

    if not secrets.compare_digest(
        otp_record.otp_hash,
        hash_otp(otp),
    ):
        otp_record.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP",
        )

    otp_record.is_used = True
    db.commit()

    access_token = create_access_token(
        {
            "sub": admin.username,
            "role": admin.role,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": admin.role,
    }