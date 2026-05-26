from __future__ import annotations

from datetime import datetime, timezone

from adaptive_controller.analyze import (
    AnalysisFinding,
    AnalysisReport,
    AnalysisSeverity,
    ServiceAnalysis,
    SignalStatus,
)
from adaptive_controller.config import PlannerSettings
from adaptive_controller.plan import AdaptationAction, AdaptationPlanner, PlanPriority


def _report(*services: ServiceAnalysis) -> AnalysisReport:
    return AnalysisReport(
        namespace="sockshop",
        analyzed_at=datetime.now(timezone.utc),
        window="5m",
        services=list(services),
    )


def _finding(
    signal: str,
    status: SignalStatus,
    severity: AnalysisSeverity = AnalysisSeverity.WARNING,
) -> AnalysisFinding:
    return AnalysisFinding(
        service_name="front-end",
        signal=signal,
        status=status,
        severity=severity,
        message="test finding",
        value=1.0,
        threshold=0.5,
    )


def test_planner_scales_up_for_critical_latency_violation() -> None:
    planner = AdaptationPlanner(PlannerSettings(scale_step=2))
    service = ServiceAnalysis(
        service_name="front-end",
        findings=[
            _finding(
                "latency_p95_seconds",
                SignalStatus.VIOLATED,
                AnalysisSeverity.CRITICAL,
            )
        ],
    )

    batch = planner.plan(_report(service), current_replicas_by_service={"front-end": 3})

    plan = batch.plans[0]
    assert batch.has_actions is True
    assert plan.action == AdaptationAction.SCALE_UP
    assert plan.priority == PlanPriority.HIGH
    assert plan.current_replicas == 3
    assert plan.target_replicas == 5
    assert plan.changes_replicas is True


def test_planner_scales_up_for_high_cpu() -> None:
    planner = AdaptationPlanner(PlannerSettings(scale_step=1))
    service = ServiceAnalysis(
        service_name="front-end",
        findings=[_finding("cpu_usage_cores", SignalStatus.HIGH)],
    )

    batch = planner.plan(_report(service), current_replicas_by_service={"front-end": 2})

    assert batch.plans[0].action == AdaptationAction.SCALE_UP
    assert batch.plans[0].priority == PlanPriority.MEDIUM
    assert batch.plans[0].target_replicas == 3


def test_planner_scales_down_for_low_throughput() -> None:
    planner = AdaptationPlanner(PlannerSettings(scale_step=1))
    service = ServiceAnalysis(
        service_name="front-end",
        findings=[_finding("request_rate_rps", SignalStatus.LOW)],
    )

    batch = planner.plan(_report(service), current_replicas_by_service={"front-end": 4})

    plan = batch.plans[0]
    assert plan.action == AdaptationAction.SCALE_DOWN
    assert plan.priority == PlanPriority.LOW
    assert plan.current_replicas == 4
    assert plan.target_replicas == 3


def test_planner_returns_no_op_when_no_findings_exist() -> None:
    planner = AdaptationPlanner(PlannerSettings(default_current_replicas=2))
    service = ServiceAnalysis(service_name="front-end", findings=[])

    batch = planner.plan(_report(service))

    plan = batch.plans[0]
    assert batch.has_actions is False
    assert plan.action == AdaptationAction.NO_OP
    assert plan.current_replicas == 2
    assert plan.target_replicas == 2


def test_planner_ranks_high_priority_before_low_priority() -> None:
    planner = AdaptationPlanner(PlannerSettings())
    critical_service = ServiceAnalysis(
        service_name="catalogue",
        findings=[
            AnalysisFinding(
                service_name="catalogue",
                signal="error_rate_rps",
                status=SignalStatus.VIOLATED,
                severity=AnalysisSeverity.CRITICAL,
                message="error spike",
            )
        ],
    )
    low_service = ServiceAnalysis(
        service_name="front-end",
        findings=[_finding("request_rate_rps", SignalStatus.LOW)],
    )

    batch = planner.plan(
        _report(low_service, critical_service),
        current_replicas_by_service={"front-end": 3, "catalogue": 2},
    )

    assert batch.plans[0].service_name == "catalogue"
    assert batch.plans[0].priority == PlanPriority.HIGH
    assert batch.plans[1].service_name == "front-end"
