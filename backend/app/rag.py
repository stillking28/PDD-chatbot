import json
from cachetools import TTLCache

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.config import settings
from app.schemas import PddClause, TieredAnswer
from app.vector_store import VectorStoreClient


class RagService:
    def __init__(self, vector_store: VectorStoreClient) -> None:
        self.vector_store = vector_store
        self.cache = TTLCache(maxsize=500, ttl=600)
        self.answer_cache = TTLCache(maxsize=500, ttl=600)
        self.generator = None
        if settings.openai_api_key:
            self.generator = (
                ChatPromptTemplate.from_template(
                    """Ты — помощник по ПДД. Отвечай ТОЛЬКО на основе контекста.
Если в контексте нет точного правила, верни safe_block=true.
Сгенерируй JSON строго по схеме:
{{
  "short_answer": "короткий ответ",
  "simple_explanation": "простое объяснение уровня школьника с логикой почему",
  "source_clause_id": "id пункта",
  "safe_block": false
}}

Вопрос: {question}
Контекст: {context}
"""
                )
                | ChatOpenAI(
                    model=settings.openai_model,
                    api_key=settings.openai_api_key,
                    temperature=0,
                    timeout=1.2,
                )
                | StrOutputParser()
            )

    def retrieve(self, question: str, language: str = "ru") -> list[PddClause]:
        key = f"{language}:{question.strip().lower()}"
        cached_result = self.cache.get(key)
        if cached_result is not None:
            return cached_result

        # Language hook is kept to support multilingual filtering.
        _ = language
        result = self.vector_store.query(question, top_k=settings.top_k)
        self.cache[key] = result
        return result

    def generate_from_context(self, question: str, clauses: list[PddClause], show_source: bool) -> TieredAnswer:
        cache_key = f"{question.strip().lower()}:{show_source}"
        cached_answer = self.answer_cache.get(cache_key)
        if cached_answer is not None:
            return cached_answer

        if not clauses:
            blocked = TieredAnswer(
                short_answer="Я не нашел точный пункт ПДД для этого вопроса.",
                simple_explanation=(
                    "Чтобы не дать неверный совет, я отвечаю только по официальному тексту. "
                    "Уточните сценарий: кто куда поворачивает, есть ли светофор, знаки и пешеходы."
                ),
                source_clause_id="N/A",
                source_url="",
                source_raw_text=None,
                blocked_by_guardrail=True,
                guardrail_reason="no_retrieval_context",
            )
            self.answer_cache[cache_key] = blocked
            return blocked

        primary = clauses[0]
        short = "Нужно действовать по пункту ПДД."
        simple = "Я объясняю только на базе официального пункта, чтобы избежать ошибок."
        if self.generator is not None:
            context = "\n".join([f"{c.clause_id}: {c.raw_text}" for c in clauses])
            try:
                raw = self.generator.invoke({"question": question, "context": context})
                payload = json.loads(raw)
                if payload.get("safe_block") is True:
                    blocked = TieredAnswer(
                        short_answer="Я не могу безопасно подтвердить ответ.",
                        simple_explanation="В найденных пунктах нет достаточного основания для точного вывода по вашей ситуации.",
                        source_clause_id=primary.clause_id,
                        source_url=primary.official_url,
                        source_raw_text=primary.raw_text if show_source else None,
                        diagram_url=primary.diagram_url,
                        blocked_by_guardrail=True,
                        guardrail_reason="llm_safe_block",
                    )
                    self.answer_cache[cache_key] = blocked
                    return blocked
                short = str(payload.get("short_answer", short))
                simple = str(payload.get("simple_explanation", simple))
            except Exception:
                # Fallback remains source-grounded and conservative.
                short = "Нужно действовать строго по официальному пункту."
                simple = (
                    "По этому вопросу я опираюсь только на найденный пункт ПДД. "
                    "Если ситуация отличается деталями, лучше уточнить сценарий."
                )

        answer = TieredAnswer(
            short_answer=short,
            simple_explanation=simple,
            source_clause_id=primary.clause_id,
            source_url=primary.official_url,
            source_raw_text=primary.raw_text if show_source else None,
            diagram_url=primary.diagram_url,
        )
        self.answer_cache[cache_key] = answer
        return answer
