from __future__ import annotations

from datetime import datetime, timezone

from adaptive_controller.analyze import AnalysisEngine, AnalysisSeverity, SignalStatus
from adaptive_controller.config import AnalyzerSettings
from adaptive_controller.monitor.metric_models import (
    MetricQueryResult,
    MetricSample,
    MetricSnapshot,
    ServiceMetrics,
)


def _sample(value: float, timestamp: float = 1710000000.0) -> MetricSample:
    return MetricSample(
        timestamp=datetime.fromtimestamp(timestamp, tz=timezone.utc),
        value=value,
        labels={"service": "front-end"},
    )


def _result(name: str, value: float, samples: list[MetricSample] | None = None) -> MetricQueryResult:
    return MetricQueryResult(
        name=name,
        query=f"{name}_query",
        samples=samples or [_sample(value)],
    )


def _service_metrics(**overrides) -> ServiceMetrics:
    values = {
        "service_name": "front-end",
        "cpu_usage_cores": _result("cpu_usage_cores", 0.2),
        "memory_usage_bytes": _result("memory_usage_bytes", 128 * 1024 * 1024),
        "request_rate_rps": _result("request_rate_rps", 20.0),
        "error_rate_rps": _result("error_rate_rps", 0.0),
        "latency_p95_seconds": _result("latency_p95_seconds", 0.1),
        "desired_replicas": _result("desired_replicas", 3.0),
        "current_replicas": _result("current_replicas", 3.0),
        "ready_pods": _result("ready_pods", 3.0),
    }
    values.update(overrides)
    return ServiceMetrics(**values)


def _snapshot(metrics: ServiceMetrics) -> MetricSnapshot:
    return MetricSnapshot(namespace="sockshop", window="5m", services=[metrics])


def test_analysis_engine_returns_no_findings_for_normal_metrics() -> None:
    report = AnalysisEngine(AnalyzerSettings()).analyze(_snapshot(_service_metrics()))

    assert report.namespace == "sockshop"
    assert report.requires_attention is False
    assert report.has_critical_findings is False
    assert report.services[0].findings == []


def test_analysis_engine_flags_threshold_and_sla_violations() -> None:
    settings = AnalyzerSettings(
        cpu_high_threshold_cores=0.8,
        latency_p95_sla_seconds=0.5,
        error_rate_sla_rps=1.0,
    )
    metrics = _service_metrics(
        cpu_usage_cores=_result("cpu_usage_cores", 1.2),
        latency_p95_seconds=_result("latency_p95_seconds", 0.9),
        error_rate_rps=_result("error_rate_rps", 2.0),
    )

    report = AnalysisEngine(settings).analyze(_snapshot(metrics))
    findings = report.services[0].findings

    assert report.requires_attention is True
    assert report.has_critical_findings is True
    assert any(f.signal == "cpu_usage_cores" and f.status == SignalStatus.HIGH for f in findings)
    assert any(
        f.signal == "latency_p95_seconds"
        and f.status == SignalStatus.VIOLATED
        and f.severity == AnalysisSeverity.CRITICAL
        for f in findings
    )
    assert any(f.signal == "error_rate_rps" and f.status == SignalStatus.VIOLATED for f in findings)


def test_analysis_engine_marks_missing_metrics_without_crashing() -> None:
    missing_cpu = MetricQueryResult.unavailable(
        name="cpu_usage_cores",
        query="cpu_query",
        reason="Prometheus returned no series for this metric",
    )
    metrics = _service_metrics(cpu_usage_cores=missing_cpu)

    report = AnalysisEngine(AnalyzerSettings()).analyze(_snapshot(metrics))

    assert report.requires_attention is True
    finding = report.services[0].findings[0]
    assert finding.signal == "cpu_usage_cores"
    assert finding.status == SignalStatus.MISSING
    assert finding.severity == AnalysisSeverity.WARNING


def test_analysis_engine_flags_unready_replicas() -> None:
    metrics = _service_metrics(
        current_replicas=_result("current_replicas", 4.0),
        ready_pods=_result("ready_pods", 2.0),
    )

    report = AnalysisEngine(AnalyzerSettings()).analyze(_snapshot(metrics))

    assert any(
        f.signal == "ready_pods"
        and f.status == SignalStatus.UNHEALTHY
        and f.severity == AnalysisSeverity.CRITICAL
        for f in report.services[0].findings
    )


def test_analysis_engine_detects_metric_trends() -> None:
    metrics = _service_metrics(
        latency_p95_seconds=_result(
            "latency_p95_seconds",
            0.4,
            samples=[_sample(0.2, 1710000000.0), _sample(0.4, 1710000060.0)],
        )
    )

    report = AnalysisEngine(AnalyzerSettings(trend_change_threshold_ratio=0.15)).analyze(
        _snapshot(metrics)
    )

    assert any(
        f.signal == "latency_p95_seconds" and f.status == SignalStatus.INCREASING
        for f in report.services[0].findings
    )
