"""Deprecated step-wise extraction endpoint.

This route is kept only for legacy/manual compatibility and is mounted when
KG_ENABLE_LEGACY_ROUTES=1. Chat-first multi-agent services are the active
runtime path.
"""

from fastapi import APIRouter, HTTPException

from backend.models import ExtractRequest, ExtractionResult
from backend.routers.upload import pdf_store
from backend.services.extraction_pipeline import run_extraction_pipeline

router = APIRouter(tags=["legacy-step-wise"], deprecated=True)


@router.post("/extract-tables", response_model=ExtractionResult)
async def extract_tables(req: ExtractRequest):
    if req.pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found. Upload a PDF first.")

    store = pdf_store[req.pdf_id]
    try:
        return run_extraction_pipeline(store, req)
    except RuntimeError as exc:
        detail = str(exc)
        status_code = 408 if "stopped after" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc
