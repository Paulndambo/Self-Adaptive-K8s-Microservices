from __future__ import annotations

from datetime import timezone

from adaptive_controller.config import AnalyzerSettings
from adaptive_controller.analyze.analysis_models import AnalysisReport, ServiceAnalysis
from adaptive_controller.analyze.anomaly_detector import AnomalyDetector
from adaptive_controller.analyze.sla_analyzer import SlaAnalyzer
from adaptive_controller.analyze.threshold_analyzer import ThresholdAnalyzer
from adaptive_controller.analyze.trend_analyzer import TrendAnalyzer
from adaptive_controller.monitor.metric_models import MetricSnapshot


class AnalysisEngine:
    def __init__(self, settings: AnalyzerSettings):
        self.threshold_analyzer = ThresholdAnalyzer(settings)
        self.sla_analyzer = SlaAnalyzer(settings)
        self.trend_analyzer = TrendAnalyzer(settings)
        self.anomaly_detector = AnomalyDetector()

    def analyze(self, snapshot: MetricSnapshot) -> AnalysisReport:
        services: list[ServiceAnalysis] = []
        for service_metrics in snapshot.services:
            findings = []
            findings.extend(self.anomaly_detector.analyze(service_metrics))
            findings.extend(self.threshold_analyzer.analyze(service_metrics))
            findings.extend(self.sla_analyzer.analyze(service_metrics))
            findings.extend(self.trend_analyzer.analyze(service_metrics))
            services.append(
                ServiceAnalysis(
                    service_name=service_metrics.service_name,
                    findings=findings,
                )
            )

        analyzed_at = snapshot.collected_at
        if analyzed_at.tzinfo is None:
            analyzed_at = analyzed_at.replace(tzinfo=timezone.utc)

        return AnalysisReport(
            namespace=snapshot.namespace,
            analyzed_at=analyzed_at,
            window=snapshot.window,
            services=services,
        )
