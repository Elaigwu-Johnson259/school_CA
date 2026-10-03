from __future__ import annotations

import logging
import math
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentType
from app.models.enums import AssessmentCategory, UserRole
from app.models.examination import ExaminationQuestion, QuestionType, ReviewStatus, ScriptStatus, StudentExaminationScript, StudentQuestionAnswer
from app.models.user import User
from app.services.ai_provider import AIProviderConfigurationError, AIProviderError, AIProviderResponseError, AIProposal, ExtractedAnswer, get_ai_provider

logger = logging.getLogger(__name__)


def process_ai_marking(db: Session, current_user: User, script_id: int, assessment_type_id: int | None = None) -> StudentExaminationScript:
    """Processes a submitted script with the configured AI provider and stores pending teacher reviews."""
    script = db.get(StudentExaminationScript, script_id)
    if script is None:
        raise HTTPException(status_code=404, detail="Student script not found")
    if current_user.role not in {UserRole.SCHOOL_ADMIN, UserRole.TEACHER, UserRole.SUPER_ADMIN}:
        raise HTTPException(status_code=403, detail="Only staff may process AI marking")
    from app.services.examination_service import _get_exam

    exam = _get_exam(db, current_user, script.examination_id)
    selected_assessment_id = assessment_type_id or script.assessment_type_id
    if selected_assessment_id is None:
        raise HTTPException(status_code=400, detail="Select an assessment type before processing this script")
    assessment_type = db.get(AssessmentType, selected_assessment_id)
    if assessment_type is None or assessment_type.school_id != exam.school_id:
        raise HTTPException(status_code=404, detail="Assessment type not found")
    if assessment_type.category not in {AssessmentCategory.CA, AssessmentCategory.EXAM}:
        raise HTTPException(status_code=400, detail="Only CA and Exam assessment types can be marked")
    if script.assessment_type_id not in {None, assessment_type.id}:
        raise HTTPException(status_code=409, detail="Assessment type does not match the uploaded script")
    if script.status == ScriptStatus.APPROVED:
        raise HTTPException(status_code=409, detail="This script has already been approved")
    if script.status in {ScriptStatus.PROCESSING, ScriptStatus.AI_MARKED, ScriptStatus.TEACHER_REVIEW}:
        raise HTTPException(status_code=409, detail="This script has already been processed")
    if script.status not in {ScriptStatus.UPLOADED, ScriptStatus.PROCESSING_FAILED, ScriptStatus.MARKING_FAILED}:
        raise HTTPException(status_code=409, detail="This script is not in a processable state")

    questions = db.query(ExaminationQuestion).filter(ExaminationQuestion.examination_id == exam.id).order_by(ExaminationQuestion.display_order).all()
    if not questions:
        raise HTTPException(status_code=400, detail="This examination has no questions to mark")
    existing_answers = {
        answer.question_id: answer
        for answer in db.query(StudentQuestionAnswer).filter(StudentQuestionAnswer.script_id == script.id).all()
    }
    question_data = [{
        "id": question.id,
        "question_number": question.question_number,
        "question_text": question.question_text,
    } for question in questions]

    try:
        provider = get_ai_provider()
        script.status = ScriptStatus.PROCESSING
        script.processing_error = None
        db.commit()
        extracted = provider.extract_script_answers(script.original_file_path, script.content_type, question_data)
        proposals: dict[int, tuple[str, ExtractedAnswer | None, AIProposal | None]] = {}
        for question in questions:
            existing = existing_answers.get(question.id)
            extraction = extracted.get(question.id)
            student_text = (existing.extracted_text if existing and existing.extracted_text else extraction.text if extraction else "").strip()
            if not student_text:
                proposals[question.id] = (student_text, extraction, None)
                continue

            maximum = float(question.maximum_marks)
            if question.question_type == QuestionType.OBJECTIVE:
                normalize_option = lambda value: "".join(char for char in value.upper().strip() if char.isalnum())
                correct = normalize_option(question.correct_option or "")
                selected = normalize_option(student_text)
                score = maximum if correct and selected == correct else 0.0
                evidence = "Configured objective answer matched." if score else "Answer did not match the configured objective answer."
                proposal = AIProposal(score=score, max_marks=maximum, evidence=evidence, confidence=1.0, extracted_text=student_text)
            else:
                proposal = provider.evaluate_answer(
                    question={
                        "id": question.id,
                        "question_type": question.question_type.value,
                        "maximum_marks": maximum,
                        "correct_option": question.correct_option,
                        "question_text": question.question_text,
                        "marking_guidance": question.marking_guidance,
                        "expected_concepts": question.expected_concepts,
                        "acceptable_alternatives": question.acceptable_alternatives,
                    },
                    student_answer=student_text,
                    reference_materials=list(question.references),
                    context={"script_id": script.id, "exam_id": exam.id, "assessment_type_id": assessment_type.id},
                )
            if not math.isfinite(float(proposal.score)) or proposal.score < 0 or proposal.score > maximum:
                raise AIProviderResponseError("The AI provider returned a score outside the question maximum.")
            if proposal.max_marks != maximum or not proposal.evidence:
                raise AIProviderResponseError("The AI provider returned an incomplete marking proposal.")
            proposals[question.id] = (student_text, extraction, proposal)
    except AIProviderConfigurationError as exc:
        logger.warning("AI provider configuration error while processing script %s", script.id)
        script.status = ScriptStatus.PROCESSING_FAILED
        script.processing_error = "AI marking is not configured. Contact your administrator."
        db.commit()
        raise HTTPException(status_code=503, detail=script.processing_error) from exc
    except (AIProviderError, OSError) as exc:
        logger.exception("AI provider failed while processing script %s", script.id)
        script.status = ScriptStatus.MARKING_FAILED
        script.processing_error = "AI marking could not process this script. Review the file or try again later."
        db.commit()
        raise HTTPException(status_code=502, detail=script.processing_error) from exc
    except Exception as exc:
        logger.exception("Unexpected marking failure for script %s", script.id)
        script.status = ScriptStatus.MARKING_FAILED
        script.processing_error = "AI marking could not process this script. Review the file or try again later."
        db.commit()
        raise HTTPException(status_code=502, detail=script.processing_error) from exc

    for question in questions:
        answer = existing_answers.get(question.id)
        if answer is None:
            answer = StudentQuestionAnswer(script_id=script.id, question_id=question.id)
            db.add(answer)
        student_text, extraction, proposal = proposals[question.id]
        answer.extracted_text = student_text
        answer.original_answer_image_path = script.original_file_path
        answer.extraction_status = "NEEDS_REVIEW" if extraction is None or extraction.needs_review else "EXTRACTED"
        if proposal is None:
            answer.ai_proposed_score = None
            answer.ai_evidence = "No answer could be confidently mapped to this question; teacher input is required."
            answer.ai_confidence = float(extraction.confidence) if extraction and extraction.confidence is not None else None
        else:
            answer.ai_proposed_score = proposal.score
            answer.ai_evidence = proposal.evidence
            answer.ai_confidence = proposal.confidence
        answer.teacher_final_score = None
        answer.teacher_adjustment = None
        answer.teacher_review_notes = None
        answer.review_status = ReviewStatus.PENDING

    script.status = ScriptStatus.AI_MARKED
    script.processed_at = datetime.now(timezone.utc)
    script.assessment_type_id = assessment_type.id
    script.processing_error = None
    db.commit()
    db.refresh(script)
    return script
