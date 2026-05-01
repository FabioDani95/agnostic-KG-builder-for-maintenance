"""Interactive batch export runner for manuals/batch_manuals.

Scans manuals/batch_manuals for PDFs, asks the operator which configured model
to use, then asks for the absolute PDF page that corresponds to manual page 1
for each file. For every manual it runs:

1. load
2. scoping + automatic cut-plan approval
3. ontology draft
4. extraction
5. automatic export of all extracted triplets

Results are written to the standard output bundles:
- output/<manual_slug>/ontology.json
- output/<manual_slug>/metrics.json

A dedicated batch result folder is also written to:
- batch_runs/<timestamp>_batch_export/summary.json
- batch_runs/<timestamp>_batch_export/kpi_summary.json
- batch_runs/<timestamp>_batch_export/manuals/<manual_key>_kpis.json
- batch_runs/<timestamp>_batch_export/exports/<manual_key>/{ontology,metrics}.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import shutil
import sys
import time
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz
from fastapi import HTTPException

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

BATCH_MANUALS_DIR = REPO_ROOT / "manuals" / "batch_manuals"
DEFAULT_SUMMARY_DIR = REPO_ROOT / "batch_runs"


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-language", default="en", help="Target language for export text.")
    parser.add_argument("--log-level", default="INFO", help="Logging verbosity.")
    parser.add_argument(
        "--summary-dir",
        "--results-dir",
        dest="summary_dir",
        default=str(DEFAULT_SUMMARY_DIR.relative_to(REPO_ROOT)),
        help="Root directory where timestamped batch result folders are written.",
    )
    return parser.parse_args()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized.strip().lower()).strip("_")
    return slug or "manual"


def _manual_key(manual_path: Path, index: int) -> str:
    return f"{index:02d}_{_slugify(manual_path.stem)}"


def _list_manual_paths() -> list[Path]:
    if not BATCH_MANUALS_DIR.exists():
        raise FileNotFoundError(
            f"Batch manuals directory not found: {BATCH_MANUALS_DIR}"
        )
    manuals = sorted(
        path for path in BATCH_MANUALS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() == ".pdf"
    )
    if not manuals:
        raise FileNotFoundError(
            f"No PDF manuals found in {BATCH_MANUALS_DIR}"
        )
    return manuals


def _pdf_page_count(pdf_path: Path) -> int:
    with fitz.open(str(pdf_path)) as doc:
        return int(doc.page_count)


def _prompt_model_choice() -> str:
    from backend.app_config import get_extraction_config
    from backend.config import settings

    models = [
        model for model in (get_extraction_config().get("models") or [])
        if isinstance(model, dict) and str(model.get("id", "")).strip()
    ]
    if not models:
        return settings.MODEL_NAME

    default_index = 1
    print("\nAvailable extraction models:")
    for index, model in enumerate(models, start=1):
        label = str(model.get("label") or model["id"])
        is_default = bool(model.get("default"))
        if is_default:
            default_index = index
        suffix = " [default]" if is_default else ""
        print(f"  {index}. {label} ({model['id']}){suffix}")

    valid_ids = {str(model["id"]): str(model["id"]) for model in models}
    while True:
        raw = input(f"Choose model [default {default_index}]: ").strip()
        if not raw:
            return str(models[default_index - 1]["id"])
        if raw.isdigit():
            choice = int(raw)
            if 1 <= choice <= len(models):
                return str(models[choice - 1]["id"])
        if raw in valid_ids:
            return valid_ids[raw]
        print("Invalid model choice. Enter a list number or one of the listed model ids.")


def _prompt_page_one_absolute_page(manuals: list[Path]) -> dict[str, int]:
    answers: dict[str, int] = {}
    print("\nEnter the absolute PDF page that corresponds to manual page 1 for each file.")
    print("Press Enter to use 1 when the manual numbering starts on the first PDF page.\n")
    for manual_path in manuals:
        page_count = _pdf_page_count(manual_path)
        while True:
            raw = input(
                f"{manual_path.name} ({page_count} PDF pages) -> absolute page for manual page 1 [1]: "
            ).strip()
            if not raw:
                answers[manual_path.name] = 1
                break
            if raw.isdigit():
                absolute_page = int(raw)
                if 1 <= absolute_page <= page_count:
                    answers[manual_path.name] = absolute_page
                    break
            print(f"Invalid page. Enter an integer between 1 and {page_count}.")
    return answers


def _page_offset_from_absolute_page_one(absolute_page_one: int) -> int:
    return max(0, int(absolute_page_one) - 1)


def _ratio(numerator: int | float, denominator: int | float) -> float:
    denominator = float(denominator or 0)
    if denominator <= 0:
        return 0.0
    return round(float(numerator or 0) / denominator, 4)


def _build_store(pdf_path: Path, model_name: str) -> dict[str, Any]:
    from backend.graph.store import seed_graph_state
    from backend.routers.upload import DATA_DIR, pdf_store
    from backend.services.pdf_service import extract_text_by_page
    from backend.services.run_metrics import ensure_run_metrics

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pdf_id = str(uuid.uuid4())
    target_path = DATA_DIR / f"{pdf_id}.pdf"
    shutil.copy2(str(pdf_path), str(target_path))

    pages = extract_text_by_page(str(target_path))
    if not pages:
        raise RuntimeError(f"Could not extract text from PDF: {pdf_path}")

    store = {
        "pdf_id": pdf_id,
        "filename": pdf_path.name,
        "pdf_path": str(target_path),
        "pages": pages,
        "page_count": len(pages),
        "source_type": "",
        "source_title": "",
        "model_name": model_name,
        "selected_models": {
            "scoping": None,
            "ontology_draft": None,
            "extraction": None,
        },
    }
    pdf_store[pdf_id] = store
    ensure_run_metrics(store)
    seed_graph_state(store, pdf_id)
    return store


def _cleanup_store(store: dict[str, Any]) -> None:
    from backend.routers.upload import pdf_store
    from backend.services.ontology_export_store import GENERATED_DIR

    pdf_id = str(store.get("pdf_id", "") or "")
    pdf_path = Path(str(store.get("pdf_path", "") or ""))
    if pdf_path.exists():
        pdf_path.unlink(missing_ok=True)
    if pdf_id:
        pdf_store.pop(pdf_id, None)
        manifest_path = GENERATED_DIR / f"{pdf_id}.path"
        manifest_path.unlink(missing_ok=True)


def _approve_cut_plan(store: dict[str, Any], *, page_offset: int, model_name: str) -> dict[str, Any]:
    from backend.agents.scoping_agent import run_scoping_agent
    from backend.models import CutPlanApproval, CutPlanApprovalSection, CutPlanRequest
    from backend.services.scoping_workflow import approve_cut_plan_workflow

    req = CutPlanRequest(
        pdf_id=store["pdf_id"],
        model_name=model_name,
        page_offset=page_offset,
    )
    cut_plan = run_scoping_agent(store, req)
    approval = CutPlanApproval(
        pdf_id=store["pdf_id"],
        pages_to_keep=cut_plan.pages_to_keep,
        page_offset=page_offset,
        sections=[
            CutPlanApprovalSection(
                name=section.name,
                page_range=section.page_range,
                source=section.source,
            )
            for section in cut_plan.sections
        ],
    )
    approve_cut_plan_workflow(store, approval)
    return {
        "selected_pages": len(cut_plan.pages_to_keep),
        "pages_to_keep": list(cut_plan.pages_to_keep),
        "sections": len(cut_plan.sections),
        "skipped": bool(cut_plan.skipped),
        "product_info": cut_plan.product_info.model_dump() if cut_plan.product_info else None,
    }


def _confidence_kpis(confidence_report: Any) -> dict[str, Any]:
    if confidence_report is None:
        return {
            "available": False,
            "counts": {},
            "total_entries": 0,
            "human_review_ratio": 0.0,
            "auto_reject_ratio": 0.0,
        }
    if hasattr(confidence_report, "model_dump"):
        report = confidence_report.model_dump()
    elif isinstance(confidence_report, dict):
        report = confidence_report
    else:
        report = {}

    counts = {
        str(key): int(value or 0)
        for key, value in (report.get("counts") or {}).items()
    }
    entries = [
        item for item in (report.get("entries") or [])
        if isinstance(item, dict)
    ]
    scores = [
        float(item.get("score"))
        for item in entries
        if isinstance(item.get("score"), (int, float))
    ]
    total = sum(counts.values()) or len(entries)
    return {
        "available": True,
        "counts": counts,
        "total_entries": total,
        "theta_high": float(report.get("theta_high", 0.0) or 0.0),
        "theta_low": float(report.get("theta_low", 0.0) or 0.0),
        "auto_reject_enabled": bool(report.get("auto_reject_enabled", False)),
        "average_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
        "minimum_score": round(min(scores), 4) if scores else 0.0,
        "human_review_ratio": _ratio(counts.get("human_review", 0), total),
        "auto_reject_ratio": _ratio(counts.get("auto_reject", 0), total),
    }


async def _run_ontology_phase(store: dict[str, Any], *, model_name: str, target_language: str) -> dict[str, Any]:
    from backend.agents.ontology_draft_agent import run_ontology_draft_agent
    from backend.models import OntologyDraftRequest

    req = OntologyDraftRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type") or "Owner's manual",
        source_title=store.get("source_title") or store["filename"],
        model_name=model_name,
        pages_to_keep=None,
        target_language=target_language,
    )
    result = await run_ontology_draft_agent(store, req)
    return {
        "status": result.status,
        "retry_count": result.retry_count,
        "semantic_issues": len(result.semantic_issues),
        "schema_issues": len(result.schema_issues),
        "human_required_fields": len(result.human_required_fields),
        "graph_issues": len(result.graph_issues),
        "suggested_relations": len(result.suggested_relations),
        "is_schema_compliant": result.is_schema_compliant,
        "total_nodes": sum(len(items) for items in (result.ontology.nodes or {}).values()),
        "total_relations": len(result.ontology.relations or []),
        "confidence": _confidence_kpis(result.confidence_report),
    }


def _run_extraction_phase(store: dict[str, Any], *, model_name: str, target_language: str) -> dict[str, Any]:
    from backend.agents.extraction_agent import run_extraction_agent
    from backend.models import ExtractRequest

    req = ExtractRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type") or "Owner's manual",
        source_title=store.get("source_title") or store["filename"],
        model_name=model_name,
        pages_to_keep=None,
        target_language=target_language,
    )
    result = run_extraction_agent(store, req)
    triplets = list(getattr(result, "triplets", []) or [])
    return {
        "triplets": triplets,
        "triplet_count": len(triplets),
        "total_failure_modes": sum(len(triplet.failure_modes) for triplet in triplets),
        "total_corrective_actions": sum(len(triplet.corrective_actions) for triplet in triplets),
    }


def _run_batch_quality_checks(store: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic advisory checks that enrich batch KPIs without blocking export."""
    logger = logging.getLogger("batch_export")
    summary: dict[str, Any] = {
        "validation": {"enabled": True, "status": "not_run"},
        "coverage": {"enabled": True, "status": "not_run"},
    }
    try:
        from backend.agents.validation_agent import run_validation_agent

        verdicts, validation_summary = run_validation_agent(store)
        scores = [
            float(item.get("grounding_score", 0.0) or 0.0)
            for item in verdicts
            if isinstance(item, dict)
        ]
        summary["validation"] = {
            "enabled": True,
            "status": "ok",
            **validation_summary,
            "average_grounding_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "minimum_grounding_score": round(min(scores), 4) if scores else 0.0,
        }
    except Exception as exc:
        logger.warning("Batch validation KPI check failed: %s", exc)
        summary["validation"] = {
            "enabled": True,
            "status": "failed",
            "error": str(exc),
        }

    try:
        from backend.agents.coverage_agent import run_coverage_agent

        coverage_map = run_coverage_agent(store)
        gap_counts: dict[str, int] = {}
        for details in coverage_map.values():
            gap_type = str((details or {}).get("gap_type", "") or "")
            if not gap_type:
                continue
            gap_counts[gap_type] = gap_counts.get(gap_type, 0) + 1
        selected_pages = len(coverage_map)
        summary["coverage"] = {
            "enabled": True,
            "status": "ok",
            "selected_pages": selected_pages,
            "gap_counts": gap_counts,
            "missing_extraction_pages": gap_counts.get("missing_extraction", 0),
            "partially_covered_pages": gap_counts.get("partially_covered", 0),
            "fully_covered_pages": gap_counts.get("fully_covered", 0),
            "missing_extraction_page_ratio": _ratio(gap_counts.get("missing_extraction", 0), selected_pages),
            "partially_covered_page_ratio": _ratio(gap_counts.get("partially_covered", 0), selected_pages),
        }
    except Exception as exc:
        logger.warning("Batch coverage KPI check failed: %s", exc)
        summary["coverage"] = {
            "enabled": True,
            "status": "failed",
            "error": str(exc),
        }
    return summary


async def _run_export_phase(
    store: dict[str, Any],
    *,
    triplets: list[Any],
    target_language: str,
) -> dict[str, Any]:
    from backend.models import GenerateJsonRequest
    from backend.routers.generate import generate_json

    req = GenerateJsonRequest(
        pdf_id=store["pdf_id"],
        validated_triplets=triplets,
        target_language=target_language,
    )
    response = await generate_json(req)
    if getattr(response, "status_code", 200) >= 400:
        raise RuntimeError(f"Export failed with status {response.status_code}")
    return {
        "ontology_path": str(store.get("ontology_path") or ""),
        "metrics_path": str(store.get("metrics_path") or ""),
        "download_filename": response.headers.get("Content-Disposition", ""),
    }


def _cost_and_tokens(store: dict[str, Any]) -> tuple[float, int]:
    from backend.services.run_metrics import build_metrics_payload

    metrics_payload = build_metrics_payload(store)
    totals = metrics_payload.get("totals", {}) or {}
    return (
        float(totals.get("estimated_cost_usd", 0.0) or 0.0),
        int(totals.get("total_tokens", 0) or 0),
    )


def _read_json_file(path_value: str | Path | None) -> dict[str, Any]:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _nested(payload: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
        if current is None:
            return default
    return current


def _average(values: list[float]) -> float:
    items = [float(value) for value in values if isinstance(value, (int, float))]
    return round(sum(items) / len(items), 4) if items else 0.0


def _quality_flags(kpis: dict[str, Any], result: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if result.get("status") != "success":
        flags.append("batch_processing_not_successful")

    ontology = kpis.get("ontology_quality") or {}
    extraction = kpis.get("extraction_quality") or {}
    graph = kpis.get("graph_coverage") or {}
    validation = kpis.get("advisory_validation") or {}
    page_coverage = kpis.get("page_coverage") or {}
    confidence = kpis.get("confidence") or {}

    if int(extraction.get("triplet_count", 0) or 0) == 0 and int(kpis.get("scope", {}).get("selected_pages", 0) or 0) > 0:
        flags.append("zero_triplets_extracted")
    if float(extraction.get("triplets_per_selected_page", 0.0) or 0.0) < 0.10 and int(extraction.get("triplet_count", 0) or 0) > 0:
        flags.append("low_triplet_density")
    if int(ontology.get("schema_issue_count", 0) or 0) > 0:
        flags.append("ontology_schema_issues")
    if int(ontology.get("human_required_field_count", 0) or 0) > 0:
        flags.append("ontology_requires_human_fields")
    if int(ontology.get("semantic_issue_count", 0) or 0) > 0:
        flags.append("semantic_validation_issues")
    if int(ontology.get("retry_count", 0) or 0) > 0:
        flags.append("reflective_loop_used")

    health_score = float(graph.get("health_score", 0.0) or 0.0)
    if graph and health_score < 0.65:
        flags.append("low_graph_health_score")
    schema_integrity = graph.get("schema_integrity") or {}
    if int(schema_integrity.get("dangling_references", 0) or 0) > 0:
        flags.append("dangling_graph_references")
    if int(schema_integrity.get("domain_range_violations", 0) or 0) > 0:
        flags.append("domain_range_violations")
    failure_mode_coverage = graph.get("failure_mode_coverage") or {}
    if (
        int(failure_mode_coverage.get("failure_modes_total", 0) or 0) > 0
        and float(failure_mode_coverage.get("with_corrective_action_ratio", 0.0) or 0.0) < 0.75
    ):
        flags.append("low_failure_mode_resolution_coverage")
    if int(page_coverage.get("missing_extraction_pages", 0) or 0) > 0:
        flags.append("selected_pages_without_extractions")
    if int(page_coverage.get("partially_covered_pages", 0) or 0) > 0:
        flags.append("partially_covered_selected_pages")
    if float(validation.get("flagged_entity_ratio", 0.0) or 0.0) > 0.25:
        flags.append("high_advisory_validation_flag_rate")
    if float(confidence.get("human_review_ratio", 0.0) or 0.0) > 0.20:
        flags.append("high_confidence_human_review_ratio")
    if int((confidence.get("counts") or {}).get("auto_reject", 0) or 0) > 0:
        flags.append("confidence_auto_rejects_present")

    return sorted(dict.fromkeys(flags))


def _quality_status(flags: list[str]) -> str:
    blocking = {
        "batch_processing_not_successful",
        "zero_triplets_extracted",
        "ontology_schema_issues",
        "ontology_requires_human_fields",
        "low_graph_health_score",
        "dangling_graph_references",
        "domain_range_violations",
    }
    if any(flag in blocking for flag in flags):
        return "needs_attention"
    return "watch" if flags else "ok"


def _collect_manual_kpis(store: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    from backend.app_config import get_effective_reflective_loop_config
    from backend.services.run_metrics import build_metrics_payload

    metrics_payload = build_metrics_payload(store)
    totals = metrics_payload.get("totals", {}) or {}
    stages = metrics_payload.get("stages", {}) or {}
    ontology_details = (stages.get("ontology", {}) or {}).get("details", {}) or {}
    validation_details = (stages.get("validation", {}) or {}).get("details", {}) or {}
    batch_quality_checks = result.get("batch_quality_checks") or {}
    page_coverage = (batch_quality_checks.get("coverage") or {}).copy()

    ontology_payload = _read_json_file(store.get("ontology_path"))
    graph_coverage = (
        _nested(ontology_payload, "metadata", "graph_coverage", default=None)
        or metrics_payload.get("graph_coverage")
        or {}
    )
    ontology_summary = result.get("ontology") if isinstance(result.get("ontology"), dict) else {}
    confidence = (
        ontology_summary.get("confidence")
        or _confidence_kpis((store.get("ontology_pipeline") or {}).get("confidence_report"))
    )

    selected_pages = int(
        _nested(metrics_payload, "document", "selected_pages", default=0)
        or result.get("selected_pages")
        or 0
    )
    total_pages = int(
        _nested(metrics_payload, "document", "total_pages", default=0)
        or result.get("page_count")
        or 0
    )
    triplet_count = int(result.get("triplet_count", 0) or 0)
    failure_modes = int(result.get("total_failure_modes", 0) or 0)
    corrective_actions = int(result.get("total_corrective_actions", 0) or 0)
    flagged_entities = int(validation_details.get("flagged_entities", 0) or 0)
    total_entities = int(validation_details.get("total_entities", 0) or 0)
    page_coverage.setdefault("missing_extraction_pages", 0)
    page_coverage.setdefault("partially_covered_pages", 0)
    page_coverage.setdefault("missing_extraction_page_ratio", _ratio(page_coverage["missing_extraction_pages"], selected_pages))

    kpis: dict[str, Any] = {
        "quality_status": "unknown",
        "human_input": {
            "required_fields": ["absolute_page_one"],
            "absolute_page_one": result.get("absolute_page_one"),
            "page_offset": result.get("page_offset"),
        },
        "automation": {
            "accepted_all_triplets": result.get("status") == "success",
            "operator_triplet_validation_required": False,
            "reflective_loop": get_effective_reflective_loop_config(),
            "batch_quality_checks": {
                "validation": (batch_quality_checks.get("validation") or {}).get("status"),
                "coverage": (batch_quality_checks.get("coverage") or {}).get("status"),
            },
        },
        "scope": {
            "total_pages": total_pages,
            "selected_pages": selected_pages,
            "pages_kept_ratio": _ratio(selected_pages, total_pages),
            "selected_sections": int(result.get("selected_sections", 0) or 0),
            "scoping_skipped": bool(result.get("scoping_skipped", False)),
        },
        "ontology_quality": {
            "status": ontology_summary.get("status") or ontology_details.get("status"),
            "retry_count": int(ontology_summary.get("retry_count") or ontology_details.get("retry_count") or 0),
            "semantic_issue_count": int(ontology_summary.get("semantic_issues") or ontology_details.get("semantic_issue_count") or 0),
            "schema_issue_count": int(ontology_summary.get("schema_issues") or ontology_details.get("schema_issue_count") or 0),
            "graph_issue_count": int(ontology_summary.get("graph_issues") or ontology_details.get("graph_issue_count") or 0),
            "suggested_relation_count": int(ontology_summary.get("suggested_relations") or ontology_details.get("suggested_relation_count") or 0),
            "human_required_field_count": int(ontology_summary.get("human_required_fields") or ontology_details.get("human_required_count") or 0),
            "is_schema_compliant": bool(ontology_summary.get("is_schema_compliant", False)),
            "total_nodes": int(ontology_summary.get("total_nodes", 0) or 0),
            "total_relations": int(ontology_summary.get("total_relations", 0) or 0),
        },
        "extraction_quality": {
            "triplet_count": triplet_count,
            "failure_mode_count": failure_modes,
            "corrective_action_count": corrective_actions,
            "triplets_per_selected_page": _ratio(triplet_count, selected_pages),
            "failure_modes_per_triplet": _ratio(failure_modes, triplet_count),
            "corrective_actions_per_failure_mode": _ratio(corrective_actions, failure_modes),
        },
        "advisory_validation": {
            **validation_details,
            "flagged_entity_ratio": _ratio(flagged_entities, total_entities),
        },
        "page_coverage": page_coverage,
        "confidence": confidence,
        "graph_coverage": graph_coverage,
        "resolution_completion": metrics_payload.get("resolution_completion") or {},
        "cost_and_runtime": {
            "duration_seconds": round(float(result.get("duration_seconds", 0.0) or 0.0), 3),
            "tokens": int(totals.get("total_tokens", result.get("total_tokens", 0)) or 0),
            "estimated_cost_usd": round(float(totals.get("estimated_cost_usd", result.get("estimated_cost_usd", 0.0)) or 0.0), 6),
            "seconds_per_selected_page": _ratio(float(result.get("duration_seconds", 0.0) or 0.0), selected_pages),
            "cost_per_extracted_triplet_usd": _ratio(float(totals.get("estimated_cost_usd", 0.0) or 0.0), triplet_count),
        },
    }
    flags = _quality_flags(kpis, result)
    kpis["quality_flags"] = flags
    kpis["quality_status"] = _quality_status(flags)
    return kpis


def _copy_export_artifacts(
    batch_results_dir: Path,
    *,
    manual_key: str,
    ontology_path: str,
    metrics_path: str,
) -> dict[str, str]:
    export_dir = batch_results_dir / "exports" / manual_key
    export_dir.mkdir(parents=True, exist_ok=True)
    copied: dict[str, str] = {"batch_export_dir": str(export_dir)}
    for label, source_value in (("ontology", ontology_path), ("metrics", metrics_path)):
        source_path = Path(str(source_value or ""))
        if not source_path.exists() or not source_path.is_file():
            continue
        target_path = export_dir / f"{label}.json"
        shutil.copy2(str(source_path), str(target_path))
        copied[f"batch_{label}_path"] = str(target_path)
    return copied


def _batch_results_dir(results_root: Path) -> Path:
    results_root.mkdir(parents=True, exist_ok=True)
    batch_dir = results_root / f"{_utc_timestamp()}_batch_export"
    batch_dir.mkdir(parents=True, exist_ok=False)
    return batch_dir


def _batch_totals(results: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [item for item in results if item.get("status") == "success"]
    failed = [item for item in results if item.get("status") == "failed"]
    interrupted = [item for item in results if item.get("status") == "interrupted"]
    quality_kpis = [item.get("quality_kpis") or {} for item in successful]
    return {
        "processed": len(results),
        "success": len(successful),
        "failed": len(failed),
        "interrupted": len(interrupted),
        "total_triplets": sum(int(item.get("triplet_count", 0) or 0) for item in successful),
        "total_tokens": sum(int(item.get("total_tokens", 0) or 0) for item in successful),
        "estimated_cost_usd": round(
            sum(float(item.get("estimated_cost_usd", 0.0) or 0.0) for item in successful),
            6,
        ),
        "total_duration_seconds": round(
            sum(float(item.get("duration_seconds", 0.0) or 0.0) for item in results),
            3,
        ),
        "total_semantic_issues": sum(
            int(_nested(kpis, "ontology_quality", "semantic_issue_count", default=0) or 0)
            for kpis in quality_kpis
        ),
        "total_schema_issues": sum(
            int(_nested(kpis, "ontology_quality", "schema_issue_count", default=0) or 0)
            for kpis in quality_kpis
        ),
        "total_graph_issues": sum(
            int(_nested(kpis, "ontology_quality", "graph_issue_count", default=0) or 0)
            for kpis in quality_kpis
        ),
        "total_reflective_retries": sum(
            int(_nested(kpis, "ontology_quality", "retry_count", default=0) or 0)
            for kpis in quality_kpis
        ),
        "avg_graph_health_score": _average([
            _nested(kpis, "graph_coverage", "health_score", default=0.0)
            for kpis in quality_kpis
            if kpis.get("graph_coverage")
        ]),
        "avg_triplets_per_selected_page": _average([
            _nested(kpis, "extraction_quality", "triplets_per_selected_page", default=0.0)
            for kpis in quality_kpis
        ]),
    }


def _batch_config_snapshot() -> dict[str, Any]:
    from backend.app_config import (
        get_agents_config,
        get_effective_reflective_loop_config,
        get_pipeline_config,
    )

    agents = get_agents_config()
    return {
        "pipeline": get_pipeline_config(),
        "reflective_loop": get_effective_reflective_loop_config(),
        "agents_enabled": {
            name: bool((cfg or {}).get("enabled", False))
            for name, cfg in agents.items()
        },
        "batch_quality_checks": {
            "validation": "always_run_advisory",
            "coverage": "always_run_advisory",
        },
    }


def _build_summary(
    *,
    results: list[dict[str, Any]],
    model_name: str,
    target_language: str,
    interrupted: bool,
    batch_results_dir: Path,
) -> dict[str, Any]:
    return {
        "started_at": results[0]["started_at"] if results else _now_iso(),
        "finished_at": _now_iso(),
        "batch_directory": str(BATCH_MANUALS_DIR.relative_to(REPO_ROOT)),
        "batch_results_directory": str(batch_results_dir),
        "model": model_name,
        "target_language": target_language,
        "config": _batch_config_snapshot(),
        "interrupted": interrupted,
        "manuals": results,
        "totals": _batch_totals(results),
    }


def _build_batch_kpi_summary(summary: dict[str, Any]) -> dict[str, Any]:
    successful = [
        item for item in summary.get("manuals", [])
        if item.get("status") == "success"
    ]
    kpis = [item.get("quality_kpis") or {} for item in successful]
    quality_status_counts: dict[str, int] = {}
    flag_counts: dict[str, int] = {}
    for manual_kpis in kpis:
        status = str(manual_kpis.get("quality_status") or "unknown")
        quality_status_counts[status] = quality_status_counts.get(status, 0) + 1
        for flag in manual_kpis.get("quality_flags") or []:
            flag = str(flag)
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    return {
        "started_at": summary.get("started_at"),
        "finished_at": summary.get("finished_at"),
        "batch_results_directory": summary.get("batch_results_directory"),
        "batch_directory": summary.get("batch_directory"),
        "model": summary.get("model"),
        "target_language": summary.get("target_language"),
        "automation_contract": {
            "human_inputs_required": ["absolute_page_one_per_manual"],
            "triplet_validation": "auto_accept_all",
            "cut_plan_approval": "auto_accept_scoping_agent_output",
        },
        "config": summary.get("config") or {},
        "totals": summary.get("totals") or {},
        "quality_status_counts": quality_status_counts,
        "quality_flag_counts": dict(sorted(flag_counts.items())),
        "aggregate_quality": {
            "avg_graph_health_score": _average([
                _nested(item, "graph_coverage", "health_score", default=0.0)
                for item in kpis
                if item.get("graph_coverage")
            ]),
            "avg_pages_kept_ratio": _average([
                _nested(item, "scope", "pages_kept_ratio", default=0.0)
                for item in kpis
            ]),
            "avg_triplets_per_selected_page": _average([
                _nested(item, "extraction_quality", "triplets_per_selected_page", default=0.0)
                for item in kpis
            ]),
            "avg_corrective_actions_per_failure_mode": _average([
                _nested(item, "extraction_quality", "corrective_actions_per_failure_mode", default=0.0)
                for item in kpis
            ]),
            "avg_advisory_validation_flagged_entity_ratio": _average([
                _nested(item, "advisory_validation", "flagged_entity_ratio", default=0.0)
                for item in kpis
            ]),
            "avg_confidence_human_review_ratio": _average([
                _nested(item, "confidence", "human_review_ratio", default=0.0)
                for item in kpis
                if (item.get("confidence") or {}).get("available")
            ]),
        },
        "per_manual": [
            {
                "manual_key": item.get("manual_key"),
                "filename": item.get("filename"),
                "status": item.get("status"),
                "quality_status": (item.get("quality_kpis") or {}).get("quality_status"),
                "quality_flags": (item.get("quality_kpis") or {}).get("quality_flags") or [],
                "graph_health_score": _nested(item.get("quality_kpis") or {}, "graph_coverage", "health_score", default=None),
                "triplets_per_selected_page": _nested(item.get("quality_kpis") or {}, "extraction_quality", "triplets_per_selected_page", default=None),
                "validation_flagged_entity_ratio": _nested(item.get("quality_kpis") or {}, "advisory_validation", "flagged_entity_ratio", default=None),
                "retry_count": _nested(item.get("quality_kpis") or {}, "ontology_quality", "retry_count", default=0),
                "ontology_path": item.get("ontology_path"),
                "metrics_path": item.get("metrics_path"),
                "batch_artifacts": item.get("batch_artifacts") or {},
            }
            for item in summary.get("manuals", [])
        ],
        "kpi_definitions": {
            "graph_health_score": "0-1 aggregate graph coverage/integrity score computed from the exported ontology.",
            "triplets_per_selected_page": "Extracted diagnostic triplets divided by scoped pages.",
            "flagged_entity_ratio": "Advisory validation entities not accepted divided by all validated entities.",
            "confidence_human_review_ratio": "Ontology nodes classified as human_review divided by all confidence-scored nodes.",
            "missing_extraction_page_ratio": "Scoped diagnostic pages with no extracted entities divided by scoped pages.",
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_batch_artifacts(batch_results_dir: Path, summary: dict[str, Any]) -> None:
    _write_json(batch_results_dir / "summary.json", summary)
    _write_json(batch_results_dir / "kpi_summary.json", _build_batch_kpi_summary(summary))
    manuals_dir = batch_results_dir / "manuals"
    manuals_dir.mkdir(parents=True, exist_ok=True)
    for item in summary.get("manuals", []):
        manual_key = str(item.get("manual_key") or _slugify(str(item.get("filename") or "manual")))
        _write_json(
            manuals_dir / f"{manual_key}_kpis.json",
            {
                "manual_key": manual_key,
                "filename": item.get("filename"),
                "status": item.get("status"),
                "started_at": item.get("started_at"),
                "finished_at": item.get("finished_at"),
                "paths": {
                    "ontology": item.get("ontology_path"),
                    "metrics": item.get("metrics_path"),
                    **(item.get("batch_artifacts") or {}),
                },
                "quality_kpis": item.get("quality_kpis") or {},
                "batch_quality_checks": item.get("batch_quality_checks") or {},
                "error": item.get("error"),
            },
        )


async def _process_manual(
    manual_path: Path,
    *,
    model_name: str,
    absolute_page_one: int,
    target_language: str,
    index: int,
    total: int,
) -> dict[str, Any]:
    logger = logging.getLogger("batch_export")
    page_offset = _page_offset_from_absolute_page_one(absolute_page_one)
    started_at_perf = time.perf_counter()
    started_at = _now_iso()
    store: dict[str, Any] | None = None

    result: dict[str, Any] = {
        "filename": manual_path.name,
        "status": "success",
        "started_at": started_at,
        "model": model_name,
        "target_language": target_language,
        "absolute_page_one": absolute_page_one,
        "page_offset": page_offset,
        "page_count": 0,
    }

    logger.info("[%d/%d] Starting %s", index, total, manual_path.name)
    try:
        store = _build_store(manual_path, model_name)
        result["page_count"] = int(store.get("page_count") or 0)
        logger.info("[%d/%d] pages=%d absolute_page_one=%d page_offset=%d model=%s",
                    index, total, result["page_count"], absolute_page_one, page_offset, model_name)

        scoping_summary = _approve_cut_plan(store, page_offset=page_offset, model_name=model_name)
        result.update({
            "selected_pages": scoping_summary["selected_pages"],
            "selected_sections": scoping_summary["sections"],
            "scoping_skipped": scoping_summary["skipped"],
            "product_info": scoping_summary["product_info"],
        })
        logger.info("[%d/%d] scoping: selected_pages=%d sections=%d skipped=%s",
                    index, total, scoping_summary["selected_pages"], scoping_summary["sections"], scoping_summary["skipped"])

        try:
            ontology_summary = await _run_ontology_phase(
                store,
                model_name=model_name,
                target_language=target_language,
            )
            result["ontology"] = ontology_summary
            logger.info(
                "[%d/%d] ontology: status=%s nodes=%d relations=%d human_required=%d schema_issues=%d",
                index,
                total,
                ontology_summary["status"],
                ontology_summary["total_nodes"],
                ontology_summary["total_relations"],
                ontology_summary["human_required_fields"],
                ontology_summary["schema_issues"],
            )
        except Exception as exc:
            result["ontology_error"] = str(exc)
            logger.warning(
                "[%d/%d] ontology draft failed for %s; continuing with minimal export fallback: %s",
                index,
                total,
                manual_path.name,
                exc,
            )

        extraction_summary = _run_extraction_phase(
            store,
            model_name=model_name,
            target_language=target_language,
        )
        result.update({
            "triplet_count": extraction_summary["triplet_count"],
            "total_failure_modes": extraction_summary["total_failure_modes"],
            "total_corrective_actions": extraction_summary["total_corrective_actions"],
        })
        logger.info(
            "[%d/%d] extraction: triplets=%d failure_modes=%d corrective_actions=%d",
            index,
            total,
            extraction_summary["triplet_count"],
            extraction_summary["total_failure_modes"],
            extraction_summary["total_corrective_actions"],
        )

        export_summary = await _run_export_phase(
            store,
            triplets=extraction_summary["triplets"],
            target_language=target_language,
        )
        result.update({
            "ontology_path": export_summary["ontology_path"],
            "metrics_path": export_summary["metrics_path"],
        })
        logger.info(
            "[%d/%d] export: ontology=%s metrics=%s",
            index,
            total,
            export_summary["ontology_path"] or "<missing>",
            export_summary["metrics_path"] or "<missing>",
        )
    except HTTPException as exc:
        result["status"] = "failed"
        result["error"] = exc.detail
        logger.exception("[%d/%d] %s failed with HTTPException: %s", index, total, manual_path.name, exc.detail)
    except asyncio.CancelledError:
        result["status"] = "interrupted"
        result["error"] = "Interrupted by operator."
        logger.warning("[%d/%d] %s interrupted by operator", index, total, manual_path.name)
        raise
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = str(exc)
        logger.exception("[%d/%d] %s failed: %s", index, total, manual_path.name, exc)
    finally:
        if store is not None:
            estimated_cost_usd, total_tokens = _cost_and_tokens(store)
            result["estimated_cost_usd"] = round(estimated_cost_usd, 6)
            result["total_tokens"] = total_tokens
            _cleanup_store(store)
        else:
            result["estimated_cost_usd"] = 0.0
            result["total_tokens"] = 0
        result["duration_seconds"] = round(max(0.0, time.perf_counter() - started_at_perf), 3)
        result["finished_at"] = _now_iso()

    if result["status"] == "success":
        logger.info(
            "[%d/%d] completed %s in %.2fs cost=$%.6f tokens=%d",
            index,
            total,
            manual_path.name,
            result["duration_seconds"],
            result["estimated_cost_usd"],
            result["total_tokens"],
        )
    return result


async def _main_async() -> int:
    args = _parse_args()
    _setup_logging(args.log_level)
    logger = logging.getLogger("batch_export")

    manuals = _list_manual_paths()
    model_name = _prompt_model_choice()
    absolute_page_one_by_name = _prompt_page_one_absolute_page(manuals)
    target_language = str(args.target_language or "en").strip() or "en"

    logger.info("Batch directory: %s", BATCH_MANUALS_DIR)
    logger.info("Manuals found: %d", len(manuals))
    logger.info("Selected model: %s", model_name)
    logger.info("Target language: %s", target_language)

    results: list[dict[str, Any]] = []
    summary_dir = REPO_ROOT / args.summary_dir
    summary_path = _summary_path(summary_dir)
    interrupted = False

    for index, manual_path in enumerate(manuals, start=1):
        try:
            manual_result = await _process_manual(
                manual_path,
                model_name=model_name,
                absolute_page_one=absolute_page_one_by_name[manual_path.name],
                target_language=target_language,
                index=index,
                total=len(manuals),
            )
            results.append(manual_result)
        except (KeyboardInterrupt, asyncio.CancelledError):
            interrupted = True
            page_offset = _page_offset_from_absolute_page_one(absolute_page_one_by_name[manual_path.name])
            results.append({
                "filename": manual_path.name,
                "status": "interrupted",
                "started_at": _now_iso(),
                "finished_at": _now_iso(),
                "duration_seconds": 0.0,
                "model": model_name,
                "target_language": target_language,
                "absolute_page_one": absolute_page_one_by_name[manual_path.name],
                "page_offset": page_offset,
                "page_count": 0,
                "estimated_cost_usd": 0.0,
                "total_tokens": 0,
                "error": "Interrupted by operator.",
            })
            logger.warning("Batch interrupted while processing %s", manual_path.name)
            break

        _write_summary(
            summary_path,
            _build_summary(
                results=results,
                model_name=model_name,
                target_language=target_language,
                interrupted=False,
            ),
        )

    summary = _build_summary(
        results=results,
        model_name=model_name,
        target_language=target_language,
        interrupted=interrupted,
    )
    _write_summary(summary_path, summary)
    logger.info("Batch summary written to %s", summary_path.relative_to(REPO_ROOT))

    print("\n" + "=" * 72)
    print("BATCH EXPORT SUMMARY")
    print("=" * 72)
    print(json.dumps(summary["totals"], indent=2, ensure_ascii=False))
    print(f"Summary file: {summary_path}")

    if interrupted:
        return 130
    return 0 if summary["totals"]["failed"] == 0 else 1


def main() -> int:
    return asyncio.run(_main_async())


if __name__ == "__main__":
    sys.exit(main())
