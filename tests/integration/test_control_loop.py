from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from adaptive_controller.config import Settings
from adaptive_controller.core import ControlLoop, ControlLoopStatus
from adaptive_controller.execute import ExecutionReport, ExecutionResult, ExecutionStatus
from adaptive_controller.monitor import MetricQueryResult, MetricSample, MetricSnapshot, ServiceMetrics
from adaptive_controller.observability import AuditLogger, DecisionLogger, JsonlTelemetrySink, TraceLogger
from adaptive_controller.plan import AdaptationAction


class FakeMetricsCollector:
    def __init__(self, snapshot: MetricSnapshot):
        self.snapshot = snapshot

    def collect(self, services=None):
        return self.snapshot


class FakeKnowledgeStore:
    def __init__(self):
        self.metrics = []
        self.plans = []
        self.validations = []
        self.executions = []

    def record_metrics(self, snapshot):
        self.metrics.append(snapshot)

    def record_plan_batch(self, batch):
        self.plans.append(batch)

    def record_validation_report(self, report):
        self.validations.append(report)

    def record_execution_report(self, report):
        self.executions.append(report)

    def recent_decision_context(self, service_name):
        return {
            "latest_metrics": None,
            "recent_plans": [],
            "recent_validations": [],
            "recent_executions": [],
            "policies": {},
            "scenarios": [],
        }


class FakeDeploymentExecutor:
    def __init__(self):
        self.reports = []

    def execute_approved(self, validation_report):
        results = [
            ExecutionResult(
                plan=plan,
                status=ExecutionStatus.SUCCEEDED,
                message="executed",
            )
            for plan in validation_report.approved_plans
            if plan.action != AdaptationAction.NO_OP
        ]
        report = ExecutionReport(namespace=validation_report.namespace, results=results)
        self.reports.append(report)
        return report


def _workspace_tmp() -> Path:
    path = Path(".test-artifacts") / f"control-loop-{uuid4()}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _sample(value: float) -> MetricSample:
    return MetricSample(
        timestamp=datetime.now(timezone.utc),
        value=value,
        labels={"service": "front-end"},
    )


def _result(name: str, value: float) -> MetricQueryResult:
    return MetricQueryResult(name=name, query=f"{name}_query", samples=[_sample(value)])


def _snapshot(cpu: float = 1.2, latency: float = 0.9) -> MetricSnapshot:
    service = ServiceMetrics(
        service_name="front-end",
        cpu_usage_cores=_result("cpu_usage_cores", cpu),
        memory_usage_bytes=_result("memory_usage_bytes", 128.0),
        request_rate_rps=_result("request_rate_rps", 20.0),
        error_rate_rps=_result("error_rate_rps", 0.0),
        latency_p95_seconds=_result("latency_p95_seconds", latency),
        desired_replicas=_result("desired_replicas", 2.0),
        current_replicas=_result("current_replicas", 2.0),
        ready_pods=_result("ready_pods", 2.0),
    )
    return MetricSnapshot(namespace="sockshop", window="5m", services=[service])


def test_control_loop_runs_monitor_analyze_plan_safety_knowledge_and_reasoning() -> None:
    settings = Settings()
    knowledge = FakeKnowledgeStore()

    result = ControlLoop(
        settings=settings,
        metrics_collector=FakeMetricsCollector(_snapshot()),
        knowledge_store=knowledge,
        execute_actions=False,
    ).run_once(
        services=["front-end"],
        current_replicas_by_service={"front-end": 2},
    )

    assert result.run.status == ControlLoopStatus.SUCCEEDED
    assert result.metrics is not None
    assert result.analysis is not None
    assert result.plans is not None
    assert result.validation is not None
    assert result.execution is None
    assert result.explanation is not None
    assert result.validation.approved_plans[0].target_replicas == 3
    assert len(knowledge.metrics) == 1
    assert len(knowledge.plans) == 1
    assert len(knowledge.validations) == 1


def test_control_loop_executes_when_enabled_and_executor_is_provided() -> None:
    settings = Settings()
    knowledge = FakeKnowledgeStore()
    executor = FakeDeploymentExecutor()

    result = ControlLoop(
        settings=settings,
        metrics_collector=FakeMetricsCollector(_snapshot()),
        deployment_executor=executor,
        knowledge_store=knowledge,
        execute_actions=True,
    ).run_once(
        services=["front-end"],
        current_replicas_by_service={"front-end": 2},
    )

    assert result.run.status == ControlLoopStatus.SUCCEEDED
    assert result.execution is not None
    assert result.execution.results[0].status == ExecutionStatus.SUCCEEDED
    assert len(knowledge.executions) == 1


def test_control_loop_returns_failed_result_when_pipeline_raises() -> None:
    class BrokenCollector:
        def collect(self, services=None):
            raise RuntimeError("prometheus unavailable")

    result = ControlLoop(
        settings=Settings(),
        metrics_collector=BrokenCollector(),
        knowledge_store=FakeKnowledgeStore(),
    ).run_once(services=["front-end"])

    assert result.run.status == ControlLoopStatus.FAILED
    assert result.run.error == "prometheus unavailable"
    assert result.metrics is None


def test_control_loop_emits_observability_events() -> None:
    path = _workspace_tmp()
    try:
        trace_sink = JsonlTelemetrySink(path / "trace.jsonl")
        decision_sink = JsonlTelemetrySink(path / "decisions.jsonl")
        audit_sink = JsonlTelemetrySink(path / "audit.jsonl")

        result = ControlLoop(
            settings=Settings(),
            metrics_collector=FakeMetricsCollector(_snapshot()),
            knowledge_store=FakeKnowledgeStore(),
            trace_logger=TraceLogger(trace_sink),
            decision_logger=DecisionLogger(decision_sink),
            audit_logger=AuditLogger(audit_sink),
        ).run_once(
            services=["front-end"],
            current_replicas_by_service={"front-end": 2},
        )

        assert result.run.status == ControlLoopStatus.SUCCEEDED
        assert any(event["payload"]["stage"] == "monitor" for event in trace_sink.read_events())
        assert decision_sink.read_events()[0]["event_type"] == "decision"
        assert audit_sink.read_events()[0]["event_type"] == "safety_validation"
    finally:
        _cleanup(path)
