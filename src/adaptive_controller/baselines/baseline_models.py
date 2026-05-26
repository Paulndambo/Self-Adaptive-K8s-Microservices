from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BaselineAction(str, Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_OP = "no_op"


class BaselineDecision(BaseModel):
    controller_name: str
    service_name: str
    action: BaselineAction
    current_replicas: int
    target_replicas: int
    reason: str
    generated_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @property
    def changes_replicas(self) -> bool:
        return self.current_replicas != self.target_replicas


class BaselineRunResult(BaseModel):
    controller_name: str
    namespace: str
    decisions: list[BaselineDecision] = Field(default_factory=list)

    @property
    def has_actions(self) -> bool:
        return any(decision.action != BaselineAction.NO_OP for decision in self.decisions)
