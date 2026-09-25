"""Authentication endpoints: login, current user, token refresh, logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, decode_token
from app.models.user import User
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Same message for "no such email", "wrong password", and "inactive
# account" — see auth_service.authenticate_user for why.
INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password",
)

INVALID_REFRESH_TOKEN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired refresh token",
)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise INVALID_CREDENTIALS

    access_token, refresh_token = auth_service.issue_tokens(db, user)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> AccessTokenResponse:
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise INVALID_REFRESH_TOKEN

    # Reject an access token being used where a refresh token is expected.
    if claims.get("type") != "refresh":
        raise INVALID_REFRESH_TOKEN

    jti = claims.get("jti")
    user_id = claims.get("sub")
    if jti is None or user_id is None:
        raise INVALID_REFRESH_TOKEN

    if auth_service.get_valid_refresh_token(db, jti) is None:
        raise INVALID_REFRESH_TOKEN

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise INVALID_REFRESH_TOKEN

    access_token = create_access_token(user.id, user.role.value, user.school_id)
    return AccessTokenResponse(access_token=access_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    """
    Revokes the given refresh token so it can no longer be used at
    /api/auth/refresh. The access token itself keeps working until it
    naturally expires (it's short-lived and stateless by design) — the
    frontend is expected to discard it immediately on logout.
    """
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        # Already invalid/expired: nothing to revoke, and logging out
        # should never fail from the client's point of view.
        return None

    if claims.get("type") == "refresh" and claims.get("jti"):
        auth_service.revoke_refresh_token(db, claims["jti"])
    return None
