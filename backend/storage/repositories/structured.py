"""Persistence for G2 structured profiles, exceptions and explicit joins."""

from __future__ import annotations

import json
from typing import Any

from backend.adapters.structured import StructuredInspection
from backend.adapters.structured.common import ADAPTER_VERSION, ROLE_ALIAS_CONFIG_VERSION
from backend.domain.ids import new_id, utc_now
from backend.domain.sources import Source
from backend.domain.structured import (
    JoinSpecView,
    MappingProfilePayload,
    PreparationException,
    StructuredProfileView,
)
from backend.storage.database import Database, get_database


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


#: Roles that feed one field of the evidence record, and therefore one claim.
#: ``attribute`` and ``excluded`` are not among them: any number of columns may
#: be kept as plain data or left out.
_EXCLUSIVE_ROLES = frozenset({
    "observation", "cause", "action", "component",
    "error_code", "occurred_at", "outcome", "measurement",
})


def _one_column_per_role(columns: dict[str, Any]) -> dict[str, Any]:
    """Let at most one column hold each semantic role.

    Aliases can propose the same role for several columns — a free-text event
    description and a reported symptom both look like observations. Their texts
    would then be concatenated into a single evidence field, and the graph would
    show one element carrying two different statements glued together.

    The first column in file order keeps the role; the others start as plain
    attributes, so their content stays readable and searchable but produces no
    graph element. The operator can hand the role to a different column at any
    time (see :meth:`StructuredPreparationRepository.set_column_role`).
    """
    taken: set[str] = set()
    resolved: dict[str, Any] = {}
    for column, config in columns.items():
        payload = config.model_dump(mode="json")
        role = payload.get("role")
        if role in _EXCLUSIVE_ROLES:
            if role in taken:
                payload["role"] = "attribute"
                payload["included"] = True
            else:
                taken.add(role)
        resolved[column] = payload
    return resolved


class StructuredPreparationRepository:
    def __init__(self, database: Database | None = None):
        self.database = database or get_database()

    def current_profile(self, source_id: str) -> StructuredProfileView | None:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT p.*, s.file_name, s.source_kind
                FROM structured_profiles p
                JOIN sources s ON s.source_id = p.source_id
                JOIN preparations prep ON prep.active_config_id = p.profile_id
                WHERE p.source_id = ?
                """,
                (source_id,),
            ).fetchone()
        return self._profile(row) if row is not None else None

    def get_profile(self, profile_id: str) -> StructuredProfileView:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT p.*, s.file_name, s.source_kind
                FROM structured_profiles p
                JOIN sources s ON s.source_id = p.source_id
                WHERE p.profile_id = ?
                """,
                (profile_id,),
            ).fetchone()
        if row is None:
            raise LookupError(profile_id)
        return self._profile(row)

    def create_profile(self, source: Source, inspection: StructuredInspection) -> StructuredProfileView:
        existing = self.current_profile(source.source_id)
        if existing is not None and existing.fingerprint == inspection.fingerprint:
            return existing
        profile_id = new_id("mapping_profile")
        now = utc_now()
        actionable = [
            item
            for item in inspection.exceptions
            if item["severity"] == "blocking" or item["exception_kind"] == "hidden_sheet"
        ]
        blocking = any(item["severity"] == "blocking" for item in actionable)
        state = "needs_attention" if actionable else "analyzing"
        profile_payload = {
            "structures": [item.model_dump(mode="json") for item in inspection.structures],
            "adapter_version": ADAPTER_VERSION,
            "role_alias_config_version": ROLE_ALIAS_CONFIG_VERSION,
        }
        mapping_payload = {
            "structures": {
                structure_id: _one_column_per_role(columns)
                for structure_id, columns in inspection.mapping.items()
            }
        }
        summary = {
            "structure_count": len(inspection.structures),
            "record_count": len(inspection.records),
            "included_record_count": sum(1 for item in inspection.records if item.included),
            "isolated_record_count": sum(1 for item in inspection.records if not item.included),
            "blocking_count": sum(1 for item in inspection.exceptions if item["severity"] == "blocking"),
            "warning_count": sum(1 for item in inspection.exceptions if item["severity"] == "warning"),
            "has_blocking": blocking,
        }
        with self.database.transaction() as connection:
            version = int(
                connection.execute(
                    "SELECT COALESCE(MAX(version), 0) + 1 FROM structured_profiles WHERE source_id = ?",
                    (source.source_id,),
                ).fetchone()[0]
            )
            preparation = connection.execute(
                "SELECT * FROM preparations WHERE source_id = ?", (source.source_id,)
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
                    (preparation_id, source.source_id, source.workspace_id, now, now),
                )
                connection.execute(
                    "UPDATE preparations SET state = 'profiling_or_scoping', updated_at = ? WHERE preparation_id = ?",
                    (now, preparation_id),
                )
            else:
                preparation_id = preparation["preparation_id"]
                if preparation["state"] == "ready":
                    connection.execute(
                        "UPDATE preparations SET state = 'invalidated', updated_at = ? WHERE preparation_id = ?",
                        (now, preparation_id),
                    )
                    connection.execute(
                        "UPDATE preparations SET state = 'profiling_or_scoping', updated_at = ? WHERE preparation_id = ?",
                        (now, preparation_id),
                    )
            connection.execute(
                "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'mapping_profile', ?)",
                (profile_id, now),
            )
            connection.execute(
                """
                INSERT INTO structured_profiles(
                    profile_id, source_id, workspace_id, version, fingerprint, state,
                    profile_json, mapping_json, summary_json, run_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                """,
                (
                    profile_id,
                    source.source_id,
                    source.workspace_id,
                    version,
                    inspection.fingerprint,
                    state,
                    _json(profile_payload),
                    _json(mapping_payload),
                    _json(summary),
                    now,
                    now,
                ),
            )
            active_exception_created = False
            for item in inspection.exceptions:
                exception_id = new_id("preparation_exception")
                needs_operator = item["severity"] == "blocking" or item["exception_kind"] == "hidden_sheet"
                # The UI intentionally exposes one decision at a time.  Later
                # blocking decisions remain persisted and auditable, but cannot
                # be skipped or resolved out of order.
                if needs_operator:
                    exception_status = "queued" if active_exception_created else "open"
                    active_exception_created = True
                    automatic_resolution = None
                    resolved_at = None
                else:
                    exception_status = "acknowledged"
                    automatic_resolution = _json({"automatic_isolation": True})
                    resolved_at = now
                connection.execute(
                    "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'preparation_exception', ?)",
                    (exception_id, now),
                )
                connection.execute(
                    """
                    INSERT INTO structured_exceptions(
                        exception_id, profile_id, source_id, exception_kind, severity,
                        status, title, explanation, payload_json, resolution_json,
                        created_at, resolved_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        exception_id,
                        profile_id,
                        source.source_id,
                        item["exception_kind"],
                        item["severity"],
                        exception_status,
                        item["title"],
                        item["explanation"],
                        _json(item["payload"]),
                        automatic_resolution,
                        now,
                        resolved_at,
                    ),
                )
            if actionable:
                connection.execute(
                    "UPDATE preparations SET state = 'awaiting_operator', active_config_id = ?, updated_at = ? WHERE preparation_id = ?",
                    (profile_id, now, preparation_id),
                )
            else:
                connection.execute(
                    "UPDATE preparations SET active_config_id = ?, updated_at = ? WHERE preparation_id = ?",
                    (profile_id, now, preparation_id),
                )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'structured_profile_created', ?, ?, ?)
                """,
                (
                    source.workspace_id,
                    profile_id,
                    _json({"source_id": source.source_id, "fingerprint": inspection.fingerprint, "exception_count": len(inspection.exceptions)}),
                    now,
                ),
            )
        return self.get_profile(profile_id)

    def profiles_for_workspace(self, workspace_id: str) -> list[StructuredProfileView]:
        with self.database.read() as connection:
            rows = connection.execute(
                """
                SELECT p.*, s.file_name, s.source_kind
                FROM structured_profiles p
                JOIN sources s ON s.source_id = p.source_id
                JOIN preparations prep ON prep.active_config_id = p.profile_id
                WHERE p.workspace_id = ? AND s.status != 'excluded'
                ORDER BY s.created_at, p.version
                """,
                (workspace_id,),
            ).fetchall()
        return [self._profile(row) for row in rows]

    def exceptions_for_workspace(self, workspace_id: str, *, open_only: bool = False) -> list[PreparationException]:
        query = """
            SELECT e.*, s.file_name
            FROM structured_exceptions e
            JOIN structured_profiles p ON p.profile_id = e.profile_id
            JOIN sources s ON s.source_id = e.source_id
            JOIN preparations prep ON prep.active_config_id = p.profile_id
            WHERE p.workspace_id = ? AND s.status != 'excluded'
        """
        values: list[Any] = [workspace_id]
        if open_only:
            query += " AND e.status = 'open'"
        query += " ORDER BY CASE e.severity WHEN 'blocking' THEN 0 ELSE 1 END, e.created_at, e.exception_id"
        with self.database.read() as connection:
            rows = connection.execute(query, values).fetchall()
        return [self._exception(row) for row in rows]

    def get_exception(self, exception_id: str) -> PreparationException:
        with self.database.read() as connection:
            row = connection.execute(
                """
                SELECT e.*, s.file_name
                FROM structured_exceptions e
                JOIN sources s ON s.source_id = e.source_id
                WHERE e.exception_id = ?
                """,
                (exception_id,),
            ).fetchone()
        if row is None:
            raise LookupError(exception_id)
        return self._exception(row)

    def resolve_exception(self, exception_id: str, resolution: dict[str, Any]) -> PreparationException:
        now = utc_now()
        with self.database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM structured_exceptions WHERE exception_id = ?", (exception_id,)
            ).fetchone()
            if row is None:
                raise LookupError(exception_id)
            if row["status"] != "open":
                result = connection.execute(
                    """
                    SELECT e.*, s.file_name FROM structured_exceptions e
                    JOIN sources s ON s.source_id = e.source_id WHERE e.exception_id = ?
                    """,
                    (exception_id,),
                ).fetchone()
                return self._exception(result)
            profile = connection.execute(
                "SELECT * FROM structured_profiles WHERE profile_id = ?", (row["profile_id"],)
            ).fetchone()
            mapping = json.loads(profile["mapping_json"])
            payload = json.loads(row["payload_json"])
            released: list[str] = []
            if row["exception_kind"] == "mapping_ambiguous":
                role = resolution.get("role")
                if not role:
                    raise ValueError("Scegli il ruolo della colonna prima di continuare")
                if role not in payload.get("choices", []):
                    raise ValueError("Il ruolo scelto non è disponibile per questa colonna")
                columns = mapping["structures"][payload["structure_id"]]
                # Answering a question assigns a role exactly like editing the
                # mapping table does, so it must obey the same rule: a role
                # belongs to one column only.  The previous holder keeps its
                # content as a plain attribute — nothing is dropped, it simply
                # stops producing graph elements.  See `set_column_role`.
                if role not in {"attribute", "excluded"}:
                    for other, config in columns.items():
                        if other != payload["column"] and config.get("role") == role:
                            config["role"] = "attribute"
                            config["included"] = True
                            released.append(other)
                columns[payload["column"]]["role"] = role
                columns[payload["column"]]["included"] = role != "excluded"
            elif row["exception_kind"] == "hidden_sheet" and resolution.get("included") is not None:
                for config in mapping["structures"].get(payload["structure_id"], {}).values():
                    config["included"] = bool(resolution["included"])
            elif not resolution.get("acknowledge") and row["severity"] == "warning":
                raise ValueError("Conferma di aver preso visione dell'avviso")
            target_status = "acknowledged" if resolution.get("acknowledge") else "resolved"
            connection.execute(
                "UPDATE structured_exceptions SET status = ?, resolution_json = ?, resolved_at = ? WHERE exception_id = ?",
                (target_status, _json(resolution), now, exception_id),
            )
            connection.execute(
                "UPDATE structured_profiles SET mapping_json = ?, updated_at = ? WHERE profile_id = ?",
                (_json(mapping), now, row["profile_id"]),
            )
            # Promote exactly one queued decision after the current one is
            # resolved.  Keeping this in the same transaction makes retries
            # deterministic and prevents two UI prompts from becoming active.
            next_exception = connection.execute(
                """
                SELECT exception_id FROM structured_exceptions
                WHERE profile_id = ? AND status = 'queued'
                ORDER BY CASE severity WHEN 'blocking' THEN 0 ELSE 1 END, created_at, exception_id
                LIMIT 1
                """,
                (row["profile_id"],),
            ).fetchone()
            if next_exception is not None:
                connection.execute(
                    "UPDATE structured_exceptions SET status = 'open' WHERE exception_id = ?",
                    (next_exception["exception_id"],),
                )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'structured_exception_resolved', ?, ?, ?)
                """,
                (
                    profile["workspace_id"],
                    exception_id,
                    _json({**resolution, "released_columns": released}),
                    now,
                ),
            )
        with self.database.read() as connection:
            result = connection.execute(
                """
                SELECT e.*, s.file_name FROM structured_exceptions e
                JOIN sources s ON s.source_id = e.source_id WHERE e.exception_id = ?
                """,
                (exception_id,),
            ).fetchone()
        return self._exception(result)

    def set_column_role(
        self,
        profile_id: str,
        *,
        structure_id: str,
        column: str,
        role: str,
    ) -> str:
        """Reassign one column's semantic role.

        A semantic role is held by at most one column: two columns feeding the
        same role would have to be concatenated into a single evidence field,
        and the graph generator would then read one claim where the file states
        two.  Taking a role therefore releases it from whoever held it, and the
        previous holder keeps its content as a plain attribute — nothing is
        dropped, it simply stops producing graph elements.

        Editing the mapping invalidates the work downstream of it: the profile
        goes back to being re-read, and the operator's confirmation is withdrawn
        because it was given for a different reading of the file.  The source
        subgraph invalidates itself, since its identity includes the mapping
        fingerprint that just changed.
        """
        now = utc_now()
        with self.database.transaction() as connection:
            profile = connection.execute(
                "SELECT * FROM structured_profiles WHERE profile_id = ?", (profile_id,)
            ).fetchone()
            if profile is None:
                raise LookupError(profile_id)
            mapping = json.loads(profile["mapping_json"])
            structures = mapping.get("structures", {})
            if structure_id not in structures:
                raise ValueError("La tabella indicata non esiste in questa fonte")
            if column not in structures[structure_id]:
                raise ValueError("La colonna indicata non esiste in questa tabella")

            released: list[str] = []
            if role not in {"attribute", "excluded"}:
                for other, config in structures[structure_id].items():
                    if other != column and config.get("role") == role:
                        config["role"] = "attribute"
                        config["included"] = True
                        released.append(other)

            structures[structure_id][column]["role"] = role
            structures[structure_id][column]["included"] = role != "excluded"

            connection.execute(
                """
                UPDATE structured_profiles
                SET mapping_json = ?, state = 'analyzing', run_id = NULL, updated_at = ?
                WHERE profile_id = ?
                """,
                (_json(mapping), now, profile_id),
            )
            # The ledger already models this: a preparation that is no longer
            # valid passes through `invalidated` before being redone. Jumping
            # straight back to profiling would skip the record of why.
            preparation = connection.execute(
                "SELECT state FROM preparations WHERE source_id = ?", (profile["source_id"],)
            ).fetchone()
            if preparation is not None and preparation["state"] == "ready":
                connection.execute(
                    "UPDATE preparations SET state = 'invalidated', updated_at = ? WHERE source_id = ?",
                    (now, profile["source_id"]),
                )
            if preparation is not None and preparation["state"] != "profiling_or_scoping":
                # `active_config_id` keeps pointing at this profile: the mapping
                # is still the current one, it simply has to be applied again.
                # Clearing it would detach the profile and the next pass would
                # build a fresh one, throwing the correction away.
                connection.execute(
                    "UPDATE preparations SET state = 'profiling_or_scoping', updated_at = ? WHERE source_id = ?",
                    (now, profile["source_id"]),
                )
            # The confirmation applied to the previous reading of the file, so
            # it no longer holds. The ledger is append-only and must stay that
            # way: the confirmation is not erased, it is countered by a later
            # event, and both remain readable.
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'structured_source_confirmation_withdrawn', ?, ?, ?)
                """,
                (
                    profile["workspace_id"],
                    profile_id,
                    _json({"reason": "mapping_edited", "column": column, "role": role}),
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'structured_mapping_edited', ?, ?, ?)
                """,
                (
                    profile["workspace_id"],
                    profile_id,
                    _json({
                        "structure_id": structure_id,
                        "column": column,
                        "role": role,
                        "released_columns": released,
                    }),
                    now,
                ),
            )
            return profile["workspace_id"]

    def mark_prepared(self, profile_id: str, *, run_id: str, summary_updates: dict[str, Any]) -> None:
        profile = self.get_profile(profile_id)
        now = utc_now()
        summary = {**profile.summary, **summary_updates, "has_blocking": False, "blocking_count": 0}
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE structured_profiles SET state = 'prepared', run_id = ?, summary_json = ?, updated_at = ? WHERE profile_id = ?",
                (run_id, _json(summary), now, profile_id),
            )
            preparation = connection.execute(
                "SELECT * FROM preparations WHERE source_id = ?", (profile.source_id,)
            ).fetchone()
            if preparation["state"] == "awaiting_operator":
                connection.execute(
                    "UPDATE preparations SET state = 'profiling_or_scoping', updated_at = ? WHERE preparation_id = ?",
                    (now, preparation["preparation_id"]),
                )
            connection.execute(
                "UPDATE preparations SET state = 'ready', active_config_id = ?, updated_at = ? WHERE preparation_id = ?",
                (profile_id, now, preparation["preparation_id"]),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'structured_source_prepared', ?, ?, ?)
                """,
                (profile.workspace_id, profile.source_id, _json(summary_updates), now),
            )

    def set_needs_attention(self, profile_id: str) -> None:
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE structured_profiles SET state = 'needs_attention', updated_at = ? WHERE profile_id = ? AND state != 'prepared'",
                (now, profile_id),
            )
            row = connection.execute("SELECT source_id FROM structured_profiles WHERE profile_id = ?", (profile_id,)).fetchone()
            connection.execute(
                "UPDATE preparations SET state = 'awaiting_operator', updated_at = ? WHERE source_id = ? AND state = 'profiling_or_scoping'",
                (now, row["source_id"]),
            )

    def create_join(self, workspace_id: str, primary_profile_id: str, lookup_profile_id: str, spec: dict[str, Any], preview: dict[str, Any]) -> JoinSpecView:
        with self.database.read() as connection:
            existing = connection.execute(
                """
                SELECT * FROM join_specs
                WHERE workspace_id = ? AND primary_profile_id = ? AND lookup_profile_id = ?
                ORDER BY version DESC LIMIT 1
                """,
                (workspace_id, primary_profile_id, lookup_profile_id),
            ).fetchone()
        if existing is not None:
            return self._join(existing)
        join_id = new_id("join_spec")
        now = utc_now()
        with self.database.transaction() as connection:
            connection.execute(
                "INSERT INTO entity_ids(entity_id, entity_type, created_at) VALUES (?, 'join_spec', ?)",
                (join_id, now),
            )
            connection.execute(
                """
                INSERT INTO join_specs(
                    join_spec_id, workspace_id, version, primary_profile_id,
                    lookup_profile_id, status, spec_json, preview_json,
                    decision_json, created_at, decided_at
                ) VALUES (?, ?, 1, ?, ?, 'proposed', ?, ?, NULL, ?, NULL)
                """,
                (join_id, workspace_id, primary_profile_id, lookup_profile_id, _json(spec), _json(preview), now),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'join_proposed', ?, ?, ?)
                """,
                (workspace_id, join_id, _json({"spec": spec, "preview": preview}), now),
            )
        self.set_needs_attention(primary_profile_id)
        return self.get_join(join_id)

    def get_join(self, join_id: str) -> JoinSpecView:
        with self.database.read() as connection:
            row = connection.execute("SELECT * FROM join_specs WHERE join_spec_id = ?", (join_id,)).fetchone()
        if row is None:
            raise LookupError(join_id)
        return self._join(row)

    def joins_for_workspace(self, workspace_id: str) -> list[JoinSpecView]:
        with self.database.read() as connection:
            rows = connection.execute(
                """
                SELECT j.*
                FROM join_specs j
                JOIN structured_profiles pp ON pp.profile_id = j.primary_profile_id
                JOIN structured_profiles lp ON lp.profile_id = j.lookup_profile_id
                JOIN sources ps ON ps.source_id = pp.source_id
                JOIN sources ls ON ls.source_id = lp.source_id
                WHERE j.workspace_id = ?
                  AND ps.status != 'excluded'
                  AND ls.status != 'excluded'
                ORDER BY j.created_at, j.join_spec_id
                """,
                (workspace_id,),
            ).fetchall()
        return [self._join(row) for row in rows]

    def decide_join(self, join_id: str, action: str) -> JoinSpecView:
        join = self.get_join(join_id)
        if join.status != "proposed":
            return join
        now = utc_now()
        status = "approved" if action == "approve" else "rejected"
        decision = {"action": action, "operator": "Product Owner"}
        with self.database.transaction() as connection:
            connection.execute(
                "UPDATE join_specs SET status = ?, decision_json = ?, decided_at = ? WHERE join_spec_id = ?",
                (status, _json(decision), now, join_id),
            )
            connection.execute(
                """
                INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                VALUES (?, 'join_decided', ?, ?, ?)
                """,
                (join.workspace_id, join_id, _json(decision), now),
            )
        return self.get_join(join_id)

    @staticmethod
    def _profile(row) -> StructuredProfileView:
        payload = json.loads(row["profile_json"])
        return StructuredProfileView(
            profile_id=row["profile_id"],
            workspace_id=row["workspace_id"],
            source_id=row["source_id"],
            source_name=row["file_name"],
            source_kind=row["source_kind"],
            version=row["version"],
            fingerprint=row["fingerprint"],
            state=row["state"],
            structures=payload["structures"],
            mapping=MappingProfilePayload.model_validate(json.loads(row["mapping_json"])),
            summary=json.loads(row["summary_json"]),
            run_id=row["run_id"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _exception(row) -> PreparationException:
        return PreparationException(
            exception_id=row["exception_id"],
            profile_id=row["profile_id"],
            source_id=row["source_id"],
            source_name=row["file_name"],
            exception_kind=row["exception_kind"],
            severity=row["severity"],
            status=row["status"],
            title=row["title"],
            explanation=row["explanation"],
            payload=json.loads(row["payload_json"]),
            resolution=json.loads(row["resolution_json"]) if row["resolution_json"] else None,
            created_at=row["created_at"],
            resolved_at=row["resolved_at"],
        )

    @staticmethod
    def _join(row) -> JoinSpecView:
        return JoinSpecView(
            join_spec_id=row["join_spec_id"],
            workspace_id=row["workspace_id"],
            status=row["status"],
            primary_profile_id=row["primary_profile_id"],
            lookup_profile_id=row["lookup_profile_id"],
            spec=json.loads(row["spec_json"]),
            preview=json.loads(row["preview_json"]),
            decision=json.loads(row["decision_json"]) if row["decision_json"] else None,
        )
