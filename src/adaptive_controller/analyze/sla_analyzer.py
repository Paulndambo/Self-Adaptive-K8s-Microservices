from __future__ import annotations

from adaptive_controller.config import AnalyzerSettings
from adaptive_controller.analyze.analysis_models import (
    AnalysisFinding,
    AnalysisSeverity,
    SignalStatus,
)
from adaptive_controller.monitor.metric_models import ServiceMetrics


class SlaAnalyzer:
    def __init__(self, settings: AnalyzerSettings):
        self.settings = settings

    def analyze(self, metrics: ServiceMetrics) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        latency = metrics.latency_p95_seconds.latest_value
        if latency is not None and latency > self.settings.latency_p95_sla_seconds:
            findings.append(
                AnalysisFinding(
                    service_name=metrics.service_name,
                    signal="latency_p95_seconds",
                    status=SignalStatus.VIOLATED,
                    severity=AnalysisSeverity.CRITICAL,
                    message="p95 latency violates the configured SLA",
                    value=latency,
                    threshold=self.settings.latency_p95_sla_seconds,
                )
            )

        error_rate = metrics.error_rate_rps.latest_value
        if error_rate is not None and error_rate > self.settings.error_rate_sla_rps:
            findings.append(
                AnalysisFinding(
                    service_name=metrics.service_name,
                    signal="error_rate_rps",
                    status=SignalStatus.VIOLATED,
                    severity=AnalysisSeverity.CRITICAL,
                    message="Error rate violates the configured SLA",
                    value=error_rate,
                    threshold=self.settings.error_rate_sla_rps,
                )
            )
        return findings
