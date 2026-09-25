"""
Reusable FastAPI dependencies for authentication and authorization.

get_current_user() is the building block: any endpoint that needs a
logged-in user takes `current_user: User = Depends(get_current_user)`.
require_roles(...) builds on top of it for endpoints that also need to
check the user's role, e.g. `Depends(require_roles(UserRole.SCHOOL_ADMIN))`.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models.enums import UserRole
from app.models.user import User

# auto_error=False so we can raise our own 401 with a consistent message,
# rather than FastAPI's default "Not authenticated" for a missing header.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise unauthorized

    # Reject a refresh token being used where an access token is expected.
    if payload.get("type") != "access":
        raise unauthorized

    user_id = payload.get("sub")
    if user_id is None:
        raise unauthorized

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise unauthorized

    return user


def require_roles(*roles: UserRole):
    """
    Returns a dependency that only allows through users whose role is one
    of `roles`. Usage:

        @router.get("/admin-only")
        def admin_only(user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN))):
            ...

        @router.get("/admins-and-teachers")
        def both(user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER))):
            ...
    """

    def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return _check_role
