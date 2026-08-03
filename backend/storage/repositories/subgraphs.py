"""Immutable persistence for source-scoped graph revisions and decisions."""

from __future__ import annotations

import json
from typing import Any

from backend.domain.ids import new_id, utc_now
from backend.domain.subgraphs import SourceSubgraphRevision, SourceSubgraphStatus
from backend.storage.database import Database, get_database


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class SourceSubgraphRepository:
    def __init__(self, database: Database | None = None):
        self.database = database or get_database()

    def find_matching(
        self,
        *,
        source_id: str,
        preparation_fingerprint: str,
        input_config_hash: str,
    ) -> SourceSubgraphRevision | None:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT r.*, d.decision_id, d.action, d.note
                FROM source_subgraph_revisions r
                LEFT JOIN source_subgraph_decisions d ON d.decision_id = (
                    SELECT decision_id FROM source_subgraph_decisions
                    WHERE source_subgraph_revision_id = r.source_subgraph_revision_id
                    ORDER BY created_at DESC, decision_id DESC LIMIT 1
                )
                WHERE r.source_id = ? AND r.preparation_fingerprint = ?
                  AND r.input_config_hash = ?
                """,
                (source_id, preparation_fingerprint, input_config_hash),
            ).fetchone()
        return self._revision(row) if row is not None else None

    def get(self, revision_id: str) -> SourceSubgraphRevision:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT r.*, d.decision_id, d.action, d.note
                FROM source_subgraph_revisions r
                LEFT JOIN source_subgraph_decisions d ON d.decision_id = (
                    SELECT decision_id FROM source_subgraph_decisions
                    WHERE source_subgraph_revision_id = r.source_subgraph_revision_id
                    ORDER BY created_at DESC, decision_id DESC LIMIT 1
                )
                WHERE r.source_subgraph_revision_id = ?
                """,
                (revision_id,),
            ).fetchone()
        if row is None:
            raise LookupError(revision_id)
        return self._revision(row)

    def current_for_workspace(self, workspace_id: str) -> dict[str, SourceSubgraphRevision]:
        with self.database.read() as connection:
            rows = connection.execute(
                """
                SELECT r.*, d.decision_id, d.action, d.note
                FROM source_subgraph_revisions r
                LEFT JOIN source_subgraph_decisions d ON d.decision_id = (
                    SELECT decision_id FROM source_subgraph_decisions
                    WHERE source_subgraph_revision_id = r.source_subgraph_revision_id
                    ORDER BY created_at DESC, decision_id DESC LIMIT 1
                )
                WHERE r.workspace_id = ? AND r.source_subgraph_revision_id = (
                    SELECT r2.source_subgraph_revision_id FROM source_subgraph_revisions r2
                    WHERE r2.source_id = r.source_id
                    ORDER BY r2.created_at DESC, r2.source_subgraph_revision_id DESC LIMIT 1
                )
                ORDER BY r.created_at, r.source_subgraph_revision_id
                """,
                (workspace_id,),
            ).fetchall()
        return {row["source_id"]: self._revision(row) for row in rows}

    def create(self, revision: SourceSubgraphRevision) -> SourceSubgraphRevision:
        payload = revision.model_dump(mode="json", exclude={"status", "approval_decision_id", "decision_note"})
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'source_subgraph', ?)",
                (revision.source_subgraph_revision_id, revision.created_at),
            )
            connection.execute(
                """
                INSERT INTO source_subgraph_revisions(
                    source_subgraph_revision_id, workspace_id, source_id,
                    preparation_fingerprint, input_config_hash, payload_json,
                    supersedes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    revision.source_subgraph_revision_id,
                    revision.workspace_id,
                    revision.source_id,
                    revision.preparation_fingerprint,
                    revision.input_config_hash,
                    _json(payload),
                    revision.supersedes,
                    revision.created_at,
                ),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'source_subgraph_generated', ?, ?, ?)
                """,
                (
                    revision.workspace_id,
                    revision.source_subgraph_revision_id,
                    _json({
                        "source_id": revision.source_id,
                        "node_count": len(revision.nodes),
                        "relation_count": len(revision.relations),
                        "evidence_count": len(revision.evidence_ids),
                    }),
                    revision.created_at,
                ),
            )
        return self.get(revision.source_subgraph_revision_id)

    def decide(self, revision_id: str, *, action: str, note: str | None) -> SourceSubgraphRevision:
        revision = self.get(revision_id)
        normalized_note = str(note or "").strip() or None
        if action == "reject" and not normalized_note:
            raise ValueError("Indica brevemente cosa deve essere corretto")
        if action == "approve" and not revision.approval_eligible:
            if revision.knowledge_gaps:
                raise ValueError(
                    "Il sottografo contiene lacune dichiarate: completa o escludi esplicitamente i dati prima dell'approvazione"
                )
            raise ValueError(
                "Il sottografo non supera la validazione ontologica e di provenienza richiesta per l'approvazione"
            )
        current_action = revision.status.value if revision.status is not SourceSubgraphStatus.REVIEWING else None
        target = "approved" if action == "approve" else "rejected"
        if current_action == target:
            return revision
        decision_id = new_id("decision")
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'decision', ?)",
                (decision_id, now),
            )
            connection.execute(
                """
                INSERT INTO source_subgraph_decisions(
                    decision_id, source_subgraph_revision_id, workspace_id, action, note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (decision_id, revision_id, revision.workspace_id, action, normalized_note, now),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'source_subgraph_decided', ?, ?, ?)
                """,
                (
                    revision.workspace_id,
                    revision_id,
                    _json({"decision_id": decision_id, "action": action, "note": normalized_note}),
                    now,
                ),
            )
        return self.get(revision_id)

    @staticmethod
    def _revision(row) -> SourceSubgraphRevision:
        payload = json.loads(row["payload_json"])
        action = row["action"]
        status = {
            "approve": SourceSubgraphStatus.APPROVED,
            "reject": SourceSubgraphStatus.REJECTED,
        }.get(action, SourceSubgraphStatus.REVIEWING)
        return SourceSubgraphRevision.model_validate({
            **payload,
            "status": status,
            "approval_decision_id": row["decision_id"],
            "decision_note": row["note"],
        })
