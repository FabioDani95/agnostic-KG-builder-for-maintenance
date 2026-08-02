import hashlib
import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.graph.store import seed_graph_state
from backend.models import LoadManualRequest, UploadResponse
from backend.runstore import RunStore
from backend.security.boundary import contained_file, validate_inventory_name
from backend.services.pdf_service import (
    PdfEncryptedError,
    PdfReadError,
    extract_text_by_page,
    summarize_page_ingestion,
)
from backend.services.run_metrics import ensure_run_metrics

router = APIRouter()

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT_DIR / "data"


def _manuals_dir() -> Path:
    """Manuals directory, overridable via KG_MANUALS_DIR (used by e2e tests)."""
    override = str(os.environ.get("KG_MANUALS_DIR", "") or "").strip()
    if not override:
        return ROOT_DIR / "manuals"
    path = Path(override)
    return path if path.is_absolute() else ROOT_DIR / path

pdf_store: dict[str, dict] = {}


def _manual_inventory() -> dict[str, Path]:
    manuals_dir = _manuals_dir().resolve()
    if not manuals_dir.exists():
        return {}
    inventory: dict[str, Path] = {}
    for candidate in sorted(manuals_dir.iterdir()):
        if candidate.suffix.casefold() != ".pdf":
            continue
        try:
            path = contained_file(manuals_dir, candidate)
        except FileNotFoundError:
            continue
        inventory[candidate.name] = path
    return inventory


def _inventory_id(name: str, path: Path) -> str:
    digest = hashlib.sha256(f"{name}\x1f{path}".encode("utf-8")).hexdigest()[:24]
    return f"manual_{digest}"


@router.get("/api/manuals")
async def list_manuals():
    """List available PDF manuals in the manuals/ directory."""
    manuals = []
    for name, path in _manual_inventory().items():
        manuals.append({
            "inventory_id": _inventory_id(name, path),
            "filename": name,
            "size_bytes": path.stat().st_size,
        })
    return {"manuals": manuals}


@router.post("/api/load-manual", response_model=UploadResponse)
async def load_manual(req: LoadManualRequest):
    """Load a PDF from the manuals/ directory into memory for processing."""
    try:
        inventory_name = validate_inventory_name(req.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Manual name is not an inventory entry") from exc
    manual_path = _manual_inventory().get(inventory_name)
    if manual_path is None:
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

    if not pages or not any(str(page.get("text", "") or "").strip() for page in pages):
        pdf_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF; OCR is unavailable or returned no text.",
        )

    store = {
        "pdf_id": pdf_id,
        "filename": req.filename,
        "pdf_path": str(pdf_path),
        "pages": pages,
        "page_count": len(pages),
        "ingestion": summarize_page_ingestion(pages),
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
    try:
        RunStore().create_run(store, input_path=pdf_path)
    except Exception:
        pass

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
