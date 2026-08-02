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
                "SELECT * FROM sources WHERE workspace_id = ? ORDER BY created_at, source_id",
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
        observed_claims: list[ObservedAssetClaim],
        outcome: AssessmentOutcome,
        reason_codes: list[str],
    ) -> tuple[Source, bool]:
        existing = self.find_by_hash(workspace_id, sha256)
        if existing is not None:
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
        status = (
            SourceState.ACCEPTED
            if outcome is AssessmentOutcome.COMPATIBLE
            else SourceState.QUARANTINED
        )
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
                    json.dumps([claim.model_dump(mode="json") for claim in observed_claims], sort_keys=True),
                    outcome.value,
                    json.dumps(reason_codes, sort_keys=True),
                    now,
                ),
            )
            connection.execute(
                "UPDATE sources SET status = ?, active_assessment_id = ? WHERE source_id = ?",
                (status.value, assessment_id, source_id),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'source_assessed', ?, ?, ?)
                """,
                (
                    workspace_id,
                    source_id,
                    json.dumps({"assessment_id": assessment_id, "outcome": outcome.value}, sort_keys=True),
                    now,
                ),
            )
        return self.get(source_id), False

    def resolve_uncertain(
        self,
        source_id: str,
        *,
        action: str,
        reason: str,
        observation_basis: str,
        operator: str,
        evidence_seen: list[str],
    ) -> Source:
        source = self.get(source_id)
        active = source.active_assessment
        if active is None or active.outcome is not AssessmentOutcome.UNCERTAIN:
            raise SourceAssessmentError("Only an uncertain active assessment can be resolved by the operator")
        if action not in {"confirm", "exclude"}:
            raise SourceAssessmentError("Action must be confirm or exclude")
        now = utc_now()
        assertion_id = new_id("assertion")
        decision_id = new_id("decision")
        assessment_id = new_id("assessment")
        new_outcome = AssessmentOutcome.COMPATIBLE if action == "confirm" else AssessmentOutcome.UNCERTAIN
        new_status = SourceState.ACCEPTED if action == "confirm" else SourceState.EXCLUDED
        reason_code = "OPERATOR_CONFIRMED_APPLICABILITY" if action == "confirm" else "OPERATOR_EXCLUDED_SOURCE"
        with self.database.transaction() as connection:
            for entity_id, entity_type in (
                (assertion_id, "assertion"),
                (decision_id, "decision"),
                (assessment_id, "assessment"),
            ):
                connection.execute(
                    "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, ?, ?)",
                    (entity_id, entity_type, now),
                )
            connection.execute(
                """
                INSERT INTO source_assessment_assertions(
                    assertion_id, workspace_id, assessment_id, asserted_value_json, reason,
                    evidence_seen_json, observation_basis, decision_id, operator, supersedes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
                """,
                (
                    assertion_id,
                    source.workspace_id,
                    active.assessment_id,
                    json.dumps({"action": action}, sort_keys=True),
                    reason,
                    json.dumps(evidence_seen, sort_keys=True),
                    observation_basis,
                    decision_id,
                    operator,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO source_assessments(
                    assessment_id, source_id, workspace_id, asset_identity_version,
                    observed_claims_json, outcome, reason_codes_json, decided_by_kind,
                    decision_id, operator_assertion_id, supersedes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'operator_assertion', ?, ?, ?, ?)
                """,
                (
                    assessment_id,
                    source.source_id,
                    source.workspace_id,
                    active.asset_identity_version,
                    json.dumps([claim.model_dump(mode="json") for claim in active.observed_claims], sort_keys=True),
                    new_outcome.value,
                    json.dumps([reason_code]),
                    decision_id,
                    assertion_id,
                    active.assessment_id,
                    now,
                ),
            )
            if action == "confirm":
                connection.execute(
                    "UPDATE sources SET status = 'assessing' WHERE source_id = ?",
                    (source.source_id,),
                )
            connection.execute(
                "UPDATE sources SET status = ?, active_assessment_id = ? WHERE source_id = ?",
                (new_status.value, assessment_id, source.source_id),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'source_assessment_resolved', ?, ?, ?)
                """,
                (
                    source.workspace_id,
                    source.source_id,
                    json.dumps(
                        {
                            "assessment_id": assessment_id,
                            "assertion_id": assertion_id,
                            "action": action,
                        },
                        sort_keys=True,
                    ),
                    now,
                ),
            )
        return self.get(source_id)

    def reopen_resolution(self, source_id: str) -> Source:
        source = self.get(source_id)
        active = source.active_assessment
        if active is None or active.decided_by.kind != "operator_assertion" or active.supersedes is None:
            raise SourceAssessmentError("The active assessment has no operator resolution to reopen")
        with self.database.read() as connection:
            previous_row = connection.execute(
                "SELECT * FROM source_assessments WHERE assessment_id = ?",
                (active.supersedes,),
            ).fetchone()
            if previous_row is None:
                raise SourceAssessmentError("Superseded assessment is missing")
            previous = self._assessment_from_row(previous_row)
        now = utc_now()
        assessment_id = new_id("assessment")
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'assessment', ?)",
                (assessment_id, now),
            )
            connection.execute(
                """
                INSERT INTO source_assessments(
                    assessment_id, source_id, workspace_id, asset_identity_version,
                    observed_claims_json, outcome, reason_codes_json, decided_by_kind,
                    decision_id, operator_assertion_id, supersedes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'reopened', NULL, NULL, ?, ?)
                """,
                (
                    assessment_id,
                    source.source_id,
                    source.workspace_id,
                    previous.asset_identity_version,
                    json.dumps([claim.model_dump(mode="json") for claim in previous.observed_claims], sort_keys=True),
                    previous.outcome.value,
                    json.dumps(["OPERATOR_RESOLUTION_REOPENED"]),
                    active.assessment_id,
                    now,
                ),
            )
            status = (
                SourceState.ACCEPTED
                if previous.outcome is AssessmentOutcome.COMPATIBLE
                else SourceState.QUARANTINED
            )
            if source.status is SourceState.ACCEPTED:
                connection.execute(
                    "UPDATE sources SET status = 'assessing' WHERE source_id = ?",
                    (source.source_id,),
                )
            connection.execute(
                "UPDATE sources SET status = ?, active_assessment_id = ? WHERE source_id = ?",
                (status.value, assessment_id, source.source_id),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'source_assessment_reopened', ?, ?, ?)
                """,
                (
                    source.workspace_id,
                    source.source_id,
                    json.dumps({"assessment_id": assessment_id, "reopened": active.assessment_id}),
                    now,
                ),
            )
        return self.get(source_id)

    def raw_reference(self, source_id: str) -> str:
        source = self.get(source_id)
        if source.raw_relpath is None:
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
