"""
Shared enum types used across models.

Stored as plain strings in the database (native_enum=False on the SQLAlchemy
Enum columns that use these) so they work identically on SQLite (local dev)
and PostgreSQL (production) without needing a native DB enum type.
"""
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"


class PersonStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class TermName(str, enum.Enum):
    FIRST = "FIRST"
    SECOND = "SECOND"
    THIRD = "THIRD"


class AssessmentCategory(str, enum.Enum):
    CA = "CA"
    EXAM = "EXAM"


class ResultStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    LOCKED = "LOCKED"
