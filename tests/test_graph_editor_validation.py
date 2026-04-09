import unittest

from backend.services.graph_editor_validation import (
    validate_node_update,
    validate_relationship_add,
)


SCHEMA = {
    "node_types": {
        "Asset": [
            {"name": "asset_id", "type": "string", "required": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "brand", "type": "string", "required": True},
            {"name": "model", "type": "string", "required": True},
        ],
        "Component": [
            {"name": "component_id", "type": "string", "required": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "category", "type": "string", "required": True},
        ],
        "Symptom": [
            {"name": "symptom_id", "type": "string", "required": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "severity", "type": "string", "required": True},
        ],
        "FailureMode": [
            {"name": "failure_mode_id", "type": "string", "required": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "material_context", "type": "string", "required": True},
        ],
        "CorrectiveAction": [
            {"name": "action_id", "type": "string", "required": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "instruction_text", "type": "string", "required": True},
        ],
        "ErrorCode": [
            {"name": "error_code_id", "type": "string", "required": True},
            {"name": "name", "type": "string", "required": True},
            {"name": "description", "type": "string", "required": True},
            {"name": "code", "type": "string", "required": True},
        ],
    },
    "relation_constraints": {
        "MAY_INDICATE": {"domain": ["Symptom"], "range": ["FailureMode"]},
        "RESOLVED_BY": {"domain": ["FailureMode"], "range": ["CorrectiveAction"]},
        "AFFECTS": {"domain": ["FailureMode"], "range": ["Component"]},
    },
}

ONTOLOGY = {
    "nodes": {
        "Asset": [{"asset_id": "ASSET-001", "name": "Boy35E", "description": "Machine", "brand": "Dr. Boy", "model": "35E"}],
        "Component": [{"component_id": "CMP-001", "name": "Pump", "description": "Main pump", "category": "Hydraulics"}],
        "Symptom": [{"symptom_id": "SYM-001", "name": "Low pressure", "description": "Pressure low", "severity": "High"}],
        "FailureMode": [{"failure_mode_id": "FM-001", "name": "Pump wear", "description": "Worn pump", "material_context": "Hydraulic circuit"}],
        "CorrectiveAction": [{"action_id": "CA-001", "name": "Replace pump", "description": "Replace it", "instruction_text": "1. Stop\n2. Replace"}],
        "ErrorCode": [],
    },
    "relations": [],
}


class GraphEditorValidationTests(unittest.TestCase):
    def test_validate_node_update_rejects_missing_required_field(self):
        with self.assertRaisesRegex(ValueError, "Asset.brand is required"):
            validate_node_update(ONTOLOGY, SCHEMA, "ASSET-001", {"brand": ""})

    def test_validate_node_update_returns_merged_payload(self):
        node_type, updated = validate_node_update(ONTOLOGY, SCHEMA, "ASSET-001", {"description": "Updated machine"})
        self.assertEqual(node_type, "Asset")
        self.assertEqual(updated["description"], "Updated machine")
        self.assertEqual(updated["asset_id"], "ASSET-001")

    def test_validate_relationship_add_rejects_wrong_domain_range(self):
        with self.assertRaisesRegex(ValueError, "MAY_INDICATE must start from Symptom"):
            validate_relationship_add(ONTOLOGY, SCHEMA, "MAY_INDICATE", "FM-001", "SYM-001")

    def test_validate_relationship_add_rejects_duplicates(self):
        ontology = {
            **ONTOLOGY,
            "relations": [{"name": "AFFECTS", "from_id": "FM-001", "to_id": "CMP-001"}],
        }
        with self.assertRaisesRegex(ValueError, "Duplicate relationship"):
            validate_relationship_add(ontology, SCHEMA, "AFFECTS", "FM-001", "CMP-001")

    def test_validate_relationship_add_returns_resolved_types(self):
        from_type, to_type = validate_relationship_add(ONTOLOGY, SCHEMA, "AFFECTS", "FM-001", "CMP-001")
        self.assertEqual((from_type, to_type), ("FailureMode", "Component"))


if __name__ == "__main__":
    unittest.main()
