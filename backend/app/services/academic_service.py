from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.tenancy import ensure_same_school
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import ClassSubject, SchoolClass, Subject
from app.models.enums import UserRole
from app.models.people import Student, StudentClass, Teacher, TeacherAssignment
from app.models.user import User


def create_session(
    db: Session,
    current_user: User,
    name: str,
    is_current: bool = False,
) -> AcademicSession:
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a school-bound account",
        )

    if is_current:
        db.query(AcademicSession).filter(
            AcademicSession.school_id == current_user.school_id,
            AcademicSession.is_current.is_(True),
        ).update({"is_current": False}, synchronize_session=False)

    session = AcademicSession(
        school_id=current_user.school_id,
        name=name,
        is_current=is_current,
    )

    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_sessions(db: Session, current_user: User) -> list[AcademicSession]:
    query = db.query(AcademicSession)

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(AcademicSession.school_id == current_user.school_id)

    return query.order_by(AcademicSession.name.desc()).all()


def get_session(
    db: Session,
    current_user: User,
    session_id: int,
) -> AcademicSession:
    session = db.get(AcademicSession, session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    ensure_same_school(current_user, session.school_id)
    return session


def update_session(
    db: Session,
    current_user: User,
    session_id: int,
    name: str | None = None,
    is_current: bool | None = None,
) -> AcademicSession:
    session = get_session(db, current_user, session_id)

    if name is not None:
        session.name = name

    if is_current is True:
        db.query(AcademicSession).filter(
            AcademicSession.school_id == session.school_id,
            AcademicSession.id != session.id,
        ).update({"is_current": False}, synchronize_session=False)

        session.is_current = True

    elif is_current is False:
        session.is_current = False

    db.commit()
    db.refresh(session)
    return session


def create_term(
    db: Session,
    current_user: User,
    session_id: int,
    name,
    is_current: bool = False,
    start_date=None,
    end_date=None,
) -> Term:
    session = get_session(db, current_user, session_id)

    if is_current:
        db.query(Term).filter(
            Term.academic_session_id == session.id,
            Term.is_current.is_(True),
        ).update({"is_current": False}, synchronize_session=False)

    term = Term(
        academic_session_id=session.id,
        name=name,
        is_current=is_current,
        start_date=start_date,
        end_date=end_date,
    )

    db.add(term)
    db.commit()
    db.refresh(term)
    return term


def list_terms(
    db: Session,
    current_user: User,
    session_id: int,
) -> list[Term]:
    session = get_session(db, current_user, session_id)

    return (
        db.query(Term)
        .filter(Term.academic_session_id == session.id)
        .order_by(Term.id)
        .all()
    )


def get_term(
    db: Session,
    current_user: User,
    term_id: int,
) -> Term:
    term = db.get(Term, term_id)

    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Term not found",
        )

    session = db.get(AcademicSession, term.academic_session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Academic session not found",
        )

    ensure_same_school(current_user, session.school_id)
    return term


def create_class(
    db: Session,
    current_user: User,
    name: str,
) -> SchoolClass:
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a school-bound account",
        )

    school_class = SchoolClass(
        school_id=current_user.school_id,
        name=name,
    )

    db.add(school_class)
    db.commit()
    db.refresh(school_class)
    return school_class


def list_classes(
    db: Session,
    current_user: User,
) -> list[SchoolClass]:
    query = db.query(SchoolClass)

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(SchoolClass.school_id == current_user.school_id)

    return query.order_by(SchoolClass.name).all()


def get_class(
    db: Session,
    current_user: User,
    class_id: int,
) -> SchoolClass:
    school_class = db.get(SchoolClass, class_id)

    if school_class is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found",
        )

    ensure_same_school(current_user, school_class.school_id)
    return school_class


def update_class(
    db: Session,
    current_user: User,
    class_id: int,
    name: str | None = None,
) -> SchoolClass:
    school_class = get_class(db, current_user, class_id)

    if name is not None:
        school_class.name = name

    db.commit()
    db.refresh(school_class)
    return school_class


def create_subject(
    db: Session,
    current_user: User,
    name: str,
    code: str | None = None,
) -> Subject:
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a school-bound account",
        )

    subject = Subject(
        school_id=current_user.school_id,
        name=name,
        code=code,
    )

    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def list_subjects(
    db: Session,
    current_user: User,
) -> list[Subject]:
    query = db.query(Subject)

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(Subject.school_id == current_user.school_id)

    return query.order_by(Subject.name).all()


def get_subject(
    db: Session,
    current_user: User,
    subject_id: int,
) -> Subject:
    subject = db.get(Subject, subject_id)

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found",
        )

    ensure_same_school(current_user, subject.school_id)
    return subject


def update_subject(
    db: Session,
    current_user: User,
    subject_id: int,
    name: str | None = None,
    code: str | None = None,
) -> Subject:
    subject = get_subject(db, current_user, subject_id)

    if name is not None:
        subject.name = name

    if code is not None:
        subject.code = code

    db.commit()
    db.refresh(subject)
    return subject


def create_class_subject(
    db: Session,
    current_user: User,
    school_class_id: int,
    subject_id: int,
) -> ClassSubject:
    school_class = get_class(db, current_user, school_class_id)
    subject = get_subject(db, current_user, subject_id)

    if school_class.school_id != subject.school_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class or subject not found",
        )

    existing = db.query(ClassSubject).filter(
        ClassSubject.school_class_id == school_class.id,
        ClassSubject.subject_id == subject.id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject is already linked to this class",
        )

    link = ClassSubject(
        school_class_id=school_class.id,
        subject_id=subject.id,
    )

    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def list_class_subjects(
    db: Session,
    current_user: User,
    class_id: int,
) -> list[ClassSubject]:
    school_class = get_class(db, current_user, class_id)

    return (
        db.query(ClassSubject)
        .join(Subject, Subject.id == ClassSubject.subject_id)
        .filter(ClassSubject.school_class_id == school_class.id)
        .all()
    )


def create_teacher(
    db: Session,
    current_user: User,
    first_name: str,
    last_name: str,
    email: str | None = None,
    phone: str | None = None,
    employee_id: str | None = None,
) -> Teacher:
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a school-bound account",
        )

    teacher = Teacher(
        school_id=current_user.school_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        employee_id=employee_id,
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def list_teachers(
    db: Session,
    current_user: User,
) -> list[Teacher]:
    query = db.query(Teacher)

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(Teacher.school_id == current_user.school_id)

    return query.order_by(Teacher.last_name, Teacher.first_name).all()


def get_teacher(
    db: Session,
    current_user: User,
    teacher_id: int,
) -> Teacher:
    teacher = db.get(Teacher, teacher_id)

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    ensure_same_school(current_user, teacher.school_id)
    return teacher


def update_teacher(
    db: Session,
    current_user: User,
    teacher_id: int,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    employee_id: str | None = None,
) -> Teacher:
    teacher = get_teacher(db, current_user, teacher_id)

    if first_name is not None:
        teacher.first_name = first_name

    if last_name is not None:
        teacher.last_name = last_name

    if email is not None:
        teacher.email = email

    if phone is not None:
        teacher.phone = phone

    if employee_id is not None:
        teacher.employee_id = employee_id

    db.commit()
    db.refresh(teacher)
    return teacher



def create_student(
    db: Session,
    current_user: User,
    admission_number: str,
    first_name: str,
    middle_name: str | None = None,
    last_name: str = "",
    gender=None,
    date_of_birth=None,
    guardian_name: str | None = None,
    guardian_phone: str | None = None,
    address: str | None = None,
) -> Student:
    if current_user.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a school-bound account",
        )

    student = Student(
        school_id=current_user.school_id,
        admission_number=admission_number,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        gender=gender,
        date_of_birth=date_of_birth,
        guardian_name=guardian_name,
        guardian_phone=guardian_phone,
        address=address,
    )

    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def list_students(
    db: Session,
    current_user: User,
) -> list[Student]:
    query = db.query(Student)

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(Student.school_id == current_user.school_id)

    return query.order_by(Student.last_name, Student.first_name).all()


def get_student(
    db: Session,
    current_user: User,
    student_id: int,
) -> Student:
    student = db.get(Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    ensure_same_school(current_user, student.school_id)
    return student


def update_student(
    db: Session,
    current_user: User,
    student_id: int,
    admission_number: str | None = None,
    first_name: str | None = None,
    middle_name: str | None = None,
    last_name: str | None = None,
    gender=None,
    date_of_birth=None,
    guardian_name: str | None = None,
    guardian_phone: str | None = None,
    address: str | None = None,
) -> Student:
    student = get_student(db, current_user, student_id)

    if admission_number is not None:
        student.admission_number = admission_number

    if first_name is not None:
        student.first_name = first_name

    if middle_name is not None:
        student.middle_name = middle_name

    if last_name is not None:
        student.last_name = last_name

    if gender is not None:
        student.gender = gender

    if date_of_birth is not None:
        student.date_of_birth = date_of_birth

    if guardian_name is not None:
        student.guardian_name = guardian_name

    if guardian_phone is not None:
        student.guardian_phone = guardian_phone

    if address is not None:
        student.address = address

    db.commit()
    db.refresh(student)
    return student


def create_student_enrollment(
    db: Session,
    current_user: User,
    student_id: int,
    school_class_id: int,
    academic_session_id: int,
) -> StudentClass:
    student = get_student(db, current_user, student_id)
    school_class = get_class(db, current_user, school_class_id)
    academic_session = get_session(db, current_user, academic_session_id)

    if (
        student.school_id != school_class.school_id
        or student.school_id != academic_session.school_id
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student, class, or academic session not found",
        )

    existing = db.query(StudentClass).filter(
        StudentClass.student_id == student.id,
        StudentClass.academic_session_id == academic_session.id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student is already enrolled for this academic session",
        )

    enrollment = StudentClass(
        student_id=student.id,
        school_class_id=school_class.id,
        academic_session_id=academic_session.id,
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def list_student_enrollments(
    db: Session,
    current_user: User,
) -> list[StudentClass]:
    query = (
        db.query(StudentClass)
        .join(Student, Student.id == StudentClass.student_id)
    )

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(Student.school_id == current_user.school_id)

    return query.order_by(StudentClass.id).all()


def get_student_enrollment(
    db: Session,
    current_user: User,
    enrollment_id: int,
) -> StudentClass:
    enrollment = db.get(StudentClass, enrollment_id)

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student enrollment not found",
        )

    student = db.get(Student, enrollment.student_id)

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student enrollment not found",
        )

    ensure_same_school(current_user, student.school_id)
    return enrollment


def delete_student_enrollment(
    db: Session,
    current_user: User,
    enrollment_id: int,
) -> None:
    enrollment = get_student_enrollment(
        db=db,
        current_user=current_user,
        enrollment_id=enrollment_id,
    )

    db.delete(enrollment)
    db.commit()

def create_teacher_assignment(
    db: Session,
    current_user: User,
    teacher_id: int,
    school_class_id: int,
    subject_id: int,
) -> TeacherAssignment:
    teacher = db.get(Teacher, teacher_id)

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    ensure_same_school(current_user, teacher.school_id)

    school_class = get_class(db, current_user, school_class_id)
    subject = get_subject(db, current_user, subject_id)

    if school_class.school_id != subject.school_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class or subject not found",
        )

    class_subject = db.query(ClassSubject).filter(
        ClassSubject.school_class_id == school_class.id,
        ClassSubject.subject_id == subject.id,
    ).first()

    if class_subject is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject must be linked to the class before assigning a teacher",
        )

    existing = db.query(TeacherAssignment).filter(
        TeacherAssignment.teacher_id == teacher.id,
        TeacherAssignment.school_class_id == school_class.id,
        TeacherAssignment.subject_id == subject.id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teacher is already assigned to this class and subject",
        )

    assignment = TeacherAssignment(
        teacher_id=teacher.id,
        school_class_id=school_class.id,
        subject_id=subject.id,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def list_teacher_assignments(
    db: Session,
    current_user: User,
) -> list[TeacherAssignment]:
    query = (
        db.query(TeacherAssignment)
        .join(Teacher, Teacher.id == TeacherAssignment.teacher_id)
    )

    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(Teacher.school_id == current_user.school_id)

    return query.order_by(TeacherAssignment.id).all()


def get_teacher_assignment(
    db: Session,
    current_user: User,
    assignment_id: int,
) -> TeacherAssignment:
    assignment = db.get(TeacherAssignment, assignment_id)

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher assignment not found",
        )

    teacher = db.get(Teacher, assignment.teacher_id)

    if teacher is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found",
        )

    ensure_same_school(current_user, teacher.school_id)
    return assignment


def delete_teacher_assignment(
    db: Session,
    current_user: User,
    assignment_id: int,
) -> None:
    assignment = get_teacher_assignment(db, current_user, assignment_id)

    db.delete(assignment)
    db.commit()
