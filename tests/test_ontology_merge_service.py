import unittest

from backend.models import CorrectiveAction, FailureMode, Severity, Symptom, Triplet
from backend.services.ontology_merge_service import merge_validated_triplets


class OntologyMergeServiceTests(unittest.TestCase):
    def test_merge_adds_missing_has_component_relation(self):
        base = {
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "Demo",
            "nodes": {
                "Asset": [
                    {
                        "asset_id": "ASSET-001",
                        "name": "Demo",
                        "description": "Demo asset",
                        "brand": "Demo",
                        "model": "One",
                        "asset_type": "machine",
                    }
                ],
                "Component": [
                    {
                        "component_id": "CMP-001",
                        "name": "Pump",
                        "description": "Main pump",
                        "category": "Hydraulics",
                    }
                ],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            "relations": [],
        }

        merged = merge_validated_triplets(base, [])

        self.assertTrue(any(
            rel["name"] == "HAS_COMPONENT" and rel["from_id"] == "ASSET-001" and rel["to_id"] == "CMP-001"
            for rel in merged["relations"]
        ))

    def test_merge_preserves_existing_component_context(self):
        base = {
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "Demo",
            "nodes": {
                "Asset": [
                    {
                        "asset_id": "ASSET-001",
                        "name": "Demo",
                        "description": "Demo asset",
                        "brand": "Demo",
                        "model": "One",
                        "asset_type": "machine",
                    }
                ],
                "Component": [
                    {
                        "component_id": "CMP-001",
                        "name": "Pump",
                        "description": "Main pump",
                        "category": "Hydraulics",
                    }
                ],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            "relations": [
                {
                    "name": "HAS_COMPONENT",
                    "from_type": "Asset",
                    "from_id": "ASSET-001",
                    "to_type": "Component",
                    "to_id": "CMP-001",
                    "evidence": [],
                },
            ],
        }

        merged = merge_validated_triplets(base, [])

        self.assertEqual(len(merged["nodes"]["Component"]), 1)
        self.assertEqual(len(merged["relations"]), 1)
        self.assertEqual(merged["relations"][0]["name"], "HAS_COMPONENT")

    def test_merge_validated_triplets_reuses_existing_semantic_nodes(self):
        base = {
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "UR Series Control box 5.5/5.6",
            "nodes": {
                "Asset": [],
                "Component": [],
                "Symptom": [
                    {
                        "symptom_id": "SYM-BASE",
                        "name": "System does not start",
                        "description": "The control box has no power.",
                        "severity": "High",
                    }
                ],
                "FailureMode": [
                    {
                        "failure_mode_id": "FM-BASE",
                        "name": "Loose power connector",
                        "description": "The power connector is loose.",
                        "material_context": "Control box",
                    }
                ],
                "CorrectiveAction": [
                    {
                        "action_id": "CA-BASE",
                        "name": "Reconnect power connector",
                        "description": "Reconnect the loose power connector.",
                        "instruction_text": "1. Power off the system\n2. Reconnect the power connector",
                        "source_type": "Service Manual",
                        "source_title": "UR Series Control box 5.5/5.6",
                        "source_page": 10,
                        "source_reference": "PAGE 10",
                    }
                ],
                "ErrorCode": [],
            },
            "relations": [
                {
                    "name": "MAY_INDICATE",
                    "from_type": "Symptom",
                    "from_id": "SYM-BASE",
                    "to_type": "FailureMode",
                    "to_id": "FM-BASE",
                    "evidence": [],
                },
                {
                    "name": "RESOLVED_BY",
                    "from_type": "FailureMode",
                    "from_id": "FM-BASE",
                    "to_type": "CorrectiveAction",
                    "to_id": "CA-BASE",
                    "evidence": [],
                },
            ],
        }

        merged = merge_validated_triplets(base, [
            Triplet(
                symptom=Symptom(
                    symptom_id="SYM-NEW",
                    name="System will not start",
                    description="No power from the control box prevents startup.",
                    severity=Severity.CRITICAL,
                ),
                failure_modes=[
                    FailureMode(
                        failure_mode_id="FM-NEW",
                        name="Power connector loose",
                        description="Loose connector at the control box power input.",
                        material_context="Controller",
                        linked_symptom_id="SYM-NEW",
                    ),
                ],
                corrective_actions=[
                    CorrectiveAction(
                        action_id="CA-NEW",
                        name="Reconnect the power connector",
                        description="Reconnect the power connector at the control box.",
                        instruction_text="1. Power off the system\n2. Reconnect the power connector",
                        source_type="Service Manual",
                        source_title="UR Series Control box 5.5/5.6",
                        source_page=11,
                        linked_failure_mode_id="FM-NEW",
                    ),
                ],
            )
        ])

        self.assertEqual(len(merged["nodes"]["Symptom"]), 1)
        self.assertEqual(len(merged["nodes"]["FailureMode"]), 1)
        self.assertEqual(len(merged["nodes"]["CorrectiveAction"]), 1)
        self.assertEqual(merged["nodes"]["Symptom"][0]["symptom_id"], "SYM-BASE")
        self.assertEqual(merged["nodes"]["FailureMode"][0]["failure_mode_id"], "FM-BASE")
        self.assertEqual(merged["nodes"]["CorrectiveAction"][0]["action_id"], "CA-BASE")
        self.assertEqual(len(merged["relations"]), 2)

    def test_merge_infers_affects_relation_from_existing_component(self):
        base = {
            "ontology_name": "diagnostic",
            "version": "V1",
            "language": "en",
            "source_type": "Service Manual",
            "source_title": "Pump skid",
            "nodes": {
                "Asset": [
                    {
                        "asset_id": "ASSET-001",
                        "name": "Pump skid",
                        "description": "Pump skid",
                        "brand": "Demo",
                        "model": "S1",
                        "asset_type": "pump skid",
                    }
                ],
                "Component": [
                    {
                        "component_id": "CMP-PUMP",
                        "name": "Hydraulic pump",
                        "description": "Main hydraulic pump assembly",
                        "category": "Hydraulics",
                    }
                ],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            "relations": [
                {
                    "name": "HAS_COMPONENT",
                    "from_type": "Asset",
                    "from_id": "ASSET-001",
                    "to_type": "Component",
                    "to_id": "CMP-PUMP",
                    "evidence": [],
                },
            ],
        }

        merged = merge_validated_triplets(base, [
            Triplet(
                symptom=Symptom(
                    symptom_id="SYM-001",
                    name="Low hydraulic pressure",
                    description="Hydraulic pressure drops during operation.",
                    severity=Severity.HIGH,
                ),
                failure_modes=[
                    FailureMode(
                        failure_mode_id="FM-001",
                        name="Hydraulic pump wear",
                        description="Pump internals are worn.",
                        material_context="Hydraulic pump",
                        linked_symptom_id="SYM-001",
                    ),
                ],
                corrective_actions=[
                    CorrectiveAction(
                        action_id="CA-001",
                        name="Replace hydraulic pump",
                        description="Replace the worn hydraulic pump.",
                        instruction_text="1. Shut down the skid\n2. Replace the hydraulic pump",
                        source_type="Service Manual",
                        source_title="Pump skid",
                        source_page=12,
                        linked_failure_mode_id="FM-001",
                    ),
                ],
            )
        ])

        self.assertTrue(any(
            rel["name"] == "AFFECTS" and rel["to_id"] == "CMP-PUMP"
            for rel in merged["relations"]
        ))


if __name__ == "__main__":
    unittest.main()
