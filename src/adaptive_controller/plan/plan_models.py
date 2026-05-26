from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AdaptationAction(str, Enum):
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    NO_OP = "no_op"
    CONFIG_CHANGE = "config_change"


class PlanPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AdaptationPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    service_name: str
    action: AdaptationAction
    priority: PlanPriority
    reason: str
    current_replicas: int | None = None
    target_replicas: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    source_findings: list[str] = Field(default_factory=list)
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)

    @property
    def changes_replicas(self) -> bool:
        return (
            self.action in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}
            and self.current_replicas is not None
            and self.target_replicas is not None
            and self.current_replicas != self.target_replicas
        )


class PlanBatch(BaseModel):
    namespace: str
    generated_at: datetime = Field(default_factory=utc_now)
    plans: list[AdaptationPlan] = Field(default_factory=list)

    @property
    def has_actions(self) -> bool:
        return any(plan.action != AdaptationAction.NO_OP for plan in self.plans)
