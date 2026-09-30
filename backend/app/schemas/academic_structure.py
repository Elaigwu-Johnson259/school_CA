from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SchoolClassBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class SchoolClassCreate(SchoolClassBase):
    pass


class SchoolClassUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)


class SchoolClassRead(SchoolClassBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    created_at: datetime


class SubjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: Optional[str] = Field(default=None, max_length=20)


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    code: Optional[str] = Field(default=None, max_length=20)


class SubjectRead(SubjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    created_at: datetime


class ClassSubjectCreate(BaseModel):
    school_class_id: int
    subject_id: int


class ClassSubjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_class_id: int
    subject_id: int
    created_at: datetime
