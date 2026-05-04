from app.config import settings
from app.pdd_repository import PddRepository
from app.vector_store import VectorStoreClient


def main() -> None:
    repository = PddRepository(seed_path="data/pdd_seed.json")
    repository.load()

    store = VectorStoreClient(db_url=settings.vector_db_url)
    store.upsert(repository.all())

    print(f"Ingested {len(repository.all())} clauses into vector store.")
    print(f"DB available: {store.is_db_available()}")


if __name__ == "__main__":
    main()
