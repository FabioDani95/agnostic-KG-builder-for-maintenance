"""Persistence for PDF scope revisions and immutable EvidenceUnit payloads."""

from __future__ import annotations

import hashlib
import json

from backend.domain.evidence import (
    EvidenceContent,
    EvidenceUnit,
    IngestionInfo,
    LanguageInfo,
    LanguageQualification,
    ProvenanceRef,
    RawReference,
    RecordRole,
)
from backend.domain.ids import new_id, utc_now
from backend.domain.locators import OperatorInputLocator, PdfLocator
from backend.domain.sources import SourceAuthority, SourceKind
from backend.domain.workspace import OperatorAssertion, Workspace
from backend.storage.database import Database, get_database


class EvidenceRepository:
    def __init__(self, database: Database | None = None):
        self.database = database or get_database()

    def current_scope(self, source_id: str) -> dict | None:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT s.*
                FROM pdf_scopes s
                JOIN preparations p ON p.active_config_id = s.scope_id
                WHERE p.source_id = ?
                """,
                (source_id,),
            ).fetchone()
        if row is None:
            return None
        return self._scope_from_row(row)

    @staticmethod
    def _scope_from_row(row) -> dict:
        return {
            "scope_id": row["scope_id"],
            "version": row["version"],
            "included_pages": json.loads(row["included_pages_json"]),
            "excluded_pages": json.loads(row["excluded_pages_json"]),
            "operator": row["operator"],
            "supersedes": row["supersedes"],
            "created_at": row["created_at"],
        }

    def ensure_asset_assertion_evidence(
        self,
        workspace: Workspace,
        assertion: OperatorAssertion,
    ) -> EvidenceUnit:
        token = hashlib.sha256(assertion.assertion_id.encode("utf-8")).hexdigest()[:28]
        source_id = f"src_{token}"
        assessment_id = f"srcassess_{token}"
        raw_unit_id = f"raw_{token}"
        evidence_id = f"ev_{token}"
        raw_hash = hashlib.sha256(
            json.dumps(
                assertion.asserted_value,
                sort_keys=True,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        locator = OperatorInputLocator(
            assertion_id=assertion.assertion_id,
            decision_id=assertion.decision_id,
            field_path=assertion.field_path,
        )
        locator_hash = hashlib.sha256(
            json.dumps(
                locator.model_dump(mode="json"),
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        evidence = EvidenceUnit(
            evidence_id=evidence_id,
            workspace_id=workspace.workspace_id,
            asset_id=workspace.asset.asset_id,
            source_id=source_id,
            source_kind=SourceKind.OPERATOR_INPUT,
            authority=SourceAuthority.NORMATIVE,
            locator=locator,
            provenance_refs=[
                ProvenanceRef(
                    role="primary",
                    raw_unit_id=raw_unit_id,
                    source_id=source_id,
                    locator=locator,
                    raw_hash=raw_hash,
                    structure_id="asset_identity",
                )
            ],
            language=LanguageInfo(
                detected="unknown",
                qualification=LanguageQualification.UNKNOWN,
            ),
            record_role=RecordRole.ASSET_MASTER,
            content=EvidenceContent(
                title=workspace.asset.name,
                observation=(
                    f"Operator attested Asset {workspace.asset.name}, "
                    f"brand {workspace.asset.brand}, model {workspace.asset.model}."
                ),
            ),
            attributes={"assertion_id": assertion.assertion_id},
            raw_ref=RawReference(
                source_id=source_id,
                raw_unit_id=raw_unit_id,
                locator_hash=locator_hash,
            ),
            ingestion=IngestionInfo(adapter_version="operator-input-v1"),
        )
        now = utc_now()
        with self.database.transaction() as connection:
            existing = connection.execute(
                "SELECT payload_json FROM evidence_units WHERE evidence_id = ?",
                (evidence_id,),
            ).fetchone()
            if existing is not None:
                return EvidenceUnit.model_validate_json(existing["payload_json"])
            for entity_id, entity_type in (
                (source_id, "source"),
                (assessment_id, "assessment"),
                (evidence_id, "evidence"),
            ):
                connection.execute(
                    "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, ?, ?)",
                    (entity_id, entity_type, now),
                )
            connection.execute(
                """
                INSERT INTO sources(
                    source_id, workspace_id, source_kind, authority, file_name, media_type,
                    size_bytes, sha256, raw_relpath, language_hints_json, status,
                    active_assessment_id, created_at
                ) VALUES (?, ?, 'operator_input', 'normative', NULL, NULL, NULL, NULL, NULL,
                          '[]', 'accepted', ?, ?)
                """,
                (source_id, workspace.workspace_id, assessment_id, now),
            )
            connection.execute(
                """
                INSERT INTO source_assessments(
                    assessment_id, source_id, workspace_id, asset_identity_version,
                    observed_claims_json, outcome, reason_codes_json, decided_by_kind,
                    decision_id, operator_assertion_id, supersedes, created_at
                ) VALUES (?, ?, ?, ?, '[]', 'compatible', '["OPERATOR_INPUT_WORKSPACE"]',
                          'operator_assertion', ?, ?, NULL, ?)
                """,
                (
                    assessment_id,
                    source_id,
                    workspace.workspace_id,
                    workspace.asset_identity_version,
                    assertion.decision_id,
                    assertion.assertion_id,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO evidence_units(
                    evidence_id, workspace_id, asset_id, source_id, raw_unit_id,
                    locator_hash, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evidence.evidence_id,
                    evidence.workspace_id,
                    evidence.asset_id,
                    evidence.source_id,
                    evidence.raw_ref.raw_unit_id,
                    evidence.raw_ref.locator_hash,
                    evidence.model_dump_json(),
                    now,
                ),
            )
        return evidence

    def save_scope(
        self,
        *,
        workspace_id: str,
        source_id: str,
        included_pages: list[int],
        excluded_pages: dict[str, str],
        operator: str,
        evidence_units: list[EvidenceUnit],
        reuse_matching: bool = False,
    ) -> dict:
        now = utc_now()
        with self.database.transaction() as connection:
            current_row = connection.execute(
                """
                SELECT s.*
                FROM pdf_scopes s
                JOIN preparations p ON p.active_config_id = s.scope_id
                WHERE p.source_id = ?
                """,
                (source_id,),
            ).fetchone()
            current = self._scope_from_row(current_row) if current_row is not None else None
            normalized_pages = sorted(included_pages)
            normalized_excluded = dict(sorted(excluded_pages.items()))
            if (
                reuse_matching
                and current is not None
                and current["included_pages"] == normalized_pages
                and current["excluded_pages"] == normalized_excluded
                and current["operator"] == operator
            ):
                return current

            version = int((current or {}).get("version", 0)) + 1
            scope_id = f"scope_{source_id}_{version:04d}"
            preparation = connection.execute(
                "SELECT * FROM preparations WHERE source_id = ?",
                (source_id,),
            ).fetchone()
            if preparation is None:
                preparation_id = new_id("preparation")
                connection.execute(
                    "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'preparation', ?)",
                    (preparation_id, now),
                )
                connection.execute(
                    """
                    INSERT INTO preparations(
                        preparation_id, source_id, workspace_id, state,
                        active_config_id, created_at, updated_at
                    ) VALUES (?, ?, ?, 'not_started', NULL, ?, ?)
                    """,
                    (preparation_id, source_id, workspace_id, now, now),
                )
                connection.execute(
                    """
                    UPDATE preparations
                    SET state = 'profiling_or_scoping', updated_at = ?
                    WHERE preparation_id = ?
                    """,
                    (now, preparation_id),
                )
            else:
                preparation_id = preparation["preparation_id"]
                if preparation["state"] == "ready":
                    connection.execute(
                        """
                        UPDATE preparations
                        SET state = 'invalidated', updated_at = ?
                        WHERE preparation_id = ?
                        """,
                        (now, preparation_id),
                    )
                    connection.execute(
                        """
                        UPDATE preparations
                        SET state = 'profiling_or_scoping', updated_at = ?
                        WHERE preparation_id = ?
                        """,
                        (now, preparation_id),
                    )
            connection.execute(
                """
                INSERT INTO pdf_scopes(
                    scope_id, preparation_id, source_id, version, included_pages_json,
                    excluded_pages_json, operator, supersedes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scope_id,
                    preparation_id,
                    source_id,
                    version,
                    json.dumps(normalized_pages),
                    json.dumps(normalized_excluded, sort_keys=True),
                    operator,
                    (current or {}).get("scope_id"),
                    now,
                ),
            )
            for evidence in evidence_units:
                exists = connection.execute(
                    "SELECT 1 FROM evidence_units WHERE evidence_id = ?",
                    (evidence.evidence_id,),
                ).fetchone()
                if exists is None:
                    connection.execute(
                        "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'evidence', ?)",
                        (evidence.evidence_id, now),
                    )
                    connection.execute(
                        """
                        INSERT INTO evidence_units(
                            evidence_id, workspace_id, asset_id, source_id, raw_unit_id,
                            locator_hash, payload_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            evidence.evidence_id,
                            evidence.workspace_id,
                            evidence.asset_id,
                            evidence.source_id,
                            evidence.raw_ref.raw_unit_id,
                            evidence.raw_ref.locator_hash,
                            evidence.model_dump_json(),
                            now,
                        ),
                    )
                connection.execute(
                    "INSERT INTO scope_evidence(scope_id, evidence_id) VALUES (?, ?)",
                    (scope_id, evidence.evidence_id),
                )
            connection.execute(
                """
                UPDATE preparations
                SET state = 'ready', active_config_id = ?, updated_at = ?
                WHERE preparation_id = ?
                """,
                (scope_id, now, preparation_id),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    workspace_id,
                    "pdf_all_pages_prepared" if reuse_matching else "pdf_scope_approved",
                    source_id,
                    json.dumps(
                        {
                            "scope_id": scope_id,
                            "version": version,
                            "included_pages": normalized_pages,
                            "excluded_pages": normalized_excluded,
                            "evidence_count": len(evidence_units),
                        },
                        sort_keys=True,
                    ),
                    now,
                ),
            )
        return self.current_scope(source_id)

    def list_evidence(self, *, workspace_id: str, source_id: str | None = None) -> list[EvidenceUnit]:
        query = """
            SELECT DISTINCT e.payload_json
            FROM evidence_units e
            JOIN sources s ON s.source_id = e.source_id
            LEFT JOIN preparations p ON p.source_id = e.source_id
            LEFT JOIN scope_evidence se
              ON se.scope_id = p.active_config_id AND se.evidence_id = e.evidence_id
            LEFT JOIN structured_evidence ste
              ON ste.profile_id = p.active_config_id AND ste.evidence_id = e.evidence_id
            WHERE e.workspace_id = ?
              AND (
                s.source_kind = 'operator_input'
                OR se.evidence_id IS NOT NULL
                OR ste.evidence_id IS NOT NULL
              )
        """
        values: list[str] = [workspace_id]
        if source_id is not None:
            query += " AND e.source_id = ?"
            values.append(source_id)
        query += " ORDER BY e.source_id, e.evidence_id"
        with self.database.read() as connection:
            rows = connection.execute(query, values).fetchall()
        evidence = [EvidenceUnit.model_validate_json(row["payload_json"]) for row in rows]

        def semantic_order(item: EvidenceUnit) -> tuple:
            locator = item.locator
            if not isinstance(locator, PdfLocator):
                return (item.source_id, 0, 0, 0, 0, item.evidence_id)
            if locator.block_index is not None:
                position = (0, locator.block_index, 0)
            elif locator.table_index is not None:
                position = (1, locator.table_index, locator.row_index or 0)
            elif locator.ocr_region_index is not None:
                position = (2, locator.ocr_region_index, 0)
            else:
                position = (3, 0, 0)
            return (item.source_id, locator.page, *position, item.evidence_id)

        return sorted(evidence, key=semantic_order)

    def save_structured_evidence(
        self,
        *,
        profile_id: str,
        evidence_units: list[EvidenceUnit],
    ) -> list[EvidenceUnit]:
        now = utc_now()
        with self.database.transaction() as connection:
            # Evidence units are immutable and stay on the record. What this
            # rewrites is which of them is the profile's current reading: after
            # a mapping correction the previous set must stop being served,
            # otherwise the graph would be built from two readings at once.
            connection.execute(
                "DELETE FROM structured_evidence WHERE profile_id = ?", (profile_id,)
            )
            for evidence in evidence_units:
                existing = connection.execute(
                    "SELECT payload_json FROM evidence_units WHERE evidence_id = ?",
                    (evidence.evidence_id,),
                ).fetchone()
                if existing is None:
                    connection.execute(
                        "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'evidence', ?)",
                        (evidence.evidence_id, now),
                    )
                    connection.execute(
                        """
                        INSERT INTO evidence_units(
                            evidence_id, workspace_id, asset_id, source_id, raw_unit_id,
                            locator_hash, payload_json, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            evidence.evidence_id,
                            evidence.workspace_id,
                            evidence.asset_id,
                            evidence.source_id,
                            evidence.raw_ref.raw_unit_id,
                            evidence.raw_ref.locator_hash,
                            evidence.model_dump_json(),
                            now,
                        ),
                    )
                connection.execute(
                    "INSERT OR IGNORE INTO structured_evidence(profile_id, evidence_id) VALUES (?, ?)",
                    (profile_id, evidence.evidence_id),
                )
        return evidence_units
