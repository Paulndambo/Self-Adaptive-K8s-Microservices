from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


LOAD_TEST_DIR = Path("workloads/online-boutique/load-tests")


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, LOAD_TEST_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


load_generator = _load_module("online_boutique_load_generator", "load_generator.py")
sys.modules["load_generator"] = load_generator
steady_state = _load_module("online_boutique_steady_state", "steady_state.py")
flash_crowd = _load_module("online_boutique_flash_crowd", "flash_crowd.py")
gradual_ramp = _load_module("online_boutique_gradual_ramp", "gradual_ramp.py")


def test_online_boutique_paths_are_domain_specific() -> None:
    assert "/" in load_generator.DEFAULT_PATHS
    assert "/product" in load_generator.DEFAULT_PATHS
    assert "/checkout" in load_generator.DEFAULT_PATHS


def test_online_boutique_steady_state_steps() -> None:
    steps = steady_state.build_steps(duration_seconds=30, users=12)

    assert [(step.duration_seconds, step.users) for step in steps] == [(30, 12)]


def test_online_boutique_flash_crowd_steps() -> None:
    steps = flash_crowd.build_steps(
        duration_seconds=120,
        initial_users=20,
        peak_users=100,
        surge_after_seconds=30,
    )

    assert [(step.duration_seconds, step.users) for step in steps] == [(30, 20), (90, 100)]


def test_online_boutique_gradual_ramp_steps() -> None:
    steps = gradual_ramp.build_steps(
        duration_seconds=180,
        initial_users=10,
        peak_users=30,
        ramp_step_seconds=60,
    )

    assert [(step.duration_seconds, step.users) for step in steps] == [(60, 10), (60, 20), (60, 30)]
