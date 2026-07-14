import unittest

from backend.models import TocEntry
from backend.services.cutplan_service import (
    extract_asset_identity,
    find_toc_pages,
    is_component_inventory_section,
    normalize_product_info,
    select_toc_sections,
)


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
        self.assertEqual(normalized["product_short_name"], "UR Series Control box 5.5/5.6")
        self.assertEqual(normalized["asset_id"], "asset_ur_series_control_box_5_5_5_6")
        self.assertEqual(normalized["asset_type"], "control box")
        self.assertEqual(normalized["document_type"], "service manual")
        self.assertEqual(normalized["language"], "English")

    def test_normalize_product_info_uses_filename_fallback(self):
        normalized = normalize_product_info({}, filename="Service-Manual-UR-Series-en.pdf")
        self.assertEqual(normalized["product_name"], "UR Series")
        self.assertEqual(normalized["asset_id"], "asset_ur_series")

    def test_extract_asset_identity_prefers_source_title_over_filename(self):
        identity = extract_asset_identity(
            {},
            fallback_name="Acme Pump P-100",
            source_type="maintenance manual",
            filename="clean_pump_manual.md",
        )

        self.assertEqual(identity["name"], "Acme Pump P-100")
        self.assertEqual(identity["brand"], "Acme")
        self.assertEqual(identity["model"], "P-100")
        self.assertEqual(identity["asset_id"], "asset_acme_p_100")

    def test_extract_asset_identity_infers_brand_and_model_from_source_title(self):
        identity = extract_asset_identity(
            {},
            fallback_name="RoboLift RL-5",
            source_type="service bulletin",
            filename="noisy_table_robot_manual.md",
        )

        self.assertEqual(identity["brand"], "RoboLift")
        self.assertEqual(identity["model"], "RL-5")
        self.assertEqual(identity["product_short_name"], "RoboLift RL-5")

    def test_normalize_product_info_preserves_brand_and_model_when_available(self):
        normalized = normalize_product_info(
            {
                "product_name": "Eagle Automatic Laser Cutting System Model: Eagle S3L",
                "product_short_name": "Eastman Eagle S3L",
                "brand": "Eastman",
                "model": "Eagle S3L",
                "document_type": "Service Manual",
                "language": "English",
            },
            filename="eagle_s3l_laser_cutting_system_service_manual.pdf",
        )
        self.assertEqual(normalized["brand"], "Eastman")
        self.assertEqual(normalized["model"], "Eagle S3L")
        self.assertEqual(normalized["product_short_name"], "Eastman Eagle S3L")
        self.assertEqual(normalized["asset_id"], "asset_eastman_eagle_s3l")

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
            "Spare parts",
        ])
        self.assertEqual(sections[0].manual_page_range.start, 20)
        self.assertEqual(sections[0].manual_page_range.end, 29)

    def test_select_toc_sections_does_not_shift_when_manual_page_one_is_pdf_page_one(self):
        toc_entries = [
            TocEntry(title="Reference Manuals", manual_page=8),
            TocEntry(title="INSTALLATION", manual_page=8),
            TocEntry(title="Table Assembly", manual_page=9),
        ]

        sections = select_toc_sections(toc_entries, page_offset=0, total_pages=20)

        self.assertEqual(sections[0].name, "INSTALLATION")
        self.assertEqual(sections[0].manual_page_range.start, 8)
        self.assertEqual(sections[0].page_range.start, 8)
        self.assertEqual(sections[0].page_range.end, 8)

    def test_select_toc_sections_includes_component_inventory_titles(self):
        toc_entries = [
            TocEntry(title="ATC Operation", manual_page=31),
            TocEntry(title="VB-60 Assembly Drawings & Parts Lists", manual_page=76),
            TocEntry(title="Table Guard Assembly Drawings & Parts Lists", manual_page=86),
            TocEntry(title="Warranty", manual_page=120),
        ]

        sections = select_toc_sections(toc_entries, page_offset=0, total_pages=130)
        section_names = [section.name for section in sections]

        self.assertEqual(section_names, [
            "VB-60 Assembly Drawings & Parts Lists",
            "Table Guard Assembly Drawings & Parts Lists",
        ])
        self.assertEqual(sections[0].manual_page_range.start, 76)
        self.assertEqual(sections[0].manual_page_range.end, 85)

    def test_is_component_inventory_section_matches_parts_lists_and_reference_diagrams(self):
        self.assertTrue(is_component_inventory_section("VB-60 Assembly Drawings & Parts Lists"))
        self.assertTrue(is_component_inventory_section("Control Circuit Reference Diagram"))
        self.assertFalse(is_component_inventory_section("Revision History"))


class FindTocPagesTests(unittest.TestCase):
    @staticmethod
    def _pages(total: int, toc_start: int, toc_len: int) -> list[dict]:
        pages = []
        for number in range(1, total + 1):
            if toc_start <= number < toc_start + toc_len:
                header = "Contents\n" if number == toc_start else ""
                text = header + "\n".join(
                    f"Section {number}.{idx} title . . . . . . {number + idx}"
                    for idx in range(1, 6)
                )
            else:
                text = f"Ordinary body text of page {number}."
            pages.append({"page_number": number, "text": text})
        return pages

    def test_toc_behind_long_front_matter_is_found_on_large_manuals(self):
        # ToC at physical page 17 of a 500-page manual: the old fixed 15-page
        # scan window missed it entirely (observed on a real Haas manual).
        pages = self._pages(total=500, toc_start=17, toc_len=3)
        found, toc_text, start, end = find_toc_pages(pages)
        self.assertTrue(found)
        self.assertEqual(start, 17)
        self.assertGreaterEqual(end, 19)

    def test_long_toc_is_collected_beyond_six_pages(self):
        pages = self._pages(total=200, toc_start=5, toc_len=15)
        found, toc_text, start, end = find_toc_pages(pages)
        self.assertTrue(found)
        self.assertEqual(start, 5)
        self.assertEqual(end, 19)
        self.assertIn("--- PAGE 19 ---", toc_text)

    def test_small_doc_default_window_still_15_pages(self):
        pages = self._pages(total=30, toc_start=14, toc_len=2)
        found, _, start, _ = find_toc_pages(pages)
        self.assertTrue(found)
        self.assertEqual(start, 14)


if __name__ == "__main__":
    unittest.main()
