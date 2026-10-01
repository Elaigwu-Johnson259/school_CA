from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.tenancy import ensure_same_school
from app.models.assessment import Score
from app.models.enums import AssessmentCategory, UserRole
from app.models.people import Student
from app.models.result import Result
from app.models.user import User


def calculate_result(
    db: Session,
    current_user: User,
    student_id: int,
    subject_id: int,
    term_id: int,
) -> Result:
    if current_user.role not in {
        UserRole.SCHOOL_ADMIN,
        UserRole.TEACHER,
        UserRole.SUPER_ADMIN,
    }:
        raise HTTPException(status_code=403, detail="Not authorized")

    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    ensure_same_school(current_user, student.school_id)

    scores = db.scalars(
        select(Score).where(
            Score.student_id == student_id,
            Score.subject_id == subject_id,
            Score.term_id == term_id,
        )
    ).all()

    if not scores:
        raise HTTPException(status_code=404, detail="No scores found")

    ca_total = sum(
        float(score.value)
        for score in scores
        if score.assessment_type.category == AssessmentCategory.CA
    )

    exam_score = sum(
        float(score.value)
        for score in scores
        if score.assessment_type.category == AssessmentCategory.EXAM
    )

    if ca_total > 30:
        raise HTTPException(status_code=400, detail="CA total cannot exceed 30")

    if exam_score > 70:
        raise HTTPException(status_code=400, detail="Exam score cannot exceed 70")

    total = ca_total + exam_score

    result = db.scalar(
        select(Result).where(
            Result.student_id == student_id,
            Result.subject_id == subject_id,
            Result.term_id == term_id,
        )
    )

    if not result:
        result = Result(
            student_id=student_id,
            subject_id=subject_id,
            term_id=term_id,
        )
        db.add(result)

    result.ca_total = ca_total
    result.exam_score = exam_score
    result.total = total

    db.commit()
    db.refresh(result)

    return result
