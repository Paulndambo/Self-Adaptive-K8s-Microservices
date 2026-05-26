from __future__ import annotations

from adaptive_controller.execute import ExecutionReport
from adaptive_controller.observability.telemetry import JsonlTelemetrySink, TelemetryEvent
from adaptive_controller.safety import ValidationReport


class AuditLogger:
    def __init__(self, sink: JsonlTelemetrySink):
        self.sink = sink

    def log_validation(self, run_id: str, validation: ValidationReport) -> None:
        self.sink.emit(
            TelemetryEvent(
                event_type="safety_validation",
                run_id=run_id,
                payload=validation.model_dump(mode="json"),
            )
        )

    def log_execution(self, run_id: str, execution: ExecutionReport) -> None:
        self.sink.emit(
            TelemetryEvent(
                event_type="execution",
                run_id=run_id,
                payload=execution.model_dump(mode="json"),
            )
        )
