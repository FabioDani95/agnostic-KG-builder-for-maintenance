"""The fixed ontology as an input: prompt text and response schemas are derived from it.

Nothing here names a node type. The root type (the asset) is the one that is
never the target of a relation; relations leaving it are added by the code,
all others are extracted by the model.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

ONTOLOGY_PATH = Path(__file__).resolve().parents[2] / "ontology_schema.JSON"
ACTION_KINDS = ("", "repair", "inspection", "escalation")


@dataclass(frozen=True)
class RelationSpec:
    name: str
    domain: str
    range: str
    description: str


@dataclass(frozen=True)
class OntologySpec:
    root: str
    node_types: dict[str, str]
    properties: dict[str, tuple[tuple[str, bool], ...]]
    relations: tuple[RelationSpec, ...]

    @property
    def extractable_types(self) -> list[str]:
        return [name for name in self.node_types if name != self.root]

    @property
    def extractable_relations(self) -> list[RelationSpec]:
        return [relation for relation in self.relations if relation.domain != self.root]

    @property
    def root_relations(self) -> list[RelationSpec]:
        return [relation for relation in self.relations if relation.domain == self.root]

    def relation(self, name: str) -> RelationSpec | None:
        return next((item for item in self.relations if item.name == name), None)

    def relation_between(self, domain: str, range_: str) -> RelationSpec | None:
        return next((item for item in self.extractable_relations if (item.domain, item.range) == (domain, range_)), None)


@lru_cache(maxsize=4)
def load_ontology(path: str = str(ONTOLOGY_PATH)) -> OntologySpec:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    nodes = {item["name"]: item.get("description", "") for item in data["nodes"]}
    properties = {
        item["name"]: tuple((prop["name"], bool(prop.get("required"))) for prop in item.get("properties", []))
        for item in data["nodes"]
    }
    relations = tuple(
        RelationSpec(item["name"], item["domain"], item["range"], item.get("description", ""))
        for item in data["relations"]
    )
    targets = {relation.range for relation in relations}

    def reach(start: str) -> int:
        seen, frontier = {start}, [start]
        while frontier:
            current = frontier.pop()
            for relation in relations:
                if relation.domain == current and relation.range not in seen:
                    seen.add(relation.range)
                    frontier.append(relation.range)
        return len(seen) - 1

    # The root (the asset) is never a target and reaches the most other types.
    sources = sorted((name for name in nodes if name not in targets), key=reach, reverse=True)
    if not sources or (len(sources) > 1 and reach(sources[0]) == reach(sources[1])):
        raise ValueError(f"the ontology has no unique root type among {sources}")
    return OntologySpec(root=sources[0], node_types=nodes, properties=properties, relations=relations)


def ontology_brief(spec: OntologySpec) -> str:
    lines = ["Node types:"]
    lines.extend(f"- {name}: {spec.node_types[name]}" for name in spec.extractable_types)
    lines.append("Relations (source type -> target type):")
    lines.extend(
        f"- {item.domain} -[{item.name}]-> {item.range}: {item.description}" for item in spec.extractable_relations
    )
    return "\n".join(lines)


def _citations(segment_ids: list[str]) -> dict[str, Any]:
    items: dict[str, Any] = {"type": "string"}
    if segment_ids:
        items["enum"] = sorted(set(segment_ids))
    return {"type": "array", "items": items}


def _object(properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False, "required": list(properties), "properties": properties}


def extraction_schema(spec: OntologySpec, segment_ids: list[str]) -> dict[str, Any]:
    """Strict schema of one extraction read; citations can only name real segments."""

    cite = _citations(segment_ids)
    entity = _object({
        "key": {"type": "string"},
        "type": {"type": "string", "enum": spec.extractable_types},
        "name": {"type": "string"},
        "code": {"type": "string"},
        "kind": {"type": "string", "enum": list(ACTION_KINDS)},
        "stated": {"type": "boolean"},
        "cite": cite,
    })
    relation = _object({
        "type": {"type": "string", "enum": [item.name for item in spec.extractable_relations]},
        "source": {"type": "string"},
        "target": {"type": "string"},
        "record": {"type": "string"},
        "conditions": {"type": "array", "items": {"type": "string"}},
        "cite": cite,
    })
    unclear = _object({"note": {"type": "string"}, "cite": cite})
    return _object({
        "entities": {"type": "array", "items": entity},
        "relations": {"type": "array", "items": relation},
        "unclear": {"type": "array", "items": unclear},
    })


def verification_schema(statement_ids: list[str]) -> dict[str, Any]:
    verdict = _object({
        "id": {"type": "string", "enum": statement_ids} if statement_ids else {"type": "string"},
        "verdict": {"type": "string", "enum": ["supported", "not_supported", "unclear"]},
    })
    return _object({"verdicts": {"type": "array", "items": verdict}})
