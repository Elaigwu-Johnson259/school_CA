"""Authentication business logic."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.models.auth import RefreshToken
from app.models.enums import UserRole
from app.models.people import Student
from app.models.user import User


def authenticate_user(db: Session, identifier: str, password: str) -> Optional[User]:
    """Authenticate email-based staff accounts or admission-number students."""
    identifier = identifier.strip()
    user: Optional[User] = None

    if "@" in identifier:
        user = db.query(User).filter(User.email == identifier).first()
    else:
        student = (
            db.query(Student)
            .filter(Student.admission_number == identifier)
            .first()
        )
        if student is not None and student.user_id is not None:
            user = db.get(User, student.user_id)

    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_tokens(db: Session, user: User) -> tuple[str, str]:
    access_token = create_access_token(user.id, user.role.value, user.school_id)
    refresh_token, jti, expires_at = create_refresh_token(user.id)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
    db.commit()
    return access_token, refresh_token


def get_valid_refresh_token(db: Session, jti: str) -> Optional[RefreshToken]:
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
    token_row = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if token_row is not None:
        token_row.revoked = True
        db.commit()


def create_user(
    db: Session,
    *,
    email: Optional[str],
    password: str,
    role: UserRole,
    school_id: Optional[int] = None,
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role,
        school_id=school_id,
    )
    db.add(user)
    db.flush()
    return user
