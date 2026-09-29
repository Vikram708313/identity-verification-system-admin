from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_admin
from app.auth.security import create_access_token, verify_password
from app.database.connection import get_db
from app.database.models import Admin


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    admin = (
        db.query(Admin)
        .filter(
            Admin.username == form_data.username,
            Admin.is_active == True,
        )
        .first()
    )

    if not admin or not verify_password(
        form_data.password,
        admin.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
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


@router.get("/me")
def get_current_admin_profile(
    current_admin: Admin = Depends(get_current_admin),
):
    return {
        "id": current_admin.id,
        "username": current_admin.username,
        "full_name": current_admin.full_name,
        "email": current_admin.email,
        "role": current_admin.role,
        "is_active": current_admin.is_active,
    }