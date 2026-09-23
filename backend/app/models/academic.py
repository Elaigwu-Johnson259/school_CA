"""Academic sessions (school years) and the terms within them."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import TermName


class AcademicSession(Base, TimestampMixin):
    """A school year, e.g. "2026/2027". School-specific."""

    __tablename__ = "academic_sessions"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_session_school_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    school: Mapped["School"] = relationship(back_populates="academic_sessions")
    terms: Mapped[List["Term"]] = relationship(
        back_populates="academic_session", cascade="all, delete-orphan"
    )


class Term(Base, TimestampMixin):
    """First / Second / Third term within one academic session."""

    __tablename__ = "terms"
    __table_args__ = (
        UniqueConstraint("academic_session_id", "name", name="uq_term_session_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_session_id: Mapped[int] = mapped_column(
        ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[TermName] = mapped_column(
        SAEnum(TermName, native_enum=False, length=20), nullable=False
    )
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)

    academic_session: Mapped["AcademicSession"] = relationship(back_populates="terms")
