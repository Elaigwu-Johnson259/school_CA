"""The School model: the root of every tenant's data."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class School(Base, TimestampMixin):
    """
    A single tenant on the platform.

    Every other school-owned table (users, students, teachers, classes,
    subjects, scores, results, ...) links back to a school via a
    ``school_id`` foreign key. Enforcing that a logged-in user can only
    touch rows whose ``school_id`` matches their own is the core of
    multi-tenant isolation (built in Phase 4).
    """

    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))
    motto: Mapped[Optional[str]] = mapped_column(String(200))
    website: Mapped[Optional[str]] = mapped_column(String(200))
    principal_name: Mapped[Optional[str]] = mapped_column(String(150))
    logo_path: Mapped[Optional[str]] = mapped_column(String(300))
    signature_path: Mapped[Optional[str]] = mapped_column(String(300))
    stamp_path: Mapped[Optional[str]] = mapped_column(String(300))
    primary_color: Mapped[Optional[str]] = mapped_column(String(20))
    secondary_color: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[List["User"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
    academic_sessions: Mapped[List["AcademicSession"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
    classes: Mapped[List["SchoolClass"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
    subjects: Mapped[List["Subject"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
    students: Mapped[List["Student"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
    teachers: Mapped[List["Teacher"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
    assessment_types: Mapped[List["AssessmentType"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
    grading_scales: Mapped[List["GradingScale"]] = relationship(
        back_populates="school", cascade="all, delete-orphan"
    )
