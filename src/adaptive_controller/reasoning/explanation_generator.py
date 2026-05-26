from __future__ import annotations

from pydantic import BaseModel, Field

from adaptive_controller.analyze import AnalysisReport
from adaptive_controller.plan import AdaptationAction, PlanBatch
from adaptive_controller.reasoning.llm_client import LlmResponse
from adaptive_controller.safety import ValidationReport


class DecisionExplanation(BaseModel):
    summary: str
    approved_actions: list[str] = Field(default_factory=list)
    rejected_actions: list[str] = Field(default_factory=list)
    llm_response: LlmResponse | None = None


class ExplanationGenerator:
    def generate_deterministic(
        self,
        analysis_report: AnalysisReport,
        plan_batch: PlanBatch,
        validation_report: ValidationReport,
        llm_response: LlmResponse | None = None,
    ) -> DecisionExplanation:
        approved_actions = [
            self._describe_plan(plan)
            for plan in validation_report.approved_plans
            if plan.action != AdaptationAction.NO_OP
        ]
        rejected_actions = [
            self._describe_plan(result.plan)
            for result in validation_report.results
            if not result.approved
        ]

        critical = analysis_report.has_critical_findings
        if approved_actions:
            summary = "Safety-approved adaptation actions are ready for execution."
        elif rejected_actions:
            summary = "All proposed adaptation actions were rejected by safety validation."
        elif critical:
            summary = "Critical findings exist, but no executable adaptation was approved."
        else:
            summary = "No adaptation is required for the current snapshot."

        if llm_response is not None:
            summary = f"{summary} LLM explanation: {llm_response.text}"

        return DecisionExplanation(
            summary=summary,
            approved_actions=approved_actions,
            rejected_actions=rejected_actions,
            llm_response=llm_response,
        )

    def _describe_plan(self, plan) -> str:
        if plan.action in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}:
            return (
                f"{plan.action.value} {plan.service_name} from "
                f"{plan.current_replicas} to {plan.target_replicas} replicas"
            )
        return f"{plan.action.value} {plan.service_name}"
