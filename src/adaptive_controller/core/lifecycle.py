from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LifecycleState:
    running: bool = False
    stop_requested: bool = False


class LifecycleManager:
    def __init__(self):
        self.state = LifecycleState()

    def start(self) -> None:
        self.state.running = True
        self.state.stop_requested = False

    def request_stop(self) -> None:
        self.state.stop_requested = True

    def stop(self) -> None:
        self.state.running = False
        self.state.stop_requested = False
