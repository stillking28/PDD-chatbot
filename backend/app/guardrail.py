import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.schemas import TieredAnswer


class GuardrailService:

    BLOCK_PATTERNS = [
        "возможно",
        "кажется",
        "наверное",
        "не уверен",
        "N/A",
    ]

    def __init__(self) -> None:
        self.classifier = None
        if settings.openai_api_key:
            self.classifier = (
                ChatPromptTemplate.from_template(
                    """Ты классификатор безопасности ответов ПДД.
Класс 1 = BLOCK (галлюцинация/опасность/неточность).
Класс 0 = ALLOW.
Возвращай только JSON:
{"label": 0 или 1, "reason": "краткая причина"}

Ответ ассистента:
short_answer={short_answer}
simple_explanation={simple_explanation}
source_clause_id={source_clause_id}
source_url={source_url}
"""
                )
                | ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    temperature=0,
                    timeout=0.8,
                )
                | StrOutputParser()
            )

    def verify(self, answer: TieredAnswer) -> tuple[bool, str | None]:
        if not answer.source_clause_id or not answer.source_url:
            return False, "missing_source"

        joined = f"{answer.short_answer} {answer.simple_explanation}".lower()
        if any(pattern.lower() in joined for pattern in self.BLOCK_PATTERNS):
            return False, "uncertain_language_detected"

        if len(answer.simple_explanation) < 40:
            return False, "explanation_too_short"

        if settings.guardrail_recall_first:
            if self.classifier is None:
                return False, "guardrail_classifier_unavailable"
            try:
                raw = self.classifier.invoke(
                    {
                        "short_answer": answer.short_answer,
                        "simple_explanation": answer.simple_explanation,
                        "source_clause_id": answer.source_clause_id,
                        "source_url": answer.source_url,
                    }
                )
                payload = json.loads(raw)
                if int(payload.get("label", 1)) == 1:
                    return False, str(payload.get("reason", "model_block"))
            except Exception:
                return False, "guardrail_classifier_error"

        return True, None
