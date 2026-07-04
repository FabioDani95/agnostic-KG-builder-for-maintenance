from __future__ import annotations

import unittest

from backend.models import OntologyInstance
from backend.services.coverage_completion_service import (
    apply_missing_chains,
    build_chain_summary,
)


def _ontology() -> OntologyInstance:
    return OntologyInstance.model_validate({
        "ontology_name": "diagnostic",
        "version": "V1",
        "language": "en",
        "source_type": "Service Manual",
        "source_title": "Demo Manual",
        "nodes": {
            "Symptom": [
                {"symptom_id": "sym_keep_filling", "name": "Keep filling water",
                 "description": "Water keeps filling.", "severity": "High"},
            ],
            "FailureMode": [
                {"failure_mode_id": "fm_valve_leak", "name": "Water inlet valve leaking open",
                 "description": "Valve fills without power.", "material_context": "comp_valve"},
            ],
            "CorrectiveAction": [
                {"action_id": "ca_replace_valve", "name": "Replace the water inlet valve",
                 "description": "r", "instruction_text": "Replace the water inlet valve."},
            ],
        },
        "relations": [
            {"name": "MAY_INDICATE", "from_type": "Symptom", "from_id": "sym_keep_filling",
             "to_type": "FailureMode", "to_id": "fm_valve_leak",
             "evidence": [{"source_page": 19, "source_reference": "PAGE 19",
                           "quote": "water can fill into the water inlet valve"}]},
            {"name": "RESOLVED_BY", "from_type": "FailureMode", "from_id": "fm_valve_leak",
             "to_type": "CorrectiveAction", "to_id": "ca_replace_valve",
             "evidence": [{"source_page": 19, "source_reference": "PAGE 19",
                           "quote": "replace the water inlet valve"}]},
        ],
    })


_PAGES = [{
    "page_number": 19,
    "text": (
        "If water can fill into the water inlet valve, replace the water inlet valve. "
        "If the wire connecting the computer board to the water level sensor is bad, "
        "replace the wire unit."
    ),
}]


def _chain(quote: str, source_page: int = 19) -> dict:
    return {
        "symptom": {"symptom_id": "sym_keep_filling", "name": "Keep filling water",
                    "description": "Water keeps filling.", "severity": "High"},
        "failure_mode": {"failure_mode_id": "fm_wire_bad", "name": "Wire unit bad to water level sensor",
                         "description": "Wire between board and sensor is bad.",
                         "material_context": "comp_wire_unit"},
        "corrective_action": {"action_id": "ca_replace_wire", "name": "Replace the wire unit",
                              "description": "r", "instruction_text": "Replace the wire unit.",
                              "source_page": source_page},
        "evidence": {"source_page": source_page, "source_reference": f"PAGE {source_page}",
                     "quote": quote},
    }


class ChainSummaryTests(unittest.TestCase):
    def test_summary_lists_symptom_with_failure_modes(self):
        summary = build_chain_summary(_ontology())
        self.assertEqual(summary, [{
            "symptom": "Keep filling water",
            "failure_modes": ["Water inlet valve leaking open"],
        }])


class ApplyMissingChainsTests(unittest.TestCase):
    def test_grounded_chain_is_added(self):
        payload = {"missing_chains": [_chain("replace the wire unit")]}
        updated, report = apply_missing_chains(_ontology(), payload, _PAGES, max_chains=12)
        self.assertEqual(report["applied"], 1)
        fm_ids = {fm["failure_mode_id"] for fm in updated.nodes["FailureMode"]}
        self.assertIn("fm_wire_bad", fm_ids)
        self.assertTrue(any(
            r.name == "RESOLVED_BY" and r.to_id == "ca_replace_wire" for r in updated.relations
        ))

    def test_chain_without_supported_quote_is_dropped(self):
        payload = {"missing_chains": [_chain("this sentence is not in the manual at all")]}
        updated, report = apply_missing_chains(_ontology(), payload, _PAGES, max_chains=12)
        self.assertEqual(report["applied"], 0)
        self.assertEqual(report["dropped_no_quote"], 1)
        self.assertEqual(updated, _ontology())

    def test_reemitted_existing_chain_dedupes_to_noop(self):
        # Same names as the existing chain (different ids): must reuse via
        # semantic keys and not duplicate nodes or relations.
        chain = {
            "symptom": {"symptom_id": "sym_new", "name": "Keep filling water",
                        "description": "", "severity": "High"},
            "failure_mode": {"failure_mode_id": "fm_new", "name": "Water inlet valve leaking open",
                             "description": "", "material_context": "asset_level"},
            "corrective_action": {"action_id": "ca_new", "name": "Replace the water inlet valve",
                                  "description": "", "instruction_text": "Replace the water inlet valve.",
                                  "source_page": 19},
            "evidence": {"source_page": 19, "source_reference": "PAGE 19",
                         "quote": "replace the water inlet valve"},
        }
        updated, report = apply_missing_chains(_ontology(), {"missing_chains": [chain]}, _PAGES, max_chains=12)
        self.assertEqual(report["applied"], 0)
        self.assertEqual(report["dropped_duplicate"], 1)
        self.assertEqual(len(updated.nodes["Symptom"]), 1)
        self.assertEqual(len(updated.nodes["FailureMode"]), 1)
        self.assertEqual(len(updated.relations), 2)

    def test_max_chains_cap_is_respected(self):
        chains = [
            _chain("replace the wire unit"),
            {**_chain("water level sensor is bad"),
             "failure_mode": {"failure_mode_id": "fm_sensor", "name": "Water level sensor bad",
                              "description": "", "material_context": "asset_level"}},
        ]
        _, report = apply_missing_chains(_ontology(), {"missing_chains": chains}, _PAGES, max_chains=1)
        self.assertEqual(report["applied"], 1)

    def test_placeholder_ids_never_produce_dangling_relations(self):
        # Real-run regression: the model copied the prompt placeholder
        # "existing_or_new_id" into BOTH failure_mode_id and action_id. The
        # global id-reuse resolved the second occurrence to the first node
        # (wrong type), emitting RESOLVED_BY to a target that did not exist.
        chain = {
            "symptom": {"symptom_id": "existing_or_new_id", "name": "No water filling",
                        "description": "", "severity": "Medium"},
            "failure_mode": {"failure_mode_id": "existing_or_new_id", "name": "Drain hose end set too low",
                             "description": "", "material_context": "asset_level"},
            "corrective_action": {"action_id": "existing_or_new_id", "name": "Raise the drain hose end",
                                  "description": "", "instruction_text": "Raise the drain hose end.",
                                  "source_page": 19},
            "evidence": {"source_page": 19, "source_reference": "PAGE 19",
                         "quote": "replace the wire unit"},
        }
        updated, report = apply_missing_chains(_ontology(), {"missing_chains": [chain]}, _PAGES, max_chains=12)
        self.assertEqual(report["applied"], 1)
        node_ids = {
            str(node.get(field))
            for label, field in (("Symptom", "symptom_id"), ("FailureMode", "failure_mode_id"),
                                 ("CorrectiveAction", "action_id"))
            for node in updated.nodes.get(label, [])
        }
        self.assertNotIn("existing_or_new_id", node_ids)
        # Every relation endpoint must reference an existing node.
        for relation in updated.relations:
            self.assertIn(relation.from_id, node_ids | {"comp_valve"}, relation)
            self.assertIn(relation.to_id, node_ids | {"comp_valve"}, relation)

    def test_empty_payload_is_noop(self):
        updated, report = apply_missing_chains(_ontology(), {"missing_chains": []}, _PAGES, max_chains=12)
        self.assertEqual(report, {"returned": 0, "applied": 0, "dropped_no_quote": 0, "dropped_duplicate": 0})
        self.assertEqual(updated, _ontology())


if __name__ == "__main__":
    unittest.main()
