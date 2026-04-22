import unittest

from backend.services.ontology_workflow import _resolve_draft_pages


class OntologyWorkflowPageSelectionTests(unittest.TestCase):
    def test_keeps_scoping_selection_stable_when_asset_identity_is_known(self):
        all_pages = [{"page_number": page_number, "text": f"Page {page_number}"} for page_number in range(1, 11)]

        result = _resolve_draft_pages(
            all_pages,
            pages_to_keep=[3, 4, 5, 8],
            always_include_first_pages=5,
            asset_identity={"name": "VB Series"},
        )

        self.assertEqual([page["page_number"] for page in result], [3, 4, 5, 8])

    def test_can_still_prepend_front_matter_when_asset_identity_is_missing(self):
        all_pages = [{"page_number": page_number, "text": f"Page {page_number}"} for page_number in range(1, 11)]

        result = _resolve_draft_pages(
            all_pages,
            pages_to_keep=[6, 7],
            always_include_first_pages=3,
            asset_identity={},
        )

        self.assertEqual([page["page_number"] for page in result], [1, 2, 3, 6, 7])


if __name__ == "__main__":
    unittest.main()
