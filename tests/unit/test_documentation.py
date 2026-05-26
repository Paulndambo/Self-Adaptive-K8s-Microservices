from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_readme_documents_current_pipeline_and_safety_boundary() -> None:
    readme = _read("README.md")

    assert "monitor -> analyze -> plan -> safety -> execute -> knowledge -> reasoning" in readme
    assert "The LLM is never the actuator" in readme
    assert "python -m pytest -p no:cacheprovider" in readme


def test_architecture_docs_cover_core_components() -> None:
    overview = _read("docs/architecture/system-overview.md")
    mape = _read("docs/architecture/mape-k-design.md")
    safety = _read("docs/architecture/safety-validator.md")
    reasoning = _read("docs/architecture/llm-reasoning-layer.md")

    assert "monitor" in overview
    assert "Analyze" in mape
    assert "cooldown" in safety
    assert "does not directly control Kubernetes" in reasoning


def test_experiment_docs_cover_baselines_and_metrics() -> None:
    baselines = _read("docs/experiments/baselines.md")
    metrics = _read("docs/experiments/metrics.md")
    plan = _read("docs/experiments/evaluation-plan.md")

    assert "HPA" in baselines
    assert "PID" in baselines
    assert "SLA violation rate" in metrics
    assert "Bonferroni" in plan
