from __future__ import annotations

from statistics import mean, stdev


def cohens_d(control: list[float], treatment: list[float]) -> float:
    if len(control) < 2 or len(treatment) < 2:
        raise ValueError("at least two samples per group are required")

    pooled_count = len(control) + len(treatment) - 2
    pooled_variance = (
        ((len(control) - 1) * stdev(control) ** 2)
        + ((len(treatment) - 1) * stdev(treatment) ** 2)
    ) / pooled_count
    if pooled_variance == 0:
        return 0.0
    return (mean(treatment) - mean(control)) / (pooled_variance ** 0.5)
