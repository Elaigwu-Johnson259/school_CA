from app.core.security import hash_password
from app.models.academic import AcademicSession, Term
from app.models.academic_structure import ClassSubject, SchoolClass, Subject
from app.models.assessment import AssessmentType, GradingScale, Score
from app.models.enums import AssessmentCategory, TermName, UserRole
from app.models.people import Student, StudentClass, Teacher, TeacherAssignment
from app.models.school import School
from app.models.user import User


def setup_school(db):
    school = School(name="Results Academy", email="results@example.com")
    db.add(school)
    db.flush()
    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    db.add(session)
    db.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    school_class = SchoolClass(school_id=school.id, name="JSS 1A")
    subject = Subject(school_id=school.id, name="Mathematics", code="MATH")
    db.add_all([term, school_class, subject])
    db.flush()
    db.add(ClassSubject(school_class_id=school_class.id, subject_id=subject.id))
    for name, category, maximum, order in [
        ("CA1", AssessmentCategory.CA, 10, 1),
        ("CA2", AssessmentCategory.CA, 10, 2),
        ("CA3", AssessmentCategory.CA, 10, 3),
        ("Exam", AssessmentCategory.EXAM, 70, 4),
    ]:
        db.add(AssessmentType(school_id=school.id, name=name, category=category, max_score=maximum, display_order=order))
    db.add(GradingScale(school_id=school.id, grade="A", min_score=80, max_score=100))
    db.commit()
    return school, session, term, school_class, subject


def make_user(db, school, email, password, role):
    user = User(school_id=school.id, email=email, hashed_password=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_student_can_login_with_admission_number(client, db_session):
    school, session, term, school_class, subject = setup_school(db_session)
    user = User(school_id=school.id, email=None, hashed_password=hash_password("StudentPass123!"), role=UserRole.STUDENT)
    db_session.add(user)
    db_session.flush()
    student = Student(school_id=school.id, user_id=user.id, admission_number="JSA001", first_name="Johnson", last_name="Peter")
    db_session.add(student)
    db_session.commit()

    response = client.post("/api/auth/login", json={"identifier": "JSA001", "password": "StudentPass123!"})
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "STUDENT"
    assert response.json()["user"]["email"] is None


def test_teacher_assignment_controls_score_entry(db_session):
    school, session, term, school_class, subject = setup_school(db_session)
    user = make_user(db_session, school, "teacher@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher = Teacher(school_id=school.id, user_id=user.id, first_name="Peter", last_name="Teacher", email=user.email)
    student = Student(school_id=school.id, admission_number="JSA001", first_name="Johnson", last_name="Peter")
    db_session.add_all([teacher, student])
    db_session.flush()
    db_session.add(StudentClass(student_id=student.id, school_class_id=school_class.id, academic_session_id=session.id))
    db_session.add(TeacherAssignment(teacher_id=teacher.id, school_class_id=school_class.id, subject_id=subject.id))
    db_session.commit()
    assert teacher.user_id == user.id


def test_score_limits_are_10_10_10_70(db_session):
    school, session, term, school_class, subject = setup_school(db_session)
    types = db_session.query(AssessmentType).filter(AssessmentType.school_id == school.id).order_by(AssessmentType.display_order).all()
    assert [(t.name, float(t.max_score)) for t in types] == [("CA1", 10.0), ("CA2", 10.0), ("CA3", 10.0), ("Exam", 70.0)]


def test_result_math_is_24_plus_61_equals_85(db_session):
    from app.services.assessment_service import create_score
    from app.services.result_service import calculate_result

    school, session, term, school_class, subject = setup_school(db_session)
    user = make_user(db_session, school, "teacher@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher = Teacher(
        school_id=school.id,
        user_id=user.id,
        first_name="Peter",
        last_name="Teacher",
        email=user.email,
    )
    student = Student(school_id=school.id, admission_number="JSA001", first_name="Johnson", last_name="Peter")
    db_session.add_all([teacher, student])
    db_session.flush()
    db_session.add(StudentClass(student_id=student.id, school_class_id=school_class.id, academic_session_id=session.id))
    db_session.add(TeacherAssignment(teacher_id=teacher.id, school_class_id=school_class.id, subject_id=subject.id))
    db_session.commit()
    types = db_session.query(AssessmentType).filter(AssessmentType.school_id == school.id).order_by(AssessmentType.display_order).all()
    for item, value in zip(types, [8, 7, 9, 61]):
        create_score(db_session, user, student.id, subject.id, school_class.id, term.id, item.id, value)
    result = calculate_result(db_session, user, student.id, subject.id, term.id)
    assert float(result.ca_total) == 24
    assert float(result.total) == 85
    assert result.grade == "A"


def test_subject_positions_and_overall_class_position_recalculate_across_all_subjects(db_session):
    from app.models.result import ReportCard, Result
    from app.services.result_service import calculate_result

    school, session, term, school_class, maths = setup_school(db_session)
    english = Subject(school_id=school.id, name="English", code="ENG")
    biology = Subject(school_id=school.id, name="Biology", code="BIO")
    db_session.add_all([english, biology])
    db_session.flush()
    db_session.add_all([
        ClassSubject(school_class_id=school_class.id, subject_id=english.id),
        ClassSubject(school_class_id=school_class.id, subject_id=biology.id),
    ])
    teacher_user = make_user(db_session, school, "positions@example.com", "TeacherPass123!", UserRole.TEACHER)
    teacher = Teacher(school_id=school.id, user_id=teacher_user.id, first_name="Position", last_name="Teacher")
    students = [
        Student(school_id=school.id, admission_number="POS001", first_name="A", last_name="Student"),
        Student(school_id=school.id, admission_number="POS002", first_name="B", last_name="Student"),
        Student(school_id=school.id, admission_number="POS003", first_name="C", last_name="Student"),
    ]
    subjects = [maths, english, biology]
    db_session.add_all([teacher, *students])
    db_session.flush()
    db_session.add_all([
        StudentClass(student_id=student.id, school_class_id=school_class.id, academic_session_id=session.id)
        for student in students
    ])
    db_session.add_all([
        TeacherAssignment(teacher_id=teacher.id, school_class_id=school_class.id, subject_id=subject.id)
        for subject in subjects
    ])
    assessment_types = db_session.query(AssessmentType).filter(AssessmentType.school_id == school.id).order_by(AssessmentType.display_order).all()
    targets = {
        students[0].id: [85, 90, 80],
        students[1].id: [78, 75, 78],
        students[2].id: [72, 82, 81],
    }
    for subject_index, subject in enumerate(subjects):
        for student in students:
            target = targets[student.id][subject_index]
            values = [10, 10, 10, target - 30]
            for assessment, value in zip(assessment_types, values):
                db_session.add(Score(student_id=student.id, subject_id=subject.id, school_class_id=school_class.id,
                    term_id=term.id, assessment_type_id=assessment.id, recorded_by_id=teacher_user.id, value=value))
    db_session.commit()

    for subject in subjects:
        for student in students:
            calculate_result(db_session, teacher_user, student.id, subject.id, term.id)

    math_positions = {row.student_id: row.subject_position for row in db_session.query(Result).filter_by(subject_id=maths.id, term_id=term.id).all()}
    assert math_positions == {students[0].id: 1, students[1].id: 2, students[2].id: 3}
    positions = {row.student_id: row.class_position for row in db_session.query(ReportCard).filter_by(term_id=term.id).all()}
    assert positions == {students[0].id: 1, students[1].id: 3, students[2].id: 2}
    assert db_session.query(ReportCard).filter_by(term_id=term.id).first().number_of_students == 3

    changed_exam_score = db_session.query(Score).filter_by(
        student_id=students[2].id, subject_id=maths.id, term_id=term.id,
        assessment_type_id=assessment_types[3].id,
    ).one()
    changed_exam_score.value = 70
    db_session.commit()
    calculate_result(db_session, teacher_user, students[2].id, maths.id, term.id)

    refreshed_positions = {row.student_id: row.class_position for row in db_session.query(ReportCard).filter_by(term_id=term.id).all()}
    assert refreshed_positions == {students[0].id: 2, students[1].id: 3, students[2].id: 1}
    changed_math_result = db_session.query(Result).filter_by(student_id=students[2].id, subject_id=maths.id, term_id=term.id).one()
    assert changed_math_result.subject_position == 1
