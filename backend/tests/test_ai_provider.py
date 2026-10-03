import pytest
from types import SimpleNamespace
from pydantic import ValidationError

from app.models.academic import AcademicSession, Term
from app.models.academic_structure import ClassSubject, SchoolClass, Subject
from app.models.assessment import AssessmentType, GradingScale, Score
from app.models.enums import AssessmentCategory, TermName, UserRole
from app.models.examination import Examination, ExaminationQuestion, QuestionType, ScriptStatus, StudentExaminationScript, StudentQuestionAnswer
from app.models.people import Student, StudentClass, Teacher, TeacherAssignment
from app.models.school import School
from app.models.user import User
from app.services.ai_provider import AIProviderConfigurationError, AIProviderResponseError, MockAIProvider, OpenAIProvider, AIProviderFactory, validate_ai_provider_config
from app.services import examination_service
from app.core.security import hash_password
from app.schemas.examination import MarkReviewUpdate


def _make_user(db, school, email, role=UserRole.TEACHER):
    user = User(school_id=school.id, email=email, hashed_password=hash_password("TeacherPass123!"), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_provider_configuration_requires_credentials_for_openai(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "OPENAI_API_KEY", None)
    monkeypatch.setattr(settings, "AI_API_KEY", None)
    with pytest.raises(AIProviderConfigurationError):
        validate_ai_provider_config("openai")


def test_provider_factory_never_falls_back_from_openai_to_mock(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "AI_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key-not-used-for-network")
    provider = AIProviderFactory.create()
    assert isinstance(provider, OpenAIProvider)
    assert not isinstance(provider, MockAIProvider)


def test_production_settings_reject_mock_or_missing_openai_credentials():
    from app.core.config import Settings
    with pytest.raises(ValidationError):
        Settings(DATABASE_URL="sqlite://", JWT_SECRET="test", ENVIRONMENT="production", AI_PROVIDER="mock")
    settings = Settings(
        DATABASE_URL="sqlite://",
        JWT_SECRET="test",
        ENVIRONMENT="production",
        AI_PROVIDER="openai",
        OPENAI_API_KEY="configured-test-key",
    )
    assert settings.AI_PROVIDER == "openai"


@pytest.mark.parametrize(("filename", "mime_type", "expected_kind", "signature"), [
    ("script.pdf", "application/pdf", "input_file", b"%PDF-1.7"),
    ("script.jpg", "image/jpeg", "input_image", b"\xff\xd8\xff\xe0data"),
    ("script.png", "image/png", "input_image", b"\x89PNG\r\n\x1adata"),
])
def test_openai_extraction_sends_real_document_content(filename, mime_type, expected_kind, signature, tmp_path):
    file_path = tmp_path / filename
    file_path.write_bytes(signature)
    call = {}

    def create(**kwargs):
        call.update(kwargs)
        return SimpleNamespace(output_text='{"answers":[{"question_id":7,"answer":"B","confidence":0.92}]}')

    provider = object.__new__(OpenAIProvider)
    provider.model = "gpt-4o-mini"
    provider.client = SimpleNamespace(responses=SimpleNamespace(create=create))
    results = provider.extract_script_answers(str(file_path), mime_type, [{"id": 7, "question_number": "1", "question_text": "Select."}])
    assert results[7].text == "B"
    assert results[7].needs_review is False
    document = call["input"][0]["content"][1]
    assert document["type"] == expected_kind
    assert "base64," in (document.get("file_data") or document.get("image_url"))


def test_openai_provider_errors_are_wrapped_without_mock_fallback():
    from app.services.ai_provider import AIProviderError
    provider = object.__new__(OpenAIProvider)
    provider.model = "gpt-4o-mini"
    provider.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("secret SDK details"))))
    with pytest.raises(AIProviderError, match="could not process"):
        provider._request_json("test")


def test_typed_script_answers_are_mapped_per_question_or_left_unmapped(tmp_path):
    script = tmp_path / "answers.txt"
    script.write_text("1. B\n2) Twenty-four", encoding="utf-8")
    questions = [
        {"id": 10, "question_number": "1", "question_text": "Choose."},
        {"id": 20, "question_number": "2", "question_text": "Calculate."},
    ]
    answers = MockAIProvider().extract_script_answers(str(script), "text/plain", questions)
    assert answers[10].text == "B"
    assert answers[20].text == "Twenty-four"

    script.write_text("An unnumbered whole-script response", encoding="utf-8")
    assert MockAIProvider().extract_script_answers(str(script), "text/plain", questions) == {}


def test_openai_typed_script_returns_distinct_question_level_answers(tmp_path):
    script = tmp_path / "answers.txt"
    script.write_text("1. B\n2. 24", encoding="utf-8")
    provider = object.__new__(OpenAIProvider)
    provider.model = "gpt-4o-mini"
    provider.client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(output_text='{"answers":[{"question_id":10,"answer":"B","confidence":0.95},{"question_id":20,"answer":"24","confidence":0.91}]}')))
    questions = [
        {"id": 10, "question_number": "1", "question_text": "Choose."},
        {"id": 20, "question_number": "2", "question_text": "Calculate."},
    ]
    answers = provider.extract_script_answers(str(script), "text/plain", questions)
    assert answers[10].text == "B"
    assert answers[20].text == "24"


def test_mock_provider_marks_objective_question_correctly():
    provider = MockAIProvider()
    result = provider.evaluate_answer(
        question={
            "question_type": QuestionType.OBJECTIVE,
            "maximum_marks": 10,
            "correct_option": "B",
            "question_text": "2 + 2 = ?",
        },
        student_answer="B",
        reference_materials=[],
        context={},
    )
    assert result.score == 10
    assert result.max_marks == 10
    assert "correct option" in result.evidence.lower()
    incorrect = provider.evaluate_answer(
        question={"question_type": QuestionType.OBJECTIVE, "maximum_marks": 10, "correct_option": "B"},
        student_answer="C",
        reference_materials=[],
        context={},
    )
    assert incorrect.score == 0


def test_mock_provider_does_not_claim_semantic_subjective_marking():
    provider = MockAIProvider()
    result = provider.evaluate_answer(
        question={
            "question_type": QuestionType.SUBJECTIVE,
            "maximum_marks": 10,
            "marking_guidance": "Award up to 10 for a correct explanation with reasoning. Partial credit for a less complete answer.",
            "expected_concepts": "photosynthesis uses sunlight to make food",
            "acceptable_alternatives": "chlorophyll captures light and plants make glucose",
        },
        student_answer="Plants use sunlight to make food in leaves; chlorophyll absorbs light and they create glucose.",
        reference_materials=[],
        context={},
    )
    assert result.score == 0
    assert result.max_marks == 10
    assert "does not perform semantic evaluation" in result.evidence


def test_ai_marking_service_creates_pending_reviews_and_preserves_normal_score_flow(db_session, monkeypatch, tmp_path):
    from app.services import ai_marking_service
    monkeypatch.setattr(ai_marking_service, "get_ai_provider", MockAIProvider)

    school = School(name="AI Academy", email="ai@example.com")
    db_session.add(school)
    db_session.flush()

    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    db_session.add(session)
    db_session.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    school_class = SchoolClass(school_id=school.id, name="JSS 1")
    subject = Subject(school_id=school.id, name="Mathematics", code="MATH")
    db_session.add_all([term, school_class, subject])
    db_session.flush()
    ca1 = AssessmentType(school_id=school.id, name="CA1", category=AssessmentCategory.CA, max_score=10, display_order=1)
    db_session.add_all([
        ClassSubject(school_class_id=school_class.id, subject_id=subject.id),
        ca1,
        AssessmentType(school_id=school.id, name="Exam", category=AssessmentCategory.EXAM, max_score=70, display_order=4),
        GradingScale(school_id=school.id, grade="A", min_score=80, max_score=100),
    ])
    db_session.flush()

    teacher_user = _make_user(db_session, school, "teacher.ai@example.com", UserRole.TEACHER)
    teacher = Teacher(school_id=school.id, user_id=teacher_user.id, first_name="Aisha", last_name="Mark")
    student = Student(school_id=school.id, admission_number="AI001", first_name="Ada", last_name="Student")
    db_session.add_all([teacher, student])
    db_session.flush()
    db_session.add(StudentClass(student_id=student.id, school_class_id=school_class.id, academic_session_id=session.id))
    db_session.add(TeacherAssignment(teacher_id=teacher.id, school_class_id=school_class.id, subject_id=subject.id))
    db_session.commit()

    exam = Examination(
        school_id=school.id,
        academic_session_id=session.id,
        term_id=term.id,
        school_class_id=school_class.id,
        subject_id=subject.id,
        created_by_id=teacher_user.id,
        title="CA1 Quiz",
        maximum_score=10,
    )
    db_session.add(exam)
    db_session.flush()
    question = ExaminationQuestion(
        examination_id=exam.id,
        question_number="1",
        question_text="What is 2 + 2?",
        question_type=QuestionType.OBJECTIVE,
        maximum_marks=10,
        display_order=1,
        correct_option="B",
    )
    db_session.add(question)
    db_session.flush()

    answer_file = tmp_path / "answer.txt"
    answer_file.write_text("B", encoding="utf-8")
    script = StudentExaminationScript(
        school_id=school.id,
        examination_id=exam.id,
        student_id=student.id,
        assessment_type_id=ca1.id,
        original_file_path=str(answer_file),
        original_filename="answer.txt",
        content_type="text/plain",
        status=ScriptStatus.UPLOADED,
    )
    db_session.add(script)
    db_session.flush()
    db_session.commit()

    processed = examination_service.process_ai_marking(db_session, teacher_user, script.id)
    assert processed.status == ScriptStatus.AI_MARKED
    answer = db_session.query(StudentQuestionAnswer).filter(StudentQuestionAnswer.script_id == script.id).one()
    assert answer.ai_proposed_score is not None
    assert answer.review_status.value == "PENDING"
    assert db_session.query(Score).filter(Score.student_id == student.id).count() == 0


def test_openai_response_parser_rejects_invalid_scores_and_non_numeric_types():
    provider = object.__new__(OpenAIProvider)
    provider.model = "gpt-4o-mini"
    provider.client = type("Client", (), {"responses": type("Responses", (), {"create": lambda self, **kwargs: type("Response", (), {"output_text": '{"question_id": 21, "score": 11, "max_marks": 10, "evidence": "too high", "confidence": 1, "extracted_text": "answer"}'})()})()})()
    question = {"id": 21, "question_type": "SUBJECTIVE", "maximum_marks": 10, "question_text": "Q", "expected_concepts": "A"}
    with pytest.raises(AIProviderResponseError):
        provider.evaluate_answer(question, "answer", [], {})
    provider.client.responses.create = lambda **kwargs: type("Response", (), {"output_text": '{"question_id": 21, "score": "ten", "max_marks": 10, "evidence": "invalid", "confidence": 1, "extracted_text": "answer"}'})()
    with pytest.raises(AIProviderResponseError):
        provider.evaluate_answer(question, "answer", [], {})


def test_all_four_assessment_components_use_ai_review_and_official_score_path(db_session, monkeypatch, tmp_path):
    from app.services import ai_marking_service
    monkeypatch.setattr(ai_marking_service, "get_ai_provider", MockAIProvider)
    school = School(name="Four Components Academy", email="four-components@example.com")
    db_session.add(school)
    db_session.flush()
    session = AcademicSession(school_id=school.id, name="2026/2027", is_current=True)
    school_class = SchoolClass(school_id=school.id, name="JSS 1")
    subject = Subject(school_id=school.id, name="Mathematics", code="MATH")
    db_session.add_all([session, school_class, subject])
    db_session.flush()
    term = Term(academic_session_id=session.id, name=TermName.FIRST, is_current=True)
    assessment_types = [
        AssessmentType(school_id=school.id, name="CA1", category=AssessmentCategory.CA, max_score=10, display_order=1),
        AssessmentType(school_id=school.id, name="CA2", category=AssessmentCategory.CA, max_score=10, display_order=2),
        AssessmentType(school_id=school.id, name="CA3", category=AssessmentCategory.CA, max_score=10, display_order=3),
        AssessmentType(school_id=school.id, name="Exam", category=AssessmentCategory.EXAM, max_score=70, display_order=4),
    ]
    db_session.add_all([term, ClassSubject(school_class_id=school_class.id, subject_id=subject.id), *assessment_types,
                        GradingScale(school_id=school.id, grade="A", min_score=80, max_score=100)])
    teacher_user = _make_user(db_session, school, "four-components-teacher@example.com")
    teacher = Teacher(school_id=school.id, user_id=teacher_user.id, first_name="Four", last_name="Components")
    student = Student(school_id=school.id, admission_number="FC001", first_name="Ada", last_name="Student")
    db_session.add_all([teacher, student])
    db_session.flush()
    db_session.add_all([
        StudentClass(student_id=student.id, school_class_id=school_class.id, academic_session_id=session.id),
        TeacherAssignment(teacher_id=teacher.id, school_class_id=school_class.id, subject_id=subject.id),
    ])
    exam = Examination(school_id=school.id, academic_session_id=session.id, term_id=term.id,
        school_class_id=school_class.id, subject_id=subject.id, created_by_id=teacher_user.id,
        title="Shared assessment question set", maximum_score=70)
    db_session.add(exam)
    db_session.flush()
    question = ExaminationQuestion(examination_id=exam.id, question_number="1", question_text="Choose the correct answer.",
        question_type=QuestionType.OBJECTIVE, maximum_marks=10, display_order=1, correct_option="B")
    db_session.add(question)
    script_file = tmp_path / "answer.txt"
    script_file.write_text("B", encoding="utf-8")
    db_session.commit()

    for assessment in assessment_types:
        script = StudentExaminationScript(school_id=school.id, examination_id=exam.id, student_id=student.id,
            assessment_type_id=assessment.id, original_file_path=str(script_file), original_filename="answer.txt",
            content_type="text/plain", status=ScriptStatus.UPLOADED)
        db_session.add(script)
        db_session.commit()
        processed = examination_service.process_ai_marking(db_session, teacher_user, script.id)
        answer = db_session.query(StudentQuestionAnswer).filter(StudentQuestionAnswer.script_id == script.id).one()
        assert processed.status == ScriptStatus.AI_MARKED
        assert float(answer.ai_proposed_score) == 10
        assert answer.teacher_final_score is None
        assert db_session.query(Score).filter(Score.student_id == student.id, Score.assessment_type_id == assessment.id).count() == 0

        examination_service.update_mark(db_session, teacher_user, answer.id, MarkReviewUpdate(teacher_final_score=8, teacher_review_notes="Adjusted after review"))
        assert answer.review_status.value == "REVIEWED"
        examination_service.approve_script(db_session, teacher_user, script.id, assessment_type_id=assessment.id)
        score = db_session.query(Score).filter(Score.student_id == student.id, Score.assessment_type_id == assessment.id).one()
        assert float(score.value) == 8
        examination_service.approve_script(db_session, teacher_user, script.id, assessment_type_id=assessment.id)
        assert db_session.query(Score).filter(Score.student_id == student.id, Score.assessment_type_id == assessment.id).count() == 1

        from types import SimpleNamespace
    result = db_session.query(__import__("app.models.result", fromlist=["Result"]).Result).filter_by(
        student_id=student.id, subject_id=subject.id, term_id=term.id
    ).one()
    assert float(result.ca_total) == 24
    assert float(result.exam_score) == 8
    assert float(result.total) == 32

