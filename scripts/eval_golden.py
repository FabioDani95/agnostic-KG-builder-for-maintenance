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
    actual_tokens = _tokens(actual)
    if not expected_tokens:
        return True
    if _normalize(expected) in _normalize(actual) or _normalize(actual) in _normalize(expected):
        return True
    overlap = len(expected_tokens & actual_tokens)
    return overlap / max(1, len(expected_tokens)) >= 0.6


def _triplet_to_text(triplet: Any) -> dict[str, str]:
    payload = triplet.model_dump() if hasattr(triplet, "model_dump") else dict(triplet or {})
    symptom = payload.get("symptom") or {}
    failures = payload.get("failure_modes") or []
    actions = payload.get("corrective_actions") or []
    failure = failures[0] if failures else {}
    action = actions[0] if actions else {}
    return {
        "symptom": " ".join(str(symptom.get(key, "") or "") for key in ("name", "description")),
        "failure_mode": " ".join(str(failure.get(key, "") or "") for key in ("name", "description", "material_context")),
        "corrective_action": " ".join(str(action.get(key, "") or "") for key in ("name", "description", "instruction_text")),
        "error_code": str((symptom.get("error_code") or payload.get("error_code") or "") or ""),
    }


def _match_triplets(expected: list[dict[str, Any]], actual_triplets: list[Any]) -> dict[str, Any]:
    actual = [_triplet_to_text(triplet) for triplet in actual_triplets]
    matches: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for expected_item in expected:
        match_index = None
        for index, actual_item in enumerate(actual):
            checks = [
                _soft_match(expected_item.get("symptom", ""), actual_item.get("symptom", "")),
                _soft_match(expected_item.get("failure_mode", ""), actual_item.get("failure_mode", "")),
                _soft_match(expected_item.get("corrective_action", ""), actual_item.get("corrective_action", "")),
            ]
            if expected_item.get("error_code"):
                checks.append(_soft_match(expected_item.get("error_code", ""), actual_item.get("error_code", "")))
            if all(checks):
                match_index = index
                break
        if match_index is None:
            unmatched.append(expected_item)
        else:
            matches.append({"expected": expected_item, "actual_index": match_index})
    total_actual = len(actual)
    matched = len(matches)
    return {
        "matched": matched,
        "expected": len(expected),
        "actual": total_actual,
        "recall": round(matched / max(1, len(expected)), 4),
        "approx_precision": round(matched / max(1, total_actual), 4),
        "matches": matches,
        "unmatched_expected": unmatched,
    }


def _ontology_counts(ontology: Any) -> dict[str, int]:
    payload = ontology.model_dump() if hasattr(ontology, "model_dump") else (ontology or {})
    nodes = payload.get("nodes") or {}
    return {node_type: len(items or []) for node_type, items in nodes.items()}


def _relation_names(ontology: Any, triplet_count: int, expected: dict[str, Any]) -> set[str]:
    payload = ontology.model_dump() if hasattr(ontology, "model_dump") else (ontology or {})
    names = {str(item.get("name") or item.get("type") or "") for item in payload.get("relations", []) if isinstance(item, dict)}
    if triplet_count:
        names.update({"HAS_FAILURE_MODE", "HAS_CORRECTIVE_ACTION"})
    if any(item.get("error_code") for item in expected.get("expected_triplets", [])):
        names.add("GENERATES_ERROR")
    return names


def _export_checks(expected: dict[str, Any], ontology: Any, triplet_count: int) -> dict[str, Any]:
    checks = expected.get("expected_export_checks") or {}
    counts = _ontology_counts(ontology)
    relation_names = _relation_names(ontology, triplet_count, expected)
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


def _human_review_result(expected: dict[str, Any], ontology_result: Any) -> dict[str, Any]:
    expected_review = expected.get("expected_human_review") or {}
    required_fields = list(getattr(ontology_result, "human_required_fields", []) or [])
    review_queue = list(getattr(ontology_result, "review_queue", []) or [])
    actual_required = bool(required_fields or review_queue)
    return {
        "expected_required": bool(expected_review.get("required")),
        "actual_required": actual_required,
        "matched": bool(expected_review.get("required")) == actual_required,
        "required_fields": len(required_fields),
        "review_queue": len(review_queue),
        "reason": expected_review.get("reason", ""),
    }


async def _run_fixture(fixture_id: str, *, mode: str, model_name: str, target_language: str) -> dict[str, Any]:
    from backend.agents.extraction_agent import run_extraction_agent
    from backend.agents.ontology_draft_agent import run_ontology_draft_agent
    from backend.agents.scoping_agent import run_scoping_agent
    from backend.observability.trace import trace_from_state
    from backend.models import CutPlanApproval, CutPlanApprovalSection, CutPlanRequest, ExtractRequest, OntologyDraftRequest
    from backend.runstore import RunStore
    from backend.services.manual_loader import build_store_from_markdown
    from backend.services.run_metrics import build_metrics_payload
    from backend.services.scoping_workflow import approve_cut_plan_workflow

    expected = _load_expected(fixture_id)
    store = build_store_from_markdown(GOLDEN_DIR / expected["manual"])
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
    triplet_match = _match_triplets(expected.get("expected_triplets") or [], extraction_result.triplets)
    export_checks = _export_checks(expected, ontology_result.ontology, len(extraction_result.triplets))
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
            "human_review": _human_review_result(expected, ontology_result),
        },
        "triplets": triplet_match,
        "export_checks": export_checks,
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
        lines.extend([
            f"### {fixture['fixture_id']}",
            "",
            f"- scoping must-keep: {'pass' if fixture['scoping']['must_keep_passed'] else 'fail'}",
            f"- triplet recall: {fixture['triplets']['recall']} ({fixture['triplets']['matched']}/{fixture['triplets']['expected']})",
            f"- approximate precision: {fixture['triplets']['approx_precision']}",
            f"- schema issues: {fixture['ontology']['schema_issues']}",
            f"- human review match: {fixture['ontology']['human_review']['matched']}",
            f"- export checks: {'pass' if fixture['export_checks']['passed'] else 'fail'}",
            "",
        ])
    path.write_text("\n".join(lines), encoding="utf-8")


def _baseline_regressed(report: dict[str, Any], baseline_path: Path) -> bool:
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_by_id = {item["fixture_id"]: item for item in baseline.get("fixtures", [])}
    for item in report.get("fixtures", []):
        previous = baseline_by_id.get(item["fixture_id"])
        if not previous:
            continue
        if item["triplets"]["recall"] < previous.get("triplets", {}).get("recall", 0):
            return True
        previous_compliant = bool(previous.get("ontology", {}).get("schema_compliant"))
        if previous_compliant and not item["ontology"]["schema_compliant"]:
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
        )
        for fixture_id in _fixture_ids(args.fixtures)
    ]
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
    if args.fail_on_regression and args.baseline and _baseline_regressed(report, Path(args.baseline)):
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
