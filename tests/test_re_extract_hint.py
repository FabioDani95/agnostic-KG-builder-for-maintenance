"""The re_extract_pages chat tool must honor its `hint` argument and skip the
graph-projection shortcut (projection ignores the requested page range)."""

import asyncio
import unittest
from unittest.mock import patch

from backend.models import ExtractionResult, ExtractRequest
from backend.services.conversation.tools.extraction import _re_extract_pages
from backend.services.extraction_workflow import extract_triplets_workflow


def _store_with_pages() -> dict:
    return {
        "pdf_id": "pdf-test",
        "pages": [
            {"page_number": 1, "text": "Page one text"},
            {"page_number": 2, "text": "Page two text"},
        ],
        "cut_plan": {"pages_to_keep": [1, 2]},
        "source_type": "manual",
        "source_title": "Mock Manual",
        "graph_state": {"cleaned_triplets": []},
    }


def _empty_result() -> ExtractionResult:
    return ExtractionResult(
        triplets=[],
        raw_symptom_table="",
        raw_failure_mode_table="",
        raw_corrective_action_table="",
    )


class ReExtractHintTests(unittest.TestCase):
    def test_hint_and_force_llm_reach_workflow_request(self):
        captured: dict = {}

        def fake_workflow(store, req, on_event=None):
            captured["req"] = req
            return _empty_result(), []

        with patch(
            "backend.services.extraction_workflow.extract_triplets_workflow",
            side_effect=fake_workflow,
        ):
            result = asyncio.run(
                _re_extract_pages(
                    {"start_page": 1, "end_page": 2, "hint": "error code E42"},
                    _store_with_pages(),
                    on_event=None,
                )
            )

        self.assertEqual(result["status"], "ok")
        req = captured["req"]
        self.assertEqual(req.hint, "error code E42")
        self.assertTrue(req.force_llm)

    def test_force_llm_skips_graph_projection(self):
        store = _store_with_pages()
        req = ExtractRequest(
            pdf_id="pdf-test",
            source_type="manual",
            source_title="Mock Manual",
            hint="error code E42",
            force_llm=True,
        )
        captured: dict = {}

        def fake_chunked(**kwargs):
            captured.update(kwargs)
            return _empty_result(), {"chunk_count": 0}

        with (
            patch(
                "backend.services.extraction_workflow.extract_triplets_chunked",
                side_effect=fake_chunked,
            ),
            patch(
                "backend.services.graph_projection_service.graph_has_validatable_chains",
                return_value=True,
            ) as has_chains,
            patch(
                "backend.services.graph_projection_service.project_graph_to_triplets"
            ) as project,
        ):
            extract_triplets_workflow(store, req, on_event=None)

        project.assert_not_called()
        has_chains.assert_not_called()
        self.assertEqual(captured.get("hint"), "error code E42")

    def test_hint_is_injected_into_chunk_context(self):
        from backend.services import llm_service

        captured: dict = {}

        def fake_call_openai(**kwargs):
            captured.update(kwargs)
            return "", {"operation": "extraction", "prompt": 0, "completion": 0, "total": 0}

        with patch.object(llm_service, "call_openai", side_effect=fake_call_openai):
            llm_service.extract_triplets_chunked(
                pages=[{"page_number": 1, "text": "Page one text"}],
                source_type="manual",
                source_title="Mock Manual",
                target_language="en",
                hint="error code E42",
            )

        self.assertIn("OPERATOR HINT", captured.get("section_context", ""))
        self.assertIn("error code E42", captured["section_context"])


if __name__ == "__main__":
    unittest.main()
