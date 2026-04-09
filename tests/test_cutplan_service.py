import unittest

from backend.models import TocEntry
from backend.services.cutplan_service import normalize_product_info, select_toc_sections


class CutPlanServiceTests(unittest.TestCase):
    def test_normalize_product_info_cleans_manual_labels(self):
        normalized = normalize_product_info(
            {
                "product_name": "Service Manual - UR Series Control box 5.5/5.6",
                "document_type": "service manual",
                "language": "English",
            },
            filename="Service-Manual-UR-Series-en.pdf",
        )
        self.assertEqual(normalized["product_name"], "UR Series Control box 5.5/5.6")
        self.assertEqual(normalized["document_type"], "service manual")
        self.assertEqual(normalized["language"], "English")

    def test_normalize_product_info_uses_filename_fallback(self):
        normalized = normalize_product_info({}, filename="Service-Manual-UR-Series-en.pdf")
        self.assertEqual(normalized["product_name"], "UR Series")

    def test_select_toc_sections_prefers_service_relevant_titles(self):
        toc_entries = [
            TocEntry(title="Introduction", manual_page=1),
            TocEntry(title="Safety", manual_page=5),
            TocEntry(title="Troubleshooting", manual_page=20),
            TocEntry(title="Replacing power supply", manual_page=30),
            TocEntry(title="Calibration", manual_page=40),
            TocEntry(title="Spare parts", manual_page=50),
        ]

        sections = select_toc_sections(toc_entries, page_offset=0, total_pages=60)
        section_names = [section.name for section in sections]

        self.assertEqual(section_names, [
            "Troubleshooting",
            "Replacing power supply",
            "Calibration",
        ])
        self.assertEqual(sections[0].manual_page_range.start, 20)
        self.assertEqual(sections[0].manual_page_range.end, 29)


if __name__ == "__main__":
    unittest.main()
