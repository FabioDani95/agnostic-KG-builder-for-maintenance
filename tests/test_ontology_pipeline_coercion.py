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
