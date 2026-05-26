from __future__ import annotations

from evaluation.metrics.models import ScalingEvent, TimeSeriesSample


def oscillation_count(events: list[ScalingEvent], window_seconds: int = 300) -> int:
    ordered = sorted(events, key=lambda event: event.timestamp)
    count = 0
    for previous, current in zip(ordered, ordered[1:]):
        if previous.service_name != current.service_name:
            continue
        if previous.replica_delta == 0 or current.replica_delta == 0:
            continue
        opposite_direction = previous.replica_delta * current.replica_delta < 0
        within_window = (current.timestamp - previous.timestamp).total_seconds() <= window_seconds
        if opposite_direction and within_window:
            count += 1
    return count


def replica_variance(replica_samples: list[TimeSeriesSample]) -> float:
    if not replica_samples:
        return 0.0
    values = [sample.value for sample in replica_samples]
    avg = sum(values) / len(values)
    return sum((value - avg) ** 2 for value in values) / len(values)


def stability_score(events: list[ScalingEvent], replica_samples: list[TimeSeriesSample]) -> float:
    penalty = oscillation_count(events) + replica_variance(replica_samples)
    return 1.0 / (1.0 + penalty)
