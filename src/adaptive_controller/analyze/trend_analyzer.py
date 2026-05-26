from __future__ import annotations

from adaptive_controller.config import AnalyzerSettings
from adaptive_controller.analyze.analysis_models import (
    AnalysisFinding,
    AnalysisSeverity,
    SignalStatus,
)
from adaptive_controller.monitor.metric_models import MetricQueryResult, ServiceMetrics


class TrendAnalyzer:
    def __init__(self, settings: AnalyzerSettings):
        self.settings = settings

    def analyze(self, metrics: ServiceMetrics) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        for signal, result in (
            ("cpu_usage_cores", metrics.cpu_usage_cores),
            ("latency_p95_seconds", metrics.latency_p95_seconds),
            ("request_rate_rps", metrics.request_rate_rps),
            ("error_rate_rps", metrics.error_rate_rps),
        ):
            finding = self._trend(metrics.service_name, signal, result)
            if finding is not None:
                findings.append(finding)
        return findings

    def _trend(
        self,
        service_name: str,
        signal: str,
        result: MetricQueryResult,
    ) -> AnalysisFinding | None:
        if len(result.samples) < 2:
            return None

        first = result.samples[0].value
        last = result.samples[-1].value
        baseline = abs(first) if first != 0 else 1.0
        ratio = (last - first) / baseline
        threshold = self.settings.trend_change_threshold_ratio

        if ratio > threshold:
            status = SignalStatus.INCREASING
            message = f"{signal} is increasing over the observed window"
        elif ratio < -threshold:
            status = SignalStatus.DECREASING
            message = f"{signal} is decreasing over the observed window"
        else:
            return None

        return AnalysisFinding(
            service_name=service_name,
            signal=signal,
            status=status,
            severity=AnalysisSeverity.INFO,
            message=message,
            value=last,
            threshold=threshold,
            metadata={"first_value": first, "change_ratio": ratio},
        )
