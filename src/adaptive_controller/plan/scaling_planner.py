from __future__ import annotations

from adaptive_controller.analyze import AnalysisSeverity, ServiceAnalysis, SignalStatus
from adaptive_controller.config import PlannerSettings
from adaptive_controller.plan.plan_models import (
    AdaptationAction,
    AdaptationPlan,
    PlanPriority,
)


class ScalingPlanner:
    def __init__(self, settings: PlannerSettings):
        self.settings = settings

    def plan(
        self,
        analysis: ServiceAnalysis,
        current_replicas: int | None = None,
    ) -> AdaptationPlan | None:
        current = current_replicas or self.settings.default_current_replicas

        scale_up_findings = [
            finding
            for finding in analysis.findings
            if finding.signal in {"cpu_usage_cores", "latency_p95_seconds", "error_rate_rps", "ready_pods"}
            and finding.status in {SignalStatus.HIGH, SignalStatus.VIOLATED, SignalStatus.UNHEALTHY}
        ]
        if scale_up_findings:
            priority = (
                PlanPriority.HIGH
                if any(finding.severity == AnalysisSeverity.CRITICAL for finding in scale_up_findings)
                else PlanPriority.MEDIUM
            )
            return AdaptationPlan(
                service_name=analysis.service_name,
                action=AdaptationAction.SCALE_UP,
                priority=priority,
                reason="Increase replicas to reduce pressure from critical or high-load findings",
                current_replicas=current,
                target_replicas=current + self.settings.scale_step,
                confidence=self.settings.scale_up_confidence,
                source_findings=[finding.signal for finding in scale_up_findings],
            )

        scale_down_findings = [
            finding
            for finding in analysis.findings
            if finding.signal == "request_rate_rps" and finding.status == SignalStatus.LOW
        ]
        if scale_down_findings:
            target = max(0, current - self.settings.scale_step)
            return AdaptationPlan(
                service_name=analysis.service_name,
                action=AdaptationAction.SCALE_DOWN,
                priority=PlanPriority.LOW,
                reason="Reduce replicas because throughput is below the low-throughput threshold",
                current_replicas=current,
                target_replicas=target,
                confidence=self.settings.scale_down_confidence,
                source_findings=[finding.signal for finding in scale_down_findings],
            )

        return None
