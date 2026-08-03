"""Immutable RawUnit inventory and append-only terminal disposition ledger."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from typing import Any

from backend.domain.evidence import RawUnitDraft
from backend.domain.ids import new_id, utc_now
from backend.domain.runs import (
    DispositionError,
    DispositionOutcome,
    RawUnitDisposition,
    Retryability,
)
from backend.storage.database import Database, get_database


class RawUnitConflictError(RuntimeError):
    pass


class LedgerBalanceError(RuntimeError):
    pass


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class RawUnitRepository:
    def __init__(self, database: Database | None = None):
        self.database = database or get_database()

    def register_inventory(self, raw_units: list[RawUnitDraft]) -> list[RawUnitDraft]:
        """Persist the complete deterministic inventory before any disposition."""
        now = utc_now()
        with self.database.transaction() as connection:
            for raw_unit in raw_units:
                locator_json = _canonical_json(raw_unit.locator.model_dump(mode="json"))
                locator_hash = hashlib.sha256(locator_json.encode("utf-8")).hexdigest()
                existing = connection.execute(
                    "SELECT * FROM raw_units WHERE raw_unit_id = ?",
                    (raw_unit.raw_unit_id,),
                ).fetchone()
                if existing is not None:
                    expected = {
                        "parent_raw_unit_id": raw_unit.parent_raw_unit_id,
                        "source_id": raw_unit.source_id,
                        "unit_kind": raw_unit.unit_kind,
                        "structure_id": raw_unit.structure_id,
                        "locator_json": locator_json,
                        "locator_hash": locator_hash,
                        "raw_hash": raw_unit.raw_hash,
                        "adapter_version": raw_unit.adapter_version,
                        "quality_flags_json": _canonical_json(
                            [flag.value for flag in raw_unit.quality_flags]
                        ),
                    }
                    if any(existing[key] != value for key, value in expected.items()):
                        raise RawUnitConflictError(
                            f"Stable RawUnit ID has different immutable content: {raw_unit.raw_unit_id}"
                        )
                    continue
                owner = connection.execute(
                    "SELECT entity_type FROM entity_ids WHERE entity_id = ?",
                    (raw_unit.raw_unit_id,),
                ).fetchone()
                if owner is not None:
                    raise RawUnitConflictError(
                        f"RawUnit ID is already owned by {owner['entity_type']}: {raw_unit.raw_unit_id}"
                    )
                connection.execute(
                    "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'raw_unit', ?)",
                    (raw_unit.raw_unit_id, now),
                )
                connection.execute(
                    """
                    INSERT INTO raw_units(
                        raw_unit_id, parent_raw_unit_id, source_id, unit_kind, structure_id,
                        locator_json, locator_hash, raw_hash, adapter_version,
                        quality_flags_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        raw_unit.raw_unit_id,
                        raw_unit.parent_raw_unit_id,
                        raw_unit.source_id,
                        raw_unit.unit_kind,
                        raw_unit.structure_id,
                        locator_json,
                        locator_hash,
                        raw_unit.raw_hash,
                        raw_unit.adapter_version,
                        _canonical_json([flag.value for flag in raw_unit.quality_flags]),
                        now,
                    ),
                )
        return raw_units

    def list_inventory(self, source_id: str) -> list[RawUnitDraft]:
        """Reload the immutable adapter inventory without parsing the source again."""
        with self.database.read() as connection:
            rows = connection.execute(
                """
                SELECT * FROM raw_units
                WHERE source_id = ?
                ORDER BY parent_raw_unit_id, raw_unit_id
                """,
                (source_id,),
            ).fetchall()
        return [
            RawUnitDraft(
                raw_unit_id=row["raw_unit_id"],
                parent_raw_unit_id=row["parent_raw_unit_id"],
                unit_kind=row["unit_kind"],
                source_id=row["source_id"],
                structure_id=row["structure_id"],
                locator=json.loads(row["locator_json"]),
                raw_hash=row["raw_hash"],
                adapter_version=row["adapter_version"],
                quality_flags=json.loads(row["quality_flags_json"]),
            )
            for row in rows
        ]

    def append_disposition(
        self,
        *,
        run_id: str,
        raw_unit_id: str,
        outcome: DispositionOutcome,
        reason_code: str,
        evidence_ids: list[str] | None = None,
        canonical_raw_unit_id: str | None = None,
        checkpoint_id: str | None = None,
        retryability: Retryability = Retryability.NOT_APPLICABLE,
        error: DispositionError | None = None,
    ) -> RawUnitDisposition:
        now = utc_now()
        disposition_id = new_id("disposition")
        with self.database.transaction() as connection:
            attempt = int(
                connection.execute(
                    """
                    SELECT COALESCE(MAX(attempt), 0) + 1
                    FROM raw_unit_dispositions
                    WHERE run_id = ? AND raw_unit_id = ?
                    """,
                    (run_id, raw_unit_id),
                ).fetchone()[0]
            )
            disposition = RawUnitDisposition(
                disposition_id=disposition_id,
                run_id=run_id,
                raw_unit_id=raw_unit_id,
                attempt=attempt,
                outcome=outcome,
                reason_code=reason_code,
                canonical_raw_unit_id=canonical_raw_unit_id,
                evidence_ids=evidence_ids or [],
                checkpoint_id=checkpoint_id,
                retryability=retryability,
                error=error,
                created_at=now,
            )
            connection.execute(
                "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'disposition', ?)",
                (disposition_id, now),
            )
            connection.execute(
                """
                INSERT INTO raw_unit_dispositions(
                    disposition_id, run_id, raw_unit_id, attempt, outcome, reason_code,
                    canonical_raw_unit_id, evidence_ids_json, checkpoint_id,
                    retryability, error_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    disposition.disposition_id,
                    disposition.run_id,
                    disposition.raw_unit_id,
                    disposition.attempt,
                    disposition.outcome.value,
                    disposition.reason_code,
                    disposition.canonical_raw_unit_id,
                    _canonical_json(disposition.evidence_ids),
                    disposition.checkpoint_id,
                    disposition.retryability.value,
                    (
                        _canonical_json(disposition.error.model_dump(mode="json"))
                        if disposition.error
                        else None
                    ),
                    now,
                ),
            )
        return disposition

    def append_dispositions(
        self,
        *,
        run_id: str,
        items: list[dict[str, Any]],
    ) -> list[RawUnitDisposition]:
        """Append a prepared batch in one durable transaction for structured sources."""
        now = utc_now()
        dispositions: list[RawUnitDisposition] = []
        with self.database.transaction() as connection:
            for item in items:
                disposition_id = new_id("disposition")
                attempt = int(
                    connection.execute(
                        """
                        SELECT COALESCE(MAX(attempt), 0) + 1
                        FROM raw_unit_dispositions
                        WHERE run_id = ? AND raw_unit_id = ?
                        """,
                        (run_id, item["raw_unit_id"]),
                    ).fetchone()[0]
                )
                disposition = RawUnitDisposition(
                    disposition_id=disposition_id,
                    run_id=run_id,
                    raw_unit_id=item["raw_unit_id"],
                    attempt=attempt,
                    outcome=item["outcome"],
                    reason_code=item["reason_code"],
                    evidence_ids=item.get("evidence_ids", []),
                    retryability=item.get("retryability", Retryability.NOT_APPLICABLE),
                    error=item.get("error"),
                    created_at=now,
                )
                connection.execute(
                    "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'disposition', ?)",
                    (disposition_id, now),
                )
                connection.execute(
                    """
                    INSERT INTO raw_unit_dispositions(
                        disposition_id, run_id, raw_unit_id, attempt, outcome, reason_code,
                        canonical_raw_unit_id, evidence_ids_json, checkpoint_id,
                        retryability, error_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, ?, ?, ?)
                    """,
                    (
                        disposition.disposition_id,
                        disposition.run_id,
                        disposition.raw_unit_id,
                        disposition.attempt,
                        disposition.outcome.value,
                        disposition.reason_code,
                        _canonical_json(disposition.evidence_ids),
                        disposition.retryability.value,
                        (
                            _canonical_json(disposition.error.model_dump(mode="json"))
                            if disposition.error
                            else None
                        ),
                        now,
                    ),
                )
                dispositions.append(disposition)
        return dispositions

    def dispositions_for(self, run_id: str, raw_unit_id: str) -> list[RawUnitDisposition]:
        with self.database.read() as connection:
            rows = connection.execute(
                """
                SELECT * FROM raw_unit_dispositions
                WHERE run_id = ? AND raw_unit_id = ?
                ORDER BY attempt
                """,
                (run_id, raw_unit_id),
            ).fetchall()
        return [self._disposition_from_row(row) for row in rows]

    def accounting_report(self, run_id: str) -> dict[str, Any]:
        with self.database.read() as connection:
            run = connection.execute(
                "SELECT run_id, workspace_id, state, manifest_json FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run is None:
                raise LookupError(run_id)
            rows = connection.execute(
                """
                SELECT
                    ru.*, d.disposition_id, d.attempt, d.outcome, d.reason_code,
                    d.canonical_raw_unit_id, d.evidence_ids_json, d.checkpoint_id,
                    d.retryability, d.error_json, d.created_at AS disposition_created_at
                FROM run_sources rs
                JOIN raw_units ru ON ru.source_id = rs.source_id
                LEFT JOIN active_raw_unit_dispositions d
                  ON d.run_id = rs.run_id AND d.raw_unit_id = ru.raw_unit_id
                WHERE rs.run_id = ?
                ORDER BY ru.source_id, ru.parent_raw_unit_id, ru.raw_unit_id
                """,
                (run_id,),
            ).fetchall()

        raw_items: list[dict[str, Any]] = []
        for row in rows:
            disposition = None
            if row["disposition_id"] is not None:
                disposition = {
                    "disposition_id": row["disposition_id"],
                    "attempt": row["attempt"],
                    "outcome": row["outcome"],
                    "reason_code": row["reason_code"],
                    "canonical_raw_unit_id": row["canonical_raw_unit_id"],
                    "evidence_ids": json.loads(row["evidence_ids_json"]),
                    "checkpoint_id": row["checkpoint_id"],
                    "retryability": row["retryability"],
                    "error": json.loads(row["error_json"]) if row["error_json"] else None,
                    "created_at": row["disposition_created_at"],
                }
            raw_items.append(
                {
                    "raw_unit_id": row["raw_unit_id"],
                    "parent_raw_unit_id": row["parent_raw_unit_id"],
                    "source_id": row["source_id"],
                    "unit_kind": row["unit_kind"],
                    "structure_id": row["structure_id"],
                    "locator": json.loads(row["locator_json"]),
                    "locator_hash": row["locator_hash"],
                    "raw_hash": row["raw_hash"],
                    "adapter_version": row["adapter_version"],
                    "quality_flags": json.loads(row["quality_flags_json"]),
                    "disposition": disposition,
                }
            )

        sources = []
        for source_id in sorted({item["source_id"] for item in raw_items}):
            items = [item for item in raw_items if item["source_id"] == source_id]
            top = [item for item in items if item["parent_raw_unit_id"] is None]
            children = [item for item in items if item["parent_raw_unit_id"] is not None]
            parent_groups = []
            for parent_id in sorted({item["parent_raw_unit_id"] for item in children}):
                group = [item for item in children if item["parent_raw_unit_id"] == parent_id]
                parent = next(item for item in top if item["raw_unit_id"] == parent_id)
                parent_groups.append(
                    {
                        "parent_raw_unit_id": parent_id,
                        "parent_locator": parent["locator"],
                        **self._balance(group),
                    }
                )
            sources.append(
                {
                    "source_id": source_id,
                    **self._balance(items),
                    "top_level": self._balance(top),
                    "child_aggregate": self._balance(children),
                    "parent_groups": parent_groups,
                }
            )

        canonical_ledger = [
            {
                "raw_unit_id": item["raw_unit_id"],
                "parent_raw_unit_id": item["parent_raw_unit_id"],
                "source_id": item["source_id"],
                "locator_hash": item["locator_hash"],
                "raw_hash": item["raw_hash"],
                "active_disposition": item["disposition"],
            }
            for item in raw_items
        ]
        ledger_hash = hashlib.sha256(
            _canonical_json(canonical_ledger).encode("utf-8")
        ).hexdigest()
        balanced = all(
            source["balanced"]
            and source["top_level"]["balanced"]
            and source["child_aggregate"]["balanced"]
            and all(group["balanced"] for group in source["parent_groups"])
            for source in sources
        )
        failures = {
            retryability: [
                item
                for item in raw_items
                if item["disposition"] is not None
                and item["disposition"]["outcome"] == "failed"
                and item["disposition"]["retryability"] == retryability
            ]
            for retryability in ("same_run", "new_run_required", "not_retryable")
        }
        return {
            "run_id": run_id,
            "workspace_id": run["workspace_id"],
            "run_state": run["state"],
            "ledger_hash": ledger_hash,
            "balanced": balanced,
            "unclassified_total": sum(source["unclassified"] for source in sources),
            "sources": sources,
            "attention": {
                "retryable_same_run": failures["same_run"],
                "new_run_required": failures["new_run_required"],
                "terminal_failures": failures["not_retryable"],
                "quarantined": [
                    item
                    for item in raw_items
                    if item["disposition"] is not None
                    and item["disposition"]["outcome"] == "quarantined"
                ],
                "excluded": [
                    item
                    for item in raw_items
                    if item["disposition"] is not None
                    and item["disposition"]["outcome"] == "excluded"
                ],
            },
            "raw_units": raw_items,
        }

    def assert_balanced(self, run_id: str) -> dict[str, Any]:
        report = self.accounting_report(run_id)
        if not report["balanced"] or report["unclassified_total"] != 0:
            raise LedgerBalanceError(f"Run {run_id} has unclassified RawUnit inventory")
        return report

    @staticmethod
    def _balance(items: list[dict[str, Any]]) -> dict[str, Any]:
        outcomes = Counter(
            item["disposition"]["outcome"]
            for item in items
            if item["disposition"] is not None
        )
        classified = sum(outcomes.values())
        unclassified = len(items) - classified
        ordered_outcomes = {
            outcome: outcomes.get(outcome, 0)
            for outcome in ("processed", "duplicate", "excluded", "quarantined", "failed")
        }
        return {
            "inventory": len(items),
            "outcomes": ordered_outcomes,
            "classified": classified,
            "unclassified": unclassified,
            "balanced": len(items) == classified and unclassified == 0,
        }

    @staticmethod
    def _disposition_from_row(row: sqlite3.Row) -> RawUnitDisposition:
        return RawUnitDisposition(
            disposition_id=row["disposition_id"],
            run_id=row["run_id"],
            raw_unit_id=row["raw_unit_id"],
            attempt=row["attempt"],
            outcome=row["outcome"],
            reason_code=row["reason_code"],
            canonical_raw_unit_id=row["canonical_raw_unit_id"],
            evidence_ids=json.loads(row["evidence_ids_json"]),
            checkpoint_id=row["checkpoint_id"],
            retryability=row["retryability"],
            error=(
                DispositionError.model_validate(json.loads(row["error_json"]))
                if row["error_json"]
                else None
            ),
            created_at=row["created_at"],
        )
