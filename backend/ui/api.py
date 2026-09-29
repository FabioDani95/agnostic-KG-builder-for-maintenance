"""Local web API of the prototype interface (docs/PIANO_FRONTEND.md, section 6).

Only for localhost, without authentication. Campaign runs are read, never written.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from backend.ui.budget import Limits, Spending, estimate
from backend.ui.catalog import Catalog, process_alive
from backend.ui.events import UiEvent
from backend.ui.evidence import Evidence
from backend.ui.jobs import JobError, Jobs
from backend.ui.questions import HUMAN_QUESTION_BUDGET, open_for_people, question_views
from backend.ui.replay import replay_events

ROOT = Path(__file__).resolve().parents[2]
FINAL_KINDS = {"run_finished", "run_failed"}
HEARTBEAT_SECONDS = 15.0


class MachineIn(BaseModel):
    upload_id: str
    name: str
    brand: str = ""
    model: str = ""
    type: str = ""


class RunIn(BaseModel):
    reviewers: str


@dataclass
class UiSettings:
    root: Path = ROOT
    campaign: Path = field(default_factory=lambda: ROOT / "campaign")
    workspace: Path = field(default_factory=lambda: Path(os.environ.get("KG_UI_WORKSPACE", ROOT / "workspace")))
    ledger: Path = field(default_factory=lambda: ROOT / "campaign" / "real_call_budget.jsonl")
    frontend: Path = field(default_factory=lambda: ROOT / "frontend" / "dist")
    limits: Limits = field(default_factory=Limits)


def sse(event: UiEvent) -> str:
    return f"id: {event.seq}\ndata: {event.model_dump_json()}\n\n"


async def _pause(seconds: float) -> AsyncIterator[str]:
    """Wait, sending a comment line now and then so the connection stays open."""

    while seconds > 0:
        step = min(seconds, HEARTBEAT_SECONDS)
        await asyncio.sleep(step)
        seconds -= step
        if seconds > 0:
            yield ": attesa\n\n"


async def paced(events: list[UiEvent], after: int, speed: float) -> AsyncIterator[str]:
    """Replay events after ``after`` at ``speed`` times real time (0: all at once)."""

    previous = None
    for event in events:
        if event.seq <= after:
            continue
        if speed > 0 and previous is not None and event.t > previous:
            async for line in _pause((event.t - previous) / speed):
                yield line
        previous = event.t
        yield sse(event)


async def tail(path: Path, after: int, alive=lambda: True, poll: float = 0.5) -> AsyncIterator[str]:
    """Follow the events.jsonl of a running run until it ends."""

    position, idle, last = 0, 0.0, None
    while True:
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        for line in lines[position:]:
            if not line.strip():
                continue
            event = last = UiEvent.model_validate_json(line)
            if event.seq > after:
                yield sse(event)
            if event.kind in FINAL_KINDS:
                return
        position = len(lines)
        if not alive():
            # The process ended without saying so (for example a crash before its first event).
            log = path.with_name("job.log")
            tail_text = log.read_text(encoding="utf-8").strip().splitlines()[-1:] if log.exists() else []
            yield sse(UiEvent(seq=(last.seq if last else 0) + 1, t=last.t if last else 0.0,
                              cost_usd=last.cost_usd if last else 0.0, kind="run_failed",
                              data={"message": tail_text[0] if tail_text else "Il processo si è interrotto."}))
            return
        await asyncio.sleep(poll)
        idle += poll
        if idle >= HEARTBEAT_SECONDS:
            idle = 0.0
            yield ": attesa\n\n"


def create_app(settings: UiSettings | None = None) -> FastAPI:
    settings = settings or UiSettings()
    catalog = Catalog(settings.campaign, settings.workspace)
    cache = settings.workspace / ".cache"
    evidence = Evidence(cache)
    spending = Spending(settings.ledger, settings.limits)
    jobs = Jobs(catalog, spending, settings.workspace, settings.campaign)
    app = FastAPI(title="Grafi di manutenzione", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.add_middleware(GZipMiddleware, minimum_size=2048)
    app.state.settings, app.state.catalog = settings, catalog

    def run_dir(manual_id: str, version_id: str) -> Path:
        try:
            return catalog.run_dir(manual_id, version_id)
        except KeyError:
            raise HTTPException(404, "Versione non trovata") from None

    def manual_dir(manual_id: str) -> Path:
        try:
            return catalog.manual_dir(manual_id)
        except KeyError:
            raise HTTPException(404, "Manuale non trovato") from None

    @app.get("/api/manuals")
    def manuals() -> list[dict]:
        rows = []
        for manual in catalog.manuals():
            latest = manual.latest
            rows.append({"id": manual.id, "origin": manual.origin, "machine": manual.machine.model_dump(),
                         "pages": manual.pages, "versions": len(manual.versions),
                         "latest": latest.model_dump() if latest else None})
        return rows

    @app.get("/api/manuals/{manual_id}")
    def manual(manual_id: str) -> dict:
        try:
            return catalog.manual(manual_id).model_dump()
        except KeyError:
            raise HTTPException(404, "Manuale non trovato") from None

    @app.get("/api/manuals/{manual_id}/versions/{version_id}/graph")
    def graph(manual_id: str, version_id: str) -> FileResponse:
        path = run_dir(manual_id, version_id) / "graph.json"
        if not path.exists():
            raise HTTPException(404, "Questa versione non ha un grafo")
        return FileResponse(path, media_type="application/json")

    @app.get("/api/manuals/{manual_id}/versions/{version_id}/report")
    def report(manual_id: str, version_id: str) -> FileResponse:
        path = run_dir(manual_id, version_id) / "report.json"
        if not path.exists():
            raise HTTPException(404, "Questa versione non ha un rapporto")
        return FileResponse(path, media_type="application/json")

    @app.get("/api/manuals/{manual_id}/versions/{version_id}/events")
    async def events(manual_id: str, version_id: str, request: Request,
                     speed: float = Query(4.0, ge=0, le=64), after: int = Query(0, alias="from", ge=0)):
        folder = run_dir(manual_id, version_id)
        after = max(after, int(request.headers.get("last-event-id") or 0))
        version = catalog.find(manual_id, version_id)
        headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
        if version.status == "running":
            return StreamingResponse(tail(folder / "events.jsonl", after, alive=lambda: process_alive(folder)),
                                     media_type="text/event-stream", headers=headers)
        if not version.replay:
            raise HTTPException(409, "Lo stato di questa esecuzione non è su questo computer: niente replay")
        replayed = await asyncio.to_thread(replay_events, folder, manual_id=manual_id, version_id=version_id,
                                           ledger=settings.ledger, cache_dir=cache)
        for event in replayed[:1]:
            event.data["speed"] = speed
        return StreamingResponse(paced(replayed, after, speed), media_type="text/event-stream", headers=headers)

    @app.get("/api/manuals/{manual_id}/versions/{version_id}/questions")
    def questions(manual_id: str, version_id: str) -> dict:
        folder = run_dir(manual_id, version_id)
        is_campaign = not folder.is_relative_to(settings.workspace)
        open_, unverified = open_for_people(folder)
        return {"budget": HUMAN_QUESTION_BUDGET, "editable": not is_campaign, "copy_needed": is_campaign,
                "open": [view.model_dump() for view in question_views(folder, open_)],
                "answered": [],
                "unverified": [view.model_dump() for view in question_views(folder, unverified)]}

    @app.get("/api/manuals/{manual_id}/segments/{segment_id}")
    def segment(manual_id: str, segment_id: str) -> dict:
        try:
            return evidence.segment(manual_dir(manual_id), segment_id)
        except (KeyError, FileNotFoundError):
            raise HTTPException(404, "Segmento non trovato") from None

    @app.get("/api/manuals/{manual_id}/pages/{page}.png")
    def page_image(manual_id: str, page: int, scale: float = Query(2.0, gt=0, le=3)) -> FileResponse:
        try:
            path = evidence.page_png(manual_id, manual_dir(manual_id), page, scale)
        except (KeyError, FileNotFoundError):
            raise HTTPException(404, "Pagina non trovata") from None
        return FileResponse(path, media_type="image/png", headers={"Cache-Control": "max-age=86400"})

    @app.post("/api/uploads")
    async def upload(file: UploadFile = File(...)) -> dict:
        data = await file.read()
        try:
            return await asyncio.to_thread(jobs.save_upload, file.filename or "manual.pdf", data)
        except JobError as error:
            raise HTTPException(422, str(error)) from None

    @app.post("/api/manuals")
    def create_manual(body: MachineIn) -> dict:
        try:
            manual_id = jobs.create_manual(body.upload_id, body.model_dump(exclude={"upload_id"}))
        except JobError as error:
            raise HTTPException(422, str(error)) from None
        return {"id": manual_id}

    @app.post("/api/manuals/{manual_id}/runs")
    def start_run(manual_id: str, body: RunIn) -> dict:
        manual_dir(manual_id)
        try:
            return {"version_id": jobs.start(manual_id, body.reviewers)}
        except JobError as error:
            raise HTTPException(409, str(error)) from None

    @app.post("/api/manuals/{manual_id}/versions/{version_id}/stop")
    def stop_run(manual_id: str, version_id: str) -> dict:
        try:
            jobs.stop(run_dir(manual_id, version_id))
        except JobError as error:
            raise HTTPException(409, str(error)) from None
        return {"stopping": True}

    @app.get("/api/jobs/active")
    def active_job() -> dict:
        folder = jobs.active()
        return {"run": str(folder.relative_to(settings.workspace)) if folder else None}

    @app.get("/api/budget")
    def budget() -> dict:
        return spending.snapshot()

    @app.get("/api/estimate")
    def estimate_run(pages: int = Query(..., ge=1)) -> dict:
        return {**estimate(catalog, pages),
                "note": "Stima dalle due esecuzioni attuali con numero di pagine più vicino."}

    _serve_frontend(app, settings.frontend)
    return app


def _serve_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the built app; every non-API path gets index.html (client-side routes)."""

    index = dist / "index.html"

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(404, "Percorso non trovato")
        candidate = (dist / path).resolve()
        if path and candidate.is_file() and candidate.is_relative_to(dist.resolve()):
            return FileResponse(candidate)
        if index.exists():
            return FileResponse(index)
        raise HTTPException(404, "Frontend non compilato: esegui scripts/ui.py")
