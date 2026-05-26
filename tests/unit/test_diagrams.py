from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _parse(path: str) -> ElementTree.Element:
    return ElementTree.fromstring(_read(path))


def test_drawio_files_are_valid_xml() -> None:
    for path in (
        "docs/diagrams/architecture.drawio",
        "docs/diagrams/control-loop.drawio",
        "docs/diagrams/deployment-view.drawio",
    ):
        root = _parse(path)
        assert root.tag == "mxfile"
        assert root.find("diagram") is not None


def test_architecture_diagram_contains_core_layers() -> None:
    text = _read("docs/diagrams/architecture.drawio")

    for label in ("Monitor", "Analyze", "Plan", "Safety Validator", "Execute", "Knowledge Store", "LLM Reasoning Layer"):
        assert label in text


def test_control_loop_diagram_documents_mape_k_boundary() -> None:
    text = _read("docs/diagrams/control-loop.drawio")

    assert "Knowledge" in text
    assert "explain, not actuate" in text


def test_deployment_diagram_contains_kubernetes_namespaces() -> None:
    text = _read("docs/diagrams/deployment-view.drawio")

    assert "monitoring namespace" in text
    assert "adaptive-controller namespace" in text
    assert "sockshop namespace" in text
