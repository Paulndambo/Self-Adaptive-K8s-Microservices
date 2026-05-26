from __future__ import annotations

from datetime import datetime, timezone

import httpx
import pytest

from adaptive_controller.config import MonitorSettings
from adaptive_controller.core.exceptions import PrometheusQueryError, PrometheusResponseError
from adaptive_controller.monitor.health_checker import HealthChecker
from adaptive_controller.monitor.metric_models import HealthStatus, MetricSample
from adaptive_controller.monitor.metric_queries import (
    cpu_usage_query,
    current_replicas_query,
    desired_replicas_query,
    error_rate_query,
    latency_p95_query,
    memory_usage_query,
    ready_pods_query,
    request_rate_query,
    service_queries,
)
from adaptive_controller.monitor.metrics_collector import MetricsCollector
from adaptive_controller.monitor.prometheus_client import PrometheusClient


def test_query_builders_include_namespace_service_and_window() -> None:
    namespace = "sockshop"
    service = "front-end"
    window = "10m"

    queries = [
        cpu_usage_query(namespace, service, window),
        memory_usage_query(namespace, service),
        request_rate_query(namespace, service, window),
        error_rate_query(namespace, service, window),
        latency_p95_query(namespace, service, window),
        desired_replicas_query(namespace, service),
        current_replicas_query(namespace, service),
        ready_pods_query(namespace, service),
    ]

    assert all(namespace in query for query in queries)
    assert all(service in query for query in queries)
    assert window in queries[0]
    assert window in queries[2]
    assert window in queries[3]


def test_prometheus_client_parses_successful_vector_response(mocker) -> None:
    payload = {
        "status": "success",
        "data": {
            "resultType": "vector",
            "result": [
                {
                    "metric": {"service": "front-end"},
                    "value": [1710000000.0, "2.5"],
                }
            ],
        },
    }
    response = httpx.Response(200, json=payload)
    mocker.patch("httpx.get", return_value=response)

    samples = PrometheusClient().query("up")

    assert len(samples) == 1
    assert samples[0].value == 2.5
    assert samples[0].timestamp == datetime.fromtimestamp(1710000000.0, tz=timezone.utc)
    assert samples[0].labels == {"service": "front-end"}


def test_prometheus_client_returns_empty_series(mocker) -> None:
    payload = {
        "status": "success",
        "data": {"resultType": "vector", "result": []},
    }
    mocker.patch("httpx.get", return_value=httpx.Response(200, json=payload))

    assert PrometheusClient().query("missing_metric") == []


def test_prometheus_client_raises_for_prometheus_error(mocker) -> None:
    payload = {"status": "error", "error": "bad query"}
    mocker.patch("httpx.get", return_value=httpx.Response(200, json=payload))

    with pytest.raises(PrometheusQueryError):
        PrometheusClient().query("bad")


def test_prometheus_client_raises_for_malformed_response(mocker) -> None:
    payload = {
        "status": "success",
        "data": {"resultType": "scalar", "result": [1710000000.0, "1"]},
    }
    mocker.patch("httpx.get", return_value=httpx.Response(200, json=payload))

    with pytest.raises(PrometheusResponseError):
        PrometheusClient().query("up")


class FakePrometheusClient:
    def __init__(self, samples_by_query: dict[str, list[MetricSample]] | None = None):
        self.samples_by_query = samples_by_query or {}
        self.available = True

    def query(self, query: str) -> list[MetricSample]:
        return self.samples_by_query.get(query, [])

    def is_available(self) -> bool:
        return self.available


def _sample(value: float = 1.0) -> MetricSample:
    return MetricSample(
        timestamp=datetime.now(timezone.utc),
        value=value,
        labels={"service": "front-end"},
    )


def test_metrics_collector_returns_complete_snapshot_when_metrics_exist() -> None:
    settings = MonitorSettings(namespace="sockshop", services=("front-end",), query_window="5m")
    query_map = {
        query: [_sample(index)]
        for index, query in enumerate(service_queries("sockshop", "front-end", "5m").values())
    }
    client = FakePrometheusClient(query_map)

    snapshot = MetricsCollector(settings, client).collect()

    assert snapshot.namespace == "sockshop"
    assert snapshot.services[0].service_name == "front-end"
    assert snapshot.is_complete is True


def test_metrics_collector_marks_missing_metrics_unavailable() -> None:
    settings = MonitorSettings(namespace="sockshop", services=("front-end",), query_window="5m")
    client = FakePrometheusClient({})

    snapshot = MetricsCollector(settings, client).collect()

    assert snapshot.is_complete is False
    assert snapshot.services[0].cpu_usage_cores.available is False
    assert snapshot.services[0].cpu_usage_cores.reason == "Prometheus returned no series for this metric"


def test_health_checker_reports_prometheus_unavailable() -> None:
    settings = MonitorSettings(namespace="sockshop", services=("front-end",))
    client = FakePrometheusClient()
    client.available = False

    checker = HealthChecker(settings, client)

    assert checker.prometheus_status() == HealthStatus.UNAVAILABLE
    assert checker.workload_status() == HealthStatus.UNAVAILABLE
