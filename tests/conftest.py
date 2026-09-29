"""Test-wide defaults: every test runs offline, without model calls."""

import os
import tempfile

import pytest

# Archived provider responses of fake clients stay out of the repository.
os.environ.setdefault("KG_LLM_TRACE_DIR", tempfile.mkdtemp(prefix="kg_v3_test_trace_"))


@pytest.fixture()
def manual_doc(tmp_path):
    """The one-page troubleshooting manual of the scripted pipeline tests, read like a real PDF."""

    from backend.kg_v3.reader import read_document
    from scripts.kg_v3 import load_evidence
    from tests.test_kg_v3_reader import ASSET, troubleshooting_pdf

    pdf = tmp_path / "manual.pdf"
    troubleshooting_pdf(pdf)
    evidence, page_count, _ = load_evidence(pdf, ASSET)
    return read_document(list(evidence), page_count=page_count)
