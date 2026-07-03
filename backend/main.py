import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import upload, generate, graph_editor, modify, multi_agent, chat
from backend.app_config import (
    get_scoping_config, get_extraction_config,
    get_effective_small_doc_threshold, get_effective_reflective_loop_config,
    apply_runtime_overrides, get_pipeline_config,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)


def _legacy_routes_enabled() -> bool:
    return str(os.environ.get("KG_ENABLE_LEGACY_ROUTES", "")).strip().lower() in {"1", "true", "yes", "on"}


def create_app() -> FastAPI:
    app = FastAPI(title="Diagnostic Extraction API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(upload.router)
    if _legacy_routes_enabled():
        from backend.routers import cutplan, extract, ontology

        app.include_router(cutplan.router)
        app.include_router(extract.router)
        app.include_router(ontology.router)
    app.include_router(generate.router)
    app.include_router(graph_editor.router)
    app.include_router(modify.router)
    app.include_router(multi_agent.router)
    app.include_router(chat.router)

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
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    return app


app = create_app()
