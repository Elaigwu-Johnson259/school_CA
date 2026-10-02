from app.models.academic import AcademicSession, Term
from app.models.academic_structure import ClassSubject, SchoolClass, Subject
from app.models.enums import TermName, UserRole
from app.models.examination import (
    Examination, ExaminationQuestion, ExaminationStatus, QuestionReferenceMaterial,
    QuestionType, ReferenceMaterialType, ReviewStatus, ScriptStatus,
    StudentExaminationScript, StudentQuestionAnswer,
)
from app.models.people import Student, StudentClass
from app.models.school import School
from app.models.user import User


def _context(db):
    school = School(name="Exam Academy", email="exam@example.com")
    db.add(school)
    db.flush()
    session = AcademicSession(school_id=school.id, name="2026/2027")
    db.add(session)
    db.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST)
    school_class = SchoolClass(school_id=school.id, name="JSS 1")
    subject = Subject(school_id=school.id, name="Mathematics")
    user = User(school_id=school.id, email="teacher@example.com", hashed_password="test", role=UserRole.TEACHER)
    student = Student(school_id=school.id, admission_number="EA001", first_name="Exam", last_name="Student")
    db.add_all([term, school_class, subject, user, student])
    db.flush()
    db.add(ClassSubject(school_class_id=school_class.id, subject_id=subject.id))
    db.add(StudentClass(student_id=student.id, school_class_id=school_class.id, academic_session_id=session.id))
    db.commit()
    return school, session, term, school_class, subject, user, student


def test_examination_supports_objective_and_subjective_questions(db_session):
    school, session, term, school_class, subject, user, student = _context(db_session)
    exam = Examination(
        school_id=school.id, academic_session_id=session.id, term_id=term.id,
        school_class_id=school_class.id, subject_id=subject.id, created_by_id=user.id,
        title="First Term Examination", maximum_score=70, status=ExaminationStatus.DRAFT,
    )
    db_session.add(exam)
    db_session.flush()
    objective = ExaminationQuestion(
        examination_id=exam.id, question_number="1", question_text="2 + 2 = ?",
        question_type=QuestionType.OBJECTIVE, maximum_marks=2, display_order=1, correct_option="B",
    )
    subjective = ExaminationQuestion(
        examination_id=exam.id, question_number="2", question_text="Explain photosynthesis.",
        question_type=QuestionType.SUBJECTIVE, maximum_marks=8, display_order=2,
        expected_concepts="sunlight; water; carbon dioxide; glucose; oxygen",
        acceptable_alternatives="Equivalent scientifically correct wording is acceptable.",
        partial_credit_guidance="Award partial marks for demonstrated understanding.",
    )
    db_session.add_all([objective, subjective])
    db_session.commit()
    assert exam.questions[0].correct_option == "B"
    assert exam.questions[1].partial_credit_guidance.startswith("Award partial")


def test_multiple_reference_materials_and_future_marking_fields(db_session):
    school, session, term, school_class, subject, user, student = _context(db_session)
    exam = Examination(
        school_id=school.id, academic_session_id=session.id, term_id=term.id,
        school_class_id=school_class.id, subject_id=subject.id, created_by_id=user.id,
        title="Mathematics", maximum_score=70,
    )
    db_session.add(exam)
    db_session.flush()
    question = ExaminationQuestion(
        examination_id=exam.id, question_number="1", question_text="Solve x + 2 = 5.",
        question_type=QuestionType.SUBJECTIVE, maximum_marks=5, display_order=1,
    )
    db_session.add(question)
    db_session.flush()
    db_session.add_all([
        QuestionReferenceMaterial(question_id=question.id, material_type=ReferenceMaterialType.TYPED_ANSWER, text_content="x = 3"),
        QuestionReferenceMaterial(question_id=question.id, material_type=ReferenceMaterialType.HANDWRITTEN, original_file_path="schools/1/examinations/references/handwritten.jpg", original_filename="handwritten.jpg"),
        QuestionReferenceMaterial(question_id=question.id, material_type=ReferenceMaterialType.WORKED_SOLUTION, original_file_path="schools/1/examinations/references/worked.pdf", original_filename="worked.pdf"),
    ])
    script = StudentExaminationScript(
        school_id=school.id, examination_id=exam.id, student_id=student.id,
        original_file_path="schools/1/examinations/student-scripts/script.pdf", original_filename="script.pdf",
        status=ScriptStatus.READY_FOR_MARKING,
    )
    db_session.add(script)
    db_session.flush()
    db_session.add(StudentQuestionAnswer(
        script_id=script.id, question_id=question.id, extracted_text="x = 3",
        ai_proposed_score=4, ai_evidence="Correct method and answer", ai_confidence=0.96,
        teacher_final_score=5, teacher_adjustment=1, review_status=ReviewStatus.APPROVED,
    ))
    db_session.commit()
    assert db_session.query(QuestionReferenceMaterial).filter_by(question_id=question.id).count() == 3
    answer = db_session.query(StudentQuestionAnswer).one()
    assert float(answer.ai_proposed_score) == 4
    assert float(answer.teacher_final_score) == 5
    assert answer.review_status == ReviewStatus.APPROVED
