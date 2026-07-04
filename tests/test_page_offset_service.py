from __future__ import annotations

import unittest

from backend.services.page_offset_service import (
    detect_offset_from_page_labels,
    detect_offset_from_toc,
    detect_page_offset,
    parse_toc_entries_from_text,
)


def _pages_with_footer_labels(total: int, offset: int, unnumbered_front: int) -> list[dict]:
    """Physical pages where printed numbering starts after some front matter."""
    pages = []
    for physical in range(1, total + 1):
        printed = physical - offset
        text = f"Some section content for physical page {physical}.\n"
        if physical > unnumbered_front and printed >= 1:
            text += f"\n- {printed} -"
        pages.append({"page_number": physical, "text": text})
    return pages


class PageLabelDetectionTests(unittest.TestCase):
    def test_detects_positive_offset_from_footers(self):
        pages = _pages_with_footer_labels(total=20, offset=2, unnumbered_front=2)
        result = detect_offset_from_page_labels(pages)
        self.assertEqual(result["offset"], 2)
        self.assertGreaterEqual(result["confidence"], 0.9)

    def test_zero_offset_document(self):
        pages = _pages_with_footer_labels(total=20, offset=0, unnumbered_front=1)
        self.assertEqual(detect_offset_from_page_labels(pages)["offset"], 0)

    def test_no_labels_yields_no_detection(self):
        pages = [{"page_number": n, "text": "prose without any page footer"} for n in range(1, 10)]
        result = detect_offset_from_page_labels(pages)
        self.assertIsNone(result["offset"])

    def test_inconsistent_labels_yield_no_detection(self):
        # Numbers scattered in content (dates, quantities) must not produce a
        # confident majority.
        pages = [
            {"page_number": 1, "text": "3"},
            {"page_number": 2, "text": "9"},
            {"page_number": 3, "text": "1"},
            {"page_number": 4, "text": "7"},
        ]
        self.assertIsNone(detect_offset_from_page_labels(pages)["offset"])


class TocAnchoringTests(unittest.TestCase):
    def _pages(self) -> list[dict]:
        return [
            {"page_number": 1, "text": "COVER"},
            {"page_number": 2, "text": "TABLE OF CONTENTS\nTroubleshooting Guide ..... 10\nElectrical Diagrams ..... 14"},
            {"page_number": 11, "text": "TROUBLESHOOTING GUIDE\nIf the machine stops, check the fuse."},
            {"page_number": 15, "text": "ELECTRICAL DIAGRAMS\nWiring for the main cabinet."},
        ]

    def test_detects_offset_and_skips_toc_pages(self):
        entries = [
            {"title": "Troubleshooting Guide", "manual_page": 10},
            {"title": "Electrical Diagrams", "manual_page": 14},
        ]
        result = detect_offset_from_toc(self._pages(), entries, toc_page_range=(2, 2))
        self.assertEqual(result["offset"], 1)

    def test_short_titles_are_ignored(self):
        entries = [{"title": "Index", "manual_page": 3}]
        result = detect_offset_from_toc(self._pages(), entries, toc_page_range=(2, 2))
        self.assertIsNone(result["offset"])


class CombinedDetectionTests(unittest.TestCase):
    def test_falls_back_to_zero_when_no_signal(self):
        pages = [{"page_number": n, "text": "no labels here"} for n in range(1, 8)]
        result = detect_page_offset(pages)
        self.assertEqual(result["offset"], 0)
        self.assertEqual(result["source"], "default")

    def test_toc_supersedes_labels(self):
        # Labels say offset 0 (misleading footers); ToC anchoring says 1.
        pages = [
            {"page_number": n, "text": f"content\n- {n} -"} for n in range(1, 8)
        ]
        pages[1]["text"] = "TABLE OF CONTENTS\nTroubleshooting Procedures ..... 4\nMaintenance Schedule ..... 6"
        pages[4]["text"] = "TROUBLESHOOTING PROCEDURES\ndetails\n- 5 -"
        pages[6]["text"] = "MAINTENANCE SCHEDULE\ndetails\n- 7 -"
        entries = [
            {"title": "Troubleshooting Procedures", "manual_page": 4},
            {"title": "Maintenance Schedule", "manual_page": 6},
        ]
        result = detect_page_offset(pages, entries, toc_page_range=(2, 2))
        self.assertEqual(result["offset"], 1)
        self.assertEqual(result["source"], "toc_anchoring")
        self.assertFalse(result["agreement"])


class TocRegexParseTests(unittest.TestCase):
    def test_parses_dotted_and_dashed_entries(self):
        text = (
            "Troubleshooting Guide ......... 10\n"
            "Electrical Diagrams ___ 14\n"
            "not a toc line\n"
            "Ab . 3\n"  # too short / not enough leaders
        )
        entries = parse_toc_entries_from_text(text)
        self.assertEqual(
            [(e["title"], e["manual_page"]) for e in entries],
            [("Troubleshooting Guide", 10), ("Electrical Diagrams", 14)],
        )


class WorkflowAutodetectionTests(unittest.TestCase):
    def test_small_doc_cut_plan_autodetects_offset(self):
        from backend.models import CutPlanRequest
        from backend.services.run_metrics import ensure_run_metrics
        from backend.services.scoping_workflow import create_cut_plan_workflow

        # 10 pages (below the small-doc threshold → no LLM calls) with printed
        # numbering shifted by one cover page.
        store = {
            "pdf_id": "pdf-offset",
            "pages": _pages_with_footer_labels(total=10, offset=1, unnumbered_front=1),
        }
        ensure_run_metrics(store)
        plan = create_cut_plan_workflow(store, CutPlanRequest(pdf_id="pdf-offset"))
        self.assertEqual(plan.page_offset, 1)
        self.assertEqual(plan.page_offset_detection["source"], "page_labels")

    def test_explicit_offset_is_never_overridden(self):
        from backend.models import CutPlanRequest
        from backend.services.run_metrics import ensure_run_metrics
        from backend.services.scoping_workflow import create_cut_plan_workflow

        store = {
            "pdf_id": "pdf-offset",
            "pages": _pages_with_footer_labels(total=10, offset=1, unnumbered_front=1),
        }
        ensure_run_metrics(store)
        plan = create_cut_plan_workflow(store, CutPlanRequest(pdf_id="pdf-offset", page_offset=0))
        self.assertEqual(plan.page_offset, 0)
        self.assertIsNone(plan.page_offset_detection)


if __name__ == "__main__":
    unittest.main()
