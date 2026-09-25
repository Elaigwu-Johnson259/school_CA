"""
Unit tests for the tenancy helpers in app/core/tenancy.py, exercised
directly (no HTTP, no FastAPI dependency injection) against fake User
objects and a real in-memory DB for the query-scoping test.
"""
from types import SimpleNamespace

from fastapi import HTTPException
import pytest

from app.core.tenancy import ensure_same_school, scope_to_school
from app.models.enums import UserRole
from app.models.people import Student
from app.models.school import School


def _fake_user(role: UserRole, school_id):
    return SimpleNamespace(role=role, school_id=school_id)


def test_ensure_same_school_allows_matching_school():
    user = _fake_user(UserRole.SCHOOL_ADMIN, school_id=1)
    ensure_same_school(user, 1)  # should not raise


def test_ensure_same_school_blocks_mismatched_school_with_404():
    user = _fake_user(UserRole.TEACHER, school_id=1)
    with pytest.raises(HTTPException) as exc_info:
        ensure_same_school(user, 2)
    assert exc_info.value.status_code == 404


def test_ensure_same_school_allows_super_admin_across_any_school():
    user = _fake_user(UserRole.SUPER_ADMIN, school_id=None)
    ensure_same_school(user, 1)
    ensure_same_school(user, 999)  # should not raise for either


def test_scope_to_school_filters_to_callers_own_school(db_session):
    school_a = School(name="School A", email="a@example.com")
    school_b = School(name="School B", email="b@example.com")
    db_session.add_all([school_a, school_b])
    db_session.commit()
    db_session.refresh(school_a)
    db_session.refresh(school_b)

    db_session.add_all(
        [
            Student(school_id=school_a.id, admission_number="A-1", first_name="A", last_name="One"),
            Student(school_id=school_b.id, admission_number="B-1", first_name="B", last_name="One"),
        ]
    )
    db_session.commit()

    school_a_admin = _fake_user(UserRole.SCHOOL_ADMIN, school_id=school_a.id)
    results = scope_to_school(db_session.query(Student), Student, school_a_admin).all()

    assert len(results) == 1
    assert results[0].school_id == school_a.id


def test_scope_to_school_returns_everything_for_super_admin(db_session):
    school_a = School(name="School A", email="a@example.com")
    school_b = School(name="School B", email="b@example.com")
    db_session.add_all([school_a, school_b])
    db_session.commit()
    db_session.refresh(school_a)
    db_session.refresh(school_b)

    db_session.add_all(
        [
            Student(school_id=school_a.id, admission_number="A-1", first_name="A", last_name="One"),
            Student(school_id=school_b.id, admission_number="B-1", first_name="B", last_name="One"),
        ]
    )
    db_session.commit()

    super_admin = _fake_user(UserRole.SUPER_ADMIN, school_id=None)
    results = scope_to_school(db_session.query(Student), Student, super_admin).all()

    assert len(results) == 2
