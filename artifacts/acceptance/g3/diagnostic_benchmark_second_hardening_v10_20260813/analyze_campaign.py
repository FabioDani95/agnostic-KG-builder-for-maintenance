#!/usr/bin/env python3
"""Analyze v10 against the untouched frozen claims and KPI thresholds."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "diagnostic_benchmark_second_hardening_20260813" / "analyze_campaign.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location("v9_analyzer_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the parameterized v9 analyzer")
    analyzer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(analyzer)
    analyzer.ROOT = ROOT
    analyzer.CAMPAIGN_ID = "pdf-g3-diagnostic-second-hardening-20260813-v10"
    analyzer.EXPECTED_PIPELINE_VERSION = "pdf-g3-atomic-record-publication-v10"
    analyzer.RUN_ID_PREFIX = "v10"
    analyzer.main()


if __name__ == "__main__":
    main()
