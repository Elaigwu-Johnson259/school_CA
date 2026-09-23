"""
Import every model here so that Base.metadata is fully populated as soon
as `app.models` is imported once, anywhere (Alembic's env.py relies on
this to detect tables for autogenerate).
"""
from app.models.school import School
from app.models.user import User
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import SchoolClass, Subject, ClassSubject
from app.models.people import Teacher, Student, TeacherAssignment, StudentClass
from app.models.assessment import AssessmentType, Score, GradingScale
from app.models.result import Result, ReportCard
from app.models.audit import AuditLog

__all__ = [
    "School",
    "User",
    "AcademicSession",
    "Term",
    "SchoolClass",
    "Subject",
    "ClassSubject",
    "Teacher",
    "Student",
    "TeacherAssignment",
    "StudentClass",
    "AssessmentType",
    "Score",
    "GradingScale",
    "Result",
    "ReportCard",
    "AuditLog",
]
