"""Automatic, all-pages PDF preparation for the G1 product-owner flow."""

from __future__ import annotations

from threading import Lock

from backend.adapters.pdf import ADAPTER_VERSION, PdfAdapter, PdfAdapterResult
from backend.domain.evidence import EvidenceUnit, QualityFlag, RawUnitDraft
from backend.domain.runs import DispositionOutcome, RunState
from backend.domain.sources import Source
from backend.domain.workspace import Workspace
from backend.services.foundation_ingestion import FoundationIngestionService
from backend.storage.raw_store import RawStore
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.operational_runs import OperationalRunRepository
from backend.storage.repositories.raw_units import RawUnitRepository

_locks_guard = Lock()
_source_locks: dict[str, Lock] = {}
_AUTOMATIC_OPERATOR = "system:g1-all-pages"


def _source_lock(source_id: str) -> Lock:
    with _locks_guard:
        return _source_locks.setdefault(source_id, Lock())


def _run_uses_current_adapter(run) -> bool:
    if run is None:
        return False
    configured = run.config.get("adapter_version")
    if isinstance(configured, str):
        versions = {configured}
    elif isinstance(configured, (list, tuple, set)):
        versions = {str(item) for item in configured}
    else:
        return False
    return versions == {ADAPTER_VERSION}


def _scope_uses_current_adapter(
    *,
    scope: dict | None,
    run,
    raw_units: list[RawUnitDraft],
    evidence_units: list[EvidenceUnit],
) -> bool:
    """Return true only when the active scope was built by this adapter.

    Scope rows predate an explicit adapter-version column.  Evidence ingestion
    metadata is therefore the primary proof; a matching current run is the
    fallback for a legitimately empty-evidence PDF.
    """

    if scope is None or not any(
        item.adapter_version == ADAPTER_VERSION and item.unit_kind == "pdf_page"
        for item in raw_units
    ):
        return False
    if evidence_units:
        return all(
            item.ingestion.adapter_version == ADAPTER_VERSION
            for item in evidence_units
        )
    return (
        run is not None
        and run.config.get("scope_id") == scope["scope_id"]
        and _run_uses_current_adapter(run)
    )


def _run_is_current_and_balanced(*, run, scope_id: str, raw_repository: RawUnitRepository) -> bool:
    if (
        run is None
        or run.config.get("scope_id") != scope_id
        or not _run_uses_current_adapter(run)
    ):
        return False
    try:
        accounting = raw_repository.accounting_report(run.run_id)
    except LookupError:
        return False
    return bool(accounting["balanced"] and accounting["unclassified_total"] == 0)


def _inventory_scope_with_obsolete_history(
    *,
    workspace: Workspace,
    source: Source,
    scope: dict,
    adapter_result: PdfAdapterResult,
) -> tuple[dict, dict]:
    """Create a balanced current run while retaining old adapter inventories.

    The raw ledger is source-wide, so a new run sees immutable RawUnits from
    every adapter generation.  Current units receive normal G1 dispositions;
    older units are terminally excluded from this run rather than deleted or
    silently reused.
    """

    raw_repository = RawUnitRepository()
    all_raw_units = raw_repository.list_inventory(source.source_id)
    obsolete = [item for item in all_raw_units if item.adapter_version != ADAPTER_VERSION]
    if not obsolete:
        return FoundationIngestionService().inventory_pdf_scope(
            workspace=workspace,
            source=source,
            scope=scope,
            adapter_result=adapter_result,
        )

    run_repository = OperationalRunRepository()
    run = run_repository.create(
        workspace_id=workspace.workspace_id,
        source_ids=[source.source_id],
        config={
            "kind": "g1_pdf_inventory",
            "workspace_id": workspace.workspace_id,
            "asset_identity_version": workspace.asset_identity_version,
            "source_id": source.source_id,
            "source_sha256": source.sha256,
            "assessment_id": source.asset_assessment_id,
            "scope_id": scope["scope_id"],
            "scope_version": scope["version"],
            "ontology_version": workspace.ontology_version,
            "ontology_sha256": workspace.ontology_sha256,
            "adapter_version": [ADAPTER_VERSION],
            "obsolete_adapter_versions": sorted(
                {item.adapter_version for item in obsolete}
            ),
        },
    )
    for state in (RunState.PREFLIGHT, RunState.READY, RunState.PROCESSING):
        run = run_repository.transition(run.run_id, state)

    evidence_by_raw: dict[str, list[str]] = {}
    for evidence in adapter_result.evidence_units:
        evidence_by_raw.setdefault(evidence.raw_ref.raw_unit_id, []).append(
            evidence.evidence_id
        )
    included_pages = set(scope["included_pages"])
    for raw_unit in all_raw_units:
        evidence_ids = sorted(evidence_by_raw.get(raw_unit.raw_unit_id, []))
        if raw_unit.adapter_version != ADAPTER_VERSION:
            outcome = DispositionOutcome.EXCLUDED
            reason_code = "PDF_ADAPTER_VERSION_OBSOLETE"
            evidence_ids = []
        elif raw_unit.locator.page not in included_pages:
            outcome = DispositionOutcome.EXCLUDED
            reason_code = "PDF_SCOPE_OPERATOR_EXCLUDED"
        elif QualityFlag.OCR_LOW_CONFIDENCE in raw_unit.quality_flags:
            outcome = DispositionOutcome.QUARANTINED
            reason_code = "OCR_LOW_CONFIDENCE"
        else:
            outcome = DispositionOutcome.PROCESSED
            reason_code = (
                "EVIDENCE_UNIT_EMITTED"
                if evidence_ids
                else "INVENTORY_PROCESSING_COMPLETED"
            )
        raw_repository.append_disposition(
            run_id=run.run_id,
            raw_unit_id=raw_unit.raw_unit_id,
            outcome=outcome,
            reason_code=reason_code,
            evidence_ids=evidence_ids,
        )

    report = raw_repository.assert_balanced(run.run_id)
    run_repository.record_ledger_manifest(run.run_id, report)
    run = run_repository.transition(run.run_id, RunState.AWAITING_REVIEW)
    report = raw_repository.assert_balanced(run.run_id)
    return run.model_dump(mode="json"), report


class PdfAutoPreparationService:
    """Prepare every physical page once and return a compact persisted summary."""

    def prepare(self, *, workspace: Workspace, source: Source) -> dict:
        with _source_lock(source.source_id):
            existing = self._existing_summary(workspace=workspace, source=source)
            if existing is not None:
                return existing

            evidence_repository = EvidenceRepository()
            raw_repository = RawUnitRepository()
            current = evidence_repository.current_scope(source.source_id)
            persisted_raw_units = raw_repository.list_inventory(source.source_id)
            persisted_evidence = evidence_repository.list_evidence(
                workspace_id=workspace.workspace_id,
                source_id=source.source_id,
            )
            latest_run = OperationalRunRepository().latest_for_source(source.source_id)
            current_scope_adapter = _scope_uses_current_adapter(
                scope=current,
                run=latest_run,
                raw_units=persisted_raw_units,
                evidence_units=persisted_evidence,
            )

            if current_scope_adapter:
                # A current immutable inventory remains safe to reuse, notably
                # when a source is restored after preparation but before a G1
                # run was created.  Filter by version so historical rows can
                # never leak back into the operational adapter result.
                current_raw_units = [
                    item
                    for item in persisted_raw_units
                    if item.adapter_version == ADAPTER_VERSION
                ]
                current_evidence = [
                    item
                    for item in persisted_evidence
                    if item.ingestion.adapter_version == ADAPTER_VERSION
                ]
                pages = sorted(
                    {
                        int(item.locator.page)
                        for item in current_raw_units
                        if item.unit_kind == "pdf_page"
                    }
                )
                adapter_result = PdfAdapterResult(
                    raw_units=current_raw_units,
                    evidence_units=current_evidence,
                    page_previews=[{"page": page, "included": True} for page in pages],
                )
            else:
                # Never reconstruct a new result from obsolete raw/evidence:
                # layout/OCR semantics may have changed even when the PDF bytes
                # and page count have not.
                path = RawStore().resolve(source.raw_relpath or "")
                adapter_result = PdfAdapter().inspect(
                    path=path,
                    workspace=workspace,
                    source=source,
                    scope_version=int((current or {}).get("version", 0)) + 1,
                )
                pages = sorted(int(item["page"]) for item in adapter_result.page_previews)
            raw_repository.register_inventory(adapter_result.raw_units)

            scope_matches = (
                current_scope_adapter
                and current is not None
                and current["operator"] == _AUTOMATIC_OPERATOR
                and current["included_pages"] == pages
                and current["excluded_pages"] == {}
            )
            scope = current if scope_matches else evidence_repository.save_scope(
                workspace_id=workspace.workspace_id,
                source_id=source.source_id,
                included_pages=pages,
                excluded_pages={},
                operator=_AUTOMATIC_OPERATOR,
                evidence_units=adapter_result.evidence_units,
                # Matching page lists are insufficient across adapter changes:
                # the active scope must move to the newly generated evidence.
                reuse_matching=False,
            )

            run = OperationalRunRepository().latest_for_source(source.source_id)
            if not _run_is_current_and_balanced(
                run=run,
                scope_id=scope["scope_id"],
                raw_repository=raw_repository,
            ):
                _inventory_scope_with_obsolete_history(
                    workspace=workspace,
                    source=source,
                    scope=scope,
                    adapter_result=adapter_result,
                )
            summary = self._existing_summary(workspace=workspace, source=source)
            if summary is None:
                raise RuntimeError("Automatic PDF preparation did not persist its run")
            return summary

    @staticmethod
    def _existing_summary(*, workspace: Workspace, source: Source) -> dict | None:
        evidence_repository = EvidenceRepository()
        scope = evidence_repository.current_scope(source.source_id)
        if scope is None or scope.get("operator") != _AUTOMATIC_OPERATOR:
            return None
        run = OperationalRunRepository().latest_for_source(source.source_id)
        raw_repository = RawUnitRepository()
        if not _run_is_current_and_balanced(
            run=run,
            scope_id=scope["scope_id"],
            raw_repository=raw_repository,
        ):
            return None
        persisted_raw_units = raw_repository.list_inventory(source.source_id)
        evidence = evidence_repository.list_evidence(
            workspace_id=workspace.workspace_id,
            source_id=source.source_id,
        )
        if not _scope_uses_current_adapter(
            scope=scope,
            run=run,
            raw_units=persisted_raw_units,
            evidence_units=evidence,
        ):
            return None
        accounting = raw_repository.accounting_report(run.run_id)
        return {
            "mode": "automatic_all_pages",
            "adapter_version": ADAPTER_VERSION,
            "source_id": source.source_id,
            "scope_id": scope["scope_id"],
            "scope_version": scope["version"],
            "page_count": len(scope["included_pages"]),
            "included_page_count": len(scope["included_pages"]),
            "excluded_page_count": 0,
            "evidence_count": len(evidence),
            "run_id": run.run_id,
            "run_state": run.state.value,
            "balanced": accounting["balanced"],
            "unclassified_total": accounting["unclassified_total"],
        }
