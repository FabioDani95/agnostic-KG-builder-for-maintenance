from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from httpx import Timeout
from openai import AsyncOpenAI, OpenAI

from backend.config import settings

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_MOCK_RESPONSES_DIR = ROOT_DIR / "tests" / "golden" / "mock_responses"


def llm_mode() -> str:
    return str(os.environ.get("KG_LLM_MODE", "real") or "real").strip().lower()


def is_mock_mode() -> bool:
    return llm_mode() == "mock"


def get_client(
    *,
    timeout: Timeout | float | int | None = None,
    api_key: str | None = None,
    client_factory: Any = OpenAI,
) -> Any:
    if is_mock_mode():
        return MockOpenAI()
    return client_factory(api_key=api_key if api_key is not None else settings.OPENAI_API_KEY, timeout=timeout)


def get_async_client(
    *,
    timeout: Timeout | float | int | None = None,
    api_key: str | None = None,
    client_factory: Any = AsyncOpenAI,
) -> Any:
    if is_mock_mode():
        return MockAsyncOpenAI()
    return client_factory(api_key=api_key if api_key is not None else settings.OPENAI_API_KEY, timeout=timeout)


class _MockUsage:
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    prompt_tokens_details = SimpleNamespace(cached_tokens=0)


class _MockMessage:
    def __init__(self, content: str, tool_calls: list[Any] | None = None):
        self.content = content
        self.tool_calls = tool_calls or []


class _MockChoice:
    def __init__(self, content: str, *, finish_reason: str = "stop", tool_calls: list[Any] | None = None):
        self.finish_reason = finish_reason
        self.message = _MockMessage(content, tool_calls=tool_calls)


class _MockResponse:
    def __init__(self, content: str, *, model: str):
        self.model = model
        self.usage = _MockUsage()
        self.choices = [_MockChoice(content)]


class _MockCompletions:
    def create(self, **kwargs: Any) -> _MockResponse:
        model = str(kwargs.get("model") or settings.MODEL_NAME)
        return _MockResponse(_mock_content(kwargs), model=model)


class _MockAsyncCompletions:
    async def create(self, **kwargs: Any) -> _MockResponse:
        model = str(kwargs.get("model") or settings.MODEL_NAME)
        return _MockResponse(_mock_content(kwargs), model=model)


class MockOpenAI:
    def __init__(self, *args: Any, **kwargs: Any):
        self.chat = SimpleNamespace(completions=_MockCompletions())


class MockAsyncOpenAI:
    def __init__(self, *args: Any, **kwargs: Any):
        self.chat = SimpleNamespace(completions=_MockAsyncCompletions())


def _messages_text(kwargs: dict[str, Any]) -> str:
    parts: list[str] = []
    for message in kwargs.get("messages") or []:
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", "")
        if isinstance(content, str):
            parts.append(content)
    return "\n\n".join(parts)


def _fixture_mock_content(stage: str) -> str | None:
    """Return the fixture-specific mock response for `stage`, if configured.

    `KG_LLM_FIXTURE` selects a directory under tests/golden/mock_responses/
    (overridable via `KG_LLM_MOCK_DIR`). A `<stage>.json` holding only a
    "content" key is returned as raw text; any other JSON payload is dumped
    verbatim, matching what the real model would emit for that stage.
    """
    fixture_id = str(os.environ.get("KG_LLM_FIXTURE", "") or "").strip()
    if not fixture_id or not stage:
        return None
    base = str(os.environ.get("KG_LLM_MOCK_DIR", "") or "").strip()
    base_dir = Path(base) if base else DEFAULT_MOCK_RESPONSES_DIR
    if not base_dir.is_absolute():
        base_dir = ROOT_DIR / base_dir
    path = base_dir / fixture_id / f"{stage}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Unreadable mock fixture response: %s", path)
        return None
    if isinstance(payload, dict) and set(payload.keys()) == {"content"}:
        return str(payload["content"])
    return json.dumps(payload)


def _mock_content(kwargs: dict[str, Any]) -> str:
    text = _messages_text(kwargs)
    lower = text.lower()
    if kwargs.get("tools"):
        return "Mock assistant response."
    stage, generic = _stage_mock_content(lower, text)
    if stage:
        fixture_content = _fixture_mock_content(stage)
        if fixture_content is not None:
            return fixture_content
    return generic


def _stage_mock_content(lower: str, text: str) -> tuple[str | None, str]:
    """Detect the pipeline stage from the prompt and return (stage, generic reply)."""
    if "toc_entries" in lower or "table of contents" in lower:
        return "scoping", json.dumps({
            "product_info": {
                "product_name": "Mock Maintenance Manual",
                "product_short_name": "mock_manual",
                "brand": "Mock",
                "model": "M-1",
                "asset_type": "machine",
                "document_type": "maintenance manual",
                "language": "en",
            },
            "toc_entries": [
                {"title": "Troubleshooting", "page": 1},
                {"title": "Corrective Actions", "page": 2},
            ],
        })
    if "manual_page_start" in lower or '"sections"' in lower or "section selection" in lower:
        return "sections", json.dumps({
            "sections": [
                {
                    "name": "Troubleshooting",
                    "manual_page_start": 1,
                    "manual_page_end": 2,
                    "reasoning": "Mock diagnostic section.",
                }
            ]
        })
    if "exactly three markdown tables" in lower or "output only the three tables" in lower:
        return "extraction", _mock_extraction_tables()
    if "return the same keys" in lower or "stylistically normalized" in lower:
        return None, _echo_json_object(text)
    if "translate" in lower or "translating" in lower:
        return None, _echo_json_object(text)
    if "issues" in lower and ("semantic" in lower or "validation" in lower):
        return "validation", json.dumps({"issues": []})
    if "normalize an ontology node" in lower:
        return "node_normalization", json.dumps({"name": "Mock Node", "description": "Mock normalized node."})
    if "relation extraction agent" in lower:
        # Must win over the generic ontology branch: this stage merges its
        # output after asset-id canonicalisation, so echoing a full ontology
        # here would reintroduce unmapped node ids.
        return "relations", json.dumps({"relations": []})
    if "ontology" in lower or "nodes" in lower:
        return "ontology", json.dumps(_mock_ontology())
    if "relations" in lower and ("relation" in lower or "candidate" in lower):
        return "relations", json.dumps({"relations": []})
    if "resolution" in lower or "failure_mode" in lower:
        return "resolution", json.dumps({"matches": [], "relations": []})
    return None, "Mock assistant response."


def _echo_json_object(text: str) -> str:
    start = text.rfind("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return json.dumps({str(key): str(value) for key, value in parsed.items()})
        except Exception:
            pass
    return "{}"


def _mock_extraction_tables() -> str:
    return "\n\n".join([
        "| symptom_id | name | description | severity | evidence_page |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| SYM-001 | Low Flow | Pump flow is below target. | Medium | 1 |",
        "| failure_mode_id | name | description | material_context | linked_symptom_id | evidence_page |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| FM-001 | Clogged Filter | The inlet filter is clogged. | Hydraulic circuit | SYM-001 | 1 |",
        "| action_id | name | description | instruction_text | source_page | linked_failure_mode_id |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| CA-001 | Clean Filter | Clean or replace the inlet filter. | Stop the pump and clean the filter. | 2 | FM-001 |",
    ])


def _mock_ontology() -> dict[str, Any]:
    return {
        "ontology_name": "MockMaintenanceOntology",
        "version": "1.0",
        "language": "en",
        "source_type": "maintenance manual",
        "source_title": "Mock Maintenance Manual",
        "nodes": {
            "Asset": [
                {
                    "asset_id": "ASSET-001",
                    "name": "Mock Machine",
                    "description": "Machine covered by the mock manual.",
                    "brand": "Mock",
                    "model": "M-1",
                    "asset_type": "machine",
                }
            ],
            "Component": [
                {
                    "component_id": "CMP-001",
                    "name": "Inlet Filter",
                    "description": "Filter on the inlet circuit.",
                    "category": "Hydraulic",
                }
            ],
            "Symptom": [
                {
                    "symptom_id": "SYM-001",
                    "name": "Low Flow",
                    "description": "Pump flow is below target.",
                    "severity": "Medium",
                    "evidence_page": 1,
                }
            ],
            "FailureMode": [
                {
                    "failure_mode_id": "FM-001",
                    "name": "Clogged Filter",
                    "description": "The inlet filter is clogged.",
                    "material_context": "Hydraulic circuit",
                    "linked_symptom_id": "SYM-001",
                    "evidence_page": 1,
                }
            ],
            "CorrectiveAction": [
                {
                    "action_id": "CA-001",
                    "name": "Clean Filter",
                    "description": "Clean or replace the inlet filter.",
                    "instruction_text": "Stop the pump and clean the filter.",
                    "source_type": "maintenance manual",
                    "source_title": "Mock Maintenance Manual",
                    "source_reference": "PAGE 2",
                    "linked_failure_mode_id": "FM-001",
                }
            ],
            "ErrorCode": [],
        },
        "relations": [
            {
                "name": "MAY_INDICATE",
                "from_type": "Symptom",
                "from_id": "SYM-001",
                "to_type": "FailureMode",
                "to_id": "FM-001",
                "evidence": [{"source_page": 1, "source_reference": "", "quote": ""}],
            },
            {
                "name": "RESOLVED_BY",
                "from_type": "FailureMode",
                "from_id": "FM-001",
                "to_type": "CorrectiveAction",
                "to_id": "CA-001",
                "evidence": [{"source_page": 2, "source_reference": "", "quote": ""}],
            },
        ],
    }
