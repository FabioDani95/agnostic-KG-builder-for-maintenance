#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent


def _read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _resolve_run(value: str, runs_dir: str | None) -> Path:
    candidate = Path(value)
    if candidate.exists():
        return candidate
    base = Path(runs_dir) if runs_dir else ROOT_DIR / "data" / "runs"
    if not base.is_absolute():
        base = ROOT_DIR / base
    return base / value


def _latest_snapshot(run_dir: Path) -> dict[str, Any]:
    snapshot_dir = run_dir / "state_snapshots"
    snapshots = sorted(snapshot_dir.glob("*.json"), key=lambda path: path.stat().st_mtime)
    if not snapshots:
        return {}
    return _read_json(snapshots[-1], {})


def _load_export_metrics(run_dir: Path) -> dict[str, Any]:
    candidates = sorted((run_dir / "export").glob("*metrics*.json"))
    if not candidates:
        candidates = [run_dir / "export" / "metrics.json"]
    for candidate in candidates:
        payload = _read_json(candidate)
        if isinstance(payload, dict):
            return payload
    return {}


def _node_count(state: dict[str, Any]) -> int:
    ontology = state.get("ontology_draft") or (state.get("ontology_pipeline") or {}).get("ontology") or {}
    nodes = ontology.get("nodes") if isinstance(ontology, dict) else {}
    if not isinstance(nodes, dict):
        return 0
    return sum(len(items or []) for items in nodes.values())


def _triplet_count(state: dict[str, Any]) -> int:
    return len(state.get("cleaned_triplets") or state.get("raw_triplets") or [])


def build_summary(run_dir: Path) -> dict[str, Any]:
    manifest = _read_json(run_dir / "manifest.json", {})
    events = _read_jsonl(run_dir / "events.jsonl")
    state = _latest_snapshot(run_dir)
    metrics = _load_export_metrics(run_dir)
    phase_history = state.get("phase_history") or []
    human_actions = [event for event in events if event.get("kind") == "human_action"]
    chat_events = [event for event in events if event.get("kind") == "chat_event"]
    totals = metrics.get("totals") or metrics.get("extraction_performance") or {}
    return {
        "run_id": manifest.get("run_id") or state.get("run_id") or run_dir.name,
        "pdf_id": manifest.get("pdf_id") or state.get("pdf_id"),
        "filename": manifest.get("filename") or state.get("filename", ""),
        "current_phase": state.get("current_phase"),
        "run_status": state.get("run_status"),
        "phase_timeline": phase_history,
        "event_counts": {
            "chat_events": len(chat_events),
            "human_actions": len(human_actions),
        },
        "human_actions": [event.get("action") for event in human_actions],
        "counts": {
            "nodes": _node_count(state),
            "triplets": _triplet_count(state),
            "validated_triplets": len(state.get("validated_triplets") or []),
        },
        "metrics": {
            "duration_seconds": totals.get("duration_seconds"),
            "estimated_cost_usd": totals.get("estimated_cost_usd"),
            "total_tokens": totals.get("total_tokens"),
            "llm_calls": totals.get("llm_calls"),
        },
    }


def emit_summary(run_dir: Path) -> None:
    print(json.dumps(build_summary(run_dir), indent=2, ensure_ascii=False))


def emit_events(run_dir: Path, event_type: str | None) -> None:
    events = _read_jsonl(run_dir / "events.jsonl")
    if event_type:
        events = [
            event for event in events
            if event.get("kind") == event_type or (event.get("event") or {}).get("type") == event_type
        ]
    print(json.dumps(events, indent=2, ensure_ascii=False))


def emit_state(run_dir: Path, phase: str) -> None:
    path = run_dir / "state_snapshots" / f"{phase}.json"
    if not path.exists():
        raise SystemExit(f"State snapshot not found: {path}")
    print(json.dumps(_read_json(path, {}), indent=2, ensure_ascii=False))


def emit_diff(left: Path, right: Path) -> None:
    left_state = _latest_snapshot(left)
    right_state = _latest_snapshot(right)
    payload = {
        "left": left.name,
        "right": right.name,
        "delta": {
            "nodes": _node_count(right_state) - _node_count(left_state),
            "triplets": _triplet_count(right_state) - _triplet_count(left_state),
            "phase_history": len(right_state.get("phase_history") or []) - len(left_state.get("phase_history") or []),
        },
        "left_counts": {
            "nodes": _node_count(left_state),
            "triplets": _triplet_count(left_state),
        },
        "right_counts": {
            "nodes": _node_count(right_state),
            "triplets": _triplet_count(right_state),
        },
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay and inspect a persisted KG Builder run.")
    parser.add_argument("run", help="Run directory path or run_id under --runs-dir.")
    parser.add_argument("--runs-dir", default=None, help="Base directory for run_id lookup.")
    parser.add_argument("--summary", action="store_true", help="Print a compact run summary.")
    parser.add_argument("--events", action="store_true", help="Print events.jsonl as JSON.")
    parser.add_argument("--type", default=None, help="Filter --events by kind or chat event type.")
    parser.add_argument("--state", default=None, help="Print state_snapshots/<phase>.json.")
    parser.add_argument("--diff", default=None, help="Compare this run with another run path or id.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    run_dir = _resolve_run(args.run, args.runs_dir)
    if not run_dir.exists():
        raise SystemExit(f"Run not found: {run_dir}")
    if args.diff:
        other = _resolve_run(args.diff, args.runs_dir)
        if not other.exists():
            raise SystemExit(f"Run not found: {other}")
        emit_diff(run_dir, other)
    elif args.events:
        emit_events(run_dir, args.type)
    elif args.state:
        emit_state(run_dir, args.state)
    else:
        emit_summary(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
