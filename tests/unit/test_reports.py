from __future__ import annotations

import json
import shutil
from pathlib import Path
from uuid import uuid4

import pytest

from evaluation.reports.charts import bar_chart_series, comparison_chart_bundle
from evaluation.reports.generate_report import (
    generate_markdown_report,
    load_controller_summaries,
    write_report,
)
from evaluation.reports.report_models import ControllerSummary, ExperimentReport
from evaluation.reports.tables import controller_summary_table


def _workspace_tmp() -> Path:
    path = Path(".test-artifacts") / f"reports-{uuid4()}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _summaries() -> list[ControllerSummary]:
    return [
        ControllerSummary(
            controller_name="adaptive",
            average_latency_seconds=0.12,
            p95_latency_seconds=0.3,
            sla_violation_rate=0.01,
            pod_seconds=1200,
            scaling_events=4,
            adaptation_latency_seconds=2.5,
            stability_score=0.8,
            cost=12,
        ),
        ControllerSummary(
            controller_name="hpa",
            average_latency_seconds=0.2,
            p95_latency_seconds=0.5,
            sla_violation_rate=0.05,
            pod_seconds=1500,
            scaling_events=6,
            adaptation_latency_seconds=4.0,
            stability_score=0.6,
            cost=15,
        ),
    ]


def test_controller_summary_table_renders_markdown() -> None:
    table = controller_summary_table(_summaries())

    assert "| Controller |" in table
    assert "| adaptive | 0.1200 | 0.3000 |" in table
    assert "| hpa | 0.2000 | 0.5000 |" in table


def test_chart_helpers_return_chart_ready_series() -> None:
    series = bar_chart_series(_summaries(), "p95_latency_seconds")
    bundle = comparison_chart_bundle(_summaries())

    assert series["type"] == "bar"
    assert series["data"][0] == {"controller": "adaptive", "value": 0.3}
    assert len(bundle["charts"]) == 8


def test_chart_helper_rejects_unknown_metric() -> None:
    with pytest.raises(ValueError):
        bar_chart_series(_summaries(), "unknown_metric")


def test_generate_markdown_report_includes_key_sections() -> None:
    markdown = generate_markdown_report(
        ExperimentReport(title="Research Results", summaries=_summaries())
    )

    assert "# Research Results" in markdown
    assert "## Controller Summary" in markdown
    assert "Best p95 latency: adaptive" in markdown
    assert "```json" in markdown


def test_load_and_write_report_roundtrip() -> None:
    path = _workspace_tmp()
    try:
        input_file = path / "summaries.json"
        output_file = path / "report.md"
        input_file.write_text(
            json.dumps({"summaries": [summary.model_dump(mode="json") for summary in _summaries()]}),
            encoding="utf-8",
        )

        summaries = load_controller_summaries(input_file)
        markdown = write_report(summaries, output_file, title="Evaluation")

        assert len(summaries) == 2
        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == markdown
    finally:
        _cleanup(path)
