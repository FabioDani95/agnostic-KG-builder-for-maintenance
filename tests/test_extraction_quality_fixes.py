"""Tests for the Fase 0/1 extraction-quality fixes:

- severity normalization onto the canonical Low/Medium/High/Critical scale
- material_context resolution against real Component ids (casing, names, asset)
- actionable-instruction guard for CorrectiveActions
- alarm-context filter for mined error-code candidates
- evidence grounding of relation quotes + confidence penalty
- resolution-completion gating (code must appear in scoped pages, quote required)
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.models import OntologyInstance, SuggestedRelation
from backend.services.candidate_mining_service import mine_candidates
from backend.services.confidence import score_ontology
from backend.services.evidence_grounding_service import ground_relation_evidence
from backend.services.graph_closure_service import close_grounded_gaps
from backend.services.ontology_pipeline import (
    _extract_json_object,
    _validate_schema,
    normalize_ontology_instance,
)
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_export_store import prepare_exported_ontology
from backend.services.ontology_semantics import (
    has_actionable_instruction,
    normalize_severity,
    resolve_material_context,
)
from backend.services.resolution_completion_service import complete_resolution_gaps
from backend.services.review_queue_service import (
    build_review_queue,
    compute_open_gaps,
    summarize_queue,
)


class SeverityNormalizationTests(unittest.TestCase):
    def test_canonical_values_pass_through(self) -> None:
        for value in ("Low", "Medium", "High", "Critical"):
            self.assertEqual(normalize_severity(value), value)

    def test_common_drift_values_are_mapped(self) -> None:
        self.assertEqual(normalize_severity("moderate"), "Medium")
        self.assertEqual(normalize_severity("minor"), "Low")
        self.assertEqual(normalize_severity("SEVERE"), "High")
        self.assertEqual(normalize_severity("safety hazard"), "Critical")

    def test_empty_stays_empty_and_unknown_falls_back_to_medium(self) -> None:
        self.assertEqual(normalize_severity(""), "")
        self.assertEqual(normalize_severity("blue"), "Medium")


class MaterialContextResolutionTests(unittest.TestCase):
    _COMPONENTS = [
        {"component_id": "comp_door", "name": "Door"},
        {"component_id": "comp_thermistor", "name": "PCB Thermistor"},
    ]

    def test_case_mismatch_is_resolved_to_real_component_id(self) -> None:
        self.assertEqual(
            resolve_material_context("Comp_thermistor", self._COMPONENTS),
            "comp_thermistor",
        )

    def test_component_name_is_resolved_to_id(self) -> None:
        self.assertEqual(
            resolve_material_context("PCB Thermistor", self._COMPONENTS),
            "comp_thermistor",
        )

    def test_asset_reference_becomes_asset_level(self) -> None:
        self.assertEqual(
            resolve_material_context("Asset_demo_machine", self._COMPONENTS, {"asset_demo_machine"}),
            "asset_level",
        )

    def test_unresolved_value_is_left_unchanged_for_validation(self) -> None:
        self.assertEqual(
            resolve_material_context("hydraulic circuit", self._COMPONENTS),
            "hydraulic circuit",
        )


class ActionableInstructionTests(unittest.TestCase):
    def test_repair_steps_are_actionable(self) -> None:
        self.assertTrue(has_actionable_instruction("1. Replace the solenoid valve. 2. Cycle the tool changer."))

    def test_cause_statement_is_not_actionable(self) -> None:
        self.assertFalse(has_actionable_instruction("1. Old packing washers cause leakage of air or fluid."))

    def test_empty_is_not_actionable(self) -> None:
        self.assertFalse(has_actionable_instruction(""))


class ErrorCodeMiningContextTests(unittest.TestCase):
    def test_code_with_alarm_context_is_kept(self) -> None:
        text = "--- PAGE 4 ---\nWhen alarm C0330 is displayed, the spindle orientation failed."
        result = mine_candidates(text)
        self.assertIn("C0330", [candidate.token for candidate in result.error_codes])

    def test_exploded_view_part_codes_are_dropped(self) -> None:
        text = (
            "--- PAGE 41 ---\nEXPLODED VIEW — DOOR PARTS\n"
            "W262 door assembly\nW102 latch board\nW101 hinge bracket\n"
        )
        result = mine_candidates(text)
        self.assertEqual(
            [candidate.token for candidate in result.error_codes
             if candidate.token.upper().startswith("W")],
            [],
        )

    def test_referenced_standard_is_dropped(self) -> None:
        text = "--- PAGE 2 ---\nThis laser complies with ANSI Z136 requirements for laser safety."
        result = mine_candidates(text)
        self.assertNotIn("Z136", [candidate.token for candidate in result.error_codes])


def _ontology_fixture(**overrides) -> OntologyInstance:
    payload = {
        "ontology_name": "diagnostic",
        "version": "V1",
        "language": "en",
        "source_type": "Service Manual",
        "source_title": "Demo Manual",
        "nodes": {
            "Asset": [{
                "asset_id": "asset_demo", "name": "Demo Machine", "description": "d",
                "brand": "Demo", "model": "M1", "asset_type": "machine",
            }],
            "Component": [{
                "component_id": "comp_door", "name": "Door",
                "description": "Front door", "category": "Enclosure",
            }],
            "Symptom": [{
                "symptom_id": "sym_door_stuck", "name": "Door stuck",
                "description": "The door does not open.", "severity": "moderate",
            }],
            "FailureMode": [{
                "failure_mode_id": "fm_hinge_seized", "name": "Hinge seized",
                "description": "The hinge is seized by corrosion.",
                "material_context": "Comp_door",
            }],
            "CorrectiveAction": [{
                "action_id": "ca_replace_hinge", "name": "Replace hinge",
                "description": "Replace the seized hinge.",
                "instruction_text": "1. Replace the hinge.",
                "source_type": "Service Manual", "source_title": "Demo Manual",
                "source_reference": "PAGE 5",
            }],
            "ErrorCode": [],
        },
        "relations": [
            {
                "name": "MAY_INDICATE", "from_type": "Symptom", "from_id": "sym_door_stuck",
                "to_type": "FailureMode", "to_id": "fm_hinge_seized",
                "evidence": [{"source_page": 5, "source_reference": "PAGE 5",
                              "quote": "the hinge is seized by corrosion"}],
            },
            {
                "name": "RESOLVED_BY", "from_type": "FailureMode", "from_id": "fm_hinge_seized",
                "to_type": "CorrectiveAction", "to_id": "ca_replace_hinge",
                "evidence": [{"source_page": 5, "source_reference": "PAGE 5",
                              "quote": "this quote is fabricated and appears nowhere"}],
            },
        ],
    }
    payload.update(overrides)
    return OntologyInstance.model_validate(payload)


class NormalizationIntegrationTests(unittest.TestCase):
    def test_normalize_resolves_material_context_and_severity(self) -> None:
        normalized = normalize_ontology_instance(_ontology_fixture())
        failure_mode = normalized.nodes["FailureMode"][0]
        symptom = normalized.nodes["Symptom"][0]
        self.assertEqual(failure_mode["material_context"], "comp_door")
        self.assertEqual(symptom["severity"], "Medium")


class InstructionGuardValidationTests(unittest.TestCase):
    def test_non_actionable_instruction_emits_warning_not_error(self) -> None:
        ontology = _ontology_fixture()
        ontology.nodes["CorrectiveAction"][0]["instruction_text"] = (
            "1. Old packing washers cause leakage of air or fluid."
        )
        issues, _ = _validate_schema(ontology, load_ontology_schema())
        guard_issues = [issue for issue in issues if issue.code == "instruction_not_actionable"]
        self.assertEqual(len(guard_issues), 1)
        self.assertEqual(guard_issues[0].severity, "warning")
        self.assertEqual(guard_issues[0].target_id, "ca_replace_hinge")

    def test_actionable_instruction_emits_no_guard_warning(self) -> None:
        issues, _ = _validate_schema(_ontology_fixture(), load_ontology_schema())
        self.assertEqual(
            [issue for issue in issues if issue.code == "instruction_not_actionable"],
            [],
        )


class EvidenceGroundingTests(unittest.TestCase):
    _PAGES = {5: "If the door is stuck, the hinge is seized by corrosion. Replace the hinge."}

    def test_grounded_and_ungrounded_relations_are_separated(self) -> None:
        issues, ungrounded_keys, stats = ground_relation_evidence(_ontology_fixture(), self._PAGES)

        self.assertEqual(stats["relations_checked"], 2)
        self.assertEqual(stats["relations_grounded"], 1)
        self.assertEqual(stats["relations_ungrounded"], 1)
        # Both endpoints of the fabricated RESOLVED_BY relation are flagged.
        self.assertIn(("FailureMode", "fm_hinge_seized"), ungrounded_keys)
        self.assertIn(("CorrectiveAction", "ca_replace_hinge"), ungrounded_keys)
        self.assertTrue(all(issue.code == "ungrounded_evidence" for issue in issues))

    def test_ungrounded_nodes_drop_out_of_auto_approve(self) -> None:
        ontology = normalize_ontology_instance(_ontology_fixture())
        config = {
            "enabled": True,
            "theta_high": 0.80,
            "theta_low": 0.45,
            "weights": {
                "evidence_present": 0.25, "corroboration": 0.15,
                "required_props_complete": 0.25, "chain_participation": 0.20,
                "clean_extraction": 0.15,
            },
            "penalties": {"ungrounded_evidence": 0.15},
        }
        baseline = score_ontology(ontology=ontology, schema=load_ontology_schema(), config=config)
        penalized = score_ontology(
            ontology=ontology,
            schema=load_ontology_schema(),
            config=config,
            ungrounded_node_keys={("CorrectiveAction", "ca_replace_hinge")},
        )

        def entry(report, node_id):
            return next(item for item in report.entries if item.node_id == node_id)

        self.assertGreater(
            entry(baseline, "ca_replace_hinge").score,
            entry(penalized, "ca_replace_hinge").score,
        )
        self.assertIn(
            "ungrounded_evidence",
            entry(penalized, "ca_replace_hinge").penalties,
        )


class ResolutionCompletionGatingTests(unittest.TestCase):
    class _FakeResponse:
        def __init__(self, content: str):
            self.choices = [type("Choice", (), {
                "message": type("Message", (), {"content": content})(),
                "finish_reason": "stop",
            })()]
            self.model = "gpt-test"
            self.usage = type("Usage", (), {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
                "prompt_tokens_details": type("PromptDetails", (), {"cached_tokens": 0})(),
            })()

    class _FakeCompletions:
        def __init__(self, responses):
            self._responses = list(responses)

        def create(self, **kwargs):
            return self._responses.pop(0)

    class _FakeOpenAI:
        def __init__(self, responses):
            completions = ResolutionCompletionGatingTests._FakeCompletions(responses)
            self.chat = type("Chat", (), {"completions": completions})()

    def _ontology_with_unlinked_error(self) -> OntologyInstance:
        ontology = _ontology_fixture()
        data = ontology.model_dump()
        data["nodes"]["ErrorCode"] = [{
            "error_code_id": "err_w262", "name": "W262",
            "description": "Exploded view part code.", "code": "W262",
        }]
        return OntologyInstance.model_validate(data)

    def test_error_code_absent_from_pages_is_skipped_without_llm_call(self) -> None:
        ontology = self._ontology_with_unlinked_error()
        text = "--- PAGE 5 ---\nIf the door is stuck, replace the hinge."

        with patch(
            "backend.services.resolution_completion_service.OpenAI",
            lambda *args, **kwargs: self._FakeOpenAI([]),
        ):
            updated, usage, report = complete_resolution_gaps(
                ontology=ontology,
                text_with_pages=text,
                model_name="gpt-5.4",
                parse_json=_extract_json_object,
            )

        self.assertEqual(report["completed"], 0)
        self.assertEqual(usage, [])
        statuses = {attempt["target_id"]: attempt["status"] for attempt in report["attempts"]}
        self.assertEqual(statuses.get("err_w262"), "code_not_in_scope")
        self.assertEqual(len(updated.relations), len(ontology.relations))

    def test_retrieved_action_without_quote_is_dropped(self) -> None:
        ontology = _ontology_fixture()
        data = ontology.model_dump()
        data["relations"] = [rel for rel in data["relations"] if rel["name"] != "RESOLVED_BY"]
        data["nodes"]["CorrectiveAction"] = []
        ontology = OntologyInstance.model_validate(data)

        response = self._FakeResponse(
            '{"status":"found","failure_mode":{"failure_mode_id":"fm_hinge_seized"},'
            '"corrective_actions":[{"action_id":"ca_lubricate","name":"Lubricate hinge",'
            '"description":"Lubricate the hinge.",'
            '"instruction_text":"1. Lubricate the hinge.","source_page":5,'
            '"source_reference":"PAGE 5"}]}'
        )
        text = "--- PAGE 5 ---\nThe hinge is seized by corrosion. Lubricate the hinge."

        with patch(
            "backend.services.resolution_completion_service.OpenAI",
            lambda *args, **kwargs: self._FakeOpenAI([response]),
        ):
            updated, _, report = complete_resolution_gaps(
                ontology=ontology,
                text_with_pages=text,
                model_name="gpt-5.4",
                parse_json=_extract_json_object,
            )

        self.assertEqual(report["completed"], 0)
        self.assertFalse(any(rel.name == "RESOLVED_BY" for rel in updated.relations))


class GraphClosureTests(unittest.TestCase):
    def _orphan_symptom_ontology(self) -> OntologyInstance:
        # Symptom and FailureMode exist but there is no MAY_INDICATE linking them;
        # the FM carries page-5 evidence via its RESOLVED_BY edge, the symptom via
        # its (none) — so grounding must fall back to name co-occurrence on page 5.
        return OntologyInstance.model_validate({
            "ontology_name": "diagnostic", "version": "V1", "language": "en",
            "source_type": "Service Manual", "source_title": "Demo Manual",
            "nodes": {
                "Asset": [{"asset_id": "asset_demo", "name": "Demo Machine", "description": "d",
                           "brand": "Demo", "model": "M1", "asset_type": "machine"}],
                "Component": [{"component_id": "comp_door", "name": "Door",
                               "description": "Front door", "category": "Enclosure"}],
                "Symptom": [{"symptom_id": "sym_door_stuck", "name": "Door stuck",
                             "description": "The door does not open.", "severity": "Medium"}],
                "FailureMode": [{"failure_mode_id": "fm_hinge_seized", "name": "Hinge seized",
                                 "description": "The hinge is seized by corrosion.",
                                 "material_context": "comp_door"}],
                "CorrectiveAction": [], "ErrorCode": [],
            },
            "relations": [{
                "name": "AFFECTS", "from_type": "FailureMode", "from_id": "fm_hinge_seized",
                "to_type": "Component", "to_id": "comp_door",
                "evidence": [{"source_page": 5, "source_reference": "PAGE 5", "quote": "hinge seized"}],
            }],
        })

    def test_grounded_may_indicate_is_auto_applied(self):
        ontology = self._orphan_symptom_ontology()
        suggestions = [SuggestedRelation(
            relation_name="MAY_INDICATE", from_type="Symptom", from_id="sym_door_stuck",
            from_label="Door stuck", to_type="FailureMode", to_id="fm_hinge_seized",
            to_label="Hinge seized", confidence=0.5, rationale="overlap",
        )]
        pages = {5: "Door stuck: the hinge is seized by corrosion. Replace the hinge."}
        updated, remaining, report = close_grounded_gaps(ontology, suggestions, pages)

        self.assertEqual(report["applied"], 1)
        self.assertEqual(remaining, [])
        self.assertTrue(any(
            r.name == "MAY_INDICATE" and r.from_id == "sym_door_stuck" and r.to_id == "fm_hinge_seized"
            for r in updated.relations
        ))

    def test_ungrounded_suggestion_is_left_for_the_operator(self):
        ontology = self._orphan_symptom_ontology()
        suggestions = [SuggestedRelation(
            relation_name="MAY_INDICATE", from_type="Symptom", from_id="sym_door_stuck",
            from_label="Door stuck", to_type="FailureMode", to_id="fm_hinge_seized",
            to_label="Hinge seized", confidence=0.5, rationale="overlap",
        )]
        # No page mentions both endpoints → not grounded.
        pages = {5: "Unrelated maintenance note about lubrication schedules."}
        updated, remaining, report = close_grounded_gaps(ontology, suggestions, pages)

        self.assertEqual(report["applied"], 0)
        self.assertEqual(len(remaining), 1)
        self.assertFalse(any(r.name == "MAY_INDICATE" for r in updated.relations))

    def test_resolved_by_is_never_auto_applied(self):
        ontology = self._orphan_symptom_ontology()
        suggestions = [SuggestedRelation(
            relation_name="RESOLVED_BY", from_type="FailureMode", from_id="fm_hinge_seized",
            from_label="Hinge seized", to_type="CorrectiveAction", to_id="ca_x",
            to_label="x", confidence=0.9, rationale="overlap",
        )]
        pages = {5: "Hinge seized; x procedure."}
        _, remaining, report = close_grounded_gaps(ontology, suggestions, pages)

        self.assertEqual(report["applied"], 0)
        # RESOLVED_BY stays in the operator queue (handled by LLM resolution instead).
        self.assertEqual(len(remaining), 1)

    def test_low_confidence_suggestion_is_not_applied(self):
        ontology = self._orphan_symptom_ontology()
        suggestions = [SuggestedRelation(
            relation_name="MAY_INDICATE", from_type="Symptom", from_id="sym_door_stuck",
            from_label="Door stuck", to_type="FailureMode", to_id="fm_hinge_seized",
            to_label="Hinge seized", confidence=0.21, rationale="weak overlap",
        )]
        pages = {5: "Door stuck: the hinge is seized by corrosion."}
        _, remaining, report = close_grounded_gaps(ontology, suggestions, pages)

        self.assertEqual(report["applied"], 0)
        self.assertEqual(len(remaining), 1)


def _gappy_contract() -> dict:
    # Internal shape: a symptom with no FM, an FM with no action, an unwired error code.
    return {
        "nodes": {
            "Asset": [{"asset_id": "asset_demo", "name": "Demo", "description": "d",
                       "brand": "Demo", "model": "M1"}],
            "Component": [{"component_id": "comp_door", "name": "Door",
                           "description": "Front door", "category": "Enclosure"}],
            "Symptom": [{"symptom_id": "sym_orphan", "name": "Door stuck",
                         "description": "Door does not open.", "severity": "Medium"}],
            "FailureMode": [{"failure_mode_id": "fm_no_action", "name": "Hinge seized",
                             "description": "Hinge seized.", "material_context": "comp_door"}],
            "CorrectiveAction": [],
            "ErrorCode": [{"error_code_id": "err_e1", "name": "E1",
                           "description": "Fault.", "code": "E1"}],
        },
        "relations": [],
    }


class OpenGapsTests(unittest.TestCase):
    def test_open_gaps_name_the_specific_nodes(self):
        gaps = compute_open_gaps(_gappy_contract())
        kinds = {(g["kind"], g["target_id"]) for g in gaps}
        self.assertIn(("symptom_without_failure_mode", "sym_orphan"), kinds)
        self.assertIn(("failure_mode_without_action", "fm_no_action"), kinds)
        self.assertIn(("error_code_without_failure_mode", "err_e1"), kinds)

    def test_complete_chain_has_no_gaps(self):
        contract = _gappy_contract()
        contract["nodes"]["CorrectiveAction"] = [{
            "action_id": "ca_fix", "name": "Replace hinge", "description": "Replace.",
            "instruction_text": "1. Replace the hinge.",
        }]
        contract["relations"] = [
            {"name": "MAY_INDICATE", "from_id": "sym_orphan", "to_id": "fm_no_action"},
            {"name": "RESOLVED_BY", "from_id": "fm_no_action", "to_id": "ca_fix"},
            {"name": "INDICATES", "from_id": "err_e1", "to_id": "fm_no_action"},
        ]
        self.assertEqual(compute_open_gaps(contract), [])

    def test_review_queue_orders_blocking_before_advisory(self):
        from backend.models import PipelineIssue
        issues = [
            PipelineIssue(severity="warning", code="instruction_not_actionable",
                          message="m", target_type="CorrectiveAction", target_id="ca_x"),
        ]
        queue = build_review_queue(_gappy_contract(), schema_issues=issues)
        severities = [item["severity"] for item in queue]
        self.assertEqual(severities, sorted(severities, key=lambda s: {"blocking": 0, "open": 1, "reject": 2, "review": 3, "advisory": 4}[s]))
        self.assertTrue(summarize_queue(queue)["requires_human_review"])


class ExportGatingTests(unittest.TestCase):
    def test_export_metadata_lists_open_gaps(self):
        prepared = prepare_exported_ontology(_gappy_contract())
        meta = prepared["metadata"]
        self.assertTrue(meta["requires_human_review"])
        self.assertGreater(meta["open_gap_count"], 0)
        kinds = {g["kind"] for g in meta["open_gaps"]}
        self.assertIn("symptom_without_failure_mode", kinds)

    def test_export_metadata_clean_when_connected(self):
        contract = _gappy_contract()
        contract["nodes"]["CorrectiveAction"] = [{
            "action_id": "ca_fix", "name": "Replace hinge", "description": "Replace.",
            "instruction_text": "1. Replace the hinge.",
        }]
        contract["relations"] = [
            {"name": "MAY_INDICATE", "from_id": "sym_orphan", "to_id": "fm_no_action"},
            {"name": "RESOLVED_BY", "from_id": "fm_no_action", "to_id": "ca_fix"},
            {"name": "INDICATES", "from_id": "err_e1", "to_id": "fm_no_action"},
        ]
        prepared = prepare_exported_ontology(contract)
        meta = prepared["metadata"]
        self.assertEqual(meta["open_gap_count"], 0)
        self.assertFalse(meta["requires_human_review"])


if __name__ == "__main__":
    unittest.main()
