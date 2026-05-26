__all__ = [
    "ControlLoop",
    "ControlLoopResult",
    "ControlLoopRun",
    "ControlLoopStatus",
    "LifecycleManager",
    "LifecycleState",
]


def __getattr__(name: str):
    if name in {"ControlLoop", "ControlLoopResult"}:
        from adaptive_controller.core.control_loop import ControlLoop, ControlLoopResult

        return {"ControlLoop": ControlLoop, "ControlLoopResult": ControlLoopResult}[name]
    if name in {"ControlLoopRun", "ControlLoopStatus"}:
        from adaptive_controller.core.events import ControlLoopRun, ControlLoopStatus

        return {"ControlLoopRun": ControlLoopRun, "ControlLoopStatus": ControlLoopStatus}[name]
    if name in {"LifecycleManager", "LifecycleState"}:
        from adaptive_controller.core.lifecycle import LifecycleManager, LifecycleState

        return {"LifecycleManager": LifecycleManager, "LifecycleState": LifecycleState}[name]
    raise AttributeError(name)
