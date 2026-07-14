"""Regression tests for the block-B pipeline consistency fixes (2026-07-14):

B1  coverage completion runs BEFORE resolution completion at run level
B2  coverage completion corrects the cited page when the quote lives elsewhere
B3  resolution targets reserve a quota for error codes
B5  human-required fields group into a wildcard only above a threshold
B6  chunk merge unions relation evidence and fills missing node fields
B10 small-doc scoping still identifies the product and stores the cut plan
B11 cut-plan approval merges into the stored plan instead of replacing it
B12 coverage completion keeps the most diagnostic pages inside the input budget
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from backend.models import (
    CutPlanApproval,
    CutPlanRequest,
    OntologyInstance,
    OntologyPipelineResponse,
)
from backend.services.coverage_completion_service import (
    apply_missing_chains,
    select_pages_within_budget,
)
from backend.services.ontology_pipeline import validate_ontology_instance
from backend.services.ontology_workflow import (
    _finalize_run_level_quality,
    _merge_pipeline_results,
)
from backend.services.resolution_completion_service import build_resolution_targets
from backend.services.scoping_workflow import (
    approve_cut_plan_workflow,
    create_cut_plan_workflow,
)


def _ontology(nodes: dict | None = None, relations: list | None = None) -> OntologyInstance:
    base_nodes = {
        "Asset": [{
            "asset_id": "ASSET-001", "name": "Demo", "description": "d",
            "brand": "Demo", "model": "M1", "asset_type": "machine",
        }],
        "Component": [],
        "Symptom": [],
        "FailureMode": [],
        "CorrectiveAction": [],
        "ErrorCode": [],
    }
    base_nodes.update(nodes or {})
    return OntologyInstance.model_validate({
        "ontology_name": "diagnostic",
        "version": "V1",
        "language": "en",
        "source_type": "Service Manual",
        "source_title": "Demo",
        "nodes": base_nodes,
        "relations": relations or [],
    })


class RunLevelPassOrderingTests(unittest.TestCase):
    def test_coverage_completion_runs_before_resolution_completion(self) -> None:
        calls: list[str] = []
        ontology = _ontology()
        result = OntologyPipelineResponse(status="ready", ontology=ontology)

        def _fake_coverage(*, ontology, **kwargs):
            calls.append("coverage")
            return ontology, [], {"returned": 0, "applied": 0}

        def _fake_resolution(*, ontology, **kwargs):
            calls.append("resolution")
            return ontology, [], {"attempted": 0, "completed": 0}

        with patch(
            "backend.services.coverage_completion_service.complete_coverage_gaps",
            side_effect=_fake_coverage,
        ), patch(
            "backend.services.resolution_completion_service.complete_resolution_gaps",
            side_effect=_fake_resolution,
        ):
            _finalize_run_level_quality(
                result,
                [{"page_number": 1, "text": "demo page"}],
                None,
                None,
            )

        self.assertEqual(calls, ["coverage", "resolution"])


class CoverageCitationCorrectionTests(unittest.TestCase):
    def test_chain_citation_corrected_to_the_page_that_supports_the_quote(self) -> None:
        pages = [
            {"page_number": 4, "text": "Index of troubleshooting topics."},
            {"page_number": 5, "text": "If the door switch is faulty, replace the door switch."},
        ]
        payload = {"missing_chains": [{
            "symptom": {"symptom_id": "sym_door", "name": "Door does not latch",
                        "description": "Door open", "severity": "Medium"},
            "failure_mode": {"failure_mode_id": "fm_door_switch_faulty",
                             "name": "Door switch faulty",
                             "description": "Switch defective",
                             "material_context": "asset_level"},
            "evidence": {"source_page": 4, "source_reference": "PAGE 4",
                         "quote": "If the door switch is faulty, replace the door switch."},
        }]}

        updated, report = apply_missing_chains(_ontology(), payload, pages, max_chains=5)

        self.assertEqual(report["applied"], 1)
        may_indicate = [rel for rel in updated.relations if rel.name == "MAY_INDICATE"]
        self.assertEqual(len(may_indicate), 1)
        self.assertEqual(may_indicate[0].evidence[0].source_page, 5)
        self.assertEqual(may_indicate[0].evidence[0].source_reference, "PAGE 5")


class CoveragePageBudgetTests(unittest.TestCase):
    def test_budget_selection_prefers_diagnostic_pages(self) -> None:
        boilerplate = "Legal notices and copyright information. " * 40
        diagnostic = (
            "Troubleshooting table: symptom, cause, remedy. "
            "Alarm E42 error fault — replace the sensor. "
        ) * 20
        pages = [
            {"page_number": 1, "text": boilerplate},
            {"page_number": 2, "text": diagnostic},
            {"page_number": 3, "text": boilerplate},
        ]
        budget = len(diagnostic) + 200  # room for exactly one page

        kept, dropped = select_pages_within_budget(pages, budget)

        self.assertEqual([page["page_number"] for page in kept], [2])
        self.assertEqual(sorted(dropped), [1, 3])

    def test_budget_selection_is_noop_when_everything_fits(self) -> None:
        pages = [{"page_number": 1, "text": "short"}, {"page_number": 2, "text": "short"}]
        kept, dropped = select_pages_within_budget(pages, 10000)
        self.assertEqual(kept, pages)
        self.assertEqual(dropped, [])


class ResolutionTargetQuotaTests(unittest.TestCase):
    def test_error_codes_get_a_reserved_quota_under_the_cap(self) -> None:
        failure_modes = [{
            "failure_mode_id": f"fm_{i}", "name": f"Failure {i}",
            "description": "d", "material_context": "asset_level",
        } for i in range(10)]
        error_codes = [{
            "error_code_id": f"err_{i}", "name": f"E{i}",
            "description": "alarm", "code": f"E{i}",
        } for i in range(3)]
        ontology = _ontology({"FailureMode": failure_modes, "ErrorCode": error_codes})

        targets = build_resolution_targets(ontology, max_targets=8)

        self.assertEqual(len(targets), 8)
        by_type = {"failure_mode": 0, "error_code": 0}
        for target in targets:
            by_type[target.target_type] += 1
        # A flat cap used to starve error codes entirely (10 FMs > cap of 8).
        self.assertEqual(by_type["error_code"], 2)
        self.assertEqual(by_type["failure_mode"], 6)

    def test_no_quota_needed_when_everything_fits(self) -> None:
        ontology = _ontology({
            "FailureMode": [{
                "failure_mode_id": "fm_1", "name": "F", "description": "d",
                "material_context": "asset_level",
            }],
            "ErrorCode": [{
                "error_code_id": "err_1", "name": "E1", "description": "a", "code": "E1",
            }],
        })
        targets = build_resolution_targets(ontology, max_targets=8)
        self.assertEqual(len(targets), 2)


class WildcardHumanFieldThresholdTests(unittest.TestCase):
    def _components(self, count: int) -> list[dict]:
        return [{
            "component_id": f"CMP-{i}", "name": f"Part {i}",
            "description": "d", "category": "",
        } for i in range(count)]

    def test_small_group_keeps_per_node_fields(self) -> None:
        _, human_fields = validate_ontology_instance(
            _ontology({"Component": self._components(2)})
        )
        category_keys = sorted(
            field.field_key for field in human_fields
            if field.property_name == "category"
        )
        self.assertEqual(category_keys, [
            "Component::CMP-0::category",
            "Component::CMP-1::category",
        ])

    def test_large_group_collapses_into_wildcard(self) -> None:
        _, human_fields = validate_ontology_instance(
            _ontology({"Component": self._components(5)})
        )
        category_keys = [
            field.field_key for field in human_fields
            if field.property_name == "category"
        ]
        self.assertEqual(category_keys, ["Component::*::category"])


class ChunkMergeEnrichmentTests(unittest.TestCase):
    def _result(self, nodes: dict, relations: list) -> OntologyPipelineResponse:
        return OntologyPipelineResponse(
            status="ready",
            ontology=_ontology(nodes, relations),
        )

    def test_duplicate_relation_evidence_is_unioned_across_chunks(self) -> None:
        symptom = {"symptom_id": "sym_a", "name": "No power",
                   "description": "d", "severity": "High"}
        failure = {"failure_mode_id": "fm_a", "name": "Fuse blown",
                   "description": "d", "material_context": "asset_level"}
        relation_page_10 = {
            "name": "MAY_INDICATE", "from_type": "Symptom", "from_id": "sym_a",
            "to_type": "FailureMode", "to_id": "fm_a",
            "evidence": [{"source_page": 10, "source_reference": "PAGE 10", "quote": "q10"}],
        }
        relation_page_22 = {
            "name": "MAY_INDICATE", "from_type": "Symptom", "from_id": "sym_a",
            "to_type": "FailureMode", "to_id": "fm_a",
            "evidence": [{"source_page": 22, "source_reference": "PAGE 22", "quote": "q22"}],
        }
        merged = _merge_pipeline_results([
            self._result({"Symptom": [symptom], "FailureMode": [failure]}, [relation_page_10]),
            self._result({"Symptom": [symptom], "FailureMode": [failure]}, [relation_page_22]),
        ])

        may_indicate = [rel for rel in merged.ontology.relations if rel.name == "MAY_INDICATE"]
        self.assertEqual(len(may_indicate), 1)
        pages = sorted(ev.source_page for ev in may_indicate[0].evidence)
        self.assertEqual(pages, [10, 22])

    def test_duplicate_node_fields_are_filled_from_both_chunks(self) -> None:
        with_description = {"component_id": "comp_pump", "name": "Pump",
                            "description": "Main hydraulic pump", "category": ""}
        with_category = {"component_id": "comp_pump", "name": "Pump",
                         "description": "", "category": "Hydraulics"}
        merged = _merge_pipeline_results([
            self._result({"Component": [with_description]}, []),
            self._result({"Component": [with_category]}, []),
        ])

        component = merged.ontology.nodes["Component"][0]
        self.assertEqual(component["description"], "Main hydraulic pump")
        self.assertEqual(component["category"], "Hydraulics")


class SmallDocScopingTests(unittest.TestCase):
    _PRODUCT_JSON = (
        '{"product_name": "Acme Widget 500", "product_short_name": "Widget 500",'
        ' "brand": "Acme", "model": "W500", "asset_type": "machine",'
        ' "document_type": "service manual", "language": "en"}'
    )

    def test_small_doc_identifies_product_and_stores_cut_plan(self) -> None:
        store = {
            "pages": [
                {"page_number": 1, "text": "Acme Widget 500 service manual"},
                {"page_number": 2, "text": "Troubleshooting"},
            ],
            "filename": "acme_widget_500.pdf",
        }
        req = CutPlanRequest(pdf_id="pdf-1", page_offset=0)

        with patch(
            "backend.services.scoping_workflow.call_openai_scoping",
            return_value=(self._PRODUCT_JSON, {"operation": "scoping", "prompt": 1,
                                               "completion": 1, "total": 2}),
        ):
            cut_plan = create_cut_plan_workflow(store, req)

        self.assertTrue(cut_plan.skipped)
        self.assertIsNotNone(cut_plan.product_info)
        self.assertEqual(cut_plan.product_info.product_name, "Acme Widget 500")
        self.assertEqual(store["source_title"], "Acme Widget 500")
        self.assertTrue(store["asset_identity"]["asset_id"])
        stored_plan = store["cut_plan"]
        self.assertTrue(stored_plan["skipped"])
        self.assertEqual(stored_plan["pages_to_keep"], [1, 2])
        self.assertEqual(stored_plan["product_info"]["product_name"], "Acme Widget 500")


class ApproveCutPlanMergeTests(unittest.TestCase):
    def test_approval_preserves_scoping_metadata(self) -> None:
        store = {
            "cut_plan": {
                "pdf_id": "pdf-1",
                "total_pages": 40,
                "sections": [{"name": "Troubleshooting", "start": 10, "end": 20, "source": "rule"}],
                "pages_to_keep": list(range(10, 21)),
                "page_offset": 2,
                "page_offset_detection": {"offset": 2, "source": "toc", "confidence": "high"},
                "toc": {"entries": [], "toc_start_page": 2, "toc_end_page": 3},
                "skipped": False,
                "product_info": {"product_name": "Acme Widget 500"},
            },
        }
        approval = CutPlanApproval(pdf_id="pdf-1", pages_to_keep=[12, 11], page_offset=2)

        approve_cut_plan_workflow(store, approval)

        plan = store["cut_plan"]
        self.assertEqual(plan["pages_to_keep"], [11, 12])
        # Metadata gathered during scoping must survive the approval.
        self.assertEqual(plan["product_info"]["product_name"], "Acme Widget 500")
        self.assertEqual(plan["total_pages"], 40)
        self.assertEqual(plan["page_offset_detection"]["source"], "toc")
        self.assertIsNotNone(plan["toc"])
        # Sections were not resent: the scoping sections are kept.
        self.assertEqual(plan["sections"][0]["name"], "Troubleshooting")


if __name__ == "__main__":
    unittest.main()
