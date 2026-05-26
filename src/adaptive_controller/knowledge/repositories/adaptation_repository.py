from __future__ import annotations

from pathlib import Path

from adaptive_controller.execute import ExecutionReport
from adaptive_controller.knowledge.repositories.jsonl_repository import JsonlRepository
from adaptive_controller.plan import PlanBatch
from adaptive_controller.safety import ValidationReport


class AdaptationRepository:
    def __init__(self, storage_dir: str | Path):
        storage_path = Path(storage_dir)
        self.plans = JsonlRepository(storage_path / "plans.jsonl")
        self.validations = JsonlRepository(storage_path / "validations.jsonl")
        self.executions = JsonlRepository(storage_path / "executions.jsonl")

    def save_plan_batch(self, batch: PlanBatch) -> None:
        self.plans.append(batch.model_dump(mode="json"))

    def save_validation_report(self, report: ValidationReport) -> None:
        self.validations.append(report.model_dump(mode="json"))

    def save_execution_report(self, report: ExecutionReport) -> None:
        self.executions.append(report.model_dump(mode="json"))

    def recent_plans(self, limit: int = 100) -> list[dict]:
        return self.plans.list(limit=limit)

    def recent_validations(self, limit: int = 100) -> list[dict]:
        return self.validations.list(limit=limit)

    def recent_executions(self, limit: int = 100) -> list[dict]:
        return self.executions.list(limit=limit)
