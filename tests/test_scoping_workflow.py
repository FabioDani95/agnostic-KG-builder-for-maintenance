import unittest
from unittest.mock import patch

from backend.models import CutPlanRequest, PageRange, SectionInfo
from backend.services.scoping_workflow import create_cut_plan_workflow


class ScopingWorkflowTests(unittest.TestCase):
    @patch("backend.services.scoping_workflow.call_openai_scoping")
    def test_small_workspace_document_never_rediscovers_confirmed_asset(
        self,
        mock_call_openai_scoping,
    ):
        confirmed_asset = {
            "asset_id": "asset_workspace_pump",
            "name": "Workspace Pump",
            "description": "Operator-confirmed pump",
            "brand": "Acme",
            "model": "P-42",
            "asset_type": "pump",
        }
        store = {
            "pages": [{"page_number": 1, "text": "Different Model X service manual"}],
            "filename": "different-model-x.pdf",
            "asset_identity": dict(confirmed_asset),
        }

        result = create_cut_plan_workflow(
            store,
            CutPlanRequest(
                pdf_id="pdf-workspace",
                discover_asset_identity=False,
                page_offset=0,
            ),
        )

        mock_call_openai_scoping.assert_not_called()
        self.assertEqual(store["asset_identity"], confirmed_asset)
        self.assertEqual(result.product_info.asset_id, confirmed_asset["asset_id"])
        self.assertEqual(result.product_info.product_name, confirmed_asset["name"])
        self.assertEqual(
            store["run_metrics"]["stages"]["scoping"]["details"]["asset_identity_source"],
            "workspace",
        )

    @patch("backend.services.scoping_workflow.call_openai_scoping")
    @patch("backend.services.scoping_workflow.keyword_scan")
    @patch("backend.services.scoping_workflow.find_toc_pages")
    @patch("backend.services.scoping_workflow.get_effective_small_doc_threshold")
    def test_workspace_toc_extracts_document_metadata_but_not_asset(
        self,
        mock_small_doc_threshold,
        mock_find_toc_pages,
        mock_keyword_scan,
        mock_call_openai_scoping,
    ):
        mock_small_doc_threshold.return_value = 0
        mock_find_toc_pages.return_value = (
            True,
            "Troubleshooting ........ 10\nWarranty ........ 20",
            2,
            2,
        )
        mock_call_openai_scoping.side_effect = [
            (
                '{"document_info":{"document_type":"Service Manual","language":"English"},'
                '"toc_entries":[{"title":"Troubleshooting","page":10},'
                '{"title":"Warranty","page":20}]}',
                {},
            ),
            (
                '{"sections":[{"name":"Troubleshooting","manual_page_start":10,'
                '"manual_page_end":19,"reasoning":"Diagnostic chapter"}]}',
                {},
            ),
        ]
        confirmed_asset = {
            "asset_id": "asset_workspace_pump",
            "name": "Workspace Pump",
            "description": "Operator-confirmed pump",
            "brand": "Acme",
            "model": "P-42",
            "asset_type": "pump",
        }
        store = {
            "pages": [
                {"page_number": page, "text": f"Manual page {page}"}
                for page in range(1, 31)
            ],
            "filename": "possibly-different-product.pdf",
            "asset_identity": dict(confirmed_asset),
        }

        result = create_cut_plan_workflow(
            store,
            CutPlanRequest(
                pdf_id="pdf-workspace",
                discover_asset_identity=False,
                page_offset=0,
            ),
        )

        self.assertEqual(mock_call_openai_scoping.call_count, 2)
        toc_prompt = mock_call_openai_scoping.call_args_list[0].args[0]
        self.assertNotIn("product_name", toc_prompt)
        self.assertIn("Do NOT identify, infer, correct, or return the product", toc_prompt)
        mock_keyword_scan.assert_not_called()
        self.assertEqual(store["asset_identity"], confirmed_asset)
        self.assertEqual(result.product_info.asset_id, confirmed_asset["asset_id"])
        self.assertEqual(result.product_info.document_type, "Service Manual")

    @patch("backend.services.scoping_workflow.call_openai_scoping")
    @patch("backend.services.scoping_workflow.keyword_scan")
    @patch("backend.services.scoping_workflow.find_toc_pages")
    @patch("backend.services.scoping_workflow.get_effective_small_doc_threshold")
    def test_reliable_toc_sections_are_not_expanded_by_keyword_spans(
        self,
        mock_small_doc_threshold,
        mock_find_toc_pages,
        mock_keyword_scan,
        mock_call_openai_scoping,
    ):
        mock_small_doc_threshold.return_value = 0
        mock_find_toc_pages.return_value = (
            True,
            "Troubleshooting ........ 10\nWarranty ........ 20",
            2,
            2,
        )
        mock_call_openai_scoping.side_effect = [
            (
                '{"product_info":{"product_name":"Pump P-1"},'
                '"toc_entries":[{"title":"Troubleshooting","page":10},'
                '{"title":"Warranty","page":20}]}',
                {},
            ),
            (
                '{"sections":[{"name":"Troubleshooting","manual_page_start":10,'
                '"manual_page_end":19,"reasoning":"Diagnostic chapter"}]}',
                {},
            ),
        ]
        pages = [
            {
                "page_number": page,
                "text": "the pump check and replace component during troubleshooting",
            }
            for page in range(1, 31)
        ]

        result = create_cut_plan_workflow(
            {"pages": pages, "filename": "pump.pdf"},
            CutPlanRequest(pdf_id="pdf-1", page_offset=0),
        )

        mock_keyword_scan.assert_not_called()
        self.assertEqual(result.pages_to_keep, list(range(10, 20)))
        self.assertTrue(all(section.source != "keyword" for section in result.sections))

    @patch("backend.services.scoping_workflow.call_openai_scoping")
    @patch("backend.services.scoping_workflow.keyword_scan")
    @patch("backend.services.scoping_workflow.find_toc_pages")
    @patch("backend.services.scoping_workflow.get_effective_small_doc_threshold")
    def test_create_cut_plan_workflow_preserves_component_pages_removed_by_language_filter(
        self,
        mock_small_doc_threshold,
        mock_find_toc_pages,
        mock_keyword_scan,
        mock_call_openai_scoping,
    ):
        mock_small_doc_threshold.return_value = 0
        mock_find_toc_pages.return_value = (False, None, None, None)
        mock_keyword_scan.return_value = [
            SectionInfo(
                name="VB-60 Assembly Drawings & Parts Lists",
                page_range=PageRange(start=15, end=16),
                source="keyword",
                reasoning="Contains assembly drawings and enumerated components.",
            )
        ]
        mock_call_openai_scoping.return_value = (
            '{"product_name":"VB Series","document_type":"Maintenance Manual","language":"English"}',
            {},
        )

        pages = [
            {"page_number": page_number, "text": f"Page {page_number}"}
            for page_number in range(1, 17)
        ]
        pages[14]["text"] = "ITEM NO. PART NO. QTY."
        pages[15]["text"] = "ASSY ITEM PART NO. QTY."

        store = {
            "pages": pages,
            "filename": "VB SERIES FANUC MAINTENANCE MANUAL Ver 1.0.pdf",
        }

        result = create_cut_plan_workflow(store, CutPlanRequest(pdf_id="pdf-1"))

        self.assertEqual(result.pages_to_keep, [15, 16])
        self.assertEqual(
            [section.name for section in result.sections],
            ["VB-60 Assembly Drawings & Parts Lists"],
        )
        self.assertEqual(store["asset_identity"]["name"], "VB Series")
        self.assertEqual(store["asset_identity"]["asset_id"], "asset_vb_series")
        self.assertEqual(store["cut_plan"]["product_info"]["product_name"], "VB Series")


if __name__ == "__main__":
    unittest.main()
