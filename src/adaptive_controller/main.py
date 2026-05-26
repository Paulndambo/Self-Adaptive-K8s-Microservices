from __future__ import annotations

from adaptive_controller.config import load_settings
from adaptive_controller.core import ControlLoop
from adaptive_controller.logging_config import configure_logging


def main() -> None:
    configure_logging()
    settings = load_settings()
    result = ControlLoop(settings=settings, execute_actions=False).run_once()
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
