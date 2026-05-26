from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx

from adaptive_controller.core.exceptions import (
    PrometheusConnectionError,
    PrometheusQueryError,
    PrometheusResponseError,
)
from adaptive_controller.monitor.metric_models import MetricSample


class PrometheusClient:
    def __init__(self, base_url: str = "http://localhost:9090", timeout_seconds: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def query(self, promql: str, at: datetime | None = None) -> list[MetricSample]:
        params: dict[str, str | float] = {"query": promql}
        if at is not None:
            params["time"] = at.timestamp()
        data = self._get("/api/v1/query", params)
        return self._parse_vector(data, promql)

    def query_range(
        self,
        promql: str,
        start: datetime,
        end: datetime,
        step: str = "30s",
    ) -> list[MetricSample]:
        data = self._get(
            "/api/v1/query_range",
            {
                "query": promql,
                "start": start.timestamp(),
                "end": end.timestamp(),
                "step": step,
            },
        )
        return self._parse_matrix(data, promql)

    def is_available(self) -> bool:
        try:
            self._get("/-/ready", {})
        except (PrometheusConnectionError, PrometheusQueryError, PrometheusResponseError):
            return False
        return True

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = httpx.get(url, params=params, timeout=self.timeout_seconds)
        except httpx.TimeoutException as exc:
            raise PrometheusConnectionError(f"Prometheus request timed out: {url}") from exc
        except httpx.ConnectError as exc:
            raise PrometheusConnectionError(f"Could not connect to Prometheus: {url}") from exc
        except httpx.HTTPError as exc:
            raise PrometheusConnectionError(f"Prometheus request failed: {url}") from exc

        if response.status_code >= 400:
            raise PrometheusQueryError(
                f"Prometheus returned HTTP {response.status_code} for {url}"
            )

        if path == "/-/ready":
            return {"status": "success", "data": {}}

        try:
            payload = response.json()
        except ValueError as exc:
            raise PrometheusResponseError("Prometheus returned non-JSON response") from exc

        if not isinstance(payload, dict):
            raise PrometheusResponseError("Prometheus response must be a JSON object")
        if payload.get("status") != "success":
            error = payload.get("error", "unknown error")
            raise PrometheusQueryError(f"Prometheus query failed: {error}")
        if "data" not in payload:
            raise PrometheusResponseError("Prometheus response is missing data")
        return payload

    def _parse_vector(self, payload: dict[str, Any], promql: str) -> list[MetricSample]:
        data = payload["data"]
        if data.get("resultType") != "vector":
            raise PrometheusResponseError(f"Expected vector result for query: {promql}")
        result = data.get("result")
        if not isinstance(result, list):
            raise PrometheusResponseError("Prometheus vector result must be a list")
        return [self._sample_from_vector_item(item) for item in result]

    def _parse_matrix(self, payload: dict[str, Any], promql: str) -> list[MetricSample]:
        data = payload["data"]
        if data.get("resultType") != "matrix":
            raise PrometheusResponseError(f"Expected matrix result for query: {promql}")
        result = data.get("result")
        if not isinstance(result, list):
            raise PrometheusResponseError("Prometheus matrix result must be a list")
        samples: list[MetricSample] = []
        for item in result:
            labels = self._labels(item)
            for value in item.get("values", []):
                samples.append(self._sample_from_value(value, labels))
        return samples

    def _sample_from_vector_item(self, item: dict[str, Any]) -> MetricSample:
        return self._sample_from_value(item.get("value"), self._labels(item))

    def _sample_from_value(self, value: Any, labels: dict[str, str]) -> MetricSample:
        if not isinstance(value, list) or len(value) != 2:
            raise PrometheusResponseError("Prometheus sample must contain timestamp and value")
        try:
            timestamp = datetime.fromtimestamp(float(value[0]), tz=timezone.utc)
            numeric_value = float(value[1])
        except (TypeError, ValueError) as exc:
            raise PrometheusResponseError("Prometheus sample contains invalid values") from exc
        return MetricSample(timestamp=timestamp, value=numeric_value, labels=labels)

    def _labels(self, item: dict[str, Any]) -> dict[str, str]:
        labels = item.get("metric", {})
        if not isinstance(labels, dict):
            raise PrometheusResponseError("Prometheus metric labels must be an object")
        return {str(key): str(value) for key, value in labels.items()}
