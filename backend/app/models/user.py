"""Shared login credentials for school administrators, teachers and students."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # School admins/teachers use email. Students authenticate with their
    # admission number, so student accounts do not require an email address.
    email: Mapped[Optional[str]] = mapped_column(String(200), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=20), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    school: Mapped[Optional["School"]] = relationship(back_populates="users")
    teacher_profile: Mapped[Optional["Teacher"]] = relationship(
        back_populates="user", uselist=False
    )
    student_profile: Mapped[Optional["Student"]] = relationship(
        back_populates="user", uselist=False
    )
