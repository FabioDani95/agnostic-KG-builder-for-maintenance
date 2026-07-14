"""Regression tests for the fixes surfaced by the 588-page Haas manual run:

1. resolution-completion prompt embeds a compact id+name node view, so the
   prompt no longer scales with graph size (was: every target skipped as
   input_too_large on a 741-node graph);
2. apply_ontology_patch rejects patched relations whose endpoints do not
   exist in the merged instance (was: dangling RESOLVED_BY edges → blocking);
3. normalization drops AFFECTS edges targeting the Asset node itself
   (was: blocking domain/range violations).
"""

from __future__ import annotations

import unittest

from backend.models import OntologyInstance
from backend.services.ontology_patch_service import apply_ontology_patch
from backend.services.ontology_pipeline import (
    normalize_ontology_instance,
    validate_ontology_instance,
)
from backend.services.resolution_completion_service import (
    ResolutionTarget,
    _target_prompt,
)
from backend.services.review_queue_service import build_review_queue


def _ontology(nodes: dict | None = None, relations: list | None = None) -> OntologyInstance:
    base = {
        "Asset": [{
            "asset_id": "asset_demo", "name": "Demo", "description": "d",
            "brand": "Demo", "model": "M1", "asset_type": "machine",
        }],
        "Component": [],
        "Symptom": [],
        "FailureMode": [],
        "CorrectiveAction": [],
        "ErrorCode": [],
    }
    base.update(nodes or {})
    return OntologyInstance.model_validate({
        "ontology_name": "diagnostic", "version": "V1", "language": "en",
        "source_type": "Operator manual", "source_title": "Demo",
        "nodes": base, "relations": relations or [],
    })


class CompactResolutionPromptTests(unittest.TestCase):
    def test_prompt_node_dump_does_not_scale_with_node_payloads(self) -> None:
        long_text = "step " * 400  # ~2000 chars per node
        failure_modes = [{
            "failure_mode_id": f"fm_{i}", "name": f"Failure {i}",
            "description": long_text, "material_context": "asset_level",
        } for i in range(120)]
        actions = [{
            "action_id": f"ca_{i}", "name": f"Action {i}",
            "description": long_text, "instruction_text": long_text,
            "source_type": "m", "source_title": "t",
            "source_page": 1, "source_reference": "PAGE 1",
        } for i in range(120)]
        ontology = _ontology({"FailureMode": failure_modes, "CorrectiveAction": actions})
        target = ResolutionTarget("failure_mode", "fm_1", "Failure 1", "failure 1")

        _, user_prefix = _target_prompt(target, ontology)

        # Full payloads would exceed ~480k chars here; the compact view must
        # stay well inside the 50k input guardrail and never leak long fields.
        self.assertLess(len(user_prefix), 40000)
        self.assertNotIn("step step", user_prefix)
        # Ids and names are preserved for reuse.
        self.assertIn("fm_119", user_prefix)
        self.assertIn("Action 119", user_prefix)


class PatchDanglingRelationTests(unittest.TestCase):
    _PREVIOUS = {
        "ontology_name": "diagnostic", "version": "V1", "language": "en",
        "source_type": "m", "source_title": "t",
        "nodes": {
            "FailureMode": [{
                "failure_mode_id": "fm_estop_pressed", "name": "E-stop pressed",
                "description": "d", "material_context": "asset_level",
            }],
            "CorrectiveAction": [{
                "action_id": "ca_release_estop", "name": "Release E-stop",
                "description": "d", "instruction_text": "1. Release.",
            }],
        },
        "relations": [],
    }

    def test_contradictory_patch_cannot_add_relation_from_removed_node(self) -> None:
        patch = {
            "remove_node_ids": ["fm_estop_pressed"],
            "add_relations": [{
                "name": "RESOLVED_BY", "from_type": "FailureMode",
                "from_id": "fm_estop_pressed", "to_type": "CorrectiveAction",
                "to_id": "ca_release_estop", "evidence": [],
            }],
        }
        merged, report = apply_ontology_patch(self._PREVIOUS, patch)

        self.assertEqual(merged["relations"], [])
        self.assertEqual(report["skipped_dangling_relations"], 1)
        self.assertEqual(report["added_relations"], 0)

    def test_relation_to_invented_id_is_skipped(self) -> None:
        patch = {
            "add_relations": [{
                "name": "RESOLVED_BY", "from_type": "FailureMode",
                "from_id": "fm_never_existed", "to_type": "CorrectiveAction",
                "to_id": "ca_release_estop", "evidence": [],
            }],
        }
        merged, report = apply_ontology_patch(self._PREVIOUS, patch)

        self.assertEqual(merged["relations"], [])
        self.assertEqual(report["skipped_dangling_relations"], 1)

    def test_valid_added_relation_still_applies(self) -> None:
        patch = {
            "add_relations": [{
                "name": "RESOLVED_BY", "from_type": "FailureMode",
                "from_id": "fm_estop_pressed", "to_type": "CorrectiveAction",
                "to_id": "ca_release_estop", "evidence": [],
            }],
        }
        merged, report = apply_ontology_patch(self._PREVIOUS, patch)

        self.assertEqual(len(merged["relations"]), 1)
        self.assertEqual(report["added_relations"], 1)
        self.assertEqual(report["skipped_dangling_relations"], 0)


class OperationalStateReviewFlagTests(unittest.TestCase):
    def test_operational_state_fm_surfaces_as_advisory_not_blocking(self) -> None:
        ontology = _ontology({
            "Symptom": [{
                "symptom_id": "sym_no_start", "name": "Machine will not start",
                "description": "The machine does not start.", "severity": "Medium",
            }],
            "FailureMode": [{
                "failure_mode_id": "fm_estop_pressed", "name": "Emergency Stop button activated",
                "description": "The e-stop button is pressed.", "material_context": "asset_level",
            }],
        }, [{
            "name": "MAY_INDICATE", "from_type": "Symptom", "from_id": "sym_no_start",
            "to_type": "FailureMode", "to_id": "fm_estop_pressed", "evidence": [],
        }])

        schema_issues, _ = validate_ontology_instance(ontology)
        op_state = [i for i in schema_issues if i.code == "operational_state_failure_mode"]
        self.assertEqual(len(op_state), 1)
        self.assertEqual(op_state[0].severity, "warning")  # advisory, never blocking

        queue = build_review_queue(ontology.model_dump(), schema_issues=schema_issues)
        entry = next((i for i in queue if i.get("kind") == "operational_state_failure_mode"), None)
        self.assertIsNotNone(entry)
        self.assertEqual(entry["severity"], "advisory")
        self.assertEqual(entry["target_id"], "fm_estop_pressed")


class AffectsAssetTargetTests(unittest.TestCase):
    def test_affects_pointing_at_the_asset_is_dropped(self) -> None:
        ontology = _ontology(
            {
                "FailureMode": [{
                    "failure_mode_id": "fm_pallet_wrong", "name": "Loaded pallet incorrect",
                    "description": "d", "material_context": "asset_level",
                }],
            },
            [{
                "name": "AFFECTS", "from_type": "FailureMode",
                "from_id": "fm_pallet_wrong", "to_type": "Component",
                "to_id": "asset_demo", "evidence": [],
            }],
        )

        normalized = normalize_ontology_instance(ontology)

        self.assertFalse(any(rel.name == "AFFECTS" for rel in normalized.relations))


if __name__ == "__main__":
    unittest.main()
