from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "PDD ChatBot API"
    llm_provider: str = "groq"
    groq_api_key: str | None = None
    groq_model: str = "mixtral-8x7b-32768"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    embeddings_model: str = "text-embedding-3-small"
    vector_db_url: str | None = None
    vector_collection_name: str = "pdd_clauses"
    top_k: int = 3
    latency_budget_ms: int = 3000
    # Hard safety behavior: block if uncertainty is detected.
    guardrail_recall_first: bool = True


settings = Settings()
