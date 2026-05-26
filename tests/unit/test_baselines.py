from __future__ import annotations

from datetime import datetime, timezone

from adaptive_controller.baselines import (
    BaselineAction,
    HpaBaseline,
    PidController,
    RuleBasedController,
)
from adaptive_controller.config import BaselineSettings
from adaptive_controller.monitor import MetricQueryResult, MetricSample, ServiceMetrics


def _sample(value: float) -> MetricSample:
    return MetricSample(
        timestamp=datetime.now(timezone.utc),
        value=value,
        labels={"service": "front-end"},
    )


def _result(name: str, value: float | None) -> MetricQueryResult:
    if value is None:
        return MetricQueryResult.unavailable(name=name, query=f"{name}_query", reason="missing")
    return MetricQueryResult(name=name, query=f"{name}_query", samples=[_sample(value)])


def _metrics(
    cpu: float | None = 0.4,
    memory: float | None = 128.0,
    throughput: float | None = 10.0,
    error_rate: float | None = 0.0,
    latency: float | None = 0.1,
    desired: float | None = 2.0,
    current: float | None = 2.0,
    ready: float | None = 2.0,
) -> ServiceMetrics:
    return ServiceMetrics(
        service_name="front-end",
        cpu_usage_cores=_result("cpu_usage_cores", cpu),
        memory_usage_bytes=_result("memory_usage_bytes", memory),
        request_rate_rps=_result("request_rate_rps", throughput),
        error_rate_rps=_result("error_rate_rps", error_rate),
        latency_p95_seconds=_result("latency_p95_seconds", latency),
        desired_replicas=_result("desired_replicas", desired),
        current_replicas=_result("current_replicas", current),
        ready_pods=_result("ready_pods", ready),
    )


def test_hpa_baseline_scales_up_when_cpu_exceeds_target() -> None:
    settings = BaselineSettings(target_cpu_cores=0.5, min_replicas=1, max_replicas=10)
    decision = HpaBaseline(settings).decide(_metrics(cpu=1.0), current_replicas=2)

    assert decision.action == BaselineAction.SCALE_UP
    assert decision.target_replicas == 4
    assert decision.changes_replicas is True


def test_hpa_baseline_scales_down_when_cpu_is_low() -> None:
    settings = BaselineSettings(target_cpu_cores=0.5, min_replicas=1, max_replicas=10)
    decision = HpaBaseline(settings).decide(_metrics(cpu=0.1), current_replicas=4)

    assert decision.action == BaselineAction.SCALE_DOWN
    assert decision.target_replicas == 1


def test_hpa_baseline_no_ops_when_cpu_metric_is_missing() -> None:
    decision = HpaBaseline(BaselineSettings()).decide(_metrics(cpu=None), current_replicas=3)

    assert decision.action == BaselineAction.NO_OP
    assert decision.target_replicas == 3


def test_pid_controller_scales_up_for_high_latency() -> None:
    settings = BaselineSettings(
        target_latency_seconds=0.5,
        scale_tolerance_ratio=0.1,
        pid_kp=3.0,
        min_replicas=1,
        max_replicas=10,
    )
    decision = PidController(settings).decide(_metrics(latency=1.0), current_replicas=2)

    assert decision.action == BaselineAction.SCALE_UP
    assert decision.target_replicas > 2


def test_pid_controller_scales_down_for_low_latency() -> None:
    settings = BaselineSettings(
        target_latency_seconds=0.5,
        scale_tolerance_ratio=0.1,
        pid_kp=3.0,
        min_replicas=1,
        max_replicas=10,
    )
    decision = PidController(settings).decide(_metrics(latency=0.1), current_replicas=4)

    assert decision.action == BaselineAction.SCALE_DOWN
    assert decision.target_replicas < 4


def test_rule_based_controller_scales_up_on_latency_or_errors() -> None:
    settings = BaselineSettings(target_latency_seconds=0.5, target_cpu_cores=0.6)
    decision = RuleBasedController(settings).decide(
        _metrics(cpu=0.3, latency=0.8, error_rate=0.0),
        current_replicas=2,
    )

    assert decision.action == BaselineAction.SCALE_UP
    assert decision.target_replicas == 3


def test_rule_based_controller_scales_down_on_low_healthy_load() -> None:
    settings = BaselineSettings(target_latency_seconds=0.5, target_cpu_cores=0.6)
    decision = RuleBasedController(settings).decide(
        _metrics(cpu=0.2, latency=0.1, error_rate=0.0, throughput=0.2),
        current_replicas=3,
    )

    assert decision.action == BaselineAction.SCALE_DOWN
    assert decision.target_replicas == 2


def test_rule_based_controller_no_ops_when_no_rule_matches() -> None:
    decision = RuleBasedController(BaselineSettings()).decide(
        _metrics(cpu=0.4, latency=0.2, error_rate=0.0, throughput=5.0),
        current_replicas=2,
    )

    assert decision.action == BaselineAction.NO_OP
    assert decision.target_replicas == 2
