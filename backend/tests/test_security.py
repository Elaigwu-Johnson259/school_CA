"""Unit tests for password hashing and JWT helpers (no DB, no HTTP)."""
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_does_not_store_plaintext():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert hashed.startswith("$2b$")  # bcrypt hash prefix


def test_verify_password_accepts_correct_password():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_wrong_password():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("wrong password", hashed) is False


def test_access_token_has_expected_claims():
    token = create_access_token(user_id=42, role="TEACHER", school_id=7)
    claims = decode_token(token)
    assert claims["sub"] == "42"
    assert claims["type"] == "access"
    assert claims["role"] == "TEACHER"
    assert claims["school_id"] == 7


def test_refresh_token_has_expected_claims_and_jti():
    token, jti, expires_at = create_refresh_token(user_id=42)
    claims = decode_token(token)
    assert claims["sub"] == "42"
    assert claims["type"] == "refresh"
    assert claims["jti"] == jti
    assert expires_at > datetime.now(timezone.utc)


def test_decode_token_rejects_garbage_token():
    with pytest.raises(JWTError):
        decode_token("not-a-real-token")


def test_decode_token_rejects_expired_token():
    expired_payload = {
        "sub": "1",
        "type": "access",
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
    }
    expired_token = jwt.encode(
        expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    with pytest.raises(JWTError):
        decode_token(expired_token)
