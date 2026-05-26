from __future__ import annotations

from adaptive_controller.config import MonitorSettings
from adaptive_controller.core.exceptions import MonitorError
from adaptive_controller.monitor.metric_models import (
    MetricQueryResult,
    MetricSnapshot,
    ServiceMetrics,
)
from adaptive_controller.monitor.metric_queries import service_queries
from adaptive_controller.monitor.prometheus_client import PrometheusClient


class MetricsCollector:
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

    def collect(self, services: tuple[str, ...] | list[str] | None = None) -> MetricSnapshot:
        service_names = tuple(services or self.settings.services)
        collected_services = [
            self.collect_service(service_name) for service_name in service_names
        ]
        return MetricSnapshot(
            namespace=self.settings.namespace,
            window=self.settings.query_window,
            services=collected_services,
            metadata={"prometheus_url": self.settings.prometheus_url},
        )

    def collect_service(self, service_name: str) -> ServiceMetrics:
        queries = service_queries(
            namespace=self.settings.namespace,
            service=service_name,
            window=self.settings.query_window,
        )
        results = {
            name: self._safe_query(name, query)
            for name, query in queries.items()
        }
        return ServiceMetrics(service_name=service_name, **results)

    def _safe_query(self, name: str, query: str) -> MetricQueryResult:
        try:
            samples = self.prometheus_client.query(query)
        except MonitorError as exc:
            return MetricQueryResult.unavailable(name=name, query=query, reason=str(exc))

        if not samples:
            return MetricQueryResult.unavailable(
                name=name,
                query=query,
                reason="Prometheus returned no series for this metric",
            )
        return MetricQueryResult(name=name, query=query, samples=samples)
