import copy

import pytest
from pydantic import TypeAdapter, ValidationError

from backend.ui.graph_document import EditError, EditOperation, apply_operations, schema, with_occurrence_ids
from backend.ui.graph_validation import validate, value_state


def fixture_graph():
    spec = schema()
    nodes = []
    for t, id, name in [
        ("Asset", "asset", "Pump"),
        ("Symptom", "sym", "Noise"),
        ("FailureMode", "cause", "Wear"),
        ("CorrectiveAction", "action", "Replace"),
    ]:
        fields = next(n["properties"] for n in spec["nodes"] if n["name"] == t)
        props = {
            f["name"]: id if f["name"].endswith("_id") else name if f["name"] == "name" else "not_stated"
            for f in fields
            if f.get("required")
        }
        nodes.append(
            {"id": id, "type": t, "name": name, "properties": props, "evidence": [], "unknown": {"a": [0, False]}}
        )
    return {
        "version": "kg-v3-graph-2",
        "status": "approved",
        "nodes": nodes,
        "edges": [
            {
                "id": "edge",
                "type": "MAY_INDICATE",
                "from": "sym",
                "to": "cause",
                "tier": "green",
                "trusted": True,
                "conditions": [],
                "unknown": 42,
                "occurrences": [
                    {
                        "record": "r",
                        "tier": "green",
                        "certificate": {"segment_ids": ["seg"], "witnesses": ["llm"]},
                        "evidence": [{"segment_id": "seg", "text": "Noise means wear", "page": 1, "bbox": None}],
                        "conditions": [],
                    }
                ],
            }
        ],
        "excluded_relations": [{"old": True}],
        "report": {"historical": True},
        "unknown": {"nested": [None, False]},
    }


def ops(*values):
    return TypeAdapter(list[EditOperation]).validate_python(list(values))


def test_roundtrip_unknowns_and_invalidation():
    base = fixture_graph()
    original = copy.deepcopy(base)
    edited = apply_operations(base, ops({"op": "node.set_name", "node_id": "sym", "value": "Loud noise"}), schema(), {})
    assert base == original
    assert edited["unknown"] == base["unknown"]
    assert edited["edges"][0]["unknown"] == 42
    assert edited["excluded_relations"] == base["excluded_relations"]
    assert edited["nodes"][1]["properties"]["name"] == "Loud noise"
    assert not edited["edges"][0]["trusted"]
    assert edited["edges"][0]["tier"] is None
    assert "certificate" not in edited["edges"][0]["occurrences"][0]
    untouched = apply_operations(base, [], schema(), {})
    assert untouched["edges"][0]["occurrences"][0]["certificate"] == base["edges"][0]["occurrences"][0]["certificate"]


def test_domain_allowlist_root_cascade_and_schema():
    base = fixture_graph()
    with pytest.raises(EditError, match="ROOT_PROTECTED"):
        apply_operations(base, ops({"op": "node.delete", "node_id": "asset"}), schema(), {})
    with pytest.raises(EditError, match="RESERVED_FIELD"):
        apply_operations(
            base, ops({"op": "node.set_property", "node_id": "sym", "field": "certificate", "value": {}}), schema(), {}
        )
    with pytest.raises(ValidationError):
        ops(
            {
                "op": "edge.add",
                "temp_id": "tmp_edge_x",
                "relation_type": "MAY_INDICATE",
                "from": "sym",
                "to": "cause",
                "occurrences": [{"certificate": {"trusted": True}}],
            }
        )
    result = apply_operations(base, ops({"op": "node.delete", "node_id": "sym"}), schema(), {})
    assert not result["edges"]
    bad = apply_operations(
        base,
        ops(
            {
                "op": "edge.add",
                "temp_id": "tmp_edge_x",
                "relation_type": "MAY_INDICATE",
                "from": "cause",
                "to": "sym",
                "occurrences": [{}],
            }
        ),
        schema(),
        {},
    )
    assert any(i["code"] == "ENDPOINT_TYPE" and i["severity"] == "error" for i in validate(bad, base, schema()))


def test_types_empty_absent_and_multiline():
    base = fixture_graph()
    spec = schema()
    fields = next(n["properties"] for n in spec["nodes"] if n["name"] == "Symptom")
    fields += [
        {"name": "count", "type": "number", "required": False},
        {"name": "enabled", "type": "boolean", "required": False},
        {"name": "list", "type": "array", "items": "string", "required": False},
    ]
    changes = ops(
        *[
            {"op": "node.set_property", "node_id": "sym", "field": field, "value": value}
            for field, value in [
                ("count", 0),
                ("enabled", False),
                ("list", []),
                ("description", "Line 1\nLine 2"),
                ("severity", None),
            ]
        ]
    )
    result = apply_operations(base, changes, spec, {})
    props = result["nodes"][1]["properties"]
    assert props["count"] == 0 and props["enabled"] is False and props["list"] == []
    assert props["description"] == "Line 1\nLine 2" and props["severity"] is None
    assert value_state(props, "count") == value_state(props, "enabled") == "filled"
    assert value_state(props, "missing") == "missing"
    assert value_state(props, "list") == "empty"
    assert value_state({"a": "not_stated"}, "a") == "not_stated"


def test_occurrence_decision_and_source_allowlist():
    base = with_occurrence_ids(fixture_graph())
    occ = base["edges"][0]["occurrences"][0]
    with pytest.raises(EditError, match="SOURCE_SEGMENT_UNAVAILABLE"):
        apply_operations(
            base,
            ops({"op": "occurrence.update", "edge_id": "edge", "occurrence_id": occ["id"], "segment_ids": ["fake"]}),
            schema(),
            {},
        )
    result = apply_operations(
        base,
        ops(
            {
                "op": "occurrence.reject",
                "edge_id": "edge",
                "occurrence_id": occ["id"],
                "content_hash": occ["content_hash"],
            }
        ),
        schema(),
        {},
    )
    assert not result["edges"][0]["trusted"]
    assert result["edges"][0]["occurrences"][0]["review"]["status"] == "rejected"


def test_confirmation_survives_acceptance_but_expires_when_content_changes():
    from backend.ui.graph_document import occurrence_hash

    base = with_occurrence_ids(fixture_graph())
    rename = {"op": "node.set_name", "node_id": "sym", "value": "Corrected noise"}
    preview = apply_operations(base, ops(rename), schema(), {})
    occurrence = preview["edges"][0]["occurrences"][0]
    confirm = {
        "op": "occurrence.confirm",
        "edge_id": "edge",
        "occurrence_id": occurrence["id"],
        "content_hash": occurrence["content_hash"],
        "reason": "Inspected the source",
    }
    confirmed = apply_operations(base, ops(rename, confirm), schema(), {})
    assertion = confirmed["edges"][0]["occurrences"][0]
    assert assertion["trusted"] and assertion["tier"] is None and "certificate" not in assertion
    assert assertion["review"]["status"] == "confirmed"
    assert assertion["content_hash"] == occurrence_hash(confirmed["edges"][0], assertion, confirmed["nodes"])
    expired = apply_operations(
        base, ops(rename, confirm, {"op": "node.set_name", "node_id": "sym", "value": "Changed again"}), schema(), {}
    )
    assert not expired["edges"][0]["trusted"]


def test_multiple_occurrences_conditions_and_unique_diagnostics():
    base = with_occurrence_ids(fixture_graph())
    result = apply_operations(
        base,
        ops(
            {
                "op": "occurrence.add",
                "edge_id": "edge",
                "occurrence_id": "tmp_occ_new",
                "conditions": [{"kind": "if", "text": "Motor cold", "scope": "relation", "cite": []}],
                "annotation": "Operator note",
            }
        ),
        schema(),
        {},
    )
    edge = result["edges"][0]
    assert edge["trusted"] and not edge["occurrences"][1]["trusted"]
    assert edge["conditions"] == []
    ids = [i["id"] for i in validate(result, base, schema())]
    assert len(ids) == len(set(ids))
    assert edge["occurrences"][0]["certificate"] == base["edges"][0]["occurrences"][0]["certificate"]


def test_duplicate_ids_and_triplets_are_blocking():
    base = fixture_graph()
    base["nodes"].append(copy.deepcopy(base["nodes"][1]))
    graph = with_occurrence_ids(base)
    graph["edges"].append({**copy.deepcopy(graph["edges"][0]), "id": "second"})
    issues = validate(graph, base, schema())
    assert any(i["code"] == "DUPLICATE_ID" and i["severity"] == "error" for i in issues)
    assert any(i["code"] == "DUPLICATE_EDGE" and i["severity"] == "error" for i in issues)


def test_path_diagnostics_distinguish_preexisting_issues_and_rejected_content():
    base = with_occurrence_ids(fixture_graph())
    changed = apply_operations(
        base, ops({"op": "node.set_name", "node_id": "sym", "value": "Another name"}), schema(), {}
    )
    issues = validate(changed, base, schema())
    assert not next(i for i in issues if i["code"] == "NO_COMPATIBLE_ACTION_PATH")["introduced"]
    rejected = copy.deepcopy(changed)
    rejected["edges"][0]["occurrences"][0]["review"] = {"status": "rejected"}
    issues = validate(rejected, base, schema())
    assert not any(i["code"] in ("UNVERIFIED_CONTENT", "NO_EVIDENCE") for i in issues)
    assert next(i for i in issues if i["code"] == "ISOLATED_NODE" and i["target"]["id"] == "sym")["introduced"]
    assert next(i for i in issues if i["code"] == "PROBLEM_WITHOUT_CAUSE")["introduced"]
