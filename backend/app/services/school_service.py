"""
School-management business logic: public new-school registration and
authenticated school-profile updates. Kept separate from app/api/schools.py
so it can be unit-tested without going through HTTP, matching the pattern
already used by app/services/auth_service.py.
"""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.school import School
from app.models.user import User
from app.schemas.school import SchoolRegistrationRequest


class SchoolEmailAlreadyRegistered(Exception):
    """A school already exists with the requested school_email."""


class AdminEmailAlreadyRegistered(Exception):
    """A user already exists with the requested admin_email."""


class RegistrationConflict(Exception):
    """
    Generic fallback for a uniqueness violation caught only at the
    database level (e.g. a race between two near-simultaneous
    registrations using the same email) — the pre-checks below catch the
    common case, but the DB's own UNIQUE constraints are the real,
    final guarantee, since two requests can both pass the pre-check
    before either commits.
    """


def register_school(db: Session, payload: SchoolRegistrationRequest) -> tuple[School, User]:
    """
    Creates a new School and its first SCHOOL_ADMIN user atomically: both
    inserts happen in one transaction, so if anything fails, neither
    record is left behind.

    Tenant ownership is never taken from the client — school_id for the
    new admin comes from `school.id` right after we insert the school in
    this same function, and role is hard-coded to SCHOOL_ADMIN. There is
    no code path here that lets a request body choose either value.
    """
    # Friendly pre-checks first (nicer error messages than a raw
    # IntegrityError) — the UNIQUE constraints on School.email and
    # User.email are still what actually prevents a race condition
    # between two concurrent registrations; see the except block below.
    if db.query(School).filter(School.email == payload.school_email).first() is not None:
        raise SchoolEmailAlreadyRegistered()
    if db.query(User).filter(User.email == payload.admin_email).first() is not None:
        raise AdminEmailAlreadyRegistered()

    school = School(
        name=payload.school_name,
        email=payload.school_email,
        phone=payload.phone,
        address=payload.address,
        state=payload.state,
        country=payload.country,
    )
    db.add(school)

    try:
        # Flush (not commit) so `school.id` is assigned by the database
        # without ending the transaction — the admin insert below still
        # shares the same transaction, so a failure after this point
        # rolls back the school insert too.
        db.flush()

        admin = User(
            school_id=school.id,
            email=payload.admin_email,
            hashed_password=hash_password(payload.password),
            role=UserRole.SCHOOL_ADMIN,
        )
        db.add(admin)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise RegistrationConflict() from exc

    db.refresh(school)
    db.refresh(admin)
    return school, admin
