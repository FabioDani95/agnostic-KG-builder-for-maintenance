from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineStep(BaseModel):
    """Structured, persistable trace entry for one multi-agent pipeline step."""

    model_config = ConfigDict(extra="allow")

    step: str
    agent: str = ""
    phase: str | None = None
    timestamp: str | None = None
    input_digest: dict[str, Any] = Field(default_factory=dict)
    output_summary: dict[str, Any] = Field(default_factory=dict)
    decision: str = ""
    confidence: float | None = None
    human_handoff: bool = False
    artifacts: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    retry_count: int = 0
    tokens: int = 0
    cost: float = 0.0
