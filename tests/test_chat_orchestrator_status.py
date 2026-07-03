import unittest

from backend.graph.state import GraphPhase
from backend.services.conversation.heuristics import (
    detect_inventory_request as _detect_inventory_request,
    detect_rerun_action as _detect_rerun_action,
    maybe_build_direct_status_reply as _maybe_build_direct_status_reply,
    maybe_build_scope_guard_reply as _maybe_build_scope_guard_reply,
    workflow_status_reply as _workflow_status_reply,
)
from backend.services.conversation.orchestrator import (
    _build_messages,
    _next_action_for_continue,
    _strip_leading_widget_payload,
    _summarise_tool_result_for_followup,
)


class ChatOrchestratorStatusTests(unittest.TestCase):
    def test_scoping_page_count_reply_uses_live_cut_plan_counts(self):
        store = {
            "cut_plan": {
                "pages_to_keep": list(range(12, 94)),
                "total_pages": 114,
                "sections": [
                    {"name": "Troubleshooting", "start": 12, "end": 54},
                    {"name": "Electrical diagrams", "start": 55, "end": 93},
                ],
            },
            "graph_state": {
                "current_phase": GraphPhase.SCOPING.value,
                "selected_pages": list(range(12, 60)),  # stale value should be ignored
            },
        }

        reply = _maybe_build_direct_status_reply(store, "how many pages you selected?")

        self.assertIsNotNone(reply)
        self.assertIn("82 pages out of 114", reply)
        self.assertIn("2 section(s)", reply)
        self.assertNotIn("48", reply)

    def test_non_status_query_returns_none(self):
        store = {
            "cut_plan": {"pages_to_keep": [1, 2, 3], "total_pages": 10},
            "graph_state": {"current_phase": GraphPhase.SCOPING.value},
        }

        reply = _maybe_build_direct_status_reply(store, "rename the second section")

        self.assertIsNone(reply)

    def test_off_topic_query_is_blocked_with_contextual_redirect(self):
        store = {
            "filename": "VB SERIES FANUC MAINTENANCE MANUAL Ver 1.0.pdf",
            "cut_plan": {"pages_to_keep": [12, 13, 14], "total_pages": 114},
            "graph_state": {"current_phase": GraphPhase.SCOPING.value},
        }

        reply = _maybe_build_scope_guard_reply(store, "how far is binago from lugano?")

        self.assertIsNotNone(reply)
        self.assertIn("loaded manual and this extraction workflow", reply)
        self.assertIn("VB SERIES FANUC MAINTENANCE MANUAL Ver 1.0.pdf", reply)
        self.assertIn("scoping", reply)

    def test_short_process_command_is_not_treated_as_off_topic(self):
        store = {
            "cut_plan": {"pages_to_keep": [1, 2, 3], "total_pages": 10},
            "graph_state": {"current_phase": GraphPhase.SCOPING.value},
        }

        reply = _maybe_build_scope_guard_reply(store, "approve it")

        self.assertIsNone(reply)

    def test_scoping_section_reply_uses_real_section_names(self):
        store = {
            "filename": "VB SERIES FANUC MAINTENANCE MANUAL Ver 1.0.pdf",
            "cut_plan": {
                "pages_to_keep": list(range(12, 94)),
                "total_pages": 114,
                "sections": [
                    {"name": "Troubleshooting", "start": 12, "end": 54},
                    {"name": "Electrical diagrams", "start": 55, "end": 93},
                ],
            },
            "graph_state": {
                "current_phase": GraphPhase.SCOPING.value,
            },
        }

        reply = _maybe_build_direct_status_reply(store, "which sections did you select?")

        self.assertIsNotNone(reply)
        self.assertIn("2 section(s)", reply)
        self.assertIn("Troubleshooting", reply)
        self.assertIn("Electrical diagrams", reply)
        self.assertIn("pp. 12-54", reply)
        self.assertIn("pp. 55-93", reply)

    def test_repeat_section_query_lists_all_sections_and_cleans_duplicate_ranges(self):
        store = {
            "cut_plan": {
                "pages_to_keep": list(range(3, 31)),
                "total_pages": 114,
                "sections": [
                    {"name": "Keyword match (pp. 3-10)", "start": 3, "end": 10},
                    {"name": "2.52 Cleaning & Lubricating Machine", "start": 10, "end": 11},
                    {"name": "3.35 Check / Adjusting Ballscrew Endplay", "start": 24, "end": 24},
                ],
            },
            "graph_state": {
                "current_phase": GraphPhase.SCOPING.value,
            },
        }

        reply = _maybe_build_direct_status_reply(store, "can you repeat the section?")

        self.assertIsNotNone(reply)
        self.assertIn("3 section(s)", reply)
        self.assertIn("1. Keyword match (pp. 3-10)", reply)
        self.assertNotIn("Keyword match (pp. 3-10) (pp. 3-10)", reply)
        self.assertIn("2. 2.52 Cleaning & Lubricating Machine (pp. 10-11)", reply)
        self.assertIn("3. 3.35 Check / Adjusting Ballscrew Endplay (pp. 24-24)", reply)

    def test_build_messages_includes_authoritative_live_snapshot(self):
        store = {
            "filename": "mock-manual.pdf",
            "ontology_pipeline": {
                "ontology": {
                    "nodes": {
                        "Asset": [{"asset_id": "ASSET-001", "name": "Mock Machine"}],
                        "Symptom": [{"symptom_id": "SYM-001", "name": "Axis Backlash"}],
                    }
                }
            },
            "validated_triplets": [{"id": "t1"}],
            "cut_plan": {
                "pages_to_keep": [12, 13, 14, 30, 31],
                "total_pages": 114,
                "sections": [
                    {"name": "Troubleshooting", "start": 12, "end": 14},
                    {"name": "Diagnostics", "start": 30, "end": 31},
                ],
            },
            "graph_state": {
                "current_phase": GraphPhase.SCOPING.value,
                "run_status": "awaiting_operator",
                "next_step": "review current cut plan",
                "cleaned_triplets": [{"id": "t2"}, {"id": "t3"}],
            },
        }

        messages = _build_messages({"messages": []}, store)

        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "system")
        self.assertIn("LIVE STATE SNAPSHOT", messages[1]["content"])
        self.assertIn("filename: mock-manual.pdf", messages[1]["content"])
        self.assertIn("selected_pages_count: 5", messages[1]["content"])
        self.assertIn("selected_page_ranges: 12-14, 30-31", messages[1]["content"])
        self.assertIn("selected_sections: 1. Troubleshooting (pp. 12-14); 2. Diagnostics (pp. 30-31)", messages[1]["content"])
        self.assertIn("selected_sections_full: 1. Troubleshooting (pp. 12-14); 2. Diagnostics (pp. 30-31)", messages[1]["content"])
        self.assertIn("extracted_node_count: 2", messages[1]["content"])
        self.assertIn('"Asset": 1', messages[1]["content"])
        self.assertIn("Mock Machine (ASSET-001)", messages[1]["content"])

    def test_inventory_request_detection_handles_italian_node_questions(self):
        detected = _detect_inventory_request("quali nodi e tipi hai estratto?")

        self.assertIsNotNone(detected)
        tool_name, args = detected
        self.assertEqual(tool_name, "list_extracted_nodes")
        self.assertEqual(args["limit"], 60)

    def test_inventory_request_detection_handles_triplet_questions(self):
        detected = _detect_inventory_request("fammi vedere le triplette estratte")

        self.assertIsNotNone(detected)
        tool_name, args = detected
        self.assertEqual(tool_name, "list_extracted_triplets")
        self.assertEqual(args["status"], "all")

    def test_strip_leading_widget_payload_keeps_plain_followup(self):
        text = (
            '{"widget":"sections","event":"update","payload":{"sections":[{"name":"A","start":1,"end":2}]}}\n'
            "Scoping is complete. Review the Section Selection widget."
        )

        cleaned = _strip_leading_widget_payload(text)

        self.assertEqual(cleaned, "Scoping is complete. Review the Section Selection widget.")

    def test_widget_tool_result_followup_summary_omits_raw_payload_lists(self):
        result = {
            "status": "ok",
            "widget": "sections",
            "sections": [
                {"name": "Keyword match (pp. 3-10)", "start": 3, "end": 10},
                {"name": "Alarms", "start": 32, "end": 32},
            ],
            "pages_to_keep": [3, 4, 5, 6, 7, 8, 9, 10, 32],
            "total_pages": 114,
        }

        summary = _summarise_tool_result_for_followup("propose_cut_plan", result)

        self.assertEqual(summary["widget_rendered"], "sections")
        self.assertEqual(summary["section_count"], 2)
        self.assertEqual(summary["selected_page_count"], 9)
        self.assertEqual(summary["selected_page_ranges"], "3-10, 32")
        self.assertNotIn("sections", summary)
        self.assertNotIn("pages_to_keep", summary)
        self.assertEqual(summary["preview_sections"][0]["name"], "Keyword match")

    def test_progress_reply_reports_ontology_blockers_and_next_step(self):
        store = {
            "cut_plan": {
                "pages_to_keep": [3, 4, 5],
                "total_pages": 10,
                "sections": [{"name": "Troubleshooting", "start": 3, "end": 5}],
            },
            "ontology_pipeline": {
                "status": "needs_human",
                "ontology": {"nodes": {"Asset": [{"asset_id": "ASSET-001"}]}},
                "schema_issues": [],
                "human_required_fields": [{"field_key": "Asset::ASSET-001::brand"}],
                "graph_issues": [],
                "suggested_relations": [{"relation_name": "HAS_COMPONENT"}],
            },
            "graph_state": {"current_phase": GraphPhase.ONTOLOGY_DRAFT.value},
        }

        reply = _maybe_build_direct_status_reply(store, "cosa manca per procedere?")

        self.assertIsNotNone(reply)
        self.assertIn("required ontology field", reply)
        self.assertIn("Fill the required fields", reply)

    def test_status_reply_says_extraction_is_not_blocked_by_suggestions_only(self):
        store = {
            "cut_plan": {
                "pages_to_keep": [3, 4, 5],
                "total_pages": 10,
                "sections": [{"name": "Troubleshooting", "start": 3, "end": 5}],
            },
            "ontology_pipeline": {
                "status": "ready",
                "ontology": {"nodes": {"Asset": [{"asset_id": "ASSET-001"}]}},
                "schema_issues": [],
                "human_required_fields": [],
                "graph_issues": [{"issue_type": "orphan"}],
                "suggested_relations": [{"relation_name": "HAS_COMPONENT"}],
            },
            "graph_state": {"current_phase": GraphPhase.ONTOLOGY_DRAFT.value},
        }

        reply = _workflow_status_reply(store)
        action, reason = _next_action_for_continue(store)

        self.assertIn("No hard blocker", reply)
        self.assertIn("Continue to Extraction", reply)
        self.assertEqual(action, "run_extraction")
        self.assertIsNone(reason)

    def test_continue_is_not_used_for_next_step_questions(self):
        store = {
            "cut_plan": {
                "pages_to_keep": [3, 4, 5],
                "total_pages": 10,
                "sections": [{"name": "Troubleshooting", "start": 3, "end": 5}],
            },
            "graph_state": {"current_phase": GraphPhase.SCOPING.value},
        }

        reply = _maybe_build_direct_status_reply(store, "what is the next step?")

        self.assertIsNotNone(reply)
        self.assertIn("section selection", reply.lower())

    def test_rerun_detection_targets_completed_step(self):
        store = {"graph_state": {"current_phase": GraphPhase.ONTOLOGY_DRAFT.value}}

        self.assertEqual(_detect_rerun_action("rifai ontology", store), "draft_ontology")
        self.assertEqual(_detect_rerun_action("re-scope the document", store), "propose_cut_plan")


if __name__ == "__main__":
    unittest.main()
