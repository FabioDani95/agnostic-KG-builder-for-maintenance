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


if __name__ == "__main__":
    unittest.main()
