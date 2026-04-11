"""Unit tests for the Step 3 schema-aware confidence scoring service."""
import unittest

from backend.models import (
    HumanRequiredField,
    OntologyInstance,
    OntologyRelationInstance,
    PipelineIssue,
)
from backend.services.confidence import score_ontology
from backend.services.ontology_schema_service import load_ontology_schema


def _base_ontology() -> OntologyInstance:
    """A small but schema-complete ontology with a single Symptom→FM→CA chain."""
    return OntologyInstance(
        ontology_name="diagnostic",
        version="V1",
        language="en",
        source_type="Operating manual",
        source_title="TestBot",
        nodes={
            "Asset": [{
                "asset_id": "ASSET-001",
                "name": "TestBot",
                "description": "Test asset",
                "brand": "Acme",
                "model": "X1",
                "asset_type": "robot",
                "evidence": [{"source_page": 1, "source_reference": "", "quote": ""}],
            }],
            "Component": [{
                "component_id": "COMP-001",
                "name": "Joint",
                "description": "J1 servo",
                "category": "actuator",
                "evidence": [{"source_page": 2, "source_reference": "", "quote": ""}],
            }],
            "Symptom": [{
                "symptom_id": "SYM-001",
                "name": "Vibration",
                "description": "Unusual vibration on J1",
                "severity": "Medium",
                "evidence": [
                    {"source_page": 10, "source_reference": "", "quote": ""},
                    {"source_page": 11, "source_reference": "", "quote": ""},
                ],
            }],
            "FailureMode": [{
                "failure_mode_id": "FM-001",
                "name": "Bearing wear",
                "description": "Worn bearing in J1",
                "material_context": "",
                "evidence": [{"source_page": 12, "source_reference": "", "quote": ""}],
            }],
            "CorrectiveAction": [{
                "action_id": "CA-001",
                "name": "Replace bearing",
                "description": "Swap the worn bearing",
                "instruction_text": "Follow procedure 4.2",
                "source_type": "Operating manual",
                "source_title": "TestBot",
                "source_page": 13,
                "evidence": [{"source_page": 13, "source_reference": "", "quote": ""}],
            }],
        },
        relations=[
            OntologyRelationInstance(
                name="HAS_COMPONENT",
                from_type="Asset", from_id="ASSET-001",
                to_type="Component", to_id="COMP-001",
            ),
            OntologyRelationInstance(
                name="MAY_INDICATE",
                from_type="Symptom", from_id="SYM-001",
                to_type="FailureMode", to_id="FM-001",
            ),
            OntologyRelationInstance(
                name="RESOLVED_BY",
                from_type="FailureMode", from_id="FM-001",
                to_type="CorrectiveAction", to_id="CA-001",
            ),
            OntologyRelationInstance(
                name="AFFECTS",
                from_type="FailureMode", from_id="FM-001",
                to_type="Component", to_id="COMP-001",
            ),
        ],
    )


class ConfidenceScoringTests(unittest.TestCase):
    def setUp(self):
        self.schema = load_ontology_schema()

    # ─── happy path ──────────────────────────────────────────────────────

    def test_complete_node_gets_high_score(self):
        ontology = _base_ontology()
        report = score_ontology(ontology=ontology, schema=self.schema)

        # Every entry must classify and score
        self.assertTrue(len(report.entries) > 0)
        for entry in report.entries:
            self.assertGreaterEqual(entry.score, 0.0)
            self.assertLessEqual(entry.score, 1.0)
            self.assertIn(entry.classification, {"auto_approve", "human_review", "auto_reject"})

        # The Symptom with 2 corroborating pages + full chain participation should be auto_approve
        sym = next(e for e in report.entries if e.node_type == "Symptom")
        self.assertGreaterEqual(sym.score, 0.80)
        self.assertEqual(sym.classification, "auto_approve")

    def test_counts_sum_matches_total_entries(self):
        ontology = _base_ontology()
        report = score_ontology(ontology=ontology, schema=self.schema)
        self.assertEqual(sum(report.counts.values()), len(report.entries))

    # ─── signal sensitivity ──────────────────────────────────────────────

    def test_missing_evidence_lowers_score(self):
        ontology = _base_ontology()
        # Strip evidence from the Symptom AND from its incident relations
        ontology.nodes["Symptom"][0]["evidence"] = []
        # Ensure relations also carry no evidence for this node
        for rel in ontology.relations:
            rel.evidence = []
        report = score_ontology(ontology=ontology, schema=self.schema)

        sym = next(e for e in report.entries if e.node_type == "Symptom")
        self.assertEqual(sym.signals["evidence_present"], 0.0)
        self.assertEqual(sym.signals["corroboration"], 0.0)
        self.assertIn("no evidence attached", sym.reasons)

    def test_evidence_propagated_from_relations(self):
        """Nodes without own evidence get provenance from incident relation evidence."""
        ontology = _base_ontology()
        # Strip node-level evidence from all nodes
        for items in ontology.nodes.values():
            for item in items:
                item["evidence"] = []
        # Attach evidence to a relation touching SYM-001
        from backend.models import OntologyEvidence
        for rel in ontology.relations:
            if rel.name == "MAY_INDICATE":
                rel.evidence = [
                    OntologyEvidence(source_page=10),
                    OntologyEvidence(source_page=11),
                ]
        report = score_ontology(ontology=ontology, schema=self.schema)

        sym = next(e for e in report.entries if e.node_type == "Symptom")
        # evidence_present should now be 1.0 because of relation propagation
        self.assertEqual(sym.signals["evidence_present"], 1.0)
        # corroboration > 0 (2 propagated pages at 0.5 weight each = 1 effective page)
        self.assertGreater(sym.signals["corroboration"], 0.0)
        # reason should be "inferred from relations" not "no evidence attached"
        self.assertNotIn("no evidence attached", sym.reasons)
        self.assertIn("evidence inferred from relations only", sym.reasons)

        # FM-001 also appears in MAY_INDICATE (to_id) → also gets provenance
        fm = next(e for e in report.entries if e.node_type == "FailureMode")
        self.assertEqual(fm.signals["evidence_present"], 1.0)

    def test_missing_required_property_lowers_score(self):
        ontology = _base_ontology()
        # Remove a required property from FailureMode
        ontology.nodes["FailureMode"][0]["description"] = ""
        report = score_ontology(ontology=ontology, schema=self.schema)

        fm = next(e for e in report.entries if e.node_type == "FailureMode")
        self.assertLess(fm.signals["required_props_complete"], 1.0)
        self.assertIn("missing required properties", fm.reasons)

    def test_missing_chain_relation_penalizes_failure_mode(self):
        ontology = _base_ontology()
        # Drop the RESOLVED_BY relation — FailureMode loses outgoing chain participation
        ontology.relations = [r for r in ontology.relations if r.name != "RESOLVED_BY"]
        report = score_ontology(ontology=ontology, schema=self.schema)

        fm = next(e for e in report.entries if e.node_type == "FailureMode")
        self.assertLess(fm.signals["chain_participation"], 1.0)
        self.assertIn("incomplete schema-expected relations", fm.reasons)

    # ─── penalties ───────────────────────────────────────────────────────

    def test_human_binding_penalty_applied(self):
        ontology = _base_ontology()
        human_fields = [HumanRequiredField(
            field_key="asset_type",
            prompt="",
            target_type="Asset",
            target_id="ASSET-001",
            property_name="asset_type",
            reason="",
        )]
        report = score_ontology(
            ontology=ontology,
            schema=self.schema,
            human_required_fields=human_fields,
        )
        asset = next(e for e in report.entries if e.node_type == "Asset")
        self.assertIn("human_binding_required", asset.penalties)
        self.assertIn("human binding required", asset.reasons)

    def test_retry_penalty_applied(self):
        ontology = _base_ontology()
        report = score_ontology(
            ontology=ontology,
            schema=self.schema,
            retry_count=2,
        )
        # All entries should carry the per_retry penalty since retry_count > 0
        for entry in report.entries:
            self.assertIn("per_retry", entry.penalties)

    def test_semantic_issue_on_node_kills_clean_extraction_signal(self):
        ontology = _base_ontology()
        issues = [PipelineIssue(
            severity="error",
            code="bad_property",
            message="description too short",
            target_type="Symptom",
            target_id="SYM-001",
        )]
        report = score_ontology(
            ontology=ontology,
            schema=self.schema,
            semantic_issues=issues,
        )
        sym = next(e for e in report.entries if e.node_type == "Symptom")
        self.assertEqual(sym.signals["clean_extraction"], 0.0)

    # ─── classification boundaries ───────────────────────────────────────

    def test_auto_reject_disabled_by_default(self):
        # Build an intentionally broken ontology
        ontology = _base_ontology()
        for items in ontology.nodes.values():
            for item in items:
                item["evidence"] = []
                for key in list(item.keys()):
                    if key.endswith("_id"):
                        continue
                    if isinstance(item[key], str):
                        item[key] = ""
        ontology.relations = []
        report = score_ontology(ontology=ontology, schema=self.schema)
        # With auto_reject off (default), nothing should be auto_rejected
        self.assertEqual(report.counts.get("auto_reject", 0), 0)

    def test_auto_reject_enabled_via_config_override(self):
        ontology = _base_ontology()
        for items in ontology.nodes.values():
            for item in items:
                item["evidence"] = []
                for key in list(item.keys()):
                    if key.endswith("_id"):
                        continue
                    if isinstance(item[key], str):
                        item[key] = ""
        ontology.relations = []
        custom_cfg = {
            "enabled": True,
            "theta_high": 0.80,
            "theta_low": 0.45,
            "auto_reject_enabled": True,
            "weights": {
                "evidence_present": 0.25,
                "corroboration": 0.15,
                "required_props_complete": 0.25,
                "chain_participation": 0.20,
                "clean_extraction": 0.15,
            },
            "penalties": {"human_binding_required": 0.20, "per_retry": 0.05},
        }
        report = score_ontology(ontology=ontology, schema=self.schema, config=custom_cfg)
        self.assertGreaterEqual(report.counts.get("auto_reject", 0), 1)

    def test_disabled_config_short_circuits(self):
        ontology = _base_ontology()
        custom_cfg = {"enabled": False}
        report = score_ontology(ontology=ontology, schema=self.schema, config=custom_cfg)
        self.assertEqual(len(report.entries), 0)


if __name__ == "__main__":
    unittest.main()
