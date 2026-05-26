from __future__ import annotations

from pathlib import Path
from typing import Any

from adaptive_controller.knowledge.repositories.jsonl_repository import JsonlRepository


class ScenarioMemory:
    def __init__(self, storage_dir: str | Path):
        self.repository = JsonlRepository(Path(storage_dir) / "scenarios.jsonl")

    def remember(
        self,
        service_name: str,
        summary: str,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.repository.append(
            {
                "service_name": service_name,
                "summary": summary,
                "tags": tags or [],
                "metadata": metadata or {},
            }
        )

    def find_by_tag(self, tag: str, limit: int = 100) -> list[dict[str, Any]]:
        return [
            record
            for record in self.repository.list(limit=limit)
            if tag in record.get("tags", [])
        ]

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        return self.repository.list(limit=limit)
