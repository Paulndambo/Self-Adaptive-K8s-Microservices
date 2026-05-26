from __future__ import annotations

from evaluation.metrics.models import TimeSeriesSample


def pod_seconds(replica_samples: list[TimeSeriesSample]) -> float:
    if len(replica_samples) < 2:
        return 0.0

    ordered = sorted(replica_samples, key=lambda sample: sample.timestamp)
    total = 0.0
    for previous, current in zip(ordered, ordered[1:]):
        duration = (current.timestamp - previous.timestamp).total_seconds()
        total += max(0.0, duration) * previous.value
    return total


def average_replicas(replica_samples: list[TimeSeriesSample]) -> float:
    total_duration = _duration_seconds(replica_samples)
    if total_duration == 0:
        return 0.0
    return pod_seconds(replica_samples) / total_duration


def peak_replicas(replica_samples: list[TimeSeriesSample]) -> int:
    if not replica_samples:
        return 0
    return int(max(sample.value for sample in replica_samples))


def _duration_seconds(samples: list[TimeSeriesSample]) -> float:
    if len(samples) < 2:
        return 0.0
    ordered = sorted(samples, key=lambda sample: sample.timestamp)
    return max(0.0, (ordered[-1].timestamp - ordered[0].timestamp).total_seconds())
