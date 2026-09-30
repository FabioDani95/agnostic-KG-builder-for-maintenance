"""Real runs started from the interface: upload, new manual, start, stop.

A run is the command line of the campaign (``scripts/kg_v3.py``) in its own process,
with ``--events`` and a gate preset for the interface. It always writes under
``workspace/``, never under ``campaign/``. Before starting, the estimate of the most
expensive similar run must fit both the spend ceiling and the interface limit; the
ceiling handed to the run is also cut so the interface can never spend past its limit.
"""

from __future__ import annotations

import asyncio
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

from backend.kg_v3.contracts import Answer, QuestionKind, ReviewerIdentity, ReviewerKind, validate_answer
from backend.ui.budget import UI_RUN_PREFIX, Spending, estimate
from backend.ui.catalog import Catalog, process_alive
from backend.ui.questions import HUMAN_QUESTION_BUDGET, open_for_people
from backend.ui.store import STORE_NAME, FileQuestionStore

ROOT = Path(__file__).resolve().parents[2]
PRESETS = {"agent": "ui-agent", "agent_human": "ui-interactive", "human": "ui-human"}
PERSON = ReviewerIdentity(kind=ReviewerKind.HUMAN, name="operator")
# A resume should make no call; this is the most it may spend if the saved state falls short.
RESUME_ALLOWANCE_USD = 0.05
# Reading the machine from the first pages: one small call, far below a cent; this is its cap.
IDENTIFY_ALLOWANCE_USD = 0.01
IDENTIFY_TIMEOUT_SECONDS = 90
# Model settings a copied campaign run must keep when it resumes.
MODEL_FLAGS = {"model": "--model", "reasoning_effort": "--reasoning", "reads": "--reads",
               "agent_model": "--agent-model", "agent_reasoning_effort": "--agent-reasoning"}


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

    def identify_command(self, pdf: Path, ceiling: float) -> list[str]:
        limits = self.spending.limits
        return [sys.executable, "-m", "backend.ui.identify", "--pdf", str(pdf), "--ledger", str(self.spending.ledger),
                "--budget", f"{limits.budget_usd:g}", "--run-id", f"{UI_RUN_PREFIX}identify_{pdf.stem[:12]}",
                "--spend-ceiling", f"{ceiling:.4f}"]

    async def identify(self, upload_id: str) -> dict[str, Any]:
        """Machine fields read from the first pages by a small model; kept next to the upload."""

        if not re.fullmatch(r"[0-9a-f]{64}", upload_id):
            raise JobError("Caricamento sconosciuto: carica di nuovo il PDF.")
        pdf = self.workspace / "uploads" / f"{upload_id}.pdf"
        if not pdf.exists():
            raise JobError("Caricamento sconosciuto: carica di nuovo il PDF.")
        saved = pdf.with_suffix(".machine.json")
        if saved.exists():
            return {**json.loads(saved.read_text(encoding="utf-8")), "cached": True}
        spent = self.spending.snapshot()
        used = spent["committed_usd"] + spent["reserved_usd"]
        room = min(spent["ceiling_usd"] - used, spent["ui_limit_usd"] - spent["ui_spent_usd"])
        if room <= 0:
            raise JobError("Non c'è più spesa possibile per leggere i dati: scrivili tu.")
        process = await asyncio.create_subprocess_exec(
            *self.identify_command(pdf, used + min(IDENTIFY_ALLOWANCE_USD, room)), cwd=ROOT,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        try:
            out, err = await asyncio.wait_for(process.communicate(), timeout=IDENTIFY_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            process.kill()
            raise JobError("La lettura dei dati ci mette troppo: scrivili tu.") from None
        if process.returncode != 0:
            detail = err.decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
            raise JobError(f"Non riesco a leggere i dati della macchina ({detail[0][:160]}): scrivili tu.")
        result = json.loads(out.decode("utf-8").strip().splitlines()[-1])
        saved.write_text(json.dumps(result), encoding="utf-8")
        return {**result, "cached": False}

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
        self._launch(manual_id, run_dir, reviewers, allowed["spend_ceiling"], {"estimate": allowed["estimate"]})
        return f"workspace~{run_dir.name}"

    def _command(self, manual_id: str, run_dir: Path, reviewers: str, ceiling: float,
                 model: dict[str, Any] | None = None) -> list[str]:
        source = self.catalog.manual_dir(manual_id)
        command = [sys.executable, str(ROOT / "scripts" / "kg_v3.py")]
        if source.parent == self.campaign:
            command += ["--manual", manual_id]
        else:
            command += ["--pdf", str(source / "manual.pdf"), "--info", str(source / "info.yaml")]
        for key, flag in MODEL_FLAGS.items():
            if model and model.get(key) is not None:
                command += [flag, str(model[key])]
        return command + ["--out", str(run_dir), "--gates", PRESETS[reviewers], "--events", "--human-store",
                          "--spend-ceiling", f"{ceiling:.4f}", "--run-id", f"{UI_RUN_PREFIX}{manual_id}_{run_dir.name}"]

    def _launch(self, manual_id: str, run_dir: Path, reviewers: str, ceiling: float, extra: dict[str, Any]) -> None:
        job = json.loads((run_dir / "job.json").read_text(encoding="utf-8")) if (run_dir / "job.json").exists() else {}
        model = job.get("model")
        command = self._command(manual_id, run_dir, reviewers, ceiling, model)
        (run_dir / "events.jsonl").touch()
        with (run_dir / "job.log").open("a", encoding="utf-8") as log:
            process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        self.processes[run_dir] = process
        history = [*job.get("history", []), {"started_at": _now(), "command": command}]
        (run_dir / "job.json").write_text(json.dumps({
            **job, **extra, "pid": process.pid, "started_at": _now(), "reviewers": reviewers, "model": model,
            "command": command, "spend_ceiling_usd": ceiling, "history": history,
        }, indent=1), encoding="utf-8")

    def stop(self, run_dir: Path) -> None:
        process = self.processes.get(run_dir)
        pid = process.pid if process else (json.loads((run_dir / "job.json").read_text()).get("pid")
                                           if (run_dir / "job.json").exists() else None)
        if pid is None or not process_alive(run_dir):
            raise JobError("Questa esecuzione non è in corso.")
        # Like Ctrl+C: the command line records the stop in events.jsonl; saved state stays for a resume.
        os.kill(pid, signal.SIGINT)

    # Answers ---------------------------------------------------------------------

    def store(self, run_dir: Path) -> FileQuestionStore:
        """The run's store; a run that never had one gets the questions it offered to people."""

        store = FileQuestionStore(run_dir / STORE_NAME, budget=HUMAN_QUESTION_BUDGET)
        if not (run_dir / STORE_NAME).exists():
            store.publish(open_for_people(run_dir)[0])
        return store

    def copy_version(self, manual_id: str, run_dir: Path, units_now: list[str]) -> str:
        """Copy a campaign version into workspace/ so a person can answer; the original never changes."""

        saved = json.loads((run_dir / "state" / "units.json").read_text(encoding="utf-8"))
        if [unit["unit_id"] for unit in saved] != units_now:
            raise JobError("Questa versione è stata prodotta da un codice diverso: per rispondere serve una nuova "
                           "esecuzione.")
        runs = self.workspace / manual_id / "runs"
        runs.mkdir(parents=True, exist_ok=True)
        number = 1 + max((int(match.group(1)) for path in runs.iterdir()
                          if (match := re.fullmatch(r"risposte-(\d+)", path.name))), default=0)
        target = runs / f"risposte-{number}"
        shutil.copytree(run_dir / "state", target / "state")
        # In the interface the approval is the person's button: an automatic approval of the campaign
        # does not come along (the pipeline would read it even after the graph changed).
        approval = target / "state" / "gate_approval.json"
        if approval.exists():
            record = json.loads(approval.read_text(encoding="utf-8"))
            record["answers"] = [answer for answer in record.get("answers", [])
                                 if answer["answered_by"]["kind"] == ReviewerKind.HUMAN.value]
            answered = {answer["question_id"] for answer in record["answers"]}
            record["pending"] = [question["question_id"] for question in record.get("questions", [])
                                 if question["question_id"] not in answered]
            approval.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        for name in ("graph.json", "report.json", "questions_for_people.txt"):
            if (run_dir / name).exists():
                shutil.copy2(run_dir / name, target / name)
        report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
        config = (report.get("provenance") or {}).get("config") or {}
        (target / "origin.json").write_text(json.dumps({
            "from": str(run_dir.relative_to(ROOT)) if run_dir.is_relative_to(ROOT) else str(run_dir),
            "copied_at": _now(), "commit_of_original": (report.get("provenance") or {}).get("commit"),
        }, indent=1), encoding="utf-8")
        (target / "job.json").write_text(json.dumps({
            "reviewers": "agent_human", "model": {key: config.get(key) for key in MODEL_FLAGS},
        }, indent=1), encoding="utf-8")
        self.store(target)
        return f"workspace~{target.name}"

    def answer(self, run_dir: Path, question_id: str, option_id: str, keep: list[int], text: str) -> None:
        if process_alive(run_dir):
            raise JobError("L'esecuzione è in corso: rispondi quando è finita.")
        store = self.store(run_dir)
        edits = {"keep": sorted(set(keep))} if option_id == "correct" and keep else {}
        answer = Answer(question_id=question_id, option_id=option_id, text=text.strip(), edits=edits,
                        answered_by=PERSON)
        try:
            store.submit(answer)
        except KeyError:
            raise JobError("Questa domanda non è tra quelle per te.") from None
        except ValueError as error:
            raise JobError(f"Risposta non valida: {error}") from None

    def _resume_ceiling(self) -> float:
        """Checked before anything is written: a resume needs no other run and a little room to spend."""

        if self.active() is not None:
            raise JobError("C'è già un'esecuzione in corso: aspetta che finisca.")
        spent = self.spending.snapshot()
        committed = spent["committed_usd"] + spent["reserved_usd"]
        left_for_ui = spent["ui_limit_usd"] - spent["ui_spent_usd"]
        ceiling = min(spent["ceiling_usd"], committed + min(RESUME_ALLOWANCE_USD, left_for_ui))
        if ceiling <= committed:
            raise JobError("Non resta spesa per riprendere l'esecuzione.")
        return round(ceiling, 4)

    def _resume(self, manual_id: str, run_dir: Path, ceiling: float) -> None:
        job = json.loads((run_dir / "job.json").read_text(encoding="utf-8")) if (run_dir / "job.json").exists() else {}
        self._launch(manual_id, run_dir, job.get("reviewers") or "agent_human", ceiling, {})

    def apply(self, manual_id: str, run_dir: Path) -> None:
        store = self.store(run_dir)
        if store.open_questions():
            raise JobError("Rispondi prima a tutte le domande.")
        if not store.unapplied():
            raise JobError("Non ci sono risposte nuove da applicare.")
        ceiling = self._resume_ceiling()
        store.mark_applied()
        self._resume(manual_id, run_dir, ceiling)

    def approve(self, manual_id: str, run_dir: Path, decision: str) -> None:
        if decision not in ("approve", "reject"):
            raise JobError("Decisione sconosciuta.")
        store = self.store(run_dir)
        if store.open_questions():
            raise JobError(f"Rispondi prima alle {len(store.open_questions())} domande.")
        if store.unapplied():
            raise JobError("Applica prima le risposte date.")
        path = run_dir / "state" / "gate_approval.json"
        record = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        from backend.kg_v3.contracts import Question

        question = next((Question.model_validate(item) for item in reversed(record.get("questions", []))
                         if item["kind"] == QuestionKind.GRAPH_APPROVAL.value
                         and item["question_id"] in record.get("pending", [])), None)
        if question is None:
            raise JobError("Questa versione non aspetta un'approvazione.")
        answer = Answer(question_id=question.question_id, option_id=decision, answered_by=PERSON)
        validate_answer(question, answer)
        ceiling = self._resume_ceiling()
        record["answers"] = [*record.get("answers", []), answer.model_dump(mode="json")]
        record["pending"] = [key for key in record.get("pending", []) if key != question.question_id]
        path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
        self._resume(manual_id, run_dir, ceiling)


def current_units(doc, run_dir: Path) -> list[str]:
    """Reading units the current code builds from the run's saved map and map answers."""

    from backend.kg_v3.contracts import DocumentMap
    from backend.kg_v3.mapper import apply_map_answer, build_units
    from backend.kg_v3.run import RunConfig

    state = run_dir / "state"
    page_map = DocumentMap.model_validate(json.loads((state / "map.json").read_text(encoding="utf-8")))
    record = json.loads((state / "gate_map.json").read_text(encoding="utf-8")) if (state / "gate_map.json").exists() else {}
    for answer in record.get("answers", []):
        if answer.get("option_id") == "correct":
            page_map = apply_map_answer(page_map, answer.get("edits") or {})
    report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
    config = RunConfig(**((report.get("provenance") or {}).get("config") or {}))
    return [unit.unit_id for unit in build_units(doc, page_map, max_chars=config.unit_max_chars)]
