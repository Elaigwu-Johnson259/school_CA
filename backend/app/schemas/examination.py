from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.examination import (
    ExaminationFileType, ExaminationStatus, QuestionType, ReferenceMaterialType,
    ReviewStatus, ScriptStatus,
)


class ExaminationBase(BaseModel):
    academic_session_id: int
    term_id: int
    school_class_id: int
    subject_id: int
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    examination_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(default=None, gt=0)
    maximum_score: float = Field(gt=0)
    status: ExaminationStatus = ExaminationStatus.DRAFT


class ExaminationCreate(ExaminationBase):
    pass


class ExaminationUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    instructions: Optional[str] = None
    examination_date: Optional[date] = None
    duration_minutes: Optional[int] = Field(default=None, gt=0)
    maximum_score: Optional[float] = Field(default=None, gt=0)
    status: Optional[ExaminationStatus] = None


class ExaminationRead(ExaminationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime


class QuestionBase(BaseModel):
    question_number: str = Field(min_length=1, max_length=30)
    section: Optional[str] = Field(default=None, max_length=100)
    question_text: str = Field(min_length=1)
    question_type: QuestionType
    maximum_marks: float = Field(gt=0)
    display_order: int = Field(ge=0)
    instructions: Optional[str] = None
    correct_option: Optional[str] = Field(default=None, max_length=50)
    expected_concepts: Optional[str] = None
    key_points: Optional[str] = None
    acceptable_alternatives: Optional[str] = None
    partial_credit_guidance: Optional[str] = None
    marking_guidance: Optional[str] = None
    teacher_notes: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_number: Optional[str] = Field(default=None, min_length=1, max_length=30)
    section: Optional[str] = Field(default=None, max_length=100)
    question_text: Optional[str] = Field(default=None, min_length=1)
    question_type: Optional[QuestionType] = None
    maximum_marks: Optional[float] = Field(default=None, gt=0)
    display_order: Optional[int] = Field(default=None, ge=0)
    instructions: Optional[str] = None
    correct_option: Optional[str] = Field(default=None, max_length=50)
    expected_concepts: Optional[str] = None
    key_points: Optional[str] = None
    acceptable_alternatives: Optional[str] = None
    partial_credit_guidance: Optional[str] = None
    marking_guidance: Optional[str] = None
    teacher_notes: Optional[str] = None


class QuestionRead(QuestionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    examination_id: int
    created_at: datetime
    updated_at: datetime


class ReferenceMaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_id: int
    material_type: ReferenceMaterialType
    title: Optional[str] = None
    text_content: Optional[str] = None
    original_file_path: Optional[str] = None
    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


class ReferenceMaterialCreate(BaseModel):
    material_type: ReferenceMaterialType
    title: Optional[str] = Field(default=None, max_length=200)
    text_content: Optional[str] = None
    notes: Optional[str] = None


class ExaminationFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    examination_id: int
    file_type: ExaminationFileType
    original_file_path: str
    original_filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    title: Optional[str] = None
    created_at: datetime


class ScriptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    school_id: int
    examination_id: int
    student_id: int
    original_file_path: str
    original_filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    status: ScriptStatus
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class StudentAnswerCreate(BaseModel):
    question_id: int
    extracted_text: Optional[str] = None
    original_answer_image_path: Optional[str] = None
    page_number: Optional[int] = Field(default=None, ge=1)
    answer_position: Optional[str] = Field(default=None, max_length=100)
    extraction_status: Optional[str] = Field(default=None, max_length=30)


class StudentAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    script_id: int
    question_id: int
    extracted_text: Optional[str] = None
    original_answer_image_path: Optional[str] = None
    page_number: Optional[int] = None
    answer_position: Optional[str] = None
    extraction_status: Optional[str] = None
    ai_proposed_score: Optional[float] = None
    ai_evidence: Optional[str] = None
    ai_confidence: Optional[float] = None
    teacher_final_score: Optional[float] = None
    teacher_adjustment: Optional[float] = None
    teacher_review_notes: Optional[str] = None
    review_status: ReviewStatus
    created_at: datetime
    updated_at: datetime


class MarkReviewUpdate(BaseModel):
    teacher_final_score: float = Field(ge=0)
    teacher_review_notes: Optional[str] = None
    review_status: ReviewStatus = ReviewStatus.REVIEWED


class ApproveScriptRequest(BaseModel):
    confirm: bool = True
