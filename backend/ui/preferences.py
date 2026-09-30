"""Settings of the interface, kept in ``workspace/settings.json`` (never versioned).

They apply to runs started from here and to the reading of the machine after an upload.
The OpenAI key is optional: without one the key of ``.env`` is used. A key written here is
stored locally and never sent back to the browser, only its last four characters.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.config import settings as app_settings

REASONING = ("none", "low", "medium", "high")
# OpenAI models the pipeline knows the price of, lightest first.
AGENT_MODELS = ("gpt-6-luna", "gpt-5.6-luna", "gpt-5.4-mini", "gpt-5.6-terra", "gpt-6-sol", "gpt-5.6-sol")


class Preferences(BaseModel):
    # Same defaults as the command line (scripts/kg_v3.py) and the run (RunConfig).
    reasoning: Literal["none", "low", "medium", "high"] = "low"
    reads: int = Field(2, ge=1, le=3)
    agent_model: Literal[AGENT_MODELS] = "gpt-6-luna"  # type: ignore[valid-type]
    agent_reasoning: Literal["none", "low", "medium", "high"] = "medium"
    human_questions: int = Field(10, ge=1, le=30)
    show_code_relations: bool = True
    node_labels: bool = False
    api_key: str | None = None

    def run_flags(self) -> dict[str, Any]:
        """The model settings of a new run, in the keys of jobs.MODEL_FLAGS."""
        return {"reasoning_effort": self.reasoning, "reads": self.reads, "agent_model": self.agent_model,
                "agent_reasoning_effort": self.agent_reasoning, "human_questions": self.human_questions}

    def environment(self) -> dict[str, str]:
        """Environment of a child process: the key written here wins over the one in .env."""
        return {**os.environ, "OPENAI_API_KEY": self.api_key} if self.api_key else dict(os.environ)

    def public(self) -> dict[str, Any]:
        key = self.api_key or app_settings.OPENAI_API_KEY
        return {**self.model_dump(exclude={"api_key"}),
                "key": {"source": "custom" if self.api_key else ("env" if key else "none"),
                        "hint": f"…{key[-4:]}" if key else None},
                "choices": {"reasoning": list(REASONING), "agent_models": list(AGENT_MODELS)}}


class PreferencesStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> Preferences:
        try:
            return Preferences.model_validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            return Preferences()

    def save(self, changes: dict[str, Any]) -> Preferences:
        current = self.load().model_dump()
        if changes.pop("clear_api_key", False):
            current["api_key"] = None
        key = str(changes.pop("api_key", "") or "").strip()
        if key:
            if not key.startswith("sk-") or len(key) < 20:
                raise ValueError("La chiave non sembra una chiave OpenAI (inizia con «sk-»).")
            current["api_key"] = key
        updated = Preferences.model_validate({**current, **changes})
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(updated.model_dump(), indent=1), encoding="utf-8")
        self.path.chmod(0o600)
        return updated
