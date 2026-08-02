"""Single-workspace repository with one-Asset enforcement."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from backend.domain.ids import new_id, utc_now
from backend.domain.workspace import (
    AssertionSubject,
    Asset,
    AssetIdentifier,
    OperatorAssertion,
    Workspace,
    WorkspaceState,
)
from backend.services.ontology_schema_service import ontology_contract
from backend.storage.database import Database, get_database


class WorkspaceConflictError(RuntimeError):
    """Raised when a second machine would be persisted."""


def _claim_id(connection: sqlite3.Connection, entity_id: str, entity_type: str, now: str) -> None:
    try:
        connection.execute(
            "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, ?, ?)",
            (entity_id, entity_type, now),
        )
    except sqlite3.IntegrityError as exc:
        raise WorkspaceConflictError(f"Identifier already belongs to another entity: {entity_id}") from exc


class WorkspaceRepository:
    def __init__(self, database: Database | None = None):
        self.database = database or get_database()

    def get(self) -> Workspace | None:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT w.*, a.asset_id, a.name, a.description, a.brand, a.model, a.asset_type
                FROM workspaces w
                JOIN assets a ON a.workspace_id = w.workspace_id
                ORDER BY w.created_at
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None
            identifiers = [
                AssetIdentifier.model_validate(dict(item))
                for item in connection.execute(
                    """
                    SELECT namespace, value, kind
                    FROM asset_identifiers
                    WHERE workspace_id = ?
                    ORDER BY identifier_id
                    """,
                    (row["workspace_id"],),
                )
            ]
            status = self._derive_state(connection, row["workspace_id"])
        return self._workspace_from_row(row, identifiers, status)

    def create_confirmed(
        self,
        *,
        asset_values: dict[str, Any],
        identifiers: list[AssetIdentifier],
        assertion_reason: str,
        observation_basis: str,
        operator: str,
    ) -> tuple[Workspace, OperatorAssertion, bool]:
        existing = self.get()
        if existing is not None:
            requested = {
                key: (str(asset_values.get(key) or "").strip() or None)
                for key in ("name", "description", "brand", "model", "asset_type")
            }
            current = existing.asset.model_dump(exclude={"asset_id"})
            if requested == current:
                assertion = self.latest_asset_assertion(existing.workspace_id)
                if assertion is None:
                    raise RuntimeError("Confirmed workspace is missing its onboarding assertion")
                return existing, assertion, True
            raise WorkspaceConflictError("This MVP already contains a different confirmed Asset")

        now = utc_now()
        workspace_id = new_id("workspace")
        asset_id = new_id("asset")
        assertion_id = new_id("assertion")
        decision_id = new_id("decision")
        asset = Asset(asset_id=asset_id, **asset_values)
        contract = ontology_contract()
        asserted_value = asset.model_dump(exclude_none=True)

        with self.database.transaction() as connection:
            already = connection.execute("SELECT workspace_id FROM workspaces LIMIT 1").fetchone()
            if already is not None:
                raise WorkspaceConflictError("This MVP already contains a confirmed Asset")
            for entity_id, entity_type in (
                (workspace_id, "workspace"),
                (asset_id, "asset"),
                (assertion_id, "assertion"),
                (decision_id, "decision"),
            ):
                _claim_id(connection, entity_id, entity_type, now)
            connection.execute(
                """
                INSERT INTO workspaces(
                    workspace_id, asset_identity_version, ontology_version, ontology_sha256,
                    confirmed_at, created_at, updated_at
                ) VALUES (?, 1, ?, ?, ?, ?, ?)
                """,
                (workspace_id, contract.version, contract.sha256, now, now, now),
            )
            connection.execute(
                """
                INSERT INTO assets(
                    asset_id, workspace_id, name, description, brand, model, asset_type, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset.asset_id,
                    workspace_id,
                    asset.name,
                    asset.description,
                    asset.brand,
                    asset.model,
                    asset.asset_type,
                    now,
                ),
            )
            for identifier in identifiers:
                connection.execute(
                    """
                    INSERT INTO asset_identifiers(workspace_id, namespace, value, kind, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (workspace_id, identifier.namespace, identifier.value, identifier.kind, now),
                )
            connection.execute(
                """
                INSERT INTO operator_assertions(
                    assertion_id, workspace_id, subject_kind, subject_id, subject_version,
                    field_path, asserted_value_json, reason, evidence_ids_seen_json,
                    observation_basis, decision_id, operator, supersedes, created_at
                ) VALUES (?, ?, 'asset_identity', ?, 1, 'Asset', ?, ?, '[]', ?, ?, ?, NULL, ?)
                """,
                (
                    assertion_id,
                    workspace_id,
                    asset_id,
                    json.dumps(asserted_value, sort_keys=True, ensure_ascii=False),
                    assertion_reason,
                    observation_basis,
                    decision_id,
                    operator,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'asset_identity_confirmed', ?, ?, ?)
                """,
                (
                    workspace_id,
                    asset_id,
                    json.dumps(
                        {"assertion_id": assertion_id, "decision_id": decision_id},
                        sort_keys=True,
                    ),
                    now,
                ),
            )

        workspace = Workspace(
            workspace_id=workspace_id,
            status=WorkspaceState.SOURCES_REQUIRED,
            asset=asset,
            asset_identity_version=1,
            ontology_version=contract.version,
            ontology_sha256=contract.sha256,
            confirmed_at=now,
            created_at=now,
            updated_at=now,
            identifiers=identifiers,
        )
        assertion = OperatorAssertion(
            assertion_id=assertion_id,
            workspace_id=workspace_id,
            subject_ref=AssertionSubject(
                kind="asset_identity",
                asset_id=asset_id,
                asset_identity_version=1,
            ),
            field_path="Asset",
            asserted_value=asserted_value,
            reason=assertion_reason,
            evidence_ids_seen=[],
            observation_basis=observation_basis,
            decision_id=decision_id,
            operator=operator,
            supersedes=None,
            created_at=now,
        )
        return workspace, assertion, False

    def latest_asset_assertion(self, workspace_id: str) -> OperatorAssertion | None:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT * FROM operator_assertions
                WHERE workspace_id = ? AND subject_kind = 'asset_identity'
                ORDER BY created_at DESC, assertion_id DESC
                LIMIT 1
                """,
                (workspace_id,),
            ).fetchone()
        if row is None:
            return None
        return OperatorAssertion(
            assertion_id=row["assertion_id"],
            workspace_id=row["workspace_id"],
            subject_ref=AssertionSubject(
                kind="asset_identity",
                asset_id=row["subject_id"],
                asset_identity_version=row["subject_version"],
            ),
            field_path=row["field_path"],
            asserted_value=json.loads(row["asserted_value_json"]),
            reason=row["reason"],
            evidence_ids_seen=json.loads(row["evidence_ids_seen_json"]),
            observation_basis=row["observation_basis"],
            decision_id=row["decision_id"],
            operator=row["operator"],
            supersedes=row["supersedes"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _derive_state(connection: sqlite3.Connection, workspace_id: str) -> WorkspaceState:
        run = connection.execute(
            """
            SELECT state, resume_state
            FROM runs
            WHERE workspace_id = ?
              AND state NOT IN ('published', 'cancelled', 'superseded')
            ORDER BY created_at DESC, run_id DESC
            LIMIT 1
            """,
            (workspace_id,),
        ).fetchone()
        if run is not None:
            run_state = run["state"]
            if run_state in {"created", "preflight", "ready"}:
                return WorkspaceState.READY
            if run_state == "processing":
                return WorkspaceState.PROCESSING
            if run_state == "pausing":
                resume_state = run["resume_state"]
                if resume_state == "processing":
                    return WorkspaceState.PROCESSING
                if resume_state == "awaiting_review":
                    return WorkspaceState.AWAITING_REVIEW
                if resume_state == "ready_to_publish":
                    return WorkspaceState.READY_TO_PUBLISH
                return WorkspaceState.READY
            run_mapping = {
                "paused": WorkspaceState.PAUSED,
                "failed_resumable": WorkspaceState.FAILED_RESUMABLE,
                "failed_terminal": WorkspaceState.FAILED_TERMINAL,
                "awaiting_review": WorkspaceState.AWAITING_REVIEW,
                "ready_to_publish": WorkspaceState.READY_TO_PUBLISH,
            }
            if run_state in run_mapping:
                return run_mapping[run_state]
        accepted = connection.execute(
            """
            SELECT source_id
            FROM sources
            WHERE workspace_id = ? AND source_kind != 'operator_input' AND status = 'accepted'
            """,
            (workspace_id,),
        ).fetchall()
        if not accepted:
            return WorkspaceState.SOURCES_REQUIRED
        not_ready = connection.execute(
            """
            SELECT COUNT(*)
            FROM sources s
            LEFT JOIN preparations p ON p.source_id = s.source_id
            WHERE s.workspace_id = ? AND s.source_kind != 'operator_input'
              AND s.status = 'accepted' AND COALESCE(p.state, 'not_started') != 'ready'
            """,
            (workspace_id,),
        ).fetchone()[0]
        return WorkspaceState.PREPARATION_REQUIRED if not_ready else WorkspaceState.READY

    @staticmethod
    def _workspace_from_row(
        row,
        identifiers: list[AssetIdentifier],
        status: WorkspaceState,
    ) -> Workspace:
        return Workspace(
            workspace_id=row["workspace_id"],
            status=status,
            asset=Asset(
                asset_id=row["asset_id"],
                name=row["name"],
                description=row["description"],
                brand=row["brand"],
                model=row["model"],
                asset_type=row["asset_type"],
            ),
            asset_identity_version=row["asset_identity_version"],
            ontology_version=row["ontology_version"],
            ontology_sha256=row["ontology_sha256"],
            confirmed_at=row["confirmed_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            identifiers=identifiers,
        )
