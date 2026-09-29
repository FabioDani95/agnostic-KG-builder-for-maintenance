"""Progress events for the interface, translated from the pipeline's raw events.

The pipeline emits raw events (``step_started``, ``step_finished``, ``state_saved``,
``state_loaded``); the command line adds ``run_started``, ``run_finished`` and
``run_failed``. A replay rebuilds the same raw events from a finished run folder. Both
go through :class:`EventTranslator`, so a live run and a replay produce identical
interface events.

Provisional node and edge IDs use the formulas of ``merger.py``: a node that is not
merged already has its final ID, and ``graph_final.merged_into`` maps the others.
"""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from backend.kg_v3.contracts import Certificate, Tier, assign_tier
from backend.kg_v3.extractor import Endpoint
from backend.kg_v3.merger import identity, node_id

# Pipeline steps grouped into the six stations of docs/PIANO_V3.md.
STATIONS = ("read", "map", "extract", "check", "merge", "ask")
STEP_STATION = {
    "pdf_read": "read",
    "map": "map", "scan": "map", "gate_map": "map",
    "extract": "extract",
    "check": "check", "split_recheck": "check", "navigation": "check", "action_reduction": "check",
    "omissions": "check", "visual": "check",
    "merge": "merge",
    "gate_doubts": "ask", "gate_recovery": "ask", "gate_approval": "ask",
}
_TIER_RANK = {Tier.GREEN.value: 0, Tier.YELLOW.value: 1, Tier.RED.value: 2}
_PAGE = re.compile(r"^p(\d+)\.")


class UiEvent(BaseModel):
    seq: int
    t: float
    cost_usd: float = 0.0
    kind: str
    data: dict[str, Any]


def page_of(segment_id: str) -> int | None:
    match = _PAGE.match(segment_id)
    return int(match.group(1)) if match else None


def pages_of(segment_ids: list[str]) -> list[int]:
    return sorted({page for page in map(page_of, segment_ids) if page is not None})


def endpoint_id(endpoint: dict[str, Any]) -> str:
    return node_id(identity(Endpoint.model_validate(endpoint)))


def edge_id(relation_type: str, source: str, target: str) -> str:
    """Same formula as the edges assembled in ``merger.assemble``."""

    return "v3e_" + hashlib.sha256("|".join((relation_type, source, target)).encode("utf-8")).hexdigest()[:20]


def _best(tiers: list[str]) -> str:
    return min(tiers, key=_TIER_RANK.__getitem__)


class EventTranslator:
    """Turn raw pipeline events into interface events, keeping what the view already knows."""

    def __init__(self) -> None:
        self.seq = 0
        self.cost = 0.0
        self.station: str | None = None
        self.units_total = 0
        self.units_done: set[str] = set()
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}

    # Output ----------------------------------------------------------------

    def _event(self, t: float, kind: str, **data: Any) -> UiEvent:
        self.seq += 1
        return UiEvent(seq=self.seq, t=round(t, 3), cost_usd=round(self.cost, 6), kind=kind, data=data)

    def feed(self, kind: str, data: dict[str, Any], t: float) -> list[UiEvent]:
        if data.get("cost_usd") is not None:
            self.cost = max(self.cost, float(data["cost_usd"]))
        handler = getattr(self, f"_on_{kind}", None)
        return handler(data, t) if handler else []

    # Run -------------------------------------------------------------------

    def _on_run_started(self, data: dict[str, Any], t: float) -> list[UiEvent]:
        fields = ("manual_id", "version_id", "mode", "speed", "pages")
        return [self._event(t, "run_started", **{key: data.get(key) for key in fields})]

    def _on_run_failed(self, data: dict[str, Any], t: float) -> list[UiEvent]:
        return [*self._close_station(t), self._event(t, "run_failed", message=str(data.get("message", "")))]

    def _on_run_finished(self, data: dict[str, Any], t: float) -> list[UiEvent]:
        graph = data.get("graph") or {}
        nodes = [{"id": node["id"], "type": node["type"], "name": node["name"]} for node in graph.get("nodes", [])]
        edges = [{"id": edge["id"], "type": edge["type"], "from": edge["from"], "to": edge["to"],
                  "tier": edge["tier"], "derived": bool(edge.get("derived"))} for edge in graph.get("edges", [])]
        merged_into: dict[str, str] = {}
        for node in graph.get("nodes", []):
            code = str((node.get("properties") or {}).get("code") or "")
            for name in [node["name"], *node.get("aliases", [])]:
                provisional = endpoint_id({"type": node["type"], "name": name, "code": code})
                if provisional != node["id"]:
                    merged_into[provisional] = node["id"]
        # Where each provisional edge ends up once its ends follow the merges.
        final_ids = {edge["id"] for edge in edges}
        edges_into = {}
        for key, edge in self.edges.items():
            moved = edge_id(edge["type"], merged_into.get(edge["from"], edge["from"]),
                            merged_into.get(edge["to"], edge["to"]))
            if moved != key and moved in final_ids:
                edges_into[key] = moved
        # Asset relations added by the export are not knowledge verified from the manual.
        tiers = [edge["tier"] for edge in graph.get("edges", []) if not edge.get("derived")]
        return [
            *self._close_station(t),
            self._event(t, "graph_final", nodes=nodes, edges=edges, merged_into=merged_into,
                        edges_into=edges_into),
            self._event(t, "run_finished", status=data.get("status") or graph.get("status"),
                        verified=tiers.count(Tier.GREEN.value), doubtful=tiers.count(Tier.YELLOW.value),
                        excluded=len(graph.get("excluded_relations", [])),
                        open_questions=int(data.get("open_questions") or 0)),
        ]

    # Steps -----------------------------------------------------------------

    def _close_station(self, t: float) -> list[UiEvent]:
        if self.station is None:
            return []
        done, self.station = self.station, None
        return [self._event(t, "station", station=done, state="done")]

    def _on_step_started(self, data: dict[str, Any], t: float) -> list[UiEvent]:
        station = STEP_STATION.get(str(data.get("step")))
        if station is None or station == self.station:
            return []
        events = self._close_station(t)
        self.station = station
        detail: dict[str, Any] = {"step": data.get("step")}
        if station == "extract":
            detail.update(done=len(self.units_done), total=self.units_total)
        return [*events, self._event(t, "station", station=station, state="running", **detail)]

    def _on_step_finished(self, data: dict[str, Any], t: float) -> list[UiEvent]:
        return []

    # State -----------------------------------------------------------------

    def _on_state_loaded(self, data: dict[str, Any], t: float) -> list[UiEvent]:
        return self._on_state_saved(data, t)

    def _on_state_saved(self, data: dict[str, Any], t: float) -> list[UiEvent]:
        name, value = str(data.get("name", "")), data.get("value")
        if value is None:
            return []
        if name == "map":
            pages = [{"page": entry["page"], "label": entry["label"], "unsure": entry.get("unsure", False)}
                     for entry in value.get("entries", [])]
            return [self._event(t, "pages_mapped", pages=pages)]
        if name == "units":
            self.units_total = len(value)
            units = [{"unit_id": unit["unit_id"], "pages": unit["pages"], "section": unit.get("section", "")}
                     for unit in value]
            return [self._event(t, "units_planned", units=units)]
        if name.startswith("extract_"):
            return self._extracted(value, t)
        if name.startswith(("checked_", "rechecked_", "recovery_")):
            return self._checked(value, t, replace=True)
        if name.startswith("navigation_"):
            return self._checked(value, t, replace=False)
        if name.startswith("merge_plan_"):
            same = [[node_id(pair["left"]), node_id(pair["right"])] for pair in value.get("same", [])]
            return [self._event(t, "merged", same=same, unsure=len(value.get("unsure", [])))]
        if name.startswith("gate_"):
            answered = [{"question_id": answer["question_id"], "option_id": answer["option_id"],
                         "by": answer["answered_by"]["kind"]} for answer in value.get("answers", [])]
            return [self._event(t, "questions", gate=name.removeprefix("gate_"),
                                total=len(value.get("questions", [])), answered=answered,
                                pending=list(value.get("pending", [])))]
        return []

    def _node(self, endpoint: dict[str, Any]) -> tuple[str, dict[str, Any] | None]:
        key = endpoint_id(endpoint)
        if key in self.nodes:
            return key, None
        node = {"id": key, "type": endpoint["type"], "name": endpoint["name"],
                "pages": pages_of(list(endpoint.get("cites") or []))}
        self.nodes[key] = node
        return key, node

    def _extracted(self, value: dict[str, Any], t: float) -> list[UiEvent]:
        unit_id = value["unit_id"]
        if unit_id in self.units_done:
            return []
        self.units_done.add(unit_id)
        nodes, edges = [], []
        for proposal in value.get("proposals", []):
            source, new_source = self._node(proposal["source"])
            target, new_target = self._node(proposal["target"])
            nodes.extend(node for node in (new_source, new_target) if node)
            key = edge_id(proposal["relation_type"], source, target)
            if key not in self.edges:
                edge = {"id": key, "type": proposal["relation_type"], "from": source, "to": target,
                        "pages": pages_of(list(proposal.get("cites") or [])), "tier": None}
                self.edges[key] = edge
                edges.append(edge)
        return [self._event(t, "unit_extracted", unit_id=unit_id, index=len(self.units_done),
                            total=self.units_total, nodes=nodes, edges=edges)]

    def _checked(self, relations: list[dict[str, Any]], t: float, *, replace: bool) -> list[UiEvent]:
        tiers: dict[str, list[str]] = {}
        nodes, shapes = [], {}
        for relation in relations:
            lead = relation["proposals"][0] if relation.get("proposals") else None
            if lead is None:
                continue
            source, new_source = self._node(lead["source"])
            target, new_target = self._node(lead["target"])
            nodes.extend(node for node in (new_source, new_target) if node)
            key = edge_id(relation["assertion"]["relation_type"], source, target)
            certificate = Certificate.model_validate(relation["assertion"]["certificate"])
            tiers.setdefault(key, []).append(assign_tier(certificate).value)
            shapes[key] = {"type": relation["assertion"]["relation_type"], "from": source, "to": target,
                           "pages": pages_of(list(certificate.segment_ids))}
        removed = []
        if replace:
            removed = [key for key in self.edges if key not in tiers]
            for key in removed:
                del self.edges[key]
        edges = []
        for key, found in tiers.items():
            previous = self.edges.get(key, {})
            # A full list replaces what was known; added relations only improve an edge.
            if not replace and previous.get("tier"):
                found = [*found, previous["tier"]]
            edge = {**previous, "id": key, **shapes[key], "tier": _best(found)}
            self.edges[key] = edge
            edges.append(edge)
        return [self._event(t, "relations_checked", nodes=nodes, edges=edges, removed=removed)]



class EventLog:
    """Event listener that appends interface events to ``events.jsonl`` as they happen.

    A resumed run continues the numbering and the clock of the file it appends to.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.translator = EventTranslator()
        self.offset = 0.0
        if path.exists():
            lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if lines:
                last = UiEvent.model_validate_json(lines[-1])
                self.translator.seq, self.offset = last.seq, last.t
        self.started = time.perf_counter()

    def __call__(self, kind: str, data: dict[str, Any]) -> None:
        events = self.translator.feed(kind, data, self.offset + time.perf_counter() - self.started)
        if events:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.writelines(event.model_dump_json() + "\n" for event in events)
