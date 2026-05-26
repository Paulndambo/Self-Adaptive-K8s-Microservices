from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from adaptive_controller.baselines import HpaBaseline, PidController, RuleBasedController
from adaptive_controller.config import BaselineSettings
from adaptive_controller.monitor import MetricSnapshot
from experiments.runners.experiment_models import ensure_output_dir


def load_baseline_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def build_baseline_controller(controller_name: str, settings: BaselineSettings | None = None):
    settings = settings or BaselineSettings()
    if controller_name == "hpa":
        return HpaBaseline(settings)
    if controller_name == "pid":
        return PidController(settings)
    if controller_name == "rule_based":
        return RuleBasedController(settings)
    raise ValueError(f"Unsupported baseline controller: {controller_name}")


def run_baseline_snapshot(
    controller_name: str,
    snapshot: MetricSnapshot,
    current_replicas_by_service: dict[str, int],
    output_dir: str | Path = "experiments/results/raw/baselines",
    settings: BaselineSettings | None = None,
) -> list[dict[str, Any]]:
    controller = build_baseline_controller(controller_name, settings)
    decisions = []
    for service_metrics in snapshot.services:
        current_replicas = current_replicas_by_service.get(service_metrics.service_name, 1)
        decision = controller.decide(service_metrics, current_replicas)
        decisions.append(decision.model_dump(mode="json"))

    directory = ensure_output_dir(output_dir)
    output_file = directory / f"{controller_name}_decisions.json"
    with output_file.open("w", encoding="utf-8") as file:
        json.dump(decisions, file, indent=2, sort_keys=True)
    return decisions


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Prepare a baseline controller from config.")
    parser.add_argument("config", help="Path to baseline YAML config.")
    args = parser.parse_args()
    config = load_baseline_config(args.config)
    controller_name = config.get("controller", "hpa")
    controller = build_baseline_controller(controller_name)
    print(f"Loaded baseline controller: {controller.controller_name}")


if __name__ == "__main__":
    main()
