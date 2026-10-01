from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.academic import (
    AcademicSessionCreate,
    AcademicSessionRead,
    AcademicSessionUpdate,
    TermCreate,
    TermRead,
    TermUpdate,
)
from app.schemas.assessment import AssessmentTypeCreate, AssessmentTypeRead, AssessmentTypeUpdate, ScoreCreate, ScoreRead, ResultRead
from app.schemas.academic_structure import (
    ClassSubjectCreate,
    ClassSubjectRead,
    SchoolClassCreate,
    SchoolClassRead,
    SchoolClassUpdate,
    SubjectCreate,
    SubjectRead,
    SubjectUpdate,
)
from app.schemas.people import (
    StudentCreate,
    StudentUpdate,
    StudentRead,
    StudentEnrollmentCreate,
    StudentEnrollmentRead,
    TeacherAssignmentCreate,
    TeacherAssignmentRead,
    TeacherCreate,
    TeacherRead,
)
from app.services import academic_service
from app.services import assessment_service
from app.services import result_service

router = APIRouter(prefix="/api/academic", tags=["academic"])


# ---------------------------------------------------------------------------
# Academic sessions
# ---------------------------------------------------------------------------

@router.post(
    "/sessions",
    response_model=AcademicSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_academic_session(
    payload: AcademicSessionCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_session(
        db=db,
        current_user=current_user,
        name=payload.name,
        is_current=payload.is_current,
    )


@router.get("/sessions", response_model=list[AcademicSessionRead])
def list_academic_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_sessions(db, current_user)


@router.get("/sessions/{session_id}", response_model=AcademicSessionRead)
def get_academic_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_session(db, current_user, session_id)


@router.patch(
    "/sessions/{session_id}",
    response_model=AcademicSessionRead,
)
def update_academic_session(
    session_id: int,
    payload: AcademicSessionUpdate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.update_session(
        db=db,
        current_user=current_user,
        session_id=session_id,
        name=payload.name,
        is_current=payload.is_current,
    )


# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/terms",
    response_model=TermRead,
    status_code=status.HTTP_201_CREATED,
)
def create_term(
    session_id: int,
    payload: TermCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_term(
        db=db,
        current_user=current_user,
        session_id=session_id,
        name=payload.name,
        is_current=payload.is_current,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )


@router.get(
    "/sessions/{session_id}/terms",
    response_model=list[TermRead],
)
def list_terms(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_terms(db, current_user, session_id)


@router.get("/terms/{term_id}", response_model=TermRead)
def get_term(
    term_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_term(db, current_user, term_id)


@router.patch("/terms/{term_id}", response_model=TermRead)
def update_term(
    term_id: int,
    payload: TermUpdate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    term = academic_service.get_term(db, current_user, term_id)

    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        setattr(term, field, value)

    db.commit()
    db.refresh(term)
    return term


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

@router.post(
    "/classes",
    response_model=SchoolClassRead,
    status_code=status.HTTP_201_CREATED,
)
def create_class(
    payload: SchoolClassCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_class(
        db=db,
        current_user=current_user,
        name=payload.name,
    )


@router.get("/classes", response_model=list[SchoolClassRead])
def list_classes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_classes(db, current_user)


@router.get("/classes/{class_id}", response_model=SchoolClassRead)
def get_class(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_class(db, current_user, class_id)


@router.patch("/classes/{class_id}", response_model=SchoolClassRead)
def update_class(
    class_id: int,
    payload: SchoolClassUpdate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.update_class(
        db=db,
        current_user=current_user,
        class_id=class_id,
        name=payload.name,
    )


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

@router.post(
    "/subjects",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(
    payload: SubjectCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_subject(
        db=db,
        current_user=current_user,
        name=payload.name,
        code=payload.code,
    )


@router.get("/subjects", response_model=list[SubjectRead])
def list_subjects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_subjects(db, current_user)


@router.get("/subjects/{subject_id}", response_model=SubjectRead)
def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_subject(db, current_user, subject_id)


@router.patch("/subjects/{subject_id}", response_model=SubjectRead)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.update_subject(
        db=db,
        current_user=current_user,
        subject_id=subject_id,
        name=payload.name,
        code=payload.code,
    )


# ---------------------------------------------------------------------------
# Class ↔ subject links
# ---------------------------------------------------------------------------

@router.post(
    "/classes/{class_id}/subjects",
    response_model=ClassSubjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_class_subject(
    class_id: int,
    payload: ClassSubjectCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_class_subject(
        db=db,
        current_user=current_user,
        school_class_id=class_id,
        subject_id=payload.subject_id,
    )


@router.get(
    "/classes/{class_id}/subjects",
    response_model=list[ClassSubjectRead],
)
def list_class_subjects(
    class_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_class_subjects(
        db=db,
        current_user=current_user,
        class_id=class_id,
    )


# ---------------------------------------------------------------------------
# Teachers
# ---------------------------------------------------------------------------

@router.post(
    "/teachers",
    response_model=TeacherRead,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher(
    payload: TeacherCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_teacher(
        db=db,
        current_user=current_user,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        employee_id=payload.employee_id,
    )


@router.get("/teachers", response_model=list[TeacherRead])
def list_teachers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_teachers(db, current_user)


@router.get("/teachers/{teacher_id}", response_model=TeacherRead)
def get_teacher(
    teacher_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_teacher(
        db=db,
        current_user=current_user,
        teacher_id=teacher_id,
    )


@router.patch(
    "/teachers/{teacher_id}",
    response_model=TeacherRead,
)
def update_teacher(
    teacher_id: int,
    payload: TeacherCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.update_teacher(
        db=db,
        current_user=current_user,
        teacher_id=teacher_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
        employee_id=payload.employee_id,
    )


# ---------------------------------------------------------------------------
# Students
# ---------------------------------------------------------------------------

@router.post(
    "/students",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    payload: StudentCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_student(
        db=db,
        current_user=current_user,
        admission_number=payload.admission_number,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        gender=payload.gender,
        date_of_birth=payload.date_of_birth,
        guardian_name=payload.guardian_name,
        guardian_phone=payload.guardian_phone,
        address=payload.address,
    )


@router.get("/students", response_model=list[StudentRead])
def list_students(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_students(db, current_user)


@router.get("/students/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_student(
        db=db,
        current_user=current_user,
        student_id=student_id,
    )


@router.patch(
    "/students/{student_id}",
    response_model=StudentRead,
)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.update_student(
        db=db,
        current_user=current_user,
        student_id=student_id,
        admission_number=payload.admission_number,
        first_name=payload.first_name,
        middle_name=payload.middle_name,
        last_name=payload.last_name,
        gender=payload.gender,
        date_of_birth=payload.date_of_birth,
        guardian_name=payload.guardian_name,
        guardian_phone=payload.guardian_phone,
        address=payload.address,
    )



# ---------------------------------------------------------------------------
# Student enrollments
# ---------------------------------------------------------------------------

@router.post(
    "/student-enrollments",
    response_model=StudentEnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_student_enrollment(
    payload: StudentEnrollmentCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_student_enrollment(
        db=db,
        current_user=current_user,
        student_id=payload.student_id,
        school_class_id=payload.school_class_id,
        academic_session_id=payload.academic_session_id,
    )


@router.get(
    "/student-enrollments",
    response_model=list[StudentEnrollmentRead],
)
def list_student_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_student_enrollments(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/student-enrollments/{enrollment_id}",
    response_model=StudentEnrollmentRead,
)
def get_student_enrollment(
    enrollment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_student_enrollment(
        db=db,
        current_user=current_user,
        enrollment_id=enrollment_id,
    )


@router.delete(
    "/student-enrollments/{enrollment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student_enrollment(
    enrollment_id: int,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    academic_service.delete_student_enrollment(
        db=db,
        current_user=current_user,
        enrollment_id=enrollment_id,
    )
    return None


# ---------------------------------------------------------------------------
# Teacher assignments
# ---------------------------------------------------------------------------

@router.post(
    "/teacher-assignments",
    response_model=TeacherAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_teacher_assignment(
    payload: TeacherAssignmentCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return academic_service.create_teacher_assignment(
        db=db,
        current_user=current_user,
        teacher_id=payload.teacher_id,
        school_class_id=payload.school_class_id,
        subject_id=payload.subject_id,
    )


@router.get(
    "/teacher-assignments",
    response_model=list[TeacherAssignmentRead],
)
def list_teacher_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.list_teacher_assignments(db, current_user)


@router.get(
    "/teacher-assignments/{assignment_id}",
    response_model=TeacherAssignmentRead,
)
def get_teacher_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return academic_service.get_teacher_assignment(
        db=db,
        current_user=current_user,
        assignment_id=assignment_id,
    )


@router.delete(
    "/teacher-assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_teacher_assignment(
    assignment_id: int,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    academic_service.delete_teacher_assignment(
        db=db,
        current_user=current_user,
        assignment_id=assignment_id,
    )


# ---------------------------------------------------------------------------
# Assessment types
# ---------------------------------------------------------------------------

@router.post(
    "/assessment-types",
    response_model=AssessmentTypeRead,
    status_code=status.HTTP_201_CREATED,
)
def create_assessment_type(
    payload: AssessmentTypeCreate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return assessment_service.create_assessment_type(
        db=db,
        current_user=current_user,
        name=payload.name,
        category=payload.category,
        max_score=payload.max_score,
        display_order=payload.display_order,
    )


@router.get(
    "/assessment-types",
    response_model=list[AssessmentTypeRead],
)
def list_assessment_types(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assessment_service.list_assessment_types(
        db=db,
        current_user=current_user,
    )


@router.get(
    "/assessment-types/{assessment_type_id}",
    response_model=AssessmentTypeRead,
)
def get_assessment_type(
    assessment_type_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return assessment_service.get_assessment_type(
        db=db,
        current_user=current_user,
        assessment_type_id=assessment_type_id,
    )

@router.patch(
    "/assessment-types/{assessment_type_id}",
    response_model=AssessmentTypeRead,
)
def update_assessment_type(
    assessment_type_id: int,
    payload: AssessmentTypeUpdate,
    current_user: User = Depends(
        require_roles(UserRole.SCHOOL_ADMIN, UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
):
    return assessment_service.update_assessment_type(
        db=db,
        current_user=current_user,
        assessment_type_id=assessment_type_id,
        name=payload.name,
        category=payload.category,
        max_score=payload.max_score,
        display_order=payload.display_order,
    )

@router.post(
    "/scores",
    response_model=ScoreRead,
    status_code=status.HTTP_201_CREATED,
)
def create_score(
    payload: ScoreCreate,
    current_user: User = Depends(
        require_roles(
            UserRole.SCHOOL_ADMIN,
            UserRole.TEACHER,
            UserRole.SUPER_ADMIN,
        )
    ),
    db: Session = Depends(get_db),
):
    return assessment_service.create_score(
        db=db,
        current_user=current_user,
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        school_class_id=payload.school_class_id,
        term_id=payload.term_id,
        assessment_type_id=payload.assessment_type_id,
        value=payload.value,
    )

@router.post("/results/calculate", response_model=ResultRead)
def calculate_result(
    student_id: int,
    subject_id: int,
    term_id: int,
    current_user: User = Depends(
        require_roles(
            UserRole.SCHOOL_ADMIN,
            UserRole.TEACHER,
            UserRole.SUPER_ADMIN,
        )
    ),
    db: Session = Depends(get_db),
):
    return result_service.calculate_result(
        db=db,
        current_user=current_user,
        student_id=student_id,
        subject_id=subject_id,
        term_id=term_id,
    )
