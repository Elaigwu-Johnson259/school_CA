"""Teachers, students, and the join tables linking them to classes/subjects."""
from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.models.enums import Gender, PersonStatus


class Teacher(Base, TimestampMixin):
    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint("school_id", "employee_id", name="uq_teacher_school_employee_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Optional link to a login account. A teacher record can exist before
    # (or without) portal access being set up for them.
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    employee_id: Mapped[Optional[str]] = mapped_column(String(50))
    profile_photo_path: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[PersonStatus] = mapped_column(
        SAEnum(PersonStatus, native_enum=False, length=20),
        default=PersonStatus.ACTIVE,
        nullable=False,
    )

    school: Mapped["School"] = relationship(back_populates="teachers")
    user: Mapped[Optional["User"]] = relationship(back_populates="teacher_profile")
    assignments: Mapped[List["TeacherAssignment"]] = relationship(
        back_populates="teacher", cascade="all, delete-orphan"
    )


class Student(Base, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint(
            "school_id", "admission_number", name="uq_student_school_admission_number"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    admission_number: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[Optional[Gender]] = mapped_column(
        SAEnum(Gender, native_enum=False, length=10)
    )
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(150))
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(30))
    address: Mapped[Optional[str]] = mapped_column(String(300))
    photo_path: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[PersonStatus] = mapped_column(
        SAEnum(PersonStatus, native_enum=False, length=20),
        default=PersonStatus.ACTIVE,
        nullable=False,
    )

    school: Mapped["School"] = relationship(back_populates="students")
    user: Mapped[Optional["User"]] = relationship(back_populates="student_profile")
    class_enrollments: Mapped[List["StudentClass"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )


class TeacherAssignment(Base, TimestampMixin):
    """Assigns one teacher to teach one subject in one class."""

    __tablename__ = "teacher_assignments"
    __table_args__ = (
        UniqueConstraint(
            "teacher_id", "school_class_id", "subject_id", name="uq_teacher_class_subject"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    teacher: Mapped["Teacher"] = relationship(back_populates="assignments")
    school_class: Mapped["SchoolClass"] = relationship()
    subject: Mapped["Subject"] = relationship()


class StudentClass(Base, TimestampMixin):
    """Which class a student belongs to for a given academic session (students move up each year)."""

    __tablename__ = "student_classes"
    __table_args__ = (
        UniqueConstraint(
            "student_id", "academic_session_id", name="uq_student_session_enrollment"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    school_class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    academic_session_id: Mapped[int] = mapped_column(
        ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )

    student: Mapped["Student"] = relationship(back_populates="class_enrollments")
    school_class: Mapped["SchoolClass"] = relationship(back_populates="student_enrollments")
    academic_session: Mapped["AcademicSession"] = relationship()
