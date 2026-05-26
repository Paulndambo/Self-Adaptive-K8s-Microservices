from __future__ import annotations

from adaptive_controller.analyze import AnalysisReport
from adaptive_controller.config import ReasoningSettings
from adaptive_controller.knowledge import KnowledgeStore
from adaptive_controller.plan import PlanBatch
from adaptive_controller.reasoning.explanation_generator import (
    DecisionExplanation,
    ExplanationGenerator,
)
from adaptive_controller.reasoning.llm_client import LlmClient, OfflineLlmClient
from adaptive_controller.reasoning.prompt_builder import PromptBuilder
from adaptive_controller.reasoning.retrieved_context import (
    RetrievedContext,
    RetrievedContextItem,
)
from adaptive_controller.safety import ValidationReport


class ReasoningEngine:
    def __init__(
        self,
        settings: ReasoningSettings,
        knowledge_store: KnowledgeStore | None = None,
        llm_client: LlmClient | None = None,
    ):
        self.settings = settings
        self.knowledge_store = knowledge_store
        self.llm_client = llm_client or OfflineLlmClient(settings.model)
        self.prompt_builder = PromptBuilder()
        self.explanation_generator = ExplanationGenerator()

    def explain(
        self,
        analysis_report: AnalysisReport,
        plan_batch: PlanBatch,
        validation_report: ValidationReport,
        service_name: str | None = None,
    ) -> DecisionExplanation:
        selected_service = service_name or self._first_service_name(analysis_report, plan_batch)
        context = self.retrieve_context(selected_service)
        llm_response = None
        if self.settings.enabled:
            request = self.prompt_builder.build_explanation_prompt(
                analysis_report=analysis_report,
                plan_batch=plan_batch,
                validation_report=validation_report,
                context=context,
            )
            llm_response = self.llm_client.complete(request)

        return self.explanation_generator.generate_deterministic(
            analysis_report=analysis_report,
            plan_batch=plan_batch,
            validation_report=validation_report,
            llm_response=llm_response,
        )

    def retrieve_context(self, service_name: str) -> RetrievedContext:
        if self.knowledge_store is None:
            return RetrievedContext(service_name=service_name)

        decision_context = self.knowledge_store.recent_decision_context(service_name)
        items: list[RetrievedContextItem] = []
        latest_metrics = decision_context.get("latest_metrics")
        if latest_metrics:
            items.append(
                RetrievedContextItem(
                    source="performance_history",
                    content=f"Latest metrics are available for {service_name}.",
                    metadata={"service_name": service_name},
                )
            )

        for scenario in decision_context.get("scenarios", [])[: self.settings.max_context_items]:
            items.append(
                RetrievedContextItem(
                    source="scenario_memory",
                    content=str(scenario.get("summary", "")),
                    metadata={"service_name": str(scenario.get("service_name", ""))},
                )
            )

        return RetrievedContext(service_name=service_name, items=items[: self.settings.max_context_items])

    def _first_service_name(self, analysis_report: AnalysisReport, plan_batch: PlanBatch) -> str:
        if analysis_report.services:
            return analysis_report.services[0].service_name
        if plan_batch.plans:
            return plan_batch.plans[0].service_name
        return "unknown"
