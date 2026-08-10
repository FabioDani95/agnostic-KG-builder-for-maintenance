from backend.models import OntologyInstance, OntologyRelationInstance
from backend.prompts.ontology_prompt import (
    build_ontology_extraction_prompt,
    build_ontology_re_extraction_prompt,
    build_ontology_relation_extraction_prompt,
)
from backend.services.ontology_pipeline_coercion import _normalize_ontology_instance
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_semantics import WORKSPACE_CANONICAL_ASSET_MARKER
from backend.services.ontology_workflow import _canonical_asset_identity


def _canonical_asset() -> dict[str, str]:
    return {
        "asset_id": "asset_workspace_pump",
        "name": "Workspace Pump",
        "description": "Operator-confirmed production pump",
        "brand": "Acme",
        "model": "P-42",
        "asset_type": "pump",
    }


def test_canonical_asset_prompt_extracts_only_five_source_node_types():
    prompt = build_ontology_extraction_prompt(
        schema_json="{}",
        source_type="technical PDF",
        source_title="manual.pdf",
        extract_asset=False,
    )

    assert "ALL 5 source-derived node types" in prompt
    assert "Do NOT extract, infer, rename, or emit any Asset node" in prompt
    assert "Extract exactly one Asset node per document" not in prompt
    assert "The system derives\n    HAS_COMPONENT and GENERATES_ERROR" in prompt


def test_canonical_asset_retry_and_relation_prompts_protect_root_structure():
    retry_prompt = build_ontology_re_extraction_prompt(
        schema_json="{}",
        source_type="technical PDF",
        source_title="manual.pdf",
        issues_summary="none",
        previous_ontology_json="{}",
        extract_asset=False,
    )
    relation_prompt = build_ontology_relation_extraction_prompt("{}", "[]")

    assert "Never upsert, remove, rename, or otherwise modify the canonical Asset" in retry_prompt
    assert "Do NOT emit HAS_COMPONENT or GENERATES_ERROR" in relation_prompt
    assert "GENERATES_ERROR: Asset -> ErrorCode" not in relation_prompt


def test_normalization_discards_model_assets_and_injects_workspace_asset():
    schema = load_ontology_schema()
    ontology = OntologyInstance(
        ontology_name=schema.ontology_name,
        version=schema.version,
        language="en",
        source_type="technical PDF",
        source_title="different-product-manual.pdf",
        nodes={
            "Asset": [
                {
                    "asset_id": "asset_model_guess_one",
                    "name": "Model guess one",
                    "description": "LLM output",
                    "brand": "Wrong",
                    "model": "X1",
                    "asset_type": "machine",
                },
                {
                    "asset_id": "asset_model_guess_two",
                    "name": "Model guess two",
                    "description": "Second LLM output",
                    "brand": "Wrong",
                    "model": "X2",
                    "asset_type": "machine",
                },
            ],
            "Component": [
                {
                    "component_id": "comp_pump_motor",
                    "name": "Pump motor",
                    "description": "Drive motor",
                    "category": "electrical",
                }
            ],
            "ErrorCode": [
                {
                    "error_code_id": "err_e42",
                    "name": "Alarm E42",
                    "description": "Motor overload alarm",
                    "code": "E42",
                }
            ],
        },
        relations=[
            OntologyRelationInstance(
                name="HAS_COMPONENT",
                from_type="Asset",
                from_id="asset_model_guess_two",
                to_type="Component",
                to_id="comp_pump_motor",
                evidence=[],
            )
        ],
    )

    normalized = _normalize_ontology_instance(
        ontology=ontology,
        schema=schema,
        source_type=ontology.source_type,
        source_title=ontology.source_title,
        asset_identity={**_canonical_asset(), WORKSPACE_CANONICAL_ASSET_MARKER: True},
    )

    assert normalized.nodes["Asset"] == [_canonical_asset()]
    assert {
        (relation.name, relation.from_id, relation.to_id)
        for relation in normalized.relations
    } == {
        ("HAS_COMPONENT", "asset_workspace_pump", "comp_pump_motor"),
        ("GENERATES_ERROR", "asset_workspace_pump", "err_e42"),
    }


def test_only_workspace_identity_gets_the_canonical_marker():
    workspace_identity = _canonical_asset_identity({
        "asset_identity": _canonical_asset(),
        "asset_identity_is_canonical": True,
        "source_type": "technical PDF",
        "source_title": "manual.pdf",
    })
    discovered_identity = _canonical_asset_identity({
        "asset_identity": _canonical_asset(),
        "source_type": "technical PDF",
        "source_title": "manual.pdf",
    })

    assert workspace_identity[WORKSPACE_CANONICAL_ASSET_MARKER] is True
    assert WORKSPACE_CANONICAL_ASSET_MARKER not in discovered_identity
