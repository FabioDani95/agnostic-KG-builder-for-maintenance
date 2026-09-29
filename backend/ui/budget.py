"""Spending read from the real-call ledger, and time and cost estimates from past runs.

The ledger is only read here; every real call still goes through the budgeted gateway
of the command line.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.ui.catalog import Catalog

# Run IDs of the runs started from the interface start with this prefix.
UI_RUN_PREFIX = "ui_"


@dataclass(frozen=True)
class Limits:
    budget_usd: float = 20.0  # absolute budget of the campaign ledger
    ceiling_usd: float = 15.0  # --spend-ceiling of every run started here (Fabio, 2026-09-29)
    ui_limit_usd: float = 0.5  # all interface work together (docs/PROMPT_FRONTEND.md)


class Spending:
    def __init__(self, ledger: Path, limits: Limits) -> None:
        self.ledger = ledger
        self.limits = limits
        self._cache: tuple[tuple[int, int], dict[str, Any]] | None = None

    def snapshot(self) -> dict[str, Any]:
        if not self.ledger.exists():
            return {"committed_usd": 0.0, "reserved_usd": 0.0, "ceiling_usd": self.limits.ceiling_usd,
                    "budget_usd": self.limits.budget_usd, "ui_limit_usd": self.limits.ui_limit_usd,
                    "ui_spent_usd": 0.0}
        stat = self.ledger.stat()
        stamp = (stat.st_mtime_ns, stat.st_size)
        if self._cache and self._cache[0] == stamp:
            return self._cache[1]
        committed = reserved_total = ui_spent = 0.0
        reserved: dict[str, float] = {}
        with self.ledger.open(encoding="utf-8") as handle:
            for line in handle:
                if '"call_reserved"' in line:
                    entry = json.loads(line)
                    reserved[entry["call_id"]] = float(entry.get("worst_case_cost_usd") or 0.0)
                elif '"call_finalized"' in line:
                    entry = json.loads(line)
                    charged = float(entry.get("charged_cost_usd") or 0.0)
                    committed += charged
                    reserved.pop(entry["call_id"], None)
                    if str(entry["call_id"]).startswith(UI_RUN_PREFIX):
                        ui_spent += charged
        reserved_total = sum(reserved.values())
        value = {"committed_usd": round(committed, 4), "reserved_usd": round(reserved_total, 4),
                 "ceiling_usd": self.limits.ceiling_usd, "budget_usd": self.limits.budget_usd,
                 "ui_limit_usd": self.limits.ui_limit_usd, "ui_spent_usd": round(ui_spent, 4)}
        self._cache = (stamp, value)
        return value


def estimate(catalog: Catalog, pages: int) -> dict[str, Any]:
    """Range of time and cost of the two current campaign runs closest in page count."""

    samples = []
    for manual in catalog.manuals():
        current = [version for version in manual.versions
                   if version.origin == "campaign" and version.iteration == "" and version.cost_usd is not None
                   and version.seconds and version.status != "failed"]
        if current and manual.pages:
            version = current[0]
            samples.append((abs(manual.pages - pages), manual.id, version.seconds, version.cost_usd))
    samples.sort()
    nearest = samples[:2]
    if not nearest:
        return {"seconds": None, "cost_usd": None, "based_on": []}
    seconds = sorted(round(item[2]) for item in nearest)
    costs = sorted(round(item[3], 3) for item in nearest)
    return {"seconds": [seconds[0], seconds[-1]], "cost_usd": [costs[0], costs[-1]],
            "based_on": [item[1] for item in nearest]}
