from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssessmentCategory


class AssessmentTypeBase(BaseModel):
    name: str
    category: AssessmentCategory
    max_score: float = Field(gt=0)
    display_order: int = 0


class AssessmentTypeCreate(AssessmentTypeBase):
    pass


class AssessmentTypeRead(AssessmentTypeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int


class GradingScaleBase(BaseModel):
    grade: str
    min_score: float
    max_score: float
    remark: Optional[str] = None


class GradingScaleCreate(GradingScaleBase):
    pass


class GradingScaleRead(GradingScaleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int


class ScoreCreate(BaseModel):
    student_id: int
    subject_id: int
    school_class_id: int
    term_id: int
    assessment_type_id: int
    value: float = Field(ge=0)


class ScoreRead(ScoreCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int

class AssessmentTypeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[AssessmentCategory] = None
    max_score: Optional[float] = Field(default=None, gt=0)
    display_order: Optional[int] = None

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
