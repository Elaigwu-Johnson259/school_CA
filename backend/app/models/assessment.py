"""
Configurable assessment structure (Phase 7 will build the UI for this):
what components make up a subject's score (CA1, CA2, Exam, ...), how many
marks each is worth, and the raw scores teachers enter.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import AssessmentCategory


class AssessmentType(Base, TimestampMixin):
    """A configurable scoring component, e.g. CA1 = 10 marks, Exam = 60 marks."""

    __tablename__ = "assessment_types"
    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_assessment_type_school_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[AssessmentCategory] = mapped_column(
        SAEnum(AssessmentCategory, native_enum=False, length=10), nullable=False
    )
    max_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    school: Mapped["School"] = relationship(back_populates="assessment_types")


class Score(Base, TimestampMixin):
    """
    One score a teacher enters, for one student, in one subject, for one
    assessment component (e.g. "CA1"), in one term.
    """

    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "subject_id",
            "term_id",
            "assessment_type_id",
            name="uq_score_unique_entry",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assessment_type_id: Mapped[int] = mapped_column(
        ForeignKey("assessment_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recorded_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    value: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    student: Mapped["Student"] = relationship()
    subject: Mapped["Subject"] = relationship()
    school_class: Mapped["SchoolClass"] = relationship()
    term: Mapped["Term"] = relationship()
    assessment_type: Mapped["AssessmentType"] = relationship()
    recorded_by: Mapped[Optional["User"]] = relationship()


class GradingScale(Base, TimestampMixin):
    """Configurable grade boundaries per school, e.g. 70-100 = A = Excellent."""

    __tablename__ = "grading_scales"
    __table_args__ = (
        UniqueConstraint("school_id", "grade", name="uq_grading_scale_school_grade"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    grade: Mapped[str] = mapped_column(String(5), nullable=False)
    min_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(50))

    school: Mapped["School"] = relationship(back_populates="grading_scales")
