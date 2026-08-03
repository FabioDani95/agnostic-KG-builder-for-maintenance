"""Transactional Source registry and append-only assessment repository."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from backend.domain.ids import new_id, utc_now
from backend.domain.sources import (
    AssessmentDecider,
    AssessmentOutcome,
    ObservedAssetClaim,
    Source,
    SourceAssetAssessment,
    SourceAuthority,
    SourceKind,
    SourceState,
)
from backend.storage.database import Database, get_database


class SourceNotFoundError(LookupError):
    pass


class SourceAssessmentError(RuntimeError):
    pass


class SourceRepository:
    def __init__(self, database: Database | None = None):
        self.database = database or get_database()

    def list_for_workspace(self, workspace_id: str) -> list[Source]:
        with self.database.read() as connection:
            rows = connection.execute(
                """
                SELECT * FROM sources
                WHERE workspace_id = ? AND status != 'excluded'
                ORDER BY created_at, source_id
                """,
                (workspace_id,),
            ).fetchall()
            return [self._source_from_row(connection, row) for row in rows]

    def get(self, source_id: str) -> Source:
        with self.database.read() as connection:
            row = connection.execute(
                "SELECT * FROM sources WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            if row is None:
                raise SourceNotFoundError(source_id)
            return self._source_from_row(connection, row)

    def find_by_hash(self, workspace_id: str, sha256: str) -> Source | None:
        with self.database.read() as connection:
            row = connection.execute(
                "SELECT * FROM sources WHERE workspace_id = ? AND sha256 = ?",
                (workspace_id, sha256),
            ).fetchone()
            return self._source_from_row(connection, row) if row is not None else None

    def register(
        self,
        *,
        workspace_id: str,
        source_kind: SourceKind,
        authority: SourceAuthority,
        file_name: str,
        media_type: str,
        size_bytes: int,
        sha256: str,
        raw_relpath: str,
    ) -> tuple[Source, bool]:
        existing = self.find_by_hash(workspace_id, sha256)
        if existing is not None:
            if existing.status is SourceState.EXCLUDED:
                now = utc_now()
                with self.database.transaction() as connection:
                    connection.execute(
                        "UPDATE sources SET status = 'accepted' WHERE source_id = ?",
                        (existing.source_id,),
                    )
                    connection.execute(
                        """
                        INSERT INTO audit_events(
                            workspace_id, event_kind, subject_id, payload_json, created_at
                        ) VALUES (?, 'source_restored', ?, ?, ?)
                        """,
                        (
                            workspace_id,
                            existing.source_id,
                            json.dumps({"sha256": sha256, "file_name": file_name}, sort_keys=True),
                            now,
                        ),
                    )
                return self.get(existing.source_id), False
            self._append_audit(
                workspace_id,
                "source_duplicate_detected",
                existing.source_id,
                {"sha256": sha256, "file_name": file_name},
            )
            return existing, True

        now = utc_now()
        source_id = new_id("source")
        assessment_id = new_id("assessment")
        try:
            with self.database.transaction() as connection:
                for entity_id, entity_type in (
                    (source_id, "source"),
                    (assessment_id, "assessment"),
                ):
                    connection.execute(
                        "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, ?, ?)",
                        (entity_id, entity_type, now),
                    )
                workspace = connection.execute(
                    "SELECT asset_identity_version FROM workspaces WHERE workspace_id = ?",
                    (workspace_id,),
                ).fetchone()
                if workspace is None:
                    raise SourceAssessmentError("Workspace does not exist")
                connection.execute(
                    """
                    INSERT INTO sources(
                        source_id, workspace_id, source_kind, authority, file_name, media_type,
                        size_bytes, sha256, raw_relpath, language_hints_json, status,
                        active_assessment_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '[]', 'uploaded', NULL, ?)
                    """,
                    (
                        source_id,
                        workspace_id,
                        source_kind.value,
                        authority.value,
                        file_name,
                        media_type,
                        size_bytes,
                        sha256,
                        raw_relpath,
                        now,
                    ),
                )
                connection.execute(
                    "UPDATE sources SET status = 'assessing' WHERE source_id = ?",
                    (source_id,),
                )
                connection.execute(
                    """
                    INSERT INTO source_assessments(
                        assessment_id, source_id, workspace_id, asset_identity_version,
                        observed_claims_json, outcome, reason_codes_json, decided_by_kind,
                        decision_id, operator_assertion_id, supersedes, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'deterministic_rule', NULL, NULL, NULL, ?)
                    """,
                    (
                        assessment_id,
                        source_id,
                        workspace_id,
                        workspace["asset_identity_version"],
                        "[]",
                        AssessmentOutcome.COMPATIBLE.value,
                        json.dumps(["OPERATOR_SELECTED_SUPPORTED_FILE"]),
                        now,
                    ),
                )
                connection.execute(
                    "UPDATE sources SET status = ?, active_assessment_id = ? WHERE source_id = ?",
                    (SourceState.ACCEPTED.value, assessment_id, source_id),
                )
                connection.execute(
                    """
                    INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                    VALUES (?, 'source_assessed', ?, ?, ?)
                    """,
                    (
                        workspace_id,
                        source_id,
                        json.dumps(
                            {
                                "assessment_id": assessment_id,
                                "outcome": AssessmentOutcome.COMPATIBLE.value,
                                "accepted_by": "operator_upload",
                            },
                            sort_keys=True,
                        ),
                        now,
                    ),
                )
        except sqlite3.IntegrityError:
            concurrent = self.find_by_hash(workspace_id, sha256)
            if concurrent is None:
                raise
            self._append_audit(
                workspace_id,
                "source_duplicate_detected",
                concurrent.source_id,
                {"sha256": sha256, "file_name": file_name},
            )
            return concurrent, True
        return self.get(source_id), False

    def remove(self, source_id: str) -> None:
        source = self.get(source_id)
        if source.source_kind is SourceKind.OPERATOR_INPUT:
            raise SourceNotFoundError(source_id)
        if source.status is SourceState.EXCLUDED:
            return
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE sources SET status = 'excluded' WHERE source_id = ?",
                (source_id,),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'source_removed', ?, ?, ?)
                """,
                (
                    source.workspace_id,
                    source_id,
                    json.dumps({"file_name": source.file_name}, sort_keys=True),
                    now,
                ),
            )

    def raw_reference(self, source_id: str) -> str:
        source = self.get(source_id)
        if source.status is SourceState.EXCLUDED or source.raw_relpath is None:
            raise SourceNotFoundError(source_id)
        return source.raw_relpath

    def _append_audit(self, workspace_id: str, kind: str, subject_id: str, payload: dict[str, Any]) -> None:
        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (workspace_id, kind, subject_id, json.dumps(payload, sort_keys=True), utc_now()),
            )

    def _source_from_row(self, connection: sqlite3.Connection, row) -> Source:
        assessment = None
        if row["active_assessment_id"]:
            assessment_row = connection.execute(
                "SELECT * FROM source_assessments WHERE assessment_id = ?",
                (row["active_assessment_id"],),
            ).fetchone()
            if assessment_row is not None:
                assessment = self._assessment_from_row(assessment_row)
        return Source(
            source_id=row["source_id"],
            workspace_id=row["workspace_id"],
            source_kind=row["source_kind"],
            authority=row["authority"],
            file_name=row["file_name"],
            media_type=row["media_type"],
            size_bytes=row["size_bytes"],
            sha256=row["sha256"],
            language_hints=json.loads(row["language_hints_json"]),
            status=row["status"],
            asset_assessment_id=row["active_assessment_id"],
            raw_relpath=row["raw_relpath"],
            created_at=row["created_at"],
            active_assessment=assessment,
        )

    @staticmethod
    def _assessment_from_row(row) -> SourceAssetAssessment:
        return SourceAssetAssessment(
            assessment_id=row["assessment_id"],
            source_id=row["source_id"],
            workspace_id=row["workspace_id"],
            asset_identity_version=row["asset_identity_version"],
            observed_claims=[
                ObservedAssetClaim.model_validate(item)
                for item in json.loads(row["observed_claims_json"])
            ],
            outcome=row["outcome"],
            reason_codes=json.loads(row["reason_codes_json"]),
            decided_by=AssessmentDecider(
                kind=row["decided_by_kind"],
                decision_id=row["decision_id"],
                operator_assertion_id=row["operator_assertion_id"],
            ),
            supersedes=row["supersedes"],
            created_at=row["created_at"],
        )
