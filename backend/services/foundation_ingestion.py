"""G1 deterministic PDF inventory run with complete terminal accounting."""

from __future__ import annotations

from backend.adapters.pdf import PdfAdapterResult
from backend.domain.evidence import QualityFlag
from backend.domain.runs import DispositionOutcome, RunState
from backend.domain.sources import Source
from backend.domain.workspace import Workspace
from backend.storage.repositories.operational_runs import OperationalRunRepository
from backend.storage.repositories.raw_units import RawUnitRepository


class FoundationIngestionService:
    def inventory_pdf_scope(
        self,
        *,
        workspace: Workspace,
        source: Source,
        scope: dict,
        adapter_result: PdfAdapterResult,
    ) -> tuple[dict, dict]:
        raw_repository = RawUnitRepository()
        run_repository = OperationalRunRepository()
        raw_repository.register_inventory(adapter_result.raw_units)
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
                "adapter_version": sorted(
                    {item.adapter_version for item in adapter_result.raw_units}
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
        for raw_unit in adapter_result.raw_units:
            page = raw_unit.locator.page
            evidence_ids = sorted(evidence_by_raw.get(raw_unit.raw_unit_id, []))
            if page not in included_pages:
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
