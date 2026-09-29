"""Manuals and their versions, read from ``campaign/`` and ``workspace/`` without writing.

A manual is a folder with ``info.yaml``; the same ID in both places is one manual. A
version is one run folder ``runs*/v3_rN`` (campaign) or ``runs/<name>`` (workspace)
with a report or at least saved state. The old ``v22`` runs have another format and
are left out.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from backend.ui.questions import open_for_people

WORKSPACE_ITERATION = "workspace"


class Machine(BaseModel):
    name: str
    brand: str = ""
    model: str = ""
    type: str = ""


class Version(BaseModel):
    version_id: str
    origin: str  # campaign | workspace
    iteration: str  # runs_E -> "E", runs -> "", workspace -> "workspace"
    run: str  # v3_r1
    repetition: int | None
    date: str | None
    commit: str
    verified: int
    doubtful: int
    excluded: int
    open_questions: int
    status: str  # approved, awaiting_approval, incomplete, rejected, failed, running
    # Who decided the approval gate: auto (campaign runs), human (the interface button).
    decided_by: str | None = None
    cost_usd: float | None
    seconds: float | None
    pages: int | None
    replay: bool
    copied_from: str | None = None


class Manual(BaseModel):
    id: str
    origin: str  # where its info.yaml lives: campaign | workspace
    machine: Machine
    pages: int | None
    versions: list[Version]

    @property
    def latest(self) -> Version | None:
        return self.versions[0] if self.versions else None


def _read_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat(timespec="seconds")


def _last_event(run_dir: Path) -> str | None:
    path = run_dir / "events.jsonl"
    if not path.exists():
        return None
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return json.loads(lines[-1])["kind"] if lines else None


def process_alive(run_dir: Path) -> bool:
    """The command-line process of a run started from the interface is still running."""

    job = _read_json(run_dir / "job.json")
    if not job or not job.get("pid"):
        return False
    try:
        os.kill(int(job["pid"]), 0)
    except (OSError, ValueError):
        return False
    return True


def _status(run_dir: Path, report: dict[str, Any] | None) -> str:
    last = _last_event(run_dir)
    if last not in ("run_finished", "run_failed") and process_alive(run_dir):
        return "running"
    if report is None or last == "run_failed":
        return "failed"
    return str(report.get("status") or "failed")


def _decided_by(run_dir: Path) -> str | None:
    answers = (_read_json(run_dir / "state" / "gate_approval.json") or {}).get("answers") or []
    return answers[-1]["answered_by"]["kind"] if answers else None


def _date(run_dir: Path) -> str | None:
    """Last recorded answer of the gates, else the date of the report or of the events file.

    Answers come first: a campaign folder copied or restored keeps them, not its file dates.
    """

    stamps = []
    for path in (run_dir / "state").glob("gate_*.json"):
        for answer in (_read_json(path) or {}).get("answers", []):
            if answer.get("answered_at"):
                stamps.append(datetime.fromisoformat(answer["answered_at"].replace("Z", "+00:00")))
    # A run waiting for a person has answered only the map: its report is the better date.
    waiting = (_read_json(run_dir / "report.json") or {}).get("status") == "awaiting_approval"
    if stamps and not waiting:
        return max(stamps).astimezone(timezone.utc).isoformat(timespec="seconds")
    for name in ("report.json", "events.jsonl"):
        if (run_dir / name).exists():
            return _iso((run_dir / name).stat().st_mtime)
    return max(stamps).astimezone(timezone.utc).isoformat(timespec="seconds") if stamps else None


@dataclass
class _Cached:
    stamp: tuple
    version: Version


class Catalog:
    def __init__(self, campaign: Path, workspace: Path) -> None:
        self.campaign = campaign
        self.workspace = workspace
        self._versions: dict[Path, _Cached] = {}

    # Folders ---------------------------------------------------------------

    def _manual_dirs(self) -> dict[str, list[Path]]:
        found: dict[str, list[Path]] = {}
        for base in (self.campaign, self.workspace):
            if not base.exists():
                continue
            for folder in sorted(base.iterdir()):
                if folder.is_dir() and not folder.name.startswith(".") and (
                        (folder / "info.yaml").exists() or (base == self.workspace and (folder / "runs").exists())):
                    found.setdefault(folder.name, []).append(folder)
        return {key: dirs for key, dirs in found.items() if any((d / "info.yaml").exists() for d in dirs)}

    def run_dirs(self, manual_id: str) -> dict[str, tuple[str, Path]]:
        """Version ID -> (origin, folder)."""

        runs: dict[str, tuple[str, Path]] = {}
        campaign = self.campaign / manual_id
        if campaign.exists():
            for folder in sorted(campaign.glob("runs*")):
                for run in sorted(folder.iterdir()) if folder.is_dir() else []:
                    if run.is_dir() and run.name.startswith("v3_") and (
                            (run / "report.json").exists() or (run / "state").exists()):
                        runs[f"{folder.name}~{run.name}"] = ("campaign", run)
        workspace = self.workspace / manual_id / "runs"
        if workspace.exists():
            for run in sorted(workspace.iterdir()):
                if run.is_dir() and ((run / "report.json").exists() or (run / "state").exists()
                                     or (run / "events.jsonl").exists()):
                    runs[f"{WORKSPACE_ITERATION}~{run.name}"] = ("workspace", run)
        return runs

    def run_dir(self, manual_id: str, version_id: str) -> Path:
        found = self.run_dirs(manual_id).get(version_id)
        if found is None:
            raise KeyError(f"{manual_id}/{version_id}")
        return found[1]

    def find(self, manual_id: str, version_id: str) -> Version:
        found = self.run_dirs(manual_id).get(version_id)
        if found is None:
            raise KeyError(f"{manual_id}/{version_id}")
        return self.version(version_id, *found)

    def manual_dir(self, manual_id: str) -> Path:
        """Folder with info.yaml and manual.pdf: the campaign's, else the workspace's."""

        for base in (self.campaign, self.workspace):
            if (base / manual_id / "info.yaml").exists():
                return base / manual_id
        raise KeyError(manual_id)

    # Reading -----------------------------------------------------------------

    def version(self, version_id: str, origin: str, run_dir: Path) -> Version:
        watched = [run_dir / name for name in ("report.json", "events.jsonl", "people.json", "origin.json", "job.json")]
        watched += sorted((run_dir / "state").glob("gate_*.json"))
        # A process that ends changes no file: its liveness is part of the key.
        stamp = (*((path.name, path.stat().st_mtime_ns) for path in watched if path.exists()),
                 process_alive(run_dir))
        cached = self._versions.get(run_dir)
        if cached and cached.stamp == stamp:
            return cached.version
        report = _read_json(run_dir / "report.json")
        tiers = ((report or {}).get("graph") or {}).get("edges_by_tier") or {}
        folder, run = version_id.split("~", 1)
        repetition = int(run.rsplit("_r", 1)[1]) if "_r" in run and run.rsplit("_r", 1)[1].isdigit() else None
        seconds = (report or {}).get("seconds") or {}
        cost = None
        if report and report.get("usage"):
            cost = float(report["usage"].get("estimated_cost_usd") or 0.0)
            cost += float((report.get("agent_usage") or {}).get("estimated_cost_usd") or 0.0)
        copied = (_read_json(run_dir / "origin.json") or {}).get("from")
        version = Version(
            version_id=version_id, origin=origin,
            iteration=folder.removeprefix("runs").removeprefix("_").replace("_", " ") if origin == "campaign"
            else WORKSPACE_ITERATION,
            run=run, repetition=repetition, date=_date(run_dir),
            commit=str(((report or {}).get("provenance") or {}).get("commit") or "")[:7],
            verified=int(tiers.get("green", 0)), doubtful=int(tiers.get("yellow", 0)),
            excluded=int(tiers.get("red", 0)),
            open_questions=len(open_for_people(run_dir)[0]) if (run_dir / "state").exists() else 0,
            status=_status(run_dir, report), decided_by=_decided_by(run_dir), cost_usd=round(cost, 6) if cost is not None else None,
            seconds=seconds.get("end_to_end") or seconds.get("total"), pages=(report or {}).get("pages"),
            replay=(run_dir / "state").exists() or (run_dir / "events.jsonl").exists(),
            copied_from=copied,
        )
        self._versions[run_dir] = _Cached(stamp, version)
        return version

    def manual(self, manual_id: str) -> Manual:
        dirs = self._manual_dirs().get(manual_id)
        if not dirs:
            raise KeyError(manual_id)
        info = yaml.safe_load((self.manual_dir(manual_id) / "info.yaml").read_text(encoding="utf-8")) or {}
        machine = Machine.model_validate(info.get("machine") or {"name": manual_id})
        versions = [self.version(version_id, origin, path)
                    for version_id, (origin, path) in self.run_dirs(manual_id).items()]
        versions.sort(key=lambda item: item.date or "", reverse=True)
        pages = (_read_json(self.manual_dir(manual_id) / "manual.json") or {}).get("pages")
        if pages is None:
            pages = next((item.pages for item in versions if item.pages), None)
        origin = "campaign" if self.manual_dir(manual_id).parent == self.campaign else "workspace"
        return Manual(id=manual_id, origin=origin,
                      machine=machine, pages=pages, versions=versions)

    def manuals(self) -> list[Manual]:
        return [self.manual(manual_id) for manual_id in sorted(self._manual_dirs())]
