from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.examination import ReferenceMaterialType
from app.models.user import User
from app.schemas.examination import (
    ApproveScriptRequest, ExaminationCreate, ExaminationFileRead, ExaminationRead, ExaminationUpdate,
    MarkReviewUpdate, QuestionCreate, QuestionRead, QuestionUpdate,
    ReferenceMaterialCreate, ReferenceMaterialRead, ScriptRead, StudentAnswerCreate, StudentAnswerRead,
)
from app.services import examination_service

router = APIRouter(prefix="/api/academic", tags=["examinations"])


@router.post("/examinations", response_model=ExaminationRead, status_code=status.HTTP_201_CREATED)
def create_examination(payload: ExaminationCreate, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    return examination_service.create_examination(db, current_user, payload)


@router.get("/examinations", response_model=list[ExaminationRead])
def list_examinations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return examination_service.list_examinations(db, current_user)


@router.patch("/examinations/{exam_id}", response_model=ExaminationRead)
def update_examination(exam_id: int, payload: ExaminationUpdate, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    return examination_service.update_examination(db, current_user, exam_id, payload)


@router.get("/examinations/{exam_id}/questions", response_model=list[QuestionRead])
def list_questions(exam_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return examination_service.list_questions(db, current_user, exam_id)


@router.post("/examinations/{exam_id}/questions", response_model=QuestionRead, status_code=status.HTTP_201_CREATED)
def create_question(exam_id: int, payload: QuestionCreate, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    return examination_service.create_question(db, current_user, exam_id, payload)


@router.get("/questions/{question_id}", response_model=QuestionRead)
def get_question(question_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return examination_service.get_question(db, current_user, question_id)


@router.patch("/questions/{question_id}", response_model=QuestionRead)
def update_question(question_id: int, payload: QuestionUpdate, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    return examination_service.update_question(db, current_user, question_id, payload)


@router.get("/questions/{question_id}/references", response_model=list[ReferenceMaterialRead])
def list_references(question_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return examination_service.list_references(db, current_user, question_id)


@router.post("/questions/{question_id}/references", response_model=ReferenceMaterialRead, status_code=status.HTTP_201_CREATED)
def create_reference(question_id: int, payload: ReferenceMaterialCreate, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    return examination_service.create_text_reference(db, current_user, question_id, payload)


@router.post("/questions/{question_id}/references/upload", response_model=ReferenceMaterialRead, status_code=status.HTTP_201_CREATED)
def upload_reference(
    question_id: int,
    file: UploadFile = File(...),
    material_type: ReferenceMaterialType = Form(ReferenceMaterialType.UPLOAD),
    title: str | None = Form(None),
    notes: str | None = Form(None),
    current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    return examination_service.upload_reference(db, current_user, question_id, file, material_type, title, notes)


@router.post("/examinations/{exam_id}/question-paper", response_model=ExaminationFileRead, status_code=status.HTTP_201_CREATED)
def upload_question_paper(
    exam_id: int,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    return examination_service.upload_question_paper(db, current_user, exam_id, file, title)


@router.get("/examinations/{exam_id}/scripts", response_model=list[ScriptRead])
def list_scripts(exam_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return examination_service.list_scripts(db, current_user, exam_id)


@router.post("/examinations/{exam_id}/scripts", response_model=ScriptRead, status_code=status.HTTP_201_CREATED)
def upload_script(
    exam_id: int,
    student_id: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    return examination_service.upload_script(db, current_user, exam_id, student_id, file)


@router.get("/scripts/{script_id}/answers", response_model=list[StudentAnswerRead])
def list_answers(script_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return examination_service.list_answers(db, current_user, script_id)


@router.post("/scripts/{script_id}/answers", response_model=StudentAnswerRead, status_code=status.HTTP_201_CREATED)
def add_answer(script_id: int, payload: StudentAnswerCreate, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    return examination_service.add_answer(db, current_user, script_id, payload)


@router.patch("/answers/{answer_id}/review", response_model=StudentAnswerRead)
def review_answer(answer_id: int, payload: MarkReviewUpdate, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    return examination_service.update_mark(db, current_user, answer_id, payload)


@router.post("/scripts/{script_id}/approve", response_model=ScriptRead)
def approve_script(script_id: int, payload: ApproveScriptRequest, current_user: User = Depends(require_roles(UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN)), db: Session = Depends(get_db)):
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Approval confirmation is required")
    return examination_service.approve_script(db, current_user, script_id)
