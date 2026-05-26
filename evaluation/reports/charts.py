from __future__ import annotations

from evaluation.reports.report_models import ControllerSummary


def bar_chart_series(
    summaries: list[ControllerSummary],
    metric_name: str,
) -> dict:
    values = []
    for summary in summaries:
        if not hasattr(summary, metric_name):
            raise ValueError(f"Unknown summary metric: {metric_name}")
        values.append(
            {
                "controller": summary.controller_name,
                "value": getattr(summary, metric_name),
            }
        )
    return {"type": "bar", "metric": metric_name, "data": values}


def comparison_chart_bundle(summaries: list[ControllerSummary]) -> dict:
    metrics = [
        "average_latency_seconds",
        "p95_latency_seconds",
        "sla_violation_rate",
        "pod_seconds",
        "scaling_events",
        "adaptation_latency_seconds",
        "stability_score",
        "cost",
    ]
    return {
        "charts": [bar_chart_series(summaries, metric_name) for metric_name in metrics]
    }
