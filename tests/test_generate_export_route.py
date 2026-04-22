import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import app_config
from backend.graph.store import seed_graph_state
from backend.main import app
from backend.models import HumanRequiredField, PipelineIssue
from backend.routers.upload import pdf_store
from backend.services.run_metrics import ensure_run_metrics


class GenerateExportRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        pdf_store.clear()
        app_config._runtime_overrides.clear()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        pdf_store.clear()
        app_config._runtime_overrides.clear()

    def _store(self, pdf_id: str) -> dict:
        store = {
            "pdf_id": pdf_id,
            "filename": "manual.pdf",
            "pages": [
                {"page_number": 1, "text": "Troubleshooting content."},
                {"page_number": 2, "text": "Corrective action content."},
            ],
            "page_count": 2,
            "source_type": "Service manual",
            "source_title": "Mock Robot",
            "selected_models": {
                "scoping": None,
                "ontology_draft": None,
                "extraction": None,
            },
        }
        ensure_run_metrics(store)
        seed_graph_state(store, pdf_id)
        return store

    @patch(
        "backend.routers.generate.persist_export_metrics",
        return_value={"target_path": "/tmp/metrics.json", "filename": "metrics.json"},
    )
    @patch(
        "backend.routers.generate.persist_exported_ontology",
        return_value={
            "target_path": "/tmp/mock_export.json",
            "filename": "ontology.json",
            "download_filename": "mock_export.json",
            "metrics_path": "/tmp/metrics.json",
            "directory_name": "manual",
        },
    )
    @patch(
        "backend.routers.generate.cleanup_export_ontology",
        side_effect=lambda ontology, target_language, model_name: (ontology, {}, {}),
    )
    def test_generate_json_does_not_block_on_warning_only_schema_issues(
        self,
        _mock_cleanup,
        _mock_persist_ontology,
        _mock_persist_metrics,
    ) -> None:
        pdf_store["pdf-warning"] = self._store("pdf-warning")

        response = self.client.post("/generate-json", json={
            "pdf_id": "pdf-warning",
            "validated_triplets": [
                {
                    "symptom": {
                        "symptom_id": "SYM-001",
                        "name": "Robot does not start",
                        "description": "Startup failure",
                        "severity": "High",
                    },
                    "failure_modes": [
                        {
                            "failure_mode_id": "FM-001",
                            "name": "Power board fault",
                            "description": "Board failure",
                            "material_context": "Power board",
                            "linked_symptom_id": "SYM-001",
                        },
                    ],
                    "corrective_actions": [
                        {
                            "action_id": "CA-001",
                            "name": "Replace power board",
                            "description": "Replace faulty board",
                            "instruction_text": "1. Install a new board. 2. Reboot.",
                            "source_type": "Service manual",
                            "source_title": "Mock Robot",
                            "source_page": 1,
                            "linked_failure_mode_id": "FM-001",
                        },
                    ],
                },
            ],
            "target_language": "en",
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["nodes"]["FailureMode"][0]["material_context"], "Power board")
        self.assertTrue(response.headers["content-disposition"].endswith("filename=mock_export.json"))
        self.assertEqual(response.headers["x-export-warnings-count"], "0")

    @patch(
        "backend.routers.generate.persist_export_metrics",
        return_value={"target_path": "/tmp/metrics.json", "filename": "metrics.json"},
    )
    @patch(
        "backend.routers.generate.persist_exported_ontology",
        return_value={
            "target_path": "/tmp/mock_export.json",
            "filename": "ontology.json",
            "download_filename": "mock_export.json",
            "metrics_path": "/tmp/metrics.json",
            "directory_name": "manual",
        },
    )
    @patch(
        "backend.routers.generate.cleanup_export_ontology",
        side_effect=lambda ontology, target_language, model_name: (ontology, {}, {}),
    )
    @patch(
        "backend.routers.generate.validate_ontology_instance",
        return_value=(
            [
                PipelineIssue(
                    severity="error",
                    code="empty_draft_content",
                    message="No substantive content.",
                    target_type="ontology",
                    fix_hint="Export anyway.",
                )
            ],
            [
                HumanRequiredField(
                    field_key="Component::*::category",
                    prompt="Provide the category.",
                    target_type="Component",
                    target_id="*",
                    property_name="category",
                    reason="Required by ontology schema but missing from the draft.",
                )
            ],
        ),
    )
    def test_generate_json_exports_best_effort_even_with_blocking_schema_issues(
        self,
        _mock_validate,
        _mock_cleanup,
        _mock_persist_ontology,
        _mock_persist_metrics,
    ) -> None:
        pdf_store["pdf-best-effort"] = self._store("pdf-best-effort")

        response = self.client.post("/generate-json", json={
            "pdf_id": "pdf-best-effort",
            "validated_triplets": [
                {
                    "symptom": {
                        "symptom_id": "SYM-001",
                        "name": "Robot does not start",
                        "description": "Startup failure",
                        "severity": "High",
                    },
                    "failure_modes": [
                        {
                            "failure_mode_id": "FM-001",
                            "name": "Power board fault",
                            "description": "Board failure",
                            "material_context": "Power board",
                            "linked_symptom_id": "SYM-001",
                        },
                    ],
                    "corrective_actions": [
                        {
                            "action_id": "CA-001",
                            "name": "Replace power board",
                            "description": "Replace faulty board",
                            "instruction_text": "1. Install a new board. 2. Reboot.",
                            "source_type": "Service manual",
                            "source_title": "Mock Robot",
                            "source_page": 1,
                            "linked_failure_mode_id": "FM-001",
                        },
                    ],
                },
            ],
            "target_language": "en",
        })

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(int(response.headers["x-export-warnings-count"]), 0)


if __name__ == "__main__":
    unittest.main()
