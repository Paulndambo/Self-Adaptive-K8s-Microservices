from __future__ import annotations

from adaptive_controller.config import MonitorSettings
from adaptive_controller.monitor.metric_models import HealthStatus
from adaptive_controller.monitor.metrics_collector import MetricsCollector
from adaptive_controller.monitor.prometheus_client import PrometheusClient


class HealthChecker:
    def __init__(
        self,
        settings: MonitorSettings,
        prometheus_client: PrometheusClient | None = None,
    ):
        self.settings = settings
        self.prometheus_client = prometheus_client or PrometheusClient(
            base_url=settings.prometheus_url,
            timeout_seconds=settings.query_timeout_seconds,
        )

    def prometheus_status(self) -> HealthStatus:
        if self.prometheus_client.is_available():
            return HealthStatus.HEALTHY
        return HealthStatus.UNAVAILABLE

    def workload_status(self, services: tuple[str, ...] | list[str] | None = None) -> HealthStatus:
        if self.prometheus_status() == HealthStatus.UNAVAILABLE:
            return HealthStatus.UNAVAILABLE

        collector = MetricsCollector(self.settings, self.prometheus_client)
        snapshot = collector.collect(services)
        if not snapshot.services:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY if snapshot.is_complete else HealthStatus.DEGRADED
