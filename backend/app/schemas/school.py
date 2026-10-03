from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.schemas.user import UserRead


class SchoolBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    motto: Optional[str] = None
    website: Optional[str] = None
    principal_name: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class SchoolCreate(SchoolBase):
    pass


class SchoolRead(SchoolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    logo_path: Optional[str] = None
    signature_path: Optional[str] = None
    stamp_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("logo_path")
    def serialize_logo_path(self, value: Optional[str]) -> Optional[str]:
        return "/api/schools/me/logo" if value else None


class SchoolUpdate(BaseModel):
    """
    Fields a SCHOOL_ADMIN may edit on their own school via PATCH /api/schools/me.

    Deliberately a whitelist, not SchoolBase reused with everything
    optional: `id`, `is_active`, and the `*_path` branding fields are
    left out on purpose, so there is no field on this schema a client
    could send to change tenant ownership or flip privileged flags, no
    matter what the request body contains.
    """

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    motto: Optional[str] = None
    website: Optional[str] = None
    principal_name: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None


class SchoolRegistrationRequest(BaseModel):
    """
    Public new-school sign-up. Intentionally has NO `role`, `school_id`,
    `is_active`, or any other privileged field — the backend always
    assigns role=SCHOOL_ADMIN and a freshly created school_id itself (see
    app/services/school_service.py). There is nothing here for a client
    to override even if it tried.
    """

    school_name: str = Field(min_length=1, max_length=200)
    school_email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    admin_email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SchoolRegistrationResponse(BaseModel):
    message: str
    school: SchoolRead
    admin: UserRead
