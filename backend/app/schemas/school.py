from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


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
