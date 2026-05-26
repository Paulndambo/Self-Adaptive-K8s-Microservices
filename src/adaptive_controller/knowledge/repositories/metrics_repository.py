from __future__ import annotations

from pathlib import Path

from adaptive_controller.knowledge.repositories.jsonl_repository import JsonlRepository
from adaptive_controller.monitor import MetricSnapshot


class MetricsRepository:
    def __init__(self, storage_dir: str | Path):
        self.repository = JsonlRepository(Path(storage_dir) / "metrics.jsonl")

    def save_snapshot(self, snapshot: MetricSnapshot) -> None:
        self.repository.append(snapshot.model_dump(mode="json"))

    def recent_snapshots(self, limit: int = 100) -> list[dict]:
        return self.repository.list(limit=limit)
