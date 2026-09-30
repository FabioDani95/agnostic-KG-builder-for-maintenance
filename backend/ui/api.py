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

from backend.kg_v3.ontology import load_ontology
from backend.ui.budget import Limits, Spending, estimate
from backend.ui.catalog import Catalog, process_alive
from backend.ui.events import UiEvent
from backend.ui.evidence import Evidence
from backend.ui.jobs import JobError, Jobs, current_units, question_budget
from backend.ui.questions import open_for_people, pending_questions, question_views
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


class AnswerIn(BaseModel):
    option_id: str
    keep: list[int] = []
    text: str = ""


class DecisionIn(BaseModel):
    decision: str


@dataclass
class UiSettings:
    root: Path = ROOT
    campaign: Path = field(default_factory=lambda: ROOT / "campaign")
    workspace: Path = field(default_factory=lambda: Path(os.environ.get("KG_UI_WORKSPACE", ROOT / "workspace")))
    ledger: Path = field(default_factory=lambda: ROOT / "campaign" / "real_call_budget.jsonl")
    frontend: Path = field(default_factory=lambda: ROOT / "frontend" / "dist")
    limits: Limits = field(default_factory=Limits)
    # How long «Applica» and «Approva» wait for the resumed run to start before answering.
    resume_wait_seconds: float = 20.0


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

    position, idle, last = None, 0.0, None
    while True:
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        if position is None:
            # A resumed run appends a new attempt; it reloads the whole state, so it is enough to follow it.
            position = last_attempt(lines)
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


def last_attempt(lines: list[str]) -> int:
    """Index of the last run_started line: where the current attempt of a run begins."""

    starts = [index for index, line in enumerate(lines) if '"kind":"run_started"' in line]
    return starts[-1] if starts else 0


async def wait_for_attempt(path: Path, before: int, seconds: float = 20.0) -> None:
    """Return once the resumed command line has written its first event, so the view follows it."""

    for _ in range(int(seconds / 0.25)):
        lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        if sum('"kind":"run_started"' in line for line in lines) > before:
            return
        await asyncio.sleep(0.25)


def attempts(path: Path) -> int:
    return path.read_text(encoding="utf-8").count('"kind":"run_started"') if path.exists() else 0


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

    @app.get("/api/runs")
    def runs() -> list[dict]:
        """Every version of every manual, newest first: the log of all runs."""
        rows = [{"manual_id": manual.id, "machine": manual.machine.model_dump(), **version.model_dump()}
                for manual in catalog.manuals() for version in manual.versions]
        rows.sort(key=lambda row: row["date"] or "", reverse=True)
        return rows

    @app.get("/api/ontology")
    def ontology() -> dict:
        """The fixed schema every run reads (backend/kg_v3/ontology.py), as the interface shows it."""
        spec = load_ontology()
        return {
            "root": spec.root,
            "nodes": [{"name": name, "description": description,
                       "properties": [{"name": prop, "required": required} for prop, required in spec.properties[name]]}
                      for name, description in spec.node_types.items()],
            "relations": [{"name": item.name, "domain": item.domain, "range": item.range,
                           "description": item.description, "added_by_code": item.domain == spec.root}
                          for item in spec.relations],
        }

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
    def questions(manual_id: str, version_id: str, lang: str = Query("it", pattern="^(it|en)$")) -> dict:
        folder = run_dir(manual_id, version_id)
        is_campaign = not folder.is_relative_to(settings.workspace)
        version = catalog.find(manual_id, version_id)
        if is_campaign or version.status == "running" or not (folder / "state").exists():
            open_, unverified = open_for_people(folder) if (folder / "state").exists() else ([], [])
            answered: list[dict] = []
            unapplied = 0
        else:
            store = jobs.store(folder)
            open_ = store.open_questions()
            published = {question.question_id for question in store.questions}
            pending_all, deferred = pending_questions(folder, budget=10**6)
            unverified = [question for question in pending_all + deferred
                          if question.question_id not in published and question.kind.value != "graph_approval"]
            answered = []
            done = [question for question in store.questions if question.question_id in store.answers]
            for view in question_views(folder, done, lang):
                given = store.answers[view.question_id]
                answered.append({**view.model_dump(), "answer": {"option_id": given.option_id, "text": given.text,
                                                                 "keep": given.edits.get("keep", [])}})
            unapplied = len(store.unapplied())
        awaiting = version.status == "awaiting_approval"
        return {"budget": question_budget(folder), "editable": not is_campaign, "copy_needed": is_campaign,
                "open": [view.model_dump() for view in question_views(folder, open_, lang)],
                "answered": answered, "unapplied": unapplied, "awaiting_approval": awaiting,
                "can_approve": awaiting and not is_campaign and not open_ and not unapplied,
                "unverified": [view.model_dump() for view in question_views(folder, unverified, lang)]}

    @app.post("/api/manuals/{manual_id}/versions/{version_id}/questions/{question_id}/answer")
    async def answer(manual_id: str, version_id: str, question_id: str, body: AnswerIn) -> dict:
        folder = run_dir(manual_id, version_id)
        try:
            if not folder.is_relative_to(settings.workspace):
                # Campaign runs are never written: the first answer works on a copy in workspace/.
                doc = await asyncio.to_thread(evidence.document, manual_dir(manual_id))
                units = await asyncio.to_thread(current_units, doc, folder)
                version_id = jobs.copy_version(manual_id, folder, units)
                folder = run_dir(manual_id, version_id)
            jobs.answer(folder, question_id, body.option_id, body.keep, body.text)
        except JobError as error:
            raise HTTPException(409, str(error)) from None
        store = jobs.store(folder)
        return {"version_id": version_id, "open": len(store.open_questions()), "answered": len(store.answers)}

    @app.post("/api/manuals/{manual_id}/versions/{version_id}/apply")
    async def apply_answers(manual_id: str, version_id: str) -> dict:
        folder = run_dir(manual_id, version_id)
        before = attempts(folder / "events.jsonl")
        try:
            jobs.apply(manual_id, folder)
        except JobError as error:
            raise HTTPException(409, str(error)) from None
        await wait_for_attempt(folder / "events.jsonl", before, settings.resume_wait_seconds)
        return {"version_id": version_id}

    @app.post("/api/manuals/{manual_id}/versions/{version_id}/approve")
    async def approve(manual_id: str, version_id: str, body: DecisionIn) -> dict:
        folder = run_dir(manual_id, version_id)
        before = attempts(folder / "events.jsonl")
        try:
            jobs.approve(manual_id, folder, body.decision)
        except JobError as error:
            raise HTTPException(409, str(error)) from None
        await wait_for_attempt(folder / "events.jsonl", before, settings.resume_wait_seconds)
        return {"version_id": version_id}

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

    @app.post("/api/uploads/{upload_id}/machine")
    async def identify_machine(upload_id: str) -> dict:
        try:
            return await jobs.identify(upload_id)
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

    @app.get("/api/settings")
    def read_settings() -> dict:
        return jobs.preferences.load().public()

    @app.put("/api/settings")
    def write_settings(body: dict) -> dict:
        try:
            return jobs.preferences.save(dict(body)).public()
        except ValueError as error:
            raise HTTPException(422, _first_error(error)) from None

    @app.get("/api/budget")
    def budget() -> dict:
        return spending.snapshot()

    @app.get("/api/estimate")
    def estimate_run(pages: int = Query(..., ge=1)) -> dict:
        return {**estimate(catalog, pages),
                "note": "Stima dalle due esecuzioni attuali con numero di pagine più vicino."}

    _serve_frontend(app, settings.frontend)
    return app


def _first_error(error: ValueError) -> str:
    """One sentence for the person: the message of a refused value, not the whole validation report."""
    errors = getattr(error, "errors", None)
    if callable(errors):
        first = errors()[0]
        return f"Valore non valido per «{'.'.join(str(part) for part in first['loc'])}»: {first['msg']}"
    return str(error)


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
