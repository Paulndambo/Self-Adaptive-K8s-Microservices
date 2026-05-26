from __future__ import annotations

from adaptive_controller.analyze import AnalysisReport
from adaptive_controller.plan import PlanBatch
from adaptive_controller.reasoning.llm_client import LlmRequest
from adaptive_controller.reasoning.retrieved_context import RetrievedContext
from adaptive_controller.safety import ValidationReport


class PromptBuilder:
    system_prompt = (
        "You support a self-adaptive microservices controller. "
        "You may explain or suggest, but you must not claim to execute actions. "
        "Kubernetes changes are applied only by the deterministic executor after safety validation."
    )

    def build_explanation_prompt(
        self,
        analysis_report: AnalysisReport,
        plan_batch: PlanBatch,
        validation_report: ValidationReport,
        context: RetrievedContext,
    ) -> LlmRequest:
        service_sections = []
        for service in analysis_report.services:
            findings = "\n".join(
                f"- {finding.signal}: {finding.status.value} ({finding.severity.value}) - {finding.message}"
                for finding in service.findings
            ) or "- No findings"
            service_sections.append(f"Service: {service.service_name}\nFindings:\n{findings}")

        plans = "\n".join(
            (
                f"- {plan.service_name}: {plan.action.value} from {plan.current_replicas} "
                f"to {plan.target_replicas}; priority={plan.priority.value}; reason={plan.reason}"
            )
            for plan in plan_batch.plans
        ) or "- No plans"

        validations = "\n".join(
            (
                f"- {result.plan.service_name}: {result.status.value}; "
                f"reasons={'; '.join(reason.message for reason in result.reasons) or 'none'}"
            )
            for result in validation_report.results
        ) or "- No validation results"

        user_prompt = (
            f"Namespace: {analysis_report.namespace}\n\n"
            f"Analysis:\n{chr(10).join(service_sections)}\n\n"
            f"Planned actions:\n{plans}\n\n"
            f"Safety validation:\n{validations}\n\n"
            f"Retrieved context:\n{context.as_prompt_text()}\n\n"
            "Explain why the approved action is reasonable, mention any rejected actions, "
            "and keep the explanation concise and operational."
        )
        return LlmRequest(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            metadata={"namespace": analysis_report.namespace, "service_name": context.service_name},
        )
