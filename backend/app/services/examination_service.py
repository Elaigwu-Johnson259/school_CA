from __future__ import annotations

import os
import hashlib
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tenancy import ensure_same_school
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import ClassSubject, SchoolClass, Subject
from app.models.assessment import AssessmentType, Score
from app.models.enums import AssessmentCategory, UserRole
from app.models.examination import (
    Examination, ExaminationFile, ExaminationFileType, ExaminationQuestion,
    ExaminationStatus, QuestionReferenceMaterial, QuestionType, ReferenceMaterialType,
    ReviewStatus, ScriptStatus, StudentExaminationScript, StudentQuestionAnswer,
)
from app.models.people import Student, StudentClass, TeacherAssignment
from app.models.user import User
from app.services.assessment_service import get_teacher_for_user
from app.services import result_service
from app.services.ai_provider import get_ai_provider


def _school_id_for_context(db: Session, current_user: User, session_id: int, class_id: int, subject_id: int, term_id: int) -> int:
    session = db.get(AcademicSession, session_id)
    term = db.get(Term, term_id)
    school_class = db.get(SchoolClass, class_id)
    subject = db.get(Subject, subject_id)
    if not all((session, term, school_class, subject)):
        raise HTTPException(status_code=404, detail="Academic context not found")
    if term.academic_session_id != session.id or school_class.school_id != session.school_id or subject.school_id != session.school_id:
        raise HTTPException(status_code=400, detail="Academic context does not match")
    ensure_same_school(current_user, session.school_id)
    class_subject = db.query(ClassSubject).filter(ClassSubject.school_class_id == class_id, ClassSubject.subject_id == subject_id).first()
    if class_subject is None:
        raise HTTPException(status_code=400, detail="Subject is not linked to this class")
    if current_user.role == UserRole.TEACHER:
        teacher = get_teacher_for_user(db, current_user)
        assignment = db.query(TeacherAssignment).filter(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.school_class_id == class_id,
            TeacherAssignment.subject_id == subject_id,
        ).first()
        if assignment is None:
            raise HTTPException(status_code=403, detail="You are not assigned to this class and subject")
    return session.school_id


def _get_exam(db: Session, current_user: User, exam_id: int) -> Examination:
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Students cannot access examination management")
    exam = db.get(Examination, exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="Examination not found")
    ensure_same_school(current_user, exam.school_id)
    if current_user.role == UserRole.TEACHER:
        _school_id_for_context(db, current_user, exam.academic_session_id, exam.school_class_id, exam.subject_id, exam.term_id)
    return exam


def _save_upload(upload: UploadFile, school_id: int, category: str) -> tuple[str, int, str]:
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    root = Path(settings.LOCAL_STORAGE_PATH) / "schools" / str(school_id) / "examinations" / category
    safe_name = Path(upload.filename or "upload.bin").name
    target = root / f"{uuid.uuid4().hex}_{safe_name}"
    total = 0
    digest = hashlib.sha256()
    try:
        root.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as destination:
            while True:
                chunk = upload.file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit")
                destination.write(chunk)
                digest.update(chunk)
    except HTTPException:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    except OSError as exc:
        try:
            target.unlink(missing_ok=True)
        except OSError:
            pass
        raise HTTPException(status_code=503, detail="File storage is unavailable") from exc
    return str(target), total, digest.hexdigest()


def _validate_script_upload(upload: UploadFile) -> None:
    filename = Path(upload.filename or "").name
    extension = Path(filename).suffix.lower()
    allowed = {".pdf", ".jpg", ".jpeg", ".png", ".txt"}
    if extension not in allowed:
        raise HTTPException(status_code=415, detail="Upload a PDF, JPG, JPEG, PNG, or typed TXT student script")
    content_type = (upload.content_type or "").lower()
    expected_types = {
        ".pdf": {"application/pdf", "application/octet-stream"},
        ".jpg": {"image/jpeg", "application/octet-stream"},
        ".jpeg": {"image/jpeg", "application/octet-stream"},
        ".png": {"image/png", "application/octet-stream"},
        ".txt": {"text/plain"},
    }
    if content_type not in expected_types[extension]:
        raise HTTPException(status_code=415, detail="File type does not match its filename")
    signature = upload.file.read(8)
    upload.file.seek(0)
    valid_signature = (
        extension == ".pdf" and signature.startswith(b"%PDF-")
        or extension in {".jpg", ".jpeg"} and signature.startswith(b"\xff\xd8\xff")
        or extension == ".png" and signature.startswith(b"\x89PNG\r\n\x1a\n")
        or extension == ".txt" and bool(signature.strip())
    )
    if not valid_signature:
        raise HTTPException(status_code=415, detail="Uploaded file content is not a valid supported document")


def create_examination(db: Session, current_user: User, payload) -> Examination:
    if current_user.role not in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Not authorized")
    school_id = _school_id_for_context(db, current_user, payload.academic_session_id, payload.school_class_id, payload.subject_id, payload.term_id)
    exam = Examination(school_id=school_id, created_by_id=current_user.id, **payload.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def list_examinations(db: Session, current_user: User) -> list[Examination]:
    if current_user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Students cannot access examination management")
    query = db.query(Examination)
    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(Examination.school_id == current_user.school_id)
    if current_user.role == UserRole.TEACHER:
        teacher = get_teacher_for_user(db, current_user)
        query = query.filter(Examination.id.in_(db.query(Examination.id).join(
            TeacherAssignment,
            (TeacherAssignment.school_class_id == Examination.school_class_id) & (TeacherAssignment.subject_id == Examination.subject_id)
        ).filter(TeacherAssignment.teacher_id == teacher.id)))
    return query.order_by(Examination.created_at.desc()).all()


def update_examination(db: Session, current_user: User, exam_id: int, payload) -> Examination:
    exam = _get_exam(db, current_user, exam_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(exam, key, value)
    db.commit()
    db.refresh(exam)
    return exam


def create_question(db: Session, current_user: User, exam_id: int, payload) -> ExaminationQuestion:
    exam = _get_exam(db, current_user, exam_id)
    if exam.status == ExaminationStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Closed examinations cannot be changed")
    if payload.question_type == QuestionType.OBJECTIVE and not payload.correct_option:
        raise HTTPException(status_code=400, detail="Objective questions require a correct option")
    question = ExaminationQuestion(examination_id=exam.id, **payload.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def get_question(db: Session, current_user: User, question_id: int) -> ExaminationQuestion:
    question = db.get(ExaminationQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")
    _get_exam(db, current_user, question.examination_id)
    return question


def list_questions(db: Session, current_user: User, exam_id: int) -> list[ExaminationQuestion]:
    _get_exam(db, current_user, exam_id)
    return db.query(ExaminationQuestion).filter(ExaminationQuestion.examination_id == exam_id).order_by(ExaminationQuestion.display_order, ExaminationQuestion.id).all()


def update_question(db: Session, current_user: User, question_id: int, payload) -> ExaminationQuestion:
    question = get_question(db, current_user, question_id)
    if question.examination.status == ExaminationStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Closed examinations cannot be changed")
    values = payload.model_dump(exclude_unset=True)
    if values.get("question_type") == QuestionType.OBJECTIVE and not values.get("correct_option", question.correct_option):
        raise HTTPException(status_code=400, detail="Objective questions require a correct option")
    for key, value in values.items():
        setattr(question, key, value)
    db.commit()
    db.refresh(question)
    return question


def create_text_reference(db: Session, current_user: User, question_id: int, payload) -> QuestionReferenceMaterial:
    question = get_question(db, current_user, question_id)
    material = QuestionReferenceMaterial(question_id=question.id, **payload.model_dump())
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def upload_reference(db: Session, current_user: User, question_id: int, upload: UploadFile, material_type: ReferenceMaterialType, title: str | None, notes: str | None) -> QuestionReferenceMaterial:
    question = get_question(db, current_user, question_id)
    path, size, _ = _save_upload(upload, question.examination.school_id, "references")
    material = QuestionReferenceMaterial(
        question_id=question.id, material_type=material_type, title=title, notes=notes,
        original_file_path=path, original_filename=Path(upload.filename or "upload.bin").name,
        content_type=upload.content_type, file_size=size,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


def upload_question_paper(db: Session, current_user: User, exam_id: int, upload: UploadFile, title: str | None) -> ExaminationFile:
    exam = _get_exam(db, current_user, exam_id)
    path, size, _ = _save_upload(upload, exam.school_id, "question-papers")
    item = ExaminationFile(examination_id=exam.id, file_type=ExaminationFileType.QUESTION_PAPER,
        original_file_path=path, original_filename=Path(upload.filename or "question-paper").name,
        content_type=upload.content_type, file_size=size, title=title)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_references(db: Session, current_user: User, question_id: int) -> list[QuestionReferenceMaterial]:
    question = get_question(db, current_user, question_id)
    return db.query(QuestionReferenceMaterial).filter(QuestionReferenceMaterial.question_id == question.id).order_by(QuestionReferenceMaterial.id).all()


def get_reference_file(db: Session, current_user: User, reference_id: int) -> QuestionReferenceMaterial:
    material = db.get(QuestionReferenceMaterial, reference_id)
    if material is None:
        raise HTTPException(status_code=404, detail="Reference material not found")
    get_question(db, current_user, material.question_id)
    if not material.original_file_path or not Path(material.original_file_path).is_file():
        raise HTTPException(status_code=404, detail="Reference file is unavailable")
    return material


def _resolve_script_assessment_type(db: Session, current_user: User, exam: Examination, assessment_type_id: int | None = None) -> AssessmentType:
    if assessment_type_id is not None:
        assessment_type = db.get(AssessmentType, assessment_type_id)
        if assessment_type is None:
            raise HTTPException(status_code=404, detail="Assessment type not found")
        ensure_same_school(current_user, assessment_type.school_id)
        if assessment_type.school_id != exam.school_id:
            raise HTTPException(status_code=404, detail="Assessment type not found")
        if assessment_type.category not in {AssessmentCategory.CA, AssessmentCategory.EXAM}:
            raise HTTPException(status_code=400, detail="Only CA or Exam assessment types are supported for AI marking")
        return assessment_type

    raise HTTPException(status_code=400, detail="Select an assessment type before uploading a script")


def upload_script(db: Session, current_user: User, exam_id: int, student_id: int, upload: UploadFile, assessment_type_id: int) -> StudentExaminationScript:
    exam = _get_exam(db, current_user, exam_id)
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    ensure_same_school(current_user, student.school_id)
    if student.school_id != exam.school_id:
        raise HTTPException(status_code=404, detail="Student not found")
    enrollment = db.query(StudentClass).filter(StudentClass.student_id == student.id, StudentClass.school_class_id == exam.school_class_id, StudentClass.academic_session_id == exam.academic_session_id).first()
    if enrollment is None:
        raise HTTPException(status_code=400, detail="Student is not enrolled in the examination class for this session")
    existing = db.query(StudentExaminationScript).filter(
        StudentExaminationScript.examination_id == exam.id,
        StudentExaminationScript.student_id == student.id,
        StudentExaminationScript.assessment_type_id == assessment_type_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="A script already exists for this student and examination")
    assessment_type = _resolve_script_assessment_type(db, current_user, exam, assessment_type_id)
    _validate_script_upload(upload)
    path, size, checksum = _save_upload(upload, exam.school_id, "student-scripts")
    script = StudentExaminationScript(school_id=exam.school_id, examination_id=exam.id, student_id=student.id,
        assessment_type_id=assessment_type.id,
        original_file_path=path, original_filename=Path(upload.filename or "script").name,
        content_type=upload.content_type, file_size=size, checksum_sha256=checksum)
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


def list_scripts(db: Session, current_user: User, exam_id: int) -> list[StudentExaminationScript]:
    exam = _get_exam(db, current_user, exam_id)
    return db.query(StudentExaminationScript).filter(StudentExaminationScript.examination_id == exam.id).order_by(StudentExaminationScript.id).all()


def get_script_file(db: Session, current_user: User, script_id: int) -> StudentExaminationScript:
    script = db.get(StudentExaminationScript, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Student script not found")
    _get_exam(db, current_user, script.examination_id)
    if not Path(script.original_file_path).is_file():
        raise HTTPException(status_code=404, detail="Stored script file is unavailable")
    return script


def add_answer(db: Session, current_user: User, script_id: int, payload) -> StudentQuestionAnswer:
    script = db.get(StudentExaminationScript, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Student script not found")
    _get_exam(db, current_user, script.examination_id)
    question = db.get(ExaminationQuestion, payload.question_id)
    if question is None or question.examination_id != script.examination_id:
        raise HTTPException(status_code=400, detail="Question does not belong to this examination")
    if db.query(StudentQuestionAnswer).filter(StudentQuestionAnswer.script_id == script.id, StudentQuestionAnswer.question_id == question.id).first():
        raise HTTPException(status_code=409, detail="Answer already exists for this question")
    answer = StudentQuestionAnswer(script_id=script.id, **payload.model_dump())
    db.add(answer)
    db.commit()
    db.refresh(answer)
    return answer


def list_answers(db: Session, current_user: User, script_id: int) -> list[StudentQuestionAnswer]:
    script = db.get(StudentExaminationScript, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Student script not found")
    _get_exam(db, current_user, script.examination_id)
    return db.query(StudentQuestionAnswer).filter(StudentQuestionAnswer.script_id == script.id).order_by(StudentQuestionAnswer.question_id).all()


def update_mark(db: Session, current_user: User, answer_id: int, payload) -> StudentQuestionAnswer:
    answer = db.get(StudentQuestionAnswer, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="Student answer not found")
    _get_exam(db, current_user, answer.script.examination_id)
    if answer.script.status == ScriptStatus.APPROVED:
        raise HTTPException(status_code=409, detail="Approved script answers cannot be changed")
    if payload.review_status == ReviewStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Only script approval can mark an answer approved")
    if not math.isfinite(payload.teacher_final_score) or payload.teacher_final_score > float(answer.question.maximum_marks):
        raise HTTPException(status_code=400, detail="Teacher score cannot exceed question maximum marks")
    answer.teacher_final_score = payload.teacher_final_score
    answer.teacher_adjustment = payload.teacher_final_score - float(answer.ai_proposed_score) if answer.ai_proposed_score is not None else None
    answer.teacher_review_notes = payload.teacher_review_notes
    if payload.extracted_text is not None:
        answer.extracted_text = payload.extracted_text
    answer.review_status = payload.review_status
    answer.script.status = ScriptStatus.TEACHER_REVIEW
    db.commit()
    db.refresh(answer)
    return answer


def process_ai_marking(db: Session, current_user: User, script_id: int, assessment_type_id: int | None = None) -> StudentExaminationScript:
    from app.services.ai_marking_service import process_ai_marking as service_marking

    return service_marking(db, current_user, script_id, assessment_type_id=assessment_type_id)


def approve_script(db: Session, current_user: User, script_id: int, assessment_type_id: int | None = None) -> StudentExaminationScript:
    script = db.query(StudentExaminationScript).filter(
        StudentExaminationScript.id == script_id
    ).with_for_update().first()
    if script is None:
        raise HTTPException(status_code=404, detail="Student script not found")
    exam = _get_exam(db, current_user, script.examination_id)
    if script.status == ScriptStatus.APPROVED:
        if assessment_type_id is not None and assessment_type_id != script.assessment_type_id:
            raise HTTPException(status_code=409, detail="Approved script assessment type cannot be changed")
        return script
    if script.status not in {ScriptStatus.AI_MARKED, ScriptStatus.TEACHER_REVIEW}:
        raise HTTPException(status_code=409, detail="Script must be AI-marked before approval")
    assessment_type_id = assessment_type_id or script.assessment_type_id
    if assessment_type_id is None or script.assessment_type_id != assessment_type_id:
        raise HTTPException(status_code=400, detail="Approval assessment type must match the uploaded script")
    assessment_type = _resolve_script_assessment_type(db, current_user, exam, assessment_type_id)
    answers = db.query(StudentQuestionAnswer).filter(StudentQuestionAnswer.script_id == script.id).all()
    questions = db.query(ExaminationQuestion).filter(ExaminationQuestion.examination_id == exam.id).all()
    by_q = {answer.question_id: answer for answer in answers}
    if not questions or any(question.id not in by_q for question in questions):
        raise HTTPException(status_code=400, detail="Every examination question must have a reviewed answer before approval")
    if any(by_q[q.id].teacher_final_score is None for q in questions):
        raise HTTPException(status_code=400, detail="Every question must have a teacher-approved score before approval")
    if any(by_q[q.id].review_status != ReviewStatus.REVIEWED for q in questions):
        raise HTTPException(status_code=400, detail="Every question must be explicitly reviewed before approval")
    approved_total = sum(float(by_q[q.id].teacher_final_score) for q in questions)
    if approved_total > float(assessment_type.max_score):
        raise HTTPException(status_code=400, detail=f"Approved marks exceed the {assessment_type.name} maximum score")
    if exam.maximum_score and float(exam.maximum_score) != float(assessment_type.max_score):
        if assessment_type.category == AssessmentCategory.EXAM:
            raise HTTPException(status_code=400, detail="Examination maximum score must match the school's EXAM assessment maximum")

    existing = db.query(Score).filter(
        Score.student_id == script.student_id, Score.subject_id == exam.subject_id,
        Score.term_id == exam.term_id, Score.assessment_type_id == assessment_type.id,
    ).first()
    if existing:
        existing.value = approved_total
        existing.recorded_by_id = current_user.id
    else:
        db.add(Score(student_id=script.student_id, subject_id=exam.subject_id, school_class_id=exam.school_class_id,
                     term_id=exam.term_id, assessment_type_id=assessment_type.id, recorded_by_id=current_user.id, value=approved_total))
    script.assessment_type_id = assessment_type.id
    script.status = ScriptStatus.APPROVED
    script.approved_at = datetime.now(timezone.utc)
    script.approved_by_id = current_user.id
    for answer in answers:
        answer.review_status = ReviewStatus.APPROVED
    db.commit()
    result_service.calculate_result(db, current_user, script.student_id, exam.subject_id, exam.term_id)
    db.refresh(script)
    return script
