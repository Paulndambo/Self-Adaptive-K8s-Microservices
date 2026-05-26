class AdaptiveControllerError(Exception):
    """Base exception for the adaptive controller."""


class MonitorError(AdaptiveControllerError):
    """Base exception for monitoring failures."""


class PrometheusConnectionError(MonitorError):
    """Raised when Prometheus cannot be reached."""


class PrometheusQueryError(MonitorError):
    """Raised when Prometheus rejects a query or returns an error status."""


class PrometheusResponseError(MonitorError):
    """Raised when Prometheus returns a malformed response."""


class ExecutionError(AdaptiveControllerError):
    """Base exception for execution failures."""


class KubernetesClientError(ExecutionError):
    """Raised when a Kubernetes API operation fails."""


class UnsupportedExecutionPlanError(ExecutionError):
    """Raised when an executor receives a plan it cannot apply."""
