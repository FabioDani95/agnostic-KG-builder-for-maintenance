import json
import re
import time
from copy import deepcopy
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.app_config import get_pipeline_config
from backend.config import settings
from backend.graph.supervisor import record_export_route
from backend.graph.store import update_export_state
from backend.models import GenerateJsonRequest, OntologyInstance
from backend.routers.upload import pdf_store
from backend.services.ontology_merge_service import merge_validated_triplets
from backend.services.ontology_export_store import (
    persist_export_metrics,
    persist_exported_ontology,
    prepare_exported_ontology,
)
from backend.services.ontology_pipeline import validate_ontology_instance
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_semantics import infer_asset_type
from backend.services.run_metrics import aggregate_usage, build_metrics_payload, record_stage_metrics
from backend.services.style_cleanup_service import cleanup_export_ontology
from backend.services.translation_service import translate_extraction
from backend.services.language_utils import normalize_language_code

router = APIRouter()

_GENERIC_BRAND_TOKENS = {
    "automatic",
    "control",
    "cutting",
    "equipment",
    "guide",
    "industrial",
    "instruction",
    "instructions",
    "laser",
    "machine",
    "maintenance",
    "manual",
    "model",
    "owner",
    "owners",
    "robot",
    "service",
    "series",
    "system",
    "technical",
    "ver",
    "version",
}
_MODEL_LABEL_RE = re.compile(r"\bmodel\s*[:#-]?\s*(.+)$", re.IGNORECASE)
_MODELISH_TOKEN_RE = re.compile(r"[A-Za-z]*\d+[A-Za-z0-9-]*")


def _clean_identity_value(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip(" \t\r\n-_:;,.")


def _source_title_from_store(store: dict | None) -> str:
    if not store:
        return ""
    source_title = _clean_identity_value(str(store.get("source_title") or ""))
    if source_title:
        return source_title
    return _clean_identity_value(Path(str(store.get("filename") or "")).stem)


def _tokenize_identity_source(value: str) -> list[str]:
    return [token for token in re.split(r"[\s/,_:;()]+", value) if token]


def _is_modelish_token(token: str) -> bool:
    cleaned = _clean_identity_value(token)
    if not cleaned:
        return False
    if _MODELISH_TOKEN_RE.search(cleaned):
        return True
    return "-" in cleaned and any(char.isalpha() for char in cleaned) and any(char.isdigit() for char in cleaned)


def _infer_asset_identity(store: dict | None) -> tuple[str, str, str]:
    source_title = _source_title_from_store(store)
    fallback_name = source_title or _clean_identity_value(Path(str((store or {}).get("filename") or "asset")).stem)
    if not source_title:
        return ("Unknown", fallback_name or "Unknown Asset", fallback_name or "Unknown Asset")

    match = _MODEL_LABEL_RE.search(source_title)
    explicit_model = _clean_identity_value(match.group(1)) if match else ""
    title_prefix = _clean_identity_value(source_title[:match.start()]) if match else source_title

    base_tokens = _tokenize_identity_source(title_prefix or source_title)
    significant_tokens = [
        token
        for token in base_tokens
        if token.lower() not in _GENERIC_BRAND_TOKENS
    ]

    first_modelish_index = next((idx for idx, token in enumerate(base_tokens) if _is_modelish_token(token)), None)
    pre_model_tokens = base_tokens[:first_modelish_index] if first_modelish_index is not None else base_tokens
    pre_model_significant = [
        token
        for token in pre_model_tokens
        if token.lower() not in _GENERIC_BRAND_TOKENS
    ]

    uppercase_brand_tokens = [
        token
        for token in pre_model_significant
        if token.isupper() and len(token) > 2 and not any(char.isdigit() for char in token)
    ]

    titlecase_prefix = []
    for token in significant_tokens:
        if any(char.isdigit() for char in token):
            break
        if token[:1].isupper() and token.lower() != token.upper() and not token.isupper():
            titlecase_prefix.append(token)
            if len(titlecase_prefix) == 2:
                break
        elif titlecase_prefix:
            break

    if len(titlecase_prefix) >= 2:
        brand = " ".join(titlecase_prefix[:2])
    elif uppercase_brand_tokens:
        brand = uppercase_brand_tokens[-1]
    elif significant_tokens:
        brand = significant_tokens[0]
    else:
        brand = base_tokens[0] if base_tokens else "Unknown"

    if explicit_model:
        model = explicit_model
    elif first_modelish_index is not None:
        model = _clean_identity_value(" ".join(base_tokens[first_modelish_index:])) or source_title
    else:
        model = source_title

    brand = _clean_identity_value(brand) or "Unknown"
    model = _clean_identity_value(model) or source_title or fallback_name or "Unknown Asset"
    name = source_title or model or fallback_name or "Unknown Asset"
    return brand, model, name


def _ensure_asset_identity(base_ontology: dict, store: dict | None) -> dict:
    ontology = deepcopy(base_ontology)
    nodes = ontology.setdefault("nodes", {})
    source_type = str(ontology.get("source_type") or (store or {}).get("source_type") or "").strip()
    source_title = _clean_identity_value(str(ontology.get("source_title") or _source_title_from_store(store)))
    ontology["source_title"] = source_title

    brand, model, asset_name = _infer_asset_identity(store)
    if source_title:
        asset_name = source_title
    asset_description = source_title or asset_name or "Technical asset extracted from manual context"

    assets = nodes.setdefault("Asset", [])
    if not assets:
        assets.append({
            "asset_id": "ASSET-001",
            "name": asset_name or "Unknown Asset",
            "description": asset_description,
            "brand": brand,
            "model": model,
            "asset_type": infer_asset_type(asset_name or source_title, source_type),
        })
        return ontology

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        if not _clean_identity_value(str(asset.get("name") or "")):
            asset["name"] = asset_name or "Unknown Asset"
        if not _clean_identity_value(str(asset.get("description") or "")):
            asset["description"] = asset_description
        if not _clean_identity_value(str(asset.get("brand") or "")):
            asset["brand"] = brand
        if not _clean_identity_value(str(asset.get("model") or "")):
            asset["model"] = model
        if not _clean_identity_value(str(asset.get("asset_type") or "")):
            asset["asset_type"] = infer_asset_type(
                str(asset.get("name") or asset_name or source_title),
                source_type,
            )
    return ontology


def _build_minimal_ontology(store: dict | None = None) -> dict:
    schema = load_ontology_schema()
    minimal = {
        "ontology_name": schema.ontology_name,
        "version": schema.version,
        "language": schema.language,
        "source_type": str((store or {}).get("source_type") or "").strip(),
        "source_title": _source_title_from_store(store),
        "nodes": {node.name: [] for node in schema.nodes},
        "relations": [],
    }
    return _ensure_asset_identity(minimal, store)


def _export_cleanup_model_name(store: dict, graph_state: dict) -> str:
    selected_models = (graph_state.get("selected_models") or store.get("selected_models") or {})
    extraction_model = str(selected_models.get("extraction") or "").strip()
    if extraction_model:
        return extraction_model
    return str(store.get("model_name") or settings.MODEL_NAME)

@router.post("/generate-json")
async def generate_json(req: GenerateJsonRequest):
    t0 = time.perf_counter()
    if req.pdf_id and req.pdf_id in pdf_store:
        store = pdf_store[req.pdf_id]
        graph_state = store.get("graph_state") or {}
        if get_pipeline_config().get("mode") == "multi_agent":
            pipeline_state = graph_state.get("ontology_pipeline") or store.get("ontology_pipeline")
        else:
            pipeline_state = store.get("ontology_pipeline")
        pipeline_has_ontology = bool(pipeline_state and pipeline_state.get("ontology"))
        pipeline_is_clean = (
            pipeline_has_ontology
            and not pipeline_state.get("schema_issues")
            and not pipeline_state.get("human_required_fields")
        )

        export_base_candidates = []
        if pipeline_has_ontology:
            export_base_candidates.append((
                "ontology_draft",
                _ensure_asset_identity(pipeline_state["ontology"], store),
            ))
        export_base_candidates.append(("minimal_fallback", _build_minimal_ontology(store)))

        last_issues: list = []
        last_human_fields: list = []
        selected_base_label = "minimal_fallback"
        ontology = None
        for base_label, base_ontology in export_base_candidates:
            output = merge_validated_triplets(base_ontology, req.validated_triplets)
            candidate = OntologyInstance.model_validate(output)
            schema_issues, human_fields = validate_ontology_instance(candidate)
            last_issues = schema_issues
            last_human_fields = human_fields
            if not schema_issues and not human_fields:
                ontology = candidate
                selected_base_label = base_label
                break

        if ontology is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Final ontology export is blocked by schema issues.",
                    "schema_issues": [issue.model_dump() for issue in last_issues],
                    "human_required_fields": [field.model_dump() for field in last_human_fields],
                },
            )

        # Translate human-readable fields if target language differs from source.
        target_lang = normalize_language_code(req.target_language)
        translation_usage = {}
        style_cleanup_usage = {}
        style_cleanup_report = {}
        if target_lang != "en":
            triplets_as_dicts = [t.model_dump() for t in req.validated_triplets]
            translated_nodes, translated_triplets_dicts, translation_usage = translate_extraction(
                nodes=ontology.nodes,
                triplets=triplets_as_dicts,
                target_language=target_lang,
                model_name=store.get("model_name"),
            )
            ontology_data = ontology.model_dump()
            ontology_data["nodes"] = translated_nodes
            ontology_data["language"] = target_lang
            ontology = OntologyInstance.model_validate(ontology_data)

        cleaned_ontology_data, style_cleanup_usage, style_cleanup_report = cleanup_export_ontology(
            ontology.model_dump(),
            target_language=target_lang,
            model_name=_export_cleanup_model_name(store, graph_state),
        )
        ontology = OntologyInstance.model_validate(cleaned_ontology_data)

        try:
            ontology_payload = prepare_exported_ontology(ontology.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        export_info = persist_exported_ontology(
            ontology_payload,
            req.pdf_id,
            manual_filename=store.get("filename"),
        )
        pdf_store[req.pdf_id]["ontology_path"] = export_info["target_path"]

        export_usage = aggregate_usage([
            entry for entry in (translation_usage, style_cleanup_usage)
            if entry
        ])
        record_stage_metrics(
            pdf_store[req.pdf_id],
            "export",
            {
                "stage": "export",
                "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
                **export_usage,
                "details": {
                    "validated_triplets": len(req.validated_triplets),
                    "filename": export_info.get("download_filename") or export_info["filename"],
                    "export_base": selected_base_label,
                    "used_clean_ontology_draft": pipeline_is_clean,
                    "translation_language": target_lang if target_lang != "en" else None,
                    "style_cleanup_fields_seen": int(style_cleanup_report.get("llm_fields_seen", 0) or 0),
                    "style_cleanup_fields_changed": int(style_cleanup_report.get("llm_fields_changed", 0) or 0),
                    "style_cleanup_fields_rejected": int(style_cleanup_report.get("llm_fields_rejected", 0) or 0),
                    "style_cleanup_deterministic_fields_changed": int(
                        style_cleanup_report.get("deterministic_fields_changed", 0) or 0
                    ),
                    "style_cleanup_model": style_cleanup_report.get("model"),
                },
            },
        )
        metrics_payload = build_metrics_payload(pdf_store[req.pdf_id])
        metrics_info = persist_export_metrics(
            metrics_payload,
            ontology_payload,
            export_info,
            manual_filename=store.get("filename"),
        )
        pdf_store[req.pdf_id]["metrics_path"] = metrics_info["target_path"]
        if get_pipeline_config().get("mode") == "multi_agent":
            update_export_state(
                store,
                ontology_payload=ontology_payload,
                export_base=selected_base_label,
            )
            record_export_route(store)
        json_str = json.dumps(ontology_payload, indent=2, ensure_ascii=False)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={export_info.get('download_filename') or export_info['filename']}"},
        )

    output = {
        "nodes": {
            "Symptom": [],
            "FailureMode": [],
            "CorrectiveAction": [],
        },
        "relations": [],
    }

    for triplet in req.validated_triplets:
        sym = triplet.symptom
        sym_dict = sym.model_dump()
        sym_dict["severity"] = sym.severity.value
        output["nodes"]["Symptom"].append(sym_dict)

        for fm in triplet.failure_modes:
            fm_dict = fm.model_dump(exclude={"linked_symptom_id"})
            output["nodes"]["FailureMode"].append(fm_dict)
            output["relations"].append({
                "name": "MAY_INDICATE",
                "from_id": sym.symptom_id,
                "to_id": fm.failure_mode_id,
            })

        for ca in triplet.corrective_actions:
            ca_dict = ca.model_dump(exclude={"linked_failure_mode_id"})
            output["nodes"]["CorrectiveAction"].append(ca_dict)
            output["relations"].append({
                "name": "RESOLVED_BY",
                "from_id": ca.linked_failure_mode_id,
                "to_id": ca.action_id,
            })

    output, style_cleanup_usage, style_cleanup_report = cleanup_export_ontology(
        output,
        target_language=normalize_language_code(req.target_language),
        model_name=settings.MODEL_NAME,
    )
    try:
        ontology_payload = prepare_exported_ontology(output)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    export_info = persist_exported_ontology(ontology_payload, req.pdf_id)
    if req.pdf_id and req.pdf_id in pdf_store:
        pdf_store[req.pdf_id]["ontology_path"] = export_info["target_path"]
        export_usage = aggregate_usage([style_cleanup_usage] if style_cleanup_usage else [])
        record_stage_metrics(
            pdf_store[req.pdf_id],
            "export",
            {
                "stage": "export",
                "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
                **export_usage,
                "details": {
                    "validated_triplets": len(req.validated_triplets),
                    "filename": export_info.get("download_filename") or export_info["filename"],
                    "style_cleanup_fields_seen": int(style_cleanup_report.get("llm_fields_seen", 0) or 0),
                    "style_cleanup_fields_changed": int(style_cleanup_report.get("llm_fields_changed", 0) or 0),
                    "style_cleanup_fields_rejected": int(style_cleanup_report.get("llm_fields_rejected", 0) or 0),
                    "style_cleanup_deterministic_fields_changed": int(
                        style_cleanup_report.get("deterministic_fields_changed", 0) or 0
                    ),
                    "style_cleanup_model": style_cleanup_report.get("model"),
                },
            },
        )
        metrics_payload = build_metrics_payload(pdf_store[req.pdf_id])
        metrics_info = persist_export_metrics(
            metrics_payload,
            ontology_payload,
            export_info,
            manual_filename=pdf_store[req.pdf_id].get("filename"),
        )
        pdf_store[req.pdf_id]["metrics_path"] = metrics_info["target_path"]
        if get_pipeline_config().get("mode") == "multi_agent":
            update_export_state(
                pdf_store[req.pdf_id],
                ontology_payload=ontology_payload,
                export_base="minimal_fallback",
            )
            record_export_route(pdf_store[req.pdf_id])
    json_str = json.dumps(ontology_payload, indent=2, ensure_ascii=False)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={export_info.get('download_filename') or export_info['filename']}"},
    )


@router.get("/run-metrics/{pdf_id}")
async def get_run_metrics(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    return build_metrics_payload(pdf_store[pdf_id])
