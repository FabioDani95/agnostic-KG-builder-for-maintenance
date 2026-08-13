#!/usr/bin/env python3
"""One-shot v10 runner using the frozen manuals and evaluation-only golden."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "diagnostic_benchmark_second_hardening_20260813" / "run_benchmark_once.py"


def main() -> int:
    spec = importlib.util.spec_from_file_location("v9_runner_base", BASE)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the parameterized v9 runner")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.CAMPAIGN_ROOT = ROOT
    runner.CAMPAIGN_ID = "pdf-g3-diagnostic-second-hardening-20260813-v10"
    runner.RUN_ID_PREFIX = "v10"
    runner.RUNNER_PATH = Path(__file__)
    return int(runner.main())


if __name__ == "__main__":
    raise SystemExit(main())
