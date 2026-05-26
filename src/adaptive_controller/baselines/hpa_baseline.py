from __future__ import annotations

import math

from adaptive_controller.baselines.baseline_models import BaselineAction, BaselineDecision
from adaptive_controller.config import BaselineSettings
from adaptive_controller.monitor import ServiceMetrics


class HpaBaseline:
    controller_name = "hpa_baseline"

    def __init__(self, settings: BaselineSettings):
        self.settings = settings

    def decide(self, metrics: ServiceMetrics, current_replicas: int) -> BaselineDecision:
        cpu = metrics.cpu_usage_cores.latest_value
        if cpu is None:
            return self._no_op(metrics.service_name, current_replicas, "CPU metric is unavailable")

        target = self.settings.target_cpu_cores
        upper = target * (1 + self.settings.scale_tolerance_ratio)
        lower = target * (1 - self.settings.scale_tolerance_ratio)

        if cpu > upper:
            desired = math.ceil(current_replicas * cpu / target)
            desired = self._clamp(desired)
            return BaselineDecision(
                controller_name=self.controller_name,
                service_name=metrics.service_name,
                action=BaselineAction.SCALE_UP if desired > current_replicas else BaselineAction.NO_OP,
                current_replicas=current_replicas,
                target_replicas=desired,
                reason="CPU usage is above the HPA target",
                metadata={"cpu_usage_cores": cpu, "target_cpu_cores": target},
            )

        if cpu < lower:
            desired = math.floor(current_replicas * cpu / target)
            desired = self._clamp(desired)
            return BaselineDecision(
                controller_name=self.controller_name,
                service_name=metrics.service_name,
                action=BaselineAction.SCALE_DOWN if desired < current_replicas else BaselineAction.NO_OP,
                current_replicas=current_replicas,
                target_replicas=desired,
                reason="CPU usage is below the HPA target",
                metadata={"cpu_usage_cores": cpu, "target_cpu_cores": target},
            )

        return self._no_op(metrics.service_name, current_replicas, "CPU usage is within HPA tolerance")

    def _clamp(self, replicas: int) -> int:
        return max(self.settings.min_replicas, min(self.settings.max_replicas, replicas))

    def _no_op(self, service_name: str, current_replicas: int, reason: str) -> BaselineDecision:
        return BaselineDecision(
            controller_name=self.controller_name,
            service_name=service_name,
            action=BaselineAction.NO_OP,
            current_replicas=current_replicas,
            target_replicas=current_replicas,
            reason=reason,
        )
