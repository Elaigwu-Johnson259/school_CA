"""
Phase 2 tests: prove the models create correctly, relate to each other
correctly, and that the constraints that matter (tenant-scoped uniqueness,
cascading deletes) actually work.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    AcademicSession,
    AssessmentType,
    ClassSubject,
    ReportCard,
    Result,
    School,
    SchoolClass,
    Score,
    Student,
    StudentClass,
    Subject,
    Teacher,
    TeacherAssignment,
    Term,
    User,
)
from app.models.enums import AssessmentCategory, ResultStatus, TermName, UserRole


def _make_school(db_session, name="Greenfield High"):
    school = School(name=name, email=f"{name.lower().replace(' ', '')}@example.com")
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


def test_school_creates_with_expected_defaults(db_session):
    school = _make_school(db_session)
    assert school.id is not None
    assert school.is_active is True


def test_full_domain_graph_relates_correctly(db_session):
    """
    Walks through creating one of everything for one school and checks
    that the relationships (not just the foreign key columns) resolve.
    """
    school = _make_school(db_session)

    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    school_class = SchoolClass(school_id=school.id, name="SS 2")
    subject = Subject(school_id=school.id, name="Mathematics", code="MTH")
    db_session.add_all([term, school_class, subject])
    db_session.commit()
    db_session.refresh(term)
    db_session.refresh(school_class)
    db_session.refresh(subject)

    db_session.add(ClassSubject(school_class_id=school_class.id, subject_id=subject.id))

    teacher = Teacher(
        school_id=school.id, first_name="Ada", last_name="Obi", employee_id="EMP-001"
    )
    student = Student(
        school_id=school.id,
        admission_number="ADM-001",
        first_name="Chidi",
        last_name="Eze",
    )
    db_session.add_all([teacher, student])
    db_session.commit()
    db_session.refresh(teacher)
    db_session.refresh(student)

    db_session.add(
        TeacherAssignment(
            teacher_id=teacher.id,
            school_class_id=school_class.id,
            subject_id=subject.id,
        )
    )
    db_session.add(
        StudentClass(
            student_id=student.id,
            school_class_id=school_class.id,
            academic_session_id=session.id,
        )
    )

    assessment_type = AssessmentType(
        school_id=school.id, name="CA1", category=AssessmentCategory.CA, max_score=10
    )
    db_session.add(assessment_type)
    db_session.commit()
    db_session.refresh(assessment_type)

    db_session.add(
        Score(
            student_id=student.id,
            subject_id=subject.id,
            school_class_id=school_class.id,
            term_id=term.id,
            assessment_type_id=assessment_type.id,
            value=8,
        )
    )
    db_session.add(
        Result(
            student_id=student.id,
            subject_id=subject.id,
            term_id=term.id,
            ca_total=8,
            exam_score=50,
            total=58,
            grade="C",
        )
    )
    db_session.add(
        ReportCard(
            student_id=student.id,
            term_id=term.id,
            total_marks=58,
            average=58,
            status=ResultStatus.DRAFT,
        )
    )
    db_session.commit()

    db_session.refresh(school)
    assert len(school.students) == 1
    assert school.students[0].first_name == "Chidi"
    assert student.school.name == school.name
    assert student.class_enrollments[0].school_class.name == "SS 2"


def test_duplicate_admission_number_in_same_school_is_rejected(db_session):
    school = _make_school(db_session)
    db_session.add(
        Student(school_id=school.id, admission_number="ADM-001", first_name="A", last_name="B")
    )
    db_session.commit()

    db_session.add(
        Student(school_id=school.id, admission_number="ADM-001", first_name="C", last_name="D")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_admission_number_allowed_across_different_schools(db_session):
    """Uniqueness is scoped per school, which is the whole point of multi-tenancy."""
    school_a = _make_school(db_session, "School A")
    school_b = _make_school(db_session, "School B")

    db_session.add(
        Student(school_id=school_a.id, admission_number="ADM-001", first_name="A", last_name="B")
    )
    db_session.add(
        Student(school_id=school_b.id, admission_number="ADM-001", first_name="C", last_name="D")
    )
    db_session.commit()  # should not raise


def test_user_role_and_school_link(db_session):
    school = _make_school(db_session)
    admin = User(
        school_id=school.id, email="admin@example.com", hashed_password="hashed",
        role=UserRole.SCHOOL_ADMIN,
    )
    super_admin = User(
        email="super@example.com", hashed_password="hashed", role=UserRole.SUPER_ADMIN
    )
    db_session.add_all([admin, super_admin])
    db_session.commit()

    assert admin.school_id == school.id
    assert super_admin.school_id is None


def test_deleting_school_cascades_to_students(db_session):
    school = _make_school(db_session)
    db_session.add(
        Student(school_id=school.id, admission_number="ADM-001", first_name="A", last_name="B")
    )
    db_session.commit()

    db_session.delete(school)
    db_session.commit()

    assert db_session.query(Student).count() == 0
