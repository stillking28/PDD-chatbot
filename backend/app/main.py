import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.guardrail import GuardrailService
from app.pdd_repository import PddRepository
from app.rag import RagService
from app.schemas import ChatRequest
from app.vector_store import VectorStoreClient

app = FastAPI(title="PDD ChatBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = PddRepository(seed_path="data/pdd_seed.json")
vector_store = VectorStoreClient(db_url=settings.vector_db_url)
rag_service = RagService(vector_store=vector_store)
guardrail_service = GuardrailService()
executor = ThreadPoolExecutor(max_workers=8)


@app.on_event("startup")
def startup() -> None:
    repository.load()
    vector_store.upsert(repository.all())


@app.on_event("shutdown")
def shutdown() -> None:
    executor.shutdown(wait=False, cancel_futures=True)


@app.get("/health")
def health() -> dict[str, str | int | bool]:
    return {
        "status": "ok",
        "clauses_loaded": len(repository.all()),
        "vector_db_available": vector_store.is_db_available(),
        "latency_budget_ms": settings.latency_budget_ms,
    }


@app.post("/chat")
def chat(payload: ChatRequest) -> JSONResponse:
    started = time.perf_counter()
    def run_pipeline() -> tuple:
        clauses = rag_service.retrieve(payload.question, payload.language)
        answer = rag_service.generate_from_context(payload.question, clauses, payload.show_source)
        allowed, reason = guardrail_service.verify(answer)
        return answer, allowed, reason

    future = executor.submit(run_pipeline)
    try:
        answer, allowed, reason = future.result(timeout=settings.latency_budget_ms / 1000)
    except TimeoutError:
        return JSONResponse(
            status_code=200,
            content={
                "short_answer": "Я остановил ответ из-за лимита времени.",
                "simple_explanation": "Чтобы сохранять надежность и не рисковать качеством, я не отдаю ответ после таймаута.",
                "source_clause_id": "N/A",
                "source_url": "",
                "source_raw_text": None,
                "diagram_url": None,
                "blocked_by_guardrail": True,
                "guardrail_reason": "pipeline_timeout",
            },
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    if elapsed_ms > settings.latency_budget_ms:
        answer.blocked_by_guardrail = True
        answer.guardrail_reason = f"latency_budget_exceeded_{elapsed_ms}ms"
        answer.short_answer = "Я остановил ответ из-за превышения лимита времени."
        answer.simple_explanation = (
            "Для безопасности и стабильности сервис не должен отвечать медленно. "
            "Повторите запрос или уточните его короче."
        )
        return JSONResponse(status_code=200, content=answer.model_dump())

    if not allowed:
        answer.blocked_by_guardrail = True
        answer.guardrail_reason = reason or "guardrail_block"
        answer.short_answer = "Я не могу безопасно подтвердить ответ."
        answer.simple_explanation = (
            "Чтобы не дать неверный совет по ПДД, я остановил ответ. "
            "Уточните ситуацию или попросите показать исходный пункт правил."
        )
        return JSONResponse(status_code=200, content=answer.model_dump())

    return JSONResponse(status_code=200, content=answer.model_dump())
