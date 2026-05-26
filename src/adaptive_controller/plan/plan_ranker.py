from __future__ import annotations

from adaptive_controller.plan.plan_models import AdaptationPlan, PlanPriority


class PlanRanker:
    _priority_order = {
        PlanPriority.HIGH: 0,
        PlanPriority.MEDIUM: 1,
        PlanPriority.LOW: 2,
    }

    def rank(self, plans: list[AdaptationPlan]) -> list[AdaptationPlan]:
        return sorted(
            plans,
            key=lambda plan: (
                self._priority_order[plan.priority],
                -plan.confidence,
                plan.service_name,
            ),
        )
