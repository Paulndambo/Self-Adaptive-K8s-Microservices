from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TimeSeriesSample(BaseModel):
    timestamp: datetime
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


class ScalingEvent(BaseModel):
    timestamp: datetime
    service_name: str
    from_replicas: int
    to_replicas: int
    controller_name: str

    @property
    def replica_delta(self) -> int:
        return self.to_replicas - self.from_replicas


class AdaptationWindow(BaseModel):
    detected_at: datetime
    executed_at: datetime
    service_name: str

    @property
    def latency_seconds(self) -> float:
        return max(0.0, (self.executed_at - self.detected_at).total_seconds())
