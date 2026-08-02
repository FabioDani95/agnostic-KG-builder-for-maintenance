"""Read-only G1 run accounting projection for API and operator drill-down."""

from __future__ import annotations

from typing import Any

from backend.storage.repositories.operational_runs import OperationalRunRepository
from backend.storage.repositories.raw_units import RawUnitRepository


def foundation_run_report(run_id: str) -> dict[str, Any]:
    """Return counters only from inventory plus the active disposition view."""
    run = OperationalRunRepository().get(run_id)
    report = RawUnitRepository().accounting_report(run_id)
    return {
        **report,
        "run": run.model_dump(mode="json"),
    }
