from __future__ import annotations

from datetime import datetime, timedelta, timezone

from adaptive_controller.config import SafetySettings
from adaptive_controller.plan import AdaptationAction, AdaptationPlan, PlanBatch, PlanPriority
from adaptive_controller.safety import SafetyValidator, ValidationStatus


def _scale_plan(
    action: AdaptationAction = AdaptationAction.SCALE_UP,
    current: int | None = 2,
    target: int | None = 3,
) -> AdaptationPlan:
    return AdaptationPlan(
        service_name="front-end",
        action=action,
        priority=PlanPriority.HIGH,
        reason="test plan",
        current_replicas=current,
        target_replicas=target,
        confidence=0.8,
    )


def _batch(*plans: AdaptationPlan) -> PlanBatch:
    return PlanBatch(namespace="sockshop", plans=list(plans))


def test_safety_validator_approves_plan_within_limits() -> None:
    validator = SafetyValidator(SafetySettings(min_replicas=1, max_replicas=5))
    plan = _scale_plan(current=2, target=3)

    report = validator.validate_batch(
        _batch(plan),
        current_replicas_by_service={"front-end": 2},
    )

    assert report.all_approved is True
    assert report.results[0].status == ValidationStatus.APPROVED
    assert report.approved_plans == [plan]
    assert report.rejected_plans == []


def test_safety_validator_rejects_target_below_min_replicas() -> None:
    validator = SafetyValidator(SafetySettings(min_replicas=1, max_replicas=5))
    plan = _scale_plan(action=AdaptationAction.SCALE_DOWN, current=1, target=0)

    report = validator.validate_batch(
        _batch(plan),
        current_replicas_by_service={"front-end": 1},
    )

    assert report.all_approved is False
    assert report.results[0].status == ValidationStatus.REJECTED
    assert report.results[0].reasons[0].guard == "replica_guard"


def test_safety_validator_rejects_target_above_max_replicas() -> None:
    validator = SafetyValidator(SafetySettings(min_replicas=1, max_replicas=5))
    plan = _scale_plan(current=5, target=6)

    report = validator.validate_batch(
        _batch(plan),
        current_replicas_by_service={"front-end": 5},
    )

    assert report.results[0].status == ValidationStatus.REJECTED
    assert any(reason.guard == "replica_guard" for reason in report.results[0].reasons)


def test_safety_validator_rejects_budget_overrun() -> None:
    validator = SafetyValidator(
        SafetySettings(
            min_replicas=1,
            max_replicas=10,
            max_total_replicas=4,
            estimated_cost_per_replica=2.0,
            max_budget_units=8.0,
        )
    )
    plan = _scale_plan(current=3, target=5)

    report = validator.validate_batch(
        _batch(plan),
        current_replicas_by_service={"front-end": 3},
    )

    assert report.results[0].status == ValidationStatus.REJECTED
    assert any(reason.guard == "budget_guard" for reason in report.results[0].reasons)


def test_safety_validator_rejects_plan_inside_cooldown_window() -> None:
    validator = SafetyValidator(SafetySettings(cooldown_seconds=300))
    plan = _scale_plan(current=2, target=3)

    report = validator.validate_batch(
        _batch(plan),
        current_replicas_by_service={"front-end": 2},
        last_action_at_by_service={
            "front-end": datetime.now(timezone.utc) - timedelta(seconds=60)
        },
    )

    assert report.results[0].status == ValidationStatus.REJECTED
    assert any(reason.guard == "oscillation_guard" for reason in report.results[0].reasons)


def test_safety_validator_rejects_scaling_plan_without_replica_counts() -> None:
    validator = SafetyValidator(SafetySettings())
    plan = _scale_plan(current=None, target=None)

    report = validator.validate_batch(_batch(plan))

    assert report.results[0].status == ValidationStatus.REJECTED
    assert any(reason.guard == "constraints" for reason in report.results[0].reasons)


def test_safety_validator_approves_no_op_plan() -> None:
    validator = SafetyValidator(SafetySettings())
    plan = AdaptationPlan(
        service_name="front-end",
        action=AdaptationAction.NO_OP,
        priority=PlanPriority.LOW,
        reason="nothing to do",
        current_replicas=2,
        target_replicas=2,
        confidence=1.0,
    )

    report = validator.validate_batch(_batch(plan))

    assert report.results[0].status == ValidationStatus.APPROVED
