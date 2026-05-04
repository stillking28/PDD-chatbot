from pydantic import BaseModel, Field


class PddClause(BaseModel):
    clause_id: str
    topic: str
    language: str = "ru"
    raw_text: str
    official_url: str
    diagram_url: str


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2)
    language: str = "ru"
    show_source: bool = False


class TieredAnswer(BaseModel):
    short_answer: str
    simple_explanation: str
    source_clause_id: str
    source_url: str
    source_raw_text: str | None = None
    diagram_url: str | None = None
    blocked_by_guardrail: bool = False
    guardrail_reason: str | None = None
