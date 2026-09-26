"""Test-wide defaults."""

import os

# The retained v22 PDF tests exercise the frozen v22 builder; V3 tests opt in.
os.environ.setdefault("KG_PDF_GENERATOR", "legacy_v22")
