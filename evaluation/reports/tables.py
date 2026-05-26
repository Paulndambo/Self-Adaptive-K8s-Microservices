from __future__ import annotations

from evaluation.reports.report_models import ControllerSummary


TABLE_COLUMNS = [
    "Controller",
    "Avg Latency (s)",
    "P95 Latency (s)",
    "SLA Viol. Rate",
    "Pod-seconds",
    "Scaling Events",
    "Adapt. Latency (s)",
    "Stability",
    "Cost",
]


def controller_summary_rows(summaries: list[ControllerSummary]) -> list[list[str]]:
    return [
        [
            summary.controller_name,
            f"{summary.average_latency_seconds:.4f}",
            f"{summary.p95_latency_seconds:.4f}",
            f"{summary.sla_violation_rate:.4f}",
            f"{summary.pod_seconds:.2f}",
            str(summary.scaling_events),
            f"{summary.adaptation_latency_seconds:.4f}",
            f"{summary.stability_score:.4f}",
            f"{summary.cost:.2f}",
        ]
        for summary in summaries
    ]


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, separator, *body])


def controller_summary_table(summaries: list[ControllerSummary]) -> str:
    return markdown_table(TABLE_COLUMNS, controller_summary_rows(summaries))
