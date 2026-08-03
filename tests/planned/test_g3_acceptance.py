from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parents[1] / "fixtures" / "g3"
HARDENING_FIXTURES = Path(__file__).parents[1] / "fixtures" / "csv_hardening"


def _workspace(client, machine_payload) -> str:
    response = client.post("/api/workspace", json=machine_payload)
    assert response.status_code == 201, response.text
    return response.json()["workspace"]["workspace_id"]


def _upload_csv(client, workspace_id: str, fixture: str | Path):
    path = Path(fixture)
    if not path.is_absolute():
        path = FIXTURES / path
    payload = path.read_bytes()
    response = client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "operational"},
        files={"file": (path.name, payload, "text/csv")},
    )
    assert response.status_code == 200, response.text
    return response.json()["source"]


def _prepare_and_confirm_all(client, workspace_id: str):
    response = client.post(f"/api/workspaces/{workspace_id}/g2/preparation")
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["state"] == "ready"
    for profile in result["profiles"]:
        response = client.post(f"/api/g2/profiles/{profile['profile_id']}/confirm")
        assert response.status_code == 200, response.text
    assert response.json()["completed"] is True


def test_g3_generates_navigable_source_graph_and_deduplicates_within_csv(
    foundation_client,
    machine_payload,
):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload_csv(foundation_client, workspace_id, "synthetic_press_events_it.csv")
    _prepare_and_confirm_all(foundation_client, workspace_id)

    initial = foundation_client.get(f"/api/workspaces/{workspace_id}/g3/subgraphs")
    assert initial.status_code == 200, initial.text
    assert initial.json()["sources"][0]["state"] == "ready"
    assert initial.json()["merge_barrier"]["state"] == "waiting_for_generation"

    response = foundation_client.post(
        f"/api/workspaces/{workspace_id}/g3/sources/{source['source_id']}/generate"
    )
    assert response.status_code == 200, response.text
    view = response.json()
    item = view["sources"][0]
    graph = item["subgraph"]
    assert item["state"] == "reviewing"
    assert graph["duplicate_nodes_consolidated"] == 5
    assert graph["duplicate_relations_consolidated"] == 6
    assert {node["node_type"] for node in graph["nodes"]} == {
        "Asset", "Component", "Symptom", "FailureMode", "CorrectiveAction", "ErrorCode"
    }
    assert {relation["relation_type"] for relation in graph["relations"]} == {
        "HAS_COMPONENT", "MAY_INDICATE", "AFFECTS", "RESOLVED_BY", "GENERATES_ERROR", "INDICATES"
    }
    metallic_noise = next(node for node in graph["nodes"] if node["label"] == "Rumore metallico")
    assert len(metallic_noise["evidence_ids"]) == 2
    assert {item["label"] for item in graph["evidence"]} >= {"Riga 2", "Riga 4"}
    assert graph["validation"]["passed"] is True
    assert graph["validation"]["required_properties_total"] == graph["validation"]["required_properties_present"]
    assert graph["validation"]["extra_properties"] == 0
    assert graph["validation"]["domain_range_errors"] == 0
    assert graph["validation"]["endpoint_errors"] == 0
    assert graph["validation"]["duplicate_ids"] == 0
    assert graph["validation"]["provenance_total"] == graph["validation"]["provenance_resolvable"]
    assert graph["approval_eligible"] is True
    assert view["merge_barrier"]["state"] == "waiting_for_approval"

    approved = foundation_client.post(
        f"/api/g3/subgraphs/{graph['source_subgraph_revision_id']}/decision",
        json={"action": "approve"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["sources"][0]["state"] == "approved"
    assert approved.json()["merge_barrier"]["state"] == "ready"


def test_g3_requires_source_by_source_approval_before_cross_source_matching(
    foundation_client,
    machine_payload,
):
    workspace_id = _workspace(foundation_client, machine_payload)
    first = _upload_csv(foundation_client, workspace_id, "synthetic_press_events_it.csv")
    second = _upload_csv(foundation_client, workspace_id, "synthetic_press_events_en.csv")
    _prepare_and_confirm_all(foundation_client, workspace_id)

    for source in (first, second):
        response = foundation_client.post(
            f"/api/workspaces/{workspace_id}/g3/sources/{source['source_id']}/generate"
        )
        assert response.status_code == 200, response.text
    view = response.json()
    assert view["merge_barrier"]["state"] == "waiting_for_approval"
    assert view["merge_barrier"]["exact_matches"] == []

    revisions = {item["source_id"]: item["subgraph"] for item in view["sources"]}
    first_approval = foundation_client.post(
        f"/api/g3/subgraphs/{revisions[first['source_id']]['source_subgraph_revision_id']}/decision",
        json={"action": "approve"},
    )
    assert first_approval.json()["merge_barrier"]["state"] == "waiting_for_approval"
    assert first_approval.json()["merge_barrier"]["exact_matches"] == []

    second_approval = foundation_client.post(
        f"/api/g3/subgraphs/{revisions[second['source_id']]['source_subgraph_revision_id']}/decision",
        json={"action": "approve"},
    )
    assert second_approval.status_code == 200, second_approval.text
    result = second_approval.json()
    assert result["merge_barrier"]["state"] == "ready"
    assert any(item["label"] == "E-PUMP-17" for item in result["merge_barrier"]["exact_matches"])


def test_g3_rejection_requires_a_human_note(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload_csv(foundation_client, workspace_id, "synthetic_press_events_it.csv")
    _prepare_and_confirm_all(foundation_client, workspace_id)
    view = foundation_client.post(
        f"/api/workspaces/{workspace_id}/g3/sources/{source['source_id']}/generate"
    ).json()
    revision_id = view["sources"][0]["subgraph"]["source_subgraph_revision_id"]

    missing_note = foundation_client.post(
        f"/api/g3/subgraphs/{revision_id}/decision", json={"action": "reject"}
    )
    assert missing_note.status_code == 409
    rejected = foundation_client.post(
        f"/api/g3/subgraphs/{revision_id}/decision",
        json={"action": "reject", "note": "La relazione tra rumore e causa non è convincente."},
    )
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["sources"][0]["state"] == "rejected"
    assert rejected.json()["merge_barrier"]["state"] == "waiting_for_approval"


def test_g3_classifies_missing_cause_and_blocks_approval(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    fixture = HARDENING_FIXTURES / "incomplete_no_cause.csv"
    source = _upload_csv(foundation_client, workspace_id, fixture)
    _prepare_and_confirm_all(foundation_client, workspace_id)

    generated = foundation_client.post(
        f"/api/workspaces/{workspace_id}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 200, generated.text
    graph = generated.json()["sources"][0]["subgraph"]
    assert graph["validation"]["passed"] is True
    assert graph["approval_eligible"] is False
    assert {item["code"] for item in graph["knowledge_gaps"]} == {"missing_failure_mode"}

    approval = foundation_client.post(
        f"/api/g3/subgraphs/{graph['source_subgraph_revision_id']}/decision", json={"action": "approve"}
    )
    assert approval.status_code == 409
    assert "lacune dichiarate" in approval.json()["detail"]


def test_g3_refuses_cartesian_links_for_multi_value_rows(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    fixture = HARDENING_FIXTURES / "ambiguous_relationship_pairs.csv"
    source = _upload_csv(foundation_client, workspace_id, fixture)
    _prepare_and_confirm_all(foundation_client, workspace_id)

    generated = foundation_client.post(
        f"/api/workspaces/{workspace_id}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 200, generated.text
    graph = generated.json()["sources"][0]["subgraph"]
    assert {relation["relation_type"] for relation in graph["relations"]} == {
        "HAS_COMPONENT", "GENERATES_ERROR",
    }
    assert {item["code"] for item in graph["knowledge_gaps"]} == {
        "ambiguous_symptom_cause_pairing",
        "ambiguous_cause_component_pairing",
        "ambiguous_cause_action_pairing",
        "ambiguous_error_cause_pairing",
    }
    assert graph["approval_eligible"] is False
