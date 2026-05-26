from __future__ import annotations

from adaptive_controller.config import SafetySettings
from adaptive_controller.plan import AdaptationAction, AdaptationPlan
from adaptive_controller.safety.validation_models import ValidationReason


class ReplicaGuard:
    def __init__(self, settings: SafetySettings):
        self.settings = settings

    def validate(self, plan: AdaptationPlan) -> list[ValidationReason]:
        if plan.action not in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}:
            return []
        if plan.target_replicas is None:
            return []

        reasons: list[ValidationReason] = []
        if plan.target_replicas < self.settings.min_replicas:
            reasons.append(
                ValidationReason(
                    guard="replica_guard",
                    message=(
                        f"Target replicas {plan.target_replicas} is below "
                        f"minimum {self.settings.min_replicas}"
                    ),
                )
            )
        if plan.target_replicas > self.settings.max_replicas:
            reasons.append(
                ValidationReason(
                    guard="replica_guard",
                    message=(
                        f"Target replicas {plan.target_replicas} exceeds "
                        f"maximum {self.settings.max_replicas}"
                    ),
                )
            )
        return reasons
