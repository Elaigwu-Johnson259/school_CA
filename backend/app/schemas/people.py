from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import Gender, PersonStatus


class TeacherBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    employee_id: Optional[str] = None


class TeacherCreate(TeacherBase):
    pass


class TeacherRead(TeacherBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    status: PersonStatus


class StudentBase(BaseModel):
    admission_number: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    admission_number: Optional[str] = None
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    address: Optional[str] = None


class StudentRead(StudentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    status: PersonStatus

class TeacherAssignmentCreate(BaseModel):
    teacher_id: int
    school_class_id: int
    subject_id: int


class TeacherAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    school_class_id: int
    subject_id: int

class StudentEnrollmentCreate(BaseModel):
    student_id: int
    school_class_id: int
    academic_session_id: int


class StudentEnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    school_class_id: int
    academic_session_id: int
