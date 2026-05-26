from __future__ import annotations

from adaptive_controller.analyze import AnalysisReport
from adaptive_controller.config import PlannerSettings
from adaptive_controller.plan.config_planner import ConfigPlanner
from adaptive_controller.plan.plan_models import (
    AdaptationAction,
    AdaptationPlan,
    PlanBatch,
    PlanPriority,
)
from adaptive_controller.plan.plan_ranker import PlanRanker
from adaptive_controller.plan.scaling_planner import ScalingPlanner


class AdaptationPlanner:
    def __init__(self, settings: PlannerSettings):
        self.settings = settings
        self.scaling_planner = ScalingPlanner(settings)
        self.config_planner = ConfigPlanner()
        self.plan_ranker = PlanRanker()

    def plan(
        self,
        report: AnalysisReport,
        current_replicas_by_service: dict[str, int] | None = None,
    ) -> PlanBatch:
        current_replicas_by_service = current_replicas_by_service or {}
        plans: list[AdaptationPlan] = []

        for service_analysis in report.services:
            scaling_plan = self.scaling_planner.plan(
                service_analysis,
                current_replicas=current_replicas_by_service.get(service_analysis.service_name),
            )
            config_plan = self.config_planner.plan(service_analysis)
            service_plans = [plan for plan in (scaling_plan, config_plan) if plan is not None]
            if service_plans:
                plans.extend(service_plans)
            else:
                plans.append(
                    AdaptationPlan(
                        service_name=service_analysis.service_name,
                        action=AdaptationAction.NO_OP,
                        priority=PlanPriority.LOW,
                        reason="No adaptation required for the current analysis report",
                        current_replicas=current_replicas_by_service.get(
                            service_analysis.service_name,
                            self.settings.default_current_replicas,
                        ),
                        target_replicas=current_replicas_by_service.get(
                            service_analysis.service_name,
                            self.settings.default_current_replicas,
                        ),
                        confidence=1.0,
                    )
                )

        return PlanBatch(namespace=report.namespace, plans=self.plan_ranker.rank(plans))
