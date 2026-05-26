from __future__ import annotations

from statistics import mean

from evaluation.metrics.models import AdaptationWindow, ScalingEvent


def scaling_event_count(events: list[ScalingEvent]) -> int:
    return len(events)


def scale_up_count(events: list[ScalingEvent]) -> int:
    return sum(1 for event in events if event.replica_delta > 0)


def scale_down_count(events: list[ScalingEvent]) -> int:
    return sum(1 for event in events if event.replica_delta < 0)


def average_adaptation_latency(windows: list[AdaptationWindow]) -> float:
    if not windows:
        return 0.0
    return mean(window.latency_seconds for window in windows)


def max_adaptation_latency(windows: list[AdaptationWindow]) -> float:
    if not windows:
        return 0.0
    return max(window.latency_seconds for window in windows)
