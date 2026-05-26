from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


LOAD_TEST_DIR = Path("workloads/sockshop/load-tests")


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, LOAD_TEST_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load_generator = _load_module("load_generator", "load_generator.py")
steady_state = _load_module("steady_state", "steady_state.py")
flash_crowd = _load_module("flash_crowd", "flash_crowd.py")
gradual_ramp = _load_module("gradual_ramp", "gradual_ramp.py")


def test_steady_state_builds_single_constant_step() -> None:
    steps = steady_state.build_steps(duration_seconds=60, users=50)

    assert len(steps) == 1
    assert steps[0].duration_seconds == 60
    assert steps[0].users == 50


def test_flash_crowd_builds_warmup_and_peak_steps() -> None:
    steps = flash_crowd.build_steps(
        duration_seconds=300,
        initial_users=50,
        peak_users=500,
        surge_after_seconds=60,
    )

    assert [(step.duration_seconds, step.users) for step in steps] == [(60, 50), (240, 500)]


def test_gradual_ramp_builds_increasing_steps() -> None:
    steps = gradual_ramp.build_steps(
        duration_seconds=180,
        initial_users=10,
        peak_users=30,
        ramp_step_seconds=60,
    )

    assert [(step.duration_seconds, step.users) for step in steps] == [(60, 10), (60, 20), (60, 30)]


def test_run_load_test_summarizes_fake_requests() -> None:
    def fake_request(url: str, timeout_seconds: float):
        return load_generator.RequestResult(status_code=200, latency_seconds=0.1, ok=True)

    summary = load_generator.run_load_test(
        scenario="unit",
        base_url="http://example.test",
        steps=[load_generator.LoadStep(duration_seconds=1, users=2)],
        think_time_seconds=0.01,
        request_func=fake_request,
    )

    assert summary.scenario == "unit"
    assert summary.total_requests >= 2
    assert summary.successful_requests == summary.total_requests
    assert summary.failed_requests == 0
    assert summary.average_latency_seconds == pytest.approx(0.1)
    assert summary.p95_latency_seconds == pytest.approx(0.1)
