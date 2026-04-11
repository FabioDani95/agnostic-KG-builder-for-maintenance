import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.graph.store import seed_graph_state
from backend.models import LoadManualRequest, UploadResponse
from backend.services.pdf_service import (
    PdfEncryptedError,
    PdfReadError,
    extract_text_by_page,
)
from backend.services.run_metrics import ensure_run_metrics

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
MANUALS_DIR = Path(__file__).resolve().parent.parent.parent / "manuals"

# Shared in-memory store — imported by other routers
pdf_store: dict[str, dict] = {}


@router.get("/api/manuals")
async def list_manuals():
    """List available PDF manuals in the manuals/ directory."""
    if not MANUALS_DIR.exists():
        return {"manuals": []}
    manuals = []
    for f in sorted(MANUALS_DIR.iterdir()):
        if f.suffix.lower() == ".pdf":
            manuals.append({
                "filename": f.name,
                "size_bytes": f.stat().st_size,
            })
    return {"manuals": manuals}


@router.post("/api/load-manual", response_model=UploadResponse)
async def load_manual(req: LoadManualRequest):
    """Load a PDF from the manuals/ directory into memory for processing."""
    manual_path = MANUALS_DIR / req.filename
    if not manual_path.exists() or not manual_path.suffix.lower() == ".pdf":
        raise HTTPException(status_code=404, detail=f"Manual not found: {req.filename}")

    pdf_id = str(uuid.uuid4())
    pdf_path = DATA_DIR / f"{pdf_id}.pdf"
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    shutil.copy2(str(manual_path), str(pdf_path))

    try:
        pages = extract_text_by_page(str(pdf_path))
    except PdfEncryptedError as exc:
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PdfReadError as exc:
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not pages:
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Could not extract text from PDF.")

    store = {
        "pdf_id": pdf_id,
        "filename": req.filename,
        "pdf_path": str(pdf_path),
        "pages": pages,
        "page_count": len(pages),
        "source_type": "",      # filled by scoping
        "source_title": "",     # filled by scoping
        "selected_models": {
            "scoping": None,
            "ontology_draft": None,
            "extraction": None,
        },
    }
    pdf_store[pdf_id] = store
    ensure_run_metrics(store)
    seed_graph_state(store, pdf_id)

    return UploadResponse(
        pdf_id=pdf_id,
        filename=req.filename,
        page_count=len(pages),
        run_id=store["run_id"],
    )


@router.get("/pdf/{pdf_id}")
async def get_pdf(pdf_id: str):
    if pdf_id not in pdf_store:
        raise HTTPException(status_code=404, detail="PDF not found.")
    return FileResponse(
        pdf_store[pdf_id]["pdf_path"],
        media_type="application/pdf",
        filename=pdf_store[pdf_id]["filename"],
    )
