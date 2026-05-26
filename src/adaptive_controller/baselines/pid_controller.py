from __future__ import annotations

from dataclasses import dataclass

from adaptive_controller.baselines.baseline_models import BaselineAction, BaselineDecision
from adaptive_controller.config import BaselineSettings
from adaptive_controller.monitor import ServiceMetrics


@dataclass
class PidState:
    integral: float = 0.0
    previous_error: float = 0.0


class PidController:
    controller_name = "pid_controller"

    def __init__(self, settings: BaselineSettings):
        self.settings = settings
        self._state_by_service: dict[str, PidState] = {}

    def decide(self, metrics: ServiceMetrics, current_replicas: int) -> BaselineDecision:
        latency = metrics.latency_p95_seconds.latest_value
        if latency is None:
            return self._decision(
                metrics.service_name,
                BaselineAction.NO_OP,
                current_replicas,
                current_replicas,
                "Latency metric is unavailable",
                {},
            )

        state = self._state_by_service.setdefault(metrics.service_name, PidState())
        error = latency - self.settings.target_latency_seconds
        state.integral += error
        derivative = error - state.previous_error
        state.previous_error = error

        output = (
            self.settings.pid_kp * error
            + self.settings.pid_ki * state.integral
            + self.settings.pid_kd * derivative
        )

        if output > self.settings.target_latency_seconds * self.settings.scale_tolerance_ratio:
            target = self._clamp(current_replicas + max(1, round(output)))
            action = BaselineAction.SCALE_UP if target > current_replicas else BaselineAction.NO_OP
            reason = "PID output indicates latency pressure"
        elif output < -self.settings.target_latency_seconds * self.settings.scale_tolerance_ratio:
            target = self._clamp(current_replicas - max(1, round(abs(output))))
            action = BaselineAction.SCALE_DOWN if target < current_replicas else BaselineAction.NO_OP
            reason = "PID output indicates spare latency capacity"
        else:
            target = current_replicas
            action = BaselineAction.NO_OP
            reason = "PID output is within tolerance"

        return self._decision(
            metrics.service_name,
            action,
            current_replicas,
            target,
            reason,
            {
                "latency_p95_seconds": latency,
                "target_latency_seconds": self.settings.target_latency_seconds,
                "pid_output": output,
            },
        )

    def _clamp(self, replicas: int) -> int:
        return max(self.settings.min_replicas, min(self.settings.max_replicas, replicas))

    def _decision(
        self,
        service_name: str,
        action: BaselineAction,
        current_replicas: int,
        target_replicas: int,
        reason: str,
        metadata: dict,
    ) -> BaselineDecision:
        return BaselineDecision(
            controller_name=self.controller_name,
            service_name=service_name,
            action=action,
            current_replicas=current_replicas,
            target_replicas=target_replicas,
            reason=reason,
            metadata=metadata,
        )
