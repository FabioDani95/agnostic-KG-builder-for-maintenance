import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.upload import pdf_store


def _sample_export_payload() -> dict:
    return {
        "metadata": {
            "product_name": "Mock Manual",
            "product_short_name": "mock",
            "product_type": "manual",
            "domain_topics": ["maintenance"],
            "version": "1.0",
            "file_version": "1.0",
            "total_nodes": 2,
            "total_relationships": 1,
        },
        "nodes": {
            "Component": [
                {
                    "component_id": "CMP-001",
                    "name": "Main Pump",
                    "description": "Pump description",
                    "category": "Hydraulics",
                }
            ],
            "FailureMode": [
                {
                    "failure_mode_id": "FM-001",
                    "name": "Pump Wear",
                    "description": "Wear",
                    "material_context": "Hydraulic circuit",
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


class ModifyRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.export_path = Path(self.tmpdir.name) / "ontology.json"
        self.export_path.write_text(
            json.dumps(_sample_export_payload(), indent=2),
            encoding="utf-8",
        )
        pdf_store.clear()
        pdf_store["pdf-modify"] = {
            "pdf_id": "pdf-modify",
            "ontology_path": str(self.export_path),
        }
        self.client = TestClient(app)

    def tearDown(self):
        pdf_store.clear()
        self.tmpdir.cleanup()

    def test_modify_page_renders_and_uses_modify_api_base(self):
        response = self.client.get("/modify/pdf-modify")
        self.assertEqual(response.status_code, 200)
        self.assertIn("/modify/pdf-modify/api", response.text)

    def test_modify_api_returns_graph_data(self):
        response = self.client.get("/modify/pdf-modify/api/data")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["node_types"], ["Component", "FailureMode"])
        self.assertEqual(payload["edge_types"], ["AFFECTS"])
        self.assertEqual(len(payload["nodes"]), 2)
        self.assertEqual(len(payload["edges"]), 1)

    def test_modify_api_creates_node_with_relationship(self):
        response = self.client.post(
            "/modify/pdf-modify/api/node/create",
            json={
                "node_type": "Symptom",
                "attributes": {
                    "symptom_id": "SYM-002",
                    "name": "Low pressure",
                    "description": "Pressure below threshold",
                    "severity": "High",
                },
                "relationships": [
                    {
                        "type": "MAY_INDICATE",
                        "from_id": "SYM-002",
                        "to_id": "FM-001",
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["node_id"], "SYM-002")
        self.assertEqual(payload["vis_node"]["label"], "Low pressure")
        self.assertEqual(payload["edges"][0]["label"], "MAY_INDICATE")

        graph_response = self.client.get("/modify/pdf-modify/api/data")
        graph = graph_response.json()
        self.assertEqual(len(graph["nodes"]), 3)
        self.assertEqual(len(graph["edges"]), 2)

    def test_modify_api_polishes_node_fields_deterministically(self):
        response = self.client.post(
            "/modify/pdf-modify/api/node/polish",
            json={
                "node_type": "Component",
                "attributes": {
                    "name": " main pump ",
                    "description": "  pump   mounted in hydraulic circuit ",
                    "category": "Hydraulics",
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["attributes"]["name"], "Main pump")
        self.assertEqual(
            response.json()["attributes"]["description"],
            "Pump mounted in hydraulic circuit.",
        )

    def test_modify_api_drafts_node_from_text_and_suggests_links(self):
        draft_response = self.client.post(
            "/modify/pdf-modify/api/node/draft-from-text",
            json={
                "text": "Low hydraulic pressure appears during startup and may indicate pump wear.",
                "preferred_type": "Symptom",
                "agentic": False,
            },
        )

        self.assertEqual(draft_response.status_code, 200)
        draft = draft_response.json()
        self.assertEqual(draft["node_type"], "Symptom")
        self.assertEqual(draft["attributes"]["symptom_id"], "SYM-001")
        self.assertEqual(draft["attributes"]["severity"], "Low")
        self.assertFalse(draft["missing_fields"])

        suggest_response = self.client.post(
            "/modify/pdf-modify/api/relationship/suggest",
            json={
                "node_type": draft["node_type"],
                "attributes": draft["attributes"],
                "limit": 3,
                "agentic": False,
            },
        )

        self.assertEqual(suggest_response.status_code, 200)
        suggestions = suggest_response.json()["suggestions"]
        self.assertTrue(suggestions)
        self.assertEqual(suggestions[0]["relation_type"], "MAY_INDICATE")
        self.assertEqual(suggestions[0]["target_id"], "FM-001")


if __name__ == "__main__":
    unittest.main()
