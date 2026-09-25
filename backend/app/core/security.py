"""
Password hashing and JWT helpers.

Nothing in this file talks to the database — it's pure functions on top
of the app's config. Anything that needs a DB session (looking up a user,
storing a refresh token) lives in app/services/auth_service.py instead.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# bcrypt is the standard choice for password hashing: slow by design (so
# brute-forcing is expensive) and battle-tested. passlib gives us a simple
# hash_password/verify_password API on top of it.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    """Turn a plain-text password into a salted hash safe to store in the DB."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain-text password against a stored hash. Never the reverse."""
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: Optional[dict[str, Any]] = None,
) -> tuple[str, str]:
    """
    Builds and signs a JWT. Returns (token, jti) — callers that need to
    track/revoke the token (refresh tokens) keep the jti; callers that
    don't (access tokens) just discard it.
    """
    now = datetime.now(timezone.utc)
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": jti,
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def create_access_token(user_id: int, role: str, school_id: Optional[int]) -> str:
    """Short-lived token (ACCESS_TOKEN_EXPIRE_MINUTES) sent with every API request."""
    token, _ = _create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role, "school_id": school_id},
    )
    return token


def create_refresh_token(user_id: int) -> tuple[str, str, datetime]:
    """
    Long-lived token (REFRESH_TOKEN_EXPIRE_DAYS) used only to obtain new
    access tokens. Returns (token, jti, expires_at) — the caller
    (auth_service.issue_tokens) is responsible for storing jti/expires_at
    in the refresh_tokens table so it can be looked up and revoked later.
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    token, jti = _create_token(
        subject=str(user_id), token_type="refresh", expires_delta=expires_delta
    )
    expires_at = datetime.now(timezone.utc) + expires_delta
    return token, jti, expires_at


def decode_token(token: str) -> dict[str, Any]:
    """
    Verifies the token's signature and expiry and returns its claims.
    Raises jose.JWTError (via jwt.decode) if the token is invalid, expired,
    or tampered with — callers should catch that and respond with 401.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
