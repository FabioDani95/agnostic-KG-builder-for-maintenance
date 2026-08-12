from backend.domain.subgraphs import GraphEvidenceRef, SourceGraphNode, SourceGraphRelation
from backend.services.source_subgraph_generation import _strict_validation

EVIDENCE_ID = "ev_validation00001"


def test_strict_validation_requires_one_asset_and_component_ownership():
    nodes = [
        SourceGraphNode(
            node_id="asset-1",
            node_type="Asset",
            label="Pump",
            evidence_ids=[EVIDENCE_ID],
            attributes={
                "asset_id": "asset-1",
                "name": "Pump",
                "description": "Test pump",
                "brand": "Acme",
                "model": "P-1",
            },
        ),
        SourceGraphNode(
            node_id="component-1",
            node_type="Component",
            label="Motor",
            evidence_ids=[EVIDENCE_ID],
            attributes={
                "component_id": "component-1",
                "name": "Motor",
                "description": "Drive motor",
                "category": "drive",
            },
        ),
    ]
    evidence = [GraphEvidenceRef(
        evidence_id=EVIDENCE_ID,
        label="Page 1",
        excerpt="Pump motor",
        locator={"kind": "pdf", "page": 1},
    )]

    report = _strict_validation(nodes=nodes, relations=[], evidence=evidence)

    assert report.passed is False
    assert report.graph_invariant_errors == 1
    assert "component_not_owned_by_asset" in {issue.code for issue in report.issues}


def test_strict_validation_rejects_missing_canonical_asset():
    report = _strict_validation(nodes=[], relations=[], evidence=[])

    assert report.passed is False
    assert report.graph_invariant_errors == 1
    assert "asset_cardinality" in {issue.code for issue in report.issues}


def test_strict_validation_rejects_identifier_collision_across_node_types():
    nodes = [
        SourceGraphNode(
            node_id="asset-node",
            node_type="Asset",
            label="Pump",
            evidence_ids=[EVIDENCE_ID],
            attributes={
                "asset_id": "shared-id",
                "name": "Pump",
                "description": "Test pump",
                "brand": "Acme",
                "model": "P-1",
            },
        ),
        SourceGraphNode(
            node_id="component-node",
            node_type="Component",
            label="Motor",
            evidence_ids=[EVIDENCE_ID],
            attributes={
                "component_id": "shared-id",
                "name": "Motor",
                "description": "Drive motor",
                "category": "drive",
            },
        ),
    ]
    relations = [
        SourceGraphRelation(
            relation_id="rel-component",
            relation_type="HAS_COMPONENT",
            from_id="asset-node",
            to_id="component-node",
            evidence_ids=[EVIDENCE_ID],
        )
    ]
    evidence = [GraphEvidenceRef(
        evidence_id=EVIDENCE_ID,
        label="Page 1",
        excerpt="Pump motor",
        locator={"kind": "pdf", "page": 1, "quote": "Pump motor"},
    )]

    report = _strict_validation(nodes=nodes, relations=relations, evidence=evidence)

    assert report.passed is False
    assert report.duplicate_ids == 1
    assert "duplicate_id" in {issue.code for issue in report.issues}


def test_strict_validation_rejects_duplicate_graph_node_id_across_types():
    nodes = [
        SourceGraphNode(
            node_id="same-node",
            node_type="Asset",
            label="Pump",
            evidence_ids=[EVIDENCE_ID],
            attributes={
                "asset_id": "asset-1", "name": "Pump", "description": "Pump",
                "brand": "Acme", "model": "P1",
            },
        ),
        SourceGraphNode(
            node_id="same-node",
            node_type="Component",
            label="Motor",
            evidence_ids=[EVIDENCE_ID],
            attributes={
                "component_id": "component-1", "name": "Motor",
                "description": "Motor", "category": "drive",
            },
        ),
    ]
    report = _strict_validation(
        nodes=nodes,
        relations=[],
        evidence=[GraphEvidenceRef(
            evidence_id=EVIDENCE_ID,
            label="Page 1",
            excerpt="Pump motor",
            locator={"kind": "pdf", "page": 1, "quote": "Pump motor"},
        )],
    )

    assert report.passed is False
    assert "duplicate_node_id" in {issue.code for issue in report.issues}
