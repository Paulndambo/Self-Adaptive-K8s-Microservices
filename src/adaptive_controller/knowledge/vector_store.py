from __future__ import annotations

from pathlib import Path
from typing import Any

from adaptive_controller.knowledge.repositories.jsonl_repository import JsonlRepository


class VectorStore:
    def __init__(self, storage_dir: str | Path):
        self.repository = JsonlRepository(Path(storage_dir) / "retrieval_context.jsonl")

    def add_text(
        self,
        document_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.repository.append(
            {
                "document_id": document_id,
                "text": text,
                "metadata": metadata or {},
            }
        )

    def search_text(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        terms = {term.lower() for term in query.split() if term.strip()}
        scored = []
        for record in self.repository.list():
            text = str(record.get("text", "")).lower()
            score = sum(1 for term in terms if term in text)
            if score:
                scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [record for _, record in scored[:limit]]
