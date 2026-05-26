from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field

from adaptive_controller.plan import AdaptationPlan


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ValidationStatus(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ValidationReason(BaseModel):
    guard: str
    message: str


class PlanValidationResult(BaseModel):
    plan: AdaptationPlan
    status: ValidationStatus
    reasons: list[ValidationReason] = Field(default_factory=list)

    @property
    def approved(self) -> bool:
        return self.status == ValidationStatus.APPROVED


class ValidationReport(BaseModel):
    namespace: str
    validated_at: datetime = Field(default_factory=utc_now)
    results: list[PlanValidationResult] = Field(default_factory=list)

    @property
    def approved_plans(self) -> list[AdaptationPlan]:
        return [result.plan for result in self.results if result.approved]

    @property
    def rejected_plans(self) -> list[AdaptationPlan]:
        return [result.plan for result in self.results if not result.approved]

    @property
    def all_approved(self) -> bool:
        return all(result.approved for result in self.results)
