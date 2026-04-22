import unittest
from unittest.mock import patch

from backend.models import CutPlanRequest, PageRange, SectionInfo
from backend.services.scoping_workflow import create_cut_plan_workflow


class ScopingWorkflowTests(unittest.TestCase):
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
