"""
Calculated results and report cards.

`Result` holds the calculated per-subject outcome for a student in a term
(the ResultCalculationService built in Phase 8 is what actually populates
this from raw Score rows). `ReportCard` holds the per-term overall summary,
workflow status, and the extra fields (attendance, remarks) that appear on
a printed report card.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import ResultStatus


class Result(Base, TimestampMixin):
    """A student's calculated result for one subject, in one term."""

    __tablename__ = "results"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "subject_id", "term_id", name="uq_result_student_subject_term"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ca_total: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    exam_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    grade: Mapped[Optional[str]] = mapped_column(String(5))
    subject_position: Mapped[Optional[int]] = mapped_column(Integer)

    student: Mapped["Student"] = relationship()
    subject: Mapped["Subject"] = relationship()
    term: Mapped["Term"] = relationship()


class ReportCard(Base, TimestampMixin):
    """A student's overall summary + workflow status for one term."""

    __tablename__ = "report_cards"
    __table_args__ = (
        UniqueConstraint("student_id", "term_id", name="uq_report_card_student_term"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    term_id: Mapped[int] = mapped_column(
        ForeignKey("terms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    total_marks: Mapped[float] = mapped_column(Numeric(6, 2), default=0, nullable=False)
    average: Mapped[float] = mapped_column(Numeric(5, 2), default=0, nullable=False)
    overall_grade: Mapped[Optional[str]] = mapped_column(String(5))
    class_position: Mapped[Optional[int]] = mapped_column(Integer)
    number_of_students: Mapped[Optional[int]] = mapped_column(Integer)
    school_days: Mapped[Optional[int]] = mapped_column(Integer)
    days_present: Mapped[Optional[int]] = mapped_column(Integer)
    days_absent: Mapped[Optional[int]] = mapped_column(Integer)
    class_teacher_remark: Mapped[Optional[str]] = mapped_column(String(300))
    principal_remark: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[ResultStatus] = mapped_column(
        SAEnum(ResultStatus, native_enum=False, length=20),
        default=ResultStatus.DRAFT,
        nullable=False,
    )
    verification_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True)

    student: Mapped["Student"] = relationship()
    term: Mapped["Term"] = relationship()
