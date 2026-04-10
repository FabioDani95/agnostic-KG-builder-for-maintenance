import json
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.app_config import get_pipeline_config
from backend.graph.supervisor import record_export_route
from backend.graph.store import update_export_state
from backend.models import GenerateJsonRequest, OntologyInstance
from backend.routers.upload import pdf_store
from backend.services.ontology_merge_service import merge_validated_triplets
from backend.services.ontology_export_store import persist_exported_ontology, prepare_exported_ontology
from backend.services.ontology_pipeline import validate_ontology_instance
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.run_metrics import build_metrics_payload, record_stage_metrics
from backend.services.translation_service import translate_extraction
from backend.services.language_utils import normalize_language_code

router = APIRouter()


def _build_minimal_ontology() -> dict:
    schema = load_ontology_schema()
    return {
        "ontology_name": schema.ontology_name,
        "version": schema.version,
        "language": schema.language,
        "source_type": "",
        "source_title": "",
        "nodes": {node.name: [] for node in schema.nodes},
        "relations": [],
    }

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
            export_base_candidates.append(("ontology_draft", pipeline_state["ontology"]))
        export_base_candidates.append(("minimal_fallback", _build_minimal_ontology()))

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

        try:
            ontology_payload = prepare_exported_ontology(ontology.model_dump())
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        export_info = persist_exported_ontology(ontology_payload, req.pdf_id)
        pdf_store[req.pdf_id]["ontology_path"] = export_info["target_path"]

        translation_tokens = int(translation_usage.get("total_tokens", 0) or 0)
        translation_cost = float(translation_usage.get("estimated_cost_usd", 0) or 0)
        record_stage_metrics(
            pdf_store[req.pdf_id],
            "export",
            {
                "stage": "export",
                "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
                "llm_calls": 1 if translation_tokens else 0,
                "prompt_tokens": int(translation_usage.get("prompt_tokens", 0) or 0),
                "cached_prompt_tokens": 0,
                "non_cached_prompt_tokens": int(translation_usage.get("prompt_tokens", 0) or 0),
                "completion_tokens": int(translation_usage.get("completion_tokens", 0) or 0),
                "total_tokens": translation_tokens,
                "estimated_cost_usd": translation_cost,
                "models": [store.get("model_name")] if translation_tokens and store.get("model_name") else [],
                "operations": ["translation"] if translation_tokens else [],
                "details": {
                    "validated_triplets": len(req.validated_triplets),
                    "filename": export_info["filename"],
                    "export_base": selected_base_label,
                    "used_clean_ontology_draft": pipeline_is_clean,
                    "translation_language": target_lang if target_lang != "en" else None,
                },
            },
        )
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
            headers={"Content-Disposition": f"attachment; filename={export_info['filename']}"},
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

    try:
        ontology_payload = prepare_exported_ontology(output)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    export_info = persist_exported_ontology(ontology_payload, req.pdf_id)
    if req.pdf_id and req.pdf_id in pdf_store:
        pdf_store[req.pdf_id]["ontology_path"] = export_info["target_path"]
        record_stage_metrics(
            pdf_store[req.pdf_id],
            "export",
            {
                "stage": "export",
                "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
                "llm_calls": 0,
                "prompt_tokens": 0,
                "cached_prompt_tokens": 0,
                "non_cached_prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "models": [],
                "operations": [],
                "details": {
                    "validated_triplets": len(req.validated_triplets),
                    "filename": export_info["filename"],
                },
            },
        )
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
        headers={"Content-Disposition": f"attachment; filename={export_info['filename']}"},
    )


@router.get("/run-metrics/{pdf_id}")
async def get_run_metrics(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    return build_metrics_payload(pdf_store[pdf_id])
