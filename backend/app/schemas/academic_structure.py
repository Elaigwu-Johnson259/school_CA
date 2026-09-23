from typing import Optional

from pydantic import BaseModel, ConfigDict


class SchoolClassBase(BaseModel):
    name: str


class SchoolClassCreate(SchoolClassBase):
    pass


class SchoolClassRead(SchoolClassBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int


class SubjectBase(BaseModel):
    name: str
    code: Optional[str] = None


class SubjectCreate(SubjectBase):
    pass


class SubjectRead(SubjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
