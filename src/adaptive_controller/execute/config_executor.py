from __future__ import annotations

from adaptive_controller.execute.execution_models import ExecutionResult, ExecutionStatus
from adaptive_controller.plan import AdaptationPlan


class ConfigExecutor:
    def execute(self, plan: AdaptationPlan) -> ExecutionResult:
        return ExecutionResult(
            plan=plan,
            status=ExecutionStatus.SKIPPED,
            message="Config-change execution is not implemented yet",
        )
