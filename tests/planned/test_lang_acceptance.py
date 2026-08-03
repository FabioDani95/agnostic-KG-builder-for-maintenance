from __future__ import annotations

from tests.planned.test_g2_acceptance import _start, _upload, _workspace


def _language_evidence(foundation_client, machine_payload):
    workspace_id = _workspace(foundation_client, machine_payload)
    source = _upload(
        foundation_client,
        workspace_id,
        "languages.csv",
        (
            "event_id,language,symptom_observation,action_taken\n"
            "E1,EN,abnormal noise,inspect bearing\n"
            "E2,IT,rumore anomalo,ispezionare cuscinetto\n"
            "E3,DE,ungewoehnliches Geraeusch,Lager pruefen\n"
            "E4,MIXED,rumore and noise,inspect e controllare\n"
        ).encode(),
        "text/csv",
    )
    result = _start(foundation_client, workspace_id)
    assert result["state"] == "ready"
    assert result["profiles"][0]["summary"]["language_counts"] == {
        "qualified_en": 1,
        "unqualified_it": 1,
        "unqualified_de": 1,
        "mixed": 1,
    }
    return foundation_client.get(
        f"/api/workspaces/{workspace_id}/evidence", params={"source_id": source["source_id"]}
    ).json()


def test_ac_lang_001(foundation_client, machine_payload):
    evidence = _language_evidence(foundation_client, machine_payload)
    english = next(item for item in evidence if item["attributes"]["language"] == "EN")
    assert english["language"] == {
        "detected": "en",
        "confidence": 1.0,
        "qualification": "qualified_en",
    }


def test_ac_lang_002(foundation_client, machine_payload):
    evidence = _language_evidence(foundation_client, machine_payload)
    qualifications = {
        item["attributes"]["language"]: item["language"]["qualification"] for item in evidence
    }
    assert qualifications == {
        "EN": "qualified_en",
        "IT": "unqualified_it",
        "DE": "unqualified_de",
        "MIXED": "mixed",
    }
    assert any(item["content"]["observation"] == "rumore anomalo" for item in evidence)
