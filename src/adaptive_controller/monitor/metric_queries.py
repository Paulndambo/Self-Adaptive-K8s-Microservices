from __future__ import annotations


def _labels(namespace: str, service: str) -> str:
    return f'namespace="{namespace}",service="{service}"'


def cpu_usage_query(namespace: str, service: str, window: str = "5m") -> str:
    return (
        "sum(rate(container_cpu_usage_seconds_total{"
        f'namespace="{namespace}",pod=~"{service}.*",container!="",container!="POD"'
        f"}}[{window}]))"
    )


def memory_usage_query(namespace: str, service: str) -> str:
    return (
        "sum(container_memory_working_set_bytes{"
        f'namespace="{namespace}",pod=~"{service}.*",container!="",container!="POD"'
        "})"
    )


def request_rate_query(namespace: str, service: str, window: str = "5m") -> str:
    return f"sum(rate(http_requests_total{{{_labels(namespace, service)}}}[{window}]))"


def error_rate_query(namespace: str, service: str, window: str = "5m") -> str:
    return (
        "sum(rate(http_requests_total{"
        f'{_labels(namespace, service)},status=~"5.."'
        f"}}[{window}]))"
    )


def latency_p95_query(namespace: str, service: str, window: str = "5m") -> str:
    return (
        "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{"
        f"{_labels(namespace, service)}"
        f"}}[{window}])) by (le))"
    )


def desired_replicas_query(namespace: str, service: str) -> str:
    return (
        "kube_deployment_spec_replicas{"
        f'namespace="{namespace}",deployment="{service}"'
        "}"
    )


def current_replicas_query(namespace: str, service: str) -> str:
    return (
        "kube_deployment_status_replicas{"
        f'namespace="{namespace}",deployment="{service}"'
        "}"
    )


def ready_pods_query(namespace: str, service: str) -> str:
    return (
        "sum(kube_pod_status_ready{"
        f'namespace="{namespace}",pod=~"{service}.*",condition="true"'
        "})"
    )


def service_queries(namespace: str, service: str, window: str = "5m") -> dict[str, str]:
    return {
        "cpu_usage_cores": cpu_usage_query(namespace, service, window),
        "memory_usage_bytes": memory_usage_query(namespace, service),
        "request_rate_rps": request_rate_query(namespace, service, window),
        "error_rate_rps": error_rate_query(namespace, service, window),
        "latency_p95_seconds": latency_p95_query(namespace, service, window),
        "desired_replicas": desired_replicas_query(namespace, service),
        "current_replicas": current_replicas_query(namespace, service),
        "ready_pods": ready_pods_query(namespace, service),
    }
