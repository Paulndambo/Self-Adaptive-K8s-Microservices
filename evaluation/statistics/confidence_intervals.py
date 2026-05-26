from __future__ import annotations

from statistics import mean, stdev


def mean_confidence_interval(samples: list[float], z_value: float = 1.96) -> tuple[float, float]:
    if not samples:
        return (0.0, 0.0)
    if len(samples) == 1:
        return (samples[0], samples[0])

    sample_mean = mean(samples)
    standard_error = stdev(samples) / (len(samples) ** 0.5)
    margin = z_value * standard_error
    return (sample_mean - margin, sample_mean + margin)
