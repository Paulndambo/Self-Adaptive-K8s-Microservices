from __future__ import annotations

from pydantic import BaseModel, Field


class RetrievedContextItem(BaseModel):
    source: str
    content: str
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class RetrievedContext(BaseModel):
    service_name: str
    items: list[RetrievedContextItem] = Field(default_factory=list)

    def as_prompt_text(self) -> str:
        if not self.items:
            return "No prior context was retrieved."
        return "\n".join(
            f"- [{item.source}] {item.content}"
            for item in self.items
        )
