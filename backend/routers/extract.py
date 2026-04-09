import time

from fastapi import APIRouter, HTTPException

from backend.models import ExtractRequest, ExtractionResult
from backend.routers.upload import pdf_store
from backend.services.llm_service import extract_triplets_chunked
from backend.services.run_metrics import record_stage_metrics

router = APIRouter()


@router.post("/extract-tables", response_model=ExtractionResult)
async def extract_tables(req: ExtractRequest):
    t0 = time.perf_counter()
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")

    store = pdf_store[req.pdf_id]
    pages = store["pages"]

    # Filter pages if a cut plan was approved or pages_to_keep is provided
    pages_to_keep = req.pages_to_keep or (store.get("cut_plan") or {}).get("pages_to_keep")
    if pages_to_keep:
        keep_set = set(pages_to_keep)
        pages = [p for p in pages if p["page_number"] in keep_set]

    # Pass section metadata so the extractor can give the LLM section context
    cut_plan = store.get("cut_plan") or {}
    sections = cut_plan.get("sections", [])

    try:
        result, usage_summary = extract_triplets_chunked(
            pages=pages,
            source_type=req.source_type,
            source_title=req.source_title,
            target_language=req.target_language,
            model_name=req.model_name,
            sections=sections,
        )
    except RuntimeError as exc:
        detail = str(exc)
        status_code = 408 if "stopped after" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc

    record_stage_metrics(
        store,
        "extraction",
        {
            "stage": "extraction",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            **usage_summary,
            "details": {
                "selected_pages": len(pages),
                "triplet_count": len(result.triplets),
                "source_type": req.source_type,
                "source_title": req.source_title,
            },
        },
    )
    return result
