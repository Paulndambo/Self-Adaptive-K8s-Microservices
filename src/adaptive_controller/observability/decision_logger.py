from __future__ import annotations

from adaptive_controller.analyze import AnalysisReport
from adaptive_controller.observability.telemetry import JsonlTelemetrySink, TelemetryEvent
from adaptive_controller.plan import PlanBatch
from adaptive_controller.safety import ValidationReport


class DecisionLogger:
    def __init__(self, sink: JsonlTelemetrySink):
        self.sink = sink

    def log_decision(
        self,
        run_id: str,
        analysis: AnalysisReport,
        plans: PlanBatch,
        validation: ValidationReport,
    ) -> None:
        self.sink.emit(
            TelemetryEvent(
                event_type="decision",
                run_id=run_id,
                payload={
                    "namespace": analysis.namespace,
                    "findings_count": sum(len(service.findings) for service in analysis.services),
                    "plan_count": len(plans.plans),
                    "approved_count": len(validation.approved_plans),
                    "rejected_count": len(validation.rejected_plans),
                    "plans": [plan.model_dump(mode="json") for plan in plans.plans],
                },
            )
        )
