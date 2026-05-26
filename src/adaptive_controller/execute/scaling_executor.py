from __future__ import annotations

from adaptive_controller.core.exceptions import ExecutionError, UnsupportedExecutionPlanError
from adaptive_controller.execute.execution_models import ExecutionResult, ExecutionStatus
from adaptive_controller.execute.kubernetes_client import KubernetesClient
from adaptive_controller.plan import AdaptationAction, AdaptationPlan


class ScalingExecutor:
    def __init__(self, namespace: str, kubernetes_client: KubernetesClient):
        self.namespace = namespace
        self.kubernetes_client = kubernetes_client

    def execute(self, plan: AdaptationPlan) -> ExecutionResult:
        if plan.action not in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}:
            raise UnsupportedExecutionPlanError(
                f"ScalingExecutor cannot execute action {plan.action}"
            )
        if plan.target_replicas is None:
            raise ExecutionError("Scaling plans must include target_replicas")

        try:
            response = self.kubernetes_client.scale_deployment(
                namespace=self.namespace,
                deployment_name=plan.service_name,
                replicas=plan.target_replicas,
            )
        except ExecutionError as exc:
            return ExecutionResult(
                plan=plan,
                status=ExecutionStatus.FAILED,
                message=str(exc),
            )

        return ExecutionResult(
            plan=plan,
            status=ExecutionStatus.SUCCEEDED,
            message=(
                f"Scaled {self.namespace}/{plan.service_name} "
                f"from {plan.current_replicas} to {plan.target_replicas} replicas"
            ),
            metadata={
                "namespace": response["namespace"],
                "deployment": response["deployment"],
                "replicas": response["replicas"],
            },
        )
