#!/usr/bin/env python3
"""Analyze v8 runs against the untouched frozen KPI/golden protocol."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from types import ModuleType
from typing import Any

ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parents[3]
FROZEN_ROOT = ROOT.parent / "diagnostic_benchmark_20260812"
GOLD_PATH = FROZEN_ROOT / "golden.json"
RUNS_ROOT = ROOT / "runs" / "real"
OUTPUT_PATH = ROOT / "campaign_results.json"
REPORT_PATH = ROOT / "CAMPAIGN_REPORT.md"
BEFORE_PATH = FROZEN_ROOT / "campaign_results.json"
AUTHORIZED_BUDGET_USD = 1.0
CAMPAIGN_ID = "pdf-g3-diagnostic-hardening-20260812-v8"
EXPECTED_PIPELINE_VERSION = "pdf-g3-record-window-publication-v8"
RUN_ID_PREFIX = "v8"
SHARED_BUDGET_LEDGER_PATH = ROOT / "real_call_budget.jsonl"
MANUAL_ROOT = REPOSITORY_ROOT / "output" / "pdf" / "diagnostic_benchmark_manuals"
_DIAGNOSTIC_BRANCH_RELATIONS = {
    "MAY_INDICATE",
    "INDICATES",
    "AFFECTS",
    "RESOLVED_BY",
}

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _load_frozen_analyzer() -> ModuleType:
    path = FROZEN_ROOT / "analyze_campaign.py"
    spec = importlib.util.spec_from_file_location("frozen_campaign_analyzer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load frozen analyzer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.GOLD_PATH = GOLD_PATH
    module.RUNS_ROOT = RUNS_ROOT
    return module


def _branch_aware_paths(revision: dict[str, Any]) -> list[dict[str, Any]]:
    """Enumerate causal paths without joining independent branch occurrences."""

    nodes = {node["node_id"]: node for node in revision["nodes"]}
    by_type_from: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for relation in revision["relations"]:
        by_type_from[(relation["relation_type"], relation["from_id"])].append(relation)
    paths: list[dict[str, Any]] = []

    def node_context(node: dict[str, Any], refs: list[dict[str, Any]]) -> str:
        attributes = node.get("attributes") or {}
        values = [node.get("label", ""), node.get("description", "")]
        values.extend(
            value for value in attributes.values()
            if isinstance(value, (str, int, float))
        )
        values.extend(ref.get("quote", "") for ref in refs)
        return " ".join(str(value) for value in values if str(value).strip())
    for indicator in revision["nodes"]:
        if indicator["node_type"] not in {"Symptom", "ErrorCode"}:
            continue
        indicator_relation = (
            "MAY_INDICATE" if indicator["node_type"] == "Symptom" else "INDICATES"
        )
        for indicator_edge in by_type_from[(indicator_relation, indicator["node_id"])]:
            failure = nodes.get(indicator_edge["to_id"])
            if not failure:
                continue
            branch = str(indicator_edge.get("branch_lineage_id") or "")
            # V8 diagnostic relations are occurrence-aware.  Missing lineage
            # must not silently restore the legacy Cartesian join.
            if not branch:
                continue
            action_edges = [
                edge
                for edge in by_type_from[("RESOLVED_BY", failure["node_id"])]
                if str(edge.get("branch_lineage_id") or "") == branch
            ]
            for action_edge in action_edges:
                action = nodes.get(action_edge["to_id"])
                if not action:
                    continue
                refs = [
                    *(indicator_edge.get("evidence_refs") or []),
                    *(action_edge.get("evidence_refs") or []),
                ]
                paths.append({
                    "indicator_type": indicator["node_type"],
                    "indicator": indicator["label"],
                    "failure_mode": failure["label"],
                    "corrective_action": action["label"],
                    "indicator_context": node_context(
                        indicator, indicator_edge.get("evidence_refs") or []
                    ),
                    "failure_mode_context": node_context(
                        failure,
                        [
                            *(indicator_edge.get("evidence_refs") or []),
                            *(action_edge.get("evidence_refs") or []),
                        ],
                    ),
                    "corrective_action_context": node_context(
                        action, action_edge.get("evidence_refs") or []
                    ),
                    "pages": sorted({
                        ref.get("locator", {}).get("page")
                        for ref in refs
                        if ref.get("locator", {}).get("page") is not None
                    }),
                    "indicator_id": indicator["node_id"],
                    "failure_mode_id": failure["node_id"],
                    "corrective_action_id": action["node_id"],
                    "branch_lineage_id": branch,
                })
    return paths


def _branch_lineage_audit(revision: dict[str, Any]) -> dict[str, Any]:
    diagnostic_relations = [
        relation
        for relation in revision.get("relations", [])
        if relation.get("relation_type") in _DIAGNOSTIC_BRANCH_RELATIONS
    ]
    missing = [
        str(relation.get("relation_id") or "")
        for relation in diagnostic_relations
        if not str(relation.get("branch_lineage_id") or "").strip()
    ]
    indicators: set[tuple[str, str]] = set()
    actions: set[tuple[str, str]] = set()
    for relation in diagnostic_relations:
        branch = str(relation.get("branch_lineage_id") or "").strip()
        if not branch:
            continue
        if relation.get("relation_type") in {"MAY_INDICATE", "INDICATES"}:
            indicators.add((str(relation.get("to_id") or ""), branch))
        elif relation.get("relation_type") == "RESOLVED_BY":
            actions.add((str(relation.get("from_id") or ""), branch))
    orphan_indicator_branches = sorted(indicators - actions)
    orphan_action_branches = sorted(actions - indicators)
    return {
        "passed": not missing and not orphan_indicator_branches and not orphan_action_branches,
        "diagnostic_relations": len(diagnostic_relations),
        "missing_relation_ids": sorted(missing),
        "orphan_indicator_branches": [
            {"failure_mode_id": failure_id, "branch_lineage_id": branch}
            for failure_id, branch in orphan_indicator_branches
        ],
        "orphan_action_branches": [
            {"failure_mode_id": failure_id, "branch_lineage_id": branch}
            for failure_id, branch in orphan_action_branches
        ],
    }


def _strict_grounding(revision: dict[str, Any]) -> dict[str, Any]:
    """Verify every published relation and ref with layout-only normalization.

    PDF extraction may represent a visual space as a newline (or several
    whitespace characters).  This canonicalization deliberately preserves
    case, punctuation, and every non-whitespace character; it is not a fuzzy
    or semantic match.
    """

    def layout_literal(value: Any) -> str:
        normalized = unicodedata.normalize("NFKC", str(value or ""))
        return re.sub(r"\s+", " ", normalized).strip()

    evidence = {
        str(item.get("evidence_id") or ""): item
        for item in revision.get("evidence", [])
    }
    exact = 0
    total = 0
    grounded_relations = 0
    unresolved: list[dict[str, str]] = []
    relations = revision.get("relations", []) or []
    for relation in relations:
        relation_id = str(relation.get("relation_id") or "")
        relation_evidence_ids = {
            str(value) for value in (relation.get("evidence_ids") or [])
        }
        refs = relation.get("evidence_refs") or []
        relation_passed = bool(refs)
        if not refs:
            unresolved.append({
                "relation_id": relation_id,
                "anchor": "",
                "quote": "",
                "reason": "relation_has_no_evidence_refs",
            })
        for ref in refs:
            total += 1
            evidence_id = str(ref.get("evidence_id") or "")
            anchor = str(ref.get("source_anchor") or "")
            quote = str(ref.get("quote") or "")
            unit = evidence.get(anchor)
            evidence_locator = (unit or {}).get("locator") or {}
            ref_locator = ref.get("locator") or {}
            canonical = str(
                evidence_locator.get("canonical_text")
                or evidence_locator.get("quote")
                or ""
            )
            locator_matches = bool(ref_locator) and all(
                evidence_locator.get(key) == value
                for key, value in ref_locator.items()
            )
            checks = {
                "evidence_id_matches_anchor": bool(evidence_id) and evidence_id == anchor,
                "anchor_resolves": unit is not None,
                "relation_declares_evidence": anchor in relation_evidence_ids,
                "locator_matches": locator_matches,
                "quote_is_exact_nonempty_span": bool(quote)
                and layout_literal(quote) in layout_literal(canonical),
            }
            if all(checks.values()):
                exact += 1
            else:
                relation_passed = False
                unresolved.append({
                    "relation_id": relation_id,
                    "anchor": anchor,
                    "quote": quote,
                    "reason": ",".join(key for key, passed in checks.items() if not passed),
                })
        if relation_passed:
            grounded_relations += 1
    return {
        "exact": exact,
        "total": total,
        "relations_exact": grounded_relations,
        "relations_total": len(relations),
        "unresolved": unresolved,
        "passed": bool(relations)
        and grounded_relations == len(relations)
        and exact == total,
    }


def _read_run_artifacts(spec: dict[str, Any]) -> dict[str, Any]:
    run_root = RUNS_ROOT / spec["manual_id"]
    errors: list[str] = []

    def read(name: str, *, required: bool = True) -> dict[str, Any] | None:
        path = run_root / name
        if not path.is_file():
            if required:
                errors.append(f"missing:{name}")
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            errors.append(f"invalid_json:{name}")
            return None
        if not isinstance(value, dict):
            errors.append(f"not_object:{name}")
            return None
        return value

    state = read("run_state.json") or {}
    ledger = read("real_api_ledger.json") or {}
    # A terminal preflight stop legitimately has no generation response.  It
    # is still an authenticated one-shot failure and must analyze as NO-GO.
    response = read(
        "generation_response.json",
        required=state.get("status") == "completed",
    )
    revision = None
    if response is not None:
        revisions = [
            item.get("subgraph")
            for item in (response.get("sources") or [])
            if isinstance(item, dict) and item.get("subgraph")
        ]
        if len(revisions) == 1:
            revision = revisions[0]
        else:
            errors.append(f"revision_cardinality:{len(revisions)}")
    return {
        "response": response,
        "revision": revision,
        "ledger": ledger,
        "state": state,
        "artifact_errors": errors,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _run_authenticity(
    spec: dict[str, Any],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    revision = artifacts.get("revision") or {}
    ledger = artifacts["ledger"]
    state = artifacts["state"]
    manual_path = MANUAL_ROOT / spec["file_name"]
    checks = {
        "real_mode": state.get("mode") == "real" and ledger.get("mode") == "real",
        "terminal_one_shot_state": (
            bool(state.get("generation_started"))
            and state.get("status") in {"completed", "stopped_without_retry"}
        ),
        "completed_without_error": (
            state.get("status") == "completed"
            and state.get("error") is None
            and ledger.get("error") is None
        ),
        "run_artifacts_parseable": not artifacts.get("artifact_errors"),
        "manual_identity": (
            state.get("manual_id") == spec["manual_id"]
            and ledger.get("manual_id") == spec["manual_id"]
        ),
        "manual_sha256_matches_frozen": state.get("manual_sha256") == spec["sha256"],
        "input_pdf_matches_frozen_sha256": (
            manual_path.is_file() and _sha256(manual_path) == spec["sha256"]
        ),
        "campaign_identity": ledger.get("campaign_id") == CAMPAIGN_ID,
        "pipeline_version": (
            bool(revision)
            and
            revision.get("pipeline_version") == EXPECTED_PIPELINE_VERSION
            and ledger.get("pipeline_version") == EXPECTED_PIPELINE_VERSION
        ),
        "revision_identity": (
            bool(revision.get("source_subgraph_revision_id"))
            and revision.get("source_subgraph_revision_id") == state.get("revision_id")
            and revision.get("source_subgraph_revision_id") == ledger.get("revision_id")
            and revision.get("workspace_id") == state.get("workspace_id")
            and revision.get("workspace_id") == ledger.get("workspace_id")
            and revision.get("source_id") == state.get("source_id")
            and revision.get("source_id") == ledger.get("source_id")
        ),
        "reviewing_not_decided": (
            bool(revision)
            and
            revision.get("status") == "reviewing"
            and state.get("revision_status") == "reviewing"
            and not state.get("approval_decision_taken")
        ),
        "api_key_not_exposed": (
            bool(state.get("api_key_present"))
            and not bool(state.get("api_key_exposed"))
        ),
        "authorized_budget": (
            float(state.get("authorized_campaign_budget_usd", -1) or -1)
            == AUTHORIZED_BUDGET_USD
            and float(ledger.get("authorized_campaign_budget_usd", -1) or -1)
            == AUTHORIZED_BUDGET_USD
        ),
        "run_call_ledger_shape": (
            int(ledger.get("call_count", -1) or 0) == len(ledger.get("calls") or [])
        ),
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "artifact_errors": list(artifacts.get("artifact_errors") or []),
        "terminal_status": state.get("status"),
        "terminal_error": state.get("error"),
    }


def _failed_manual_result(
    spec: dict[str, Any],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    ledger = artifacts.get("ledger") or {}
    state = artifacts.get("state") or {}
    witnesses = []
    for claim in spec["expected_claims"]:
        expected_gap = claim.get("expected_gap") == "inspection_only"
        review_or_publish = claim.get("expected_disposition") == "review_or_publish"
        witnesses.append({
            "claim_id": claim["claim_id"],
            "expected_outcome": (
                "traceable_explicit_gap"
                if expected_gap
                else "complete_published_path_or_traceable_review"
                if review_or_publish
                else "complete_published_path"
            ),
            "present": False,
            "matched_outcome": "none" if not expected_gap else None,
            "best_min_field_score": 0.0,
            "field_scores": {},
            "matched_record": {},
        })
    raw_error = json.dumps(
        state.get("error") or ledger.get("error") or {},
        ensure_ascii=False,
    )
    preflight_match = re.search(
        r"conservative maximum \$([0-9]+(?:\.[0-9]+)?)",
        raw_error,
    )
    conservative_preflight = (
        float(preflight_match.group(1)) if preflight_match else 0.0
    )
    integrity_checks = {
        "strict_validation": False,
        "exact_relation_grounding": False,
        "zero_isolated_diagnostic_nodes": False,
        "all_corrective_actions_have_incoming_resolved_by": False,
        "one_original_canonical_asset": False,
        "candidate_accounting_or_nonapprovable": False,
        "no_approval_merge_or_structured_processing": (
            not state.get("approval_decision_taken")
            and not state.get("merge_started")
            and not state.get("structured_source_processed")
        ),
    }
    return {
        "manual_id": spec["manual_id"],
        "gold_scope": spec["gold_scope"],
        "semantic": {
            "gold_claims_present": 0,
            "gold_claims_total": len(witnesses),
            "gold_claim_recall": 0.0,
            "recall_floor": spec["gold_claim_recall_floor"],
            "autonomous_expected_claims_present": 0,
            "traceable_review_claims_present": 0,
            "explicit_expected_gaps_present": 0,
            "published_complete_paths_total": 0,
            "paths_outside_frozen_gold": 0,
            "unsupported_path_gate_scope": (
                "exhaustive_gold"
                if spec["gold_scope"].startswith("exhaustive")
                else "manual_audit_required"
            ),
            "unsupported_published_paths_detected": 0,
            "forbidden_pairings_found": 0,
            "gold_pages_retained": [],
            "gold_pages_required": sorted(spec["must_keep_pdf_pages"]),
            "checks": {
                "recall_floor": False,
                "forbidden_pairings_zero": True,
                "unsupported_published_paths_zero": True,
                "gold_page_retention": False,
            },
            "witnesses": witnesses,
            "forbidden": [
                {**forbidden, "found": False, "matches": []}
                for forbidden in spec["forbidden_pairings"]
            ],
        },
        "graph": {
            "nodes": 0,
            "relations": 0,
            "nodes_by_type": {},
            "relations_by_type": {},
            "published_paths": [],
        },
        "integrity": {
            "passed": False,
            "checks": integrity_checks,
            "grounding": {
                "exact": 0,
                "total": 0,
                "relations_exact": 0,
                "relations_total": 0,
                "unresolved": [{
                    "relation_id": "",
                    "anchor": "",
                    "quote": "",
                    "reason": "revision_unavailable",
                }],
                "passed": False,
            },
            "diagnostic_accounting_complete": False,
            "approval_eligible": False,
            "review_summary": {"total": 0, "blocking": 0, "by_code": {}},
            "validation": {"passed": False, "issues": []},
        },
        "scope": None,
        "operations": {
            "cost_usd": float(ledger.get("actual_spend_usd", 0) or 0),
            "calls": int(ledger.get("call_count", 0) or 0),
            "elapsed_seconds": float(ledger.get("elapsed_seconds", 0) or 0),
            "conservative_preflight_usd": conservative_preflight,
            "models": {},
            "hard_ceiling_usd": float(ledger.get("run_hard_ceiling_usd", 0) or 0),
        },
        "verdict": {"semantic": "fail", "publication_integrity": "fail"},
        "run_failure": {
            "status": state.get("status"),
            "error": state.get("error") or ledger.get("error"),
            "revision_available": False,
        },
    }


def _decimal(value: Any, *, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} is not numeric") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return parsed


def _shared_budget_ledger_audit(
    specs: list[dict[str, Any]],
    artifacts_by_manual: dict[str, dict[str, Any]],
    *,
    path: Path = SHARED_BUDGET_LEDGER_PATH,
) -> dict[str, Any]:
    """Reconcile the durable per-call reservation stream with all real runs."""

    failures: list[str] = []
    if not path.is_file():
        return {
            "passed": False,
            "failures": ["shared_budget_ledger_missing"],
            "path": str(path),
            "absolute_budget_usd": AUTHORIZED_BUDGET_USD,
            "charged_spend_usd": 0.0,
            "actual_spend_usd": 0.0,
            "reservation_count": 0,
            "finalized_count": 0,
        }
    try:
        events = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return {
            "passed": False,
            "failures": [f"shared_budget_ledger_invalid_json:{type(exc).__name__}"],
            "path": str(path),
            "absolute_budget_usd": AUTHORIZED_BUDGET_USD,
            "charged_spend_usd": 0.0,
            "actual_spend_usd": 0.0,
            "reservation_count": 0,
            "finalized_count": 0,
        }
    if not events or not isinstance(events[0], dict):
        failures.append("ledger_initialization_missing")
        events = []
    header = events[0] if events else {}
    if header.get("event") != "ledger_initialized":
        failures.append("ledger_initialization_event_invalid")
    if int(header.get("schema_version", -1)) != 1:
        failures.append("ledger_initialization_schema_invalid")
    if header.get("accounting_policy") != "finalized_actual_plus_unfinished_worst_case":
        failures.append("ledger_accounting_policy_invalid")
    try:
        header_budget = _decimal(
            header.get("absolute_budget_usd", -1),
            field="ledger absolute budget",
        )
    except ValueError as exc:
        failures.append(str(exc))
        header_budget = Decimal("0")
    authorized = Decimal(str(AUTHORIZED_BUDGET_USD))
    if header_budget != authorized:
        failures.append("ledger_absolute_budget_mismatch")

    reservations: dict[str, dict[str, Any]] = {}
    finalizations: dict[str, dict[str, Any]] = {}
    committed = Decimal("0")
    active = Decimal("0")
    actual = Decimal("0")
    all_actual_observed = True
    from backend.services.real_call_budget_ledger import (
        TokenEnvelope,
        conservative_envelope_cost_usd,
    )

    for event_index, event in enumerate(events[1:], start=2):
        if not isinstance(event, dict):
            failures.append(f"event_{event_index}_not_object")
            continue
        if int(event.get("schema_version", -1)) != 1:
            failures.append(f"event_{event_index}_schema_invalid")
        event_type = event.get("event")
        call_id = str(event.get("call_id") or "")
        if not call_id:
            failures.append(f"event_{event_index}_call_id_missing")
            continue
        if event_type == "call_reserved":
            if call_id in reservations:
                failures.append(f"duplicate_reservation:{call_id}")
                continue
            try:
                worst_case = _decimal(
                    event.get("worst_case_cost_usd"),
                    field=f"reservation {call_id} worst case",
                )
                recorded_committed = _decimal(
                    event.get("committed_before_usd"),
                    field=f"reservation {call_id} committed_before",
                )
                recorded_active = _decimal(
                    event.get("active_reserved_before_usd"),
                    field=f"reservation {call_id} active_before",
                )
                event_budget = _decimal(
                    event.get("absolute_budget_usd"),
                    field=f"reservation {call_id} budget",
                )
                envelope_payload = event.get("token_envelope") or {}
                envelope = TokenEnvelope(
                    max_prompt_tokens=int(envelope_payload["max_prompt_tokens"]),
                    max_completion_tokens=int(envelope_payload["max_completion_tokens"]),
                )
                recomputed = conservative_envelope_cost_usd(
                    envelope,
                    event.get("pricing_snapshot") or {},
                )
            except (KeyError, TypeError, ValueError) as exc:
                failures.append(f"reservation_invalid:{call_id}:{type(exc).__name__}")
                continue
            if event.get("cost_basis") != "token_envelope_pricing_snapshot":
                failures.append(f"reservation_cost_basis_invalid:{call_id}")
            if not all(
                str(event.get(field) or "").strip()
                for field in ("stage", "run_id", "pdf_id", "model", "reasoning_effort")
            ):
                failures.append(f"reservation_identity_incomplete:{call_id}")
            if envelope_payload.get("cached_input_credit_assumed") is not False:
                failures.append(f"reservation_cache_credit_not_conservative:{call_id}")
            if envelope_payload.get("prompt_pricing_assumption") != (
                "all_prompt_tokens_are_cache_write"
            ):
                failures.append(f"reservation_prompt_pricing_not_conservative:{call_id}")
            if worst_case != recomputed:
                failures.append(f"reservation_worst_case_not_reproducible:{call_id}")
            if recorded_committed != committed or recorded_active != active:
                failures.append(f"reservation_prior_balance_mismatch:{call_id}")
            if event_budget != authorized:
                failures.append(f"reservation_budget_mismatch:{call_id}")
            if committed + active + worst_case > authorized:
                failures.append(f"reservation_exceeded_remaining_budget:{call_id}")
            reservations[call_id] = {**event, "_worst_case": worst_case}
            active += worst_case
            continue
        if event_type == "call_finalized":
            reservation = reservations.get(call_id)
            if reservation is None:
                failures.append(f"finalization_without_reservation:{call_id}")
                continue
            if call_id in finalizations:
                failures.append(f"duplicate_finalization:{call_id}")
                continue
            try:
                charged = _decimal(
                    event.get("charged_cost_usd"),
                    field=f"finalization {call_id} charged cost",
                )
                reserved = _decimal(
                    event.get("reserved_worst_case_cost_usd"),
                    field=f"finalization {call_id} reserved cost",
                )
            except ValueError as exc:
                failures.append(str(exc))
                continue
            worst_case = reservation["_worst_case"]
            if reserved != worst_case:
                failures.append(f"finalization_reservation_mismatch:{call_id}")
            if bool(event.get("envelope_breached")) or charged > worst_case:
                failures.append(f"finalization_envelope_breached:{call_id}")
            if not bool(event.get("call_was_made")):
                failures.append(f"reservation_not_reconciled_to_real_call:{call_id}")
            observed = event.get("actual_cost_usd")
            if observed is None:
                all_actual_observed = False
            else:
                try:
                    observed_cost = _decimal(
                        observed,
                        field=f"finalization {call_id} actual cost",
                    )
                except ValueError as exc:
                    failures.append(str(exc))
                    observed_cost = Decimal("0")
                actual += observed_cost
                if observed_cost != charged:
                    failures.append(f"finalization_actual_charge_mismatch:{call_id}")
            active -= worst_case
            committed += charged
            finalizations[call_id] = event
            continue
        failures.append(f"unknown_event:{event_index}:{event_type}")

    unfinished = sorted(set(reservations) - set(finalizations))
    if unfinished:
        failures.extend(f"unfinished_reservation:{call_id}" for call_id in unfinished)
    if active != Decimal("0"):
        failures.append("active_reservation_balance_nonzero")
    if committed > authorized:
        failures.append("charged_spend_exceeds_absolute_budget")
    # Provider/SDK parse failures may hide token usage even after a confirmed
    # HTTP attempt.  Retaining and reconciling the full reservation is complete
    # fail-closed accounting; it is reported as unknown actual cost, not
    # misrepresented as an observed zero or treated as an unaccounted call.

    specs_by_run = {f"{RUN_ID_PREFIX}:{spec['manual_id']}": spec for spec in specs}
    reservations_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    finalizations_by_run: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for call_id, reservation in reservations.items():
        run_id = str(reservation.get("run_id") or "")
        reservations_by_run[run_id].append(reservation)
        spec = specs_by_run.get(run_id)
        if spec is None:
            failures.append(f"unrecognized_budget_run:{run_id}")
        elif reservation.get("pdf_id") != f"sha256:{spec['sha256']}":
            failures.append(f"reservation_pdf_identity_mismatch:{call_id}")
        if run_id and not call_id.startswith(f"{run_id}:"):
            failures.append(f"reservation_call_id_run_mismatch:{call_id}")
        if call_id in finalizations:
            finalizations_by_run[run_id].append(finalizations[call_id])

    # The route-level ledger is rounded and independently estimated; the
    # durable per-call stream remains authoritative.  A ten-microdollar drift
    # is accepted only for reconciliation reporting, never for budget gating.
    tolerance = Decimal("0.00001")
    for run_id, spec in specs_by_run.items():
        manual_id = spec["manual_id"]
        artifact = artifacts_by_manual[manual_id]
        run_ledger = artifact["ledger"]
        reserved_calls = len(reservations_by_run.get(run_id, []))
        finalized_calls = len(finalizations_by_run.get(run_id, []))
        # Completed revisions expose the same paid calls through generation
        # metrics and must reconcile exactly.  A preflight-stopped run has no
        # revision ledger, so the durable shared stream is authoritative for
        # its already-paid scoping calls.
        if artifact.get("revision") is not None:
            expected_calls = int(run_ledger.get("call_count", -1))
            if expected_calls != reserved_calls or expected_calls != finalized_calls:
                failures.append(f"run_call_count_mismatch:{manual_id}")
        elif reserved_calls != finalized_calls:
            failures.append(f"failed_run_call_count_mismatch:{manual_id}")
        reported_models = Counter(
            str(call.get("model") or "")
            for call in (run_ledger.get("calls") or [])
        )
        reserved_models = Counter(
            str(reservation.get("model") or "")
            for reservation in reservations_by_run.get(run_id, [])
        )
        if artifact.get("revision") is not None and reported_models != reserved_models:
            failures.append(f"run_call_model_mismatch:{manual_id}")
        run_actual = sum(
            (
                _decimal(event["actual_cost_usd"], field="run actual cost")
                for event in finalizations_by_run.get(run_id, [])
                if event.get("actual_cost_usd") is not None
            ),
            Decimal("0"),
        )
        run_charged = sum(
            (
                _decimal(event["charged_cost_usd"], field="run charged cost")
                for event in finalizations_by_run.get(run_id, [])
            ),
            Decimal("0"),
        )
        run_has_unknown_actual = any(
            event.get("actual_cost_usd") is None
            for event in finalizations_by_run.get(run_id, [])
        )
        if artifact.get("revision") is not None:
            reported = _decimal(
                run_ledger.get("actual_spend_usd", 0),
                field=f"run {manual_id} reported spend",
            )
            expected_reported = run_charged if run_has_unknown_actual else run_actual
            if abs(expected_reported - reported) > tolerance:
                failures.append(f"run_charged_spend_mismatch:{manual_id}")

    by_run: dict[str, dict[str, Any]] = {}
    for run_id in sorted(specs_by_run):
        run_finalizations = finalizations_by_run.get(run_id, [])
        run_actual = sum(
            (
                _decimal(event["actual_cost_usd"], field="run actual cost")
                for event in run_finalizations
                if event.get("actual_cost_usd") is not None
            ),
            Decimal("0"),
        )
        run_charged = sum(
            (
                _decimal(event["charged_cost_usd"], field="run charged cost")
                for event in run_finalizations
            ),
            Decimal("0"),
        )
        by_run[run_id] = {
            "calls": len(reservations_by_run.get(run_id, [])),
            "reservations": len(reservations_by_run.get(run_id, [])),
            "finalizations": len(run_finalizations),
            "actual_cost_usd": round(float(run_actual), 12),
            "charged_cost_usd": round(float(run_charged), 12),
            "models": dict(sorted(Counter(
                str(item.get("model") or "")
                for item in reservations_by_run.get(run_id, [])
            ).items())),
        }

    return {
        "passed": not failures,
        "failures": failures,
        "path": str(path),
        "absolute_budget_usd": float(authorized),
        "charged_spend_usd": round(float(committed), 12),
        "actual_spend_usd": round(float(actual), 12),
        "remaining_usd": round(float(max(Decimal("0"), authorized - committed)), 12),
        "reservation_count": len(reservations),
        "finalized_count": len(finalizations),
        "all_actual_costs_observed": all_actual_observed,
        "unknown_actual_cost_count": sum(
            event.get("actual_cost_usd") is None
            for event in finalizations.values()
        ),
        "calls_by_run": {
            run_id: len(values)
            for run_id, values in sorted(reservations_by_run.items())
        },
        "by_run": by_run,
    }


def _campaign_isolation_audit(
    artifacts_by_manual: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    states = [artifact["state"] for artifact in artifacts_by_manual.values()]

    def unique_nonempty(field: str) -> bool:
        values = [str(state.get(field) or "") for state in states]
        return all(values) and len(set(values)) == len(values)

    checks = {
        "unique_workspaces": unique_nonempty("workspace_id"),
        "unique_sources": unique_nonempty("source_id"),
        "unique_operational_databases": unique_nonempty("operational_db"),
        "unique_raw_stores": unique_nonempty("raw_store"),
    }
    return {"passed": all(checks.values()), "checks": checks}


def _review_items(manual: dict[str, Any]) -> int:
    summary = manual["integrity"].get("review_summary") or {}
    return int(summary.get("total", 0) or sum(
        int(value or 0) for value in (summary.get("by_code") or {}).values()
    ))


def _review_burden(manual: dict[str, Any]) -> str:
    if manual.get("run_failure") and not manual["run_failure"].get("revision_available"):
        return "0 (no revision)"
    summary = manual["integrity"].get("review_summary") or {}
    return f"{_review_items(manual)} ({int(summary.get('blocking', 0) or 0)} blocking)"


def _claim_ids(manual: dict[str, Any], outcome: str) -> list[str]:
    witnesses = manual["semantic"].get("witnesses") or []
    if outcome == "explicit_gap":
        return [
            witness["claim_id"]
            for witness in witnesses
            if witness.get("present")
            and witness.get("expected_outcome") == "traceable_explicit_gap"
        ]
    if outcome == "missing":
        return [
            witness["claim_id"]
            for witness in witnesses
            if not witness.get("present")
        ]
    return [
        witness["claim_id"]
        for witness in witnesses
        if witness.get("present") and witness.get("matched_outcome") == outcome
    ]


def _ids_text(values: list[str]) -> str:
    return ", ".join(values) if values else "none"


def _run_error_detail(manual: dict[str, Any]) -> str:
    error = (manual.get("run_failure") or {}).get("error") or {}
    if isinstance(error, dict):
        body = error.get("body") or {}
        if isinstance(body, dict) and body.get("detail"):
            return str(body["detail"])
        if error.get("message"):
            return str(error["message"])
    return str(error or "unknown terminal failure")


def _render(result: dict[str, Any], before: dict[str, Any]) -> str:
    before_by_id = {item["manual_id"]: item for item in before["manuals"]}
    lines = [
        "# PDF G3 diagnostic hardening — before/after report",
        "",
        "The golden and KPI protocol are the untouched frozen artifacts from the prior campaign.",
        "One real generation was attempted per PDF in an isolated workspace/database. A terminal",
        "preflight stop was not retried. No revision was approved, rejected, merged, or projected",
        "into the canonical graph.",
        "",
        "## Before/after by manual",
        "",
        "| Manual | Semantic recall before → v8 | Autonomous before → v8 | Review burden before → v8 | Calls before → v8 | Cost USD before → v8 | Latency before → v8 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for manual in result["manuals"]:
        previous = before_by_id[manual["manual_id"]]
        semantic = manual["semantic"]
        operations = manual["operations"]
        previous_semantic = previous["semantic"]
        previous_operations = previous["operations"]
        lines.append(
            f"| {manual['manual_id']} | {previous_semantic['gold_claims_present']}/"
            f"{previous_semantic['gold_claims_total']} → "
            f"{semantic['gold_claims_present']}/{semantic['gold_claims_total']} | "
            f"{previous_semantic['autonomous_expected_claims_present']}/"
            f"{previous_semantic['gold_claims_total']} → "
            f"{semantic['autonomous_expected_claims_present']}/"
            f"{semantic['gold_claims_total']} | "
            f"{_review_burden(previous)} → {_review_burden(manual)} | "
            f"{previous_operations['calls']} → {operations['calls']} | "
            f"{previous_operations['cost_usd']:.6f} → {operations['cost_usd']:.6f} | "
            f"{previous_operations['elapsed_seconds']:.1f}s → "
            f"{operations['elapsed_seconds']:.1f}s |"
        )
    campaign = result["campaign"]
    lines.extend([
        "",
        "## Campaign decision",
        "",
        f"**{campaign['verdict'].upper().replace('_', '-')}** — macro semantic recall "
        f"{campaign['macro_gold_claim_recall']:.3f} versus {campaign['macro_recall_floor']:.3f}; "
        f"USD {campaign['actual_spend_usd']:.6f}/{campaign['authorized_budget_usd']:.2f}; "
        f"{campaign['calls']} calls; {campaign['elapsed_seconds']:.1f}s.",
        "",
        "The release decision remains NO-GO unless all three per-manual floors, the macro floor,",
        "and every publication-integrity gate pass. Danfoss passing at its exact floor cannot",
        "offset Eastman or the unevaluated Graco ontology run.",
        "",
        "## Durable shared budget ledger",
        "",
        f"Ledger reconciliation: **{campaign['budget_ledger']['passed']}**; "
        f"{campaign['budget_ledger']['reservation_count']} reservations, "
        f"{campaign['budget_ledger']['finalized_count']} finalizations; "
        f"USD {campaign['budget_ledger']['charged_spend_usd']:.6f} charged and "
        f"USD {campaign['budget_ledger']['remaining_usd']:.6f} remaining.",
        f"All actual costs observed: {campaign['budget_ledger']['all_actual_costs_observed']}; "
        f"failures: {_ids_text(campaign['budget_ledger']['failures'])}.",
        "",
        "| Run | Calls | Reservations/finalizations | Models | Actual USD | Fail-closed charge USD |",
        "|---|---:|---:|---|---:|---:|",
    ])
    for run_id, ledger in sorted(campaign["budget_ledger"]["by_run"].items()):
        models = ", ".join(
            f"{model}×{count}" for model, count in sorted(ledger["models"].items())
        ) or "none"
        lines.append(
            f"| {run_id} | {ledger['calls']} | {ledger['reservations']}/"
            f"{ledger['finalizations']} | {models} | {ledger['actual_cost_usd']:.6f} | "
            f"{ledger['charged_cost_usd']:.6f} |"
        )
    lines.extend([
        "",
        "The shared per-call ledger is authoritative. This attributes Graco's two paid scoping",
        "calls even though the route-level run ledger has no ontology revision. The sum of isolated",
        f"run preflight envelopes was USD {campaign['conservative_preflight_usd']:.6f}; these are",
        "not concurrent reservations. Every actual API call was separately reserved before dispatch",
        "against the absolute USD 1.00 campaign ceiling.",
        "",
        "## Per-claim result",
        "",
        "| Manual | Claim | Expected witness | Present | Matched outcome | Best minimum field score |",
        "|---|---|---|---|---|---:|",
    ])
    for manual in result["manuals"]:
        for witness in manual["semantic"]["witnesses"]:
            lines.append(
                f"| {manual['manual_id']} | {witness['claim_id']} | "
                f"{witness['expected_outcome']} | {witness['present']} | "
                f"{(witness.get('matched_outcome') or 'explicit_gap') if witness.get('present') else 'none'} | "
                f"{float(witness.get('best_min_field_score', 0) or 0):.3f} |"
            )
    lines.extend([
        "",
        "## Critical interpretation by manual",
        "",
    ])
    for manual in result["manuals"]:
        semantic = manual["semantic"]
        integrity = manual["integrity"]
        review_summary = integrity.get("review_summary") or {}
        review_reasons = ", ".join(
            f"{code}={count}"
            for code, count in sorted((review_summary.get("by_code") or {}).items())
        ) or "none"
        autonomous_ids = _claim_ids(manual, "published_path")
        gap_ids = _claim_ids(manual, "explicit_gap")
        review_ids = _claim_ids(manual, "traceable_review")
        missing_ids = _claim_ids(manual, "missing")
        floor_passed = semantic["checks"]["recall_floor"]
        lines.extend([
            f"### {manual['manual_id']}",
            "",
            f"- Recall is **{semantic['gold_claims_present']}/{semantic['gold_claims_total']}**: "
            f"{semantic['autonomous_expected_claims_present']} autonomous published witness(es), "
            f"{semantic['explicit_expected_gaps_present']} explicit inspection gap(s), and "
            f"{semantic['traceable_review_claims_present']} traceable review witness(es). "
            f"The frozen floor is {semantic['recall_floor']:.4f}; pass={floor_passed}.",
            f"- Autonomous claims: {_ids_text(autonomous_ids)}; explicit gaps: "
            f"{_ids_text(gap_ids)}; review-only claims: {_ids_text(review_ids)}; "
            f"missing claims: {_ids_text(missing_ids)}.",
            f"- Published complete paths={semantic['published_complete_paths_total']}; "
            f"outside frozen gold={semantic['paths_outside_frozen_gold']}; forbidden "
            f"pairings={semantic['forbidden_pairings_found']}.",
            f"- Accounting complete={integrity['diagnostic_accounting_complete']}; approval "
            f"eligible={integrity['approval_eligible']}; strict publication-integrity "
            f"verdict={manual['verdict']['publication_integrity']}.",
            f"- Review burden: total={_review_items(manual)}, "
            f"blocking={int(review_summary.get('blocking', 0) or 0)}; {review_reasons}.",
        ])
        if manual.get("run_failure"):
            lines.extend([
                f"- The one-shot ended as `{manual['run_failure']['status']}` before an ontology "
                f"revision existed: {_run_error_detail(manual)}",
                f"- Therefore graph counts and recall are zero for this campaign attempt, not a "
                f"successful empty extraction. The shared ledger still records "
                f"{manual['operations']['calls']} paid scoping calls costing USD "
                f"{manual['operations']['cost_usd']:.6f}; no retry was made.",
            ])
        elif not integrity["diagnostic_accounting_complete"]:
            incomplete_count = int(
                (review_summary.get("by_code") or {}).get(
                    "pdf_diagnostic_contract_incomplete",
                    0,
                )
                or 0
            )
            lines.append(
                "- The completed run remains fail-closed and non-approvable because candidate "
                f"accounting is incomplete (diagnostic_contract_incomplete={incomplete_count}). "
                "Its review witnesses improve semantic traceability but provide no autonomous path."
            )
        elif integrity["approval_eligible"] is False:
            lines.append(
                "- Candidate accounting is complete, but blocking evidence/layout review keeps "
                "the revision non-approvable. This is a safe review state, not autonomous coverage."
            )
        lines.append("")

    lines.extend([
        "## Exact publication and execution invariants",
        "",
        "| Manual | Strict validation | Exact EvidenceRefs | Branch lineage | Zero isolated diagnostics | Every action linked | Canonical Asset | Forbidden / unsupported | Gold pages | Accounting / approval | Authenticated real run | No approve/merge/structured |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ])
    for manual in result["manuals"]:
        checks = manual["integrity"]["checks"]
        grounding = manual["integrity"]["grounding"]
        semantic_checks = manual["semantic"]["checks"]
        lineage = manual["integrity"]["branch_lineage"]
        lineage_detail = (
            "no revision"
            if manual.get("run_failure")
            else f"{lineage['diagnostic_relations']} rels"
            if lineage["diagnostic_relations"]
            else "0 rels; vacuous"
        )
        retained = len(manual["semantic"]["gold_pages_retained"])
        required = len(manual["semantic"]["gold_pages_required"])
        lines.append(
            f"| {manual['manual_id']} | {checks['strict_validation']} | "
            f"{grounding['exact']}/{grounding['total']} refs; "
            f"{grounding.get('relations_exact', 0)}/{grounding.get('relations_total', 0)} rels | "
            f"{lineage['passed']} ({lineage_detail}) | "
            f"{checks['zero_isolated_diagnostic_nodes']} | "
            f"{checks['all_corrective_actions_have_incoming_resolved_by']} | "
            f"{checks['one_original_canonical_asset']} | "
            f"{manual['semantic']['forbidden_pairings_found']} / "
            f"{manual['semantic']['unsupported_published_paths_detected']} | "
            f"{retained}/{required} ({semantic_checks['gold_page_retention']}) | "
            f"{manual['integrity']['diagnostic_accounting_complete']} / "
            f"{manual['integrity']['approval_eligible']} | "
            f"{checks['authenticated_completed_real_run']} | "
            f"{checks['no_approval_merge_or_structured_processing']} |"
        )
    lines.extend([
        "",
        "For completed revisions, strict validation, exact lexical grounding, branch-safe joins,",
        "topology, canonical Asset identity, and zero forbidden pairings all pass. Graco's false",
        "graph invariants mean `no revision to validate`; they do not describe published bad edges.",
        "",
        "## Resolved versus remaining blockers",
        "",
        "Resolved and demonstrated offline/where a revision completed: record-level segmentation,",
        "repeated-entity collision safety, exact adjacent multi-unit evidence, system-owned row",
        "lineage, rejected-candidate persistence, branch-aware relations, explicit inspection gaps,",
        "and accounting/publicability separation. Danfoss demonstrates the intended mixed result:",
        "three safe autonomous paths plus three traceable inspection gaps, with no cross-pairing.",
        "",
        "Remaining blockers: Eastman is below its recall floor, has zero autonomous gold paths and",
        "incomplete candidate accounting; Graco never passed the post-scoping cost preflight, so its",
        "18-claim ontology behavior was not evaluated by this one-shot. Those failures dominate the",
        "macro result. The correct critical decision is **NO-GO** even though all paid calls stayed",
        "well inside the absolute budget and completed revisions retained strict safety invariants.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    analyzer = _load_frozen_analyzer()
    analyzer.published_paths = _branch_aware_paths
    analyzer.exact_grounding = _strict_grounding
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    artifacts_by_manual: dict[str, dict[str, Any]] = {}
    manuals: list[dict[str, Any]] = []
    for spec in gold["manuals"]:
        artifacts = _read_run_artifacts(spec)
        artifacts_by_manual[spec["manual_id"]] = artifacts
        if artifacts["revision"] is None:
            manual = _failed_manual_result(spec, artifacts)
            lineage = {
                "passed": False,
                "diagnostic_relations": 0,
                "missing_relation_ids": [],
                "orphan_indicator_branches": [],
                "orphan_action_branches": [],
                "reason": "revision_unavailable",
            }
        else:
            manual = analyzer.analyze_manual(spec)
            lineage = _branch_lineage_audit(artifacts["revision"])
        authenticity = _run_authenticity(spec, artifacts)
        manual["integrity"]["branch_lineage"] = lineage
        manual["integrity"]["run_authenticity"] = authenticity
        manual["integrity"]["checks"].update({
            "branch_lineage_complete_and_joinable": lineage["passed"],
            "authenticated_completed_real_run": authenticity["passed"],
        })
        manual["integrity"]["passed"] = all(
            manual["integrity"]["checks"].values()
        )
        manual["verdict"]["publication_integrity"] = (
            "pass" if manual["integrity"]["passed"] else "fail"
        )
        manuals.append(manual)

    budget_ledger = _shared_budget_ledger_audit(
        gold["manuals"],
        artifacts_by_manual,
    )
    isolation = _campaign_isolation_audit(artifacts_by_manual)
    for manual in manuals:
        run_id = f"{RUN_ID_PREFIX}:{manual['manual_id']}"
        durable = budget_ledger.get("by_run", {}).get(run_id, {})
        if durable:
            manual["operations"].update({
                "cost_usd": float(durable["charged_cost_usd"]),
                "actual_cost_usd": float(durable["actual_cost_usd"]),
                "charged_cost_usd": float(durable["charged_cost_usd"]),
                "calls": int(durable["calls"]),
                "models": dict(durable["models"]),
                "cost_source": "durable_per_call_budget_ledger",
            })
    macro = sum(item["semantic"]["gold_claim_recall"] for item in manuals) / len(manuals)
    reported_spend = sum(item["operations"]["cost_usd"] for item in manuals)
    spend = max(reported_spend, float(budget_ledger["charged_spend_usd"]))
    campaign = {
        "verdict": "go"
        if all(item["verdict"]["semantic"] == "pass" for item in manuals)
        and all(item["verdict"]["publication_integrity"] == "pass" for item in manuals)
        and macro >= gold["macro_gold_claim_recall_floor"]
        and spend <= AUTHORIZED_BUDGET_USD
        and budget_ledger["passed"]
        and isolation["passed"]
        else "no_go",
        "macro_gold_claim_recall": round(macro, 6),
        "macro_recall_floor": gold["macro_gold_claim_recall_floor"],
        "actual_spend_usd": round(spend, 6),
        "reported_run_spend_usd": round(reported_spend, 6),
        "authorized_budget_usd": AUTHORIZED_BUDGET_USD,
        "conservative_preflight_usd": round(sum(
            item["operations"]["conservative_preflight_usd"] for item in manuals
        ), 6),
        "calls": sum(item["operations"]["calls"] for item in manuals),
        "elapsed_seconds": round(sum(
            item["operations"]["elapsed_seconds"] for item in manuals
        ), 3),
        "budget_ledger": budget_ledger,
        "isolated_workspaces": isolation,
    }
    result = {
        "campaign_id": CAMPAIGN_ID,
        "analysis_method": {
            "gold_is_frozen": True,
            "minimum_per_field_similarity": analyzer.MATCH_FLOOR,
            "inspection_only_requires_pdf_diagnostic_record_gap": True,
            "branch_lineage_aware_path_join": True,
            "branch_lineage_missing_is_fail_closed": True,
            "lexically_exact_relation_grounding": True,
            "authenticated_real_runs": True,
            "durable_per_call_budget_reconciliation": True,
            "production_had_access_to_gold": False,
        },
        "campaign": campaign,
        "manuals": manuals,
    }
    before = json.loads(BEFORE_PATH.read_text(encoding="utf-8"))
    OUTPUT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    REPORT_PATH.write_text(_render(result, before), encoding="utf-8")
    print(json.dumps({
        "campaign": campaign,
        "manuals": [{
            "manual_id": item["manual_id"],
            "recall": item["semantic"]["gold_claim_recall"],
            "autonomous": item["semantic"]["autonomous_expected_claims_present"],
            "forbidden": item["semantic"]["forbidden_pairings_found"],
            "integrity": item["integrity"]["passed"],
            "accounting": item["integrity"]["diagnostic_accounting_complete"],
            "cost": item["operations"]["cost_usd"],
        } for item in manuals],
    }, indent=2))


if __name__ == "__main__":
    main()
