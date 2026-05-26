from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AnalysisSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SignalStatus(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    LOW = "low"
    VIOLATED = "violated"
    MISSING = "missing"
    UNHEALTHY = "unhealthy"
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class AnalysisFinding(BaseModel):
    service_name: str
    signal: str
    status: SignalStatus
    severity: AnalysisSeverity
    message: str
    value: float | None = None
    threshold: float | None = None
    metadata: dict[str, str | float | int | bool | None] = Field(default_factory=dict)


class ServiceAnalysis(BaseModel):
    service_name: str
    findings: list[AnalysisFinding] = Field(default_factory=list)

    @property
    def has_critical_findings(self) -> bool:
        return any(finding.severity == AnalysisSeverity.CRITICAL for finding in self.findings)

    @property
    def has_warnings(self) -> bool:
        return any(finding.severity == AnalysisSeverity.WARNING for finding in self.findings)


class AnalysisReport(BaseModel):
    namespace: str
    analyzed_at: datetime
    window: str
    services: list[ServiceAnalysis]

    @property
    def requires_attention(self) -> bool:
        return any(service.findings for service in self.services)

    @property
    def has_critical_findings(self) -> bool:
        return any(service.has_critical_findings for service in self.services)
