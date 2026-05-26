from __future__ import annotations

from datetime import datetime

from adaptive_controller.config import SafetySettings
from adaptive_controller.plan import AdaptationPlan, PlanBatch
from adaptive_controller.safety.budget_guard import BudgetGuard
from adaptive_controller.safety.constraints import SafetyConstraints
from adaptive_controller.safety.oscillation_guard import OscillationGuard
from adaptive_controller.safety.replica_guard import ReplicaGuard
from adaptive_controller.safety.validation_models import (
    PlanValidationResult,
    ValidationReport,
    ValidationStatus,
)


class SafetyValidator:
    def __init__(self, settings: SafetySettings):
        self.settings = settings
        self.constraints = SafetyConstraints(settings)
        self.replica_guard = ReplicaGuard(settings)
        self.budget_guard = BudgetGuard(settings)
        self.oscillation_guard = OscillationGuard(settings)

    def validate_batch(
        self,
        batch: PlanBatch,
        current_replicas_by_service: dict[str, int] | None = None,
        last_action_at_by_service: dict[str, datetime] | None = None,
    ) -> ValidationReport:
        current_replicas_by_service = current_replicas_by_service or {}
        current_total = sum(current_replicas_by_service.values())
        results = [
            self.validate_plan(
                plan,
                total_replicas_after_plan=self._total_after_plan(plan, current_total),
                last_action_at_by_service=last_action_at_by_service,
            )
            for plan in batch.plans
        ]
        return ValidationReport(namespace=batch.namespace, results=results)

    def validate_plan(
        self,
        plan: AdaptationPlan,
        total_replicas_after_plan: int | None = None,
        last_action_at_by_service: dict[str, datetime] | None = None,
    ) -> PlanValidationResult:
        reasons = []
        reasons.extend(self.constraints.validate(plan))
        reasons.extend(self.replica_guard.validate(plan))
        reasons.extend(self.budget_guard.validate(plan, total_replicas_after_plan))
        reasons.extend(self.oscillation_guard.validate(plan, last_action_at_by_service))

        status = ValidationStatus.REJECTED if reasons else ValidationStatus.APPROVED
        return PlanValidationResult(plan=plan, status=status, reasons=reasons)

    def _total_after_plan(self, plan: AdaptationPlan, current_total: int) -> int | None:
        if plan.current_replicas is None or plan.target_replicas is None:
            return None
        return current_total - plan.current_replicas + plan.target_replicas
