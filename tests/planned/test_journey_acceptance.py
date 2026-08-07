from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parents[1] / "fixtures"


def _workspace(client, machine_payload) -> str:
    response = client.post("/api/workspace", json=machine_payload)
    assert response.status_code == 201, response.text
    return response.json()["workspace"]["workspace_id"]


def _upload(client, workspace_id: str, name: str, payload: bytes, media_type: str):
    response = client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "operational"},
        files={"file": (name, payload, media_type)},
    )
    assert response.status_code == 200, response.text
    return response.json()["source"]


def _prepare_and_confirm(client, workspace_id: str) -> None:
    preparation = client.post(f"/api/workspaces/{workspace_id}/g2/preparation")
    assert preparation.status_code == 200, preparation.text
    for profile in preparation.json()["profiles"]:
        response = client.post(f"/api/g2/profiles/{profile['profile_id']}/confirm")
        assert response.status_code == 200, response.text


def _phases(journey: dict) -> dict[str, dict]:
    return {item["phase"]: item for item in journey["phases"]}


def test_journey_guides_an_empty_workspace(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)

    response = foundation_client.get(f"/api/workspaces/{workspace_id}/journey")

    assert response.status_code == 200, response.text
    journey = response.json()
    phases = _phases(journey)
    assert phases["machine"] == {
        "phase": "machine", "state": "complete", "available": True,
        "count": 0, "attention_count": 0,
    }
    assert phases["documents"]["state"] == "needs_attention"
    assert phases["structure"]["state"] == "locked"
    assert phases["structure"]["available"] is False
    assert phases["graph"]["state"] == "locked"
    assert journey["next_action"] == {
        "code": "add_source", "phase": "documents",
        "source_id": None, "source_name": None,
    }


def test_journey_keeps_an_existing_graph_available_when_a_new_source_arrives(
    foundation_client,
    machine_payload,
):
    workspace_id = _workspace(foundation_client, machine_payload)
    first_path = FIXTURES / "g3" / "synthetic_press_events_it.csv"
    first = _upload(
        foundation_client, workspace_id, first_path.name,
        first_path.read_bytes(), "text/csv",
    )
    _prepare_and_confirm(foundation_client, workspace_id)
    generated = foundation_client.post(
        f"/api/workspaces/{workspace_id}/g3/sources/{first['source_id']}/generate"
    )
    assert generated.status_code == 200, generated.text
    revision = generated.json()["sources"][0]["subgraph"]
    approved = foundation_client.post(
        f"/api/g3/subgraphs/{revision['source_subgraph_revision_id']}/decision",
        json={"action": "approve"},
    )
    assert approved.status_code == 200, approved.text

    complete = foundation_client.get(
        f"/api/workspaces/{workspace_id}/journey"
    ).json()
    assert complete["next_action"]["code"] == "workspace_ready"
    assert _phases(complete)["graph"]["state"] == "complete"
    assert complete["sources"][0]["graph_revision_count"] == 1

    second_path = FIXTURES / "g3" / "synthetic_press_events_en.csv"
    second = _upload(
        foundation_client, workspace_id, second_path.name,
        second_path.read_bytes(), "text/csv",
    )
    reopened = foundation_client.get(
        f"/api/workspaces/{workspace_id}/journey"
    ).json()

    assert reopened["next_action"]["code"] == "prepare_source"
    assert reopened["next_action"]["source_id"] == second["source_id"]
    assert _phases(reopened)["structure"]["state"] == "in_progress"
    assert _phases(reopened)["graph"]["available"] is True
    assert _phases(reopened)["graph"]["state"] == "in_progress"
    old_source = next(item for item in reopened["sources"] if item["source_id"] == first["source_id"])
    assert old_source["graph_state"] == "approved"
    assert old_source["graph_revision_id"] == revision["source_subgraph_revision_id"]


def test_archiving_and_restoring_preserves_the_graph_revision(
    foundation_client,
    machine_payload,
):
    workspace_id = _workspace(foundation_client, machine_payload)
    source_path = FIXTURES / "g3" / "synthetic_press_events_it.csv"
    source = _upload(
        foundation_client, workspace_id, source_path.name,
        source_path.read_bytes(), "text/csv",
    )
    _prepare_and_confirm(foundation_client, workspace_id)
    generated = foundation_client.post(
        f"/api/workspaces/{workspace_id}/g3/sources/{source['source_id']}/generate"
    ).json()
    revision_id = generated["sources"][0]["subgraph"]["source_subgraph_revision_id"]

    archived = foundation_client.delete(f"/api/sources/{source['source_id']}")
    assert archived.status_code == 204, archived.text
    archived_journey = foundation_client.get(
        f"/api/workspaces/{workspace_id}/journey"
    ).json()
    archived_source = archived_journey["sources"][0]
    assert archived_source["lifecycle"] == "archived"
    assert archived_source["graph_revision_id"] == revision_id
    assert archived_source["graph_revision_count"] == 1
    assert archived_journey["next_action"]["code"] == "add_source"

    restored = foundation_client.post(f"/api/sources/{source['source_id']}/restore")
    assert restored.status_code == 200, restored.text
    restored_journey = foundation_client.get(
        f"/api/workspaces/{workspace_id}/journey"
    ).json()
    restored_source = restored_journey["sources"][0]
    assert restored_source["lifecycle"] == "active"
    assert restored_source["graph_revision_id"] == revision_id
    assert restored_source["graph_revision_count"] == 1


def test_pdf_only_workspace_offers_graph_generation(
    foundation_client,
    machine_payload,
):
    workspace_id = _workspace(foundation_client, machine_payload)
    pdf_path = FIXTURES / "manuals" / "g1_pdf_inventory.pdf"
    source = _upload(
        foundation_client, workspace_id, pdf_path.name,
        pdf_path.read_bytes(), "application/pdf",
    )

    journey = foundation_client.get(
        f"/api/workspaces/{workspace_id}/journey"
    ).json()
    phases = _phases(journey)
    assert phases["structure"]["state"] == "complete"
    assert phases["graph"]["state"] == "needs_attention"
    assert phases["graph"]["available"] is True
    pdf_source = next(item for item in journey["sources"] if item["source_id"] == source["source_id"])
    assert pdf_source["structure_state"] == "not_applicable"
    assert pdf_source["graph_state"] == "ready"
    assert journey["next_action"] == {
        "code": "generate_graph",
        "phase": "graph",
        "source_id": source["source_id"],
        "source_name": pdf_path.name,
    }
