"""The quality profile's stages inside one V3 run.

``run.Pipeline`` calls these at fixed points; with the base profile none of them runs.

1. ``prepare_roles``: a client per role (review, verify, vision), recorded with its model.
2. ``prepare_source_index``: the evidence catalog of the document (segments, cell items, regions).
3. ``visual_catalog``: which pages need their image read; layout of pages without text.
4. ``start_coverage``: observed items of the read pages, against the checked relations.
5. ``completeness_review``: bounded review of missing items, then merge decisions for new pairs.
6. ``finalize``: coverage, scope promotion after review, and the final validation.
"""

from __future__ import annotations

from typing import Any

from backend.kg_v3.contracts import ReviewerKind
from backend.kg_v3.coverage import inventory, update_coverage
from backend.kg_v3.llm import ModelClient, RoleClient
from backend.kg_v3.merger import MergePlan, judge_pairs, merge_candidates
from backend.kg_v3.omissions import review_quality
from backend.kg_v3.quality_contracts import DocumentIdentity, PageRoute
from backend.kg_v3.run_state import atomic_json, digest, stable_id
from backend.kg_v3.source_index import SourceIndex, bind_proposal, build_source_index
from backend.kg_v3.validation import validate_quality
from backend.kg_v3.visual_catalog import QualityImages, classify_visual_pages, read_visual_structure

ROLES = ("review", "verify", "vision")


def prepare_roles(pipeline) -> None:
    """One client per role. Without a model of its own a role reuses the primary model,
    with its own reasoning effort; a requested model must be known and actually used."""

    from backend.services.model_pricing import MODEL_PRICING

    cfg = pipeline.config.quality
    primary = getattr(pipeline.llm, "model", pipeline.config.model)
    for role in ROLES:
        requested = getattr(cfg, role + "_model")
        effort = getattr(cfg, role + "_reasoning")
        if requested and requested not in MODEL_PRICING:
            raise ValueError(f"{role}_model not configured/known: {requested}")
        client = pipeline.role_clients.get(role)
        if client is None:
            client = (
                ModelClient(model=requested, reasoning_effort=effort)
                if requested and requested != primary
                else pipeline.llm
            )
        actual = getattr(client, "model", requested or primary)
        if requested and actual != requested:
            raise ValueError(f"{role}_model mismatch: requested {requested}, configured {actual}")
        if not isinstance(client, RoleClient):
            client = RoleClient(client, effort, role=role)
        pipeline.role_clients[role] = client
        pipeline.role_profiles[role] = {
            "model": actual,
            "reasoning_effort": effort,
            "same_model_review": actual == primary,
        }


def prepare_source_index(pipeline, manifest: dict[str, Any]) -> None:
    """Build the catalog, or reload the one this run already saved for the same document."""

    identity = DocumentIdentity(
        document_id=stable_id("document", manifest["pdf_sha256"]),
        pdf_sha256=manifest["pdf_sha256"],
        asset_scope_id=manifest["asset_scope_id"],
        source_title=pipeline.pdf_path.name if pipeline.pdf_path else pipeline.asset_name,
        parser_fingerprint=manifest["parser_base_fingerprint"],
        inventory_fingerprint=manifest["document_basis_sha256"],
    )
    saved = pipeline.workdir / "source_index.json" if pipeline.workdir else None
    if saved and saved.exists():
        index = SourceIndex.model_validate(pipeline.run_state.load_index())
    else:
        index = build_source_index(pipeline.doc, pipeline.doc.page_geometry, identity)
    if index.identity != identity:
        raise ValueError("source index belongs to different document/parser")
    pipeline.source_index = pipeline.doc.source_index = index
    pipeline.run_state.revise_index(index, {"stage": "parser_base"})


async def visual_catalog(pipeline) -> list[PageRoute]:
    """Route pages by layout; catalogue the diagram of every diagnostic page without text.

    Pages with text are read from their text plus the page image, as in the base profile.
    """

    cfg = pipeline.config.quality
    if pipeline.pdf_path is None:
        raise ValueError("visual_routing requires pdf_path and page regions")
    saved = pipeline._load("quality_routes")
    if saved is not None:
        routes = [PageRoute.model_validate(r) for r in saved]
    else:
        vision, index = pipeline.role_clients["vision"], pipeline.source_index
        routes = await classify_visual_pages(
            vision, pipeline.pdf_path, pipeline.doc, index, cfg, pipeline.workdir, state=pipeline.run_state
        )
        for route in routes:
            textless = not pipeline.doc.pages.get(route.page)
            if route.relevance == "DIAGNOSTIC" and "VISUAL_REVIEW" in route.routes and textless:
                try:
                    await read_visual_structure(
                        vision,
                        pipeline.pdf_path,
                        pipeline.doc,
                        index,
                        route,
                        pipeline.workdir,
                        state=pipeline.run_state,
                    )
                except Exception as exc:
                    index.dispositions.append(
                        {"reason": "VISUAL_LAYOUT_FAILED", "page": route.page, "error": type(exc).__name__}
                    )
        pipeline.run_state.revise_index(index, {"stage": "visual_catalog"})
        pipeline._save("quality_routes", [r.model_dump(mode="json") for r in routes])
    pipeline.images = QualityImages(
        pipeline.pdf_path, pipeline.doc, pipeline.source_index, max_images=cfg.max_images_per_request
    )
    return routes


def start_coverage(pipeline, page_map, units, extractions, proposals, relations) -> None:
    """Observed items of the read pages. Mentions are rebound also when stages were reloaded."""

    by_unit = {u.unit_id: u for u in units}
    for proposal in proposals:
        bind_proposal(pipeline.source_index, pipeline.doc, proposal, by_unit.get(proposal.unit_id))
    ledger = inventory(pipeline.source_index, pipeline.doc, page_map, units, extractions)
    pipeline.coverage = update_coverage(ledger, pipeline.source_index, relations)


async def completeness_review(pipeline, units, relations, plan: MergePlan, checker):
    """Review missing items; judge only the merge pairs the review created."""

    relations, pipeline.coverage = await pipeline._timed(
        "quality_review", review_quality(pipeline, units, relations, pipeline.coverage, checker)
    )
    judged = {(p.left, p.right) for p in [*plan.same, *plan.unsure, *plan.different]}
    pairs = [p for p in merge_candidates(relations) if (p.left, p.right) not in judged]
    name = "quality_merge_" + digest([r.assertion.fact_fingerprint for r in relations])[:24]
    saved = pipeline._load(name)
    if saved is not None:
        return relations, MergePlan.model_validate(saved)
    extra = await judge_pairs(pipeline.role_clients["review"], pairs, pipeline.doc, relations) if pairs else MergePlan()
    plan = MergePlan(
        same=[*plan.same, *extra.same],
        unsure=[*plan.unsure, *extra.unsure],
        different=[*plan.different, *extra.different],
        deferred=[*plan.deferred, *extra.deferred],
    )
    pipeline._save(name, plan)
    return relations, plan


def finalize(pipeline, graph, relations) -> None:
    """Coverage of the final relations, reviewed scopes, mandatory validation and artifacts."""

    index = pipeline.source_index
    pipeline.coverage = update_coverage(pipeline.coverage, index, relations)
    # A branch a person or agent confirmed against its source is a verified scope.
    for relation in relations:
        cert = relation.assertion.certificate
        branch = index.branches.get(relation.assertion.branch_id)
        reviewed = cert.confirmed_by and cert.confirmed_by.kind in {ReviewerKind.HUMAN, ReviewerKind.AGENT}
        if branch and reviewed and not cert.validation_issues and cert.scope_status == "VERIFIED_REVIEW":
            index.branches[branch.branch_id] = branch.model_copy(update={"scope_status": "VERIFIED_REVIEW"})
    pipeline.validation = validate_quality(graph, relations, index, pipeline.doc, pipeline.coverage)
    pipeline.run_state.revise_index(index, {"stage": "final"})
    if pipeline.workdir:
        atomic_json(pipeline.workdir / "coverage.json", pipeline.coverage)
        atomic_json(pipeline.workdir / "review_requests.json", pipeline.coverage.requests)
