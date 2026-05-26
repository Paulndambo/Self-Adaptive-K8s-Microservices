from __future__ import annotations

from adaptive_controller.config import KnowledgeSettings
from adaptive_controller.execute import ExecutionReport
from adaptive_controller.knowledge.performance_history import PerformanceHistory
from adaptive_controller.knowledge.policy_registry import PolicyRegistry
from adaptive_controller.knowledge.repositories import (
    AdaptationRepository,
    MetricsRepository,
    PolicyRepository,
)
from adaptive_controller.knowledge.scenario_memory import ScenarioMemory
from adaptive_controller.knowledge.vector_store import VectorStore
from adaptive_controller.monitor import MetricSnapshot
from adaptive_controller.plan import PlanBatch
from adaptive_controller.safety import ValidationReport


class KnowledgeStore:
    def __init__(
        self,
        settings: KnowledgeSettings,
        policy_dir: str = "data/policies",
    ):
        self.settings = settings
        self.metrics_repository = MetricsRepository(settings.storage_dir)
        self.adaptation_repository = AdaptationRepository(settings.storage_dir)
        self.policy_registry = PolicyRegistry(PolicyRepository(policy_dir))
        self.performance_history = PerformanceHistory(
            self.metrics_repository,
            max_recent_items=settings.max_recent_items,
        )
        self.scenario_memory = ScenarioMemory(settings.storage_dir)
        self.vector_store = VectorStore(settings.storage_dir)

    def record_metrics(self, snapshot: MetricSnapshot) -> None:
        self.metrics_repository.save_snapshot(snapshot)

    def record_plan_batch(self, batch: PlanBatch) -> None:
        self.adaptation_repository.save_plan_batch(batch)

    def record_validation_report(self, report: ValidationReport) -> None:
        self.adaptation_repository.save_validation_report(report)

    def record_execution_report(self, report: ExecutionReport) -> None:
        self.adaptation_repository.save_execution_report(report)

    def recent_decision_context(self, service_name: str) -> dict:
        return {
            "latest_metrics": self.performance_history.latest_for_service(service_name),
            "recent_plans": self.adaptation_repository.recent_plans(self.settings.max_recent_items),
            "recent_validations": self.adaptation_repository.recent_validations(
                self.settings.max_recent_items
            ),
            "recent_executions": self.adaptation_repository.recent_executions(
                self.settings.max_recent_items
            ),
            "policies": self.policy_registry.all_policies(),
            "scenarios": self.scenario_memory.recent(self.settings.max_recent_items),
        }
