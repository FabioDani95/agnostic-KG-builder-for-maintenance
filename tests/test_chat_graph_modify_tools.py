import asyncio
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from backend.models import OntologyInstance, OntologyPipelineResponse
from backend.services.conversation.tools import dispatch
from backend.services.run_metrics import ensure_run_metrics, record_stage_metrics


def _sample_ontology_instance() -> OntologyInstance:
    return OntologyInstance(
        ontology_name="Test Graph",
        version="1.0",
        language="en",
        source_type="manual",
        source_title="Mock Manual",
        nodes={
            "Asset": [
                {
                    "asset_id": "ASSET-001",
                    "name": "Mock Machine",
                    "description": "Machine under test",
                    "brand": "OpenAI",
                    "model": "M1",
                }
            ],
            "Component": [
                {
                    "component_id": "CMP-001",
                    "name": "Main Pump",
                    "description": "Original pump description",
                    "category": "Hydraulics",
                }
            ],
            "FailureMode": [
                {
                    "failure_mode_id": "FM-001",
                    "name": "Pump Wear",
                    "description": "Pump wear detected",
                    "material_context": "Hydraulic circuit",
                }
            ],
        },
        relations=[
            {
                "name": "AFFECTS",
                "from_type": "FailureMode",
                "from_id": "FM-001",
                "to_type": "Component",
                "to_id": "CMP-001",
                "evidence": [],
            }
        ],
    )


def _export_payload_from_ontology(ontology: OntologyInstance) -> dict:
    return {
        "metadata": {
            "product_name": ontology.source_title,
            "product_short_name": "mock",
            "product_type": ontology.source_type,
            "domain_topics": ["maintenance"],
            "version": ontology.version,
            "file_version": "1.0",
            "total_nodes": sum(len(items) for items in ontology.nodes.values()),
            "total_relationships": len(ontology.relations),
        },
        "nodes": ontology.model_dump()["nodes"],
        "relationships": [
            {
                "type": rel["name"],
                "from_id": rel["from_id"],
                "to_id": rel["to_id"],
                "evidence": rel.get("evidence", []),
            }
            for rel in ontology.model_dump()["relations"]
        ],
    }


class ChatGraphModifyToolsTests(unittest.TestCase):
    def test_export_tool_registers_modify_workspace(self):
        ontology = _sample_ontology_instance()
        pipeline_result = OntologyPipelineResponse(
            status="ready",
            ontology=ontology,
            resolution_completion_report={
                "target_count": 2,
                "attempted": 2,
                "completed": 1,
                "attempts": [{"target_id": "FM-001", "status": "completed", "pages": [4]}],
            },
        )

        with TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "ontology.json"
            conversation_path = Path(tmpdir) / "conversation.json"
            store = {
                "pdf_id": "pdf-1",
                "filename": "mock-manual.pdf",
                "conversation": {"messages": [{"role": "assistant", "content": "done"}]},
                "validated_triplets": [],
                "target_language": "en",
                "ontology_pipeline": pipeline_result.model_dump(),
            }
            ensure_run_metrics(store)
            record_stage_metrics(
                store,
                "extraction",
                {
                    "stage": "extraction",
                    "duration_seconds": 4.2,
                    "llm_calls": 2,
                    "prompt_tokens": 1000,
                    "cached_prompt_tokens": 0,
                    "non_cached_prompt_tokens": 1000,
                    "completion_tokens": 240,
                    "total_tokens": 1240,
                    "estimated_cost_usd": 0.0041,
                    "details": {"triplet_count": 2, "selected_pages": 3},
                    "by_model": {
                        "gpt-5.4": {
                            "label": "GPT-5.4",
                            "llm_calls": 2,
                            "prompt_tokens": 1000,
                            "cached_prompt_tokens": 0,
                            "non_cached_prompt_tokens": 1000,
                            "completion_tokens": 240,
                            "total_tokens": 1240,
                            "estimated_cost_usd": 0.0041,
                        }
                    },
                },
            )

            def fake_persist(payload, pdf_id, manual_filename=None):
                export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
                return {
                    "target_path": str(export_path),
                    "filename": "ontology.json",
                    "download_filename": "mock-manual_ontology.json",
                    "metrics_path": str(Path(tmpdir) / "metrics.json"),
                }

            with patch(
                "backend.services.pipeline_actions.get_current_ontology",
                return_value=pipeline_result,
            ), patch(
                "backend.services.style_cleanup_service.cleanup_export_ontology",
                side_effect=lambda ontology_dict, target_language="en": (ontology_dict, {}, {}),
            ), patch(
                "backend.services.ontology_export_store.prepare_exported_ontology",
                side_effect=lambda data: _export_payload_from_ontology(ontology),
            ), patch(
                "backend.services.ontology_export_store.persist_exported_ontology",
                side_effect=fake_persist,
            ), patch(
                "backend.services.ontology_export_store.persist_export_metrics",
                return_value={"target_path": str(Path(tmpdir) / "metrics.json"), "filename": "metrics.json"},
            ), patch(
                "backend.graph.store._record_phase",
                return_value=None,
            ):
                result = asyncio.run(dispatch("export_ontology", {}, store, None))

            self.assertEqual(result["status"], "ok")
            self.assertTrue(result["exported"])
            self.assertEqual(result["editor_url"], "/modify/pdf-1")
            self.assertEqual(store["ontology_path"], str(export_path))
            self.assertIn("metrics", result)
            self.assertEqual(result["metrics"]["review"]["validated_triplets"], 0)
            self.assertTrue(export_path.exists())
            self.assertTrue(conversation_path.exists())

    def test_get_run_metrics_returns_full_kpi_widget_payload(self):
        ontology = _sample_ontology_instance()
        pipeline_result = OntologyPipelineResponse(
            status="ready",
            ontology=ontology,
            resolution_completion_report={
                "target_count": 2,
                "attempted": 2,
                "completed": 1,
                "attempts": [{"target_id": "FM-001", "status": "completed", "pages": [4]}],
            },
        )
        store = {
            "pdf_id": "pdf-metrics",
            "filename": "mock-manual.pdf",
            "page_count": 8,
            "validated_triplets": [{"id": "t1"}],
            "ontology_pipeline": pipeline_result.model_dump(),
        }
        ensure_run_metrics(store)
        record_stage_metrics(
            store,
            "scoping",
            {
                "stage": "scoping",
                "duration_seconds": 3.0,
                "llm_calls": 1,
                "prompt_tokens": 500,
                "cached_prompt_tokens": 0,
                "non_cached_prompt_tokens": 500,
                "completion_tokens": 80,
                "total_tokens": 580,
                "estimated_cost_usd": 0.0015,
                "details": {"selected_pages": 2, "total_pages": 8},
                "by_model": {
                    "gpt-5.4": {
                        "label": "GPT-5.4",
                        "llm_calls": 1,
                        "prompt_tokens": 500,
                        "cached_prompt_tokens": 0,
                        "non_cached_prompt_tokens": 500,
                        "completion_tokens": 80,
                        "total_tokens": 580,
                        "estimated_cost_usd": 0.0015,
                    }
                },
            },
        )
        record_stage_metrics(
            store,
            "extraction",
            {
                "stage": "extraction",
                "duration_seconds": 5.0,
                "llm_calls": 2,
                "prompt_tokens": 1200,
                "cached_prompt_tokens": 0,
                "non_cached_prompt_tokens": 1200,
                "completion_tokens": 220,
                "total_tokens": 1420,
                "estimated_cost_usd": 0.0049,
                "details": {"triplet_count": 3, "selected_pages": 2},
                "by_model": {
                    "gpt-5.4": {
                        "label": "GPT-5.4",
                        "llm_calls": 2,
                        "prompt_tokens": 1200,
                        "cached_prompt_tokens": 0,
                        "non_cached_prompt_tokens": 1200,
                        "completion_tokens": 220,
                        "total_tokens": 1420,
                        "estimated_cost_usd": 0.0049,
                    }
                },
            },
        )

        result = asyncio.run(dispatch("get_run_metrics", {}, store, None))

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["widget"], "run_metrics")
        self.assertEqual(result["metrics"]["review"]["validated_triplets"], 1)
        self.assertEqual(result["metrics"]["review"]["discarded_triplets"], 2)
        self.assertEqual(result["metrics"]["nodes_by_type"]["FailureMode"], 1)
        self.assertEqual(result["metrics"]["resolution_completion"]["completed"], 1)
        self.assertGreater(result["metrics"]["totals"]["estimated_cost_usd"], 0)

    def test_graph_tools_can_inspect_modify_and_save_exported_workspace(self):
        ontology = _sample_ontology_instance()
        payload = _export_payload_from_ontology(ontology)

        with TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "ontology.json"
            export_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            store = {
                "pdf_id": "pdf-graph",
                "ontology_path": str(export_path),
            }

            inspect_result = asyncio.run(
                dispatch("inspect_exported_graph", {"query": "pump"}, store, None)
            )
            self.assertEqual(inspect_result["status"], "ok")
            self.assertEqual(inspect_result["matches"][0]["id"], "CMP-001")

            update_result = asyncio.run(
                dispatch(
                    "update_exported_node",
                    {
                        "node_id": "CMP-001",
                        "attributes": {"description": "Updated pump description"},
                    },
                    store,
                    None,
                )
            )
            self.assertEqual(update_result["status"], "ok")
            self.assertEqual(update_result["widget"], "modify_workspace_sync")

            node_result = asyncio.run(
                dispatch("inspect_exported_graph", {"node_id": "CMP-001"}, store, None)
            )
            self.assertEqual(node_result["status"], "ok")
            self.assertEqual(
                node_result["node"]["attributes"]["description"],
                "Updated pump description",
            )

            save_result = asyncio.run(dispatch("save_exported_graph", {}, store, None))
            self.assertEqual(save_result["status"], "ok")
            saved_payload = json.loads(export_path.read_text(encoding="utf-8"))
            component = next(
                item
                for item in saved_payload["nodes"]["Component"]
                if item["component_id"] == "CMP-001"
            )
            self.assertEqual(component["description"], "Updated pump description")


if __name__ == "__main__":
    unittest.main()
