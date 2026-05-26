from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel

from adaptive_controller.analyze import AnalysisEngine, AnalysisReport
from adaptive_controller.config import Settings, load_settings
from adaptive_controller.core.events import ControlLoopRun, ControlLoopStatus
from adaptive_controller.execute import DeploymentExecutor, ExecutionReport
from adaptive_controller.knowledge import KnowledgeStore
from adaptive_controller.monitor import MetricSnapshot, MetricsCollector
from adaptive_controller.observability import (
    AuditLogger,
    DecisionLogger,
    JsonlTelemetrySink,
    TraceLogger,
)
from adaptive_controller.plan import AdaptationPlanner, PlanBatch
from adaptive_controller.reasoning import DecisionExplanation, ReasoningEngine
from adaptive_controller.safety import SafetyValidator, ValidationReport


class ControlLoopResult(BaseModel):
    run: ControlLoopRun
    metrics: MetricSnapshot | None = None
    analysis: AnalysisReport | None = None
    plans: PlanBatch | None = None
    validation: ValidationReport | None = None
    execution: ExecutionReport | None = None
    explanation: DecisionExplanation | None = None


class ControlLoop:
    def __init__(
        self,
        settings: Settings | None = None,
        metrics_collector: MetricsCollector | None = None,
        analysis_engine: AnalysisEngine | None = None,
        adaptation_planner: AdaptationPlanner | None = None,
        safety_validator: SafetyValidator | None = None,
        deployment_executor: DeploymentExecutor | None = None,
        knowledge_store: KnowledgeStore | None = None,
        reasoning_engine: ReasoningEngine | None = None,
        trace_logger: TraceLogger | None = None,
        decision_logger: DecisionLogger | None = None,
        audit_logger: AuditLogger | None = None,
        execute_actions: bool = False,
    ):
        self.settings = settings or load_settings()
        self.metrics_collector = metrics_collector or MetricsCollector(self.settings.monitor)
        self.analysis_engine = analysis_engine or AnalysisEngine(self.settings.analyzer)
        self.adaptation_planner = adaptation_planner or AdaptationPlanner(self.settings.planner)
        self.safety_validator = safety_validator or SafetyValidator(self.settings.safety)
        self.deployment_executor = deployment_executor
        self.knowledge_store = knowledge_store or KnowledgeStore(self.settings.knowledge)
        self.reasoning_engine = reasoning_engine or ReasoningEngine(
            self.settings.reasoning,
            knowledge_store=self.knowledge_store,
        )
        self.trace_logger = trace_logger
        self.decision_logger = decision_logger
        self.audit_logger = audit_logger
        if self.settings.observability.enabled and (
            self.trace_logger is None or self.decision_logger is None or self.audit_logger is None
        ):
            self.trace_logger = self.trace_logger or TraceLogger(
                JsonlTelemetrySink(f"{self.settings.observability.log_dir}/trace.jsonl")
            )
            self.decision_logger = self.decision_logger or DecisionLogger(
                JsonlTelemetrySink(f"{self.settings.observability.log_dir}/decisions.jsonl")
            )
            self.audit_logger = self.audit_logger or AuditLogger(
                JsonlTelemetrySink(f"{self.settings.observability.log_dir}/audit.jsonl")
            )
        self.execute_actions = execute_actions

    def run_once(
        self,
        services: tuple[str, ...] | list[str] | None = None,
        current_replicas_by_service: dict[str, int] | None = None,
        last_action_at_by_service: dict[str, datetime] | None = None,
    ) -> ControlLoopResult:
        run_id = str(uuid4())
        started_at = datetime.now(timezone.utc)
        selected_services = list(services or self.settings.monitor.services)

        try:
            self._stage_started(run_id, "monitor")
            metrics = self.metrics_collector.collect(services)
            self.knowledge_store.record_metrics(metrics)
            self._stage_completed(run_id, "monitor", service_count=len(metrics.services))

            self._stage_started(run_id, "analyze")
            analysis = self.analysis_engine.analyze(metrics)
            self._stage_completed(
                run_id,
                "analyze",
                findings_count=sum(len(service.findings) for service in analysis.services),
            )

            self._stage_started(run_id, "plan")
            plans = self.adaptation_planner.plan(
                analysis,
                current_replicas_by_service=current_replicas_by_service,
            )
            self.knowledge_store.record_plan_batch(plans)
            self._stage_completed(run_id, "plan", plan_count=len(plans.plans))

            self._stage_started(run_id, "safety")
            validation = self.safety_validator.validate_batch(
                plans,
                current_replicas_by_service=current_replicas_by_service,
                last_action_at_by_service=last_action_at_by_service,
            )
            self.knowledge_store.record_validation_report(validation)
            if self.audit_logger is not None:
                self.audit_logger.log_validation(run_id, validation)
            if self.decision_logger is not None:
                self.decision_logger.log_decision(run_id, analysis, plans, validation)
            self._stage_completed(
                run_id,
                "safety",
                approved_count=len(validation.approved_plans),
                rejected_count=len(validation.rejected_plans),
            )

            execution = None
            if self.execute_actions and self.deployment_executor is not None:
                self._stage_started(run_id, "execute")
                execution = self.deployment_executor.execute_approved(validation)
                self.knowledge_store.record_execution_report(execution)
                if self.audit_logger is not None:
                    self.audit_logger.log_execution(run_id, execution)
                self._stage_completed(run_id, "execute", result_count=len(execution.results))

            self._stage_started(run_id, "reasoning")
            explanation = self.reasoning_engine.explain(
                analysis_report=analysis,
                plan_batch=plans,
                validation_report=validation,
            )
            self._stage_completed(run_id, "reasoning")

            run = ControlLoopRun(
                run_id=run_id,
                status=ControlLoopStatus.SUCCEEDED,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                namespace=metrics.namespace,
                services=selected_services or [service.service_name for service in metrics.services],
                metadata={"execute_actions": self.execute_actions},
            )
            return ControlLoopResult(
                run=run,
                metrics=metrics,
                analysis=analysis,
                plans=plans,
                validation=validation,
                execution=execution,
                explanation=explanation,
            )
        except Exception as exc:
            self._stage_failed(run_id, "control_loop", str(exc))
            run = ControlLoopRun(
                run_id=run_id,
                status=ControlLoopStatus.FAILED,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                namespace=self.settings.monitor.namespace,
                services=selected_services,
                error=str(exc),
                metadata={"execute_actions": self.execute_actions},
            )
            return ControlLoopResult(run=run)

    def _stage_started(self, run_id: str, stage: str) -> None:
        if self.trace_logger is not None:
            self.trace_logger.stage_started(run_id, stage)

    def _stage_completed(self, run_id: str, stage: str, **metadata) -> None:
        if self.trace_logger is not None:
            self.trace_logger.stage_completed(run_id, stage, **metadata)

    def _stage_failed(self, run_id: str, stage: str, error: str) -> None:
        if self.trace_logger is not None:
            self.trace_logger.stage_failed(run_id, stage, error)
