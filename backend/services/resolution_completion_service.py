from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Callable

from httpx import Timeout
from openai import OpenAI

from backend.app_config import get_resolution_completion_config
from backend.config import settings
from backend.models import OntologyEvidence, OntologyInstance, OntologyRelationInstance
from backend.services.llm_guardrails import enforce_llm_limits, llm_timeout_message
from backend.services.llm_gateway import chat_temperature_kwargs, get_client
from backend.services.ontology_semantics import build_semantic_key, semantic_tokens
from backend.services.run_metrics import usage_from_response

logger = logging.getLogger(__name__)


@dataclass
class ResolutionTarget:
    target_type: str  # failure_mode | error_code
    target_id: str
    label: str
    query_text: str
    code: str = ""  # literal machine code for error_code targets


_PAGE_MARKER_RE = re.compile(r"(?m)^--- PAGE (\d+) ---$")
_ID_SAFE_RE = re.compile(r"[^a-z0-9_]+")


def _get_client(timeout_seconds: int) -> OpenAI:
    return get_client(timeout=Timeout(timeout_seconds, connect=10.0), client_factory=OpenAI)


def _node_id(node_type: str, item: dict[str, Any]) -> str:
    id_field = {
        "Asset": "asset_id",
        "Component": "component_id",
        "Symptom": "symptom_id",
        "FailureMode": "failure_mode_id",
        "CorrectiveAction": "action_id",
        "ErrorCode": "error_code_id",
    }.get(node_type, f"{node_type.lower()}_id")
    value = str(item.get(id_field, "") or "").strip()
    if value:
        return value
    for key, raw in item.items():
        if key.endswith("_id") and raw:
            return str(raw).strip()
    return ""


def _slug(value: str, *, prefix: str, fallback: str) -> str:
    text = "_".join(semantic_tokens(value)) or fallback
    cleaned = _ID_SAFE_RE.sub("_", text.lower()).strip("_")
    if not cleaned:
        cleaned = fallback
    return f"{prefix}_{cleaned}" if not cleaned.startswith(f"{prefix}_") else cleaned


def _unique_id(candidate: str, used_ids: set[str], *, prefix: str, fallback: str) -> str:
    base = _slug(candidate, prefix=prefix, fallback=fallback)
    value = base
    index = 2
    while value in used_ids:
        value = f"{base}_{index}"
        index += 1
    used_ids.add(value)
    return value


def _parse_pages(text_with_pages: str) -> list[dict[str, Any]]:
    matches = list(_PAGE_MARKER_RE.finditer(text_with_pages or ""))
    if not matches:
        return [{"page_number": 0, "text": text_with_pages or ""}] if text_with_pages else []
    pages: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text_with_pages)
        page_text = text_with_pages[start:end].strip()
        if page_text:
            pages.append({"page_number": int(match.group(1)), "text": page_text})
    return pages


def _existing_resolution_indexes(ontology: OntologyInstance) -> tuple[set[str], dict[str, set[str]]]:
    resolved_failure_ids: set[str] = set()
    indicated_by_error: dict[str, set[str]] = {}
    for relation in ontology.relations or []:
        if relation.name == "RESOLVED_BY" and relation.from_type == "FailureMode":
            resolved_failure_ids.add(relation.from_id)
        if relation.name == "INDICATES" and relation.from_type == "ErrorCode":
            indicated_by_error.setdefault(relation.from_id, set()).add(relation.to_id)
    return resolved_failure_ids, indicated_by_error


def build_resolution_targets(ontology: OntologyInstance, *, max_targets: int) -> list[ResolutionTarget]:
    resolved_failure_ids, indicated_by_error = _existing_resolution_indexes(ontology)
    targets: list[ResolutionTarget] = []
    seen: set[tuple[str, str]] = set()

    for failure_mode in ontology.nodes.get("FailureMode", []) or []:
        if not isinstance(failure_mode, dict):
            continue
        failure_id = _node_id("FailureMode", failure_mode)
        if not failure_id or failure_id in resolved_failure_ids:
            continue
        label = str(failure_mode.get("name") or failure_id)
        query = " ".join(
            str(failure_mode.get(field, "") or "")
            for field in ("name", "description", "material_context")
        )
        key = ("failure_mode", failure_id)
        if key not in seen:
            targets.append(ResolutionTarget("failure_mode", failure_id, label, query))
            seen.add(key)

    for error_code in ontology.nodes.get("ErrorCode", []) or []:
        if not isinstance(error_code, dict):
            continue
        error_id = _node_id("ErrorCode", error_code)
        if not error_id or indicated_by_error.get(error_id):
            continue
        label = str(error_code.get("name") or error_code.get("code") or error_id)
        query = " ".join(
            str(error_code.get(field, "") or "")
            for field in ("code", "name", "description")
        )
        key = ("error_code", error_id)
        if key not in seen:
            targets.append(ResolutionTarget(
                "error_code",
                error_id,
                label,
                query,
                code=str(error_code.get("code") or "").strip(),
            ))
            seen.add(key)

    return targets[:max(0, int(max_targets or 0))]


def _score_page(target: ResolutionTarget, page_text: str) -> float:
    haystack = page_text.lower()
    query = target.query_text.lower()
    score = 0.0
    for term in sorted(set(semantic_tokens(query)), key=len, reverse=True):
        if len(term) < 2:
            continue
        score += haystack.count(term) * (2.0 if len(term) >= 4 else 1.0)
    key = build_semantic_key(query)
    if key and key in build_semantic_key(page_text, max_tokens=80):
        score += 3.0
    for phrase in ("corrective", "remedy", "repair", "replace", "reset", "reconnect", "adjust", "clean"):
        if phrase in haystack:
            score += 0.75
    if target.target_type == "error_code":
        for token in re.findall(r"[A-Za-z]*\d+[A-Za-z0-9-]*", target.query_text):
            if token.lower() in haystack:
                score += 8.0
    return score


def select_target_pages(
    pages: list[dict[str, Any]],
    target: ResolutionTarget,
    *,
    top_pages: int,
    context_window: int,
) -> list[dict[str, Any]]:
    if not pages:
        return []
    page_lookup = {int(page["page_number"]): page for page in pages}
    scored = [
        (_score_page(target, str(page.get("text", ""))), int(page["page_number"]))
        for page in pages
    ]
    matched = [page_number for score, page_number in sorted(scored, reverse=True) if score > 0]
    if not matched:
        matched = [int(page["page_number"]) for page in pages[:top_pages]]

    selected: set[int] = set()
    for page_number in matched:
        for candidate in range(page_number - context_window, page_number + context_window + 1):
            if candidate in page_lookup:
                selected.add(candidate)
            if len(selected) >= top_pages:
                break
        if len(selected) >= top_pages:
            break
    return [page_lookup[page_number] for page_number in sorted(selected)]


def _format_pages(pages: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"--- PAGE {page['page_number']} ---\n{page['text']}"
        for page in pages
    )


def _target_prompt(target: ResolutionTarget, ontology: OntologyInstance) -> tuple[str, str]:
    compact_nodes = {
        "FailureMode": ontology.nodes.get("FailureMode", []),
        "CorrectiveAction": ontology.nodes.get("CorrectiveAction", []),
        "ErrorCode": ontology.nodes.get("ErrorCode", []),
    }
    system = """You complete missing troubleshooting resolution links in an ontology-first extraction pipeline.
Use only the provided manual pages. Do not invent actions or causes.
Return valid JSON only with this exact shape:
{
  "status": "found|not_found",
  "failure_mode": {
    "failure_mode_id": "existing_or_new_id",
    "name": "technical cause",
    "description": "short cause description",
    "material_context": "component_id_or_asset_level"
  },
  "corrective_actions": [
    {
      "action_id": "ca_descriptive_id",
      "name": "action name",
      "description": "short description",
      "instruction_text": "1. first supported step. 2. second supported step.",
      "source_page": 12,
      "source_reference": "PAGE 12",
      "evidence_quote": "short verbatim quote supporting the action"
    }
  ]
}
Rules:
- For a failure_mode target, keep the provided failure_mode_id.
- For an error_code target, identify the FailureMode the code indicates; reuse an existing FailureMode id when it matches.
- A found result must include at least one restorative CorrectiveAction.
- Inspection-only or verification-only steps are not corrective actions unless the text says they resolve the fault.
- If the selected pages do not contain a supported action, return {"status":"not_found","corrective_actions":[]}.
"""
    user = (
        f"TARGET_TYPE: {target.target_type}\n"
        f"TARGET_ID: {target.target_id}\n"
        f"TARGET_LABEL: {target.label}\n"
        f"TARGET_QUERY: {target.query_text}\n\n"
        "CURRENT ONTOLOGY NODES\n"
        f"{json.dumps(compact_nodes, ensure_ascii=False, indent=2)}\n\n"
        "MANUAL PAGES\n"
    )
    return system, user


def _relation_exists(relations: list[OntologyRelationInstance], candidate: OntologyRelationInstance) -> bool:
    return any(
        relation.name == candidate.name
        and relation.from_type == candidate.from_type
        and relation.from_id == candidate.from_id
        and relation.to_type == candidate.to_type
        and relation.to_id == candidate.to_id
        for relation in relations
    )


def _evidence_from_action(action: dict[str, Any]) -> list[OntologyEvidence]:
    try:
        page = int(action.get("source_page") or 0)
    except (TypeError, ValueError):
        page = 0
    source_reference = str(action.get("source_reference") or "").strip()
    if not source_reference and page:
        source_reference = f"PAGE {page}"
    quote = str(action.get("evidence_quote") or action.get("quote") or "").strip()
    if not (page or source_reference or quote):
        return []
    return [OntologyEvidence(source_page=page, source_reference=source_reference, quote=quote)]


def _apply_completion_payload(
    ontology: OntologyInstance,
    target: ResolutionTarget,
    payload: dict[str, Any],
) -> tuple[OntologyInstance, bool]:
    if str(payload.get("status") or "").strip().lower() != "found":
        return ontology, False
    raw_actions = payload.get("corrective_actions")
    if not isinstance(raw_actions, list) or not raw_actions:
        return ontology, False

    data = ontology.model_dump()
    nodes = data.setdefault("nodes", {})
    relations = [
        OntologyRelationInstance.model_validate(relation)
        for relation in data.setdefault("relations", [])
        if isinstance(relation, dict)
    ]

    used_ids = {
        _node_id(node_type, item)
        for node_type, items in nodes.items()
        for item in (items or [])
        if isinstance(item, dict)
    }
    used_ids = {item for item in used_ids if item}

    failure_id = target.target_id if target.target_type == "failure_mode" else ""
    if target.target_type == "error_code":
        raw_fm = payload.get("failure_mode") if isinstance(payload.get("failure_mode"), dict) else {}
        candidate_fm_id = str(raw_fm.get("failure_mode_id") or "").strip()
        existing_failure_ids = {
            _node_id("FailureMode", item)
            for item in nodes.get("FailureMode", []) or []
            if isinstance(item, dict)
        }
        if candidate_fm_id in existing_failure_ids:
            failure_id = candidate_fm_id
        else:
            failure_id = _unique_id(
                str(raw_fm.get("name") or target.label),
                used_ids,
                prefix="fm",
                fallback="retrieved_failure_mode",
            )
            nodes.setdefault("FailureMode", []).append({
                "failure_mode_id": failure_id,
                "name": str(raw_fm.get("name") or target.label).strip(),
                "description": str(raw_fm.get("description") or raw_fm.get("name") or target.label).strip(),
                "material_context": str(raw_fm.get("material_context") or "asset_level").strip(),
                "related_measurements": raw_fm.get("related_measurements", []),
            })

        evidence = _evidence_from_action(raw_actions[0] if isinstance(raw_actions[0], dict) else {})
        indicates = OntologyRelationInstance(
            name="INDICATES",
            from_type="ErrorCode",
            from_id=target.target_id,
            to_type="FailureMode",
            to_id=failure_id,
            evidence=evidence,
        )
        if not _relation_exists(relations, indicates):
            relations.append(indicates)

    if not failure_id:
        return ontology, False

    changed = False
    for raw_action in raw_actions:
        if not isinstance(raw_action, dict):
            continue
        name = str(raw_action.get("name") or "").strip()
        instruction_text = str(raw_action.get("instruction_text") or "").strip()
        if not name or not instruction_text:
            continue
        evidence_quote = str(raw_action.get("evidence_quote") or raw_action.get("quote") or "").strip()
        if not evidence_quote:
            logger.info(
                "[resolution_completion] Dropping retrieved action '%s' for %s — no verbatim evidence quote",
                name,
                target.target_id,
            )
            continue
        action_id = str(raw_action.get("action_id") or "").strip()
        if not action_id or action_id in used_ids:
            action_id = _unique_id(name, used_ids, prefix="ca", fallback="retrieved_corrective_action")
        else:
            used_ids.add(action_id)
        try:
            source_page = int(raw_action.get("source_page") or 0)
        except (TypeError, ValueError):
            source_page = 0
        source_reference = str(raw_action.get("source_reference") or "").strip()
        if not source_reference and source_page:
            source_reference = f"PAGE {source_page}"
        nodes.setdefault("CorrectiveAction", []).append({
            "action_id": action_id,
            "name": name,
            "description": str(raw_action.get("description") or name).strip(),
            "instruction_text": instruction_text,
            "source_type": ontology.source_type,
            "source_title": ontology.source_title,
            "source_page": source_page,
            "source_reference": source_reference,
        })
        resolved_by = OntologyRelationInstance(
            name="RESOLVED_BY",
            from_type="FailureMode",
            from_id=failure_id,
            to_type="CorrectiveAction",
            to_id=action_id,
            evidence=_evidence_from_action(raw_action),
        )
        if not _relation_exists(relations, resolved_by):
            relations.append(resolved_by)
            changed = True

    if not changed:
        return ontology, False
    data["relations"] = [relation.model_dump() for relation in relations]
    return OntologyInstance.model_validate(data), True


def complete_resolution_gaps(
    *,
    ontology: OntologyInstance,
    text_with_pages: str,
    model_name: str,
    parse_json: Callable[[str], dict[str, Any]],
) -> tuple[OntologyInstance, list[dict[str, Any]], dict[str, Any]]:
    cfg = get_resolution_completion_config()
    if not cfg.get("enabled", True):
        return ontology, [], {"attempted": 0, "completed": 0, "skipped": "disabled"}

    pages = _parse_pages(text_with_pages)
    targets = build_resolution_targets(ontology, max_targets=int(cfg.get("max_targets", 8)))
    if not pages or not targets:
        return ontology, [], {"attempted": 0, "completed": 0, "target_count": len(targets)}

    usage_entries: list[dict[str, Any]] = []
    completed = 0
    attempts: list[dict[str, Any]] = []
    client = _get_client(int(cfg.get("timeout_seconds", 90)))
    updated = ontology

    for target in targets:
        selected_pages = select_target_pages(
            pages,
            target,
            top_pages=int(cfg.get("top_pages_per_target", 6)),
            context_window=int(cfg.get("context_window_pages", 1)),
        )
        if not selected_pages:
            attempts.append({"target_id": target.target_id, "status": "no_pages"})
            continue
        if target.target_type == "error_code" and target.code:
            code_lower = target.code.lower()
            if not any(code_lower in str(page.get("text", "")).lower() for page in selected_pages):
                logger.info(
                    "[resolution_completion] Skipping error code %s — literal code '%s' not found in scoped pages",
                    target.target_id,
                    target.code,
                )
                attempts.append({
                    "target_type": target.target_type,
                    "target_id": target.target_id,
                    "status": "code_not_in_scope",
                })
                continue
        system_prompt, user_prefix = _target_prompt(target, updated)
        user_text = user_prefix + _format_pages(selected_pages)
        try:
            enforce_llm_limits(
                phase="Resolution completion",
                cfg={
                    "timeout_seconds": int(cfg.get("timeout_seconds", 90)),
                    "max_input_chars": int(cfg.get("max_input_chars", 50000)),
                    "estimated_max_input_tokens": int(cfg.get("estimated_max_input_tokens", 12500)),
                    "max_output_tokens": int(cfg.get("max_output_tokens", 2500)),
                },
                system_text=system_prompt,
                user_text=user_text,
            )
        except RuntimeError as exc:
            # A single oversized target must not abort the whole draft run.
            logger.warning(
                "[resolution_completion] Skipping target %s — %s",
                target.target_id,
                exc,
            )
            attempts.append({
                "target_type": target.target_type,
                "target_id": target.target_id,
                "status": "input_too_large",
            })
            continue
        try:
            resolved_model = model_name or settings.MODEL_NAME
            response = client.chat.completions.create(
                model=resolved_model,
                **chat_temperature_kwargs(resolved_model, 0.0),
                max_completion_tokens=int(cfg.get("max_output_tokens", 2500)),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "timeout" in msg:
                raise RuntimeError(llm_timeout_message("Resolution completion", int(cfg.get("timeout_seconds", 90)))) from exc
            raise RuntimeError(f"Resolution completion failed before completion: {exc}") from exc

        usage_entries.append(usage_from_response(response, "resolution_completion"))
        raw = response.choices[0].message.content or "{}"
        try:
            payload = parse_json(raw)
        except Exception:
            logger.warning("[resolution_completion] Failed to parse response for %s", target.target_id)
            attempts.append({"target_id": target.target_id, "status": "parse_failed"})
            continue
        updated, changed = _apply_completion_payload(updated, target, payload)
        status = "completed" if changed else str(payload.get("status") or "not_found")
        if changed:
            completed += 1
        attempts.append({
            "target_type": target.target_type,
            "target_id": target.target_id,
            "status": status,
            "pages": [page["page_number"] for page in selected_pages],
        })

    return updated, usage_entries, {
        "attempted": len(attempts),
        "completed": completed,
        "target_count": len(targets),
        "attempts": attempts,
    }
