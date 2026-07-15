#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

GOLDEN_DIR = REPO_ROOT / "tests" / "golden"


def _now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_expected(fixture_id: str) -> dict[str, Any]:
    return json.loads((GOLDEN_DIR / "expected" / f"{fixture_id}.json").read_text(encoding="utf-8"))


def _fixture_ids(selected: str | None) -> list[str]:
    if selected:
        return [item.strip() for item in selected.split(",") if item.strip()]
    return sorted(path.stem for path in (GOLDEN_DIR / "expected").glob("*.json"))


def _normalize(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(value: Any) -> set[str]:
    return {token for token in _normalize(value).split() if token}


def _soft_match(expected: str, actual: str) -> bool:
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return True
    expected_norm = _normalize(expected)
    actual_norm = _normalize(actual)
    if not actual_norm:
        # An empty actual can never satisfy a non-empty expectation. (The old
        # substring check made "" match everything, which silently disabled
        # the error-code comparison.)
        return False
    if expected_norm in actual_norm or actual_norm in expected_norm:
        return True
    overlap = len(expected_tokens & _tokens(actual))
    return overlap / max(1, len(expected_tokens)) >= 0.6


def _code_match(expected: str, actual: str) -> bool:
    """Error codes match on exact tokens, not substrings ("E1" must not match "E17")."""
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return True
    return expected_tokens.issubset(_tokens(actual))


def _strict_match(expected: str, actual: str) -> bool:
    """Normalized substring containment only — no token-overlap fallback.

    Used for forbidden_chains: they are a precision tool, and overlap scoring
    on stopword-heavy phrases makes "machine does not spin" match "the machine
    does not fill with water", flagging valid chains as contaminated.
    """
    expected_norm = _normalize(expected)
    if not expected_norm:
        return True
    actual_norm = _normalize(actual)
    return bool(actual_norm) and expected_norm in actual_norm


def _part_text(node: dict[str, Any], keys: tuple[str, ...]) -> str:
    return " ".join(str(node.get(key, "") or "") for key in keys).strip()


def _triplet_chains(triplet: Any, triplet_index: int) -> list[dict[str, Any]]:
    """Explode one projected triplet into atomic Symptom→FM→CA chains.

    The projection aggregates every failure mode / action under one symptom,
    but the FM→CA pairing is preserved via linked_failure_mode_id. Matching on
    atomic chains (instead of one concatenated blob per symptom) makes a wrong
    pairing a miss instead of a silent pass. material_context is excluded: it
    is an internal component id, not diagnostic text.
    """
    payload = triplet.model_dump() if hasattr(triplet, "model_dump") else dict(triplet or {})
    symptom = payload.get("symptom") or {}
    symptom_text = _part_text(symptom, ("name", "description"))
    symptom_id = str(symptom.get("symptom_id", "") or "")
    failures = payload.get("failure_modes") or []
    actions = payload.get("corrective_actions") or []

    actions_by_fm: dict[str, list[dict[str, Any]]] = {}
    unlinked_actions: list[dict[str, Any]] = []
    fm_ids = {str(fm.get("failure_mode_id", "") or "") for fm in failures}
    for action in actions:
        linked = str(action.get("linked_failure_mode_id", "") or "")
        if linked in fm_ids and linked:
            actions_by_fm.setdefault(linked, []).append(action)
        else:
            unlinked_actions.append(action)

    chains: list[dict[str, Any]] = []
    for failure in failures:
        fm_id = str(failure.get("failure_mode_id", "") or "")
        fm_codes = [str(code) for code in (failure.get("error_codes") or []) if str(code)]
        # Legacy LLM-extracted triplets may not carry reliable FM→CA links;
        # fall back to the unpaired actions so they stay matchable.
        linked_actions = actions_by_fm.get(fm_id) or unlinked_actions
        base = {
            "triplet_index": triplet_index,
            "symptom_id": symptom_id,
            "symptom": symptom_text,
            "failure_mode": _part_text(failure, ("name", "description")),
            "failure_mode_name": str(failure.get("name", "") or ""),
            "failure_mode_id": fm_id,
            "error_code": " ".join(fm_codes),
            "source": "projection",
        }
        if linked_actions:
            for action in linked_actions:
                chains.append({
                    **base,
                    "corrective_action": _part_text(action, ("name", "description", "instruction_text")),
                    "corrective_action_name": str(action.get("name", "") or ""),
                    "action_id": str(action.get("action_id", "") or ""),
                })
        else:
            chains.append({**base, "corrective_action": "", "corrective_action_name": "", "action_id": ""})
    return chains


def _graph_error_code_chains(ontology: Any) -> list[dict[str, Any]]:
    """Alarm-code chains read directly from the graph: ErrorCode→INDICATES→FM→RESOLVED_BY→CA.

    Error-code-rooted expectations are matched against the graph itself, so the
    golden gate does not depend on how the projection groups symptoms.
    """
    payload = ontology.model_dump() if hasattr(ontology, "model_dump") else (ontology or {})
    nodes = payload.get("nodes") or {}

    def _by_id(label: str, id_field: str) -> dict[str, dict[str, Any]]:
        return {
            str(node.get(id_field, "") or "").strip(): node
            for node in nodes.get(label) or []
            if isinstance(node, dict) and str(node.get(id_field, "") or "").strip()
        }

    error_codes = _by_id("ErrorCode", "error_code_id")
    failure_modes = _by_id("FailureMode", "failure_mode_id")
    actions = _by_id("CorrectiveAction", "action_id")

    indicates: list[tuple[str, str]] = []
    resolved_by: dict[str, list[str]] = {}
    for rel in payload.get("relations") or []:
        if not isinstance(rel, dict):
            continue
        name = str(rel.get("name") or rel.get("type") or "").strip()
        from_id = str(rel.get("from_id") or "").strip()
        to_id = str(rel.get("to_id") or "").strip()
        if name == "INDICATES" and from_id in error_codes and to_id in failure_modes:
            indicates.append((from_id, to_id))
        elif name == "RESOLVED_BY" and from_id in failure_modes and to_id in actions:
            resolved_by.setdefault(from_id, []).append(to_id)

    chains: list[dict[str, Any]] = []
    for ec_id, fm_id in indicates:
        ec_node = error_codes[ec_id]
        code = str(ec_node.get("code") or ec_node.get("name") or "").strip()
        failure = failure_modes[fm_id]
        base = {
            "symptom": "",
            "failure_mode": _part_text(failure, ("name", "description")),
            "failure_mode_name": str(failure.get("name", "") or ""),
            "error_code": code,
            "source": "graph_error_code",
        }
        action_ids = resolved_by.get(fm_id) or []
        if action_ids:
            for action_id in action_ids:
                action = actions[action_id]
                chains.append({
                    **base,
                    "corrective_action": _part_text(action, ("name", "description", "instruction_text")),
                    "corrective_action_name": str(action.get("name", "") or ""),
                })
        else:
            chains.append({**base, "corrective_action": "", "corrective_action_name": ""})
    return chains


def _expected_matches_chain(expected_item: dict[str, Any], chain: dict[str, Any]) -> bool:
    checks = [
        _soft_match(expected_item.get("symptom", ""), chain.get("symptom", "")),
        _soft_match(expected_item.get("failure_mode", ""), chain.get("failure_mode", "")),
        _soft_match(expected_item.get("corrective_action", ""), chain.get("corrective_action", "")),
    ]
    if expected_item.get("error_code"):
        checks.append(_code_match(expected_item.get("error_code", ""), chain.get("error_code", "")))
    return all(checks)


def _forbidden_matches_chain(rule: dict[str, Any], chain: dict[str, Any]) -> bool:
    checks = [
        _strict_match(rule.get("symptom", ""), chain.get("symptom", "")),
        _strict_match(rule.get("failure_mode", ""), chain.get("failure_mode", "")),
        _strict_match(rule.get("corrective_action", ""), chain.get("corrective_action", "")),
    ]
    if rule.get("error_code"):
        checks.append(_code_match(rule.get("error_code", ""), chain.get("error_code", "")))
    return all(checks)


def _relation_quotes_index(ontology: Any) -> dict[tuple[str, str, str], list[str]]:
    """(relation type, source id, target id) → attached evidence quotes."""
    payload = ontology.model_dump() if hasattr(ontology, "model_dump") else (ontology or {})
    index: dict[tuple[str, str, str], list[str]] = {}
    for rel in payload.get("relations") or []:
        if not isinstance(rel, dict):
            continue
        quotes = [
            str(ev.get("quote", "") or "").strip()
            for ev in rel.get("evidence") or []
            if isinstance(ev, dict) and str(ev.get("quote", "") or "").strip()
        ]
        if not quotes:
            continue
        key = (
            str(rel.get("name") or rel.get("type") or "").strip(),
            str(rel.get("from_id") or "").strip(),
            str(rel.get("to_id") or "").strip(),
        )
        if all(key):
            index.setdefault(key, []).extend(quotes)
    return index


def _chain_grounded(
    chain: dict[str, Any],
    page_texts: list[str],
    quotes_index: dict[tuple[str, str, str], list[str]] | None = None,
    *,
    require_relation_evidence: bool = False,
) -> bool:
    """Verify the specific Symptom→FM and FM→CA links, not isolated node names."""
    from backend.services.llm_service import _fragment_supported_by_page

    quotes_index = quotes_index or {}

    def _quoted_relation_supported(name: str, from_id: str, to_id: str) -> bool:
        return any(
            _fragment_supported_by_page(quote, text)
            for quote in quotes_index.get((name, from_id, to_id), [])
            for text in page_texts
        )

    symptom_id = str(chain.get("symptom_id") or "")
    failure_mode_id = str(chain.get("failure_mode_id") or "")
    action_id = str(chain.get("action_id") or "")
    if require_relation_evidence:
        may_indicate_ok = _quoted_relation_supported(
            "MAY_INDICATE", symptom_id, failure_mode_id
        )
        resolved_by_ok = True if not action_id else _quoted_relation_supported(
            "RESOLVED_BY", failure_mode_id, action_id
        )
        return may_indicate_ok and resolved_by_ok

    # Legacy/no-ontology fallback: both endpoints of each causal link must
    # occur in the same line or sentence, not merely somewhere in the scope.
    units = [
        unit.strip()
        for page_text in page_texts
        for unit in re.split(r"(?:\n+|(?<=[.!?;])\s+)", page_text)
        if unit.strip()
    ]

    def _same_unit(left: str, right: str) -> bool:
        if not left or not right:
            return False
        return any(
            _fragment_supported_by_page(left, unit)
            and _fragment_supported_by_page(right, unit)
            for unit in units
        )

    symptom_name = str(chain.get("symptom") or "")
    failure_mode_name = str(chain.get("failure_mode_name") or chain.get("failure_mode") or "")
    action_name = str(chain.get("corrective_action_name") or chain.get("corrective_action") or "")
    return _same_unit(symptom_name, failure_mode_name) and (
        True if not action_name else _same_unit(failure_mode_name, action_name)
    )


def _match_triplets(
    expected: list[dict[str, Any]],
    actual_triplets: list[Any],
    *,
    ontology: Any = None,
    page_texts: list[str] | None = None,
    forbidden: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    projection_chains: list[dict[str, Any]] = []
    for index, triplet in enumerate(actual_triplets):
        projection_chains.extend(_triplet_chains(triplet, index))
    graph_chains = _graph_error_code_chains(ontology) if ontology is not None else []

    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    matched_chain_indexes: set[int] = set()
    matched_triplet_indexes: set[int] = set()
    matched_graph_chain_indexes: set[int] = set()
    for expected_item in expected:
        found: dict[str, Any] | None = None
        for index, chain in enumerate(projection_chains):
            if index in matched_chain_indexes:
                continue
            if _expected_matches_chain(expected_item, chain):
                found = {"expected": expected_item, "chain_index": index, "source": "projection",
                         "actual_index": chain["triplet_index"]}
                matched_chain_indexes.add(index)
                matched_triplet_indexes.add(chain["triplet_index"])
                break
        if found is None:
            for index, chain in enumerate(graph_chains):
                if index in matched_graph_chain_indexes:
                    continue
                if _expected_matches_chain(expected_item, chain):
                    found = {"expected": expected_item, "chain_index": index, "source": "graph_error_code"}
                    matched_graph_chain_indexes.add(index)
                    break
        if found is None:
            unmatched.append(expected_item)
        else:
            matches.append(found)

    # Three-way classification: matched / extra-but-grounded / unsupported.
    # Extra grounded chains are valid manual coverage outside the golden's
    # sample; only unsupported chains count as false positives.
    page_texts = page_texts or []
    quotes_index = _relation_quotes_index(ontology) if ontology is not None else {}
    extra_grounded = 0
    unsupported = 0
    annotated_chains: list[dict[str, Any]] = []
    for index, chain in enumerate(projection_chains):
        if index in matched_chain_indexes:
            status = "matched"
        elif _chain_grounded(
            chain,
            page_texts,
            quotes_index,
            require_relation_evidence=ontology is not None,
        ):
            status = "extra_grounded"
            extra_grounded += 1
        else:
            status = "unsupported"
            unsupported += 1
        annotated_chains.append({**chain, "status": status})

    violations: list[dict[str, Any]] = []
    for rule in forbidden or []:
        for index, chain in enumerate(projection_chains):
            if _forbidden_matches_chain(rule, chain):
                violations.append({"rule": rule, "chain_index": index,
                                   "symptom": chain.get("symptom", ""),
                                   "failure_mode": chain.get("failure_mode", "")})

    total_chains = len(projection_chains)
    matched = len(matches)
    # Legacy triplet-level precision: distinct projected triplets that matched.
    matched_actual = len(matched_triplet_indexes)
    return {
        "matched": matched,
        "expected": len(expected),
        "actual": len(actual_triplets),
        "recall": round(matched / max(1, len(expected)), 4),
        "approx_precision": round(matched_actual / max(1, len(actual_triplets)), 4),
        "chains": {
            "total": total_chains,
            "matched": len(matched_chain_indexes),
            "extra_grounded": extra_grounded,
            "unsupported": unsupported,
            "precision_strict": round(len(matched_chain_indexes) / max(1, total_chains), 4),
            "grounded_precision": round((len(matched_chain_indexes) + extra_grounded) / max(1, total_chains), 4),
            "unsupported_rate": round(unsupported / max(1, total_chains), 4),
        },
        "actual_chains": annotated_chains,
        "graph_error_code_chains": graph_chains,
        "matches": matches,
        "unmatched_expected": unmatched,
        "forbidden": {
            "rules": len(forbidden or []),
            "violations": violations,
            "passed": not violations,
        },
    }


def _ontology_counts(ontology: Any) -> dict[str, int]:
    payload = ontology.model_dump() if hasattr(ontology, "model_dump") else (ontology or {})
    nodes = payload.get("nodes") or {}
    return {node_type: len(items or []) for node_type, items in nodes.items()}


def _dangling_relation_count(ontology: Any) -> int:
    payload = ontology.model_dump() if hasattr(ontology, "model_dump") else (ontology or {})
    nodes = payload.get("nodes") or {}
    id_fields = {
        "Asset": "asset_id",
        "Component": "component_id",
        "Symptom": "symptom_id",
        "FailureMode": "failure_mode_id",
        "CorrectiveAction": "action_id",
        "ErrorCode": "error_code_id",
    }
    node_ids = {
        str(item.get(id_fields[node_type]) or "").strip()
        for node_type, items in nodes.items()
        if node_type in id_fields
        for item in (items or [])
        if isinstance(item, dict) and str(item.get(id_fields[node_type]) or "").strip()
    }
    return sum(
        1
        for rel in payload.get("relations") or []
        if isinstance(rel, dict)
        and (
            str(rel.get("from_id") or "").strip() not in node_ids
            or str(rel.get("to_id") or "").strip() not in node_ids
        )
    )


def _relation_names(ontology: Any, triplets: list[Any]) -> set[str]:
    """Relation names actually present in the run output.

    Derived from the ontology's own relations plus the structure of the
    extracted triplets (a triplet with failure modes / corrective actions is
    what the export projects into HAS_FAILURE_MODE / HAS_CORRECTIVE_ACTION
    edges). Nothing is inferred from the expected file, so a regression that
    drops a relation type is visible here.
    """
    payload = ontology.model_dump() if hasattr(ontology, "model_dump") else (ontology or {})
    names = {str(item.get("name") or item.get("type") or "") for item in payload.get("relations", []) if isinstance(item, dict)}
    for triplet in triplets:
        item = triplet.model_dump() if hasattr(triplet, "model_dump") else dict(triplet or {})
        if item.get("failure_modes"):
            names.add("HAS_FAILURE_MODE")
        if item.get("corrective_actions"):
            names.add("HAS_CORRECTIVE_ACTION")
    names.discard("")
    return names


def _export_checks(expected: dict[str, Any], ontology: Any, triplets: list[Any]) -> dict[str, Any]:
    checks = expected.get("expected_export_checks") or {}
    counts = _ontology_counts(ontology)
    relation_names = _relation_names(ontology, triplets)
    results: dict[str, Any] = {}
    mapping = {
        "min_symptoms": "Symptom",
        "min_failure_modes": "FailureMode",
        "min_corrective_actions": "CorrectiveAction",
        "min_error_codes": "ErrorCode",
    }
    for check_key, node_type in mapping.items():
        if check_key in checks:
            results[check_key] = {
                "expected": checks[check_key],
                "actual": counts.get(node_type, 0),
                "passed": counts.get(node_type, 0) >= int(checks[check_key]),
            }
    required_relations = list(checks.get("required_relations") or [])
    results["required_relations"] = {
        "expected": required_relations,
        "actual": sorted(relation_names),
        "missing": [name for name in required_relations if name not in relation_names],
    }
    results["passed"] = all(
        value.get("passed", not value.get("missing"))
        for value in results.values()
        if isinstance(value, dict)
    )
    return results


_REVIEW_SEVERITY_KEYS = (
    ("max_blocking", "blocking"),
    ("max_open", "open"),
    ("max_reject", "reject"),
    ("max_review", "review"),
    ("max_advisory", "advisory"),
)


def _quality_gates_result(expected: dict[str, Any], triplet_match: dict[str, Any]) -> dict[str, Any]:
    """Absolute per-fixture quality gates from `expected_quality_gates`.

    Real-model recall oscillates run-to-run (observed ±0.1 on the same code),
    so "never worse than the previous run" false-alarms on pure variance. A
    per-fixture floor (min_recall) states the actual quality bar; when
    present it REPLACES the baseline recall comparison. max_unsupported_rate
    (typically 0.0) turns the no-hallucination result into a hard gate.
    """
    gates = expected.get("expected_quality_gates") or {}
    results: dict[str, Any] = {}
    if "min_recall" in gates:
        actual = float(triplet_match.get("recall", 0))
        results["min_recall"] = {
            "expected": float(gates["min_recall"]),
            "actual": actual,
            "passed": actual >= float(gates["min_recall"]),
        }
    if "max_unsupported_rate" in gates:
        actual = float((triplet_match.get("chains") or {}).get("unsupported_rate", 0))
        results["max_unsupported_rate"] = {
            "expected": float(gates["max_unsupported_rate"]),
            "actual": actual,
            "passed": actual <= float(gates["max_unsupported_rate"]),
        }
    results["passed"] = all(
        value.get("passed", True) for value in results.values() if isinstance(value, dict)
    )
    return results


def _human_review_result(expected: dict[str, Any], ontology_result: Any) -> dict[str, Any]:
    """Compare the review queue against the expectation.

    Two expectation styles are supported:
    - boolean: {"required": true/false} — queue emptiness must match exactly.
    - granular: {"max_blocking": 0, "max_open": 2, ...} — per-severity upper
      bounds. Real manuals legitimately produce advisory/review items (every
      flowchart symptom is multi-cause by design), so "queue must be empty" is
      the wrong bar; "nothing blocking" is the meaningful one.
    Both styles can be combined; all present checks must pass.
    """
    expected_review = expected.get("expected_human_review") or {}
    required_fields = list(getattr(ontology_result, "human_required_fields", []) or [])
    review_queue = list(getattr(ontology_result, "review_queue", []) or [])
    actual_required = bool(required_fields or review_queue)
    severity_counts = _count_by([
        str((item or {}).get("severity", "")) for item in review_queue if isinstance(item, dict)
    ])

    checks: list[bool] = []
    if "required" in expected_review:
        checks.append(bool(expected_review.get("required")) == actual_required)
    for key, severity in _REVIEW_SEVERITY_KEYS:
        if key in expected_review:
            checks.append(severity_counts.get(severity, 0) <= int(expected_review[key]))
    if "max_total" in expected_review:
        checks.append(len(review_queue) <= int(expected_review["max_total"]))

    return {
        "expected_required": bool(expected_review.get("required")),
        "actual_required": actual_required,
        "matched": all(checks) if checks else True,
        "required_fields": len(required_fields),
        "review_queue": len(review_queue),
        "severity_counts": severity_counts,
        "reason": expected_review.get("reason", ""),
    }


async def _run_fixture(
    fixture_id: str,
    *,
    mode: str,
    model_name: str,
    target_language: str,
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    from backend.agents.extraction_agent import run_extraction_agent
    from backend.agents.ontology_draft_agent import run_ontology_draft_agent
    from backend.agents.scoping_agent import run_scoping_agent
    from backend.models import (
        CutPlanApproval,
        CutPlanApprovalSection,
        CutPlanRequest,
        ExtractRequest,
        OntologyDraftRequest,
    )
    from backend.observability.trace import trace_from_state
    from backend.runstore import RunStore
    from backend.services.manual_loader import build_store_from_markdown
    from backend.services.run_metrics import build_metrics_payload
    from backend.services.scoping_workflow import approve_cut_plan_workflow

    expected = _load_expected(fixture_id)
    store = build_store_from_markdown(GOLDEN_DIR / expected["manual"])
    if mode == "mock":
        # Route the mock LLM to this fixture's canned responses
        # (tests/golden/mock_responses/<fixture_id>/<stage>.json).
        os.environ["KG_LLM_FIXTURE"] = fixture_id
    started = time.perf_counter()

    cut_plan = run_scoping_agent(
        store,
        CutPlanRequest(pdf_id=store["pdf_id"], model_name=model_name, page_offset=0),
    )
    approval = CutPlanApproval(
        pdf_id=store["pdf_id"],
        pages_to_keep=cut_plan.pages_to_keep,
        page_offset=cut_plan.page_offset,
        sections=[
            CutPlanApprovalSection(name=section.name, page_range=section.page_range, source=section.source)
            for section in cut_plan.sections
        ],
    )
    approve_cut_plan_workflow(store, approval)

    ontology_result = await run_ontology_draft_agent(
        store,
        OntologyDraftRequest(
            pdf_id=store["pdf_id"],
            source_type=store.get("source_type") or "maintenance manual",
            source_title=store.get("source_title") or store["filename"],
            model_name=model_name,
            pages_to_keep=cut_plan.pages_to_keep,
            target_language=target_language,
        ),
    )

    extraction_result = run_extraction_agent(
        store,
        ExtractRequest(
            pdf_id=store["pdf_id"],
            source_type=store.get("source_type") or "maintenance manual",
            source_title=store.get("source_title") or store["filename"],
            model_name=model_name,
            pages_to_keep=cut_plan.pages_to_keep,
            target_language=target_language,
        ),
    )

    metrics = build_metrics_payload(store)
    run_id = str(store.get("run_id") or "")
    persisted_trace = RunStore().read_trace(run_id) if run_id else []
    trace = persisted_trace or trace_from_state(store.get("graph_state") or {})
    selected_pages = list(cut_plan.pages_to_keep)
    expected_pages = list((expected.get("expected_scoping") or {}).get("must_keep_pages") or [])
    keep_set = set(selected_pages)
    page_texts = [
        str(page.get("text", "") or "")
        for page in store.get("pages", [])
        if not keep_set or page.get("page_number") in keep_set
    ]
    triplet_match = _match_triplets(
        expected.get("expected_triplets") or [],
        extraction_result.triplets,
        ontology=ontology_result.ontology,
        page_texts=page_texts,
        forbidden=list(expected.get("forbidden_chains") or []),
    )
    export_checks = _export_checks(expected, ontology_result.ontology, extraction_result.triplets)
    quality_gates = _quality_gates_result(expected, triplet_match)
    artifacts: dict[str, str] = {}
    if artifacts_dir is not None:
        # Full payloads for offline audit: a real-model run costs real money,
        # so every re-analysis must be possible without re-running the LLM.
        fixture_dir = artifacts_dir / fixture_id
        fixture_dir.mkdir(parents=True, exist_ok=True)
        ontology_payload = (
            ontology_result.ontology.model_dump()
            if hasattr(ontology_result.ontology, "model_dump")
            else ontology_result.ontology
        )
        triplet_payloads = [
            triplet.model_dump() if hasattr(triplet, "model_dump") else triplet
            for triplet in extraction_result.triplets
        ]
        for name, payload in (
            ("ontology.json", ontology_payload),
            ("triplets.json", triplet_payloads),
            ("chains.json", triplet_match.get("actual_chains", [])),
            ("review_queue.json", list(getattr(ontology_result, "review_queue", []) or [])),
        ):
            (fixture_dir / name).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
            )
            artifacts[name.removesuffix(".json")] = str((fixture_dir / name).relative_to(artifacts_dir.parent))
    return {
        "fixture_id": fixture_id,
        "mode": mode,
        "duration_seconds": round(time.perf_counter() - started, 3),
        "scoping": {
            "total_pages": cut_plan.total_pages,
            "selected_pages": selected_pages,
            "must_keep_pages": expected_pages,
            "must_keep_passed": set(expected_pages).issubset(set(selected_pages)),
            "sections": [
                {
                    "name": section.name,
                    "start": section.page_range.start,
                    "end": section.page_range.end,
                    "source": section.source,
                }
                for section in cut_plan.sections
            ],
        },
        "ontology": {
            "status": ontology_result.status,
            "schema_compliant": ontology_result.is_schema_compliant,
            "schema_issues": len(ontology_result.schema_issues),
            "schema_issues_by_severity": _count_by([item.severity for item in ontology_result.schema_issues]),
            "node_counts": _ontology_counts(ontology_result.ontology),
            "relation_count": len(ontology_result.ontology.relations or []),
            "dangling_relations": _dangling_relation_count(ontology_result.ontology),
            "human_review": _human_review_result(expected, ontology_result),
        },
        "triplets": triplet_match,
        "export_checks": export_checks,
        "quality_gates": quality_gates,
        "artifacts": artifacts,
        "metrics": {
            "totals": metrics.get("totals", {}),
            "stages": metrics.get("stages", {}),
        },
        "trace": trace,
    }


def _count_by(items: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item or "")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _write_markdown_report(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# Golden Eval Report {report['run_id']}",
        "",
        f"- mode: {report['mode']}",
        f"- fixtures: {len(report['fixtures'])}",
        f"- duration_seconds: {report['summary']['duration_seconds']}",
        "",
        "## Summary",
        "",
    ]
    for fixture in report["fixtures"]:
        chains = fixture["triplets"].get("chains") or {}
        forbidden = fixture["triplets"].get("forbidden") or {}
        gates = fixture.get("quality_gates") or {}
        gate_line = ", ".join(
            f"{name} {'pass' if gate.get('passed') else 'FAIL'} ({gate.get('actual')}/{gate.get('expected')})"
            for name, gate in gates.items()
            if isinstance(gate, dict)
        ) or "none defined"
        lines.extend([
            f"### {fixture['fixture_id']}",
            "",
            f"- scoping must-keep: {'pass' if fixture['scoping']['must_keep_passed'] else 'fail'}",
            f"- triplet recall: {fixture['triplets']['recall']} ({fixture['triplets']['matched']}/{fixture['triplets']['expected']})",
            f"- approximate precision: {fixture['triplets']['approx_precision']}",
            f"- chains: {chains.get('matched', 0)} matched / {chains.get('extra_grounded', 0)} extra grounded / "
            f"{chains.get('unsupported', 0)} unsupported (of {chains.get('total', 0)})",
            f"- chain precision (strict/grounded): {chains.get('precision_strict', 0)} / {chains.get('grounded_precision', 0)}",
            f"- forbidden chains: {'pass' if forbidden.get('passed', True) else 'FAIL (' + str(len(forbidden.get('violations') or [])) + ' violations)'}",
            f"- quality gates: {gate_line}",
            f"- schema issues: {fixture['ontology']['schema_issues']}",
            f"- human review match: {fixture['ontology']['human_review']['matched']}",
            f"- export checks: {'pass' if fixture['export_checks']['passed'] else 'fail'}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _latest_baseline(output_root: Path, *, exclude: Path) -> Path | None:
    """Most recent report.json under `output_root`, excluding the current run."""
    candidates = sorted(
        (
            path / "report.json"
            for path in output_root.iterdir()
            if path.is_dir() and path != exclude and (path / "report.json").exists()
        ),
        key=lambda path: path.parent.name,
    )
    return candidates[-1] if candidates else None


def _report_gate_failures(report: dict[str, Any]) -> list[str]:
    """Absolute failures that do not need a baseline (forbidden chains, quality gates)."""
    failures: list[str] = []
    for item in report.get("fixtures", []):
        if not bool((item.get("scoping") or {}).get("must_keep_passed")):
            failures.append(f"{item['fixture_id']}: scoping must-keep pages failed")
        if not bool((item.get("export_checks") or {}).get("passed")):
            failures.append(f"{item['fixture_id']}: export checks failed")
        schema_errors = int(
            ((item.get("ontology") or {}).get("schema_issues_by_severity") or {}).get("error", 0)
            or 0
        )
        if schema_errors:
            failures.append(f"{item['fixture_id']}: {schema_errors} schema error(s)")
        dangling = int((item.get("ontology") or {}).get("dangling_relations", 0) or 0)
        if dangling:
            failures.append(f"{item['fixture_id']}: {dangling} dangling relation(s)")
        if not bool(((item.get("ontology") or {}).get("human_review") or {}).get("matched", True)):
            failures.append(f"{item['fixture_id']}: human-review bounds failed")
        violations = (item.get("triplets", {}).get("forbidden") or {}).get("violations") or []
        if violations:
            failures.append(f"{item['fixture_id']}: {len(violations)} forbidden chain violation(s)")
        gates = item.get("quality_gates") or {}
        for gate_name, gate in gates.items():
            if isinstance(gate, dict) and not gate.get("passed", True):
                failures.append(
                    f"{item['fixture_id']}: quality gate {gate_name} failed "
                    f"(expected {gate.get('expected')}, actual {gate.get('actual')})"
                )
    return failures


def _baseline_regressed(report: dict[str, Any], baseline_path: Path) -> bool:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_by_id = {item["fixture_id"]: item for item in baseline.get("fixtures", [])}
    for item in report.get("fixtures", []):
        previous = baseline_by_id.get(item["fixture_id"])
        if not previous:
            continue
        # When the fixture defines a min_recall floor, that absolute gate
        # replaces the "never worse than the previous run" comparison: real
        # model recall oscillates ±0.1 run-to-run, so comparing against the
        # latest run false-alarms on pure variance.
        has_recall_floor = "min_recall" in (item.get("quality_gates") or {})
        if not has_recall_floor and item["triplets"]["recall"] < previous.get("triplets", {}).get("recall", 0):
            return True
        previous_compliant = bool(previous.get("ontology", {}).get("schema_compliant"))
        if previous_compliant and not item["ontology"]["schema_compliant"]:
            return True
        # Chain-level gate only applies when the baseline already has the
        # metrics (older reports predate them). unsupported_rate is the
        # quality signal; precision_strict is deliberately NOT compared — its
        # denominator is total branch coverage, which varies run-to-run.
        previous_chains = previous.get("triplets", {}).get("chains") or {}
        current_chains = item["triplets"].get("chains") or {}
        if previous_chains and current_chains:
            if current_chains.get("unsupported_rate", 0) > previous_chains.get("unsupported_rate", 0):
                return True
        previous_review = bool(previous.get("ontology", {}).get("human_review", {}).get("matched"))
        if previous_review and not item["ontology"]["human_review"]["matched"]:
            return True
    return False


async def _main_async(args: argparse.Namespace) -> int:
    mode = args.mode
    if mode == "mock":
        os.environ["KG_LLM_MODE"] = "mock"
    else:
        os.environ.setdefault("KG_LLM_MODE", "real")
    output_root = Path(args.output_dir)
    if not output_root.is_absolute():
        output_root = REPO_ROOT / output_root
    run_dir = output_root / _now_slug()
    run_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    fixtures = [
        await _run_fixture(
            fixture_id,
            mode=mode,
            model_name=args.model,
            target_language=args.target_language,
            artifacts_dir=run_dir / "artifacts",
        )
        for fixture_id in _fixture_ids(args.fixtures)
    ]
    os.environ.pop("KG_LLM_FIXTURE", None)
    report = {
        "run_id": run_dir.name,
        "mode": mode,
        "fixtures": fixtures,
        "summary": {
            "duration_seconds": round(time.perf_counter() - started, 3),
            "fixture_count": len(fixtures),
            "average_triplet_recall": round(
                sum(item["triplets"]["recall"] for item in fixtures) / max(1, len(fixtures)),
                4,
            ),
            "schema_compliant_count": sum(1 for item in fixtures if item["ontology"]["schema_compliant"]),
        },
    }
    report_path = run_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    _write_markdown_report(run_dir / "report.md", report)
    print(str(report_path))
    if args.fail_on_regression:
        gate_failures = _report_gate_failures(report)
        if gate_failures:
            for failure in gate_failures:
                print(f"Gate failure: {failure}", file=sys.stderr)
            return 1
        baseline_path = Path(args.baseline) if args.baseline else _latest_baseline(output_root, exclude=run_dir)
        if baseline_path is not None and _baseline_regressed(report, baseline_path):
            print(f"Regression against baseline {baseline_path}", file=sys.stderr)
            return 1
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the KG pipeline against golden markdown fixtures.")
    parser.add_argument("--fixtures", default=None, help="Comma-separated fixture ids. Defaults to all.")
    parser.add_argument("--mode", choices=("mock", "economy", "full"), default="mock")
    parser.add_argument("--model", default="mock", help="Model name passed to pipeline calls.")
    parser.add_argument("--target-language", default="en")
    parser.add_argument("--output-dir", default="eval_runs")
    parser.add_argument("--baseline", default=None)
    parser.add_argument("--fail-on-regression", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_main_async(parse_args(argv or sys.argv[1:])))


if __name__ == "__main__":
    raise SystemExit(main())
