from __future__ import annotations

import json
from pathlib import Path

import yaml


def _load_yaml_documents(path: str) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as file:
        return [document for document in yaml.safe_load_all(file) if document]


def test_sockshop_manifests_define_namespace_deployments_services_and_ingress() -> None:
    namespace = _load_yaml_documents("workloads/sockshop/manifests/namespace.yaml")[0]
    deployments = _load_yaml_documents("workloads/sockshop/manifests/deployments.yaml")
    services = _load_yaml_documents("workloads/sockshop/manifests/services.yaml")
    ingress = _load_yaml_documents("workloads/sockshop/manifests/ingress.yaml")[0]

    assert namespace["metadata"]["name"] == "sockshop"
    assert {item["metadata"]["name"] for item in deployments} == {"front-end", "catalogue", "carts"}
    assert {item["metadata"]["name"] for item in services} == {"front-end", "catalogue", "carts"}
    assert ingress["spec"]["rules"][0]["host"] == "sockshop.local"


def test_controller_rbac_allows_scaling_sockshop_deployments() -> None:
    service_account = _load_yaml_documents("kubernetes/controller/service-account.yaml")[0]
    role = _load_yaml_documents("kubernetes/controller/role.yaml")[0]
    binding = _load_yaml_documents("kubernetes/controller/role-binding.yaml")[0]

    assert service_account["metadata"]["namespace"] == "adaptive-controller"
    assert role["metadata"]["namespace"] == "sockshop"
    assert "deployments/scale" in role["rules"][0]["resources"]
    assert "patch" in role["rules"][0]["verbs"]
    assert binding["subjects"][0]["namespace"] == "adaptive-controller"


def test_controller_deployment_uses_configmap_and_service_account() -> None:
    deployment = _load_yaml_documents("kubernetes/controller/deployment.yaml")[0]
    template_spec = deployment["spec"]["template"]["spec"]
    container = template_spec["containers"][0]

    assert deployment["metadata"]["namespace"] == "adaptive-controller"
    assert template_spec["serviceAccountName"] == "adaptive-controller"
    assert container["envFrom"][0]["configMapRef"]["name"] == "adaptive-controller-config"
    assert container["command"] == ["python", "-m", "adaptive_controller.main"]


def test_hpa_and_monitoring_manifests_are_valid_yaml_json() -> None:
    hpas = _load_yaml_documents("kubernetes/hpa/sockshop-hpa.yaml")
    online_boutique_hpas = _load_yaml_documents("kubernetes/hpa/online-boutique-hpa.yaml")
    service_monitor = _load_yaml_documents("kubernetes/monitoring/servicemonitor.yaml")[0]

    with Path("kubernetes/monitoring/grafana-dashboard.json").open("r", encoding="utf-8") as file:
        dashboard = json.load(file)

    assert {hpa["metadata"]["name"] for hpa in hpas} == {"front-end-hpa", "catalogue-hpa"}
    assert {hpa["metadata"]["name"] for hpa in online_boutique_hpas} == {
        "frontend-hpa",
        "productcatalogservice-hpa",
        "cartservice-hpa",
    }
    assert service_monitor["kind"] == "ServiceMonitor"
    assert dashboard["title"] == "Adaptive Controller Experiment Dashboard"


def test_kind_cluster_exposes_http_ports() -> None:
    cluster = _load_yaml_documents("infra/local/kind-cluster.yaml")[0]
    mappings = cluster["nodes"][0]["extraPortMappings"]

    assert cluster["name"] == "adaptive-microservices"
    assert {"containerPort": 80, "hostPort": 8080, "protocol": "TCP"} in mappings


def test_online_boutique_manifests_define_representative_services() -> None:
    namespace = _load_yaml_documents("workloads/online-boutique/manifests/namespace.yaml")[0]
    deployments = _load_yaml_documents("workloads/online-boutique/manifests/deployments.yaml")
    services = _load_yaml_documents("workloads/online-boutique/manifests/services.yaml")
    ingress = _load_yaml_documents("workloads/online-boutique/manifests/ingress.yaml")[0]

    expected = {"frontend", "productcatalogservice", "cartservice"}
    assert namespace["metadata"]["name"] == "online-boutique"
    assert {item["metadata"]["name"] for item in deployments} == expected
    assert {item["metadata"]["name"] for item in services} == expected
    assert ingress["spec"]["rules"][0]["host"] == "online-boutique.local"
