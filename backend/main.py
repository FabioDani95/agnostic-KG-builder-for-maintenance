import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from backend.app_config import (
    apply_runtime_overrides,
    get_effective_reflective_loop_config,
    get_effective_small_doc_threshold,
    get_extraction_config,
    get_pipeline_config,
    get_scoping_config,
)
from backend.routers import (
    chat,
    generate,
    journey,
    multi_agent,
    preparation,
    runs,
    sources,
    subgraphs,
    upload,
    workspaces,
)
from backend.security.boundary import (
    LocalRequestBoundaryMiddleware,
    RequestLimitMiddleware,
    allowed_origins,
)
from backend.storage.database import get_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

def create_app() -> FastAPI:
    get_database()
    app = FastAPI(title="Diagnostic Extraction API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins(),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "Origin"],
    )
    app.add_middleware(RequestLimitMiddleware)
    app.add_middleware(LocalRequestBoundaryMiddleware)

    app.include_router(upload.router)
    app.include_router(generate.router)
    app.include_router(multi_agent.router)
    app.include_router(chat.router)
    app.include_router(runs.router)
    app.include_router(workspaces.router)
    app.include_router(workspaces.inventory_router)
    app.include_router(sources.router)
    app.include_router(journey.router)
    app.include_router(preparation.router)
    app.include_router(subgraphs.router)

    @app.get("/api/config")
    async def get_frontend_config():
        """Return model lists and runtime-editable settings for the frontend."""
        scoping = get_scoping_config()
        extraction = get_extraction_config()
        rl = get_effective_reflective_loop_config()
        pipeline = get_pipeline_config()
        return {
            "scoping_models": scoping.get("models", []),
            "extraction_models": extraction.get("models", []),
            "pipeline": {
                "mode": pipeline.get("mode", "multi_agent"),
            },
            "small_doc_threshold": get_effective_small_doc_threshold(),
            "reflective_loop": {
                "max_retries": rl.get("max_retries", 0),
                "retry_on_severity": rl.get("retry_on_severity", "error"),
            },
        }

    @app.post("/api/config")
    async def update_runtime_config(body: dict):
        """Apply in-memory overrides to runtime-editable settings."""
        allowed = {"small_doc_threshold", "max_retries", "retry_on_severity"}
        overrides = {k: v for k, v in body.items() if k in allowed}
        apply_runtime_overrides(overrides)
        return {"status": "ok", "applied": overrides}

    @app.get("/api/health")
    async def health_check():
        """Health endpoint used by dev/test launchers."""
        return {"status": "ok", "pipeline_mode": "multi_agent"}

    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"

    @app.get("/", include_in_schema=False)
    async def console_home():
        """Open the workspace home at the canonical app URL."""
        return RedirectResponse(
            url="/home.html",
            headers={"Cache-Control": "no-store"},
        )

    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    return app


app = create_app()
