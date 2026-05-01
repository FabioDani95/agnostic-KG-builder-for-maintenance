import json
from pathlib import Path
from types import SimpleNamespace

from backend.services import graph_editor_session


class FakeOpenAIClient:
    def __init__(self, payload):
        self.payload = payload
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    def _create(self, **_kwargs):
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(self.payload))
                )
            ]
        )


def _write_ontology(path: Path):
    path.write_text(
        json.dumps(
            {
                "metadata": {
                    "product_name": "Mock Manual",
                    "product_short_name": "mock",
                    "product_type": "manual",
                    "domain_topics": ["maintenance"],
                    "version": "1.0",
                    "file_version": "1.0",
                    "total_nodes": 3,
                    "total_relationships": 1,
                },
                "nodes": {
                    "Component": [
                        {
                            "component_id": "CMP-001",
                            "name": "Main Pump",
                            "description": "Hydraulic pump",
                            "category": "Hydraulics",
                        }
                    ],
                    "Symptom": [
                        {
                            "symptom_id": "SYM-001",
                            "name": "Low pressure",
                            "description": "Pressure below threshold",
                            "severity": "Low",
                        }
                    ],
                    "FailureMode": [
                        {
                            "failure_mode_id": "FM-001",
                            "name": "Pump wear",
                            "description": "Pump wear causes low hydraulic pressure",
                            "material_context": "Hydraulics",
                        }
                    ],
                },
                "relationships": [
                    {
                        "type": "AFFECTS",
                        "from_id": "FM-001",
                        "to_id": "CMP-001",
                        "evidence": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_llm_draft_is_normalized_by_schema(tmp_path):
    path = tmp_path / "ontology.json"
    _write_ontology(path)
    fake_client = FakeOpenAIClient(
        {
            "node_type": "Symptom",
            "attributes": {
                "symptom_id": "SYM-001",
                "name": "Hydraulic pressure drops",
                "description": "Pressure drops during pump startup.",
                "severity": "High",
                "not_in_schema": "discard me",
            },
            "rationale": "The note describes an observable condition.",
        }
    )

    result = graph_editor_session.draft_node_from_text(
        path,
        "Hydraulic pressure drops during pump startup.",
        llm_client=fake_client,
    )

    assert result["agent_mode"] == "llm_symbolic"
    assert result["node_type"] == "Symptom"
    assert result["attributes"]["symptom_id"] == "SYM-002"
    assert result["attributes"]["name"] == "Hydraulic pressure drops"
    assert "not_in_schema" not in result["attributes"]
    assert result["missing_fields"] == []


def test_llm_link_ranking_is_constrained_to_symbolic_candidates(tmp_path):
    path = tmp_path / "ontology.json"
    _write_ontology(path)
    fake_client = FakeOpenAIClient(
        {
            "suggestions": [
                {
                    "candidate_id": "c0",
                    "confidence": 0.91,
                    "reason": "The symptom and failure mode share hydraulic pressure context.",
                }
            ]
        }
    )

    result = graph_editor_session.suggest_relationships(
        path,
        "Symptom",
        {
            "symptom_id": "SYM-002",
            "name": "Hydraulic pressure drops",
            "description": "Pressure drops during pump startup.",
            "severity": "High",
        },
        limit=3,
        llm_client=fake_client,
    )

    assert result["agent_mode"] == "llm_symbolic"
    assert result["suggestions"][0]["relation_type"] == "MAY_INDICATE"
    assert result["suggestions"][0]["target_id"] == "FM-001"
    assert result["suggestions"][0]["confidence"] == 0.91
