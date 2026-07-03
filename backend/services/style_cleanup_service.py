"""Final export-only style normalization with deterministic and guarded LLM passes."""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from typing import Any

from httpx import Timeout
from openai import OpenAI

from backend.app_config import get_style_cleanup_config
from backend.config import settings
from backend.services.language_utils import language_label, normalize_language_code
from backend.services.ontology_semantics import (
    instruction_steps,
    normalize_semantic_text,
    semantic_tokens,
    semantically_equivalent,
)
from backend.services.llm_gateway import get_client
from backend.services.run_metrics import usage_from_response

logger = logging.getLogger(__name__)

_NAME_LIKE_FIELDS = {"name", "material_context", "category"}
_DESCRIPTION_LIKE_FIELDS = {"description"}
_INSTRUCTION_FIELDS = {"instruction_text"}
_PAGE_REF_RE = re.compile(
    r"(?i)\b(?:page|pages|pagina|pagine|seite|seiten)\s+\d+(?:\s*[-–]\s*\d+)?\b"
)
_NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
_CODE_RE = re.compile(r"\b[A-Z]{1,6}(?:[-_/]?[A-Z0-9]{1,8})+\b")
_UNIT_RE = re.compile(r"(?i)(?:°[cf]|%|\b(?:vac|vdc|bar|psi|hz|khz|mhz|kw|kg|mg|mm|cm|min)\b)")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_PERMISSIVE_STEP_MARKER_RE = re.compile(r"(?:(?<=^)|(?<=[\s\n\r]))\d+\.\s+")
_WHITESPACE_RE = re.compile(r"\s+")

_SYSTEM_PROMPT = """\
You are a technical style normalization assistant for ontology export fields.
You will receive a flat JSON object whose values are already validated technical text.
Rewrite only the VALUES to improve grammar, casing, fluency, and consistency.

Rules:
- Do NOT change meaning, scope, or specificity.
- Do NOT add or remove facts, components, failure causes, conditions, or steps.
- Preserve all numbers, units, codes, model names, and page references exactly.
- Preserve the original language of each value. Do not translate.
- Keys ending with "__name": concise standardized technical label, sentence case, no trailing period.
- Keys ending with "__description": one concise factual sentence with terminal punctuation.
- Keys ending with "__material_context" or "__category": concise noun phrase, no trailing period.
- Keys ending with "__instruction_text": keep the same step count and order, formatted as "1. ... 2. ...".
- Return valid JSON only. No commentary. No markdown.
"""


def cleanup_export_ontology(
    ontology: dict[str, Any],
    *,
    target_language: str | None = None,
    model_name: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Normalize export text without altering graph semantics."""
    cfg = get_style_cleanup_config()
    cleaned = deepcopy(ontology)
    report = {
        "enabled": bool(cfg.get("enabled", True)),
        "deterministic_enabled": bool(cfg.get("deterministic_enabled", True)),
        "llm_enabled": bool(cfg.get("llm_enabled", True)),
        "deterministic_fields_seen": 0,
        "deterministic_fields_changed": 0,
        "llm_fields_seen": 0,
        "llm_fields_changed": 0,
        "llm_fields_rejected": 0,
        "model": None,
    }

    nodes = cleaned.get("nodes")
    if not report["enabled"] or not isinstance(nodes, dict):
        return cleaned, {}, report

    editable_fields = cfg.get("editable_fields", {}) or {}

    if report["deterministic_enabled"]:
        normalized_nodes, det_stats = _apply_deterministic_cleanup(nodes, editable_fields)
        cleaned["nodes"] = normalized_nodes
        nodes = normalized_nodes
        report["deterministic_fields_seen"] = det_stats["fields_seen"]
        report["deterministic_fields_changed"] = det_stats["fields_changed"]

    if not report["llm_enabled"]:
        return cleaned, {}, report

    flat_fields = _collect_editable_fields(nodes, editable_fields)
    report["llm_fields_seen"] = len(flat_fields)
    if not flat_fields:
        return cleaned, {}, report

    target_lang = normalize_language_code(target_language or cleaned.get("language"))
    rewrites, usage = _rewrite_fields_with_llm(
        flat_fields=flat_fields,
        target_language=target_lang,
        model_name=model_name,
        timeout_seconds=int(cfg.get("timeout_seconds", 120) or 120),
        max_output_tokens=int(cfg.get("max_output_tokens", 6000) or 6000),
    )
    if usage:
        report["model"] = str(usage.get("model", "") or model_name or settings.MODEL_NAME)
    if not rewrites:
        return cleaned, usage, report

    accepted_updates: dict[str, str] = {}
    for key, original in flat_fields.items():
        candidate = rewrites.get(key)
        if candidate is None or not isinstance(candidate, str):
            continue
        field_name = key.rsplit("__", 1)[-1]
        accepted, normalized_candidate = _accept_llm_rewrite(
            original=original,
            candidate=candidate,
            field_name=field_name,
            cfg=cfg,
        )
        if accepted:
            if normalized_candidate != original:
                accepted_updates[key] = normalized_candidate
                report["llm_fields_changed"] += 1
        elif normalize_semantic_text(candidate) != normalize_semantic_text(original):
            report["llm_fields_rejected"] += 1

    if accepted_updates:
        cleaned["nodes"] = _apply_flat_updates(nodes, accepted_updates)
    return cleaned, usage, report


def _collect_editable_fields(
    nodes: dict[str, list[dict[str, Any]]],
    editable_fields: dict[str, list[str]],
) -> dict[str, str]:
    flat: dict[str, str] = {}
    for node_type, items in nodes.items():
        if not isinstance(items, list):
            continue
        allowed_fields = editable_fields.get(node_type, [])
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            for field_name in allowed_fields:
                value = item.get(field_name)
                if isinstance(value, str) and value.strip():
                    flat[f"node__{node_type}__{idx}__{field_name}"] = value
    return flat


def _apply_flat_updates(
    nodes: dict[str, list[dict[str, Any]]],
    updates: dict[str, str],
) -> dict[str, list[dict[str, Any]]]:
    result = deepcopy(nodes)
    for key, value in updates.items():
        parts = key.split("__")
        if len(parts) != 4 or parts[0] != "node":
            continue
        _, node_type, raw_index, field_name = parts
        if not raw_index.isdigit():
            continue
        index = int(raw_index)
        node_list = result.get(node_type)
        if not isinstance(node_list, list) or index >= len(node_list):
            continue
        if isinstance(node_list[index], dict):
            node_list[index][field_name] = value
    return result


def _apply_deterministic_cleanup(
    nodes: dict[str, list[dict[str, Any]]],
    editable_fields: dict[str, list[str]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    result = deepcopy(nodes)
    fields_seen = 0
    fields_changed = 0
    for node_type, items in result.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            for field_name in editable_fields.get(node_type, []):
                value = item.get(field_name)
                if not isinstance(value, str) or not value.strip():
                    continue
                fields_seen += 1
                normalized = _normalize_field_value(field_name, value)
                if normalized != value:
                    item[field_name] = normalized
                    fields_changed += 1
    return result, {"fields_seen": fields_seen, "fields_changed": fields_changed}


def _normalize_field_value(field_name: str, value: str) -> str:
    if field_name in _INSTRUCTION_FIELDS:
        return _normalize_instruction_text(value)
    if field_name in _DESCRIPTION_LIKE_FIELDS:
        return _normalize_description(value)
    if field_name in _NAME_LIKE_FIELDS:
        return _normalize_phrase(value)
    return _normalize_inline_text(value)


def _normalize_inline_text(value: str) -> str:
    cleaned = str(value or "").replace("\u00a0", " ").strip()
    return _WHITESPACE_RE.sub(" ", cleaned)


def _capitalize_first_alpha(value: str) -> str:
    chars = list(value)
    for index, char in enumerate(chars):
        if char.isalpha():
            if char.islower():
                chars[index] = char.upper()
            break
    return "".join(chars)


def _strip_terminal_punctuation(value: str) -> str:
    return re.sub(r"[ \t\r\n]+$", "", re.sub(r"[.;:,\s]+$", "", value))


def _ensure_terminal_punctuation(value: str) -> str:
    stripped = value.rstrip()
    if not stripped:
        return stripped
    if stripped.endswith((".", "!", "?")):
        return stripped
    return f"{stripped}."


def _normalize_phrase(value: str) -> str:
    cleaned = _normalize_inline_text(value)
    cleaned = _strip_terminal_punctuation(cleaned)
    return _capitalize_first_alpha(cleaned)


def _normalize_description(value: str) -> str:
    cleaned = _normalize_inline_text(value)
    cleaned = _capitalize_first_alpha(cleaned)
    return _ensure_terminal_punctuation(cleaned)


def _normalize_instruction_text(value: str) -> str:
    steps = _style_instruction_steps(value)
    if not steps:
        return _normalize_description(value)
    normalized_steps = []
    for step in steps:
        cleaned = _normalize_inline_text(step)
        cleaned = _capitalize_first_alpha(cleaned)
        cleaned = _ensure_terminal_punctuation(cleaned)
        normalized_steps.append(cleaned)
    return " ".join(f"{index}. {step}" for index, step in enumerate(normalized_steps, start=1))


def _style_instruction_steps(value: str) -> list[str]:
    primary_steps = instruction_steps(value)
    if len(primary_steps) > 1:
        return primary_steps

    raw = str(value or "").replace("\r", "\n").strip()
    if not raw:
        return []
    if _PERMISSIVE_STEP_MARKER_RE.search(raw):
        parts = [
            part.strip(" -\n\t")
            for part in _PERMISSIVE_STEP_MARKER_RE.split(raw)
            if part.strip(" -\n\t")
        ]
        if len(parts) > 1:
            return parts
    return primary_steps


def _rewrite_fields_with_llm(
    *,
    flat_fields: dict[str, str],
    target_language: str,
    model_name: str | None,
    timeout_seconds: int,
    max_output_tokens: int,
) -> tuple[dict[str, str], dict[str, Any]]:
    client = get_client(timeout=Timeout(float(timeout_seconds), connect=10.0), client_factory=OpenAI)
    model = model_name or settings.MODEL_NAME
    target_label = language_label(target_language)
    user_payload = json.dumps(flat_fields, ensure_ascii=False)
    logger.info(
        "[style_cleanup] Rewriting %d export fields in %s using %s",
        len(flat_fields), target_label, model,
    )
    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.0,
            max_completion_tokens=max_output_tokens,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Keep all values in {target_label}. "
                        f"Return the same keys with stylistically normalized values only.\n\n{user_payload}"
                    ),
                },
            ],
        )
    except Exception as exc:  # pragma: no cover - network/API failure path
        logger.warning("[style_cleanup] LLM cleanup failed: %s", exc)
        return {}, {}

    raw = response.choices[0].message.content or "{}"
    usage = usage_from_response(response, "style_cleanup")
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return {str(key): str(value) for key, value in payload.items() if isinstance(value, str)}, usage
    except Exception:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            payload = json.loads(match.group(0))
            if isinstance(payload, dict):
                return {str(key): str(value) for key, value in payload.items() if isinstance(value, str)}, usage
        except Exception:
            logger.warning("[style_cleanup] Could not parse cleanup response JSON")
    return {}, usage


def _accept_llm_rewrite(
    *,
    original: str,
    candidate: str,
    field_name: str,
    cfg: dict[str, Any],
) -> tuple[bool, str]:
    normalized_candidate = _normalize_field_value(field_name, candidate)
    original_text = str(original or "").strip()
    candidate_text = str(normalized_candidate or "").strip()

    if not candidate_text:
        return False, original_text
    if normalize_semantic_text(candidate_text) == normalize_semantic_text(original_text):
        return True, candidate_text

    if bool(cfg.get("preserve_numbers_units_codes", True)):
        if _extract_numbers(original_text) != _extract_numbers(candidate_text):
            return False, original_text
        if _extract_codes(original_text) != _extract_codes(candidate_text):
            return False, original_text
        if _extract_units(original_text) != _extract_units(candidate_text):
            return False, original_text

    if bool(cfg.get("preserve_page_refs", True)):
        if _extract_page_refs(original_text) != _extract_page_refs(candidate_text):
            return False, original_text

    if bool(cfg.get("reject_on_semantic_drift", True)):
        if not _is_semantically_equivalent_enough(original_text, candidate_text, field_name):
            return False, original_text

    if not _passes_length_guardrails(original_text, candidate_text, field_name, cfg):
        return False, original_text

    return True, candidate_text


def _extract_numbers(value: str) -> list[str]:
    return _NUMBER_RE.findall(str(value or ""))


def _extract_codes(value: str) -> list[str]:
    return [match.upper() for match in _CODE_RE.findall(str(value or ""))]


def _extract_units(value: str) -> list[str]:
    return [match.lower() for match in _UNIT_RE.findall(str(value or ""))]


def _extract_page_refs(value: str) -> list[str]:
    return [normalize_semantic_text(match) for match in _PAGE_REF_RE.findall(str(value or ""))]


def _is_semantically_equivalent_enough(original: str, candidate: str, field_name: str) -> bool:
    if field_name in _INSTRUCTION_FIELDS:
        original_steps = _style_instruction_steps(original)
        candidate_steps = _style_instruction_steps(candidate)
        if len(original_steps) != len(candidate_steps):
            return False
        return all(_pair_is_close_enough(left, right, min_overlap=0.55) for left, right in zip(original_steps, candidate_steps))
    return _pair_is_close_enough(original, candidate, min_overlap=0.60)


def _pair_is_close_enough(left: str, right: str, *, min_overlap: float) -> bool:
    if normalize_semantic_text(left) == normalize_semantic_text(right):
        return True
    if semantically_equivalent(left, right, min_ratio=0.68, min_overlap=min_overlap):
        return True

    left_tokens = set(semantic_tokens(left))
    right_tokens = set(semantic_tokens(right))
    if not left_tokens or not right_tokens:
        return False

    forward_overlap = len(left_tokens & right_tokens) / len(left_tokens)
    backward_overlap = len(left_tokens & right_tokens) / len(right_tokens)
    return forward_overlap >= min_overlap and backward_overlap >= 0.55


def _passes_length_guardrails(
    original: str,
    candidate: str,
    field_name: str,
    cfg: dict[str, Any],
) -> bool:
    original_length = max(1, len(original.strip()))
    candidate_length = len(candidate.strip())
    ratio = candidate_length / original_length
    if original_length >= 20 and (ratio < 0.45 or ratio > 1.85):
        return False

    if field_name == "name":
        max_name_tokens = int(cfg.get("max_name_tokens", 10) or 10)
        candidate_token_count = len(candidate.split())
        if candidate_token_count > max_name_tokens and candidate_token_count >= len(original.split()):
            return False

    if field_name == "description":
        max_description_sentences = int(cfg.get("max_description_sentences", 2) or 2)
        if _sentence_count(candidate) > max_description_sentences and _sentence_count(candidate) > _sentence_count(original):
            return False

    return True


def _sentence_count(value: str) -> int:
    text = str(value or "").strip()
    if not text:
        return 0
    return len([segment for segment in _SENTENCE_SPLIT_RE.split(text) if segment.strip()])
