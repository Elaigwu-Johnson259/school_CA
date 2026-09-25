"""
Authentication business logic: verifying credentials and issuing/revoking
tokens. Kept separate from app/api/auth.py so it can be unit-tested (and
reused by other endpoints later) without going through HTTP.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.auth import RefreshToken
from app.models.enums import UserRole
from app.models.user import User


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Returns the User if email+password match an active account, else None.

    Deliberately returns the same "None" result for a wrong password, an
    unknown email, AND an inactive account. The API layer turns every case
    of None into one identical error message, so a caller can't use the
    response to figure out which reason applies (account enumeration).
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    """Creates an access + refresh token pair for a user and persists the refresh token."""
    access_token = create_access_token(user.id, user.role.value, user.school_id)
    refresh_token, jti, expires_at = create_refresh_token(user.id)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
    db.commit()
    return access_token, refresh_token


def get_valid_refresh_token(db: Session, jti: str) -> Optional[RefreshToken]:
    """Looks up a refresh token by its jti and returns it only if still usable."""
    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token_row is None or token_row.revoked:
        return None
    expires_at = token_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        return None
    return token_row


def revoke_refresh_token(db: Session, jti: str) -> None:
    """Marks a refresh token as revoked (used by /api/auth/logout)."""
    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token_row is not None:
        token_row.revoked = True
        db.commit()


def create_user(
    db: Session,
    *,
    email: str,
    password: str,
    role: UserRole,
    school_id: Optional[int] = None,
) -> User:
    """
    Controlled user creation, used by protected endpoints (not exposed
    publicly in Phase 3 — see the README for why). Callers are responsible
    for authorizing who's allowed to call this and with which role/school.
    """
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role,
        school_id=school_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
