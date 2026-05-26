from __future__ import annotations

from adaptive_controller.config import SafetySettings
from adaptive_controller.plan import AdaptationAction, AdaptationPlan
from adaptive_controller.safety.validation_models import ValidationReason


class SafetyConstraints:
    def __init__(self, settings: SafetySettings):
        self.settings = settings

    def validate(self, plan: AdaptationPlan) -> list[ValidationReason]:
        reasons: list[ValidationReason] = []
        if plan.action == AdaptationAction.NO_OP:
            return reasons

        if plan.action in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}:
            if plan.current_replicas is None or plan.target_replicas is None:
                reasons.append(
                    ValidationReason(
                        guard="constraints",
                        message="Scaling plans must include current and target replicas",
                    )
                )
            elif plan.current_replicas < 0 or plan.target_replicas < 0:
                reasons.append(
                    ValidationReason(
                        guard="constraints",
                        message="Replica counts cannot be negative",
                    )
                )
        return reasons
