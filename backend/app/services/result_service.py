from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tenancy import ensure_same_school
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import SchoolClass, Subject
from app.models.assessment import Score, GradingScale
from app.models.enums import AssessmentCategory, UserRole
from app.models.people import Student, StudentClass, TeacherAssignment
from app.models.result import ReportCard, Result
from app.models.user import User
from app.services.assessment_service import get_teacher_for_user


def _student_class(db: Session, student_id: int, term: Term) -> StudentClass:
    enrollment = db.query(StudentClass).filter(
        StudentClass.student_id == student_id,
        StudentClass.academic_session_id == term.academic_session_id,
    ).first()
    if enrollment is None:
        raise HTTPException(status_code=400, detail="Student is not enrolled for this academic session")
    return enrollment


def _authorize_result_access(db: Session, current_user: User, student_id: int, subject_id: int, term_id: int) -> tuple[Student, Term, StudentClass]:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    ensure_same_school(current_user, student.school_id)
    term = db.get(Term, term_id)
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    session = db.get(AcademicSession, term.academic_session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Academic session not found")
    ensure_same_school(current_user, session.school_id)
    enrollment = _student_class(db, student.id, term)
    if current_user.role == UserRole.TEACHER:
        teacher = get_teacher_for_user(db, current_user)
        assignment = db.query(TeacherAssignment).filter(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.school_class_id == enrollment.school_class_id,
            TeacherAssignment.subject_id == subject_id,
        ).first()
        if assignment is None:
            raise HTTPException(status_code=403, detail="You are not assigned to this class and subject")
    elif current_user.role == UserRole.STUDENT:
        if student.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only access your own result")
    return student, term, enrollment


def _grade_for(db: Session, school_id: int, total: float) -> str | None:
    scale = db.query(GradingScale).filter(
        GradingScale.school_id == school_id,
        GradingScale.min_score <= total,
        GradingScale.max_score >= total,
    ).order_by(GradingScale.min_score.desc()).first()
    return scale.grade if scale else None


def _recalculate_subject_positions(db: Session, subject_id: int, term_id: int, school_class_id: int) -> None:
    student_ids = [row[0] for row in db.query(StudentClass.student_id).filter(
        StudentClass.school_class_id == school_class_id,
        StudentClass.academic_session_id == db.get(Term, term_id).academic_session_id,
    ).all()]
    results = db.query(Result).filter(Result.subject_id == subject_id, Result.term_id == term_id, Result.student_id.in_(student_ids)).all() if student_ids else []
    for result in results:
        result.subject_position = 1 + sum(1 for other in results if float(other.total) > float(result.total))


def _recalculate_report_cards(db: Session, school_class_id: int, term: Term) -> None:
    student_ids = [row[0] for row in db.query(StudentClass.student_id).filter(
        StudentClass.school_class_id == school_class_id,
        StudentClass.academic_session_id == term.academic_session_id,
    ).all()]
    if not student_ids:
        return
    results_by_student: dict[int, list[Result]] = {sid: [] for sid in student_ids}
    for result in db.query(Result).filter(Result.term_id == term.id, Result.student_id.in_(student_ids)).all():
        results_by_student[result.student_id].append(result)

    totals = {sid: sum(float(r.total) for r in rows) for sid, rows in results_by_student.items()}
    for sid, rows in results_by_student.items():
        count = len(rows)
        total = totals[sid]
        average = total / count if count else 0
        report = db.query(ReportCard).filter(ReportCard.student_id == sid, ReportCard.term_id == term.id).first()
        if report is None:
            report = ReportCard(student_id=sid, term_id=term.id)
            db.add(report)
        report.total_marks = total
        report.average = average
        report.overall_grade = _grade_for(db, db.get(Student, sid).school_id, average) if count else None
        report.class_position = 1 + sum(1 for other_sid, other_total in totals.items() if other_sid != sid and other_total > total) if count else None
        report.number_of_students = len(student_ids)
    db.flush()


def calculate_result(db: Session, current_user: User, student_id: int, subject_id: int, term_id: int) -> Result:
    if current_user.role not in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Not authorized")
    student, term, enrollment = _authorize_result_access(db, current_user, student_id, subject_id, term_id)
    scores = db.query(Score).filter(
        Score.student_id == student_id, Score.subject_id == subject_id, Score.term_id == term_id,
    ).all()
    if not scores:
        raise HTTPException(status_code=404, detail="No scores found")
    ca_total = sum(float(score.value) for score in scores if score.assessment_type.category == AssessmentCategory.CA)
    exam_score = sum(float(score.value) for score in scores if score.assessment_type.category == AssessmentCategory.EXAM)
    if ca_total > 30:
        raise HTTPException(status_code=400, detail="CA total cannot exceed 30")
    if exam_score > 70:
        raise HTTPException(status_code=400, detail="Exam score cannot exceed 70")
    total = ca_total + exam_score

    result = db.query(Result).filter(
        Result.student_id == student_id, Result.subject_id == subject_id, Result.term_id == term_id,
    ).first()
    if result is None:
        result = Result(student_id=student_id, subject_id=subject_id, term_id=term_id)
        db.add(result)
    result.ca_total = ca_total
    result.exam_score = exam_score
    result.total = total
    result.grade = _grade_for(db, student.school_id, total)
    db.flush()
    _recalculate_subject_positions(db, subject_id, term_id, enrollment.school_class_id)
    _recalculate_report_cards(db, enrollment.school_class_id, term)
    db.commit()
    db.refresh(result)
    return result


def list_results(db: Session, current_user: User, student_id: int | None = None, term_id: int | None = None) -> list[Result]:
    query = db.query(Result).join(Student, Student.id == Result.student_id)
    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student is None:
            raise HTTPException(status_code=403, detail="Student profile is not linked to this account")
        query = query.filter(Result.student_id == student.id)
    else:
        query = query.filter(Student.school_id == current_user.school_id)
        if current_user.role == UserRole.TEACHER:
            teacher = get_teacher_for_user(db, current_user)
            query = query.join(StudentClass, StudentClass.student_id == Result.student_id).join(
                TeacherAssignment,
                (TeacherAssignment.school_class_id == StudentClass.school_class_id)
                & (TeacherAssignment.subject_id == Result.subject_id),
            ).filter(TeacherAssignment.teacher_id == teacher.id).distinct()
    if student_id is not None:
        query = query.filter(Result.student_id == student_id)
    if term_id is not None:
        query = query.filter(Result.term_id == term_id)
    return query.order_by(Result.subject_id).all()


def get_report_card(db: Session, current_user: User, student_id: int, term_id: int) -> ReportCard:
    student = db.get(Student, student_id)
    term = db.get(Term, term_id)
    if student is None or term is None:
        raise HTTPException(status_code=404, detail="Student or term not found")
    ensure_same_school(current_user, student.school_id)
    ensure_same_school(current_user, db.get(AcademicSession, term.academic_session_id).school_id)
    enrollment = _student_class(db, student.id, term)
    if current_user.role == UserRole.STUDENT and student.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only access your own report card")
    if current_user.role == UserRole.TEACHER:
        teacher = get_teacher_for_user(db, current_user)
        if not db.query(TeacherAssignment).filter(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.school_class_id == enrollment.school_class_id,
        ).first():
            raise HTTPException(status_code=403, detail="You are not assigned to this class")
    _recalculate_report_cards(db, enrollment.school_class_id, term)
    db.commit()
    report = db.query(ReportCard).filter(ReportCard.student_id == student_id, ReportCard.term_id == term_id).first()
    if report is None:
        raise HTTPException(status_code=404, detail="Report card not found")
    return report
