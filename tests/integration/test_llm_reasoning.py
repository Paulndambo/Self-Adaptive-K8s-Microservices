from __future__ import annotations

from datetime import datetime, timezone

from adaptive_controller.analyze import (
    AnalysisFinding,
    AnalysisReport,
    AnalysisSeverity,
    ServiceAnalysis,
    SignalStatus,
)
from adaptive_controller.config import ReasoningSettings
from adaptive_controller.plan import AdaptationAction, AdaptationPlan, PlanBatch, PlanPriority
from adaptive_controller.reasoning import LlmClient, LlmRequest, LlmResponse, PromptBuilder, ReasoningEngine
from adaptive_controller.safety import SafetyValidator
from adaptive_controller.config import SafetySettings


class FakeLlmClient(LlmClient):
    def __init__(self):
        self.requests: list[LlmRequest] = []

    def complete(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return LlmResponse(
            text="Scale-up is justified because latency violated the SLA and safety approved it.",
            model="fake-model",
            provider="fake",
        )


def _analysis_report() -> AnalysisReport:
    finding = AnalysisFinding(
        service_name="front-end",
        signal="latency_p95_seconds",
        status=SignalStatus.VIOLATED,
        severity=AnalysisSeverity.CRITICAL,
        message="p95 latency violates SLA",
        value=0.9,
        threshold=0.5,
    )
    return AnalysisReport(
        namespace="sockshop",
        analyzed_at=datetime.now(timezone.utc),
        window="5m",
        services=[ServiceAnalysis(service_name="front-end", findings=[finding])],
    )


def _plan_batch(target_replicas: int = 3) -> PlanBatch:
    plan = AdaptationPlan(
        service_name="front-end",
        action=AdaptationAction.SCALE_UP,
        priority=PlanPriority.HIGH,
        reason="latency violation",
        current_replicas=2,
        target_replicas=target_replicas,
        confidence=0.8,
    )
    return PlanBatch(namespace="sockshop", plans=[plan])


def _validation_report(plan_batch: PlanBatch):
    return SafetyValidator(SafetySettings(max_replicas=5)).validate_batch(
        plan_batch,
        current_replicas_by_service={"front-end": 2},
    )


def test_reasoning_engine_generates_offline_explanation_without_llm_call() -> None:
    plan_batch = _plan_batch()
    explanation = ReasoningEngine(ReasoningSettings(enabled=False)).explain(
        analysis_report=_analysis_report(),
        plan_batch=plan_batch,
        validation_report=_validation_report(plan_batch),
    )

    assert explanation.llm_response is None
    assert explanation.approved_actions == ["scale_up front-end from 2 to 3 replicas"]
    assert "ready for execution" in explanation.summary


def test_reasoning_engine_calls_llm_when_enabled() -> None:
    client = FakeLlmClient()
    plan_batch = _plan_batch()
    explanation = ReasoningEngine(
        ReasoningSettings(enabled=True, provider="fake", model="fake-model"),
        llm_client=client,
    ).explain(
        analysis_report=_analysis_report(),
        plan_batch=plan_batch,
        validation_report=_validation_report(plan_batch),
    )

    assert len(client.requests) == 1
    assert client.requests[0].metadata["service_name"] == "front-end"
    assert explanation.llm_response is not None
    assert "LLM explanation" in explanation.summary


def test_prompt_builder_includes_safety_boundary_and_validation_status() -> None:
    plan_batch = _plan_batch()
    request = PromptBuilder().build_explanation_prompt(
        analysis_report=_analysis_report(),
        plan_batch=plan_batch,
        validation_report=_validation_report(plan_batch),
        context=ReasoningEngine(ReasoningSettings()).retrieve_context("front-end"),
    )

    assert "must not claim to execute actions" in request.system_prompt
    assert "Safety validation" in request.user_prompt
    assert "approved" in request.user_prompt
    assert "scale_up" in request.user_prompt


def test_reasoning_engine_reports_rejected_actions() -> None:
    plan_batch = _plan_batch(target_replicas=10)
    explanation = ReasoningEngine(ReasoningSettings(enabled=False)).explain(
        analysis_report=_analysis_report(),
        plan_batch=plan_batch,
        validation_report=_validation_report(plan_batch),
    )

    assert explanation.approved_actions == []
    assert explanation.rejected_actions == ["scale_up front-end from 2 to 10 replicas"]
    assert "rejected" in explanation.summary
