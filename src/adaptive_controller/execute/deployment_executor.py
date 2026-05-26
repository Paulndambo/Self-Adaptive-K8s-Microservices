from __future__ import annotations

from adaptive_controller.execute.config_executor import ConfigExecutor
from adaptive_controller.execute.execution_models import ExecutionReport, ExecutionResult, ExecutionStatus
from adaptive_controller.execute.kubernetes_client import KubernetesClient
from adaptive_controller.execute.scaling_executor import ScalingExecutor
from adaptive_controller.plan import AdaptationAction
from adaptive_controller.safety import ValidationReport


class DeploymentExecutor:
    def __init__(
        self,
        namespace: str,
        kubernetes_client: KubernetesClient,
    ):
        self.namespace = namespace
        self.scaling_executor = ScalingExecutor(namespace, kubernetes_client)
        self.config_executor = ConfigExecutor()

    def execute_approved(self, validation_report: ValidationReport) -> ExecutionReport:
        results: list[ExecutionResult] = []
        approved_plan_ids = {plan.plan_id for plan in validation_report.approved_plans}

        for validation_result in validation_report.results:
            plan = validation_result.plan
            if plan.plan_id not in approved_plan_ids:
                results.append(
                    ExecutionResult(
                        plan=plan,
                        status=ExecutionStatus.SKIPPED,
                        message="Plan was rejected by safety validation",
                        metadata={
                            "rejection_reasons": "; ".join(
                                reason.message for reason in validation_result.reasons
                            )
                        },
                    )
                )
                continue

            if plan.action in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}:
                results.append(self.scaling_executor.execute(plan))
            elif plan.action == AdaptationAction.CONFIG_CHANGE:
                results.append(self.config_executor.execute(plan))
            else:
                results.append(
                    ExecutionResult(
                        plan=plan,
                        status=ExecutionStatus.SKIPPED,
                        message="No execution required for no-op plan",
                    )
                )

        return ExecutionReport(namespace=self.namespace, results=results)
