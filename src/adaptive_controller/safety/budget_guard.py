from __future__ import annotations

from adaptive_controller.config import SafetySettings
from adaptive_controller.plan import AdaptationAction, AdaptationPlan
from adaptive_controller.safety.validation_models import ValidationReason


class BudgetGuard:
    def __init__(self, settings: SafetySettings):
        self.settings = settings

    def validate(
        self,
        plan: AdaptationPlan,
        total_replicas_after_plan: int | None = None,
    ) -> list[ValidationReason]:
        if plan.action not in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}:
            return []
        if plan.target_replicas is None:
            return []

        total_replicas = total_replicas_after_plan or plan.target_replicas
        estimated_cost = total_replicas * self.settings.estimated_cost_per_replica
        reasons: list[ValidationReason] = []

        if total_replicas > self.settings.max_total_replicas:
            reasons.append(
                ValidationReason(
                    guard="budget_guard",
                    message=(
                        f"Total replicas {total_replicas} exceeds cluster limit "
                        f"{self.settings.max_total_replicas}"
                    ),
                )
            )
        if estimated_cost > self.settings.max_budget_units:
            reasons.append(
                ValidationReason(
                    guard="budget_guard",
                    message=(
                        f"Estimated cost {estimated_cost:.2f} exceeds budget "
                        f"{self.settings.max_budget_units:.2f}"
                    ),
                )
            )
        return reasons
