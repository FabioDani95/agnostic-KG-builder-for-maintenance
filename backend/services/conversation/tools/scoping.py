"""Scoping-phase tools: propose, edit and approve the cut plan.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

import asyncio
from typing import Any

from backend.services.conversation.tools.common import (
    _visible_sections_for_widget,
)


async def _propose_cut_plan(args, store, on_event):
    from backend.app_config import get_agent_config
    from backend.models import CutPlanRequest
    from backend.services.scoping_workflow import create_cut_plan_workflow

    if store.get("_scoping_in_progress"):
        return {"status": "in_progress", "message": "Scoping is already in progress."}
    store["_scoping_in_progress"] = True
    try:
        # None → the workflow autodetects the printed-page offset from the
        # document; an explicit store value (set via the start-request override)
        # is passed through untouched.
        req = CutPlanRequest(
            pdf_id=store["pdf_id"],
            page_offset=store.get("page_offset"),
            model_name=(store.get("selected_models") or {}).get("scoping") or None,
            reasoning_effort=get_agent_config("scoping").get("reasoning_effort"),
        )
        result = await asyncio.to_thread(create_cut_plan_workflow, store, req, on_event)
        # Persist cut plan in store
        from backend.graph.store import set_run_progress, update_scoping_state
        update_scoping_state(store, result, model_name=str(req.model_name or ""))
        # The pipeline now waits for the operator to approve the selection; the
        # console banner keys off run_status/next_step to say so explicitly.
        set_run_progress(store, run_status="awaiting_operator", next_step="approve_cut_plan")

        all_sections = [
            {
                "name": s.name,
                "start": s.page_range.start,
                "end": s.page_range.end,
                "source": s.source,
            }
            for s in result.sections
        ]
        visible_sections = _visible_sections_for_widget(all_sections)
        keyword_section_count = len(all_sections) - len(visible_sections)
        return {
            "status": "ok",
            "sections": visible_sections,
            "pages_to_keep": result.pages_to_keep,
            "total_pages": result.total_pages,
            "keyword_fallback_sections": keyword_section_count,
            "skipped": result.skipped,
            "product_info": result.product_info.model_dump() if result.product_info else None,
            "widget": "sections",
        }
    finally:
        store.pop("_scoping_in_progress", None)


async def _edit_cut_plan(args, store, on_event):
    cut_plan = store.get("cut_plan") or {}
    sections = list(cut_plan.get("sections") or [])

    total_pages = int(
        cut_plan.get("total_pages")
        or (store.get("graph_state") or {}).get("total_pages")
        or len(store.get("pages") or [])
        or 0
    )

    remove_names = {n.lower() for n in (args.get("remove_section_names") or [])}
    if remove_names:
        sections = [s for s in sections if s.get("name", "").lower() not in remove_names]

    rejected_adds: list[dict[str, Any]] = []
    accepted_adds: list[dict[str, Any]] = []
    for new_sec in (args.get("add_sections") or []):
        name = str(new_sec.get("name") or "").strip()
        try:
            start = int(new_sec.get("start_page"))
            end = int(new_sec.get("end_page"))
        except (TypeError, ValueError):
            start = end = 0
        reason = None
        if not name:
            reason = "missing section name"
        elif start <= 0 or end <= 0:
            reason = "missing or invalid page range (start_page and end_page must be >= 1)"
        elif end < start:
            reason = f"end_page ({end}) is smaller than start_page ({start})"
        elif total_pages and (start > total_pages or end > total_pages):
            reason = f"page range {start}-{end} exceeds total_pages ({total_pages})"

        if reason:
            rejected_adds.append({"name": name or "(unnamed)", "start": start, "end": end, "reason": reason})
            continue

        accepted_adds.append({
            "name": name,
            "start": start,
            "end": end,
            "source": "human",
        })

    sections.extend(accepted_adds)

    if rejected_adds and not accepted_adds and not remove_names:
        details = "; ".join(f"{r['name']} ({r['reason']})" for r in rejected_adds)
        return {
            "status": "refused",
            "widget": "sections",
            "sections": _visible_sections_for_widget(sections),
            "pages_to_keep": cut_plan.get("pages_to_keep") or [],
            "total_pages": total_pages,
            "keyword_fallback_sections": len(sections) - len(_visible_sections_for_widget(sections)),
            "product_info": cut_plan.get("product_info"),
            "rejected_adds": rejected_adds,
            "message": (
                f"I couldn't add the section(s) because: {details}. "
                "Please tell me the absolute PDF page range (e.g. \"Errors, pages 42 to 58\") and I'll retry."
            ),
        }

    cut_plan["sections"] = sections
    pages_to_keep = set()
    for sec in sections:
        pages_to_keep.update(range(int(sec["start"]), int(sec["end"]) + 1))
    cut_plan["pages_to_keep"] = sorted(pages_to_keep)
    store["cut_plan"] = cut_plan

    visible_sections = _visible_sections_for_widget(sections)
    payload: dict[str, Any] = {
        "status": "ok",
        "sections": visible_sections,
        "pages_to_keep": cut_plan["pages_to_keep"],
        "total_pages": total_pages,
        "keyword_fallback_sections": len(sections) - len(visible_sections),
        "product_info": cut_plan.get("product_info"),
        "widget": "sections",
    }
    if rejected_adds:
        details = "; ".join(f"{r['name']} ({r['reason']})" for r in rejected_adds)
        payload["rejected_adds"] = rejected_adds
        payload["message"] = (
            f"Applied {len(accepted_adds)} addition(s). Skipped: {details}. "
            "Give me the page range for the skipped section(s) to retry."
        )
    return payload


async def _approve_cut_plan(args, store, on_event):
    from backend.graph.store import update_cut_plan_approval
    from backend.models import CutPlanApproval
    from backend.services.scoping_workflow import approve_cut_plan_workflow

    cut_plan = store.get("cut_plan") or {}
    pages_to_keep = cut_plan.get("pages_to_keep") or [p["page_number"] for p in store.get("pages", [])]
    page_offset = cut_plan.get("page_offset")
    if page_offset is None:
        page_offset = store.get("page_offset", 0)

    sections_raw = cut_plan.get("sections") or []
    from backend.models import CutPlanApprovalSection, PageRange
    sections = []
    for s in sections_raw:
        try:
            sections.append(CutPlanApprovalSection(
                name=s.get("name", "Section"),
                page_range=PageRange(start=s.get("start", 1), end=s.get("end", 1)),
                source=s.get("source", "human"),
            ))
        except Exception:
            pass

    req = CutPlanApproval(
        pdf_id=store["pdf_id"],
        pages_to_keep=pages_to_keep,
        page_offset=page_offset,
        sections=sections,
    )
    approve_cut_plan_workflow(store, req)
    update_cut_plan_approval(
        store,
        pages_to_keep=pages_to_keep,
        page_offset=page_offset,
        sections=sections_raw,
    )
    from backend.graph.state import GraphPhase
    from backend.graph.store import ensure_graph_state, persist_graph_state, set_run_progress
    # approve_cut_plan chains draft_ontology (ACTION_CHAIN), so the run is
    # actively working again right after the approval.
    state = ensure_graph_state(store, pdf_id=store.get("pdf_id"))
    state["current_phase"] = GraphPhase.ONTOLOGY_DRAFT.value
    persist_graph_state(store, state)
    set_run_progress(store, run_status="in_progress", next_step="draft_ontology")
    return {
        "status": "ok",
        "pages_approved": len(pages_to_keep),
        "message": f"Section selection approved — {len(pages_to_keep)} pages will be processed.",
    }
