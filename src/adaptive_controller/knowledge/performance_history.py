from __future__ import annotations

from adaptive_controller.knowledge.repositories import MetricsRepository


class PerformanceHistory:
    def __init__(self, metrics_repository: MetricsRepository, max_recent_items: int = 100):
        self.metrics_repository = metrics_repository
        self.max_recent_items = max_recent_items

    def recent_for_service(self, service_name: str, limit: int | None = None) -> list[dict]:
        records = self.metrics_repository.recent_snapshots(limit or self.max_recent_items)
        matches = []
        for record in records:
            services = record.get("services", [])
            for service in services:
                if service.get("service_name") == service_name:
                    matches.append(service)
        return matches

    def latest_for_service(self, service_name: str) -> dict | None:
        recent = self.recent_for_service(service_name, limit=self.max_recent_items)
        if not recent:
            return None
        return recent[-1]
