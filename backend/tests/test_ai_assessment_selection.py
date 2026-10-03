import pytest
import hashlib
from io import BytesIO
from fastapi import HTTPException
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.security import hash_password
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import ClassSubject, SchoolClass, Subject
from app.models.assessment import AssessmentType, GradingScale, Score
from app.models.enums import AssessmentCategory, TermName, UserRole
from app.models.examination import (
    Examination,
    ExaminationQuestion,
    QuestionType,
    ReviewStatus,
    ScriptStatus,
    StudentExaminationScript,
    StudentQuestionAnswer,
)
from app.models.people import Student, StudentClass, Teacher, TeacherAssignment
from app.models.school import School
from app.models.user import User
from app.services import academic_service, assessment_service, examination_service
from app.schemas.examination import ApproveScriptRequest
from pydantic import ValidationError


def _make_user(db, school, email, password, role):
    user = User(
        school_id=school.id,
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_teacher_only_sees_assigned_subjects_for_class(db_session):
    school = School(name="Helios Academy", email="helios@example.com")
    db_session.add(school)
    db_session.flush()

    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    db_session.add(session)
    db_session.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    class_ = SchoolClass(school_id=school.id, name="JSS 1A")
    maths = Subject(school_id=school.id, name="Mathematics", code="MATH")
    english = Subject(school_id=school.id, name="English", code="ENG")
    db_session.add_all([term, class_, maths, english])
    db_session.flush()
    db_session.add_all([
        ClassSubject(school_class_id=class_.id, subject_id=maths.id),
        ClassSubject(school_class_id=class_.id, subject_id=english.id),
    ])

    user = _make_user(db_session, school, "teacher@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher = Teacher(school_id=school.id, user_id=user.id, first_name="Ada", last_name="Teacher", email=user.email)
    db_session.add(teacher)
    db_session.flush()
    db_session.add(TeacherAssignment(teacher_id=teacher.id, school_class_id=class_.id, subject_id=maths.id))
    db_session.commit()

    assigned = academic_service.list_class_subjects(db_session, user, class_.id)
    assert [entry.subject_id for entry in assigned] == [maths.id]


def test_teacher_assignments_are_unique_per_teacher_class_subject(db_session):
    school = School(name="Helios Academy", email="helios@example.com")
    db_session.add(school)
    db_session.flush()

    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    db_session.add(session)
    db_session.flush()
    class_ = SchoolClass(school_id=school.id, name="JSS 1")
    maths = Subject(school_id=school.id, name="Mathematics", code="MATH")
    english = Subject(school_id=school.id, name="English", code="ENG")
    db_session.add_all([class_, maths, english])
    db_session.flush()
    db_session.add_all([
        ClassSubject(school_class_id=class_.id, subject_id=maths.id),
        ClassSubject(school_class_id=class_.id, subject_id=english.id),
    ])

    teacher_a_user = _make_user(db_session, school, "teacher_a@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher_b_user = _make_user(db_session, school, "teacher_b@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher_a = Teacher(school_id=school.id, user_id=teacher_a_user.id, first_name="Teacher", last_name="A")
    teacher_b = Teacher(school_id=school.id, user_id=teacher_b_user.id, first_name="Teacher", last_name="B")
    db_session.add_all([teacher_a, teacher_b])
    db_session.flush()
    db_session.add_all([
        TeacherAssignment(teacher_id=teacher_a.id, school_class_id=class_.id, subject_id=maths.id),
        TeacherAssignment(teacher_id=teacher_b.id, school_class_id=class_.id, subject_id=english.id),
    ])
    db_session.commit()

    teacher_a_subjects = [item.subject_id for item in academic_service.list_class_subjects(db_session, teacher_a_user, class_.id)]
    teacher_b_subjects = [item.subject_id for item in academic_service.list_class_subjects(db_session, teacher_b_user, class_.id)]
    assert teacher_a_subjects == [maths.id]
    assert teacher_b_subjects == [english.id]


def test_student_enrollment_is_class_based_and_visible_to_all_teachers_in_that_class(db_session):
    school = School(name="Oakridge Academy", email="oakridge@example.com")
    db_session.add(school)
    db_session.flush()

    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    db_session.add(session)
    db_session.flush()
    class_ = SchoolClass(school_id=school.id, name="JSS 1")
    maths = Subject(school_id=school.id, name="Mathematics", code="MATH")
    english = Subject(school_id=school.id, name="English", code="ENG")
    db_session.add_all([class_, maths, english])
    db_session.flush()
    db_session.add_all([
        ClassSubject(school_class_id=class_.id, subject_id=maths.id),
        ClassSubject(school_class_id=class_.id, subject_id=english.id),
    ])

    teacher_a_user = _make_user(db_session, school, "teacher_a2@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher_b_user = _make_user(db_session, school, "teacher_b2@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher_a = Teacher(school_id=school.id, user_id=teacher_a_user.id, first_name="A", last_name="Teacher")
    teacher_b = Teacher(school_id=school.id, user_id=teacher_b_user.id, first_name="B", last_name="Teacher")
    db_session.add_all([teacher_a, teacher_b])
    db_session.flush()
    db_session.add_all([
        TeacherAssignment(teacher_id=teacher_a.id, school_class_id=class_.id, subject_id=maths.id),
        TeacherAssignment(teacher_id=teacher_b.id, school_class_id=class_.id, subject_id=english.id),
    ])

    student = Student(school_id=school.id, admission_number="OAK001", first_name="Student", last_name="One")
    db_session.add(student)
    db_session.flush()
    academic_service.create_student_enrollment(db_session, teacher_a_user, student.id, class_.id, session.id)
    db_session.commit()

    teacher_a_students = [entry.id for entry in academic_service.list_students(db_session, teacher_a_user)]
    teacher_b_students = [entry.id for entry in academic_service.list_students(db_session, teacher_b_user)]
    assert student.id in teacher_a_students
    assert student.id in teacher_b_students

    student_two = Student(school_id=school.id, admission_number="OAK002", first_name="Student", last_name="Two")
    db_session.add(student_two)
    db_session.flush()
    academic_service.create_student_enrollment(db_session, teacher_a_user, student_two.id, class_.id, session.id)
    db_session.commit()

    assert student_two.id in [entry.id for entry in academic_service.list_students(db_session, teacher_b_user)]


def test_teacher_authz_restricts_subject_class_and_school_access(db_session, monkeypatch):
    school_a = School(name="School A", email="schoola@example.com")
    school_b = School(name="School B", email="schoolb@example.com")
    db_session.add_all([school_a, school_b])
    db_session.flush()

    session = AcademicSession(school_id=school_a.id, name="2026/2027", is_current=True)
    db_session.add(session)
    db_session.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    school_class = SchoolClass(school_id=school_a.id, name="JSS 1")
    maths = Subject(school_id=school_a.id, name="Mathematics", code="MATH")
    english = Subject(school_id=school_a.id, name="English", code="ENG")
    db_session.add_all([term, school_class, maths, english])
    db_session.flush()
    db_session.add_all([
        ClassSubject(school_class_id=school_class.id, subject_id=maths.id),
        ClassSubject(school_class_id=school_class.id, subject_id=english.id),
    ])
    exam_type = AssessmentType(school_id=school_a.id, name="CA1", category=AssessmentCategory.CA, max_score=10, display_order=1)
    db_session.add(exam_type)
    db_session.flush()

    teacher_user = _make_user(db_session, school_a, "teacher_only_math@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher = Teacher(school_id=school_a.id, user_id=teacher_user.id, first_name="Math", last_name="Teacher")
    db_session.add(teacher)
    db_session.flush()
    db_session.add(TeacherAssignment(teacher_id=teacher.id, school_class_id=school_class.id, subject_id=maths.id))
    english_user = _make_user(db_session, school_a, "teacher_only_english@example.com", "TeacherPass123!", UserRole.TEACHER)
    english_teacher = Teacher(school_id=school_a.id, user_id=english_user.id, first_name="English", last_name="Teacher")
    db_session.add(english_teacher)
    db_session.flush()
    db_session.add(TeacherAssignment(teacher_id=english_teacher.id, school_class_id=school_class.id, subject_id=english.id))

    student_a = Student(school_id=school_a.id, admission_number="A001", first_name="Local", last_name="Student")
    student_b = Student(school_id=school_b.id, admission_number="B001", first_name="Other", last_name="School")
    db_session.add_all([student_a, student_b])
    db_session.flush()
    db_session.add(StudentClass(student_id=student_a.id, school_class_id=school_class.id, academic_session_id=session.id))
    db_session.commit()

    assert [item.subject_id for item in academic_service.list_class_subjects(db_session, teacher_user, school_class.id)] == [maths.id]
    with pytest.raises(HTTPException):
        assessment_service.create_score(
            db_session,
            teacher_user,
            student_a.id,
            english.id,
            school_class.id,
            term.id,
            exam_type.id,
            5,
        )
    with pytest.raises(HTTPException):
        academic_service.get_student(db_session, teacher_user, student_b.id)

    exam = Examination(school_id=school_a.id, academic_session_id=session.id, term_id=term.id,
        school_class_id=school_class.id, subject_id=maths.id, created_by_id=teacher_user.id,
        title="Math script", maximum_score=10)
    db_session.add(exam)
    db_session.flush()
    script = StudentExaminationScript(school_id=school_a.id, examination_id=exam.id, student_id=student_a.id,
        assessment_type_id=exam_type.id, original_file_path="/does/not/get/read", original_filename="script.pdf")
    db_session.add(script)
    db_session.commit()
    from app.services import ai_marking_service
    monkeypatch.setattr(ai_marking_service, "get_ai_provider", lambda: pytest.fail("provider must not run for unauthorized subject"))
    with pytest.raises(HTTPException) as unauthorized_subject:
        examination_service.process_ai_marking(db_session, english_user, script.id)
    assert unauthorized_subject.value.status_code == 403

    school_b_user = _make_user(db_session, school_b, "schoolb_admin@example.com", "AdminPass123!", UserRole.SCHOOL_ADMIN)
    with pytest.raises(HTTPException):
        examination_service.process_ai_marking(db_session, school_b_user, script.id)


def test_manual_scores_enforce_max_values_and_ai_approval_writes_to_normal_score_record(db_session):
    school = School(name="Final Check Academy", email="final@example.com")
    db_session.add(school)
    db_session.flush()

    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    db_session.add(session)
    db_session.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    class_ = SchoolClass(school_id=school.id, name="JSS 1")
    maths = Subject(school_id=school.id, name="Mathematics", code="MATH")
    db_session.add_all([term, class_, maths])
    db_session.flush()
    db_session.add(ClassSubject(school_class_id=class_.id, subject_id=maths.id))

    ca1 = AssessmentType(school_id=school.id, name="CA1", category=AssessmentCategory.CA, max_score=10, display_order=1)
    ca2 = AssessmentType(school_id=school.id, name="CA2", category=AssessmentCategory.CA, max_score=10, display_order=2)
    ca3 = AssessmentType(school_id=school.id, name="CA3", category=AssessmentCategory.CA, max_score=10, display_order=3)
    exam_type = AssessmentType(school_id=school.id, name="Exam", category=AssessmentCategory.EXAM, max_score=70, display_order=4)
    db_session.add_all([ca1, ca2, ca3, exam_type, GradingScale(school_id=school.id, grade="A", min_score=80, max_score=100)])
    db_session.flush()

    teacher_user = _make_user(db_session, school, "teacher_final@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher = Teacher(school_id=school.id, user_id=teacher_user.id, first_name="Final", last_name="Teacher")
    student = Student(school_id=school.id, admission_number="FIN001", first_name="Final", last_name="Student")
    db_session.add_all([teacher, student])
    db_session.flush()
    db_session.add(StudentClass(student_id=student.id, school_class_id=class_.id, academic_session_id=session.id))
    db_session.add(TeacherAssignment(teacher_id=teacher.id, school_class_id=class_.id, subject_id=maths.id))
    db_session.commit()

    with pytest.raises(HTTPException):
        assessment_service.create_score(db_session, teacher_user, student.id, maths.id, class_.id, term.id, ca1.id, 11)
    with pytest.raises(HTTPException):
        assessment_service.create_score(db_session, teacher_user, student.id, maths.id, class_.id, term.id, exam_type.id, 71)
    with pytest.raises(HTTPException):
        assessment_service.create_score(db_session, teacher_user, student.id, maths.id, class_.id, term.id, ca3.id, 11)
    with pytest.raises(HTTPException):
        assessment_service.create_score(db_session, teacher_user, student.id, maths.id, class_.id, term.id, ca1.id, -1)

    valid = assessment_service.create_score(db_session, teacher_user, student.id, maths.id, class_.id, term.id, ca1.id, 8)
    another = assessment_service.create_score(db_session, teacher_user, student.id, maths.id, class_.id, term.id, ca2.id, 9)
    ca3_score = assessment_service.create_score(db_session, teacher_user, student.id, maths.id, class_.id, term.id, ca3.id, 7)
    assert float(valid.value) == 8
    assert float(another.value) == 9
    assert float(ca3_score.value) == 7

    exam = Examination(
        school_id=school.id,
        academic_session_id=session.id,
        term_id=term.id,
        school_class_id=class_.id,
        subject_id=maths.id,
        created_by_id=teacher_user.id,
        title="Final Exam",
        maximum_score=70,
    )
    db_session.add(exam)
    db_session.flush()
    question = ExaminationQuestion(
        examination_id=exam.id,
        question_number="1",
        question_text="Solve 2 + 2.",
        question_type=QuestionType.OBJECTIVE,
        maximum_marks=10,
        display_order=1,
        correct_option="B",
    )
    db_session.add(question)
    db_session.flush()

    script = StudentExaminationScript(
        school_id=school.id,
        examination_id=exam.id,
        student_id=student.id,
        original_file_path="/tmp/final.pdf",
        original_filename="final.pdf",
        status=ScriptStatus.AI_MARKED,
        assessment_type_id=ca1.id,
    )
    db_session.add(script)
    db_session.flush()
    db_session.add(StudentQuestionAnswer(script_id=script.id, question_id=question.id, ai_proposed_score=8, teacher_final_score=8, review_status=ReviewStatus.REVIEWED))
    db_session.commit()

    approved = examination_service.approve_script(db_session, teacher_user, script.id, assessment_type_id=ca1.id)
    score = db_session.query(Score).filter(
        Score.student_id == student.id,
        Score.subject_id == maths.id,
        Score.term_id == term.id,
        Score.assessment_type_id == ca1.id,
    ).one()
    assert approved.status == ScriptStatus.APPROVED
    assert float(score.value) == 8


def test_script_upload_persists_assessment_checksum_and_prevents_same_component_duplicates(db_session, monkeypatch, tmp_path):
    from app.core.config import settings
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", str(tmp_path))
    school = School(name="Upload Academy", email="upload@example.com")
    db_session.add(school)
    db_session.flush()
    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    school_class = SchoolClass(school_id=school.id, name="JSS 1")
    subject = Subject(school_id=school.id, name="Mathematics", code="MATH")
    student = Student(school_id=school.id, admission_number="UP001", first_name="Upload", last_name="Student")
    db_session.add_all([session, school_class, subject, student])
    db_session.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    ca1 = AssessmentType(school_id=school.id, name="CA1", category=AssessmentCategory.CA, max_score=10)
    ca2 = AssessmentType(school_id=school.id, name="CA2", category=AssessmentCategory.CA, max_score=10)
    db_session.add_all([term, ca1, ca2, ClassSubject(school_class_id=school_class.id, subject_id=subject.id)])
    teacher_user = _make_user(db_session, school, "upload-teacher@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher = Teacher(school_id=school.id, user_id=teacher_user.id, first_name="Upload", last_name="Teacher")
    db_session.add(teacher)
    db_session.flush()
    db_session.add_all([
        StudentClass(student_id=student.id, school_class_id=school_class.id, academic_session_id=session.id),
        TeacherAssignment(teacher_id=teacher.id, school_class_id=school_class.id, subject_id=subject.id),
    ])
    exam = Examination(school_id=school.id, academic_session_id=session.id, term_id=term.id,
        school_class_id=school_class.id, subject_id=subject.id, created_by_id=teacher_user.id,
        title="Assessment uploads", maximum_score=10)
    db_session.add(exam)
    db_session.commit()
    pdf = b"%PDF-1.7\nscript payload"

    def upload():
        return UploadFile(file=BytesIO(pdf), filename="student.pdf", headers=Headers({"content-type": "application/pdf"}))

    ca1_script = examination_service.upload_script(db_session, teacher_user, exam.id, student.id, upload(), ca1.id)
    ca2_script = examination_service.upload_script(db_session, teacher_user, exam.id, student.id, upload(), ca2.id)
    assert ca1_script.assessment_type_id == ca1.id
    assert ca2_script.assessment_type_id == ca2.id
    assert ca1_script.checksum_sha256 == hashlib.sha256(pdf).hexdigest()
    with pytest.raises(HTTPException) as duplicate:
        examination_service.upload_script(db_session, teacher_user, exam.id, student.id, upload(), ca1.id)
    assert duplicate.value.status_code == 409


def test_approval_confirmation_is_required():
    with pytest.raises(ValidationError):
        ApproveScriptRequest.model_validate({})


def test_script_storage_failure_returns_safe_service_error(monkeypatch, tmp_path):
    from app.core.config import settings
    monkeypatch.setattr(settings, "LOCAL_STORAGE_PATH", str(tmp_path / "not-a-directory"))
    (tmp_path / "not-a-directory").write_text("blocking file", encoding="utf-8")
    upload = UploadFile(file=BytesIO(b"script"), filename="script.txt", headers=Headers({"content-type": "text/plain"}))
    with pytest.raises(HTTPException) as unavailable:
        examination_service._save_upload(upload, 1, "student-scripts")
    assert unavailable.value.status_code == 503
    assert unavailable.value.detail == "File storage is unavailable"
