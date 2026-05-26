from __future__ import annotations

from datetime import datetime, timedelta, timezone

from evaluation.metrics.adaptation_metrics import (
    average_adaptation_latency,
    max_adaptation_latency,
    scale_down_count,
    scale_up_count,
    scaling_event_count,
)
from evaluation.metrics.cost_metrics import compute_replica_cost, compute_waste_cost
from evaluation.metrics.latency_metrics import (
    average_latency,
    median_latency,
    percentile_latency,
    sla_violation_rate,
)
from evaluation.metrics.models import AdaptationWindow, ScalingEvent, TimeSeriesSample
from evaluation.metrics.resource_metrics import average_replicas, peak_replicas, pod_seconds
from evaluation.metrics.stability_metrics import oscillation_count, replica_variance, stability_score
from evaluation.statistics.bonferroni import bonferroni_alpha, bonferroni_significant
from evaluation.statistics.confidence_intervals import mean_confidence_interval
from evaluation.statistics.effect_size import cohens_d
from evaluation.statistics.paired_t_test import paired_t_statistic


def _time(offset_seconds: int) -> datetime:
    return datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=offset_seconds)


def _sample(offset_seconds: int, value: float) -> TimeSeriesSample:
    return TimeSeriesSample(timestamp=_time(offset_seconds), value=value)


def test_latency_metrics_compute_average_percentile_and_sla_rate() -> None:
    samples = [_sample(0, 0.1), _sample(10, 0.2), _sample(20, 0.9), _sample(30, 1.0)]

    assert average_latency(samples) == 0.55
    assert median_latency(samples) == 0.55
    assert percentile_latency(samples, 50) == 0.55
    assert percentile_latency(samples, 100) == 1.0
    assert sla_violation_rate(samples, threshold_seconds=0.5) == 0.5


def test_resource_metrics_compute_pod_seconds_and_average_replicas() -> None:
    samples = [_sample(0, 2), _sample(10, 4), _sample(20, 4)]

    assert pod_seconds(samples) == 60
    assert average_replicas(samples) == 3
    assert peak_replicas(samples) == 4


def test_adaptation_metrics_count_events_and_latency() -> None:
    events = [
        ScalingEvent(
            timestamp=_time(0),
            service_name="front-end",
            from_replicas=2,
            to_replicas=3,
            controller_name="adaptive",
        ),
        ScalingEvent(
            timestamp=_time(60),
            service_name="front-end",
            from_replicas=3,
            to_replicas=2,
            controller_name="adaptive",
        ),
    ]
    windows = [
        AdaptationWindow(detected_at=_time(0), executed_at=_time(5), service_name="front-end"),
        AdaptationWindow(detected_at=_time(10), executed_at=_time(25), service_name="front-end"),
    ]

    assert scaling_event_count(events) == 2
    assert scale_up_count(events) == 1
    assert scale_down_count(events) == 1
    assert average_adaptation_latency(windows) == 10
    assert max_adaptation_latency(windows) == 15


def test_stability_metrics_detect_oscillation_and_variance() -> None:
    events = [
        ScalingEvent(timestamp=_time(0), service_name="front-end", from_replicas=2, to_replicas=3, controller_name="a"),
        ScalingEvent(timestamp=_time(100), service_name="front-end", from_replicas=3, to_replicas=2, controller_name="a"),
        ScalingEvent(timestamp=_time(600), service_name="front-end", from_replicas=2, to_replicas=3, controller_name="a"),
    ]
    samples = [_sample(0, 2), _sample(10, 4), _sample(20, 2)]

    assert oscillation_count(events, window_seconds=300) == 1
    assert round(replica_variance(samples), 4) == 0.8889
    assert 0 < stability_score(events, samples) < 1


def test_cost_metrics_compute_total_and_waste_cost() -> None:
    actual = [_sample(0, 4), _sample(10, 4), _sample(20, 4)]
    required = [_sample(0, 2), _sample(10, 3), _sample(20, 4)]

    assert compute_replica_cost(actual, cost_per_pod_second=0.5) == 40
    assert compute_waste_cost(actual, required, cost_per_pod_second=1.0) == 30


def test_statistics_helpers_compute_research_comparison_values() -> None:
    assert paired_t_statistic([10, 12, 14], [8, 11, 13]) < 0
    assert cohens_d([10, 12, 14], [8, 9, 10]) < 0
    low, high = mean_confidence_interval([10, 12, 14])
    assert low < 12 < high
    assert bonferroni_alpha(0.05, 5) == 0.01
    assert bonferroni_significant([0.001, 0.02], 0.05) == [True, True]
