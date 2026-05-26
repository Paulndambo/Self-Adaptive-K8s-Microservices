from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from adaptive_controller.core import ControlLoopRun, ControlLoopStatus
from adaptive_controller.core.control_loop import ControlLoopResult
from adaptive_controller.monitor import MetricQueryResult, MetricSample, MetricSnapshot, ServiceMetrics
from experiments.runners.collect_results import collect_json_results, write_summary
from experiments.runners.experiment_models import ExperimentConfig
from experiments.runners.run_baseline import run_baseline_snapshot
from experiments.runners.run_experiment import run_adaptive_experiment


class FakeControlLoop:
    def __init__(self):
        self.calls = 0

    def run_once(self, services=None, current_replicas_by_service=None):
        self.calls += 1
        return ControlLoopResult(
            run=ControlLoopRun(
                run_id=f"run-{self.calls}",
                status=ControlLoopStatus.SUCCEEDED,
                started_at=datetime.now(timezone.utc),
                namespace="sockshop",
                services=list(services or []),
            )
        )


def _workspace_tmp() -> Path:
    path = Path(".test-artifacts") / f"experiments-{uuid4()}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def _cleanup(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def _sample(value: float) -> MetricSample:
    return MetricSample(timestamp=datetime.now(timezone.utc), value=value)


def _result(name: str, value: float) -> MetricQueryResult:
    return MetricQueryResult(name=name, query=f"{name}_query", samples=[_sample(value)])


def _snapshot() -> MetricSnapshot:
    service = ServiceMetrics(
        service_name="front-end",
        cpu_usage_cores=_result("cpu_usage_cores", 1.0),
        memory_usage_bytes=_result("memory_usage_bytes", 128.0),
        request_rate_rps=_result("request_rate_rps", 20.0),
        error_rate_rps=_result("error_rate_rps", 0.0),
        latency_p95_seconds=_result("latency_p95_seconds", 0.1),
        desired_replicas=_result("desired_replicas", 2.0),
        current_replicas=_result("current_replicas", 2.0),
        ready_pods=_result("ready_pods", 2.0),
    )
    return MetricSnapshot(namespace="sockshop", window="5m", services=[service])


def test_run_adaptive_experiment_writes_iteration_and_summary_files() -> None:
    path = _workspace_tmp()
    try:
        fake_loop = FakeControlLoop()
        config = ExperimentConfig(
            name="test_adaptive",
            controller="adaptive",
            services=["front-end"],
            iterations=2,
            output_dir=str(path),
            current_replicas_by_service={"front-end": 2},
        )

        record = run_adaptive_experiment(config, control_loop=fake_loop)

        assert record.status == "completed"
        assert record.iterations == 2
        assert fake_loop.calls == 2
        assert (path / "test_adaptive" / "iteration_1.json").exists()
        assert (path / "test_adaptive" / "summary.json").exists()
    finally:
        _cleanup(path)


def test_run_baseline_snapshot_writes_decisions() -> None:
    path = _workspace_tmp()
    try:
        decisions = run_baseline_snapshot(
            controller_name="hpa",
            snapshot=_snapshot(),
            current_replicas_by_service={"front-end": 2},
            output_dir=path,
        )

        assert decisions[0]["controller_name"] == "hpa_baseline"
        assert decisions[0]["action"] == "scale_up"
        assert (path / "hpa_decisions.json").exists()
    finally:
        _cleanup(path)


def test_collect_results_reads_json_files_and_writes_summary() -> None:
    path = _workspace_tmp()
    try:
        (path / "one.json").write_text('{"ok": true}', encoding="utf-8")
        nested = path / "nested"
        nested.mkdir()
        (nested / "two.json").write_text('{"ok": false}', encoding="utf-8")

        records = collect_json_results(path)
        summary = write_summary(path, path / "summary.json")

        assert len(records) == 2
        assert summary["record_count"] == 2
        assert (path / "summary.json").exists()
    finally:
        _cleanup(path)
