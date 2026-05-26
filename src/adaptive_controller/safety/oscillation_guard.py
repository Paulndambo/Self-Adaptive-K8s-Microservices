from __future__ import annotations

from datetime import datetime, timezone

from adaptive_controller.config import SafetySettings
from adaptive_controller.plan import AdaptationAction, AdaptationPlan
from adaptive_controller.safety.validation_models import ValidationReason


class OscillationGuard:
    def __init__(self, settings: SafetySettings):
        self.settings = settings

    def validate(
        self,
        plan: AdaptationPlan,
        last_action_at_by_service: dict[str, datetime] | None = None,
    ) -> list[ValidationReason]:
        if plan.action not in {AdaptationAction.SCALE_UP, AdaptationAction.SCALE_DOWN}:
            return []
        if not last_action_at_by_service:
            return []

        last_action_at = last_action_at_by_service.get(plan.service_name)
        if last_action_at is None:
            return []
        if last_action_at.tzinfo is None:
            last_action_at = last_action_at.replace(tzinfo=timezone.utc)

        elapsed_seconds = (datetime.now(timezone.utc) - last_action_at).total_seconds()
        if elapsed_seconds >= self.settings.cooldown_seconds:
            return []

        return [
            ValidationReason(
                guard="oscillation_guard",
                message=(
                    f"Service is within adaptation cooldown: {elapsed_seconds:.0f}s "
                    f"elapsed, {self.settings.cooldown_seconds}s required"
                ),
            )
        ]
