"""Patch-based corrective re-extraction merge.

The corrective re-extraction pass historically asked the model to REBUILD the
complete ontology instance. On real manuals that output grows with the
document (50-70k characters observed), systematically hits the completion
limit, and the parse fallback keeps the previous ontology — so the reflective
loop silently degrades to a no-op exactly on the documents that need it most.

The model now returns only a PATCH — the nodes/relations to upsert or remove
for the listed issues — and this module applies it deterministically to the
previous ontology. Output size scales with the number of issues, not with the
document size, which removes the truncation failure mode and stops the model
from re-typing (and drifting) content that was already correct.

Patch shape:

    {
      "upsert_nodes": {"NodeType": [full node objects]},
      "remove_node_ids": ["node_id", ...],
      "add_relations": [full relation objects with evidence],
      "remove_relations": [{"name": "...", "from_id": "...", "to_id": "..."}]
    }

Everything here is pure: it never mutates its inputs and performs no I/O.
"""

from __future__ import annotations

import json
from typing import Any

from backend.services.ontology_coverage import _NODE_ID_FIELDS

_PATCH_KEYS = ("upsert_nodes", "remove_node_ids", "add_relations", "remove_relations")


def is_ontology_patch(data: Any) -> bool:
    """True when the payload is a patch, not a full ontology instance.

    A full instance carries a top-level "nodes" map; a patch carries at least
    one patch key and no "nodes" map. Models that ignore the patch instruction
    and return a full instance therefore keep working through the legacy path.
    """
    if not isinstance(data, dict):
        return False
    return any(key in data for key in _PATCH_KEYS) and "nodes" not in data


def _relation_key(rel: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(rel.get("name") or rel.get("type") or "").strip(),
        str(rel.get("from_id") or "").strip(),
        str(rel.get("to_id") or "").strip(),
    )


def apply_ontology_patch(
    previous: dict[str, Any],
    patch: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, int]]:
    """Apply a patch to a full ontology dict; return (merged, report).

    - upsert_nodes REPLACE the node with the same id or APPEND a new one.
    - remove_node_ids drop the nodes AND every relation touching them, so a
      removal can never leave dangling edges.
    - remove_relations match on (name, from_id, to_id).
    - add_relations are deduplicated against the surviving relations.
    """
    result = json.loads(json.dumps(previous or {}))
    nodes: dict[str, Any] = result.setdefault("nodes", {})

    upserted = 0
    for label, items in (patch.get("upsert_nodes") or {}).items():
        id_field = _NODE_ID_FIELDS.get(str(label))
        if not id_field or not isinstance(items, list):
            continue
        bucket = [node for node in nodes.get(label) or [] if isinstance(node, dict)]
        index_by_id = {
            str(node.get(id_field) or "").strip(): position
            for position, node in enumerate(bucket)
        }
        for item in items:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get(id_field) or "").strip()
            if not node_id:
                continue
            if node_id in index_by_id:
                bucket[index_by_id[node_id]] = item
            else:
                index_by_id[node_id] = len(bucket)
                bucket.append(item)
            upserted += 1
        nodes[label] = bucket

    remove_ids = {
        str(node_id).strip()
        for node_id in patch.get("remove_node_ids") or []
        if str(node_id).strip()
    }
    removed_nodes = 0
    if remove_ids:
        for label, id_field in _NODE_ID_FIELDS.items():
            bucket = nodes.get(label)
            if not bucket:
                continue
            kept = [
                node for node in bucket
                if not isinstance(node, dict)
                or str(node.get(id_field) or "").strip() not in remove_ids
            ]
            removed_nodes += len(bucket) - len(kept)
            nodes[label] = kept

    relations = [rel for rel in result.get("relations") or [] if isinstance(rel, dict)]
    remove_rel_keys = {
        _relation_key(rel)
        for rel in patch.get("remove_relations") or []
        if isinstance(rel, dict)
    }
    before = len(relations)
    relations = [
        rel for rel in relations
        if _relation_key(rel) not in remove_rel_keys
        and str(rel.get("from_id") or "").strip() not in remove_ids
        and str(rel.get("to_id") or "").strip() not in remove_ids
    ]
    removed_relations = before - len(relations)

    # Valid endpoints AFTER upserts and removals: patched relations may only
    # reference nodes that actually exist in the merged instance. Without this
    # gate a contradictory patch (remove fm_x + add RESOLVED_BY from fm_x) or
    # an invented id produced dangling edges that surfaced as blocking
    # relation_missing_source errors (observed on a real 588-page manual run).
    valid_node_ids = {
        str(node.get(id_field) or "").strip()
        for label, id_field in _NODE_ID_FIELDS.items()
        for node in nodes.get(label) or []
        if isinstance(node, dict) and str(node.get(id_field) or "").strip()
    }

    existing_keys = {_relation_key(rel) for rel in relations}
    added_relations = 0
    skipped_dangling = 0
    for rel in patch.get("add_relations") or []:
        if not isinstance(rel, dict):
            continue
        key = _relation_key(rel)
        if not all(key) or key in existing_keys:
            continue
        if key[1] not in valid_node_ids or key[2] not in valid_node_ids:
            skipped_dangling += 1
            continue
        relations.append(rel)
        existing_keys.add(key)
        added_relations += 1

    result["relations"] = relations
    report = {
        "upserted_nodes": upserted,
        "removed_nodes": removed_nodes,
        "added_relations": added_relations,
        "removed_relations": removed_relations,
        "skipped_dangling_relations": skipped_dangling,
    }
    return result, report
