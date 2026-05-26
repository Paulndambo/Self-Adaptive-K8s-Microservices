from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.reports.charts import comparison_chart_bundle
from evaluation.reports.report_models import ControllerSummary, ExperimentReport
from evaluation.reports.tables import controller_summary_table


def load_controller_summaries(path: str | Path) -> list[ControllerSummary]:
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if isinstance(data, dict) and "summaries" in data:
        data = data["summaries"]
    if not isinstance(data, list):
        raise ValueError("summary input must be a list or an object with a summaries field")
    return [ControllerSummary(**item) for item in data]


def generate_markdown_report(report: ExperimentReport) -> str:
    table = controller_summary_table(report.summaries)
    charts = comparison_chart_bundle(report.summaries)
    best_latency = _best_controller(report.summaries, "p95_latency_seconds", lower_is_better=True)
    best_cost = _best_controller(report.summaries, "cost", lower_is_better=True)
    best_stability = _best_controller(report.summaries, "stability_score", lower_is_better=False)

    return (
        f"# {report.title}\n\n"
        "## Controller Summary\n\n"
        f"{table}\n\n"
        "## Key Comparisons\n\n"
        f"- Best p95 latency: {best_latency}\n"
        f"- Lowest cost: {best_cost}\n"
        f"- Best stability score: {best_stability}\n\n"
        "## Chart Data\n\n"
        "```json\n"
        f"{json.dumps(charts, indent=2, sort_keys=True)}\n"
        "```\n"
    )


def write_report(
    summaries: list[ControllerSummary],
    output_file: str | Path,
    title: str = "Adaptive Controller Evaluation Report",
) -> str:
    report = ExperimentReport(title=title, summaries=summaries)
    markdown = generate_markdown_report(report)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return markdown


def _best_controller(
    summaries: list[ControllerSummary],
    metric_name: str,
    lower_is_better: bool,
) -> str:
    if not summaries:
        return "n/a"
    return min(
        summaries,
        key=lambda summary: getattr(summary, metric_name) if lower_is_better else -getattr(summary, metric_name),
    ).controller_name


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Generate a Markdown evaluation report.")
    parser.add_argument("summary_json", help="JSON file containing controller summaries.")
    parser.add_argument("--output", default="experiments/results/summaries/evaluation_report.md")
    parser.add_argument("--title", default="Adaptive Controller Evaluation Report")
    args = parser.parse_args()

    markdown = write_report(
        summaries=load_controller_summaries(args.summary_json),
        output_file=args.output,
        title=args.title,
    )
    print(markdown)


if __name__ == "__main__":
    main()
