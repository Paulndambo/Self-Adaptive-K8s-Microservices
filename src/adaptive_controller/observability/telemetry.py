from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TelemetryEvent(BaseModel):
    event_type: str
    run_id: str | None = None
    service_name: str | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class JsonlTelemetrySink:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: TelemetryEvent) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")

    def read_events(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as file:
            return [json.loads(line) for line in file if line.strip()]


class TelemetryRecorder:
    def __init__(self, sink: JsonlTelemetrySink):
        self.sink = sink

    def record(self, event_type: str, run_id: str | None = None, **payload: Any) -> None:
        self.sink.emit(TelemetryEvent(event_type=event_type, run_id=run_id, payload=payload))
