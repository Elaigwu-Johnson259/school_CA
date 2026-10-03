from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import AssessmentCategory


class AssessmentTypeBase(BaseModel):
    name: str
    category: AssessmentCategory
    max_score: float = Field(gt=0, allow_inf_nan=False)
    display_order: int = 0

class AssessmentTypeCreate(AssessmentTypeBase):
    pass

class AssessmentTypeRead(AssessmentTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int

class AssessmentTypeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[AssessmentCategory] = None
    max_score: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)
    display_order: Optional[int] = None

class ScoreCreate(BaseModel):
    student_id: int
    subject_id: int
    school_class_id: int
    term_id: int
    assessment_type_id: int
    value: float = Field(ge=0, allow_inf_nan=False)

class ScoreUpdate(BaseModel):
    value: float = Field(ge=0, allow_inf_nan=False)

class ScoreRead(ScoreCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class ResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    subject_id: int
    term_id: int
    ca_total: float
    exam_score: float
    total: float
    grade: Optional[str] = None
    subject_position: Optional[int] = None

class ReportCardRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    term_id: int
    total_marks: float
    average: float
    overall_grade: Optional[str] = None
    class_position: Optional[int] = None
    number_of_students: Optional[int] = None
    school_days: Optional[int] = None
    days_present: Optional[int] = None
    days_absent: Optional[int] = None
    class_teacher_remark: Optional[str] = None
    principal_remark: Optional[str] = None
    status: str
