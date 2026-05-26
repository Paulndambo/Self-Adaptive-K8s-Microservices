from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from adaptive_controller.analyze import AnalysisReport, ServiceAnalysis
from adaptive_controller.execute import ExecutionReport
from adaptive_controller.observability import (
    AuditLogger,
    DecisionLogger,
    JsonlTelemetrySink,
    TelemetryRecorder,
    TraceLogger,
)
from adaptive_controller.plan import AdaptationAction, AdaptationPlan, PlanBatch, PlanPriority
from adaptive_controller.safety import SafetyValidator
from adaptive_controller.config import SafetySettings


def _workspace_tmp() -> Path:
    path = Path(".test-artifacts") / f"observability-{uuid4()}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _plan() -> AdaptationPlan:
    return AdaptationPlan(
        service_name="front-end",
        action=AdaptationAction.SCALE_UP,
        priority=PlanPriority.HIGH,
        reason="test",
        current_replicas=2,
        target_replicas=3,
        confidence=0.8,
    )


def test_telemetry_recorder_writes_jsonl_events() -> None:
    path = _workspace_tmp()
    try:
        sink = JsonlTelemetrySink(path / "telemetry.jsonl")
        TelemetryRecorder(sink).record("test_event", run_id="run-1", value=42)

        events = sink.read_events()
        assert events[0]["event_type"] == "test_event"
        assert events[0]["run_id"] == "run-1"
        assert events[0]["payload"]["value"] == 42
    finally:
        _cleanup(path)


def test_trace_decision_and_audit_loggers_write_structured_events() -> None:
    path = _workspace_tmp()
    try:
        trace_sink = JsonlTelemetrySink(path / "trace.jsonl")
        decision_sink = JsonlTelemetrySink(path / "decisions.jsonl")
        audit_sink = JsonlTelemetrySink(path / "audit.jsonl")
        plan_batch = PlanBatch(namespace="sockshop", plans=[_plan()])
        validation = SafetyValidator(SafetySettings()).validate_batch(
            plan_batch,
            current_replicas_by_service={"front-end": 2},
        )
        analysis = AnalysisReport(
            namespace="sockshop",
            analyzed_at=datetime.now(timezone.utc),
            window="5m",
            services=[ServiceAnalysis(service_name="front-end", findings=[])],
        )

        TraceLogger(trace_sink).stage_completed("run-1", "plan", plan_count=1)
        DecisionLogger(decision_sink).log_decision("run-1", analysis, plan_batch, validation)
        AuditLogger(audit_sink).log_validation("run-1", validation)
        AuditLogger(audit_sink).log_execution("run-1", ExecutionReport(namespace="sockshop", results=[]))

        assert trace_sink.read_events()[0]["payload"]["stage"] == "plan"
        assert decision_sink.read_events()[0]["payload"]["approved_count"] == 1
        audit_events = audit_sink.read_events()
        assert audit_events[0]["event_type"] == "safety_validation"
        assert audit_events[1]["event_type"] == "execution"
    finally:
        _cleanup(path)
