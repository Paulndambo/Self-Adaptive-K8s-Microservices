from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class MetricSample(BaseModel):
    timestamp: datetime
    value: float
    labels: dict[str, str] = Field(default_factory=dict)


class MetricQueryResult(BaseModel):
    name: str
    query: str
    samples: list[MetricSample] = Field(default_factory=list)
    available: bool = True
    reason: str | None = None

    @property
    def latest_value(self) -> float | None:
        if not self.samples:
            return None
        return self.samples[-1].value

    @classmethod
    def unavailable(cls, name: str, query: str, reason: str) -> "MetricQueryResult":
        return cls(name=name, query=query, samples=[], available=False, reason=reason)


class ServiceMetrics(BaseModel):
    service_name: str
    cpu_usage_cores: MetricQueryResult
    memory_usage_bytes: MetricQueryResult
    request_rate_rps: MetricQueryResult
    error_rate_rps: MetricQueryResult
    latency_p95_seconds: MetricQueryResult
    desired_replicas: MetricQueryResult
    current_replicas: MetricQueryResult
    ready_pods: MetricQueryResult


class MetricSnapshot(BaseModel):
    namespace: str
    collected_at: datetime = Field(default_factory=utc_now)
    window: str
    services: list[ServiceMetrics]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return all(
            result.available
            for service in self.services
            for result in (
                service.cpu_usage_cores,
                service.memory_usage_bytes,
                service.request_rate_rps,
                service.error_rate_rps,
                service.latency_p95_seconds,
                service.desired_replicas,
                service.current_replicas,
                service.ready_pods,
            )
        )
