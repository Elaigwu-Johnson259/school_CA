from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tenancy import ensure_same_school
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import ClassSubject, SchoolClass, Subject
from app.models.assessment import AssessmentType, GradingScale, Score
from app.models.enums import AssessmentCategory, UserRole
from app.models.people import Student, StudentClass, Teacher, TeacherAssignment
from app.models.user import User


def _school_assessment_types(db: Session, school_id: int) -> list[AssessmentType]:
    return db.query(AssessmentType).filter(AssessmentType.school_id == school_id).order_by(
        AssessmentType.display_order, AssessmentType.id
    ).all()


def ensure_default_assessment_types(db: Session, school_id: int) -> list[AssessmentType]:
    """Ensure the standard school_CA assessment components exist with 10/10/10/70 maxima."""
    types = _school_assessment_types(db, school_id)
    by_key = {item.name.replace(" ", "").replace("-", "").lower(): item for item in types}
    desired = [
        ("ca1", "CA1", AssessmentCategory.CA, 10, 1),
        ("ca2", "CA2", AssessmentCategory.CA, 10, 2),
        ("ca3", "CA3", AssessmentCategory.CA, 10, 3),
        ("exam", "Exam", AssessmentCategory.EXAM, 70, 4),
    ]
    changed = False
    for key, name, category, maximum, order in desired:
        item = by_key.get(key)
        if item is None:
            db.add(AssessmentType(school_id=school_id, name=name, category=category, max_score=maximum, display_order=order))
            changed = True
        else:
            if item.category != category or float(item.max_score) != maximum or item.display_order != order:
                item.category = category
                item.max_score = maximum
                item.display_order = order
                changed = True
    if not db.query(GradingScale).filter(GradingScale.school_id == school_id).first():
        defaults = [
            ("A+", 90, 100), ("A", 80, 89.99), ("B", 70, 79.99),
            ("C", 60, 69.99), ("D", 50, 59.99), ("E", 40, 49.99), ("F", 0, 39.99),
        ]
        for grade, minimum, maximum in defaults:
            db.add(GradingScale(school_id=school_id, grade=grade, min_score=minimum, max_score=maximum))
        changed = True
    if changed:
        db.commit()
    return _school_assessment_types(db, school_id)


def create_assessment_type(db: Session, current_user: User, name: str, category: AssessmentCategory, max_score: float, display_order: int = 0) -> AssessmentType:
    if current_user.role not in {UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Not authorized")
    if current_user.school_id is None:
        raise HTTPException(status_code=403, detail="School-bound account required")
    if max_score <= 0:
        raise HTTPException(status_code=400, detail="Maximum score must be greater than zero")
    existing = db.query(AssessmentType).filter(
        AssessmentType.school_id == current_user.school_id, AssessmentType.name == name
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Assessment type already exists")
    item = AssessmentType(
        school_id=current_user.school_id, name=name, category=category,
        max_score=max_score, display_order=display_order,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_assessment_type(db: Session, current_user: User, assessment_type_id: int) -> AssessmentType:
    item = db.get(AssessmentType, assessment_type_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Assessment type not found")
    ensure_same_school(current_user, item.school_id)
    return item


def list_assessment_types(db: Session, current_user: User) -> list[AssessmentType]:
    if current_user.school_id is None:
        return db.query(AssessmentType).order_by(AssessmentType.display_order, AssessmentType.id).all()
    return ensure_default_assessment_types(db, current_user.school_id)


def update_assessment_type(db: Session, current_user: User, assessment_type_id: int, name: Optional[str] = None, category: Optional[AssessmentCategory] = None, max_score: Optional[float] = None, display_order: Optional[int] = None) -> AssessmentType:
    if current_user.role not in {UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Not authorized")
    item = get_assessment_type(db, current_user, assessment_type_id)
    if name is not None and name != item.name:
        if db.query(AssessmentType).filter(
            AssessmentType.school_id == item.school_id,
            AssessmentType.name == name,
            AssessmentType.id != item.id,
        ).first():
            raise HTTPException(status_code=409, detail="Assessment type already exists")
        item.name = name
    if category is not None:
        item.category = category
    if max_score is not None:
        if max_score <= 0:
            raise HTTPException(status_code=400, detail="Maximum score must be greater than zero")
        item.max_score = max_score
    if display_order is not None:
        item.display_order = display_order
    db.commit()
    db.refresh(item)
    return item


def get_teacher_for_user(db: Session, current_user: User) -> Teacher:
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if teacher is None or teacher.school_id != current_user.school_id:
        raise HTTPException(status_code=403, detail="Teacher profile is not linked to this account")
    return teacher


def validate_score_context(db: Session, current_user: User, student_id: int, subject_id: int, school_class_id: int, term_id: int, assessment_type_id: int):
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    ensure_same_school(current_user, student.school_id)

    school_class = db.get(SchoolClass, school_class_id)
    if school_class is None:
        raise HTTPException(status_code=404, detail="Class not found")
    ensure_same_school(current_user, school_class.school_id)

    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    ensure_same_school(current_user, subject.school_id)

    term = db.get(Term, term_id)
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")
    session = db.get(AcademicSession, term.academic_session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Academic session not found")
    ensure_same_school(current_user, session.school_id)
    if school_class.school_id != subject.school_id or session.school_id != student.school_id:
        raise HTTPException(status_code=404, detail="Academic context not found")

    enrollment = db.query(StudentClass).filter(
        StudentClass.student_id == student.id,
        StudentClass.school_class_id == school_class.id,
        StudentClass.academic_session_id == session.id,
    ).first()
    if enrollment is None:
        raise HTTPException(status_code=400, detail="Student is not enrolled in this class for the session")

    class_subject = db.query(ClassSubject).filter(
        ClassSubject.school_class_id == school_class.id,
        ClassSubject.subject_id == subject.id,
    ).first()
    if class_subject is None:
        raise HTTPException(status_code=400, detail="Subject is not linked to this class")

    assessment_type = get_assessment_type(db, current_user, assessment_type_id)
    if assessment_type.school_id != student.school_id:
        raise HTTPException(status_code=404, detail="Assessment type not found")

    if current_user.role == UserRole.TEACHER:
        teacher = get_teacher_for_user(db, current_user)
        assignment = db.query(TeacherAssignment).filter(
            TeacherAssignment.teacher_id == teacher.id,
            TeacherAssignment.school_class_id == school_class.id,
            TeacherAssignment.subject_id == subject.id,
        ).first()
        if assignment is None:
            raise HTTPException(status_code=403, detail="You are not assigned to this class and subject")

    return student, school_class, subject, term, assessment_type


def create_score(db: Session, current_user: User, student_id: int, subject_id: int, school_class_id: int, term_id: int, assessment_type_id: int, value: float) -> Score:
    if current_user.role not in {UserRole.TEACHER, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Only teachers can record scores")
    if value < 0:
        raise HTTPException(status_code=400, detail="Score cannot be negative")
    _, _, _, _, assessment_type = validate_score_context(
        db, current_user, student_id, subject_id, school_class_id, term_id, assessment_type_id
    )
    if value > float(assessment_type.max_score):
        raise HTTPException(status_code=400, detail=f"Score cannot exceed maximum of {assessment_type.max_score}")
    existing = db.query(Score).filter(
        Score.student_id == student_id, Score.subject_id == subject_id,
        Score.term_id == term_id, Score.assessment_type_id == assessment_type_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Score already exists for this student and assessment")
    score = Score(
        student_id=student_id, subject_id=subject_id, school_class_id=school_class_id,
        term_id=term_id, assessment_type_id=assessment_type_id,
        recorded_by_id=current_user.id, value=value,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def list_scores(db: Session, current_user: User, student_id: int | None = None, subject_id: int | None = None, term_id: int | None = None, school_class_id: int | None = None) -> list[Score]:
    query = db.query(Score).join(Student, Student.id == Score.student_id)
    if current_user.role == UserRole.STUDENT:
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student is None:
            raise HTTPException(status_code=403, detail="Student profile is not linked to this account")
        query = query.filter(Score.student_id == student.id)
    else:
        ensure_same_school(current_user, current_user.school_id)
        query = query.filter(Student.school_id == current_user.school_id)
        if current_user.role == UserRole.TEACHER:
            teacher = get_teacher_for_user(db, current_user)
            query = query.join(TeacherAssignment, (TeacherAssignment.school_class_id == Score.school_class_id) & (TeacherAssignment.subject_id == Score.subject_id)).filter(TeacherAssignment.teacher_id == teacher.id)
    if student_id is not None:
        query = query.filter(Score.student_id == student_id)
    if subject_id is not None:
        query = query.filter(Score.subject_id == subject_id)
    if term_id is not None:
        query = query.filter(Score.term_id == term_id)
    if school_class_id is not None:
        query = query.filter(Score.school_class_id == school_class_id)
    return query.order_by(Score.student_id, Score.assessment_type_id).all()


def update_score(db: Session, current_user: User, score_id: int, value: float) -> Score:
    if current_user.role not in {UserRole.TEACHER, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Only teachers can update scores")
    score = db.get(Score, score_id)
    if score is None:
        raise HTTPException(status_code=404, detail="Score not found")
    validate_score_context(
        db, current_user, score.student_id, score.subject_id, score.school_class_id,
        score.term_id, score.assessment_type_id,
    )
    if value < 0:
        raise HTTPException(status_code=400, detail="Score cannot be negative")
    if value > float(score.assessment_type.max_score):
        raise HTTPException(status_code=400, detail=f"Score cannot exceed maximum of {score.assessment_type.max_score}")
    score.value = value
    score.recorded_by_id = current_user.id
    db.commit()
    db.refresh(score)
    return score
