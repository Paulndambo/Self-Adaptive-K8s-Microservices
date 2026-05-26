from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonlRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, sort_keys=True) + "\n")

    def list(self, limit: int | None = None) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            records = [
                json.loads(line)
                for line in file
                if line.strip()
            ]
        if limit is None:
            return records
        return records[-limit:]
