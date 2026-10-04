"""Regressions found by the independent review of 2afd41c (docs/EDITOR_GRAFO.md)."""

import json
import threading
import time

from backend.ui.graph_document import apply_operations, graph_diff, schema, with_occurrence_ids
from backend.ui.locks import manual_lock
from tests.test_ui_graph_document import fixture_graph, ops
from tests.test_ui_revisions import PATH, accept_body, editor_api  # noqa: F401  (pytest fixture)


def graph_with_exported_edge_conditions():
    """Like real exports (e.g. campaign/grizzly_g0872): edge-level conditions are not the literal
    intersection of the occurrences' conditions (the merger compares items differently)."""
    graph = fixture_graph()
    edge = graph["edges"][0]
    occ = edge["occurrences"][0]
    occ["conditions"] = [{"kind": "order", "text": "Step 3, after RESET.", "cite": ["seg"], "scope": "relation"}]
    second = json.loads(json.dumps(occ))
    second["record"] = "r2"
    second["conditions"] = [{"kind": "order", "text": "Step 3.", "cite": ["seg"], "scope": "relation"}]
    edge["occurrences"].append(second)
    edge["conditions"] = [{"kind": "order", "text": "Step 3, after RESET.", "cite": ["seg"], "scope": "relation"}]
    return graph


def test_untouched_edge_conditions_survive_an_unrelated_edit():
    base = graph_with_exported_edge_conditions()
    # Edit a node that is NOT an endpoint of the edge.
    result = apply_operations(
        base, ops({"op": "node.set_name", "node_id": "action", "value": "Replace part"}), schema(), {}
    )
    edge = next(e for e in result["edges"] if e["id"] == "edge")
    assert edge["conditions"] == base["edges"][0]["conditions"], "edge-level conditions rewritten without any edit"


def test_saved_revision_preserves_untouched_edges_and_summary_shows_every_change(editor_api):  # noqa: F811
    client, run, root = editor_api
    run.joinpath("graph.json").write_text(json.dumps(graph_with_exported_edge_conditions()))
    body = accept_body(client)  # renames node "sym": invalidation of its edge is expected
    body["operations"] = [{"op": "node.set_name", "node_id": "action", "value": "Replace part"}]
    preview = client.post(
        PATH + "/validate-edits", json={k: body[k] for k in ("preconditions", "operations", "draft_generation")}
    ).json()
    assert preview["diff"]["edges"]["updated"] == []  # the summary shown to the person: no edge change
    body["preview_hash"] = preview["preview_hash"]
    body["acceptance"]["acknowledged_issue_ids"] = preview["required_acknowledgements"]
    created = client.post(PATH + "/revisions", json=body)
    assert created.status_code == 201, created.text
    saved = client.get("/api/manuals/pump/versions/" + created.json()["version"]["version_id"] + "/graph").json()
    edge = next(e for e in saved["edges"] if e["id"] == "edge")
    assert edge["conditions"] == graph_with_exported_edge_conditions()["edges"][0]["conditions"]


def test_lock_held_by_an_acceptance_does_not_freeze_the_event_loop(editor_api):  # noqa: F811
    """api.py takes manual_lock inside `async def` endpoints (answer/apply/approve)."""
    client, run, root = editor_api
    held = threading.Event()

    def hold():
        with manual_lock(root / "workspace", "pump"):
            held.set()
            time.sleep(3)

    threading.Thread(target=hold).start()
    held.wait()
    threading.Thread(target=lambda: client.post(PATH + "/apply")).start()
    time.sleep(0.3)
    start = time.perf_counter()
    assert client.get("/api/ontology").status_code == 200  # unrelated, lock-free request
    assert time.perf_counter() - start < 1.0, "unrelated requests waited for the manual lock"


def test_untouched_edges_differ_from_raw_only_by_editor_metadata():
    """Occurrence ids, hashes and trust are added; pipeline data such as conditions is not rewritten."""
    raw = graph_with_exported_edge_conditions()
    result = apply_operations(raw, ops({"op": "node.set_name", "node_id": "action", "value": "X"}), schema(), {})
    raw_diff = graph_diff(with_occurrence_ids(raw), result)
    assert all(u["fields"] == ["occurrences"] for u in raw_diff["edges"]["updated"])
    for update in raw_diff["edges"]["updated"]:
        for before, after in zip(update["before"]["occurrences"], update["after"]["occurrences"]):
            assert {k: v for k, v in after.items() if k not in ("id", "content_hash", "trusted")} == {
                k: v for k, v in before.items() if k not in ("id", "content_hash")
            }
