from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import TermName


class AcademicSessionBase(BaseModel):
    name: str
    is_current: bool = False


class AcademicSessionCreate(AcademicSessionBase):
    pass


class AcademicSessionRead(AcademicSessionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    created_at: datetime


class TermBase(BaseModel):
    name: TermName
    is_current: bool = False
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TermCreate(TermBase):
    pass


class TermRead(TermBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_session_id: int
