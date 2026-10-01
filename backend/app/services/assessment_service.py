from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.assessment import AssessmentType
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import SchoolClass
from app.models.academic_structure import Subject
from app.models.assessment import Score
from app.models.people import Student
from app.models.enums import AssessmentCategory, UserRole
from app.models.user import User
from app.core.tenancy import ensure_same_school


def create_assessment_type(
    db: Session,
    current_user: User,
    name: str,
    category: AssessmentCategory,
    max_score: float,
    display_order: int = 0,
) -> AssessmentType:
    if current_user.role not in {
        UserRole.SCHOOL_ADMIN,
        UserRole.SUPER_ADMIN,
    }:
        raise HTTPException(status_code=403, detail="Not authorized")

    existing = (
        db.query(AssessmentType)
        .filter(
            AssessmentType.school_id == current_user.school_id,
            AssessmentType.name == name,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Assessment type already exists",
        )

    assessment_type = AssessmentType(
        school_id=current_user.school_id,
        name=name,
        category=category,
        max_score=max_score,
        display_order=display_order,
    )

    db.add(assessment_type)
    db.commit()
    db.refresh(assessment_type)

    return assessment_type


def get_assessment_type(
    db: Session,
    current_user: User,
    assessment_type_id: int,
) -> AssessmentType:
    assessment_type = db.get(AssessmentType, assessment_type_id)

    if assessment_type is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment type not found",
        )

    ensure_same_school(current_user, assessment_type.school_id)

    return assessment_type


def list_assessment_types(
    db: Session,
    current_user: User,
) -> list[AssessmentType]:
    return (
        db.query(AssessmentType)
        .filter(AssessmentType.school_id == current_user.school_id)
        .order_by(AssessmentType.display_order, AssessmentType.id)
        .all()
    )

def update_assessment_type(
    db: Session,
    current_user: User,
    assessment_type_id: int,
    name: Optional[str] = None,
    category: Optional[AssessmentCategory] = None,
    max_score: Optional[float] = None,
    display_order: Optional[int] = None,
) -> AssessmentType:
    assessment_type = get_assessment_type(
        db=db,
        current_user=current_user,
        assessment_type_id=assessment_type_id,
    )

    if name is not None and name != assessment_type.name:
        existing = (
            db.query(AssessmentType)
            .filter(
                AssessmentType.school_id == current_user.school_id,
                AssessmentType.name == name,
                AssessmentType.id != assessment_type_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Assessment type already exists",
            )

        assessment_type.name = name

    if category is not None:
        assessment_type.category = category

    if max_score is not None:
        assessment_type.max_score = max_score

    if display_order is not None:
        assessment_type.display_order = display_order

    db.commit()
    db.refresh(assessment_type)

    return assessment_type

def create_score(
    db: Session,
    current_user: User,
    student_id: int,
    subject_id: int,
    school_class_id: int,
    term_id: int,
    assessment_type_id: int,
    value: float,
) -> Score:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    ensure_same_school(current_user, student.school_id)

    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    ensure_same_school(current_user, subject.school_id)

    school_class = db.get(SchoolClass, school_class_id)
    if school_class is None:
        raise HTTPException(status_code=404, detail="Class not found")
    ensure_same_school(current_user, school_class.school_id)

    term = db.get(Term, term_id)
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")

    academic_session = db.get(AcademicSession, term.academic_session_id)
    if academic_session is None:
        raise HTTPException(status_code=404, detail="Academic session not found")
    ensure_same_school(current_user, academic_session.school_id)

    assessment_type = db.get(AssessmentType, assessment_type_id)
    if assessment_type is None:
        raise HTTPException(status_code=404, detail="Assessment type not found")
    ensure_same_school(current_user, assessment_type.school_id)

    if value > float(assessment_type.max_score):
        raise HTTPException(
            status_code=400,
            detail=f"Score cannot exceed maximum of {assessment_type.max_score}",
        )

    existing = (
        db.query(Score)
        .filter(
            Score.student_id == student_id,
            Score.subject_id == subject_id,
            Score.term_id == term_id,
            Score.assessment_type_id == assessment_type_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Score already exists for this student and assessment",
        )

    score = Score(
        student_id=student_id,
        subject_id=subject_id,
        school_class_id=school_class_id,
        term_id=term_id,
        assessment_type_id=assessment_type_id,
        recorded_by_id=current_user.id,
        value=value,
    )

    db.add(score)
    db.commit()
    db.refresh(score)

    return score

def create_score(
    db: Session,
    current_user: User,
    student_id: int,
    subject_id: int,
    school_class_id: int,
    term_id: int,
    assessment_type_id: int,
    value: float,
) -> Score:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    ensure_same_school(current_user, student.school_id)

    subject = db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    ensure_same_school(current_user, subject.school_id)

    school_class = db.get(SchoolClass, school_class_id)
    if school_class is None:
        raise HTTPException(status_code=404, detail="Class not found")
    ensure_same_school(current_user, school_class.school_id)

    term = db.get(Term, term_id)
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")

    academic_session = db.get(AcademicSession, term.academic_session_id)
    if academic_session is None:
        raise HTTPException(status_code=404, detail="Academic session not found")
    ensure_same_school(current_user, academic_session.school_id)

    assessment_type = db.get(AssessmentType, assessment_type_id)
    if assessment_type is None:
        raise HTTPException(status_code=404, detail="Assessment type not found")
    ensure_same_school(current_user, assessment_type.school_id)

    if value > float(assessment_type.max_score):
        raise HTTPException(
            status_code=400,
            detail=f"Score cannot exceed maximum of {assessment_type.max_score}",
        )

    existing = (
        db.query(Score)
        .filter(
            Score.student_id == student_id,
            Score.subject_id == subject_id,
            Score.term_id == term_id,
            Score.assessment_type_id == assessment_type_id,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Score already exists for this student and assessment",
        )

    score = Score(
        student_id=student_id,
        subject_id=subject_id,
        school_class_id=school_class_id,
        term_id=term_id,
        assessment_type_id=assessment_type_id,
        recorded_by_id=current_user.id,
        value=value,
    )

    db.add(score)
    db.commit()
    db.refresh(score)

    return score
