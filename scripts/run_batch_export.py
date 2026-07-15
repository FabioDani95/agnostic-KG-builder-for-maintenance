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

A batch summary is also written to:
- batch_runs/<timestamp>_batch_export_summary.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
import sys
import time
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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _summary_path(summary_dir: Path) -> Path:
    return summary_dir / f"{_utc_timestamp()}_batch_export_summary.json"


def _write_summary(path: Path, summary: dict[str, Any]) -> None:
    _write_json(path, summary)


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
