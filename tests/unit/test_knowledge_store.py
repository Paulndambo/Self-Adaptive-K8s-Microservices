from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from adaptive_controller.config import KnowledgeSettings
from adaptive_controller.execute import ExecutionReport, ExecutionResult, ExecutionStatus
from adaptive_controller.knowledge import KnowledgeStore
from adaptive_controller.monitor import MetricQueryResult, MetricSample, MetricSnapshot, ServiceMetrics
from adaptive_controller.plan import AdaptationAction, AdaptationPlan, PlanBatch, PlanPriority
from adaptive_controller.safety import SafetyValidator
from adaptive_controller.config import SafetySettings


def _workspace_tmp() -> Path:
    path = Path(".test-artifacts") / f"knowledge-{uuid4()}"
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


def _snapshot() -> MetricSnapshot:
    service = ServiceMetrics(
        service_name="front-end",
        cpu_usage_cores=_result("cpu_usage_cores", 0.4),
        memory_usage_bytes=_result("memory_usage_bytes", 128.0),
        request_rate_rps=_result("request_rate_rps", 20.0),
        error_rate_rps=_result("error_rate_rps", 0.0),
        latency_p95_seconds=_result("latency_p95_seconds", 0.1),
        desired_replicas=_result("desired_replicas", 2.0),
        current_replicas=_result("current_replicas", 2.0),
        ready_pods=_result("ready_pods", 2.0),
    )
    return MetricSnapshot(namespace="sockshop", window="5m", services=[service])


def _plan() -> AdaptationPlan:
    return AdaptationPlan(
        service_name="front-end",
        action=AdaptationAction.SCALE_UP,
        priority=PlanPriority.HIGH,
        reason="latency violation",
        current_replicas=2,
        target_replicas=3,
        confidence=0.8,
    )


def test_knowledge_store_persists_metrics_and_returns_latest_service_history() -> None:
    path = _workspace_tmp()
    try:
        store = KnowledgeStore(KnowledgeSettings(storage_dir=str(path), max_recent_items=10))

        store.record_metrics(_snapshot())

        latest = store.performance_history.latest_for_service("front-end")
        assert latest is not None
        assert latest["service_name"] == "front-end"
        assert latest["cpu_usage_cores"]["samples"][0]["value"] == 0.4
    finally:
        _cleanup(path)


def test_knowledge_store_persists_plan_validation_and_execution_reports() -> None:
    path = _workspace_tmp()
    try:
        store = KnowledgeStore(KnowledgeSettings(storage_dir=str(path), max_recent_items=10))
        plan = _plan()
        plan_batch = PlanBatch(namespace="sockshop", plans=[plan])
        validation_report = SafetyValidator(SafetySettings()).validate_batch(
            plan_batch,
            current_replicas_by_service={"front-end": 2},
        )
        execution_report = ExecutionReport(
            namespace="sockshop",
            results=[
                ExecutionResult(
                    plan=plan,
                    status=ExecutionStatus.SUCCEEDED,
                    message="scaled",
                )
            ],
        )

        store.record_plan_batch(plan_batch)
        store.record_validation_report(validation_report)
        store.record_execution_report(execution_report)

        assert store.adaptation_repository.recent_plans()[0]["namespace"] == "sockshop"
        assert store.adaptation_repository.recent_validations()[0]["results"][0]["status"] == "approved"
        assert store.adaptation_repository.recent_executions()[0]["results"][0]["status"] == "succeeded"
    finally:
        _cleanup(path)


def test_knowledge_store_loads_policy_files() -> None:
    path = _workspace_tmp()
    try:
        policy_dir = path / "policies"
        policy_dir.mkdir()
        (policy_dir / "safety_constraints.yaml").write_text("min_replicas: 1\n", encoding="utf-8")

        store = KnowledgeStore(
            KnowledgeSettings(storage_dir=str(path / "knowledge")),
            policy_dir=str(policy_dir),
        )

        assert store.policy_registry.get_safety_constraints() == {"min_replicas": 1}
    finally:
        _cleanup(path)


def test_scenario_memory_and_text_search_store_context() -> None:
    path = _workspace_tmp()
    try:
        store = KnowledgeStore(KnowledgeSettings(storage_dir=str(path), max_recent_items=10))

        store.scenario_memory.remember(
            service_name="front-end",
            summary="Latency spike during flash crowd",
            tags=["latency", "flash-crowd"],
        )
        store.vector_store.add_text(
            document_id="case-1",
            text="front-end latency increased during a flash crowd",
        )

        assert store.scenario_memory.find_by_tag("latency")[0]["service_name"] == "front-end"
        assert store.vector_store.search_text("latency flash")[0]["document_id"] == "case-1"
    finally:
        _cleanup(path)


def test_recent_decision_context_combines_available_knowledge() -> None:
    path = _workspace_tmp()
    try:
        store = KnowledgeStore(KnowledgeSettings(storage_dir=str(path), max_recent_items=10))
        store.record_metrics(_snapshot())
        store.record_plan_batch(PlanBatch(namespace="sockshop", plans=[_plan()]))

        context = store.recent_decision_context("front-end")

        assert context["latest_metrics"]["service_name"] == "front-end"
        assert context["recent_plans"][0]["namespace"] == "sockshop"
        assert "policies" in context
    finally:
        _cleanup(path)
