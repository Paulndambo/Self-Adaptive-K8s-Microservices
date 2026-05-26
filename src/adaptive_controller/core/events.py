from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ControlLoopStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ControlLoopRun(BaseModel):
    run_id: str
    status: ControlLoopStatus
    started_at: datetime
    finished_at: datetime = Field(default_factory=utc_now)
    namespace: str
    services: list[str] = Field(default_factory=list)
    error: str | None = None
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @property
    def duration_seconds(self) -> float:
        return max(0.0, (self.finished_at - self.started_at).total_seconds())
