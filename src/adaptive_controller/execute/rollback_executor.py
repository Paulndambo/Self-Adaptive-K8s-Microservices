from __future__ import annotations

from adaptive_controller.execute.execution_models import ExecutionResult, ExecutionStatus
from adaptive_controller.plan import AdaptationPlan


class RollbackExecutor:
    def rollback(self, plan: AdaptationPlan, reason: str) -> ExecutionResult:
        return ExecutionResult(
            plan=plan,
            status=ExecutionStatus.SKIPPED,
            message=f"Rollback is not implemented yet: {reason}",
        )
