from __future__ import annotations

from pydantic import BaseModel, Field


class LlmRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class LlmResponse(BaseModel):
    text: str
    model: str
    provider: str
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class LlmClient:
    def complete(self, request: LlmRequest) -> LlmResponse:
        raise NotImplementedError


class OfflineLlmClient(LlmClient):
    def __init__(self, model: str = "offline-explainer"):
        self.model = model

    def complete(self, request: LlmRequest) -> LlmResponse:
        return LlmResponse(
            text=(
                "Offline reasoning mode is enabled. The deterministic controller "
                "produced the decision, and this explanation is generated without "
                "calling an external LLM."
            ),
            model=self.model,
            provider="offline",
            metadata={"offline": True},
        )
