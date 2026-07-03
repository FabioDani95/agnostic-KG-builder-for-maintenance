from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

_pdf_to_run_id: dict[str, str] = {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_default(value: Any) -> str:
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default), encoding="utf-8")


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class RunStore:
    def __init__(self, root_dir: str | Path | None = None):
        self.root_dir = self._resolve_root_dir(root_dir)

    @staticmethod
    def _resolve_root_dir(root_dir: str | Path | None = None) -> Path:
        if root_dir is not None:
            path = Path(root_dir)
        else:
            override = str(os.environ.get("KG_RUNS_DIR", "") or "").strip()
            path = Path(override) if override else ROOT_DIR / "data" / "runs"
        return path if path.is_absolute() else ROOT_DIR / path

    def run_dir(self, run_id: str) -> Path:
        return self.root_dir / run_id

    def run_id_for_pdf(self, pdf_id: str) -> str | None:
        return _pdf_to_run_id.get(pdf_id)

    def load_manifest(self, run_id: str) -> dict[str, Any]:
        return _read_json(self.run_dir(run_id) / "manifest.json", {})

    def read_trace(self, run_id: str) -> list[dict[str, Any]]:
        return _read_jsonl(self.run_dir(run_id) / "trace.jsonl")

    def latest_snapshot(self, run_id: str) -> dict[str, Any]:
        snapshot_dir = self.run_dir(run_id) / "state_snapshots"
        snapshots = sorted(snapshot_dir.glob("*.json"), key=lambda path: path.stat().st_mtime)
        if not snapshots:
            return {}
        return _read_json(snapshots[-1], {})

    def load_persisted_store(self, run_id: str) -> dict[str, Any] | None:
        run_dir = self.run_dir(run_id)
        if not run_dir.exists():
            return None
        manifest = self.load_manifest(run_id)
        state = self.latest_snapshot(run_id)
        if not state:
            state = {
                "run_id": run_id,
                "pdf_id": manifest.get("pdf_id", ""),
                "filename": manifest.get("filename", ""),
                "current_phase": "loaded",
                "run_status": "loaded",
                "phase_history": [],
                "supervisor_log": [],
            }
        return {
            "run_id": run_id,
            "pdf_id": state.get("pdf_id") or manifest.get("pdf_id"),
            "filename": manifest.get("filename") or state.get("filename", ""),
            "graph_state": state,
            "pipeline_trace": self.read_trace(run_id),
            "run_dir": str(run_dir),
        }

    def create_run(self, store: dict[str, Any], *, input_path: str | Path | None = None) -> Path:
        graph_state = store.get("graph_state") or {}
        run_id = str(store.get("run_id") or graph_state.get("run_id") or "").strip()
        pdf_id = str(store.get("pdf_id") or graph_state.get("pdf_id") or "").strip()
        if not run_id or not pdf_id:
            raise ValueError("store must include pdf_id and run_id before creating a RunStore entry.")

        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        _pdf_to_run_id[pdf_id] = run_id

        manifest = {
            "run_id": run_id,
            "pdf_id": pdf_id,
            "filename": store.get("filename", ""),
            "source_type": store.get("source_type", ""),
            "source_title": store.get("source_title", ""),
            "page_count": store.get("page_count") or len(store.get("pages") or []),
            "created_at": _utc_now(),
            "config_snapshot": graph_state.get("config_snapshot") or store.get("config_snapshot") or {},
            "selected_models": graph_state.get("selected_models") or store.get("selected_models") or {},
        }
        _write_json(run_dir / "manifest.json", manifest)
        _write_json(run_dir / "pages.json", store.get("pages") or [])
        if input_path:
            self._copy_input(run_dir, input_path)
        self.snapshot(store)
        return run_dir

    def append_event(self, pdf_id: str, kind: str, payload: dict[str, Any]) -> None:
        run_id = _pdf_to_run_id.get(pdf_id)
        if not run_id:
            return
        event = {
            "timestamp": _utc_now(),
            "kind": kind,
            **payload,
        }
        path = self.run_dir(run_id) / "events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, default=_json_default) + "\n")

    def append_trace(self, pdf_id: str, step: dict[str, Any]) -> None:
        run_id = _pdf_to_run_id.get(pdf_id)
        if not run_id:
            return
        from backend.observability.trace import TraceRecorder

        TraceRecorder(self.run_dir(run_id)).record(step)

    def snapshot(self, store: dict[str, Any]) -> None:
        graph_state = store.get("graph_state") or {}
        pdf_id = str(store.get("pdf_id") or graph_state.get("pdf_id") or "").strip()
        run_id = _pdf_to_run_id.get(pdf_id)
        if not run_id:
            return
        phase = str(graph_state.get("current_phase") or "unknown").strip() or "unknown"
        _write_json(self.run_dir(run_id) / "state_snapshots" / f"{phase}.json", graph_state)

    def copy_export_artifacts(self, store: dict[str, Any]) -> None:
        graph_state = store.get("graph_state") or {}
        pdf_id = str(store.get("pdf_id") or graph_state.get("pdf_id") or "").strip()
        run_id = _pdf_to_run_id.get(pdf_id)
        if not run_id:
            return
        export_dir = self.run_dir(run_id) / "export"
        export_dir.mkdir(parents=True, exist_ok=True)
        for key in ("ontology_path", "metrics_path"):
            path_value = store.get(key)
            if not path_value:
                continue
            source = Path(str(path_value))
            if source.exists() and source.is_file():
                shutil.copy2(source, export_dir / source.name)
        ontology_path = store.get("ontology_path")
        if ontology_path:
            conversation_path = Path(str(ontology_path)).with_name("conversation.json")
            if conversation_path.exists() and conversation_path.is_file():
                shutil.copy2(conversation_path, export_dir / conversation_path.name)

    def _copy_input(self, run_dir: Path, input_path: str | Path) -> None:
        source = Path(input_path)
        if not source.exists() or not source.is_file():
            return
        input_dir = run_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        suffix = source.suffix or ".pdf"
        shutil.copy2(source, input_dir / f"manual{suffix}")


def clear_registry() -> None:
    _pdf_to_run_id.clear()


def append_chat_event(pdf_id: str, event: dict[str, Any]) -> None:
    try:
        RunStore().append_event(pdf_id, "chat_event", {"event": event})
    except Exception:
        pass


def append_human_action(pdf_id: str, action: dict[str, Any]) -> None:
    try:
        RunStore().append_event(pdf_id, "human_action", {"action": action})
    except Exception:
        pass


def append_trace_step(pdf_id: str, step: dict[str, Any]) -> None:
    try:
        RunStore().append_trace(pdf_id, step)
    except Exception:
        pass


def snapshot_store(store: dict[str, Any]) -> None:
    try:
        RunStore().snapshot(store)
    except Exception:
        pass


def copy_export_artifacts(store: dict[str, Any]) -> None:
    try:
        RunStore().copy_export_artifacts(store)
    except Exception:
        pass
