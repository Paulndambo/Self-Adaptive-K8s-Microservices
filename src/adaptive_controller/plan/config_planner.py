from __future__ import annotations

from adaptive_controller.analyze import ServiceAnalysis
from adaptive_controller.plan.plan_models import AdaptationPlan


class ConfigPlanner:
    def plan(self, analysis: ServiceAnalysis) -> AdaptationPlan | None:
        return None
