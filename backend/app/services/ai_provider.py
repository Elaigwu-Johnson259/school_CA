from __future__ import annotations

import base64
import json
import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from app.core.config import settings


class AIProviderConfigurationError(RuntimeError):
    """Raised when the selected AI provider has not been configured correctly."""


class AIProviderError(RuntimeError):
    """Raised when a configured provider cannot complete a valid request."""


class AIProviderResponseError(AIProviderError):
    """Raised when a provider response is malformed or outside the allowed rubric."""


@dataclass
class AIProposal:
    score: float
    max_marks: float
    evidence: str
    confidence: float | None = None
    extracted_text: str | None = None


@dataclass
class ExtractedAnswer:
    text: str
    confidence: float | None
    needs_review: bool


def _number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AIProviderResponseError(f"AI response field '{field_name}' must be numeric.")
    result = float(value)
    if not math.isfinite(result):
        raise AIProviderResponseError(f"AI response field '{field_name}' must be finite.")
    return result


class BaseAIProvider(ABC):
    @abstractmethod
    def evaluate_answer(self, question: dict[str, Any], student_answer: str, reference_materials: Iterable[Any], context: dict[str, Any]) -> AIProposal:
        raise NotImplementedError

    @abstractmethod
    def extract_script_answers(self, file_path: str, mime_type: str | None, questions: list[dict[str, Any]]) -> dict[int, ExtractedAnswer]:
        raise NotImplementedError


class MockAIProvider(BaseAIProvider):
    """A deterministic provider used for tests and local validation of the marking workflow."""

    def evaluate_answer(self, question: dict[str, Any], student_answer: str, reference_materials: Iterable[Any], context: dict[str, Any]) -> AIProposal:
        maximum = float(question.get("maximum_marks") or 0)
        question_type = getattr(question.get("question_type"), "value", question.get("question_type"))
        question_type_name = str(question_type).upper()
        student_response = (student_answer or "").strip()
        lower_response = student_response.lower()

        if question_type_name == "OBJECTIVE":
            correct_option = str(question.get("correct_option") or "").upper()
            if correct_option and student_response.upper() == correct_option:
                return AIProposal(score=maximum, max_marks=maximum, evidence=f"Correct option selected: {correct_option}.", confidence=0.99)
            return AIProposal(score=0.0, max_marks=maximum, evidence=f"Student answer did not match the correct option {correct_option}.", confidence=0.95)

        expected = (question.get("expected_concepts") or "").strip().lower()
        alternatives = (question.get("acceptable_alternatives") or "").strip().lower()
        reference_text = " ".join(
            getattr(material, "text_content", "") or "" for material in reference_materials
        ).lower()
        rubric_phrases = [phrase for phrase in (expected, alternatives, reference_text) if phrase]
        if student_response and any(
            " ".join(phrase.split()) in " ".join(lower_response.split())
            for phrase in rubric_phrases
        ):
            return AIProposal(score=maximum, max_marks=maximum, evidence="Exact rubric phrase matched (mock provider).", confidence=1.0, extracted_text=student_response)
        return AIProposal(score=0.0, max_marks=maximum, evidence="Mock provider does not perform semantic evaluation; teacher review required.", confidence=0.0, extracted_text=student_response)

    def extract_script_answers(self, file_path: str, mime_type: str | None, questions: list[dict[str, Any]]) -> dict[int, ExtractedAnswer]:
        target = Path(file_path)
        if not target.is_file():
            raise AIProviderError("Uploaded script file is unavailable.")
        if mime_type not in {"text/plain", "text/markdown"} and target.suffix.lower() not in {".txt", ".md"}:
            raise AIProviderError("Mock provider cannot extract scanned scripts. Configure the OpenAI provider for document vision.")
        text = target.read_text(encoding="utf-8")
        if len(questions) == 1:
            return {int(questions[0]["id"]): ExtractedAnswer(text=text, confidence=0.0, needs_review=True)}
        matched: dict[int, list[str]] = {}
        current_question_id: int | None = None
        number_to_id = {str(question["question_number"]): int(question["id"]) for question in questions}
        for line in text.splitlines():
            match = re.match(r"^\s*(?:Q(?:uestion)?\s*)?([\w-]+)[).:\-\s]+(.*)$", line, re.IGNORECASE)
            if match and match.group(1) in number_to_id:
                current_question_id = number_to_id[match.group(1)]
                matched.setdefault(current_question_id, []).append(match.group(2))
            elif current_question_id is not None:
                matched[current_question_id].append(line)
        return {
            question_id: ExtractedAnswer(text="\n".join(lines).strip(), confidence=0.0, needs_review=True)
            for question_id, lines in matched.items()
            if "\n".join(lines).strip()
        }


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or settings.AI_API_KEY
        self.model = model or settings.OPENAI_MODEL or settings.AI_MODEL
        self.base_url = base_url or settings.OPENAI_BASE_URL or settings.AI_BASE_URL
        if not self.api_key:
            raise AIProviderConfigurationError("OpenAI provider requires OPENAI_API_KEY or AI_API_KEY.")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise AIProviderConfigurationError("The openai package is required to use the OpenAI provider.") from exc
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def _request_json(self, prompt: str, document: dict[str, str] | list[dict[str, str]] | None = None) -> dict[str, Any]:
        content: list[dict[str, str]] = [{"type": "input_text", "text": prompt}]
        documents = [document] if isinstance(document, dict) else document or []
        for item in documents:
            if item["kind"] == "pdf":
                content.append({"type": "input_file", "filename": item["filename"], "file_data": item["data_url"]})
            else:
                content.append({"type": "input_image", "image_url": item["data_url"]})
        try:
            response = self.client.responses.create(
                model=self.model,
                input=[{"role": "user", "content": content}],
                text={"format": {"type": "json_object"}},
            )
        except Exception as exc:
            raise AIProviderError("The AI provider could not process this request.") from exc
        try:
            data = json.loads(response.output_text)
        except (AttributeError, TypeError, json.JSONDecodeError) as exc:
            raise AIProviderResponseError("The AI provider returned an invalid response.") from exc
        if not isinstance(data, dict):
            raise AIProviderResponseError("The AI provider response must be a JSON object.")
        return data

    def extract_script_answers(self, file_path: str, mime_type: str | None, questions: list[dict[str, Any]]) -> dict[int, ExtractedAnswer]:
        target = Path(file_path)
        if not target.is_file():
            raise AIProviderError("Uploaded script file is unavailable.")
        mime = (mime_type or "").lower()
        extension = target.suffix.lower()
        if mime == "application/pdf" or extension == ".pdf":
            kind, normalized_mime = "pdf", "application/pdf"
        elif mime in {"image/jpeg", "image/png"} or extension in {".jpg", ".jpeg", ".png"}:
            kind = "image"
            normalized_mime = mime if mime in {"image/jpeg", "image/png"} else {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}[extension]
        elif mime.startswith("text/") or extension in {".txt", ".md"}:
            text = target.read_text(encoding="utf-8")
            question_payload = [{"id": item["id"], "number": item["question_number"], "text": item["question_text"]} for item in questions]
            prompt = (
                "Map the typed script text to the supplied question IDs. Use explicit numbering and context; "
                "do not copy the same answer to multiple questions or invent missing answers. Omit uncertain mappings. "
                "Return JSON as {\"answers\":[{\"question_id\":integer,\"answer\":string,\"confidence\":number}]} . "
                f"Questions: {json.dumps(question_payload)}\nScript text:\n{text}"
            )
            data = self._request_json(prompt)
            return self._parse_extracted_answers(data, questions)
        else:
            raise AIProviderError("Unsupported script file type. Upload a PDF, JPG, JPEG, or PNG.")
        encoded = base64.b64encode(target.read_bytes()).decode("ascii")
        question_payload = [{"id": item["id"], "number": item["question_number"], "text": item["question_text"]} for item in questions]
        prompt = (
            "Read every page of this student script and map visible answer content to the supplied question IDs. "
            "Do not invent, infer, or copy an answer across questions. If an answer cannot be mapped confidently, "
            "omit it. Return JSON only as {\"answers\":[{\"question_id\":integer,\"answer\":string,\"confidence\":number}]} . "
            f"Questions: {json.dumps(question_payload)}"
        )
        data = self._request_json(prompt, {"kind": kind, "filename": target.name, "data_url": f"data:{normalized_mime};base64,{encoded}"})
        return self._parse_extracted_answers(data, questions)

    @staticmethod
    def _parse_extracted_answers(data: dict[str, Any], questions: list[dict[str, Any]]) -> dict[int, ExtractedAnswer]:
        raw_answers = data.get("answers")
        if not isinstance(raw_answers, list):
            raise AIProviderResponseError("The AI provider did not return a question-answer list.")
        known_ids = {int(question["id"]) for question in questions}
        results: dict[int, ExtractedAnswer] = {}
        for item in raw_answers:
            if not isinstance(item, dict) or type(item.get("question_id")) is not int or item["question_id"] not in known_ids:
                raise AIProviderResponseError("The AI provider returned an unknown question identifier.")
            question_id = item["question_id"]
            if question_id in results or not isinstance(item.get("answer"), str):
                raise AIProviderResponseError("The AI provider returned a duplicate or invalid answer.")
            confidence = _number(item["confidence"], "confidence") if "confidence" in item else None
            if confidence is not None and not 0 <= confidence <= 1:
                raise AIProviderResponseError("The AI provider returned invalid extraction confidence.")
            text = item["answer"].strip()
            results[question_id] = ExtractedAnswer(text=text, confidence=confidence, needs_review=not text or confidence is None or confidence < 0.7)
        return results

    def evaluate_answer(self, question: dict[str, Any], student_answer: str, reference_materials: Iterable[Any], context: dict[str, Any]) -> AIProposal:
        question_text = question.get("question_text") or ""
        reference_lines = []
        reference_documents: list[dict[str, str]] = []
        for material in reference_materials or []:
            if getattr(material, "text_content", None):
                reference_lines.append(material.text_content)
            path = getattr(material, "original_file_path", None)
            content_type = (getattr(material, "content_type", None) or "").lower()
            if path and (content_type == "application/pdf" or content_type in {"image/jpeg", "image/png"}):
                reference_path = Path(path)
                if not reference_path.is_file():
                    raise AIProviderError("A configured marking reference file is unavailable.")
                encoded_reference = base64.b64encode(reference_path.read_bytes()).decode("ascii")
                reference_documents.append({
                    "kind": "pdf" if content_type == "application/pdf" else "image",
                    "filename": getattr(material, "original_filename", None) or reference_path.name,
                    "data_url": f"data:{content_type};base64,{encoded_reference}",
                })
        guidance = question.get("marking_guidance") or ""
        expected_concepts = question.get("expected_concepts") or ""
        question_type = question.get("question_type")
        payload = {
            "question_id": question.get("id"),
            "question_type": question_type,
            "question_text": question_text,
            "student_answer": student_answer,
            "max_marks": float(question.get("maximum_marks") or 0),
            "correct_option": question.get("correct_option"),
            "expected_concepts": expected_concepts,
            "marking_guidance": guidance,
            "acceptable_alternatives": question.get("acceptable_alternatives") or "",
            "reference_materials": reference_lines,
        }
        data = self._request_json(
            "Mark the student's answer semantically using the complete rubric. Do not reward irrelevant overlap. "
            "Return JSON with the same integer question_id, numeric score, exact max_marks, nonempty evidence, "
            "numeric confidence in [0,1], and extracted_text. Do not exceed max_marks. Payload: " + json.dumps(payload),
            reference_documents,
        )
        if type(data.get("question_id")) is not int or data["question_id"] != payload["question_id"]:
            raise AIProviderResponseError("The AI provider response did not match the requested question.")
        score = _number(data.get("score"), "score")
        max_marks = _number(data.get("max_marks"), "max_marks")
        confidence = _number(data.get("confidence"), "confidence")
        evidence = data.get("evidence")
        extracted_text = data.get("extracted_text", student_answer)
        if not isinstance(evidence, str) or not evidence.strip() or not isinstance(extracted_text, str):
            raise AIProviderResponseError("The AI provider omitted required marking fields.")
        if max_marks != payload["max_marks"] or score < 0 or score > payload["max_marks"] or not 0 <= confidence <= 1:
            raise AIProviderResponseError("The AI provider returned marks outside the question rubric.")
        return AIProposal(score=score, max_marks=max_marks, evidence=evidence.strip(), confidence=confidence, extracted_text=extracted_text)


def validate_ai_provider_config(provider_name: str | None = None) -> str:
    selected = (provider_name or settings.AI_PROVIDER).strip().lower()
    if selected == "mock":
        return selected
    if selected == "openai":
        if not (settings.OPENAI_API_KEY or settings.AI_API_KEY):
            raise AIProviderConfigurationError("OpenAI provider requires OPENAI_API_KEY or AI_API_KEY to be set.")
        return selected
    raise AIProviderConfigurationError(
        f"Unsupported AI provider '{selected}'. Supported providers: mock, openai."
    )


class AIProviderFactory:
    @staticmethod
    def create(provider_name: str | None = None) -> BaseAIProvider:
        provider_value = validate_ai_provider_config(provider_name)
        try:
            if provider_value == "mock":
                return MockAIProvider()
            if provider_value == "openai":
                return OpenAIProvider()
        except AIProviderConfigurationError:
            raise
        except Exception as exc:
            raise AIProviderConfigurationError("AI provider configuration is invalid.") from exc
        raise AIProviderConfigurationError(f"Unknown provider selection: {provider_value}")


def get_ai_provider(provider_name: str | None = None) -> BaseAIProvider:
    return AIProviderFactory.create(provider_name)
