from __future__ import annotations

from adaptive_controller.baselines.baseline_models import BaselineAction, BaselineDecision
from adaptive_controller.config import BaselineSettings
from adaptive_controller.monitor import ServiceMetrics


class RuleBasedController:
    controller_name = "rule_based_controller"

    def __init__(self, settings: BaselineSettings):
        self.settings = settings

    def decide(self, metrics: ServiceMetrics, current_replicas: int) -> BaselineDecision:
        latency = metrics.latency_p95_seconds.latest_value
        error_rate = metrics.error_rate_rps.latest_value
        cpu = metrics.cpu_usage_cores.latest_value
        throughput = metrics.request_rate_rps.latest_value

        if self._should_scale_up(cpu, latency, error_rate):
            target = self._clamp(current_replicas + 1)
            return BaselineDecision(
                controller_name=self.controller_name,
                service_name=metrics.service_name,
                action=BaselineAction.SCALE_UP if target > current_replicas else BaselineAction.NO_OP,
                current_replicas=current_replicas,
                target_replicas=target,
                reason="Rule matched high CPU, high latency, or elevated error rate",
                metadata=self._metadata(cpu, latency, error_rate, throughput),
            )

        if self._should_scale_down(cpu, latency, error_rate, throughput):
            target = self._clamp(current_replicas - 1)
            return BaselineDecision(
                controller_name=self.controller_name,
                service_name=metrics.service_name,
                action=BaselineAction.SCALE_DOWN if target < current_replicas else BaselineAction.NO_OP,
                current_replicas=current_replicas,
                target_replicas=target,
                reason="Rule matched low utilization and healthy latency/error signals",
                metadata=self._metadata(cpu, latency, error_rate, throughput),
            )

        return BaselineDecision(
            controller_name=self.controller_name,
            service_name=metrics.service_name,
            action=BaselineAction.NO_OP,
            current_replicas=current_replicas,
            target_replicas=current_replicas,
            reason="No rule matched",
            metadata=self._metadata(cpu, latency, error_rate, throughput),
        )

    def _should_scale_up(
        self,
        cpu: float | None,
        latency: float | None,
        error_rate: float | None,
    ) -> bool:
        return (
            (cpu is not None and cpu > self.settings.target_cpu_cores)
            or (latency is not None and latency > self.settings.target_latency_seconds)
            or (error_rate is not None and error_rate > 0)
        )

    def _should_scale_down(
        self,
        cpu: float | None,
        latency: float | None,
        error_rate: float | None,
        throughput: float | None,
    ) -> bool:
        return (
            cpu is not None
            and cpu < self.settings.target_cpu_cores * 0.5
            and latency is not None
            and latency < self.settings.target_latency_seconds * 0.5
            and (error_rate is None or error_rate == 0)
            and (throughput is None or throughput < 1.0)
        )

    def _clamp(self, replicas: int) -> int:
        return max(self.settings.min_replicas, min(self.settings.max_replicas, replicas))

    def _metadata(
        self,
        cpu: float | None,
        latency: float | None,
        error_rate: float | None,
        throughput: float | None,
    ) -> dict:
        return {
            "cpu_usage_cores": cpu,
            "latency_p95_seconds": latency,
            "error_rate_rps": error_rate,
            "request_rate_rps": throughput,
        }
