import unittest

from backend.services.legacy_ontology_migration import migrate_legacy_ontology
from backend.services.ontology_contract import (
    build_and_validate_contract_ontology,
    build_contract_ontology,
)


class OntologyContractTests(unittest.TestCase):
    def test_legacy_printer_is_migrated_to_asset(self):
        raw = {
            "version": "V1",
            "source_title": "ABB-Robot-Manual.pdf",
            "nodes": {
                "Printer": [
                    {
                        "printer_id": "PRINTER-001",
                        "name": "Controller manipulator system",
                        "brand": "ABB",
                        "model": "IRC5",
                    }
                ],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "Component": [],
                "ErrorCode": [],
            },
            "relationships": [],
            "metadata": {
                "version": "V1",
                "source_title": "ABB-Robot-Manual.pdf",
            },
        }

        migrated = migrate_legacy_ontology(raw)

        self.assertIn("Asset", migrated["nodes"])
        self.assertNotIn("Printer", migrated["nodes"])
        self.assertEqual(migrated["nodes"]["Asset"][0]["asset_id"], "PRINTER-001")
        self.assertEqual(migrated["nodes"]["Asset"][0]["description"], "Controller manipulator system")

    def test_contract_output_has_canonical_top_level_keys(self):
        raw = {
            "source_type": "injection molding machine",
            "source_title": "Boy35E",
            "nodes": {
                "Asset": [
                    {
                        "asset_id": "ASSET-001",
                        "name": "Boy35E",
                        "description": "Injection molding machine",
                        "brand": "Dr. Boy",
                        "model": "35E",
                        "asset_type": "injection molding machine",
                    }
                ],
                "Component": [
                    {
                        "component_id": "CMP-001",
                        "name": "Hydraulic pump",
                        "description": "Main hydraulic pump",
                        "category": "Hydraulics",
                    }
                ],
                "Symptom": [
                    {
                        "symptom_id": "SYM-001",
                        "name": "Low pressure",
                        "description": "Hydraulic pressure is low",
                        "severity": "High",
                    }
                ],
                "FailureMode": [
                    {
                        "failure_mode_id": "FM-001",
                        "name": "Pump wear",
                        "description": "Pump is worn",
                        "material_context": "Hydraulic circuit",
                    }
                ],
                "CorrectiveAction": [
                    {
                        "action_id": "CA-001",
                        "name": "Replace pump",
                        "description": "Replace the worn pump",
                        "instruction_text": "1. Stop machine\n2. Replace pump",
                    }
                ],
                "ErrorCode": [],
            },
            "relations": [
                {"name": "MAY_INDICATE", "from_id": "SYM-001", "to_id": "FM-001"},
                {"name": "RESOLVED_BY", "from_id": "FM-001", "to_id": "CA-001"},
                {"name": "AFFECTS", "from_id": "FM-001", "to_id": "CMP-001"},
            ],
        }

        contract, issues = build_and_validate_contract_ontology(raw)

        self.assertEqual(sorted(contract.keys()), ["metadata", "nodes", "relationships"])
        self.assertEqual(sorted(contract["nodes"].keys()), [
            "Asset", "Component", "CorrectiveAction", "ErrorCode", "FailureMode", "Symptom"
        ])
        self.assertEqual(contract["relationships"][0]["type"], "MAY_INDICATE")
        self.assertEqual(issues, [])

    def test_contract_validation_preserves_standalone_components(self):
        raw = {
            "source_type": "injection molding machine",
            "nodes": {
                "Asset": [
                    {
                        "asset_id": "ASSET-001",
                        "name": "Boy35E",
                        "description": "Injection molding machine",
                        "brand": "Dr. Boy",
                        "model": "35E",
                    }
                ],
                "Component": [
                    {
                        "component_id": "CMP-001",
                        "name": "Hydraulic pump",
                        "description": "Main hydraulic pump",
                        "category": "Hydraulics",
                    }
                ],
                "Symptom": [
                    {
                        "symptom_id": "SYM-001",
                        "name": "Low pressure",
                        "description": "Hydraulic pressure is low",
                        "severity": "High",
                    }
                ],
                "FailureMode": [
                    {
                        "failure_mode_id": "FM-001",
                        "name": "Pump wear",
                        "description": "Pump is worn",
                        "material_context": "Hydraulic circuit",
                    }
                ],
                "CorrectiveAction": [
                    {
                        "action_id": "CA-001",
                        "name": "Replace pump",
                        "description": "Replace the worn pump",
                        "instruction_text": "1. Stop machine\n2. Replace pump",
                    }
                ],
                "ErrorCode": [],
            },
            "relations": [
                {"name": "HAS_COMPONENT", "from_id": "ASSET-001", "to_id": "CMP-001"},
            ],
        }

        contract = build_contract_ontology(raw)
        _, issues = build_and_validate_contract_ontology(raw)

        self.assertEqual(sorted(contract.keys()), ["metadata", "nodes", "relationships"])
        self.assertTrue(any("MAY_INDICATE" in issue for issue in issues))
        self.assertTrue(any("RESOLVED_BY" in issue for issue in issues))
        self.assertEqual(len(contract["nodes"]["Component"]), 1)
        self.assertEqual(contract["relationships"][0]["type"], "HAS_COMPONENT")
        self.assertFalse(any("AFFECTS" in issue for issue in issues))


if __name__ == "__main__":
    unittest.main()
