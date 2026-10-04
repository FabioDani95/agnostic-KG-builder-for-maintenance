"""Preview without persistence; append-only, idempotent acceptance under a manual lock."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import threading
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from backend.ui.catalog import Catalog, process_alive
from backend.ui.evidence import Evidence
from backend.ui.graph_document import (
    AcceptRevision,
    EditError,
    EditInput,
    apply_operations,
    digest,
    graph_diff,
    recompute,
    schema,
    with_occurrence_ids,
)
from backend.ui.graph_validation import metrics, validate
from backend.ui.locks import manual_lock
from backend.ui.questions import open_for_people
from backend.ui.store import FileQuestionStore


class RevisionError(EditError):
    def __init__(self, code: str, status: int = 409):
        super().__init__(code)
        self.status = status


def _json(path: Path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def file_hash(path: Path) -> str | None:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def capabilities(folder: Path, revision=False) -> dict:
    reason = None
    try:
        with_occurrence_ids(_json(folder / "graph.json", {}))
    except (EditError, ValueError, KeyError, TypeError):
        reason = "GRAPH_UNAVAILABLE"
    if not revision and process_alive(folder):
        reason = "PROCESS_RUNNING"
    elif not revision and FileQuestionStore(folder / "people.json").unapplied():
        reason = "UNAPPLIED_ANSWERS"
    return {
        "can_edit": reason is None,
        "edit_reason": reason,
        "can_approve": not revision,
        "can_replay": not revision and ((folder / "state").exists() or (folder / "events.jsonl").exists()),
        "can_resume": not revision,
    }


class Revisions:
    def __init__(self, catalog: Catalog, evidence: Evidence):
        self.catalog, self.evidence = catalog, evidence
        self._active: Counter[tuple[str, str]] = Counter()
        self._active_lock = threading.Lock()

    def source(self, manual_id: str, folder: Path, graph: dict) -> tuple[dict, dict, Path]:
        revision = (folder / "revision.json").exists()
        source_dir = folder if revision else self.catalog.manual_dir(manual_id)
        pdf = source_dir / ("source.pdf" if revision else "manual.pdf")
        embedded = {e["segment_id"]: e for n in graph["nodes"] for e in n.get("evidence", [])}
        embedded.update(
            {
                e["segment_id"]: e
                for edge in graph["edges"]
                for o in edge.get("occurrences", [])
                for e in o.get("evidence", [])
            }
        )
        index = _json(folder / "source-segments.json", {}) if revision else {}
        verified = revision and bool(index)
        if not revision and pdf.exists():
            try:
                candidate = self.evidence.index(source_dir)
                verified = bool(embedded) and all(
                    s in candidate and all(candidate[s].get(k) == e.get(k) for k in ("text", "page", "bbox"))
                    for s, e in embedded.items()
                )
                if verified:
                    index = candidate
            except (ValueError, KeyError, FileNotFoundError):
                verified = False
        pdf_hash = self.evidence.pdf_hash(pdf)
        meta = _json(folder / "revision.json", {})
        identity = {
            "pdf_hash": pdf_hash,
            "embedded_hash": digest(embedded),
            "index_hash": digest(index),
            "segments_available": verified,
            "pdf_available": pdf_hash is not None
            and (verified if not revision else meta.get("source_pdf_verified", True)),
            "historical_source_hash": meta.get("source_document_hash"),
        }
        return identity, index if verified else embedded, pdf

    def context(self, manual_id: str, version_id: str) -> dict:
        folder = self.catalog.version_dir(manual_id, version_id)
        raw_bytes = (folder / "graph.json").read_bytes() if (folder / "graph.json").exists() else b"{}"
        try:
            raw = json.loads(raw_bytes)
        except ValueError:
            raise RevisionError("GRAPH_UNAVAILABLE", 422) from None
        try:
            graph = with_occurrence_ids(raw)
        except (EditError, TypeError, KeyError, ValueError):
            raise RevisionError("GRAPH_UNAVAILABLE", 422) from None
        ontology = _json(folder / "ontology.json") or schema()
        recompute(graph, ontology)
        source, segments, pdf = self.source(manual_id, folder, graph)
        revision = (folder / "revision.json").exists()
        if revision:
            review = _json(folder / "source-review.json", {})
        else:
            gates = {p.name: _json(p) for p in sorted((folder / "state").glob("gate_*.json"))}
            people = _json(folder / "people.json", {})
            open_, unverified = open_for_people(folder) if (folder / "state").exists() else ([], [])
            review = {
                "version_id": version_id,
                "gates": gates,
                "people": people,
                "questions": [q.model_dump(mode="json") for q in open_ + unverified],
            }
        return {
            "graph": graph,
            "raw": raw,
            "raw_bytes": raw_bytes,
            "folder": folder,
            "pdf": pdf,
            "segments": segments,
            "ontology": ontology,
            "source": source,
            "source_review": review,
            "capabilities": capabilities(folder, revision),
            "preconditions": {
                "base_hash": digest(raw),
                "ontology_hash": digest(ontology),
                "source_token": digest(source),
                "source_review_hash": digest(review),
            },
        }

    def editor(self, manual_id: str, version_id: str) -> dict:
        context = self.context(manual_id, version_id)
        return {
            k: context[k] for k in ("graph", "ontology", "source", "source_review", "capabilities", "preconditions")
        }

    def preview(self, manual_id: str, version_id: str, body: EditInput, context=None) -> tuple[dict, dict, dict]:
        c = context or self.context(manual_id, version_id)
        if c["preconditions"] != body.preconditions.model_dump():
            raise RevisionError("BASE_CHANGED")
        if not c["capabilities"]["can_edit"]:
            raise RevisionError(c["capabilities"]["edit_reason"])
        graph = apply_operations(c["graph"], body.operations, c["ontology"], c["segments"])
        diff = graph_diff(c["graph"], graph)
        has_changes = any(diff[g][k] for g in diff for k in diff[g])
        issues = validate(graph, c["graph"], c["ontology"])
        for q in c["source_review"].get("questions", []):
            issues.append(
                {
                    "id": "source_" + q["question_id"],
                    "code": "SOURCE_QUESTION",
                    "severity": "warning",
                    "target": {"kind": "graph"},
                    "introduced": False,
                    "message_key": "SOURCE_QUESTION",
                    "message_params": {"question_id": q["question_id"]},
                }
            )
        preview = {
            "draft_generation": body.draft_generation,
            "has_changes": has_changes,
            "can_accept": not any(i["severity"] == "error" for i in issues),
            "diff": diff,
            "issues": issues,
            "metrics": metrics(graph, c["ontology"]),
            "required_acknowledgements": [
                i["id"] for i in issues if i["code"] in ("UNVERIFIED_CONTENT", "NO_EVIDENCE", "SOURCE_QUESTION")
            ],
        }
        preview["preview_hash"] = digest(
            {"graph": graph, "diff": diff, "issues": issues, "context": c["preconditions"]}
        )
        preview["graph"] = graph
        return preview, graph, c

    def request(self, manual_id: str, request_id: str) -> dict:
        for version_id, (_, folder) in self.catalog.revision_dirs(manual_id).items():
            meta = _json(folder / "revision.json")
            if meta["request_id"] == request_id:
                return {"status": "saved", "result": self.created(manual_id, version_id, meta)}
        with self._active_lock:
            active = self._active[(manual_id, request_id)] > 0
        return {"status": "in_progress" if active else "not_found"}

    def created(self, manual_id: str, version_id: str, meta: dict) -> dict:
        return {
            "version": self.catalog.find(manual_id, version_id).model_dump(),
            "parent_version_id": meta["parent_version_id"],
            "graph_hash": meta["graph_hash"],
            "request_id": meta["request_id"],
            "id_map": meta["id_map"],
        }

    def accept(self, manual_id: str, version_id: str, body: AcceptRevision) -> tuple[dict, bool]:
        self.catalog.manual_dir(manual_id)
        key = (manual_id, body.request_id)
        with self._active_lock:
            self._active[key] += 1
        try:
            return self._accept(manual_id, version_id, body)
        finally:
            with self._active_lock:
                self._active[key] -= 1
                if not self._active[key]:
                    del self._active[key]

    def _accept(self, manual_id: str, version_id: str, body: AcceptRevision) -> tuple[dict, bool]:
        payload_hash = digest({"version_id": version_id, "body": body.model_dump(mode="json", by_alias=True)})
        # Resolve manual first, preventing path injection before lock creation.
        self.catalog.manual_dir(manual_id)
        with manual_lock(self.catalog.workspace, manual_id):
            previous = self.request(manual_id, body.request_id)
            if previous["status"] == "saved":
                meta = _json(
                    self.catalog.version_dir(manual_id, previous["result"]["version"]["version_id"]) / "revision.json"
                )
                if meta["request_payload_hash"] != payload_hash:
                    raise RevisionError("REQUEST_ID_CONFLICT")
                return previous["result"], False
            preview, graph, context = self.preview(manual_id, version_id, body)
            if not preview["has_changes"]:
                raise RevisionError("NO_CHANGES", 422)
            if not preview["can_accept"]:
                raise RevisionError("VALIDATION_FAILED", 422)
            if body.preview_hash != preview["preview_hash"]:
                raise RevisionError("STALE_PREVIEW")
            if not set(preview["required_acknowledgements"]).issubset(body.acceptance.acknowledged_issue_ids):
                raise RevisionError("ACKNOWLEDGEMENT_REQUIRED", 422)
            now = datetime.now(timezone.utc).isoformat()
            id_map = {n["id"]: "human_n_" + uuid.uuid4().hex for n in graph["nodes"] if n["id"].startswith("tmp_node_")}
            id_map.update(
                {e["id"]: "human_e_" + uuid.uuid4().hex for e in graph["edges"] if e["id"].startswith("tmp_edge_")}
            )
            saved = copy.deepcopy(graph)
            for node in saved["nodes"]:
                if node["id"] in id_map:
                    node["id"] = id_map[node["id"]]
                    for field in node["properties"]:
                        if field.endswith("_id"):
                            node["properties"][field] = node["id"]
            for edge in saved["edges"]:
                edge["id"] = id_map.get(edge["id"], edge["id"])
                for field in ("from", "to"):
                    edge[field] = id_map.get(edge[field], edge[field])
                for occ in edge.get("occurrences", []):
                    if occ.get("review", {}).get("status") in ("confirmed", "rejected"):
                        from backend.ui.graph_document import occurrence_hash

                        occ["review"]["content_hash"] = occurrence_hash(edge, occ, saved["nodes"])
                        occ["review"].setdefault("date", now)
            recompute(saved, context["ontology"])
            source_report = (
                saved.pop("report", None)
                or _json(context["folder"] / "source-report.json")
                or _json(context["folder"] / "report.json")
            )
            saved.update(version="kg-v3-graph-3", status="approved")
            saved["revision_summary"] = {
                "nodes": len(saved["nodes"]),
                "edges": len(saved["edges"]),
                "trusted": sum(e["trusted"] for e in saved["edges"] if not e.get("derived")),
            }
            uid = uuid.uuid4().hex
            revision_id = "revision~" + uid
            dirs = self.catalog.revision_dirs(manual_id)
            number = max((_json(p / "revision.json")["revision_number"] for _, p in dirs.values()), default=0) + 1
            parent = _json(context["folder"] / "revision.json", {})
            try:
                commit = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
                ).strip()
            except (OSError, subprocess.CalledProcessError):
                commit = ""
            meta = {
                "schema_version": "kg-ui-revision-1",
                "revision_id": revision_id,
                "revision_number": number,
                "manual_id": manual_id,
                "parent_version_id": version_id,
                "parent_graph_hash": context["preconditions"]["base_hash"],
                "root_run_id": parent.get("root_run_id", version_id),
                "created_at": now,
                "created_by": "human:operator",
                "note": body.note,
                "graph_hash": digest(saved),
                "ontology_hash": context["preconditions"]["ontology_hash"],
                "source_document_hash": context["source"]["pdf_hash"],
                "source_pdf_verified": context["source"]["pdf_available"],
                "source_review_hash": context["preconditions"]["source_review_hash"],
                "editor_code_commit": commit,
                "request_id": body.request_id,
                "request_payload_hash": payload_hash,
                "id_map": id_map,
                "operation_summary": {g: {k: len(v) for k, v in preview["diff"][g].items()} for g in preview["diff"]},
            }
            acceptance = {
                **body.acceptance.model_dump(),
                "author": "human:operator",
                "date": now,
                "graph_hash": meta["graph_hash"],
                "preview_hash": body.preview_hash,
            }
            root = self.catalog.workspace / manual_id / "revisions"
            root.mkdir(parents=True, exist_ok=True)
            stage = root / (".tmp-" + uid)
            stage.mkdir()
            files = {
                "revision.json": meta,
                "graph.json": saved,
                "changes.json": {
                    "operations": [o.model_dump(mode="json", by_alias=True) for o in body.operations],
                    "diff": graph_diff(with_occurrence_ids(context["raw"]), saved),
                },
                "validation.json": preview,
                "acceptance.json": acceptance,
                "source-review.json": context["source_review"],
                "source-report.json": source_report,
                "ontology.json": context["ontology"],
                "source-segments.json": context["segments"] if context["source"]["segments_available"] else {},
            }
            try:
                with (stage / "base-graph.json").open("wb") as handle:
                    handle.write(context["raw_bytes"])
                    handle.flush()
                    os.fsync(handle.fileno())
                for name, value in files.items():
                    with (stage / name).open("w") as handle:
                        json.dump(value, handle, ensure_ascii=False, allow_nan=False, indent=2)
                        handle.flush()
                        os.fsync(handle.fileno())
                if context["pdf"].exists() and context["source"]["pdf_available"]:
                    shutil.copyfile(context["pdf"], stage / "source.pdf")
                    with (stage / "source.pdf").open("rb") as handle:
                        os.fsync(handle.fileno())
                # A source changed concurrently must never be silently frozen under its old hash.
                if (
                    file_hash(context["pdf"]) != context["source"]["pdf_hash"]
                    or (context["folder"] / "graph.json").read_bytes() != context["raw_bytes"]
                ):
                    raise RevisionError("BASE_CHANGED")
                for path in (stage, root):
                    fd = os.open(path, os.O_RDONLY)
                    try:
                        os.fsync(fd)
                    finally:
                        os.close(fd)
                stage.rename(root / uid)
                fd = os.open(root, os.O_RDONLY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            except Exception:
                shutil.rmtree(stage, ignore_errors=True)
                raise
            return self.created(manual_id, revision_id, meta), True
