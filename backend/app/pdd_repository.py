import json
from pathlib import Path

from app.schemas import PddClause


class PddRepository:
    def __init__(self, seed_path: str) -> None:
        self.seed_path = Path(seed_path)
        self._clauses: list[PddClause] = []

    def load(self) -> None:
        payload = json.loads(self.seed_path.read_text(encoding="utf-8"))
        self._clauses = [PddClause(**item) for item in payload]

    def all(self) -> list[PddClause]:
        return self._clauses
