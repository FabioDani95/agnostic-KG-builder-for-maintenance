"""Coverage completion — second harvest of diagnostic branches the draft missed.

Real-model branch coverage is nondeterministic: on the same manual and the
same code, one run captures a flowchart branch and the next run drops it
(observed as a ±0.1 recall oscillation on the golden gates). The draft pass
has no mechanism to notice what it missed — it never sees its own output
against the text.

This pass closes that loop deterministically-in-structure: after the draft
(and resolution completion), one targeted LLM call receives the kept pages
plus a compact summary of the chains ALREADY extracted, and returns ONLY the
diagnostic chains that are stated in the text but absent from the summary.

Guardrails, mirroring resolution_completion:
- strictly additive: the pass can add nodes/relations, never remove or edit;
- every returned chain must carry a verbatim evidence quote that is verified
  against the kept pages before anything is applied — no quote, no chain;
- existing nodes are reused by id or by semantic name key, so re-emissions of
  covered content dedupe to no-ops instead of creating duplicates;
- the number of applied chains is capped by config.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from backend.app_config import get_coverage_completion_config
from backend.config import settings
from backend.models import OntologyEvidence, OntologyInstance, OntologyRelationInstance
from backend.services.llm_gateway import chat_temperature_kwargs
from backend.services.llm_guardrails import enforce_llm_limits, llm_timeout_message
from backend.services.ontology_semantics import build_semantic_key
from backend.services.resolution_completion_service import (
    _find_supporting_page,
    _format_pages,
    _get_client,
    _node_id,
    _parse_pages,
    _relation_exists,
    _unique_id,
)
from backend.services.run_metrics import usage_from_response

logger = logging.getLogger(__name__)


def build_chain_summary(ontology: OntologyInstance) -> list[dict[str, Any]]:
    """Compact view of the chains already extracted, one entry per symptom."""
    fm_names = {
        _node_id("FailureMode", node): str(node.get("name", "") or "")
        for node in ontology.nodes.get("FailureMode", []) or []
        if isinstance(node, dict)
    }
    sym_names = {
        _node_id("Symptom", node): str(node.get("name", "") or "")
        for node in ontology.nodes.get("Symptom", []) or []
        if isinstance(node, dict)
    }
    by_symptom: dict[str, list[str]] = {}
    for relation in ontology.relations or []:
        if relation.name == "MAY_INDICATE" and relation.from_id in sym_names:
            by_symptom.setdefault(relation.from_id, []).append(
                fm_names.get(relation.to_id, relation.to_id)
            )
    summary = [
        {"symptom": sym_names[sym_id], "failure_modes": sorted(set(names))}
        for sym_id, names in by_symptom.items()
    ]
    uncovered = [name for sym_id, name in sym_names.items() if sym_id not in by_symptom]
    if uncovered:
        summary.append({"symptom_without_failure_modes": sorted(set(uncovered))})
    return summary


_SYSTEM_PROMPT = """You complete the branch coverage of a troubleshooting ontology extraction.

You receive manual pages and a summary of the diagnostic chains ALREADY extracted
(symptom -> failure modes). Identify diagnostic chains that are explicitly stated in the
pages but MISSING from the summary: alarm-table rows, flowchart branches, and
"if <finding> ... <remedy>" statements whose cause or remedy is not yet covered.

Return valid JSON only:
{
  "missing_chains": [
    {
      "symptom": {"symptom_id": "sym_descriptive_id", "name": "...", "description": "...", "severity": "Low|Medium|High|Critical"},
      "failure_mode": {"failure_mode_id": "fm_descriptive_id", "name": "technical cause", "description": "...", "material_context": "component_id_or_asset_level"},
      "corrective_action": {"action_id": "ca_descriptive_id", "name": "...", "description": "...", "instruction_text": "...", "source_page": 12},
      "evidence": {"source_page": 12, "source_reference": "PAGE 12", "quote": "short verbatim text stating this chain"}
    }
  ]
}

Rules:
- Report ONLY chains absent from the summary. Do not re-emit covered chains.
- Ids: reuse the node's EXACT existing id when the symptom/failure mode/action already
  exists; otherwise invent a new descriptive snake_case id with the type prefix
  (sym_/fm_/ca_). Never copy the placeholder ids from the example shape.
- Reuse the exact symptom name from the summary when the missing branch belongs to an
  already-extracted symptom.
- The failure mode must be a technical cause: a component or subsystem (physical OR
  software/control) in a stative condition — physical (worn, loose, seized, ...) or
  configuration (not mapped, misconfigured, out of calibration, ...). Never a test,
  verification, or inspection result, and never operator error without a system state.
- The corrective action must be restorative, not inspection-only.
- The evidence quote must be a short verbatim excerpt (10-20 words) from the SAME text
  unit (table row, flowchart branch, sentence) that states the chain, with the integer
  page number from the "--- PAGE N ---" markers.
- If the summary already covers everything the text states, return {"missing_chains": []}.
- Never invent content that is not in the pages. JSON only, no commentary.
"""


# Rough per-page diagnostic score used only to stay inside the input budget on
# very large scoped selections: pages that read like troubleshooting content
# (tables, alarm rows, cause/remedy language) are kept first.
_DIAGNOSTIC_PAGE_TERMS: tuple[tuple[str, int], ...] = (
    ("troubleshoot", 6), ("symptom", 4), ("remedy", 4), ("corrective", 4),
    ("cause", 3), ("alarm", 3), ("error", 3), ("fault", 3), ("failure", 3),
    ("replace", 2), ("repair", 2), ("check", 1), ("solution", 2),
    ("[structured tables detected", 5),
)


def _diagnostic_page_score(page_text: str) -> int:
    haystack = str(page_text or "").lower()
    return sum(weight * haystack.count(term) for term, weight in _DIAGNOSTIC_PAGE_TERMS)


def select_pages_within_budget(
    pages: list[dict[str, Any]],
    max_chars: int,
) -> tuple[list[dict[str, Any]], list[int]]:
    """Keep the most diagnostic pages within a character budget.

    Returns (kept_pages_in_document_order, dropped_page_numbers). When the full
    selection already fits, everything is kept — the ranking only kicks in on
    manuals whose scoped text exceeds the coverage-completion input budget,
    which previously aborted the whole pass.
    """
    total = sum(len(str(page.get("text", "") or "")) + 32 for page in pages)
    if total <= max_chars:
        return pages, []

    ranked = sorted(
        pages,
        key=lambda page: (
            -_diagnostic_page_score(str(page.get("text", "") or "")),
            int(page.get("page_number") or 0),
        ),
    )
    kept_numbers: set[int] = set()
    used = 0
    for page in ranked:
        page_chars = len(str(page.get("text", "") or "")) + 32
        if used + page_chars > max_chars:
            continue
        kept_numbers.add(int(page.get("page_number") or 0))
        used += page_chars

    kept = [page for page in pages if int(page.get("page_number") or 0) in kept_numbers]
    dropped = [
        int(page.get("page_number") or 0)
        for page in pages
        if int(page.get("page_number") or 0) not in kept_numbers
    ]
    return kept, dropped


def _semantic_index(nodes: list[Any], node_type: str) -> dict[str, str]:
    index: dict[str, str] = {}
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        node_id = _node_id(node_type, node)
        key = build_semantic_key(str(node.get("name", "") or ""))
        if node_id and key and key not in index:
            index[key] = node_id
    return index


# Prompt-placeholder ids the model sometimes copies verbatim instead of
# choosing a real id. Never honored: treated as "no id proposed".
_PLACEHOLDER_IDS = {"existing_or_new_id", "existing_or_new", "new_id", "node_id"}


def _resolve_or_create(
    raw: dict[str, Any],
    *,
    node_type: str,
    id_field: str,
    prefix: str,
    nodes: dict[str, Any],
    used_ids: set[str],
    semantic: dict[str, str],
    builder: Callable[[str, dict[str, Any]], dict[str, Any]],
) -> tuple[str, bool]:
    """Return (node_id, created). Reuse by id, then by semantic name key.

    Id reuse is TYPE-AWARE: a candidate id is honored as "existing" only when a
    node of THIS type carries it. A global check let a placeholder id copied
    into two fields resolve the second occurrence to a node of the wrong type,
    producing a relation to a target that does not exist (observed as a
    blocking relation_missing_target on a real run).
    """
    type_ids = {
        _node_id(node_type, item)
        for item in nodes.get(node_type, []) or []
        if isinstance(item, dict)
    }
    candidate_id = str(raw.get(id_field) or "").strip()
    if candidate_id.lower() in _PLACEHOLDER_IDS:
        candidate_id = ""
    if candidate_id and candidate_id in type_ids:
        return candidate_id, False
    name = str(raw.get("name") or "").strip()
    key = build_semantic_key(name)
    if key and key in semantic:
        return semantic[key], False
    if candidate_id and candidate_id not in used_ids:
        # The model proposed a fresh, unused id: keep it verbatim.
        used_ids.add(candidate_id)
        node_id = candidate_id
    else:
        node_id = _unique_id(name, used_ids, prefix=prefix, fallback=f"coverage_{prefix}")
    nodes.setdefault(node_type, []).append(builder(node_id, raw))
    if key:
        semantic[key] = node_id
    return node_id, True


def apply_missing_chains(
    ontology: OntologyInstance,
    payload: dict[str, Any],
    pages: list[dict[str, Any]],
    *,
    max_chains: int,
) -> tuple[OntologyInstance, dict[str, Any]]:
    """Apply the additive chain payload; return (ontology, report). Pure."""
    raw_chains = payload.get("missing_chains")
    report: dict[str, Any] = {"returned": 0, "applied": 0, "dropped_no_quote": 0, "dropped_duplicate": 0}
    if not isinstance(raw_chains, list) or not raw_chains:
        return ontology, report
    report["returned"] = len(raw_chains)

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
        if isinstance(item, dict) and _node_id(node_type, item)
    }
    sym_index = _semantic_index(nodes.get("Symptom", []), "Symptom")
    fm_index = _semantic_index(nodes.get("FailureMode", []), "FailureMode")
    ca_index = _semantic_index(nodes.get("CorrectiveAction", []), "CorrectiveAction")

    applied = 0
    for raw_chain in raw_chains:
        if applied >= max(0, int(max_chains)):
            break
        if not isinstance(raw_chain, dict):
            continue
        raw_symptom = raw_chain.get("symptom") if isinstance(raw_chain.get("symptom"), dict) else {}
        raw_failure = raw_chain.get("failure_mode") if isinstance(raw_chain.get("failure_mode"), dict) else {}
        raw_action = raw_chain.get("corrective_action") if isinstance(raw_chain.get("corrective_action"), dict) else {}
        raw_evidence = raw_chain.get("evidence") if isinstance(raw_chain.get("evidence"), dict) else {}
        if not (str(raw_symptom.get("name") or "").strip() and str(raw_failure.get("name") or "").strip()):
            continue

        quote = str(raw_evidence.get("quote") or "").strip()
        try:
            source_page = int(raw_evidence.get("source_page") or 0)
        except (TypeError, ValueError):
            source_page = 0
        supported_page = _find_supporting_page(quote, source_page, pages)
        if supported_page <= 0:
            report["dropped_no_quote"] += 1
            logger.info(
                "[coverage_completion] Dropping chain '%s -> %s' — evidence quote not found in pages",
                raw_symptom.get("name"),
                raw_failure.get("name"),
            )
            continue
        if supported_page != source_page:
            # Quote found on a different kept page: correct the citation so the
            # downstream grounding pass verifies against the right page instead
            # of flagging content this pass just accepted.
            source_page = supported_page

        evidence = [OntologyEvidence(
            source_page=source_page,
            source_reference=f"PAGE {source_page}",
            quote=quote,
        )]

        symptom_id, _ = _resolve_or_create(
            raw_symptom, node_type="Symptom", id_field="symptom_id", prefix="sym",
            nodes=nodes, used_ids=used_ids, semantic=sym_index,
            builder=lambda node_id, raw: {
                "symptom_id": node_id,
                "name": str(raw.get("name") or "").strip(),
                "description": str(raw.get("description") or raw.get("name") or "").strip(),
                "severity": str(raw.get("severity") or "Medium").strip().capitalize() or "Medium",
            },
        )
        failure_id, _ = _resolve_or_create(
            raw_failure, node_type="FailureMode", id_field="failure_mode_id", prefix="fm",
            nodes=nodes, used_ids=used_ids, semantic=fm_index,
            builder=lambda node_id, raw: {
                "failure_mode_id": node_id,
                "name": str(raw.get("name") or "").strip(),
                "description": str(raw.get("description") or raw.get("name") or "").strip(),
                "material_context": str(raw.get("material_context") or "asset_level").strip(),
            },
        )

        may_indicate = OntologyRelationInstance(
            name="MAY_INDICATE", from_type="Symptom", from_id=symptom_id,
            to_type="FailureMode", to_id=failure_id, evidence=evidence,
        )
        chain_changed = False
        if not _relation_exists(relations, may_indicate):
            relations.append(may_indicate)
            chain_changed = True

        if str(raw_action.get("name") or "").strip() and str(raw_action.get("instruction_text") or raw_action.get("name") or "").strip():
            try:
                action_page = int(raw_action.get("source_page") or 0) or source_page
            except (TypeError, ValueError):
                action_page = source_page
            action_id, _ = _resolve_or_create(
                raw_action, node_type="CorrectiveAction", id_field="action_id", prefix="ca",
                nodes=nodes, used_ids=used_ids, semantic=ca_index,
                builder=lambda node_id, raw: {
                    "action_id": node_id,
                    "name": str(raw.get("name") or "").strip(),
                    "description": str(raw.get("description") or raw.get("name") or "").strip(),
                    "instruction_text": str(raw.get("instruction_text") or raw.get("name") or "").strip(),
                    "source_type": ontology.source_type,
                    "source_title": ontology.source_title,
                    "source_page": action_page,
                    "source_reference": f"PAGE {action_page}" if action_page else "",
                },
            )
            resolved_by = OntologyRelationInstance(
                name="RESOLVED_BY", from_type="FailureMode", from_id=failure_id,
                to_type="CorrectiveAction", to_id=action_id, evidence=evidence,
            )
            if not _relation_exists(relations, resolved_by):
                relations.append(resolved_by)
                chain_changed = True

        if chain_changed:
            applied += 1
        else:
            report["dropped_duplicate"] += 1

    report["applied"] = applied
    if applied:
        data["relations"] = [relation.model_dump() for relation in relations]
        return OntologyInstance.model_validate(data), report
    return ontology, report


def complete_coverage_gaps(
    *,
    ontology: OntologyInstance,
    text_with_pages: str,
    model_name: str,
    parse_json: Callable[[str], dict[str, Any]],
) -> tuple[OntologyInstance, list[dict[str, Any]], dict[str, Any]]:
    cfg = get_coverage_completion_config()
    if not cfg.get("enabled", True):
        return ontology, [], {"returned": 0, "applied": 0, "skipped": "disabled"}

    pages = _parse_pages(text_with_pages)
    if not pages:
        return ontology, [], {"returned": 0, "applied": 0, "skipped": "no_pages"}

    summary = build_chain_summary(ontology)
    summary_json = json.dumps(summary, ensure_ascii=False, indent=2)

    # Large manuals used to abort this pass on the input guardrail — exactly the
    # runs where a second harvest matters most. Rank pages by diagnostic signal
    # and keep the best ones inside the remaining budget instead.
    max_input_chars = int(cfg.get("max_input_chars", 120000))
    page_budget = max(10000, max_input_chars - len(_SYSTEM_PROMPT) - len(summary_json) - 2000)
    budget_pages, dropped_page_numbers = select_pages_within_budget(pages, page_budget)
    if dropped_page_numbers:
        logger.info(
            "[coverage_completion] Input over budget — keeping %d/%d page(s) by diagnostic score (dropped: %s)",
            len(budget_pages),
            len(pages),
            dropped_page_numbers[:20],
        )
    if not budget_pages:
        return ontology, [], {"returned": 0, "applied": 0, "skipped": "input_too_large"}
    pages = budget_pages

    user_text = (
        "CHAINS ALREADY EXTRACTED (symptom -> failure modes)\n"
        f"{summary_json}\n\n"
        "MANUAL PAGES\n"
        f"{_format_pages(pages)}"
    )
    enforce_llm_limits(
        phase="Coverage completion",
        cfg={
            "timeout_seconds": int(cfg.get("timeout_seconds", 120)),
            "max_input_chars": int(cfg.get("max_input_chars", 120000)),
            "estimated_max_input_tokens": int(cfg.get("estimated_max_input_tokens", 30000)),
            "max_output_tokens": int(cfg.get("max_output_tokens", 6000)),
        },
        system_text=_SYSTEM_PROMPT,
        user_text=user_text,
    )
    client = _get_client(int(cfg.get("timeout_seconds", 120)))
    try:
        resolved_model = model_name or settings.MODEL_NAME
        response = client.chat.completions.create(
            model=resolved_model,
            **chat_temperature_kwargs(resolved_model, 0.0),
            max_completion_tokens=int(cfg.get("max_output_tokens", 6000)),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "timeout" in msg:
            raise RuntimeError(llm_timeout_message("Coverage completion", int(cfg.get("timeout_seconds", 120)))) from exc
        raise RuntimeError(f"Coverage completion failed before completion: {exc}") from exc

    usage_entries = [usage_from_response(response, "coverage_completion")]
    raw = response.choices[0].message.content or "{}"
    try:
        payload = parse_json(raw)
    except Exception:
        logger.warning("[coverage_completion] Failed to parse response; keeping ontology unchanged")
        return ontology, usage_entries, {"returned": 0, "applied": 0, "error": "parse_failed"}

    updated, report = apply_missing_chains(
        ontology,
        payload,
        pages,
        max_chains=int(cfg.get("max_chains", 12)),
    )
    if dropped_page_numbers:
        report["pages_dropped_for_budget"] = len(dropped_page_numbers)
    if report.get("applied"):
        logger.info(
            "[coverage_completion] Applied %d missing chain(s) (%d returned, %d dropped without quote)",
            report["applied"],
            report["returned"],
            report["dropped_no_quote"],
        )
    return updated, usage_entries, report
