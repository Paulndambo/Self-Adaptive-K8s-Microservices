from __future__ import annotations

from typing import Any

from adaptive_controller.core.exceptions import KubernetesClientError


class KubernetesClient:
    def __init__(self, apps_v1_api: Any | None = None, load_config: bool = True):
        if apps_v1_api is not None:
            self.apps_v1_api = apps_v1_api
            return

        try:
            from kubernetes import client, config
        except ImportError as exc:
            raise KubernetesClientError(
                "The kubernetes package is required for Kubernetes execution"
            ) from exc

        if load_config:
            self._load_kubernetes_config(config)
        self.apps_v1_api = client.AppsV1Api()

    def scale_deployment(
        self,
        namespace: str,
        deployment_name: str,
        replicas: int,
    ) -> dict[str, Any]:
        body = {"spec": {"replicas": replicas}}
        try:
            response = self.apps_v1_api.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=namespace,
                body=body,
            )
        except Exception as exc:
            raise KubernetesClientError(
                f"Failed to scale deployment {namespace}/{deployment_name} to {replicas}"
            ) from exc

        return {
            "namespace": namespace,
            "deployment": deployment_name,
            "replicas": replicas,
            "raw_response": response,
        }

    def read_deployment_replicas(self, namespace: str, deployment_name: str) -> int | None:
        try:
            deployment = self.apps_v1_api.read_namespaced_deployment(
                name=deployment_name,
                namespace=namespace,
            )
        except Exception as exc:
            raise KubernetesClientError(
                f"Failed to read deployment {namespace}/{deployment_name}"
            ) from exc

        spec = getattr(deployment, "spec", None)
        return getattr(spec, "replicas", None)

    def _load_kubernetes_config(self, config_module: Any) -> None:
        try:
            config_module.load_incluster_config()
        except Exception:
            try:
                config_module.load_kube_config()
            except Exception as exc:
                raise KubernetesClientError(
                    "Could not load in-cluster config or local kubeconfig"
                ) from exc
