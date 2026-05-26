from __future__ import annotations

from adaptive_controller.config import SafetySettings
from adaptive_controller.core.exceptions import KubernetesClientError
from adaptive_controller.execute import DeploymentExecutor, ExecutionStatus, KubernetesClient, ScalingExecutor
from adaptive_controller.plan import AdaptationAction, AdaptationPlan, PlanBatch, PlanPriority
from adaptive_controller.safety import SafetyValidator


class FakeKubernetesClient:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.scale_calls = []

    def scale_deployment(self, namespace: str, deployment_name: str, replicas: int):
        if self.fail:
            raise KubernetesClientError("fake Kubernetes failure")
        self.scale_calls.append(
            {
                "namespace": namespace,
                "deployment_name": deployment_name,
                "replicas": replicas,
            }
        )
        return {
            "namespace": namespace,
            "deployment": deployment_name,
            "replicas": replicas,
            "raw_response": object(),
        }


def _plan(
    action: AdaptationAction = AdaptationAction.SCALE_UP,
    current: int = 2,
    target: int = 3,
) -> AdaptationPlan:
    return AdaptationPlan(
        service_name="front-end",
        action=action,
        priority=PlanPriority.HIGH,
        reason="test plan",
        current_replicas=current,
        target_replicas=target,
        confidence=0.8,
    )


def test_scaling_executor_scales_deployment() -> None:
    client = FakeKubernetesClient()
    plan = _plan()

    result = ScalingExecutor("sockshop", client).execute(plan)

    assert result.status == ExecutionStatus.SUCCEEDED
    assert result.succeeded is True
    assert client.scale_calls == [
        {"namespace": "sockshop", "deployment_name": "front-end", "replicas": 3}
    ]


def test_scaling_executor_returns_failed_result_when_kubernetes_fails() -> None:
    client = FakeKubernetesClient(fail=True)
    plan = _plan()

    result = ScalingExecutor("sockshop", client).execute(plan)

    assert result.status == ExecutionStatus.FAILED
    assert "fake Kubernetes failure" in result.message


def test_deployment_executor_executes_only_approved_plans() -> None:
    approved_plan = _plan(current=2, target=3)
    rejected_plan = _plan(current=1, target=0)
    validation_report = SafetyValidator(SafetySettings(min_replicas=1)).validate_batch(
        PlanBatch(namespace="sockshop", plans=[approved_plan, rejected_plan]),
        current_replicas_by_service={"front-end": 2},
    )
    client = FakeKubernetesClient()

    report = DeploymentExecutor("sockshop", client).execute_approved(validation_report)

    assert len(report.results) == 2
    assert report.results[0].status == ExecutionStatus.SUCCEEDED
    assert report.results[1].status == ExecutionStatus.SKIPPED
    assert len(client.scale_calls) == 1
    assert client.scale_calls[0]["replicas"] == 3


def test_deployment_executor_skips_no_op_plan() -> None:
    plan = _plan(action=AdaptationAction.NO_OP, current=2, target=2)
    validation_report = SafetyValidator(SafetySettings()).validate_batch(
        PlanBatch(namespace="sockshop", plans=[plan]),
        current_replicas_by_service={"front-end": 2},
    )
    client = FakeKubernetesClient()

    report = DeploymentExecutor("sockshop", client).execute_approved(validation_report)

    assert report.results[0].status == ExecutionStatus.SKIPPED
    assert client.scale_calls == []


def test_kubernetes_client_uses_scale_subresource() -> None:
    class AppsApi:
        def __init__(self):
            self.call = None

        def patch_namespaced_deployment_scale(self, name, namespace, body):
            self.call = {"name": name, "namespace": namespace, "body": body}
            return {"ok": True}

    apps_api = AppsApi()
    client = KubernetesClient(apps_v1_api=apps_api)

    response = client.scale_deployment("sockshop", "front-end", 4)

    assert apps_api.call == {
        "name": "front-end",
        "namespace": "sockshop",
        "body": {"spec": {"replicas": 4}},
    }
    assert response["replicas"] == 4
