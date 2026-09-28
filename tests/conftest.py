"""Test-wide defaults: every test runs offline, without model calls."""

import os
import tempfile

# Archived provider responses of fake clients stay out of the repository.
os.environ.setdefault("KG_LLM_TRACE_DIR", tempfile.mkdtemp(prefix="kg_v3_test_trace_"))
