from __future__ import annotations

from evaluation.metrics.models import TimeSeriesSample
from evaluation.metrics.resource_metrics import pod_seconds


def compute_replica_cost(
    replica_samples: list[TimeSeriesSample],
    cost_per_pod_second: float,
) -> float:
    return pod_seconds(replica_samples) * cost_per_pod_second


def compute_waste_cost(
    actual_replica_samples: list[TimeSeriesSample],
    required_replica_samples: list[TimeSeriesSample],
    cost_per_pod_second: float,
) -> float:
    if len(actual_replica_samples) < 2 or len(required_replica_samples) < 2:
        return 0.0

    required_by_timestamp = {
        sample.timestamp: sample.value
        for sample in required_replica_samples
    }
    waste_samples = []
    for sample in actual_replica_samples:
        required = required_by_timestamp.get(sample.timestamp)
        if required is None:
            continue
        waste = max(0.0, sample.value - required)
        waste_samples.append(
            TimeSeriesSample(timestamp=sample.timestamp, value=waste, labels=sample.labels)
        )
    return pod_seconds(waste_samples) * cost_per_pod_second
