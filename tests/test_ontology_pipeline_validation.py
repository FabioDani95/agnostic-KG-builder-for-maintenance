import unittest

from backend.models import HumanBindingAnswer, OntologyInstance
from backend.services.ontology_pipeline import (
    _normalize_ontology_instance,
    _retry_regression_reason,
    apply_human_binding,
    validate_ontology_instance,
)
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_workflow import _split_pages_by_section


def _asset_only_ontology() -> OntologyInstance:
    return OntologyInstance(
        ontology_name="diagnostic",
        version="V1",
        language="en",
        source_type="Operating manual",
        source_title="IRC5",
        nodes={
            "Asset": [
                {
                    "asset_id": "ASSET-001",
                    "name": "IRC5",
                    "description": "IRC5 controller",
                    "brand": "ABB",
                    "model": "IRC5",
                    "asset_type": "irc5",
                }
            ],
            "Component": [],
            "Symptom": [],
            "FailureMode": [],
            "CorrectiveAction": [],
            "ErrorCode": [],
        },
        relations=[],
    )


class OntologyPipelineValidationTests(unittest.TestCase):
    def test_split_pages_by_section_keeps_unsectioned_filtered_pages(self):
        pages = [
            {"page_number": 1, "text": "front matter"},
            {"page_number": 2, "text": "diagram page"},
            {"page_number": 10, "text": "diagnostic page 1"},
            {"page_number": 11, "text": "diagnostic page 2"},
        ]
        sections = [
            {"name": "Diagnostics", "start": 10, "end": 11, "source": "rule"},
        ]

        chunks = _split_pages_by_section(pages, sections, max_chars=10_000, max_pages=30)
        chunk_pages = [[page["page_number"] for page in chunk] for chunk, _ in chunks]

        self.assertEqual(chunk_pages, [[1, 2], [10, 11]])

    def test_validate_ontology_instance_rejects_asset_only_draft(self):
        schema_issues, human_fields = validate_ontology_instance(_asset_only_ontology())

        self.assertEqual(human_fields, [])
        self.assertTrue(any(issue.code == "empty_draft_content" for issue in schema_issues))

    def test_apply_human_binding_keeps_asset_only_draft_blocked(self):
        result = apply_human_binding(_asset_only_ontology(), [
            HumanBindingAnswer(field_key="Asset::ASSET-001::brand", value="ABB"),
            HumanBindingAnswer(field_key="Asset::ASSET-001::model", value="IRC5"),
        ])

        self.assertEqual(result.status, "blocked")
        self.assertTrue(any(issue.code == "empty_draft_content" for issue in result.schema_issues))

    def test_missing_required_non_id_property_becomes_human_input(self):
        ontology = OntologyInstance(
            ontology_name="diagnostic",
            version="V1",
            language="en",
            source_type="Service manual",
            source_title="IRC5",
            nodes={
                "Asset": [
                    {
                        "asset_id": "ASSET-001",
                        "name": "IRC5",
                        "description": "IRC5 controller",
                        "brand": "ABB",
                        "model": "IRC5",
                        "asset_type": "",
                    }
                ],
                "Component": [
                    {
                        "component_id": "CMP-001",
                        "name": "Power board",
                        "description": "Main power board",
                        "category": "",
                    }
                ],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            relations=[],
        )

        schema_issues, human_fields = validate_ontology_instance(ontology)

        self.assertFalse(any(issue.code == "missing_required_property" for issue in schema_issues))
        self.assertTrue(any(field.field_key == "Component::*::category" for field in human_fields))

    def test_normalize_ontology_instance_infers_affects_relation(self):
        ontology = OntologyInstance(
            ontology_name="diagnostic",
            version="V1",
            language="en",
            source_type="Service manual",
            source_title="Pump skid",
            nodes={
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
                "FailureMode": [
                    {
                        "failure_mode_id": "FM-001",
                        "name": "Hydraulic pump wear",
                        "description": "Pump internals are worn.",
                        "material_context": "Hydraulic pump",
                    }
                ],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            relations=[],
        )

        normalized = _normalize_ontology_instance(
            ontology=ontology,
            schema=load_ontology_schema(),
            source_type=ontology.source_type,
            source_title=ontology.source_title,
        )

        self.assertTrue(any(
            rel.name == "AFFECTS" and rel.from_id == "FM-001" and rel.to_id == "CMP-PUMP"
            for rel in normalized.relations
        ))

    def test_normalize_ontology_instance_infers_has_component_relation(self):
        ontology = OntologyInstance(
            ontology_name="diagnostic",
            version="V1",
            language="en",
            source_type="Service manual",
            source_title="Pump skid",
            nodes={
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
            relations=[],
        )

        normalized = _normalize_ontology_instance(
            ontology=ontology,
            schema=load_ontology_schema(),
            source_type=ontology.source_type,
            source_title=ontology.source_title,
        )

        self.assertTrue(any(
            rel.name == "HAS_COMPONENT" and rel.from_id == "ASSET-001" and rel.to_id == "CMP-PUMP"
            for rel in normalized.relations
        ))

    def test_retry_regression_reason_detects_asset_only_collapse(self):
        previous = OntologyInstance(
            ontology_name="diagnostic",
            version="V1",
            language="en",
            source_type="Service manual",
            source_title="Pump skid",
            nodes={
                "Asset": [{
                    "asset_id": "ASSET-001",
                    "name": "Pump skid",
                    "description": "Pump skid",
                    "brand": "Demo",
                    "model": "S1",
                    "asset_type": "pump skid",
                }],
                "Component": [{
                    "component_id": "CMP-PUMP",
                    "name": "Hydraulic pump",
                    "description": "Main hydraulic pump assembly",
                    "category": "Hydraulics",
                }],
                "Symptom": [{
                    "symptom_id": "SYM-001",
                    "name": "Low pressure",
                    "description": "Pressure drops.",
                    "severity": "Medium",
                }],
                "FailureMode": [{
                    "failure_mode_id": "FM-001",
                    "name": "Hydraulic pump wear",
                    "description": "Pump internals are worn.",
                    "material_context": "Hydraulic pump",
                }],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            relations=[],
        )

        reason = _retry_regression_reason(previous, _asset_only_ontology())

        self.assertIsNotNone(reason)
        self.assertIn("removed all substantive nodes", reason)

    def test_retry_regression_reason_ignores_already_empty_baseline(self):
        reason = _retry_regression_reason(_asset_only_ontology(), _asset_only_ontology())

        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
