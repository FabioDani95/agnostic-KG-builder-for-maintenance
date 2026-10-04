"""Content-bound run state with atomic writes and a single local writer."""

from __future__ import annotations

import fcntl
import hashlib
import importlib.metadata
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from backend.kg_v3.contracts import Answer, Question, ReviewerKind, validate_answer

ROOT = Path(__file__).resolve().parents[2]
STATE_VERSION = "kg-run-state-1"


def canonical(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=lambda obj: obj.model_dump(mode="json") if isinstance(obj, BaseModel) else _unsupported(obj),
    ).encode()


def _unsupported(value):
    raise TypeError(f"Not JSON serializable: {type(value).__name__}")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def stable_id(prefix: str, value: Any) -> str:
    return prefix + "_" + digest(value)[:24]


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: Any):
    atomic_bytes(path, canonical(value) + b"\n")


def atomic_bytes(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def run_lock(workdir: Path | None):
    if workdir is None:
        yield
        return
    workdir.mkdir(parents=True, exist_ok=True)
    with (workdir / ".writer.lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("run directory has another writer") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def source_fingerprints() -> dict[str, str]:
    paths = sorted((ROOT / "backend/kg_v3").glob("*.py"))
    paths += [
        ROOT / p
        for p in (
            "backend/adapters/pdf.py",
            "backend/services/pdf_service.py",
            "backend/services/llm_gateway.py",
            "backend/services/model_pricing.py",
            "backend/services/real_call_budget_ledger.py",
            "backend/services/pdf_ocr_service.py",
            "backend/app_config.py",
            "scripts/kg_v3.py",
            "config.yaml",
            "ontology_schema.JSON",
        )
    ]
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths if p.exists()}


def input_manifest(doc, config, asset_name: str, pdf_path: Path | None, spec) -> dict:
    settings = config.model_dump(mode="json")
    # Reviewer availability and worker count are workflow settings. They do not
    # change extracted facts; gate checkpoints separately bind questions/briefs.
    for key in ("gates", "concurrency", "agent_concurrency", "wait_for_map", "human_question_budget"):
        settings.pop(key, None)
    segments = [s.model_dump(mode="json") for s in doc.segments()]
    basis = {
        "segments": segments,
        "pages": doc.page_count,
        "sections": doc.section_titles,
        "geometry": {
            p: {k: v for k, v in values.items() if not k.startswith("route_")}
            for p, values in doc.page_geometry.items()
        },
    }
    pdf_sha = file_hash(pdf_path) if pdf_path else digest(basis)
    source_hashes = source_fingerprints()
    value = {
        "schema_version": STATE_VERSION,
        "pdf_sha256": pdf_sha,
        "asset_scope_id": config.asset_scope_id or asset_name,
        "document_basis_sha256": digest(basis),
        "config": settings,
        "sources": source_hashes,
        "ontology": {"root": spec.root, "relations": [vars(r) for r in spec.relations]},
        "libraries": {n: importlib.metadata.version(n) for n in ("pydantic", "PyMuPDF", "openai")},
        "parser_base_fingerprint": digest(
            {
                k: v
                for k, v in source_hashes.items()
                if any(t in k for t in ("reader", "source_index", "pdf", "config.yaml"))
            }
        ),
    }
    value["input_fingerprint"] = digest(value)
    value["head"] = git_head(ROOT)
    return value


class RunState:
    def __init__(self, workdir: Path | None, manifest: dict):
        self.workdir = workdir
        self.manifest = manifest
        if workdir is not None:
            path = workdir / "input_manifest.json"
            if path.exists():
                old = json.loads(path.read_text())
                if digest({k: v for k, v in old.items() if k not in {"input_fingerprint", "head"}}) != old.get(
                    "input_fingerprint"
                ):
                    raise ValueError("input manifest checksum mismatch")
                if old.get("input_fingerprint") != manifest["input_fingerprint"]:
                    raise ValueError("incompatible input/PDF/prompt/model/parser/config; use a new run directory")
                self.manifest = old  # never relabel saved responses with today's HEAD
            elif (workdir / "state").exists() and any((workdir / "state").glob("*.json")):
                raise ValueError("legacy run without manifest is read-only; use a new run directory")
            else:
                atomic_json(path, manifest)

    def fingerprint(self, stage: str, dependencies: Any = None):
        return digest({"input": self.manifest["input_fingerprint"], "stage": stage, "dependencies": dependencies})

    def load(self, stage: str, dependencies: Any = None):
        if self.workdir is None:
            return None
        path = self.workdir / "state" / (stage + ".json")
        if not path.exists():
            return None
        envelope_path = self.workdir / "state_envelopes" / (stage + ".json")
        if not envelope_path.exists():
            raise ValueError(f"{stage}: legacy/unversioned state is read-only")
        value = json.loads(envelope_path.read_text())
        if digest({k: v for k, v in value.items() if k != "envelope_sha256"}) != value.get("envelope_sha256"):
            raise ValueError(f"{stage}: envelope checksum mismatch")
        if value.get("schema_version") != STATE_VERSION:
            raise ValueError(f"{stage}: legacy/unversioned state is read-only")
        if value.get("input_fingerprint") != self.fingerprint(stage, dependencies):
            raise ValueError(f"{stage}: incompatible checkpoint dependencies")
        payload = json.loads(path.read_text())
        if digest(payload) != value.get("payload_sha256") or digest(value["payload"]) != value.get("payload_sha256"):
            # The historical UI writes a human approval into this raw file.
            # Import only that additive answer; the question and prior answers
            # must still match the immutable checkpoint exactly.
            prior = value["payload"]
            if stage == "gate_approval" and self._human_approval_update(prior, payload):
                self.save(stage, payload, dependencies)
                return payload
            raise ValueError(f"{stage}: checkpoint checksum mismatch")
        return value["payload"]

    @staticmethod
    def _human_approval_update(prior, updated):
        if updated.get("questions") != prior.get("questions"):
            return False
        old = prior.get("answers", [])
        new = updated.get("answers", [])
        if new[: len(old)] != old or len(new) != len(old) + 1:
            return False
        try:
            answer = Answer.model_validate(new[-1])
            question = next(
                Question.model_validate(q)
                for q in prior["questions"]
                if q["question_id"] == answer.question_id and q["question_id"] in prior["pending"]
            )
            if answer.answered_by.kind is not ReviewerKind.HUMAN:
                return False
            validate_answer(question, answer)
            return updated.get("pending") == [q for q in prior["pending"] if q != answer.question_id]
        except (ValueError, StopIteration):
            return False

    def load_index(self):
        if self.workdir is None or not (self.workdir / "source_index.json").exists():
            return None
        payload = json.loads((self.workdir / "source_index.json").read_text())
        revisions = self.workdir / "source_index_revisions"
        valid = False
        for path in revisions.glob("*.json"):
            revision = json.loads(path.read_text())
            identity = {k: v for k, v in revision.items() if k != "revision_id"}
            if stable_id("revision", identity) != revision.get("revision_id"):
                raise ValueError("source index revision checksum mismatch")
            if digest(revision["snapshot"]) != revision["content_sha256"]:
                raise ValueError("source index snapshot checksum mismatch")
            valid |= revision["content_sha256"] == digest(payload)
        if not valid:
            raise ValueError("source index has no matching immutable revision")
        return payload

    def save(self, stage: str, payload: Any, dependencies: Any = None, *, status="complete", parents=(), calls=()):
        if isinstance(payload, BaseModel):
            payload = payload.model_dump(mode="json")
        if self.workdir is not None:
            atomic_json(self.workdir / "state" / (stage + ".json"), payload)
            envelope = {
                "stage": stage,
                "schema_version": STATE_VERSION,
                "status": status,
                "input_fingerprint": self.fingerprint(stage, dependencies),
                "payload_sha256": digest(payload),
                "parent_refs": list(parents),
                "call_refs": list(calls),
                "payload": payload,
            }
            envelope["envelope_sha256"] = digest(envelope)
            atomic_json(self.workdir / "state_envelopes" / (stage + ".json"), envelope)

    def call_refs(self, stage):
        if self.workdir is None:
            return []
        self.load(stage)
        path = self.workdir / "state_envelopes" / (stage + ".json")
        return json.loads(path.read_text()).get("call_refs", []) if path.exists() else []

    def revise_index(self, index, delta: dict):
        if self.workdir is None:
            return
        current = self.workdir / "source_index.json"
        previous = json.loads(current.read_text()) if current.exists() else None
        payload = index.model_dump(mode="json")
        if previous == payload:
            return
        revision = {
            "parent": digest(previous) if previous else None,
            "content_sha256": digest(payload),
            "delta": delta,
            "snapshot": payload,
        }
        revision_id = stable_id("revision", revision)
        revision["revision_id"] = revision_id
        atomic_json(self.workdir / "source_index_revisions" / (revision_id + ".json"), revision)
        atomic_json(current, payload)


def git_head(root):
    gitdir = root / ".git"
    if gitdir.is_file():
        gitdir = (root / gitdir.read_text().strip().removeprefix("gitdir: ")).resolve()
    if not (gitdir / "HEAD").exists():
        return "UNKNOWN_SOURCE_CHECKOUT"
    head = (gitdir / "HEAD").read_text().strip()
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    common = gitdir
    if (gitdir / "commondir").exists():
        common = (gitdir / (gitdir / "commondir").read_text().strip()).resolve()
    path = common / ref
    if path.exists():
        return path.read_text().strip()
    packed = common / "packed-refs"
    if packed.exists():
        for line in packed.read_text().splitlines():
            if line.endswith(" " + ref):
                return line.split()[0]
    return "UNKNOWN_REF"
