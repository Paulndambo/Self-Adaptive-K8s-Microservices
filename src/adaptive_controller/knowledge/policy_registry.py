from __future__ import annotations

from adaptive_controller.knowledge.repositories import PolicyRepository


class PolicyRegistry:
    def __init__(self, policy_repository: PolicyRepository):
        self.policy_repository = policy_repository

    def get_safety_constraints(self) -> dict:
        return self.policy_repository.load_policy("safety_constraints.yaml")

    def get_scaling_policies(self) -> dict:
        return self.policy_repository.load_policy("scaling_policies.yaml")

    def get_budget_limits(self) -> dict:
        return self.policy_repository.load_policy("budget_limits.yaml")

    def all_policies(self) -> dict[str, dict]:
        return self.policy_repository.load_all()
