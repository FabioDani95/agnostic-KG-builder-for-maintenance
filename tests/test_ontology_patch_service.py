from __future__ import annotations

import unittest

from backend.services.ontology_patch_service import apply_ontology_patch, is_ontology_patch


def _previous() -> dict:
    return {
        "ontology_name": "diagnostic",
        "version": "V1",
        "language": "en",
        "source_type": "Service Manual",
        "source_title": "Demo Manual",
        "nodes": {
            "Component": [
                {"component_id": "comp_door", "name": "Door", "description": "d", "category": "Enclosure"},
            ],
            "Symptom": [
                {"symptom_id": "sym_a", "name": "Door stuck", "description": "d", "severity": "Medium"},
            ],
            "FailureMode": [
                {"failure_mode_id": "fm_bad", "name": "Door stuck", "description": "restates the symptom",
                 "material_context": "asset_level"},
                {"failure_mode_id": "fm_ok", "name": "Hinge seized", "description": "corrosion",
                 "material_context": "comp_door"},
            ],
            "CorrectiveAction": [
                {"action_id": "ca_a", "name": "Replace hinge", "description": "r",
                 "instruction_text": "Replace the hinge."},
            ],
        },
        "relations": [
            {"name": "MAY_INDICATE", "from_id": "sym_a", "to_id": "fm_bad",
             "evidence": [{"source_page": 5, "source_reference": "PAGE 5", "quote": "door stuck"}]},
            {"name": "MAY_INDICATE", "from_id": "sym_a", "to_id": "fm_ok",
             "evidence": [{"source_page": 5, "source_reference": "PAGE 5", "quote": "hinge seized"}]},
            {"name": "RESOLVED_BY", "from_id": "fm_ok", "to_id": "ca_a",
             "evidence": [{"source_page": 5, "source_reference": "PAGE 5", "quote": "replace the hinge"}]},
        ],
    }


class IsOntologyPatchTests(unittest.TestCase):
    def test_patch_payload_is_detected(self):
        self.assertTrue(is_ontology_patch({"remove_node_ids": ["fm_bad"]}))
        self.assertTrue(is_ontology_patch({"upsert_nodes": {}, "add_relations": []}))

    def test_full_instance_is_not_a_patch(self):
        self.assertFalse(is_ontology_patch(_previous()))
        self.assertFalse(is_ontology_patch({"nodes": {}, "relations": [], "upsert_nodes": {}}))
        self.assertFalse(is_ontology_patch({}))
        self.assertFalse(is_ontology_patch(None))


class ApplyOntologyPatchTests(unittest.TestCase):
    def test_upsert_replaces_node_with_same_id(self):
        patch = {"upsert_nodes": {"FailureMode": [
            {"failure_mode_id": "fm_bad", "name": "Hinge pin sheared",
             "description": "The hinge pin is sheared.", "material_context": "comp_door"},
        ]}}
        merged, report = apply_ontology_patch(_previous(), patch)
        modes = {fm["failure_mode_id"]: fm for fm in merged["nodes"]["FailureMode"]}
        self.assertEqual(len(modes), 2)
        self.assertEqual(modes["fm_bad"]["name"], "Hinge pin sheared")
        self.assertEqual(report["upserted_nodes"], 1)

    def test_upsert_appends_new_node(self):
        patch = {"upsert_nodes": {"Component": [
            {"component_id": "comp_hinge", "name": "Hinge", "description": "d", "category": "Enclosure"},
        ]}}
        merged, _ = apply_ontology_patch(_previous(), patch)
        component_ids = [item["component_id"] for item in merged["nodes"]["Component"]]
        self.assertIn("comp_hinge", component_ids)

    def test_remove_node_also_drops_incident_relations(self):
        merged, report = apply_ontology_patch(_previous(), {"remove_node_ids": ["fm_bad"]})
        ids = [fm["failure_mode_id"] for fm in merged["nodes"]["FailureMode"]]
        self.assertEqual(ids, ["fm_ok"])
        self.assertFalse(any(rel["to_id"] == "fm_bad" for rel in merged["relations"]))
        self.assertEqual(len(merged["relations"]), 2)
        self.assertEqual(report["removed_nodes"], 1)
        self.assertEqual(report["removed_relations"], 1)

    def test_remove_relation_by_key(self):
        patch = {"remove_relations": [{"name": "MAY_INDICATE", "from_id": "sym_a", "to_id": "fm_bad"}]}
        merged, report = apply_ontology_patch(_previous(), patch)
        self.assertEqual(len(merged["relations"]), 2)
        self.assertEqual(report["removed_relations"], 1)
        # The node itself stays: only the edge was targeted.
        self.assertEqual(len(merged["nodes"]["FailureMode"]), 2)

    def test_add_relations_are_deduplicated(self):
        patch = {"add_relations": [
            {"name": "RESOLVED_BY", "from_id": "fm_ok", "to_id": "ca_a",
             "evidence": [{"source_page": 5, "source_reference": "PAGE 5", "quote": "replace the hinge"}]},
            {"name": "AFFECTS", "from_id": "fm_ok", "to_id": "comp_door",
             "evidence": [{"source_page": 5, "source_reference": "PAGE 5", "quote": "hinge seized"}]},
        ]}
        merged, report = apply_ontology_patch(_previous(), patch)
        self.assertEqual(report["added_relations"], 1)  # RESOLVED_BY already existed
        self.assertEqual(len(merged["relations"]), 4)

    def test_empty_patch_is_identity(self):
        previous = _previous()
        merged, report = apply_ontology_patch(previous, {})
        self.assertEqual(merged, previous)
        self.assertEqual(report, {"upserted_nodes": 0, "removed_nodes": 0,
                                  "added_relations": 0, "removed_relations": 0,
                                  "skipped_dangling_relations": 0})

    def test_inputs_are_not_mutated(self):
        previous = _previous()
        snapshot = _previous()
        apply_ontology_patch(previous, {"remove_node_ids": ["fm_bad"]})
        self.assertEqual(previous, snapshot)


if __name__ == "__main__":
    unittest.main()
