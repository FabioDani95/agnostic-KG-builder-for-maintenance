from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.models import OntologyInstance, OntologyPipelineResponse
from backend.services.ontology_pipeline import (
    _coerce_raw_ontology_data,
    _normalize_ontology_instance,
)
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_workflow import _merge_pipeline_results


def test_coerce_raw_ontology_data_accepts_relation_alias_key():
    schema = load_ontology_schema()
    data = {
        "ontology_name": schema.ontology_name,
        "version": schema.version,
        "language": "en",
        "nodes": {
            "Asset": [{
                "asset_id": "asset_duetto",
                "name": "Alex Duetto 3.0 Espresso Machine",
                "description": "Espresso machine",
                "brand": "Alex",
                "model": "Duetto 3.0",
                "asset_type": "espresso_machine",
            }],
            "Component": [{
                "component_id": "comp_pump",
                "name": "Pump",
                "description": "Rotary pump",
                "category": "hydraulic",
            }],
        },
        "relations": [{
            "relation": "HAS_COMPONENT",
            "from": "asset_duetto",
            "to": "comp_pump",
            "evidence": [{
                "source_page": 3,
                "source_reference": "PAGE 3",
                "quote": "Pump",
            }],
        }],
    }

    coerced = _coerce_raw_ontology_data(
        data=data,
        schema=schema,
        source_type="Owner's Manual",
        source_title="Alex Duetto 3.0 Espresso Machine",
    )

    assert len(coerced["relations"]) == 1
    relation = coerced["relations"][0]
    assert relation["name"] == "HAS_COMPONENT"
    assert relation["from_type"] == "Asset"
    assert relation["from_id"] == "asset_duetto"
    assert relation["to_type"] == "Component"
    assert relation["to_id"] == "comp_pump"


def test_normalize_ontology_instance_adds_missing_has_component():
    schema = load_ontology_schema()
    ontology = OntologyInstance(
        ontology_name=schema.ontology_name,
        version=schema.version,
        language="en",
        source_type="Owner's Manual",
        source_title="Alex Duetto 3.0 Espresso Machine",
        nodes={
            "Asset": [{
                "asset_id": "asset_duetto",
                "name": "Alex Duetto 3.0 Espresso Machine",
                "description": "Espresso machine",
                "brand": "Alex",
                "model": "Duetto 3.0",
                "asset_type": "espresso_machine",
            }],
            "Component": [{
                "component_id": "comp_pump",
                "name": "Pump",
                "description": "Rotary pump",
                "category": "hydraulic",
            }],
        },
        relations=[],
    )

    normalized = _normalize_ontology_instance(
        ontology=ontology,
        schema=schema,
        source_type=ontology.source_type,
        source_title=ontology.source_title,
    )

    assert len(normalized.relations) == 1
    relation = normalized.relations[0]
    assert relation.name == "HAS_COMPONENT"
    assert relation.from_id == "asset_duetto"
    assert relation.to_id == "comp_pump"


def test_normalize_ontology_instance_applies_canonical_asset_identity_and_remaps_relations():
    schema = load_ontology_schema()
    ontology = OntologyInstance(
        ontology_name=schema.ontology_name,
        version=schema.version,
        language="en",
        source_type="Service Manual",
        source_title="Eagle Automatic Laser Cutting System Model: Eagle S3L",
        nodes={
            "Asset": [{
                "asset_id": "asset_eastman_eagle_s3l",
                "name": "Eastman Eagle S3L",
                "description": "Short form asset label",
                "brand": "",
                "model": "",
                "asset_type": "technical asset",
            }],
            "Component": [{
                "component_id": "comp_tool_head",
                "name": "Tool head",
                "description": "Tool head assembly",
                "category": "tooling",
            }],
        },
        relations=[{
            "name": "HAS_COMPONENT",
            "from_type": "Asset",
            "from_id": "asset_eastman_eagle_s3l",
            "to_type": "Component",
            "to_id": "comp_tool_head",
            "evidence": [],
        }],
    )

    normalized = _normalize_ontology_instance(
        ontology=ontology,
        schema=schema,
        source_type=ontology.source_type,
        source_title=ontology.source_title,
        asset_identity={
            "asset_id": "asset_eastman_eagle_s3l_canonical",
            "name": "Eagle Automatic Laser Cutting System Model: Eagle S3L",
            "brand": "Eastman",
            "model": "Eagle S3L",
            "asset_type": "technical asset",
        },
    )

    asset = normalized.nodes["Asset"][0]
    assert asset["asset_id"] == "asset_eastman_eagle_s3l_canonical"
    assert asset["name"] == "Eagle Automatic Laser Cutting System Model: Eagle S3L"
    assert asset["brand"] == "Eastman"
    assert asset["model"] == "Eagle S3L"
    assert normalized.relations[0].from_id == "asset_eastman_eagle_s3l_canonical"


def test_merge_pipeline_results_rebuilds_missing_has_component():
    schema = load_ontology_schema()
    asset_only = OntologyPipelineResponse(
        status="ready",
        ontology=OntologyInstance(
            ontology_name=schema.ontology_name,
            version=schema.version,
            language="en",
            source_type="Owner's Manual",
            source_title="Alex Duetto 3.0 Espresso Machine",
            nodes={
                "Asset": [{
                    "asset_id": "asset_duetto",
                    "name": "Alex Duetto 3.0 Espresso Machine",
                    "description": "Espresso machine",
                    "brand": "Alex",
                    "model": "Duetto 3.0",
                    "asset_type": "espresso_machine",
                }],
            },
            relations=[],
        ),
        semantic_issues=[],
        schema_issues=[],
        human_required_fields=[],
    )
    component_only = OntologyPipelineResponse(
        status="ready",
        ontology=OntologyInstance(
            ontology_name=schema.ontology_name,
            version=schema.version,
            language="en",
            source_type="Owner's Manual",
            source_title="Alex Duetto 3.0 Espresso Machine",
            nodes={
                "Asset": [{
                    "asset_id": "asset_duetto",
                    "name": "Alex Duetto 3.0 Espresso Machine",
                    "description": "Espresso machine",
                    "brand": "Alex",
                    "model": "Duetto 3.0",
                    "asset_type": "espresso_machine",
                }],
                "Component": [{
                    "component_id": "comp_pump",
                    "name": "Pump",
                    "description": "Rotary pump",
                    "category": "hydraulic",
                }],
            },
            relations=[],
        ),
        semantic_issues=[],
        schema_issues=[],
        human_required_fields=[],
    )

    merged = _merge_pipeline_results([asset_only, component_only])

    assert len(merged.ontology.relations) == 1
    relation = merged.ontology.relations[0]
    assert relation.name == "HAS_COMPONENT"
    assert relation.from_id == "asset_duetto"
    assert relation.to_id == "comp_pump"


def test_merge_pipeline_results_collapses_asset_variants_to_scoping_identity():
    schema = load_ontology_schema()
    asset_primary = OntologyPipelineResponse(
        status="ready",
        ontology=OntologyInstance(
            ontology_name=schema.ontology_name,
            version=schema.version,
            language="en",
            source_type="Service Manual",
            source_title="Eagle Automatic Laser Cutting System Model: Eagle S3L",
            nodes={
                "Asset": [{
                    "asset_id": "asset_eagle_s3l",
                    "name": "Eagle Automatic Laser Cutting System Model: Eagle S3L",
                    "description": "Primary title-page label",
                    "brand": "",
                    "model": "",
                    "asset_type": "technical asset",
                }],
                "Component": [{
                    "component_id": "comp_power_supply",
                    "name": "Power supply",
                    "description": "Power supply",
                    "category": "electrical",
                }],
            },
            relations=[{
                "name": "HAS_COMPONENT",
                "from_type": "Asset",
                "from_id": "asset_eagle_s3l",
                "to_type": "Component",
                "to_id": "comp_power_supply",
                "evidence": [],
            }],
        ),
        semantic_issues=[],
        schema_issues=[],
        human_required_fields=[],
    )
    asset_variant = OntologyPipelineResponse(
        status="ready",
        ontology=OntologyInstance(
            ontology_name=schema.ontology_name,
            version=schema.version,
            language="en",
            source_type="Service Manual",
            source_title="Eagle Automatic Laser Cutting System Model: Eagle S3L",
            nodes={
                "Asset": [{
                    "asset_id": "asset_eastman_eagle_s3l",
                    "name": "Eastman Eagle S3L",
                    "description": "Brand-prefixed variant",
                    "brand": "Eastman",
                    "model": "Eagle S3L",
                    "asset_type": "technical asset",
                }],
                "Component": [{
                    "component_id": "comp_tool_head",
                    "name": "Tool head",
                    "description": "Tool head",
                    "category": "tooling",
                }],
            },
            relations=[{
                "name": "HAS_COMPONENT",
                "from_type": "Asset",
                "from_id": "asset_eastman_eagle_s3l",
                "to_type": "Component",
                "to_id": "comp_tool_head",
                "evidence": [],
            }],
        ),
        semantic_issues=[],
        schema_issues=[],
        human_required_fields=[],
    )

    merged = _merge_pipeline_results(
        [asset_primary, asset_variant],
        asset_identity={
            "asset_id": "asset_eastman_eagle_s3l",
            "name": "Eagle Automatic Laser Cutting System Model: Eagle S3L",
            "brand": "Eastman",
            "model": "Eagle S3L",
            "asset_type": "technical asset",
        },
    )

    assert len(merged.ontology.nodes["Asset"]) == 1
    asset = merged.ontology.nodes["Asset"][0]
    assert asset["asset_id"] == "asset_eastman_eagle_s3l"
    assert asset["name"] == "Eagle Automatic Laser Cutting System Model: Eagle S3L"
    assert sorted(rel.to_id for rel in merged.ontology.relations) == [
        "comp_power_supply",
        "comp_tool_head",
    ]
    assert {rel.from_id for rel in merged.ontology.relations} == {"asset_eastman_eagle_s3l"}
