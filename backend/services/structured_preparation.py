"""Automatic-with-exceptions preparation for CSV, XLSX, JSON and JSONL sources."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from threading import Lock, RLock
from typing import Any

from backend.adapters.structured import ParsedRecord, StructuredInspection, inspect_structured_source
from backend.adapters.structured.common import ADAPTER_VERSION, ROLE_ALIAS_CONFIG_VERSION, canonical_value
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
from backend.domain.runs import (
    DispositionError,
    DispositionOutcome,
    Retryability,
    RunState,
)
from backend.domain.sources import Source, SourceKind, SourceState
from backend.domain.structured import G2PreparationView, StructuredProfileView
from backend.domain.workspace import Workspace
from backend.storage.raw_store import RawStore
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.operational_runs import OperationalRunRepository
from backend.storage.repositories.raw_units import RawUnitRepository
from backend.storage.repositories.sources import SourceRepository
from backend.storage.repositories.structured import StructuredPreparationRepository
from backend.storage.repositories.workspaces import WorkspaceRepository

STRUCTURED_KINDS = {SourceKind.CSV, SourceKind.XLSX, SourceKind.JSON, SourceKind.JSONL}

_locks_guard = Lock()
_workspace_locks: dict[str, RLock] = {}


def _workspace_lock(workspace_id: str) -> RLock:
    """Serialize one workspace's profile mutation and materialization span."""
    with _locks_guard:
        return _workspace_locks.setdefault(workspace_id, RLock())

#: Which mapping profiles the operator has confirmed, right now.
#:
#: The audit ledger is append-only, so a confirmation is never removed: editing
#: the mapping appends a withdrawal instead, because the confirmation was given
#: for a different reading of the file. A profile counts as confirmed when no
#: withdrawal follows its latest confirmation — both events stay on the record.
CONFIRMED_PROFILES_SQL = """
    SELECT DISTINCT a.subject_id FROM audit_events a
    WHERE a.workspace_id = ? AND a.event_kind = 'structured_source_confirmed'
      AND NOT EXISTS (
        SELECT 1 FROM audit_events b
        WHERE b.workspace_id = a.workspace_id
          AND b.subject_id = a.subject_id
          AND b.event_kind = 'structured_source_confirmation_withdrawn'
          AND (b.created_at > a.created_at
               OR (b.created_at = a.created_at AND b.rowid > a.rowid))
      )
"""


class StructuredPreparationError(RuntimeError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(canonical_value(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


#: How meaning is derived from an already-parsed row: which cells become
#: claims, and how a role maps onto an evidence field. It belongs to the
#: fingerprint of a reading, so evidence and subgraphs built by an earlier
#: derivation invalidate instead of being reused.
#:
#: Deliberately separate from ADAPTER_VERSION, which identifies the parse and is
#: stamped into immutable RawUnits: bumping that one to express a change of
#: meaning made every existing row impossible to re-register, and the whole
#: preparation failed.
EVIDENCE_DERIVATION_VERSION = "cell-per-claim-v1"


def mapping_fingerprint(profile: StructuredProfileView) -> str:
    """Fingerprint the effective reading of a source.

    A reading is the operator-resolved mapping *and* the derivation that applies
    it. Leaving the derivation out made the fingerprint blind to a change in how
    evidence is built: the evidence changed, the fingerprint did not, and a
    subgraph built from the previous derivation was reused as if current.
    """
    return _hash({
        "mapping_profile_id": profile.profile_id,
        "mapping": profile.mapping.model_dump(mode="json"),
        "evidence_derivation_version": EVIDENCE_DERIVATION_VERSION,
    })


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return _canonical_json(value)
    return str(canonical_value(value)).strip()


class StructuredPreparationService:
    def __init__(self) -> None:
        self.sources = SourceRepository()
        self.profiles = StructuredPreparationRepository()
        self.raw_units = RawUnitRepository()
        self.runs = OperationalRunRepository()
        self.evidence = EvidenceRepository()

    def ensure_workspace(self, workspace_id: str) -> G2PreparationView:
        with _workspace_lock(workspace_id):
            return self._ensure_workspace(workspace_id)

    def _ensure_workspace(self, workspace_id: str) -> G2PreparationView:
        workspace = WorkspaceRepository().get_by_id(workspace_id)
        if workspace is None:
            raise LookupError(workspace_id)
        sources = self._structured_sources(workspace_id)
        inspections: dict[str, StructuredInspection] = {}
        for source in sources:
            inspection = self._inspect(source)
            inspections[source.source_id] = inspection
            self.profiles.create_profile(source, inspection)

        profile_views = self.profiles.profiles_for_workspace(workspace_id)
        all_exceptions = self.profiles.exceptions_for_workspace(workspace_id)
        pending_exceptions = [item for item in all_exceptions if item.status in {"open", "queued"}]
        pending_profile_ids = {item.profile_id for item in pending_exceptions}
        self._propose_safe_joins(
            workspace_id=workspace_id,
            profiles=[item for item in profile_views if item.profile_id not in pending_profile_ids],
            inspections=inspections,
        )

        proposed_primary = {
            item.primary_profile_id
            for item in self.profiles.joins_for_workspace(workspace_id)
            if item.status == "proposed"
        }
        for profile in self.profiles.profiles_for_workspace(workspace_id):
            if profile.state == "prepared" or profile.profile_id in pending_profile_ids:
                continue
            if profile.profile_id in proposed_primary:
                continue
            source = next(item for item in sources if item.source_id == profile.source_id)
            inspection = inspections[source.source_id]
            self._materialize(workspace, source, profile, inspection)
        return self.snapshot(workspace_id)

    def snapshot(self, workspace_id: str) -> G2PreparationView:
        if WorkspaceRepository().get_by_id(workspace_id) is None:
            raise LookupError(workspace_id)
        profiles = self.profiles.profiles_for_workspace(workspace_id)
        exceptions = self.profiles.exceptions_for_workspace(workspace_id)
        joins = self.profiles.joins_for_workspace(workspace_id)
        open_exceptions = [item for item in exceptions if item.status == "open"]
        queued_exceptions = [item for item in exceptions if item.status == "queued"]
        pending_exceptions = [*open_exceptions, *queued_exceptions]
        proposed_joins = [item for item in joins if item.status == "proposed"]
        from backend.storage.database import get_database

        with get_database().read() as connection:
            confirmed_profile_ids = {
                row["subject_id"]
                for row in connection.execute(
                    CONFIRMED_PROFILES_SQL, (workspace_id,)
                ).fetchall()
            }
        enriched_profiles = []
        for item in profiles:
            summary = dict(item.summary)
            if "language_counts" not in summary and item.run_id:
                units = self.evidence.list_evidence(
                    workspace_id=workspace_id,
                    source_id=item.source_id,
                )
                summary["language_counts"] = dict(
                    Counter(
                        unit.language.qualification.value
                        for unit in units
                        if unit.ingestion.mapping_profile_id == item.profile_id
                    )
                )
            enriched_profiles.append(
                item.model_copy(
                    update={
                        "confirmed": item.profile_id in confirmed_profile_ids,
                        "summary": summary,
                    }
                )
            )
        profiles = enriched_profiles
        prepared = sum(item.state == "prepared" for item in profiles)
        confirmed = sum(item.confirmed for item in profiles)
        failed = sum(item.state == "failed" for item in profiles)
        can_complete = not pending_exceptions and not proposed_joins and prepared == len(profiles)
        completed = can_complete and confirmed == len(profiles)
        if failed:
            state = "failed"
        elif pending_exceptions or proposed_joins:
            state = "needs_attention"
        elif can_complete:
            state = "ready"
        else:
            state = "analyzing"
        return G2PreparationView(
            workspace_id=workspace_id,
            state=state,
            profiles=profiles,
            exceptions=exceptions,
            joins=joins,
            counts={
                "structured_sources": len(profiles),
                "prepared_sources": prepared,
                "confirmed_sources": confirmed,
                "open_exceptions": len(open_exceptions),
                "queued_exceptions": len(queued_exceptions),
                "proposed_joins": len(proposed_joins),
                "records": sum(int(item.summary.get("record_count", 0)) for item in profiles),
                "evidence": sum(int(item.summary.get("evidence_count", 0)) for item in profiles),
                "isolated_records": sum(int(item.summary.get("isolated_record_count", 0)) for item in profiles),
            },
            can_complete=can_complete,
            completed=completed,
        )

    def resolve_exception(self, exception_id: str, resolution: dict[str, Any]) -> G2PreparationView:
        exception = self.profiles.get_exception(exception_id)
        workspace_id = self.profiles.get_profile(exception.profile_id).workspace_id
        with _workspace_lock(workspace_id):
            self.profiles.resolve_exception(exception_id, resolution)
            return self._ensure_workspace(workspace_id)

    def set_column_role(
        self,
        profile_id: str,
        *,
        structure_id: str,
        column: str,
        role: str,
    ) -> G2PreparationView:
        """Correct how one column was read, then re-read the file with it."""
        workspace_id = self.profiles.get_profile(profile_id).workspace_id
        with _workspace_lock(workspace_id):
            self.profiles.set_column_role(
                profile_id, structure_id=structure_id, column=column, role=role
            )
            return self._ensure_workspace(workspace_id)

    def decide_join(self, join_id: str, action: str) -> G2PreparationView:
        workspace_id = self.profiles.get_join(join_id).workspace_id
        with _workspace_lock(workspace_id):
            self.profiles.decide_join(join_id, action)
            return self._ensure_workspace(workspace_id)

    def confirm_profile(self, profile_id: str) -> G2PreparationView:
        profile = self.profiles.get_profile(profile_id)
        with _workspace_lock(profile.workspace_id):
            return self._confirm_profile(profile_id)

    def _confirm_profile(self, profile_id: str) -> G2PreparationView:
        profile = self.profiles.get_profile(profile_id)
        snapshot = self._ensure_workspace(profile.workspace_id)
        current = next((item for item in snapshot.profiles if item.profile_id == profile_id), None)
        if current is None:
            raise LookupError(profile_id)
        if current.state != "prepared":
            raise StructuredPreparationError(
                "Questa fonte non è ancora pronta: rispondi prima alla scelta aperta su di essa."
            )
        if any(
            item.status in {"open", "queued"} and item.profile_id == profile_id
            for item in snapshot.exceptions
        ):
            raise StructuredPreparationError("Questa fonte contiene ancora una scelta aperta.")
        if any(
            item.status == "proposed"
            and profile_id in {item.primary_profile_id, item.lookup_profile_id}
            for item in snapshot.joins
        ):
            raise StructuredPreparationError(
                "Decidi prima se collegare questa fonte all'altra tabella proposta."
            )
        from backend.domain.ids import utc_now
        from backend.storage.database import get_database

        with get_database().transaction() as connection:
            # Confirming twice must not append twice — but a confirmation that
            # was withdrawn, because the mapping changed underneath it, has to
            # be given again. The guard therefore asks whether the profile is
            # confirmed *now*, not whether it ever was.
            already_confirmed = connection.execute(
                f"SELECT 1 FROM ({CONFIRMED_PROFILES_SQL}) WHERE subject_id = ? LIMIT 1",
                (profile.workspace_id, profile_id),
            ).fetchone()
            if already_confirmed is None:
                connection.execute(
                    """
                    INSERT INTO audit_events(workspace_id, event_kind, subject_id, payload_json, created_at)
                    VALUES (?, 'structured_source_confirmed', ?, ?, ?)
                    """,
                    (
                        profile.workspace_id,
                        profile_id,
                        _canonical_json({"source_id": profile.source_id, "fingerprint": profile.fingerprint}),
                        utc_now(),
                    ),
                )
        return self.snapshot(profile.workspace_id)

    def complete(self, workspace_id: str) -> G2PreparationView:
        with _workspace_lock(workspace_id):
            snapshot = self._ensure_workspace(workspace_id)
            if not snapshot.completed:
                raise StructuredPreparationError(
                    "Conferma ogni fonte prima di continuare."
                )
            return snapshot

    def _structured_sources(self, workspace_id: str) -> list[Source]:
        return [
            source
            for source in self.sources.list_for_workspace(workspace_id)
            if source.source_kind in STRUCTURED_KINDS and source.status is not SourceState.EXCLUDED
        ]

    @staticmethod
    def _path(source: Source) -> Path:
        if not source.raw_relpath:
            raise StructuredPreparationError(f"Il contenuto originale di {source.file_name} non è disponibile")
        return RawStore().resolve(source.raw_relpath)

    def _inspect(self, source: Source) -> StructuredInspection:
        try:
            return inspect_structured_source(self._path(source), source)
        except StructuredPreparationError:
            raise
        except Exception as exc:
            raise StructuredPreparationError(
                f"Non è stato possibile leggere {source.file_name}. Il file originale è rimasto invariato: {exc}"
            ) from exc

    def _propose_safe_joins(
        self,
        *,
        workspace_id: str,
        profiles: list[StructuredProfileView],
        inspections: dict[str, StructuredInspection],
    ) -> None:
        existing = self.profiles.joins_for_workspace(workspace_id)
        occupied = {
            profile_id
            for item in existing
            if item.status == "proposed"
            for profile_id in (item.primary_profile_id, item.lookup_profile_id)
        }
        candidates = [item for item in profiles if item.state != "prepared" and item.profile_id not in occupied]
        for primary in candidates:
            for lookup in candidates:
                if primary.profile_id == lookup.profile_id or lookup.profile_id in occupied:
                    continue
                proposal = self._join_candidate(
                    primary,
                    lookup,
                    inspections[primary.source_id],
                    inspections[lookup.source_id],
                )
                if proposal is None:
                    continue
                spec, preview = proposal
                self.profiles.create_join(workspace_id, primary.profile_id, lookup.profile_id, spec, preview)
                occupied.update({primary.profile_id, lookup.profile_id})
                break

    @staticmethod
    def _join_candidate(
        primary: StructuredProfileView,
        lookup: StructuredProfileView,
        primary_inspection: StructuredInspection,
        lookup_inspection: StructuredInspection,
    ) -> tuple[dict[str, Any], dict[str, Any]] | None:
        primary_records = [item for item in primary_inspection.records if item.disposition == "processed"]
        lookup_records = [item for item in lookup_inspection.records if item.disposition == "processed"]
        if not primary_records or len(lookup_records) < 2:
            return None
        primary_columns = {key for item in primary_records for key in item.values}
        lookup_columns = {key for item in lookup_records for key in item.values}
        key_names = [
            key for key in sorted(primary_columns & lookup_columns)
            if key.casefold() in {"id", "code", "component_id", "component_code", "asset_id", "work_order_id"}
            or key.casefold().endswith(("_id", "_code"))
        ]
        for key in key_names:
            lookup_values = [_text(item.values.get(key)) for item in lookup_records]
            lookup_values = [value for value in lookup_values if value]
            if len(lookup_values) != len(set(lookup_values)) or len(lookup_values) < 2:
                continue
            primary_values = [_text(item.values.get(key)) for item in primary_records]
            matched = sum(value in set(lookup_values) for value in primary_values if value)
            if matched == 0:
                continue
            preview_rows = []
            lookup_by_key = {
                _text(item.values.get(key)): item.values for item in lookup_records if _text(item.values.get(key))
            }
            for item in primary_records[:5]:
                value = _text(item.values.get(key))
                preview_rows.append({"primary": canonical_value(item.values), "lookup": canonical_value(lookup_by_key.get(value))})
            imported_fields = sorted(lookup_columns - {key})
            return (
                {
                    "primary_source_id": primary.source_id,
                    "lookup_source_id": lookup.source_id,
                    "primary_key": key,
                    "lookup_key": key,
                    "cardinality": "n:1",
                    "unmatched_policy": "preserve_primary",
                    "multiple_policy": "block",
                    "fan_out_max": 1,
                    "imported_fields": imported_fields,
                },
                {
                    "matched_records": matched,
                    "unmatched_records": len(primary_records) - matched,
                    "lookup_records": len(lookup_records),
                    "sample": preview_rows,
                },
            )
        return None

    def _materialize(
        self,
        workspace: Workspace,
        source: Source,
        profile: StructuredProfileView,
        inspection: StructuredInspection,
    ) -> None:
        records = inspection.records
        self.raw_units.register_inventory([item.raw_unit for item in records])
        approved_join = next(
            (
                item
                for item in self.profiles.joins_for_workspace(workspace.workspace_id)
                if item.primary_profile_id == profile.profile_id and item.status == "approved"
            ),
            None,
        )
        lookup_by_key: dict[str, ParsedRecord] = {}
        if approved_join is not None:
            lookup_profile = self.profiles.get_profile(approved_join.lookup_profile_id)
            lookup_source = self.sources.get(lookup_profile.source_id)
            lookup_key = approved_join.spec["lookup_key"]
            for record in self._inspect(lookup_source).records:
                value = _text(record.values.get(lookup_key))
                if value and record.disposition == "processed":
                    lookup_by_key[value] = record

        evidence_units: list[EvidenceUnit] = []
        evidence_by_raw: dict[str, list[str]] = defaultdict(list)
        effective_mapping_fingerprint = mapping_fingerprint(profile)
        included_count = 0
        isolated_count = 0
        disposition_items: list[dict[str, Any]] = []
        for record in records:
            structure_mapping = profile.mapping.structures.get(record.raw_unit.structure_id or "", {})
            structure_included = any(item.included for item in structure_mapping.values()) if structure_mapping else record.included
            if record.disposition in {"quarantined", "failed"} or not structure_included:
                isolated_count += 1
                continue
            included_count += 1
            lookup_record = None
            if approved_join is not None:
                lookup_record = lookup_by_key.get(_text(record.values.get(approved_join.spec["primary_key"])))
            evidence = self._evidence_for_record(
                workspace=workspace,
                source=source,
                profile=profile,
                record=record,
                lookup_record=lookup_record,
                imported_fields=(approved_join.spec.get("imported_fields", []) if approved_join else []),
                effective_mapping_fingerprint=effective_mapping_fingerprint,
            )
            evidence_units.append(evidence)
            evidence_by_raw[record.raw_unit.raw_unit_id].append(evidence.evidence_id)

        self.evidence.save_structured_evidence(profile_id=profile.profile_id, evidence_units=evidence_units)
        run = self.runs.create(
            workspace_id=workspace.workspace_id,
            source_ids=[source.source_id],
            config={
                "kind": "g2_structured_preparation",
                "source_id": source.source_id,
                "source_sha256": source.sha256,
                "profile_id": profile.profile_id,
                "profile_version": profile.version,
                "mapping": profile.mapping.model_dump(mode="json"),
                "mapping_fingerprint": effective_mapping_fingerprint,
                "join_spec_id": approved_join.join_spec_id if approved_join else None,
                "adapter_version": ADAPTER_VERSION,
                "role_alias_config_version": ROLE_ALIAS_CONFIG_VERSION,
            },
        )
        for state in (RunState.PREFLIGHT, RunState.READY, RunState.PROCESSING):
            run = self.runs.transition(run.run_id, state)
        for record in records:
            evidence_ids = evidence_by_raw.get(record.raw_unit.raw_unit_id, [])
            structure_mapping = profile.mapping.structures.get(record.raw_unit.structure_id or "", {})
            structure_included = any(item.included for item in structure_mapping.values()) if structure_mapping else record.included
            disposition_error = None
            retryability = Retryability.NOT_APPLICABLE
            if record.disposition == "failed":
                outcome = DispositionOutcome.FAILED
                reason = record.reason_code
                retryability = Retryability.NOT_RETRYABLE
                disposition_error = DispositionError(
                    code=record.reason_code,
                    title="Riga strutturata non leggibile",
                    object_ref=record.raw_unit.raw_unit_id,
                    cause="La singola unità non rispetta il formato dichiarato.",
                    preserved="Il contenuto originale e tutte le altre unità sono rimasti disponibili.",
                    action="Correggere la riga nel file sorgente soltanto se deve contribuire al grafo.",
                    technical_detail=_canonical_json(record.raw_unit.locator.model_dump(mode="json")),
                )
            elif record.disposition == "quarantined":
                outcome = DispositionOutcome.QUARANTINED
                reason = record.reason_code
            elif not structure_included:
                outcome = DispositionOutcome.EXCLUDED
                reason = record.reason_code if record.disposition == "excluded" else "STRUCTURE_EXCLUDED"
            else:
                outcome = DispositionOutcome.PROCESSED
                reason = "EVIDENCE_UNIT_EMITTED" if evidence_ids else "INVENTORY_PROCESSING_COMPLETED"
            disposition_items.append(
                {
                    "raw_unit_id": record.raw_unit.raw_unit_id,
                    "outcome": outcome,
                    "reason_code": reason,
                    "evidence_ids": evidence_ids,
                    "retryability": retryability,
                    "error": disposition_error,
                }
            )
        self.raw_units.append_dispositions(run_id=run.run_id, items=disposition_items)
        report = self.raw_units.assert_balanced(run.run_id)
        self.runs.record_ledger_manifest(run.run_id, report)
        self.runs.transition(run.run_id, RunState.AWAITING_REVIEW)
        self.profiles.mark_prepared(
            profile.profile_id,
            run_id=run.run_id,
            summary_updates={
                "included_record_count": included_count,
                "isolated_record_count": isolated_count,
                "evidence_count": len(evidence_units),
                "language_counts": dict(Counter(item.language.qualification.value for item in evidence_units)),
                "ledger_hash": report["ledger_hash"],
                "balanced": report["balanced"],
            },
        )

    @staticmethod
    def _evidence_for_record(
        *,
        workspace: Workspace,
        source: Source,
        profile: StructuredProfileView,
        record: ParsedRecord,
        lookup_record: ParsedRecord | None,
        imported_fields: list[str],
        effective_mapping_fingerprint: str,
    ) -> EvidenceUnit:
        mapping = profile.mapping.structures.get(record.raw_unit.structure_id or "", {})
        by_role: dict[str, list[str]] = defaultdict(list)
        attributes: dict[str, Any] = {}
        for column, value in record.values.items():
            config = mapping.get(column)
            if config is None or not config.included or config.role == "excluded":
                continue
            attributes[column] = canonical_value(value)
            text = _text(value)
            if text and config.role != "attribute":
                by_role[config.role].append(text)
        if lookup_record is not None:
            for column in imported_fields:
                if column in lookup_record.values:
                    attributes[f"lookup.{column}"] = canonical_value(lookup_record.values[column])

        def joined(role: str) -> str:
            return " | ".join(dict.fromkeys(by_role.get(role, [])))

        semantic_texts = {
            key: value
            for key, value in {
                "symptom": joined("observation"),
                "failure_mode": joined("cause"),
                "corrective_action": joined("action"),
                "component": joined("component"),
                "error_code_context": joined("error_code"),
            }.items()
            if value
        }
        content = EvidenceContent(
            title=source.file_name or "Structured record",
            observation=joined("observation"),
            cause=joined("cause"),
            action=joined("action"),
            outcome=joined("outcome"),
            error_code=joined("error_code"),
            measurement=joined("measurement"),
            semantic_texts=semantic_texts,
        )
        if any((content.observation, content.cause, content.action, content.error_code)):
            role = RecordRole.MAINTENANCE_EVENT
        elif content.measurement:
            role = RecordRole.MEASUREMENT
        else:
            role = RecordRole.GENERIC_EVIDENCE
        language = StructuredPreparationService._language(record.values, content)
        provenance = [
            ProvenanceRef(
                role="primary",
                raw_unit_id=record.raw_unit.raw_unit_id,
                source_id=source.source_id,
                locator=record.raw_unit.locator,
                raw_hash=record.raw_unit.raw_hash,
                structure_id=record.raw_unit.structure_id,
            )
        ]
        if lookup_record is not None:
            provenance.append(
                ProvenanceRef(
                    role="lookup",
                    raw_unit_id=lookup_record.raw_unit.raw_unit_id,
                    source_id=lookup_record.raw_unit.source_id,
                    locator=lookup_record.raw_unit.locator,
                    raw_hash=lookup_record.raw_unit.raw_hash,
                    structure_id=lookup_record.raw_unit.structure_id,
                )
            )
        locator_hash = _hash(record.raw_unit.locator.model_dump(mode="json"))
        # The mapping is part of what an evidence unit *is*: the same row read
        # with a different column meaning is a different reading, and evidence
        # is immutable. Leaving the fingerprint out gave a stable id, so a
        # corrected mapping kept the old payload and the graph was rebuilt from
        # a reading nobody had confirmed.
        evidence_id = f"ev_{_hash({
            'profile_id': profile.profile_id,
            'mapping_fingerprint': effective_mapping_fingerprint,
            'raw_unit_id': record.raw_unit.raw_unit_id,
        })[:28]}"
        occurred_at = joined("occurred_at") or None
        return EvidenceUnit(
            evidence_id=evidence_id,
            workspace_id=workspace.workspace_id,
            asset_id=workspace.asset.asset_id,
            source_id=source.source_id,
            source_kind=source.source_kind,
            authority=source.authority,
            locator=record.raw_unit.locator,
            provenance_refs=provenance,
            language=language,
            record_role=role,
            occurred_at=occurred_at,
            content=content,
            attributes=attributes,
            quality_flags=record.raw_unit.quality_flags,
            raw_ref=RawReference(
                source_id=source.source_id,
                raw_unit_id=record.raw_unit.raw_unit_id,
                locator_hash=locator_hash,
            ),
            ingestion=IngestionInfo(
                adapter_version=ADAPTER_VERSION,
                mapping_profile_id=profile.profile_id,
                mapping_fingerprint=effective_mapping_fingerprint,
            ),
        )

    @staticmethod
    def _language(values: dict[str, Any], content: EvidenceContent) -> LanguageInfo:
        explicit = _text(
            values.get("language")
            or values.get("lang")
            or values.get("lingua")
            or values.get("sprache")
        ).casefold()
        if explicit in {"en", "eng", "english"}:
            return LanguageInfo(detected="en", confidence=1, qualification=LanguageQualification.QUALIFIED_EN)
        if explicit in {"it", "ita", "italian", "italiano"}:
            return LanguageInfo(detected="it", confidence=1, qualification=LanguageQualification.UNQUALIFIED_IT)
        if explicit in {"de", "deu", "german", "deutsch"}:
            return LanguageInfo(detected="de", confidence=1, qualification=LanguageQualification.UNQUALIFIED_DE)
        if explicit in {"mixed", "misto"}:
            return LanguageInfo(detected="mixed", confidence=1, qualification=LanguageQualification.MIXED)
        sample = " ".join(
            value for value in (content.observation, content.cause, content.action, content.outcome) if value
        )
        if len(sample) >= 24:
            try:
                from langdetect import detect

                detected = detect(sample)
                qualification = {
                    "en": LanguageQualification.QUALIFIED_EN,
                    "it": LanguageQualification.UNQUALIFIED_IT,
                    "de": LanguageQualification.UNQUALIFIED_DE,
                }.get(detected, LanguageQualification.UNKNOWN)
                return LanguageInfo(detected=detected, qualification=qualification)
            except Exception:
                pass
        return LanguageInfo(detected="unknown", qualification=LanguageQualification.UNKNOWN)
