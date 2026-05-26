from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class PolicyRepository:
    def __init__(self, policy_dir: str | Path = "data/policies"):
        self.policy_dir = Path(policy_dir)

    def load_policy(self, filename: str) -> dict[str, Any]:
        path = self.policy_dir / filename
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}
        if not isinstance(data, dict):
            return {"value": data}
        return data

    def load_all(self) -> dict[str, dict[str, Any]]:
        if not self.policy_dir.exists():
            return {}
        return {
            path.name: self.load_policy(path.name)
            for path in sorted(self.policy_dir.glob("*.yaml"))
        }
