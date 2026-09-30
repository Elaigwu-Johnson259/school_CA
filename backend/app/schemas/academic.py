from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TermName


class AcademicSessionBase(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    is_current: bool = False


class AcademicSessionCreate(AcademicSessionBase):
    pass


class AcademicSessionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=20)
    is_current: Optional[bool] = None


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


class TermUpdate(BaseModel):
    name: Optional[TermName] = None
    is_current: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class TermRead(TermBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    academic_session_id: int
    created_at: datetime
