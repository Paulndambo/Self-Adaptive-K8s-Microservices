from __future__ import annotations

from pydantic import BaseModel, Field


class ControllerSummary(BaseModel):
    controller_name: str
    average_latency_seconds: float = 0.0
    p95_latency_seconds: float = 0.0
    sla_violation_rate: float = 0.0
    pod_seconds: float = 0.0
    scaling_events: int = 0
    adaptation_latency_seconds: float = 0.0
    stability_score: float = 0.0
    cost: float = 0.0
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class ExperimentReport(BaseModel):
    title: str
    summaries: list[ControllerSummary] = Field(default_factory=list)

    @property
    def controller_names(self) -> list[str]:
        return [summary.controller_name for summary in self.summaries]
