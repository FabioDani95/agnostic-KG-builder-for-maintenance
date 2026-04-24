import unittest
from unittest.mock import patch

from backend.graph.state import GraphPhase
from backend.models import CutPlan
from backend.services.conversation.critic import critique_ontology_draft
from backend.services.conversation.tools import _build_ontology_review_payload
from backend.services.conversation.tools import _build_triplet_graph_payload
from backend.services.conversation.tools import _explain_decision
from backend.services.conversation.tools import _propose_cut_plan
from backend.services.conversation.tools import build_extraction_memory_snapshot
from backend.services.conversation.tools import dispatch


class ChatToolStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_explain_decision_returns_concrete_page_and_section_facts(self):
        store = {
            "pages": [{"page_number": i} for i in range(1, 115)],
            "cut_plan": {
                "total_pages": 114,
                "pages_to_keep": list(range(12, 94)),
                "sections": [
                    {"name": "Troubleshooting", "start": 12, "end": 54},
                    {"name": "Electrical diagrams", "start": 55, "end": 93},
                ],
            },
            "graph_state": {
                "current_phase": GraphPhase.SCOPING.value,
                "selected_pages": list(range(12, 60)),
                "phase_history": [{"phase": "scoping", "decision": "selected 82 pages"}],
            },
        }

        result = await _explain_decision(
            {"topic": "why was page 20 included in Troubleshooting?"},
            store,
            None,
        )

        self.assertEqual(result["status"], "ok")
        self.assertIn("Selected pages: 82/114", result["context"])
        self.assertIn("Page 20 is currently selected", result["context"])
        self.assertIn("Troubleshooting (12-54)", result["context"])
        self.assertIn("Section 'Troubleshooting' is currently selected from page 12 to 54.", result["context"])

    async def test_propose_cut_plan_preserves_zero_page_offset(self):
        captured_offsets = []

        def fake_create_cut_plan(store, req, on_event=None):
            captured_offsets.append(req.page_offset)
            return CutPlan(
                pdf_id=req.pdf_id,
                total_pages=12,
                sections=[],
                pages_to_keep=[8],
                page_offset=req.page_offset,
                skipped=False,
            )

        store = {
            "pdf_id": "pdf-1",
            "page_offset": 0,
            "selected_models": {"scoping": "mock-model"},
            "pages": [{"page_number": page_number, "text": ""} for page_number in range(1, 13)],
        }

        with patch(
            "backend.services.scoping_workflow.create_cut_plan_workflow",
            side_effect=fake_create_cut_plan,
        ):
            result = await _propose_cut_plan({}, store, None)

        self.assertEqual(captured_offsets, [0])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(store["graph_state"]["scoping_metadata"]["page_offset"], 0)

    async def test_list_extracted_nodes_returns_names_and_types_from_current_state(self):
        store = {
            "ontology_pipeline": {
                "ontology": {
                    "nodes": {
                        "Asset": [
                            {
                                "asset_id": "ASSET-001",
                                "name": "VB Series Machine",
                                "description": "Machine covered by the manual.",
                            }
                        ],
                        "Symptom": [
                            {
                                "symptom_id": "SYM-001",
                                "name": "Axis Backlash",
                                "description": "Axis backlash is detected.",
                            }
                        ],
                    }
                }
            },
            "graph_state": {
                "cleaned_triplets": [
                    {
                        "symptom": {"symptom_id": "SYM-001", "name": "Axis Backlash"},
                        "failure_modes": [
                            {
                                "failure_mode_id": "FM-001",
                                "name": "Compensation Mismatch",
                            }
                        ],
                        "corrective_actions": [
                            {
                                "action_id": "CA-001",
                                "name": "Adjust Backlash Compensation",
                            }
                        ],
                    }
                ]
            },
        }

        result = await dispatch(
            "list_extracted_nodes",
            {"limit": 20, "include_descriptions": True},
            store,
            None,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["total_nodes"], 4)
        self.assertEqual(result["node_type_counts"]["Asset"], 1)
        self.assertEqual(result["node_type_counts"]["Symptom"], 1)
        self.assertEqual(result["node_type_counts"]["FailureMode"], 1)
        self.assertEqual(result["node_type_counts"]["CorrectiveAction"], 1)
        self.assertIn("VB Series Machine", result["message"])
        self.assertIn("Axis Backlash", result["message"])

    async def test_list_extracted_triplets_reports_review_chain(self):
        store = {
            "review_index": 1,
            "validated_triplets": [],
            "graph_state": {
                "cleaned_triplets": [
                    {
                        "symptom": {"symptom_id": "SYM-001", "name": "Axis Backlash"},
                        "failure_modes": [
                            {
                                "failure_mode_id": "FM-001",
                                "name": "Compensation Mismatch",
                            }
                        ],
                        "corrective_actions": [
                            {
                                "action_id": "CA-001",
                                "name": "Adjust Backlash Compensation",
                                "linked_failure_mode_id": "FM-001",
                            }
                        ],
                    }
                ]
            },
        }

        result = await dispatch("list_extracted_triplets", {"status": "all"}, store, None)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["total_triplets"], 1)
        self.assertEqual(result["triplets"][0]["status"], "skipped")
        self.assertEqual(result["triplets"][0]["symptom"]["name"], "Axis Backlash")
        self.assertEqual(result["triplets"][0]["failure_modes"][0]["name"], "Compensation Mismatch")

    def test_extraction_memory_snapshot_keeps_compact_node_preview(self):
        store = {
            "ontology_pipeline": {
                "ontology": {
                    "nodes": {
                        "Asset": [{"asset_id": "ASSET-001", "name": "VB Series Machine"}],
                        "Symptom": [{"symptom_id": "SYM-001", "name": "Axis Backlash"}],
                    }
                }
            },
            "validated_triplets": [{"id": "t1"}],
            "review_index": 1,
            "graph_state": {"cleaned_triplets": [{"id": "t1"}, {"id": "t2"}]},
        }

        memory = build_extraction_memory_snapshot(store)

        self.assertEqual(memory["node_count"], 2)
        self.assertEqual(memory["node_type_counts"], {"Asset": 1, "Symptom": 1})
        self.assertEqual(memory["node_preview_by_type"]["Asset"], ["VB Series Machine (ASSET-001)"])
        self.assertEqual(memory["triplet_count"], 2)
        self.assertEqual(memory["validated_triplet_count"], 1)


class ChatToolPayloadTests(unittest.TestCase):
    def test_triplet_graph_payload_builds_full_graph_and_focus_metadata(self):
        triplets = [
            {
                "symptom": {
                    "symptom_id": "SYM-001",
                    "name": "Axis backlash",
                    "description": "Axis backlash detected.",
                    "severity": "Medium",
                    "evidence_page": 20,
                },
                "failure_modes": [
                    {
                        "failure_mode_id": "FM-001",
                        "name": "Backlash compensation mismatch",
                        "description": "Compensation is incorrect.",
                        "material_context": "Axis",
                        "linked_symptom_id": "SYM-001",
                        "evidence_page": 23,
                    }
                ],
                "corrective_actions": [
                    {
                        "action_id": "CA-001",
                        "name": "Adjust compensation",
                        "description": "Adjust backlash compensation.",
                        "instruction_text": "1. Measure. 2. Adjust.",
                        "source_type": "manual",
                        "source_title": "Mock",
                        "source_page": 24,
                        "linked_failure_mode_id": "FM-001",
                    }
                ],
            }
        ]

        payload = _build_triplet_graph_payload(triplets, focus_index=0)

        self.assertEqual(payload["triplet_count"], 1)
        self.assertEqual(len(payload["nodes"]), 3)
        self.assertEqual(len(payload["edges"]), 2)
        self.assertEqual(payload["focus_index"], 0)
        self.assertEqual(set(payload["focus_node_ids"]), {"SYM-001", "FM-001", "CA-001"})
        self.assertEqual(len(payload["focus_edge_ids"]), 2)

    def test_critique_ontology_draft_surfaces_candidate_relations_for_graph_issues(self):
        store = {
            "ontology_pipeline": {
                "ontology": {
                    "nodes": {
                        "Asset": [{"asset_id": "ASSET-001", "name": "VB Series"}],
                        "Symptom": [{"symptom_id": "SYM-001", "name": "Axis backlash"}],
                        "FailureMode": [{"failure_mode_id": "FM-001", "name": "Backlash compensation mismatch"}],
                    },
                },
                "graph_issues": [
                    {
                        "issue_type": "orphan",
                        "affected_nodes": ["SYM-001"],
                        "description": "Symptom 'Axis backlash' is not connected to any Asset in the graph.",
                        "suggested_fix": "Connect it to the right diagnostic chain.",
                    }
                ],
                "suggested_relations": [
                    {
                        "relation_name": "MAY_INDICATE",
                        "from_type": "Symptom",
                        "from_id": "SYM-001",
                        "from_label": "Axis backlash",
                        "to_type": "FailureMode",
                        "to_id": "FM-001",
                        "to_label": "Backlash compensation mismatch",
                        "confidence": 0.81,
                        "rationale": "Token overlap 0.81.",
                    }
                ],
            }
        }

        critiques = critique_ontology_draft(store)

        self.assertEqual(len(critiques), 1)
        critique = critiques[0]
        self.assertEqual(critique["entity_id"], "SYM-001")
        self.assertEqual(len(critique["candidates"]), 1)
        self.assertEqual(critique["candidates"][0]["relation_name"], "MAY_INDICATE")
        self.assertEqual(critique["candidates"][0]["to_label"], "Backlash compensation mismatch")

    def test_ontology_review_payload_includes_stats_and_previews(self):
        class _Field:
            def __init__(self, field_key):
                self.field_key = field_key
            def model_dump(self):
                return {"field_key": self.field_key}

        class _Issue:
            def __init__(self, issue_type, description):
                self.issue_type = issue_type
                self.description = description
                self.affected_nodes = ["SYM-001"]

        class _Suggestion:
            def __init__(self):
                self.relation_name = "MAY_INDICATE"
                self.from_label = "Axis backlash"
                self.from_id = "SYM-001"
                self.to_label = "Backlash compensation mismatch"
                self.to_id = "FM-001"
                self.confidence = 0.81
                self.rationale = "Token overlap 0.81."

        class _Confidence:
            def __init__(self):
                self.counts = {"auto_approve": 3, "human_review": 2, "auto_reject": 0}

        class _Ontology:
            def __init__(self):
                self.nodes = {
                    "Asset": [{"asset_id": "ASSET-001"}],
                    "Symptom": [{"symptom_id": "SYM-001"}],
                    "FailureMode": [{"failure_mode_id": "FM-001"}],
                }

        class _Result:
            def __init__(self):
                self.status = "needs_human_review"
                self.ontology = _Ontology()
                self.graph_issues = [_Issue("orphan", "Symptom is not connected.")]
                self.human_required_fields = [_Field("Asset::ASSET-001::brand")]
                self.schema_issues = []
                self.suggested_relations = [_Suggestion()]
                self.confidence_report = _Confidence()

        payload = _build_ontology_review_payload(
            _Result(),
            {
                "cut_plan": {
                    "pages_to_keep": [3, 4, 5],
                    "sections": [{"name": "Troubleshooting", "start": 3, "end": 5}],
                }
            },
        )

        self.assertEqual(payload["node_count"], 3)
        self.assertEqual(payload["selected_pages_count"], 3)
        self.assertEqual(payload["selected_sections_count"], 1)
        self.assertEqual(payload["graph_issues_count"], 1)
        self.assertEqual(payload["suggested_relations_count"], 1)
        self.assertEqual(payload["confidence_counts"]["human_review"], 2)
        self.assertEqual(payload["top_graph_issues"][0]["issue_type"], "orphan")
        self.assertEqual(payload["preview_relations"][0]["relation_name"], "MAY_INDICATE")


if __name__ == "__main__":
    unittest.main()
