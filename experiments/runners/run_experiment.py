from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from adaptive_controller.config import load_settings
from adaptive_controller.core import ControlLoop
from experiments.runners.experiment_models import (
    ExperimentConfig,
    ExperimentRunRecord,
    ensure_output_dir,
)


def load_experiment_config(path: str | Path) -> ExperimentConfig:
    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return ExperimentConfig(**data)


def run_adaptive_experiment(
    config: ExperimentConfig,
    control_loop: ControlLoop | None = None,
) -> ExperimentRunRecord:
    output_dir = ensure_output_dir(Path(config.output_dir) / config.name)
    record = ExperimentRunRecord(
        experiment_name=config.name,
        controller=config.controller,
        workload=config.workload,
    )
    loop = control_loop or ControlLoop(settings=load_settings(), execute_actions=config.execute_actions)

    for index in range(config.iterations):
        result = loop.run_once(
            services=config.services,
            current_replicas_by_service=config.current_replicas_by_service,
        )
        output_file = output_dir / f"iteration_{index + 1}.json"
        _write_json(output_file, result.model_dump(mode="json"))
        record.output_files.append(str(output_file))
        record.iterations += 1

    record.status = "completed"
    record.finished_at = datetime.now(timezone.utc)
    summary_file = output_dir / "summary.json"
    _write_json(summary_file, record.model_dump(mode="json"))
    record.output_files.append(str(summary_file))
    return record


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run an adaptive controller experiment.")
    parser.add_argument("config", help="Path to an experiment YAML config.")
    args = parser.parse_args()
    record = run_adaptive_experiment(load_experiment_config(args.config))
    print(record.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
