"""Real runs started from the interface: upload, new manual, start, stop.

A run is the command line of the campaign (``scripts/kg_v3.py``) in its own process,
with ``--events`` and a gate preset for the interface. It always writes under
``workspace/``, never under ``campaign/``. Before starting, the estimate of the most
expensive similar run must fit both the spend ceiling and the interface limit; the
ceiling handed to the run is also cut so the interface can never spend past its limit.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from backend.ui.budget import UI_RUN_PREFIX, Spending, estimate
from backend.ui.catalog import Catalog, process_alive

ROOT = Path(__file__).resolve().parents[2]
PRESETS = {"agent": "ui-agent", "agent_human": "ui-interactive", "human": "ui-human"}


class JobError(ValueError):
    """A request the interface must refuse, with a sentence for the person."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Jobs:
    def __init__(self, catalog: Catalog, spending: Spending, workspace: Path, campaign: Path) -> None:
        self.catalog = catalog
        self.spending = spending
        self.workspace = workspace
        self.campaign = campaign
        self.processes: dict[Path, subprocess.Popen] = {}

    # Upload ----------------------------------------------------------------

    def _known_sha(self) -> dict[str, str]:
        found = {}
        for base in (self.campaign, self.workspace):
            for path in base.glob("*/manual.json") if base.exists() else []:
                sha = (json.loads(path.read_text(encoding="utf-8")) or {}).get("sha256")
                if sha and (path.parent / "info.yaml").exists():
                    found.setdefault(sha, path.parent.name)
        return found

    def save_upload(self, file_name: str, data: bytes) -> dict[str, Any]:
        import fitz

        if not data.startswith(b"%PDF"):
            raise JobError("Il file non è un PDF. Scegline un altro.")
        try:
            with fitz.open(stream=data, filetype="pdf") as document:
                pages = document.page_count
        except Exception:
            raise JobError("Il PDF non si apre: potrebbe essere danneggiato. Scegline un altro.") from None
        sha = hashlib.sha256(data).hexdigest()
        target = self.workspace / "uploads" / f"{sha}.pdf"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        (target.with_suffix(".json")).write_text(json.dumps({"file_name": file_name, "pages": pages}),
                                                 encoding="utf-8")
        duplicate = self._known_sha().get(sha)
        machine = None
        if duplicate:
            machine = self.catalog.manual(duplicate).machine.model_dump()
        return {"upload_id": sha, "file_name": file_name, "pages": pages, "size_bytes": len(data),
                "duplicate_of": duplicate, "machine": machine}

    # Manual ------------------------------------------------------------------

    def create_manual(self, upload_id: str, machine: dict[str, str]) -> str:
        if not re.fullmatch(r"[0-9a-f]{64}", upload_id):
            raise JobError("Caricamento sconosciuto: carica di nuovo il PDF.")
        upload = self.workspace / "uploads" / f"{upload_id}.pdf"
        if not upload.exists():
            raise JobError("Caricamento sconosciuto: carica di nuovo il PDF.")
        duplicate = self._known_sha().get(upload_id)
        if duplicate:
            return duplicate  # the same PDF: a new version of that manual
        name = " ".join(str(machine.get("name") or "").split())
        if not name:
            raise JobError("Scrivi il nome della macchina.")
        slug = re.sub(r"[^a-z0-9]+", "_", f"{machine.get('brand', '')} {machine.get('model', '')}".lower()).strip("_")
        slug = slug or re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "manuale"
        manual_id, index = slug, 2
        while (self.campaign / manual_id).exists() or (self.workspace / manual_id).exists():
            manual_id, index = f"{slug}_{index}", index + 1
        folder = self.workspace / manual_id
        folder.mkdir(parents=True)
        info = {"split": "interface", "machine": {
            "name": name, "brand": str(machine.get("brand") or "not_stated"),
            "model": str(machine.get("model") or "not_stated"), "type": str(machine.get("type") or "not_stated")}}
        (folder / "info.yaml").write_text(yaml.safe_dump(info, allow_unicode=True, sort_keys=False), encoding="utf-8")
        shutil.copyfile(upload, folder / "manual.pdf")
        pages = json.loads(upload.with_suffix(".json").read_text(encoding="utf-8"))["pages"]
        (folder / "manual.json").write_text(json.dumps({"sha256": upload_id, "pages": pages}), encoding="utf-8")
        return manual_id

    # Runs ----------------------------------------------------------------------

    def active(self) -> Path | None:
        for run_dir, process in list(self.processes.items()):
            if process.poll() is None:
                return run_dir
            del self.processes[run_dir]
        return None

    def check_spending(self, pages: int) -> dict[str, Any]:
        """Refuse a run whose worst estimate does not fit; return the ceiling to hand it."""

        spent = self.spending.snapshot()
        guess = estimate(self.catalog, pages)
        if not guess["cost_usd"]:
            raise JobError("Non ho esecuzioni passate da cui stimare il costo: avvio rifiutato.")
        worst = float(guess["cost_usd"][1])
        committed, ceiling = spent["committed_usd"] + spent["reserved_usd"], spent["ceiling_usd"]
        left_for_ui = spent["ui_limit_usd"] - spent["ui_spent_usd"]
        if committed + worst >= ceiling:
            raise JobError(f"La stima massima ({worst:.3f} USD) supera il tetto di spesa rimasto "
                           f"({ceiling - committed:.3f} USD).")
        if worst >= left_for_ui:
            raise JobError(f"La stima massima ({worst:.3f} USD) supera quanto resta per l'interfaccia "
                           f"({left_for_ui:.3f} USD).")
        return {"spend_ceiling": round(min(ceiling, committed + left_for_ui), 4), "estimate": guess}

    def start(self, manual_id: str, reviewers: str) -> str:
        if reviewers not in PRESETS:
            raise JobError("Scelta di chi risponde sconosciuta.")
        if self.active() is not None:
            raise JobError("C'è già un'esecuzione in corso: aspetta che finisca o fermala.")
        manual = self.catalog.manual(manual_id)
        allowed = self.check_spending(manual.pages or 1)
        runs = self.workspace / manual_id / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        number = 1 + max((int(match.group(1)) for path in runs.iterdir()
                          if (match := re.fullmatch(r"v3_r(\d+)", path.name))), default=0)
        run_dir = runs / f"v3_r{number}"
        run_dir.mkdir()
        source = self.catalog.manual_dir(manual_id)
        command = [sys.executable, str(ROOT / "scripts" / "kg_v3.py")]
        if source.parent == self.campaign:
            command += ["--manual", manual_id]
        else:
            command += ["--pdf", str(source / "manual.pdf"), "--info", str(source / "info.yaml")]
        command += ["--out", str(run_dir), "--gates", PRESETS[reviewers], "--events",
                    "--spend-ceiling", f"{allowed['spend_ceiling']:.4f}",
                    "--run-id", f"{UI_RUN_PREFIX}{manual_id}_{run_dir.name}"]
        (run_dir / "events.jsonl").touch()
        log = (run_dir / "job.log").open("w", encoding="utf-8")
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        log.close()
        self.processes[run_dir] = process
        (run_dir / "job.json").write_text(json.dumps({
            "pid": process.pid, "started_at": _now(), "reviewers": reviewers, "command": command,
            "spend_ceiling_usd": allowed["spend_ceiling"], "estimate": allowed["estimate"],
        }, indent=1), encoding="utf-8")
        return f"workspace~{run_dir.name}"

    def stop(self, run_dir: Path) -> None:
        process = self.processes.get(run_dir)
        pid = process.pid if process else (json.loads((run_dir / "job.json").read_text()).get("pid")
                                           if (run_dir / "job.json").exists() else None)
        if pid is None or not process_alive(run_dir):
            raise JobError("Questa esecuzione non è in corso.")
        # Like Ctrl+C: the command line records the stop in events.jsonl; saved state stays for a resume.
        os.kill(pid, signal.SIGINT)
