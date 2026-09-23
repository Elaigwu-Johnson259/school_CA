"""Classes and subjects a school defines, and which subjects are taught in which class."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class SchoolClass(Base, TimestampMixin):
    """
    A class/grade level, e.g. "SS 2".

    Named SchoolClass (table name "classes") because `class` is a Python
    keyword and can't be used as a model name.
    """

    __tablename__ = "classes"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_class_school_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    school: Mapped["School"] = relationship(back_populates="classes")
    class_subjects: Mapped[List["ClassSubject"]] = relationship(
        back_populates="school_class", cascade="all, delete-orphan"
    )
    student_enrollments: Mapped[List["StudentClass"]] = relationship(
        back_populates="school_class", cascade="all, delete-orphan"
    )


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_subject_school_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[Optional[str]] = mapped_column(String(20))

    school: Mapped["School"] = relationship(back_populates="subjects")
    class_links: Mapped[List["ClassSubject"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan"
    )


class ClassSubject(Base, TimestampMixin):
    """Join table: which subjects are offered in which class."""

    __tablename__ = "class_subjects"
    __table_args__ = (
        UniqueConstraint("school_class_id", "subject_id", name="uq_class_subject"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    school_class: Mapped["SchoolClass"] = relationship(back_populates="class_subjects")
    subject: Mapped["Subject"] = relationship(back_populates="class_links")
