"""
School endpoints.

Only what Phase 4 needs to establish and prove tenant isolation. Full
school-management CRUD (editing a profile, logo upload, branding, etc.)
is Phase 5.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.tenancy import ensure_same_school, get_current_school
from app.models.school import School
from app.models.user import User
from app.schemas.school import SchoolRead

router = APIRouter(prefix="/api/schools", tags=["schools"])


@router.get("/me", response_model=SchoolRead)
def get_my_school(school: School = Depends(get_current_school)) -> School:
    """
    Returns the authenticated user's own school. Only for school-bound
    accounts (SCHOOL_ADMIN/TEACHER/STUDENT) — a SUPER_ADMIN has no single
    "home" school and gets 403 here (see get_current_school).
    """
    return school


@router.get("/{school_id}", response_model=SchoolRead)
def get_school_by_id(
    school_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> School:
    """
    Fetches a school by ID.

    - SUPER_ADMIN may fetch any school — this is the "explicitly
      authorized Super Admin functionality" the spec calls for.
    - SCHOOL_ADMIN/TEACHER/STUDENT may only fetch their OWN school by ID.
      Asking for any other school's ID returns 404, identical to asking
      for an ID that doesn't exist — proving (and testing) that changing
      the URL cannot be used to reach, or even confirm the existence of,
      another tenant's data.
    """
    ensure_same_school(current_user, school_id)

    school = db.get(School, school_id)
    if school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return school
