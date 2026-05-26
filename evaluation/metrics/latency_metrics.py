from __future__ import annotations

from statistics import mean, median

from evaluation.metrics.models import TimeSeriesSample


def average_latency(samples: list[TimeSeriesSample]) -> float:
    if not samples:
        return 0.0
    return mean(sample.value for sample in samples)


def median_latency(samples: list[TimeSeriesSample]) -> float:
    if not samples:
        return 0.0
    return median(sample.value for sample in samples)


def percentile_latency(samples: list[TimeSeriesSample], percentile: float) -> float:
    if not samples:
        return 0.0
    if not 0 <= percentile <= 100:
        raise ValueError("percentile must be between 0 and 100")

    values = sorted(sample.value for sample in samples)
    if len(values) == 1:
        return values[0]

    rank = (percentile / 100) * (len(values) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(values) - 1)
    weight = rank - lower
    return values[lower] * (1 - weight) + values[upper] * weight


def sla_violation_rate(samples: list[TimeSeriesSample], threshold_seconds: float) -> float:
    if not samples:
        return 0.0
    violations = sum(1 for sample in samples if sample.value > threshold_seconds)
    return violations / len(samples)
