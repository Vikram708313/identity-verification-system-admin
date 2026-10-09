import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    get_current_admin,
    require_roles,
)
from app.auth.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.audit import create_audit_log
from app.database.connection import get_db
from app.database.models import Admin


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ---------------------------------------------------------
# Login rate limiting
# ---------------------------------------------------------

LOGIN_ATTEMPTS = {}

MAX_LOGIN_ATTEMPTS = 5

LOGIN_WINDOW_SECONDS = 15 * 60


# ---------------------------------------------------------
# Admin schemas
# ---------------------------------------------------------

class AdminCreateRequest(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    email: EmailStr | None = None
    role: str = "ADMIN"


class AdminStatusRequest(BaseModel):
    is_active: bool


# ---------------------------------------------------------
# Password login
# ---------------------------------------------------------

@router.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    username = form_data.username.strip()

    client_ip = (
        request.client.host
        if request.client
        else "unknown"
    )

    rate_key = (
        f"{client_ip}:{username.lower()}"
    )

    now = time.time()

    attempt_data = LOGIN_ATTEMPTS.get(rate_key)

    if attempt_data:
        first_attempt, attempts = attempt_data

        if now - first_attempt < LOGIN_WINDOW_SECONDS:

            if attempts >= MAX_LOGIN_ATTEMPTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        "Too many login attempts. "
                        "Please try again later."
                    ),
                )

        else:
            LOGIN_ATTEMPTS.pop(
                rate_key,
                None,
            )

    admin = (
        db.query(Admin)
        .filter(
            Admin.username == username,
            Admin.is_active == True,
        )
        .first()
    )

    if not admin or not verify_password(
        form_data.password,
        admin.password_hash,
    ):

        attempt_data = LOGIN_ATTEMPTS.get(
            rate_key
        )

        if attempt_data:
            first_attempt, attempts = attempt_data

            if now - first_attempt < LOGIN_WINDOW_SECONDS:
                LOGIN_ATTEMPTS[rate_key] = (
                    first_attempt,
                    attempts + 1,
                )
            else:
                LOGIN_ATTEMPTS[rate_key] = (
                    now,
                    1,
                )

        else:
            LOGIN_ATTEMPTS[rate_key] = (
                now,
                1,
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    LOGIN_ATTEMPTS.pop(
        rate_key,
        None,
    )

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


# ---------------------------------------------------------
# Current admin profile
# ---------------------------------------------------------

@router.get("/me")
def get_current_admin_profile(
    current_admin: Admin = Depends(
        get_current_admin
    ),
):
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "full_name": current_admin.full_name,
        "email": current_admin.email,
        "role": current_admin.role,
        "is_active": current_admin.is_active,
    }


# ---------------------------------------------------------
# List administrators
# SUPER_ADMIN only
# ---------------------------------------------------------

@router.get("/admins")
def list_admins(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(
        require_roles("SUPER_ADMIN")
    ),
):
    admins = (
        db.query(Admin)
        .order_by(Admin.id.asc())
        .all()
    )

    return [
        {
            "id": admin.id,
            "username": admin.username,
            "full_name": admin.full_name,
            "email": admin.email,
            "role": admin.role,
            "is_active": admin.is_active,
        }
        for admin in admins
    ]


# ---------------------------------------------------------
# Create administrator
# SUPER_ADMIN only
# ---------------------------------------------------------

@router.post("/admins")
def create_admin(
    data: AdminCreateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(
        require_roles("SUPER_ADMIN")
    ),
):
    username = data.username.strip()

    if len(username) < 3:
        raise HTTPException(
            status_code=400,
            detail="Username must contain at least 3 characters.",
        )

    if len(data.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters.",
        )

    role = data.role.strip().upper()

    if role not in {
        "ADMIN",
        "SUPER_ADMIN",
    }:
        raise HTTPException(
            status_code=400,
            detail="Role must be ADMIN or SUPER_ADMIN.",
        )

    existing_admin = (
        db.query(Admin)
        .filter(
            Admin.username == username
        )
        .first()
    )

    if existing_admin:
        raise HTTPException(
            status_code=409,
            detail="An administrator with this username already exists.",
        )

    if data.email:
        existing_email = (
            db.query(Admin)
            .filter(
                Admin.email == str(data.email).lower()
            )
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=409,
                detail="An administrator with this email already exists.",
            )

    admin = Admin(
        username=username,
        full_name=(
            data.full_name.strip()
            if data.full_name
            else None
        ),
        email=(
            str(data.email).lower()
            if data.email
            else None
        ),
        password_hash=hash_password(
            data.password
        ),
        role=role,
        is_active=True,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="ADMIN_CREATED",
        details={
            "admin_id": admin.id,
            "username": admin.username,
            "role": admin.role,
        },
    )

    return {
        "message": "Administrator created successfully",
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "full_name": admin.full_name,
            "email": admin.email,
            "role": admin.role,
            "is_active": admin.is_active,
        },
    }


# ---------------------------------------------------------
# Activate / deactivate administrator
# SUPER_ADMIN only
# ---------------------------------------------------------

@router.patch("/admins/{admin_id}/status")
def update_admin_status(
    admin_id: int,
    data: AdminStatusRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(
        require_roles("SUPER_ADMIN")
    ),
):
    admin = (
        db.query(Admin)
        .filter(
            Admin.id == admin_id
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Administrator not found.",
        )

    if admin.id == current_admin.id and not data.is_active:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account.",
        )

    admin.is_active = data.is_active

    db.commit()
    db.refresh(admin)

    create_audit_log(
        db=db,
        username=current_admin.username,
        action="ADMIN_STATUS_CHANGED",
        details={
            "admin_id": admin.id,
            "target_username": admin.username,
            "is_active": admin.is_active,
        },
    )

    return {
        "message": "Administrator status updated",
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "role": admin.role,
            "is_active": admin.is_active,
        },
    }