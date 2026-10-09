from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.database.connection import get_db
from app.database.models import Admin


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Authenticate the current administrator.

    The username is taken from the JWT.
    The current role and account status are always
    read from the database.
    """

    payload = decode_access_token(token)

    username = payload.get("sub")

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
        )

    admin = (
        db.query(Admin)
        .filter(
            Admin.username == username,
            Admin.is_active == True,
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account not found or inactive",
        )

    return admin


def require_roles(*allowed_roles):
    """
    Restrict an endpoint to specific administrator roles.

    Example:

        current_admin = Depends(
            require_roles("SUPER_ADMIN")
        )
    """

    def role_checker(
        current_admin: Admin = Depends(get_current_admin),
    ):
        if current_admin.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_admin

    return role_checker