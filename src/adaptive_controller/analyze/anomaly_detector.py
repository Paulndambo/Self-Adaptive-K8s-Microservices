from __future__ import annotations

from adaptive_controller.analyze.analysis_models import (
    AnalysisFinding,
    AnalysisSeverity,
    SignalStatus,
)
from adaptive_controller.monitor.metric_models import MetricQueryResult, ServiceMetrics


class AnomalyDetector:
    def analyze(self, metrics: ServiceMetrics) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        for signal, result in self._metric_results(metrics):
            if not result.available:
                findings.append(
                    AnalysisFinding(
                        service_name=metrics.service_name,
                        signal=signal,
                        status=SignalStatus.MISSING,
                        severity=AnalysisSeverity.WARNING,
                        message=result.reason or "Metric is unavailable",
                    )
                )

        ready = metrics.ready_pods.latest_value
        current = metrics.current_replicas.latest_value
        if ready is not None and current is not None and ready < current:
            findings.append(
                AnalysisFinding(
                    service_name=metrics.service_name,
                    signal="ready_pods",
                    status=SignalStatus.UNHEALTHY,
                    severity=AnalysisSeverity.CRITICAL,
                    message="Not all current replicas are ready",
                    value=ready,
                    threshold=current,
                )
            )
        return findings

    def _metric_results(
        self,
        metrics: ServiceMetrics,
    ) -> tuple[tuple[str, MetricQueryResult], ...]:
        return (
            ("cpu_usage_cores", metrics.cpu_usage_cores),
            ("memory_usage_bytes", metrics.memory_usage_bytes),
            ("request_rate_rps", metrics.request_rate_rps),
            ("error_rate_rps", metrics.error_rate_rps),
            ("latency_p95_seconds", metrics.latency_p95_seconds),
            ("desired_replicas", metrics.desired_replicas),
            ("current_replicas", metrics.current_replicas),
            ("ready_pods", metrics.ready_pods),
        )
