from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExperimentConfig(BaseModel):
    name: str
    controller: str
    workload: str = "sockshop"
    services: list[str] = Field(default_factory=lambda: ["front-end"])
    iterations: int = 1
    execute_actions: bool = False
    output_dir: str = "experiments/results/raw"
    current_replicas_by_service: dict[str, int] = Field(default_factory=dict)


class ExperimentRunRecord(BaseModel):
    experiment_name: str
    controller: str
    workload: str
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    iterations: int = 0
    status: str = "running"
    output_files: list[str] = Field(default_factory=list)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


def ensure_output_dir(path: str | Path) -> Path:
    output_dir = Path(path)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
