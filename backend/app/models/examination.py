"""Examination, question, reference, script and marking infrastructure."""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ExaminationStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    CLOSED = "CLOSED"


class QuestionType(str, enum.Enum):
    OBJECTIVE = "OBJECTIVE"
    SUBJECTIVE = "SUBJECTIVE"


class ReferenceMaterialType(str, enum.Enum):
    TYPED_ANSWER = "TYPED_ANSWER"
    MARKING_GUIDANCE = "MARKING_GUIDANCE"
    UPLOAD = "UPLOAD"
    HANDWRITTEN = "HANDWRITTEN"
    WORKED_SOLUTION = "WORKED_SOLUTION"


class ExaminationFileType(str, enum.Enum):
    QUESTION_PAPER = "QUESTION_PAPER"


class ScriptStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY_FOR_MARKING = "READY_FOR_MARKING"
    AI_MARKED = "AI_MARKED"
    TEACHER_REVIEW = "TEACHER_REVIEW"
    APPROVED = "APPROVED"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    MARKING_FAILED = "MARKING_FAILED"


class ReviewStatus(str, enum.Enum):
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"


class Examination(Base, TimestampMixin):
    __tablename__ = "examinations"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "academic_session_id", "term_id", "school_class_id", "subject_id", "title",
            name="uq_exam_context_title",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_session_id: Mapped[int] = mapped_column(ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    term_id: Mapped[int] = mapped_column(ForeignKey("terms.id", ondelete="CASCADE"), nullable=False, index=True)
    school_class_id: Mapped[int] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    examination_date: Mapped[Optional[date]] = mapped_column(Date)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    maximum_score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    status: Mapped[ExaminationStatus] = mapped_column(
        SAEnum(ExaminationStatus, native_enum=False, length=20), default=ExaminationStatus.DRAFT, nullable=False, index=True
    )

    questions: Mapped[List["ExaminationQuestion"]] = relationship(back_populates="examination", cascade="all, delete-orphan", order_by="ExaminationQuestion.display_order")
    files: Mapped[List["ExaminationFile"]] = relationship(back_populates="examination", cascade="all, delete-orphan")
    scripts: Mapped[List["StudentExaminationScript"]] = relationship(back_populates="examination", cascade="all, delete-orphan")


class ExaminationQuestion(Base, TimestampMixin):
    __tablename__ = "examination_questions"
    __table_args__ = (
        UniqueConstraint("examination_id", "question_number", name="uq_exam_question_number"),
        UniqueConstraint("examination_id", "display_order", name="uq_exam_question_order"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    examination_id: Mapped[int] = mapped_column(ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    question_number: Mapped[str] = mapped_column(String(30), nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(100))
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType, native_enum=False, length=20), nullable=False)
    maximum_marks: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    correct_option: Mapped[Optional[str]] = mapped_column(String(50))
    expected_concepts: Mapped[Optional[str]] = mapped_column(Text)
    key_points: Mapped[Optional[str]] = mapped_column(Text)
    acceptable_alternatives: Mapped[Optional[str]] = mapped_column(Text)
    partial_credit_guidance: Mapped[Optional[str]] = mapped_column(Text)
    marking_guidance: Mapped[Optional[str]] = mapped_column(Text)
    teacher_notes: Mapped[Optional[str]] = mapped_column(Text)

    examination: Mapped["Examination"] = relationship(back_populates="questions")
    references: Mapped[List["QuestionReferenceMaterial"]] = relationship(back_populates="question", cascade="all, delete-orphan")
    answers: Mapped[List["StudentQuestionAnswer"]] = relationship(back_populates="question")


class QuestionReferenceMaterial(Base, TimestampMixin):
    __tablename__ = "question_reference_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("examination_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    material_type: Mapped[ReferenceMaterialType] = mapped_column(SAEnum(ReferenceMaterialType, native_enum=False, length=30), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200))
    text_content: Mapped[Optional[str]] = mapped_column(Text)
    original_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    content_type: Mapped[Optional[str]] = mapped_column(String(120))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    question: Mapped["ExaminationQuestion"] = relationship(back_populates="references")


class ExaminationFile(Base, TimestampMixin):
    __tablename__ = "examination_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    examination_id: Mapped[int] = mapped_column(ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    file_type: Mapped[ExaminationFileType] = mapped_column(SAEnum(ExaminationFileType, native_enum=False, length=30), nullable=False)
    original_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(120))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    title: Mapped[Optional[str]] = mapped_column(String(200))

    examination: Mapped["Examination"] = relationship(back_populates="files")


class StudentExaminationScript(Base, TimestampMixin):
    __tablename__ = "student_examination_scripts"
    __table_args__ = (
        UniqueConstraint("examination_id", "student_id", name="uq_exam_student_script"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    examination_id: Mapped[int] = mapped_column(ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    original_file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(120))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[ScriptStatus] = mapped_column(SAEnum(ScriptStatus, native_enum=False, length=30), default=ScriptStatus.UPLOADED, nullable=False, index=True)
    processing_error: Mapped[Optional[str]] = mapped_column(Text)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    examination: Mapped["Examination"] = relationship(back_populates="scripts")
    student: Mapped["Student"] = relationship()
    answers: Mapped[List["StudentQuestionAnswer"]] = relationship(back_populates="script", cascade="all, delete-orphan")


class StudentQuestionAnswer(Base, TimestampMixin):
    __tablename__ = "student_question_answers"
    __table_args__ = (
        UniqueConstraint("script_id", "question_id", name="uq_script_question_answer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    script_id: Mapped[int] = mapped_column(ForeignKey("student_examination_scripts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("examination_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    original_answer_image_path: Mapped[Optional[str]] = mapped_column(String(500))
    page_number: Mapped[Optional[int]] = mapped_column(Integer)
    answer_position: Mapped[Optional[str]] = mapped_column(String(100))
    extraction_status: Mapped[Optional[str]] = mapped_column(String(30))
    ai_proposed_score: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    ai_evidence: Mapped[Optional[str]] = mapped_column(Text)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    teacher_final_score: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    teacher_adjustment: Mapped[Optional[float]] = mapped_column(Numeric(7, 2))
    teacher_review_notes: Mapped[Optional[str]] = mapped_column(Text)
    review_status: Mapped[ReviewStatus] = mapped_column(SAEnum(ReviewStatus, native_enum=False, length=20), default=ReviewStatus.PENDING, nullable=False, index=True)

    script: Mapped["StudentExaminationScript"] = relationship(back_populates="answers")
    question: Mapped["ExaminationQuestion"] = relationship(back_populates="answers")
