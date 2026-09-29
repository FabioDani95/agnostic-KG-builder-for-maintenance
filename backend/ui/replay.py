"""Replay a finished run: rebuild the raw pipeline events from its saved state, with their times.

Times come from the modification dates of the state files. When they are missing or
inconsistent with ``report.json`` (order different from the pipeline's, or a span far
from the reported duration), they are rebuilt from the per-step seconds of the report.
The cost over time comes from the budget ledger calls of the run; without them the
reported total is spread over the run and marked as estimated.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.ui.events import EventTranslator, UiEvent

# Order in which Pipeline.run saves its state, and the step that ends with each file.
_ORDER = (
    ("map", "map"), ("gate_map", "gate_map"), ("units", None), ("extract_", "extract"),
    ("checked_", "check"), ("omissions_", "omissions"), ("merge_plan_", "merge"),
    ("rechecked_", "split_recheck"), ("navigation_", "navigation"), ("visual_", "visual"),
    ("gate_doubts", "gate_doubts"), ("recovery_", "split_recheck"), ("gate_recovery", "gate_recovery"),
    ("gate_approval", "gate_approval"),
)


@dataclass
class StateFile:
    name: str
    rank: int
    step: str | None
    mtime: float
    path: Path
    t: float = 0.0


def _rank(name: str) -> tuple[int, str | None] | None:
    for rank, (prefix, step) in enumerate(_ORDER):
        if name == prefix or (prefix.endswith("_") and name.startswith(prefix)):
            return rank, step
    return None


def state_files(run_dir: Path) -> list[StateFile]:
    files = []
    for path in (run_dir / "state").glob("*.json"):
        found = _rank(path.stem)
        if found is not None:
            files.append(StateFile(path.stem, found[0], found[1], path.stat().st_mtime, path))
    return sorted(files, key=lambda item: (item.rank, item.mtime))


def _seconds(report: dict[str, Any]) -> dict[str, float]:
    return {key: float(value) for key, value in (report.get("seconds") or {}).items()}


def _dated(files: list[StateFile], report: dict[str, Any]) -> float | None:
    """Epoch of the run start from the file dates, or None when the dates cannot be trusted."""

    if not files or any(later.mtime < earlier.mtime for earlier, later in zip(files, files[1:])):
        return None
    seconds = _seconds(report)
    before_map = seconds.get("pdf_read", 0.0) + seconds.get("map", 0.0) + seconds.get("scan", 0.0)
    span = files[-1].mtime - files[0].mtime + before_map
    total = seconds.get("end_to_end") or seconds.get("total") or 0.0
    if total and not (0.3 * total <= span <= max(2 * total, total + 120)):
        return None
    return files[0].mtime - before_map


def _synthetic(files: list[StateFile], report: dict[str, Any]) -> None:
    seconds = _seconds(report)
    extracts = [item for item in files if item.step == "extract"]
    share = {
        "map": seconds.get("map", 1.0) + seconds.get("scan", 0.0),
        "extract": seconds.get("extract", 1.0) / max(1, len(extracts)),
        # Two rechecks share one timing; the second also reduces actions.
        "split_recheck": seconds.get("split_recheck", 1.0) / 2,
    }
    clock = seconds.get("pdf_read", 0.0)
    for item in files:
        clock += 0.0 if item.step is None else share.get(item.step, seconds.get(item.step, 1.0))
        if item.name.startswith("recovery_"):
            clock += seconds.get("action_reduction", 0.0)
        item.t = round(clock, 3)


def timeline(run_dir: Path) -> tuple[list[tuple[float, str, dict[str, Any]]], float | None]:
    """Raw events of a finished run with their times, and the start epoch when dates are real."""

    report = _read(run_dir / "report.json") or {}
    files = state_files(run_dir)
    start = _dated(files, report)
    if start is None:
        _synthetic(files, report)
    else:
        for item in files:
            item.t = round(item.mtime - start, 3)
    pdf_read = _seconds(report).get("pdf_read", 0.0)
    raw: list[tuple[float, str, dict[str, Any]]] = [
        (0.0, "step_started", {"step": "pdf_read"}), (pdf_read, "step_finished", {"step": "pdf_read"}),
    ]
    previous_t, previous_step = pdf_read, "pdf_read"
    for item in files:
        if item.step and item.step != previous_step:
            raw.append((previous_t, "step_started", {"step": item.step}))
            previous_step = item.step
        raw.append((item.t, "state_saved", {"name": item.name, "value": _read(item.path)}))
        previous_t = item.t
    return raw, start


def _read(path: Path) -> Any | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


# Cost ----------------------------------------------------------------------


def run_id_of(run_dir: Path) -> str | None:
    for path in sorted((run_dir / "provider_responses").glob("*.json"))[:5]:
        run_id = (_read(path) or {}).get("run_id")
        if run_id:
            return str(run_id)
    return None


def ledger_costs(run_id: str, ledger: Path, cache_dir: Path | None = None) -> list[tuple[float, float]]:
    """(epoch, charged USD) of every finalized call of a run, read once and cached."""

    from datetime import datetime

    cache = cache_dir / f"cost_{run_id}.json" if cache_dir else None
    if cache and cache.exists():
        return [tuple(item) for item in json.loads(cache.read_text(encoding="utf-8"))]
    points = []
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if run_id not in line or '"call_finalized"' not in line:
                continue
            entry = json.loads(line)
            if not str(entry.get("call_id", "")).startswith(f"{run_id}:"):
                continue
            stamp = datetime.fromisoformat(entry["timestamp"]).timestamp()
            points.append((stamp, float(entry.get("charged_cost_usd") or 0.0)))
    points.sort()
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(points), encoding="utf-8")
    return points


def _total_cost(report: dict[str, Any]) -> float:
    total = float((report.get("usage") or {}).get("estimated_cost_usd") or 0.0)
    return total + float((report.get("agent_usage") or {}).get("estimated_cost_usd") or 0.0)


# Replay ----------------------------------------------------------------------


def open_questions_count(run_dir: Path) -> int:
    path = run_dir / "questions_for_people.txt"
    if not path.exists():
        return 0
    return sum(line.startswith("Question ") for line in path.read_text(encoding="utf-8").splitlines())


def replay_events(run_dir: Path, *, manual_id: str, version_id: str, ledger: Path | None = None,
                  cache_dir: Path | None = None) -> list[UiEvent]:
    """Interface events of a finished run, exactly as a live view would have received them."""

    saved = run_dir / "events.jsonl"
    if saved.exists():
        return [UiEvent.model_validate_json(line) for line in saved.read_text(encoding="utf-8").splitlines() if line]
    report = _read(run_dir / "report.json") or {}
    raw, start = timeline(run_dir)
    end = raw[-1][0] if raw else 0.0
    costs: list[tuple[float, float]] = []
    run_id = run_id_of(run_dir)
    if start is not None and ledger is not None and ledger.exists() and run_id:
        running = 0.0
        for stamp, charged in ledger_costs(run_id, ledger, cache_dir):
            running += charged
            costs.append((stamp - start, running))
    estimated = not costs
    total = _total_cost(report)

    def cost_at(t: float) -> float:
        if estimated:
            return total * min(1.0, t / end) if end else total
        return max((cost for when, cost in costs if when <= t), default=0.0)

    translator = EventTranslator()
    events = translator.feed("run_started", {"manual_id": manual_id, "version_id": version_id, "mode": "replay",
                                             "pages": report.get("pages")}, 0.0)
    events[0].data["cost_estimated"] = estimated
    for t, kind, data in raw:
        events += translator.feed(kind, {**data, "cost_usd": cost_at(t)}, t)
    graph = _read(run_dir / "graph.json")
    if graph is not None:
        final_cost = costs[-1][1] if costs else total
        events += translator.feed("run_finished", {"graph": graph, "status": report.get("status"),
                                                   "open_questions": open_questions_count(run_dir),
                                                   "cost_usd": final_cost}, end)
    return events
