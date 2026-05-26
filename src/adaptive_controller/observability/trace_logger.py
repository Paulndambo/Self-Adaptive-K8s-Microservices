from __future__ import annotations

from adaptive_controller.observability.telemetry import JsonlTelemetrySink, TelemetryEvent


class TraceLogger:
    def __init__(self, sink: JsonlTelemetrySink):
        self.sink = sink

    def stage_started(self, run_id: str, stage: str) -> None:
        self.sink.emit(
            TelemetryEvent(
                event_type="stage_started",
                run_id=run_id,
                payload={"stage": stage},
            )
        )

    def stage_completed(self, run_id: str, stage: str, **metadata) -> None:
        self.sink.emit(
            TelemetryEvent(
                event_type="stage_completed",
                run_id=run_id,
                payload={"stage": stage, **metadata},
            )
        )

    def stage_failed(self, run_id: str, stage: str, error: str) -> None:
        self.sink.emit(
            TelemetryEvent(
                event_type="stage_failed",
                run_id=run_id,
                payload={"stage": stage, "error": error},
            )
        )
