"""Persistent canonical Run repository for the foundation ingestion path."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.domain.ids import new_id, utc_now
from backend.domain.runs import Run, RunState, validate_run_transition
from backend.storage.database import Database, get_database


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class OperationalRunRepository:
    def __init__(self, database: Database | None = None):
        self.database = database or get_database()

    def create(
        self,
        *,
        workspace_id: str,
        source_ids: list[str],
        config: dict[str, Any],
    ) -> Run:
        run_id = new_id("run")
        now = utc_now()
        config_json = _canonical_json(config)
        config_hash = hashlib.sha256(config_json.encode("utf-8")).hexdigest()
        manifest = {
            "run_id": run_id,
            "workspace_id": workspace_id,
            "source_ids": sorted(source_ids),
            "config_hash": config_hash,
            "ledger_hash": None,
            "created_at": now,
        }
        with self.database.transaction() as connection:
            active = connection.execute(
                """
                SELECT DISTINCT r.run_id, r.state
                FROM runs r
                JOIN run_sources rs ON rs.run_id = r.run_id
                WHERE r.workspace_id = ?
                  AND rs.source_id IN ({})
                  AND r.state NOT IN (
                      'published', 'failed_terminal', 'cancelled', 'superseded'
                  )
                """.format(",".join("?" for _ in source_ids)),
                (workspace_id, *source_ids),
            ).fetchall()
            for row in active:
                connection.execute(
                    """
                    UPDATE runs
                    SET state = 'superseded', resume_state = NULL,
                        state_changed_at = ?, updated_at = ?
                    WHERE run_id = ?
                    """,
                    (now, now, row["run_id"]),
                )
            connection.execute(
                "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'run', ?)",
                (run_id, now),
            )
            connection.execute(
                """
                INSERT INTO runs(
                    run_id, workspace_id, state, resume_state, config_hash, config_json,
                    manifest_json, state_changed_at, created_at, updated_at
                ) VALUES (?, ?, 'created', NULL, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    workspace_id,
                    config_hash,
                    config_json,
                    _canonical_json(manifest),
                    now,
                    now,
                    now,
                ),
            )
            for source_id in sorted(set(source_ids)):
                connection.execute(
                    "INSERT INTO run_sources(run_id, source_id) VALUES (?, ?)",
                    (run_id, source_id),
                )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'run_created', ?, ?, ?)
                """,
                (
                    workspace_id,
                    run_id,
                    _canonical_json({"config_hash": config_hash, "source_ids": sorted(source_ids)}),
                    now,
                ),
            )
        return self.get(run_id)

    def get(self, run_id: str) -> Run:
        with self.database.read() as connection:
            row = connection.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise LookupError(run_id)
        return self._from_row(row)

    def latest_for_source(self, source_id: str) -> Run | None:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT r.*
                FROM runs r
                JOIN run_sources rs ON rs.run_id = r.run_id
                WHERE rs.source_id = ?
                ORDER BY r.created_at DESC, r.run_id DESC
                LIMIT 1
                """,
                (source_id,),
            ).fetchone()
        return self._from_row(row) if row is not None else None

    def transition(
        self,
        run_id: str,
        target: RunState,
        *,
        resume_state: RunState | None = None,
    ) -> Run:
        current = self.get(run_id)
        validate_run_transition(
            current.state,
            target,
            current_resume_state=current.resume_state,
            target_resume_state=resume_state,
        )
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                """
                UPDATE runs
                SET state = ?, resume_state = ?, state_changed_at = ?, updated_at = ?
                WHERE run_id = ?
                """,
                (
                    target.value,
                    resume_state.value if resume_state else None,
                    now,
                    now,
                    run_id,
                ),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'run_state_changed', ?, ?, ?)
                """,
                (
                    current.workspace_id,
                    run_id,
                    _canonical_json(
                        {
                            "from": current.state.value,
                            "to": target.value,
                            "resume_state": resume_state.value if resume_state else None,
                        }
                    ),
                    now,
                ),
            )
        return self.get(run_id)

    def record_ledger_manifest(self, run_id: str, report: dict[str, Any]) -> Run:
        current = self.get(run_id)
        manifest = {
            **current.manifest,
            "ledger_hash": report["ledger_hash"],
            "accounting": {
                "balanced": report["balanced"],
                "unclassified_total": report["unclassified_total"],
                "sources": [
                    {
                        "source_id": source["source_id"],
                        "inventory": source["inventory"],
                        "outcomes": source["outcomes"],
                    }
                    for source in report["sources"]
                ],
            },
        }
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE runs SET manifest_json = ?, updated_at = ? WHERE run_id = ?",
                (_canonical_json(manifest), now, run_id),
            )
        return self.get(run_id)

    @staticmethod
    def _from_row(row) -> Run:
        return Run(
            run_id=row["run_id"],
            workspace_id=row["workspace_id"],
            state=row["state"],
            resume_state=row["resume_state"],
            config_hash=row["config_hash"],
            config=json.loads(row["config_json"]),
            manifest=json.loads(row["manifest_json"]),
            state_changed_at=row["state_changed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
