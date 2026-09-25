"""
Tenant-scoping helpers.

The one rule everything here enforces: tenant identity comes from the
authenticated User object loaded from the database in Phase 3's
get_current_user() (current_user.school_id) — never from a client-supplied
ID in the URL, a query parameter, or a request body field. A JWT's own
school_id/role claims are convenience/debugging data only; they are never
used for an authorization decision here, since get_current_user() already
re-loads the user fresh from the DB on every request (so a school change,
role change, or deactivation takes effect immediately, not just after the
token expires).

These are meant to be reused by every future tenant-owned resource
(teachers, students, classes, subjects, assessments, scores, results,
report cards) rather than having each endpoint hand-roll its own school_id
check.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Query, Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.school import School
from app.models.user import User


def require_school_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Ensures the caller belongs to a school, i.e. is NOT a SUPER_ADMIN.
    Use this (instead of get_current_user directly) on any endpoint that
    only makes sense for a school-bound account.
    """
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a school-bound account",
        )
    return current_user


def get_current_school(
    current_user: User = Depends(require_school_user),
    db: Session = Depends(get_db),
) -> School:
    """
    Resolves the logged-in user's own school (their "tenant"). Only usable
    by school-bound roles — SUPER_ADMIN is rejected by require_school_user
    above before this ever runs, since a SUPER_ADMIN has no single "home"
    school by design. SUPER_ADMIN cross-school access goes through
    ensure_same_school()/scope_to_school() below instead, explicitly and
    per-endpoint.
    """
    school = db.get(School, current_user.school_id)
    if school is None:
        # Shouldn't happen if foreign-key integrity holds, but a user
        # record with a dangling school_id shouldn't 500.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return school


def require_school_role(*roles: UserRole):
    """
    Combines a role check with the "must belong to a school" check, for
    endpoints that only SCHOOL_ADMIN/TEACHER/STUDENT (never SUPER_ADMIN)
    should reach:

        Depends(require_school_role(UserRole.SCHOOL_ADMIN, UserRole.TEACHER))
    """

    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        if current_user.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This action requires a school-bound account",
            )
        return current_user

    return _check


def ensure_same_school(current_user: User, resource_school_id: int) -> None:
    """
    Guards a single resource lookup/mutation. Call this after fetching (or
    before creating/updating) a school-owned resource, passing that
    resource's own school_id:

        student = db.get(Student, student_id)
        if student is None:
            raise HTTPException(status_code=404, detail="Student not found")
        ensure_same_school(current_user, student.school_id)
        return student

    Raises 404 — never 403 — when a school-bound user's school doesn't
    match. Using 404 instead of 403 means a School A user asking for a
    School B resource ID sees the exact same response as asking for an ID
    that doesn't exist at all, so the status code alone can't be used to
    fingerprint another tenant's data.

    SUPER_ADMIN bypasses this check entirely — their cross-tenant access
    is a deliberate, role-gated exception, not an oversight.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return
    if current_user.school_id != resource_school_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


def scope_to_school(query: Query, model, current_user: User) -> Query:
    """
    Applies the tenant filter to a list/search query for a school-owned
    model (one with a school_id column), e.g.:

        students = scope_to_school(db.query(Student), Student, current_user).all()

    SUPER_ADMIN is deliberately NOT auto-scoped here — an unscoped
    SUPER_ADMIN query returns every school's rows. If a future SUPER_ADMIN
    endpoint needs to look at one specific school's list, filter
    explicitly by that school's id at the call site instead of relying on
    this helper to guess.

    Where a resource doesn't carry its own school_id column (e.g. a Score
    is scoped through its Student), don't force one on just for this
    pattern — join to the owning table and filter on that instead.
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        return query
    return query.filter(model.school_id == current_user.school_id)
