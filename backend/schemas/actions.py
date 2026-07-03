from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HumanAction(BaseModel):
    """Widget-originated human action sent to the chat action endpoint."""

    model_config = ConfigDict(extra="allow")

    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    client_action_id: str | None = None
    gate_result: dict[str, Any] | None = None
