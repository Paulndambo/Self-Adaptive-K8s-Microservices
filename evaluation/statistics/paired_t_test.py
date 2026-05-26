from __future__ import annotations

import math
from statistics import mean, stdev


def paired_t_statistic(baseline: list[float], treatment: list[float]) -> float:
    if len(baseline) != len(treatment):
        raise ValueError("baseline and treatment must have the same length")
    if len(baseline) < 2:
        raise ValueError("at least two paired samples are required")

    differences = [t - b for b, t in zip(baseline, treatment)]
    diff_std = stdev(differences)
    if diff_std == 0:
        return 0.0
    return mean(differences) / (diff_std / math.sqrt(len(differences)))
