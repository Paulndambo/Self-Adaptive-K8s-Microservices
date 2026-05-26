from __future__ import annotations

from adaptive_controller.config import AnalyzerSettings
from adaptive_controller.analyze.analysis_models import (
    AnalysisFinding,
    AnalysisSeverity,
    SignalStatus,
)
from adaptive_controller.monitor.metric_models import ServiceMetrics


class ThresholdAnalyzer:
    def __init__(self, settings: AnalyzerSettings):
        self.settings = settings

    def analyze(self, metrics: ServiceMetrics) -> list[AnalysisFinding]:
        findings: list[AnalysisFinding] = []
        findings.extend(
            self._high_threshold(
                metrics,
                signal="cpu_usage_cores",
                value=metrics.cpu_usage_cores.latest_value,
                threshold=self.settings.cpu_high_threshold_cores,
                message="CPU usage is above the configured threshold",
            )
        )
        findings.extend(
            self._high_threshold(
                metrics,
                signal="memory_usage_bytes",
                value=metrics.memory_usage_bytes.latest_value,
                threshold=self.settings.memory_high_threshold_bytes,
                message="Memory usage is above the configured threshold",
            )
        )

        throughput = metrics.request_rate_rps.latest_value
        if throughput is not None and throughput < self.settings.low_throughput_rps:
            findings.append(
                AnalysisFinding(
                    service_name=metrics.service_name,
                    signal="request_rate_rps",
                    status=SignalStatus.LOW,
                    severity=AnalysisSeverity.WARNING,
                    message="Throughput is below the configured low-throughput threshold",
                    value=throughput,
                    threshold=self.settings.low_throughput_rps,
                )
            )
        return findings

    def _high_threshold(
        self,
        metrics: ServiceMetrics,
        signal: str,
        value: float | None,
        threshold: float,
        message: str,
    ) -> list[AnalysisFinding]:
        if value is None or value <= threshold:
            return []
        return [
            AnalysisFinding(
                service_name=metrics.service_name,
                signal=signal,
                status=SignalStatus.HIGH,
                severity=AnalysisSeverity.WARNING,
                message=message,
                value=value,
                threshold=threshold,
            )
        ]
