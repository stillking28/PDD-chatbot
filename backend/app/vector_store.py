from collections import Counter
from typing import Iterable

from psycopg import connect
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from app.config import settings
from app.schemas import PddClause


class VectorStoreClient:
    def __init__(self, db_url: str | None = None) -> None:
        self._rows: list[PddClause] = []
        self.db_url = db_url
        self._pgvector: PGVector | None = None

    def upsert(self, clauses: Iterable[PddClause]) -> None:
        self._rows = list(clauses)
        if self.is_db_available() and settings.openai_api_key:
            self._ensure_pgvector_collection()
            if self._pgvector is not None:
                docs = [
                    Document(
                        page_content=clause.raw_text,
                        metadata={
                            "clause_id": clause.clause_id,
                            "topic": clause.topic,
                            "language": clause.language,
                            "official_url": clause.official_url,
                            "diagram_url": clause.diagram_url,
                        },
                    )
                    for clause in self._rows
                ]
                ids = [clause.clause_id for clause in self._rows]
                self._pgvector.add_documents(docs, ids=ids)

    def is_db_available(self) -> bool:
        if not self.db_url:
            return False
        try:
            with connect(self.db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True
        except Exception:
            return False

    def _ensure_pgvector_collection(self) -> None:
        if not self.db_url:
            return
        if self._pgvector is not None:
            return

        with connect(self.db_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()

        embeddings = OpenAIEmbeddings(model=settings.embeddings_model, api_key=settings.openai_api_key)
        self._pgvector = PGVector(
            embeddings=embeddings,
            collection_name=settings.vector_collection_name,
            connection=self.db_url,
            use_jsonb=True,
        )

    def query(self, text: str, top_k: int = 3) -> list[PddClause]:
        if self.is_db_available() and settings.openai_api_key:
            self._ensure_pgvector_collection()
            if self._pgvector is not None:
                docs = self._pgvector.similarity_search(query=text, k=top_k)
                return [self._to_clause(doc) for doc in docs]

        # Lexical fallback: match clause_id first if exact match found
        query_lower = text.lower()
        for row in self._rows:
            if row.clause_id.lower() in query_lower or query_lower in row.clause_id.lower():
                return [row]

        # Otherwise, use keyword overlap scoring
        query_tokens = Counter(text.lower().split())

        scored: list[tuple[int, PddClause]] = []
        for row in self._rows:
            clause_text = f"{row.topic} {row.raw_text}".lower()
            clause_tokens = Counter(clause_text.split())
            overlap = sum((query_tokens & clause_tokens).values())
            
            # Bonus for keyword matches
            if "пешеход" in query_lower and "пешеход" in clause_text:
                overlap += 10
            if "поворот" in query_lower and "поворот" in clause_text:
                overlap += 10
            if "положение" in query_lower and "положение" in clause_text:
                overlap += 10
            if "светофор" in query_lower and "светофор" in clause_text:
                overlap += 10
                
            scored.append((overlap, row))

        scored.sort(key=lambda x: x[0], reverse=True)
        # RAG guard: if no overlap, return empty and refuse generation later.
        if not scored or scored[0][0] == 0:
            return []
        return [item[1] for item in scored[:top_k]]

    @staticmethod
    def _to_clause(doc: Document) -> PddClause:
        return PddClause(
            clause_id=str(doc.metadata.get("clause_id", "N/A")),
            topic=str(doc.metadata.get("topic", "")),
            language=str(doc.metadata.get("language", "ru")),
            raw_text=doc.page_content,
            official_url=str(doc.metadata.get("official_url", "")),
            diagram_url=str(doc.metadata.get("diagram_url", "")),
        )
