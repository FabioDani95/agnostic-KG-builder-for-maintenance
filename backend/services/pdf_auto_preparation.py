"""Automatic, all-pages PDF preparation for the G1 product-owner flow."""

from __future__ import annotations

from threading import Lock

from backend.adapters.pdf import PdfAdapter, PdfAdapterResult
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
            if persisted_raw_units:
                pages = sorted(
                    {
                        int(item.locator.page)
                        for item in persisted_raw_units
                        if item.unit_kind == "pdf_page"
                    }
                )
                persisted_evidence = evidence_repository.list_evidence(
                    workspace_id=workspace.workspace_id,
                    source_id=source.source_id,
                )
                adapter_result = PdfAdapterResult(
                    raw_units=persisted_raw_units,
                    evidence_units=persisted_evidence,
                    page_previews=[{"page": page, "included": True} for page in pages],
                )
            else:
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
                current is not None
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
                reuse_matching=True,
            )

            run = OperationalRunRepository().latest_for_source(source.source_id)
            if run is None or run.config.get("scope_id") != scope["scope_id"]:
                FoundationIngestionService().inventory_pdf_scope(
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
        if run is None or run.config.get("scope_id") != scope["scope_id"]:
            return None
        accounting = RawUnitRepository().accounting_report(run.run_id)
        evidence_count = len(
            evidence_repository.list_evidence(
                workspace_id=workspace.workspace_id,
                source_id=source.source_id,
            )
        )
        return {
            "mode": "automatic_all_pages",
            "source_id": source.source_id,
            "scope_id": scope["scope_id"],
            "scope_version": scope["version"],
            "page_count": len(scope["included_pages"]),
            "included_page_count": len(scope["included_pages"]),
            "excluded_page_count": 0,
            "evidence_count": evidence_count,
            "run_id": run.run_id,
            "run_state": run.state.value,
            "balanced": accounting["balanced"],
            "unclassified_total": accounting["unclassified_total"],
        }
