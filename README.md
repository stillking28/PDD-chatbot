# PDD ChatBot

RAG-first traffic-rules assistant focused on safe, source-grounded responses from official PDD clauses only.

## Structure

- `backend`: FastAPI API with retrieval, guardrail, and seed data.
- `frontend`: Next.js chat client with fixed 3-tier answer format and `Show Source` toggle.

## Docker run (recommended)

```bash
cp .env.example .env
docker compose up --build
```

After startup:
- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

Notes:
- `db` runs Postgres + pgvector.
- `backend` ingests `data/pdd_seed.json` on container startup.
- Add `OPENAI_API_KEY` in `.env` for LLM generation and model-based guardrail.

## Backend quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
psql "$VECTOR_DB_URL" -f sql/init_pgvector.sql
python -m app.ingest_pgvector
uvicorn app.main:app --reload --port 8000
```

## Frontend quick start

```bash
cd frontend
npm install
npm run dev
```

## Safety and product constraints implemented

- RAG-only answers from `data/pdd_seed.json`.
- LangChain retrieval wired to pgvector (`langchain-postgres`), with lexical fallback for local-only mode.
- Guardrail middleware is binary hybrid:
  - Rule-based high-recall blocker
  - LLM classifier (BLOCK/ALLOW) with recall-first fail-closed behavior
- Recall-first safety policy (over-blocking accepted).
- Latency budget control (`LATENCY_BUDGET_MS`, default 3000ms): response is blocked if budget is exceeded.
- TTL caches for frequent questions (retrieval + answer caching).
- Three-tier response contract:
  - Level 1: Short answer
  - Level 2: Simple explanation (logic-first wording)
  - Level 3: Official clause citation
- `Show Source` toggle in UI to reveal raw legal text.
- Static diagram linkage per clause (`diagram_url`), no generated images.
