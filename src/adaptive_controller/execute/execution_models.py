from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from adaptive_controller.plan import AdaptationPlan


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExecutionStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionResult(BaseModel):
    plan: AdaptationPlan
    status: ExecutionStatus
    message: str
    executed_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return self.status == ExecutionStatus.SUCCEEDED


class ExecutionReport(BaseModel):
    namespace: str
    executed_at: datetime = Field(default_factory=utc_now)
    results: list[ExecutionResult] = Field(default_factory=list)

    @property
    def all_succeeded(self) -> bool:
        return all(result.succeeded for result in self.results)
