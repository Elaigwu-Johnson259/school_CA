"""
School endpoints.

Public new-school registration + authenticated school profile
read/update (Phase 5), plus the tenant-isolation-proving endpoints from
Phase 4. Full school management (logo upload, branding assets) beyond
text fields is a documented, deliberately deferred next step — see the
README's Phase 5 section.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.config import settings
from app.core.tenancy import ensure_same_school, get_current_school, require_school_role
from app.models.enums import UserRole
from app.models.school import School
from app.models.user import User
from app.schemas.school import (
    SchoolRead,
    SchoolRegistrationRequest,
    SchoolRegistrationResponse,
    SchoolUpdate,
)
from app.schemas.user import UserRead
from app.services import school_service

router = APIRouter(prefix="/api/schools", tags=["schools"])


@router.post("/register", response_model=SchoolRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_school(payload: SchoolRegistrationRequest, db: Session = Depends(get_db)) -> SchoolRegistrationResponse:
    """
    Public endpoint: creates a brand-new School plus its first
    SCHOOL_ADMIN, atomically. No authentication is required (the school
    doesn't have an account yet) — but that's exactly why this endpoint
    hard-codes role=SCHOOL_ADMIN and derives school_id from the school it
    just created, rather than trusting anything from the request body.

    Deliberately does NOT log the new admin in automatically — the
    response contains no tokens. The intended flow is: register → show a
    success message → redirect to /login → the admin signs in normally
    through the existing Phase 3 flow.
    """
    try:
        school, admin = school_service.register_school(db, payload)
    except school_service.SchoolEmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A school is already registered with this email",
        )
    except school_service.AdminEmailAlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists with this email",
        )
    except school_service.RegistrationConflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration could not be completed — please try again",
        )

    return SchoolRegistrationResponse(
        message="Your school account has been created successfully.",
        school=SchoolRead.model_validate(school),
        admin=UserRead.model_validate(admin),
    )


@router.get("/me", response_model=SchoolRead)
def get_my_school(school: School = Depends(get_current_school)) -> School:
    """
    Returns the authenticated user's own school. Only for school-bound
    accounts (SCHOOL_ADMIN/TEACHER/STUDENT) — a SUPER_ADMIN has no single
    "home" school and gets 403 here (see get_current_school).
    """
    return school


@router.get("/me/logo")
def get_my_school_logo(school: School = Depends(get_current_school)):
    if not school.logo_path or not Path(school.logo_path).is_file():
        raise HTTPException(status_code=404, detail="School logo not found")
    extension = Path(school.logo_path).suffix.lower()
    media_type = "image/png" if extension == ".png" else "image/jpeg"
    return FileResponse(school.logo_path, media_type=media_type)


@router.post("/me/logo", response_model=SchoolRead)
def upload_my_school_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(require_school_role(UserRole.SCHOOL_ADMIN)),
    db: Session = Depends(get_db),
):
    extension_by_type = {"image/png": ".png", "image/jpeg": ".jpg"}
    extension = extension_by_type.get((file.content_type or "").lower())
    if extension is None:
        raise HTTPException(status_code=415, detail="School logo must be a PNG or JPEG image")
    content = file.file.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit")
    valid = content.startswith(b"\x89PNG\r\n\x1a\n") if extension == ".png" else content.startswith(b"\xff\xd8\xff")
    if not valid:
        raise HTTPException(status_code=415, detail="Uploaded file content is not a valid PNG or JPEG")
    school = db.get(School, current_user.school_id)
    if school is None:
        raise HTTPException(status_code=404, detail="School not found")
    logo_directory = Path(settings.LOCAL_STORAGE_PATH) / "schools" / str(school.id) / "branding"
    target = logo_directory / f"{uuid.uuid4().hex}{extension}"
    try:
        logo_directory.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    except OSError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail="File storage is unavailable") from exc
    school.logo_path = str(target)
    db.commit()
    db.refresh(school)
    return school


@router.patch("/me", response_model=SchoolRead)
def update_my_school(
    payload: SchoolUpdate,
    current_user: User = Depends(require_school_role(UserRole.SCHOOL_ADMIN)),
    db: Session = Depends(get_db),
) -> School:
    """
    Updates the authenticated SCHOOL_ADMIN's own school profile.

    - Only SCHOOL_ADMIN may call this — require_school_role rejects
      TEACHER/STUDENT (403, wrong role) and SUPER_ADMIN (403, not
      school-bound) before this function body ever runs.
    - The school being updated is always `current_user.school_id` — there
      is no school_id in the request, so a SCHOOL_ADMIN has no way to
      even attempt to target a different school.
    - `SchoolUpdate` is a whitelist of editable text/branding fields; it
      has no `id`, `is_active`, or `*_path` field, so `.model_dump()`
      cannot produce keys that would let a client touch those through
      mass assignment.
    """
    school = db.get(School, current_user.school_id)
    if school is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(school, field, value)

    db.commit()
    db.refresh(school)
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
