from fastapi import APIRouter, HTTPException

from backend.agents.conflict_resolution_agent import run_conflict_resolution_agent
from backend.agents.coverage_agent import run_coverage_agent
from backend.agents.extraction_agent import run_extraction_agent
from backend.agents.grounding_agent import run_grounding_agent
from backend.agents.refiner_agent import run_refiner_agent
from backend.agents.validation_agent import run_validation_agent
from backend.app_config import get_agents_config, get_pipeline_config
from backend.graph.supervisor import (
    record_conflict_route,
    record_coverage_route,
    record_extraction_route,
    record_grounding_route,
    record_refinement_route,
    record_validation_route,
)
from backend.models import ExtractRequest, ExtractionResult, Triplet
from backend.routers.upload import pdf_store
from backend.services.extraction_workflow import extract_triplets_workflow

router = APIRouter()


def _agent_enabled(agents_cfg: dict, agent_name: str, *, default: bool = False) -> bool:
    return bool((agents_cfg.get(agent_name) or {}).get("enabled", default))


def _needs_refinement(store: dict) -> bool:
    graph_state = store.get("graph_state") or {}
    return bool((graph_state.get("validation_summary") or {}).get("needs_refinement", 0))


def _sync_result_triplets(result: ExtractionResult | dict, store: dict) -> ExtractionResult | dict:
    cleaned_triplets = list((store.get("graph_state") or {}).get("cleaned_triplets") or [])
    if not cleaned_triplets:
        return result
    if isinstance(result, dict):
        synced = dict(result)
        synced["triplets"] = cleaned_triplets
        return synced
    return ExtractionResult(
        triplets=[Triplet.model_validate(item) for item in cleaned_triplets],
        raw_symptom_table=result.raw_symptom_table,
        raw_failure_mode_table=result.raw_failure_mode_table,
        raw_corrective_action_table=result.raw_corrective_action_table,
    )


@router.post("/extract-tables", response_model=ExtractionResult)
async def extract_tables(req: ExtractRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")

    store = pdf_store[req.pdf_id]
    try:
        if get_pipeline_config().get("mode") == "multi_agent":
            result = run_extraction_agent(store, req)
            agents_cfg = get_agents_config()
            validation_enabled = _agent_enabled(agents_cfg, "validation", default=True)
            coverage_enabled = _agent_enabled(agents_cfg, "coverage")
            grounding_enabled = _agent_enabled(agents_cfg, "grounding")
            conflict_enabled = _agent_enabled(agents_cfg, "conflict_resolution")
            refiner_enabled = _agent_enabled(agents_cfg, "refiner")
            record_extraction_route(
                store,
                validation_enabled=validation_enabled,
                coverage_enabled=coverage_enabled,
                grounding_enabled=grounding_enabled,
                conflict_enabled=conflict_enabled,
                refiner_enabled=refiner_enabled,
            )
            if validation_enabled:
                run_validation_agent(store)
                record_validation_route(
                    store,
                    coverage_enabled=coverage_enabled,
                    grounding_enabled=grounding_enabled,
                    conflict_enabled=conflict_enabled,
                    refiner_enabled=refiner_enabled,
                )
            if coverage_enabled:
                run_coverage_agent(store)
                record_coverage_route(
                    store,
                    grounding_enabled=grounding_enabled,
                    conflict_enabled=conflict_enabled,
                    refiner_enabled=refiner_enabled,
                )
            if grounding_enabled:
                run_grounding_agent(store)
                record_grounding_route(
                    store,
                    conflict_enabled=conflict_enabled,
                    refiner_enabled=refiner_enabled,
                )
            if refiner_enabled and _needs_refinement(store):
                run_refiner_agent(store)
                record_refinement_route(store)
                if validation_enabled:
                    run_validation_agent(store)
                    record_validation_route(
                        store,
                        coverage_enabled=False,
                        grounding_enabled=grounding_enabled,
                        conflict_enabled=conflict_enabled,
                        refiner_enabled=False,
                    )
                if grounding_enabled:
                    run_grounding_agent(store)
                    record_grounding_route(
                        store,
                        conflict_enabled=conflict_enabled,
                        refiner_enabled=False,
                    )
            if conflict_enabled:
                run_conflict_resolution_agent(store)
                record_conflict_route(store)
            return _sync_result_triplets(result, store)
        result, _ = extract_triplets_workflow(store, req)
    except RuntimeError as exc:
        detail = str(exc)
        status_code = 408 if "stopped after" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return result
