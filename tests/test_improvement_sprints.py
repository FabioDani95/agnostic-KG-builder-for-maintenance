"""Focused tests for the current improvement set.

Covers:
  * JSON repair ladder in `ontology_pipeline._extract_json_object`
  * Candidate mining recall floor (Component + ErrorCode)
  * Type consistency advisory (tautological Symptom/FailureMode pair)
  * Existing ID catalog block rendering for the triplet extractor
  * Triplet extractor evidence_page parsing (new column)
  * material_context_not_linked warning in schema validation
  * Merge service evidence propagation + cross-schema fuzzy ID dedup
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.models import (
    CorrectiveAction,
    FailureMode,
    OntologyInstance,
    Severity,
    Symptom,
    Triplet,
)
from backend.prompts.extraction_prompt import (
    build_existing_id_catalog_block,
    build_extraction_prompt,
)
from backend.services.candidate_mining_service import (
    mine_candidates,
    render_candidates_prompt_block,
)
from backend.services.llm_service import parse_extraction
from backend.services.ontology_merge_service import merge_validated_triplets
from backend.services.ontology_pipeline import (
    _call_extractor_llm,
    _extract_json_object,
    _parse_json_completion_with_retry,
    _reset_parse_repair_events,
    consume_parse_repair_events,
    validate_ontology_instance,
)
from backend.services.ontology_schema_service import dump_ontology_schema_json, load_ontology_schema
from backend.services.type_consistency_service import evaluate_type_consistency


class JsonRepairLadderTests(unittest.TestCase):
    def setUp(self) -> None:
        _reset_parse_repair_events()

    def test_strict_parse_records_no_repair_event(self) -> None:
        parsed = _extract_json_object('{"nodes": {"Symptom": []}}')
        self.assertEqual(parsed, {"nodes": {"Symptom": []}})
        self.assertEqual(consume_parse_repair_events(), [])

    def test_substring_repair_fires_on_leading_prose(self) -> None:
        parsed = _extract_json_object('Here you go: {"nodes": {"Symptom": []}}   ')
        self.assertEqual(parsed, {"nodes": {"Symptom": []}})
        events = consume_parse_repair_events()
        self.assertEqual([e["strategy"] for e in events], ["substring_extraction"])

    def test_json_repair_library_handles_trailing_comma(self) -> None:
        parsed = _extract_json_object('{"nodes": {"Symptom": [{"id": "SYM-001",}]}')
        self.assertEqual(parsed, {"nodes": {"Symptom": [{"id": "SYM-001"}]}})
        strategies = [e["strategy"] for e in consume_parse_repair_events()]
        self.assertIn("json_repair_library", strategies)

    def test_completion_helper_retries_when_json_is_truncated_at_output_limit(self) -> None:
        completions = [
            ('{"nodes": {"Symptom": [{"symptom_id": "SYM-001"', {"completion": 16000}, "length"),
            ('{"nodes": {"Symptom": [{"symptom_id": "SYM-001"}]}}', {"completion": 20000}, "stop"),
        ]
        calls: list[int] = []

        def _run_completion(max_output_tokens: int):
            calls.append(max_output_tokens)
            return completions.pop(0)

        parsed, usages = _parse_json_completion_with_retry(
            phase_label="Draft",
            run_completion=_run_completion,
            initial_max_output_tokens=16000,
            retry_max_output_tokens=20000,
        )

        self.assertEqual(parsed, {"nodes": {"Symptom": [{"symptom_id": "SYM-001"}]}})
        self.assertEqual(calls, [16000, 20000])
        self.assertEqual(len(usages), 2)


class OntologyDraftResilienceTests(unittest.TestCase):
    def setUp(self) -> None:
        _reset_parse_repair_events()

    def test_call_extractor_llm_falls_back_to_empty_chunk_when_retry_still_returns_broken_json(self) -> None:
        schema = load_ontology_schema()

        class _FakeResponse:
            def __init__(self, content: str, *, completion_tokens: int, finish_reason: str):
                self.model = "gpt-5.4-2026-03-05"
                self.choices = [type("Choice", (), {
                    "message": type("Message", (), {"content": content})(),
                    "finish_reason": finish_reason,
                })()]
                self.usage = type("Usage", (), {
                    "prompt_tokens": 1234,
                    "completion_tokens": completion_tokens,
                    "total_tokens": 1234 + completion_tokens,
                    "prompt_tokens_details": type("PromptDetails", (), {"cached_tokens": 0})(),
                })()

        class _FakeCompletions:
            def __init__(self, responses):
                self._responses = list(responses)

            def create(self, **kwargs):
                return self._responses.pop(0)

        class _FakeClient:
            def __init__(self, responses):
                self.chat = type("Chat", (), {"completions": _FakeCompletions(responses)})()

        client = _FakeClient([
            _FakeResponse(
                '{"nodes": {"Asset": [{"asset_id": "ASSET-001", "name": "Demo"',
                completion_tokens=16000,
                finish_reason="length",
            ),
            _FakeResponse(
                '{"nodes": {"Asset": [{"asset_id": "ASSET-001", "name": "Demo"',
                completion_tokens=20000,
                finish_reason="length",
            ),
        ])

        state = {
            "schema": schema,
            "schema_json": dump_ontology_schema_json(),
            "source_type": "Service manual",
            "source_title": "Demo asset",
            "text_with_pages": "--- PAGE 1 ---\nDiagnostic content",
            "model_name": "gpt-5.4",
            "candidates_block": "",
            "asset_identity": {},
            "llm_usage": [],
        }

        with patch("backend.services.ontology_pipeline._get_client", return_value=client):
            result = _call_extractor_llm(state)

        self.assertEqual(sum(len(items) for items in result["ontology"].nodes.values()), 0)
        self.assertEqual(len(result["llm_usage"]), 2)
        self.assertIn(
            "fallback_empty_draft_chunk",
            [event["strategy"] for event in consume_parse_repair_events()],
        )


class CandidateMiningTests(unittest.TestCase):
    def test_component_and_error_code_recall(self) -> None:
        text = (
            "--- PAGE 1 ---\n"
            "Alarm 1234 is displayed when the spindle motor fails. "
            "Replace the ballscrew and check the encoder.\n"
            "--- PAGE 2 ---\n"
            "Error E504 indicates a low hydraulic pressure condition. "
            "Inspect the pump and solenoid valve.\n"
        )
        result = mine_candidates(text)
        component_terms = {c.term for c in result.components}
        # Must catch obvious maintenance components
        self.assertIn("spindle", component_terms)
        self.assertIn("motor", component_terms)
        self.assertIn("encoder", component_terms)
        self.assertIn("pump", component_terms)
        self.assertIn("valve", component_terms)

        error_tokens = {e.token for e in result.error_codes}
        self.assertIn("E504", error_tokens)
        self.assertIn("Alarm 1234", error_tokens)

    def test_render_prompt_block_mentions_candidates_and_recall_floor(self) -> None:
        result = mine_candidates("--- PAGE 1 ---\nThe motor drives the pump via a ballscrew.")
        block = render_candidates_prompt_block(result)
        self.assertIn("DETECTED CANDIDATES", block)
        self.assertIn("RECALL FLOOR", block)
        # Title-case rendering of a mined component
        self.assertIn("Motor", block)

    def test_empty_text_yields_empty_block(self) -> None:
        block = render_candidates_prompt_block(mine_candidates(""))
        self.assertEqual(block, "")


class TypeConsistencyTests(unittest.TestCase):
    def _ontology(self, symptoms: list[dict], failures: list[dict], relations: list[dict]) -> OntologyInstance:
        return OntologyInstance.model_validate({
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "Demo",
            "nodes": {
                "Asset": [],
                "Component": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
                "Symptom": symptoms,
                "FailureMode": failures,
            },
            "relations": relations,
        })

    def test_flags_pure_tautological_pair(self) -> None:
        ontology = self._ontology(
            symptoms=[{
                "symptom_id": "SYM-001",
                "name": "Alarm displayed",
                "description": "Alarm displayed on the controller screen.",
                "severity": "High",
            }],
            failures=[{
                "failure_mode_id": "FM-001",
                "name": "Alarm displayed",
                "description": "Alarm displayed on the controller screen.",
                "material_context": "Controller",
                "linked_symptom_id": "SYM-001",
            }],
            relations=[{
                "name": "MAY_INDICATE",
                "from_type": "Symptom", "from_id": "SYM-001",
                "to_type": "FailureMode", "to_id": "FM-001",
                "evidence": [],
            }],
        )
        issues, reports = evaluate_type_consistency(ontology)
        self.assertEqual(len(reports), 1)
        codes = [i.code for i in issues]
        self.assertIn("symptom_failure_duplicate", codes)

    def test_silent_when_failure_adds_distinctive_cause_token(self) -> None:
        ontology = self._ontology(
            symptoms=[{
                "symptom_id": "SYM-001",
                "name": "Tool changer hung up",
                "description": "The tool changer gets hung up during operation.",
                "severity": "High",
            }],
            failures=[{
                "failure_mode_id": "FM-001",
                "name": "Pneumatic valve stuck",
                "description": "Pneumatic solenoid valve stuck open on the ATC circuit.",
                "material_context": "ATC circuit",
                "linked_symptom_id": "SYM-001",
            }],
            relations=[{
                "name": "MAY_INDICATE",
                "from_type": "Symptom", "from_id": "SYM-001",
                "to_type": "FailureMode", "to_id": "FM-001",
                "evidence": [],
            }],
        )
        issues, _ = evaluate_type_consistency(ontology)
        self.assertEqual([i.code for i in issues], [])

    def test_shared_cause_token_in_symptom_does_not_suppress(self) -> None:
        """If 'damaged' already appears in the Symptom, it should NOT count as new causal context."""
        ontology = self._ontology(
            symptoms=[{
                "symptom_id": "SYM-001",
                "name": "Window damaged or scratched",
                "description": "Window damaged or scratched during operation.",
                "severity": "Medium",
            }],
            failures=[{
                "failure_mode_id": "FM-001",
                "name": "Window damaged or scratched",
                "description": "Window damaged or scratched during operation.",
                "material_context": "",
                "linked_symptom_id": "SYM-001",
            }],
            relations=[{
                "name": "MAY_INDICATE",
                "from_type": "Symptom", "from_id": "SYM-001",
                "to_type": "FailureMode", "to_id": "FM-001",
                "evidence": [],
            }],
        )
        issues, _ = evaluate_type_consistency(ontology)
        self.assertIn("symptom_failure_duplicate", [i.code for i in issues])


class ExistingIdCatalogBlockTests(unittest.TestCase):
    def test_empty_inputs_return_empty_string(self) -> None:
        self.assertEqual(build_existing_id_catalog_block(None), "")
        self.assertEqual(build_existing_id_catalog_block({}), "")
        self.assertEqual(build_existing_id_catalog_block({"nodes": {}}), "")

    def test_renders_known_id_buckets(self) -> None:
        draft = {
            "nodes": {
                "Symptom": [
                    {"symptom_id": "sym_low_power", "name": "Low power"},
                    {"symptom_id": "SYM-002", "name": "Tool jam"},
                ],
                "FailureMode": [
                    {"failure_mode_id": "fm_broken_valve", "name": "Broken valve"},
                ],
                "CorrectiveAction": [
                    {"action_id": "ca_replace_valve", "name": "Replace valve"},
                ],
            }
        }
        block = build_existing_id_catalog_block(draft)
        self.assertIn("EXISTING ENTITY IDS", block)
        self.assertIn("sym_low_power", block)
        self.assertIn("SYM-002", block)
        self.assertIn("fm_broken_valve", block)
        self.assertIn("ca_replace_valve", block)

    def test_block_is_injected_into_extraction_prompt(self) -> None:
        draft = {"nodes": {"Symptom": [{"symptom_id": "sym_x", "name": "X"}]}}
        block = build_existing_id_catalog_block(draft)
        prompt = build_extraction_prompt(
            "Service Manual",
            "Demo",
            existing_id_catalog_block=block,
        )
        self.assertIn("EXISTING ENTITY IDS", prompt)
        self.assertIn("sym_x", prompt)


class EvidencePageParsingTests(unittest.TestCase):
    def test_parse_extraction_reads_evidence_page_columns(self) -> None:
        raw = (
            "### Table 1: Symptoms\n"
            "| symptom_id | name | description | severity | evidence_page |\n"
            "|---|---|---|---|---|\n"
            "| SYM-001 | Low pressure | Pressure drops | High | 5 |\n"
            "| SYM-002 | Tool jam | Tool changer jams | Medium | PAGE 12 |\n"
            "\n"
            "### Table 2: FailureModes\n"
            "| failure_mode_id | name | description | material_context | linked_symptom_id | evidence_page |\n"
            "|---|---|---|---|---|---|\n"
            "| FM-001 | Worn valve | Valve worn | Pump | SYM-001 | 7 |\n"
            "\n"
            "### Table 3: CorrectiveActions\n"
            "| action_id | name | description | instruction_text | source_type | source_title | source_page | linked_failure_mode_id |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| CA-001 | Replace | replace | 1. replace | Service Manual | Demo | 10 | FM-001 |\n"
        )
        result = parse_extraction(raw, "Service Manual", "Demo")
        triplets = {t.symptom.symptom_id: t for t in result.triplets}
        self.assertEqual(triplets["SYM-001"].symptom.evidence_page, 5)
        self.assertEqual(triplets["SYM-002"].symptom.evidence_page, 12)
        self.assertEqual(triplets["SYM-001"].failure_modes[0].evidence_page, 7)

    def test_parse_extraction_back_compat_missing_evidence_column(self) -> None:
        raw = (
            "### Table 1: Symptoms\n"
            "| symptom_id | name | description | severity |\n"
            "|---|---|---|---|\n"
            "| SYM-001 | Low pressure | Pressure drops | High |\n"
            "\n"
            "### Table 2: FailureModes\n"
            "| failure_mode_id | name | description | material_context | linked_symptom_id |\n"
            "|---|---|---|---|---|\n"
            "| FM-001 | Worn valve | Valve worn | Pump | SYM-001 |\n"
            "\n"
            "### Table 3: CorrectiveActions\n"
            "| action_id | name | description | instruction_text | source_type | source_title | source_page | linked_failure_mode_id |\n"
            "|---|---|---|---|---|---|---|---|\n"
            "| CA-001 | Replace | replace | 1. replace | Service Manual | Demo | 10 | FM-001 |\n"
        )
        result = parse_extraction(raw, "Service Manual", "Demo")
        t = result.triplets[0]
        self.assertEqual(t.symptom.evidence_page, 0)
        self.assertEqual(t.failure_modes[0].evidence_page, 0)


class MaterialContextValidationTests(unittest.TestCase):
    def _ontology(self, components: list[dict], failure_modes: list[dict]) -> OntologyInstance:
        return OntologyInstance.model_validate({
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "Demo",
            "nodes": {
                "Asset": [{
                    "asset_id": "ASSET-001", "name": "Demo", "description": "d",
                    "brand": "", "model": "", "asset_type": "machine",
                }],
                "Component": components,
                "Symptom": [{
                    "symptom_id": "SYM-001", "name": "sym", "description": "d", "severity": "High",
                }],
                "FailureMode": failure_modes,
                "CorrectiveAction": [{
                    "action_id": "CA-001", "name": "a", "description": "d",
                    "instruction_text": "1. x", "source_type": "Service Manual",
                    "source_title": "Demo", "source_page": 1, "source_reference": "PAGE 1",
                }],
                "ErrorCode": [],
            },
            "relations": [
                {"name": "HAS_COMPONENT", "from_type": "Asset", "from_id": "ASSET-001",
                 "to_type": "Component", "to_id": "CMP-001", "evidence": []},
                {"name": "MAY_INDICATE", "from_type": "Symptom", "from_id": "SYM-001",
                 "to_type": "FailureMode", "to_id": "FM-001", "evidence": []},
                {"name": "RESOLVED_BY", "from_type": "FailureMode", "from_id": "FM-001",
                 "to_type": "CorrectiveAction", "to_id": "CA-001", "evidence": []},
            ],
        })

    def test_warns_when_material_context_is_free_text(self) -> None:
        ontology = self._ontology(
            components=[{
                "component_id": "CMP-001", "name": "Pump",
                "description": "Main pump", "category": "Hydraulics",
            }],
            failure_modes=[{
                "failure_mode_id": "FM-001", "name": "Worn pump", "description": "Pump worn",
                "material_context": "Hydraulic valve",
                "linked_symptom_id": "SYM-001",
            }],
        )
        issues, _ = validate_ontology_instance(ontology)
        codes = {(i.code, i.target_id) for i in issues}
        self.assertIn(("material_context_not_linked", "FM-001"), codes)

    def test_silent_when_material_context_is_component_id(self) -> None:
        ontology = self._ontology(
            components=[{
                "component_id": "CMP-001", "name": "Pump",
                "description": "Main pump", "category": "Hydraulics",
            }],
            failure_modes=[{
                "failure_mode_id": "FM-001", "name": "Worn pump", "description": "Pump worn",
                "material_context": "CMP-001",
                "linked_symptom_id": "SYM-001",
            }],
        )
        issues, _ = validate_ontology_instance(ontology)
        codes = {i.code for i in issues}
        self.assertNotIn("material_context_not_linked", codes)


class MergeEvidenceAndDedupTests(unittest.TestCase):
    def _empty_base(self, components: list[dict] | None = None) -> dict:
        return {
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "Demo",
            "nodes": {
                "Asset": [{
                    "asset_id": "ASSET-001", "name": "Demo", "description": "d",
                    "brand": "", "model": "", "asset_type": "machine",
                }],
                "Component": components or [],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            "relations": [],
        }

    def test_may_indicate_and_resolved_by_emit_evidence_entries(self) -> None:
        base = self._empty_base()
        merged = merge_validated_triplets(base, [
            Triplet(
                symptom=Symptom(symptom_id="SYM-001", name="sym",
                                description="d", severity=Severity.HIGH, evidence_page=5),
                failure_modes=[FailureMode(
                    failure_mode_id="FM-001", name="fm", description="d",
                    material_context="controller", linked_symptom_id="SYM-001",
                    evidence_page=7,
                )],
                corrective_actions=[CorrectiveAction(
                    action_id="CA-001", name="ca", description="d",
                    instruction_text="1. x", source_type="Service Manual",
                    source_title="Demo", source_page=9, linked_failure_mode_id="FM-001",
                )],
            ),
        ])
        relations_by_name: dict[str, dict] = {r["name"]: r for r in merged["relations"]}
        may = relations_by_name["MAY_INDICATE"]
        resolved = relations_by_name["RESOLVED_BY"]
        self.assertTrue(any(e.get("source_page") == 5 for e in may["evidence"]))
        self.assertTrue(any(e.get("source_page") == 7 for e in may["evidence"]))
        self.assertTrue(any(e.get("source_page") == 9 for e in resolved["evidence"]))

    def test_affects_inferred_from_material_context_carries_evidence(self) -> None:
        base = self._empty_base(components=[{
            "component_id": "CMP-PUMP", "name": "Hydraulic pump",
            "description": "Main hydraulic pump", "category": "Hydraulics",
        }])
        base["relations"].append({
            "name": "HAS_COMPONENT", "from_type": "Asset", "from_id": "ASSET-001",
            "to_type": "Component", "to_id": "CMP-PUMP", "evidence": [],
        })
        merged = merge_validated_triplets(base, [
            Triplet(
                symptom=Symptom(symptom_id="SYM-001", name="low pressure",
                                description="Hydraulic pressure drops", severity=Severity.HIGH),
                failure_modes=[FailureMode(
                    failure_mode_id="FM-001", name="Worn pump",
                    description="Hydraulic pump internals are worn",
                    material_context="Hydraulic pump",
                    linked_symptom_id="SYM-001", evidence_page=7,
                )],
                corrective_actions=[CorrectiveAction(
                    action_id="CA-001", name="Replace pump", description="replace",
                    instruction_text="1. replace", source_type="Service Manual",
                    source_title="Demo", source_page=12, linked_failure_mode_id="FM-001",
                )],
            ),
        ])
        affects = [r for r in merged["relations"]
                   if r["name"] == "AFFECTS" and r["to_id"] == "CMP-PUMP"]
        self.assertEqual(len(affects), 1)
        self.assertTrue(any(e.get("source_page") == 7 for e in affects[0]["evidence"]))

    def test_cross_schema_fuzzy_match_preserves_descriptive_ids(self) -> None:
        base = {
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "Demo",
            "nodes": {
                "Asset": [],
                "Component": [],
                "ErrorCode": [],
                "Symptom": [{
                    "symptom_id": "sym_no_power",
                    "name": "System does not start",
                    "description": "The control box has no power.",
                    "severity": "High",
                }],
                "FailureMode": [{
                    "failure_mode_id": "fm_loose_connector",
                    "name": "Loose power connector",
                    "description": "The power connector is loose.",
                    "material_context": "Control box",
                }],
                "CorrectiveAction": [{
                    "action_id": "ca_reconnect",
                    "name": "Reconnect connector",
                    "description": "Reconnect the loose connector.",
                    "instruction_text": "1. Power off\n2. Reconnect",
                    "source_type": "Service Manual",
                    "source_title": "Demo",
                    "source_page": 10,
                    "source_reference": "PAGE 10",
                }],
            },
            "relations": [
                {"name": "MAY_INDICATE", "from_type": "Symptom",
                 "from_id": "sym_no_power", "to_type": "FailureMode",
                 "to_id": "fm_loose_connector", "evidence": []},
                {"name": "RESOLVED_BY", "from_type": "FailureMode",
                 "from_id": "fm_loose_connector", "to_type": "CorrectiveAction",
                 "to_id": "ca_reconnect", "evidence": []},
            ],
        }
        merged = merge_validated_triplets(base, [
            Triplet(
                symptom=Symptom(
                    symptom_id="SYM-001",
                    name="System will not start",
                    description="No power from the control box prevents startup.",
                    severity=Severity.CRITICAL,
                ),
                failure_modes=[FailureMode(
                    failure_mode_id="FM-001",
                    name="Power connector loose",
                    description="Loose connector at the control box power input.",
                    material_context="Controller",
                    linked_symptom_id="SYM-001",
                )],
                corrective_actions=[CorrectiveAction(
                    action_id="CA-001",
                    name="Reconnect the power connector",
                    description="Reconnect the power connector at the control box.",
                    instruction_text="1. Power off\n2. Reconnect",
                    source_type="Service Manual",
                    source_title="Demo",
                    source_page=10,
                    linked_failure_mode_id="FM-001",
                )],
            ),
        ])
        symptom_ids = [s["symptom_id"] for s in merged["nodes"]["Symptom"]]
        failure_ids = [f["failure_mode_id"] for f in merged["nodes"]["FailureMode"]]
        action_ids = [a["action_id"] for a in merged["nodes"]["CorrectiveAction"]]
        self.assertEqual(symptom_ids, ["sym_no_power"])
        self.assertEqual(failure_ids, ["fm_loose_connector"])
        self.assertEqual(action_ids, ["ca_reconnect"])


if __name__ == "__main__":
    unittest.main()
