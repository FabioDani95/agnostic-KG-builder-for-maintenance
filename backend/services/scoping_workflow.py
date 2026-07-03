"""Reusable scoping workflow used by the multi-agent pipeline."""

from __future__ import annotations

import json
import logging
import time

from backend.app_config import (
    get_effective_small_doc_threshold,
    get_scoping_config,
)
from backend.models import (
    CutPlan,
    CutPlanApproval,
    CutPlanRequest,
    PageRange,
    ProductInfo,
    SectionInfo,
    StructuredToc,
    TocEntry,
)
from backend.prompts.scoping_prompt import (
    build_product_id_prompt,
    build_section_selection_prompt,
    build_toc_extraction_prompt,
)
from backend.services.cutplan_service import (
    extract_asset_identity,
    filter_llm_sections,
    filter_pages_by_language,
    find_toc_pages,
    is_component_inventory_section,
    keyword_scan,
    merge_sections,
    normalize_product_info,
    sections_to_page_list,
    select_toc_sections,
)
from backend.services.llm_service import call_openai_scoping
from backend.services.pdf_service import format_text_with_pages
from backend.services.run_metrics import record_stage_metrics, summarize_stage

logger = logging.getLogger(__name__)


def _clean_json(raw: str) -> str:
    """Strip markdown fences from LLM output."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    return cleaned.strip()


def _parse_toc_response(raw: str) -> tuple[list[TocEntry], dict]:
    """Parse LLM ToC extraction response into (toc_entries, product_info_raw)."""
    try:
        data = json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        logger.warning("Failed to parse ToC extraction response: %s", raw[:200])
        return [], {}

    if not isinstance(data, dict):
        return [], {}

    product_info = data.get("product_info", {})

    entries: list[TocEntry] = []
    for item in data.get("toc_entries", []):
        try:
            entries.append(TocEntry(
                title=str(item.get("title", "")),
                manual_page=int(item["page"]),
            ))
        except (KeyError, ValueError, TypeError):
            continue

    return entries, product_info


def _parse_section_response(
    raw: str,
    page_offset: int,
    total_pages: int,
) -> list[SectionInfo]:
    """Parse LLM section selection response and convert manual pages to absolute pages."""
    try:
        data = json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        logger.warning("Failed to parse section selection response: %s", raw[:200])
        return []

    if not isinstance(data, dict):
        return []

    sections: list[SectionInfo] = []
    for item in data.get("sections", []):
        try:
            manual_start = int(item["manual_page_start"])
            manual_end = int(item["manual_page_end"])
            abs_start = max(1, min(manual_start + page_offset, total_pages))
            abs_end = max(abs_start, min(manual_end + page_offset, total_pages))
            sections.append(SectionInfo(
                name=str(item.get("name", "Unnamed section")),
                page_range=PageRange(start=abs_start, end=abs_end),
                manual_page_range=PageRange(start=manual_start, end=manual_end),
                source="llm",
                reasoning=str(item.get("reasoning", "")),
            ))
        except (KeyError, ValueError, TypeError):
            continue

    return sections


def create_cut_plan_workflow(store: dict, req: CutPlanRequest, on_event=None) -> CutPlan:
    """Run the cut-plan flow against one in-memory store entry."""
    t0 = time.perf_counter()
    cfg = get_scoping_config()
    small_doc_threshold = get_effective_small_doc_threshold()
    timeout_seconds = cfg.get("timeout_seconds", 120)

    pages = store["pages"]
    total_pages = len(pages)
    page_offset = req.page_offset
    scoping_usage_entries: list[dict] = []

    logger.info(
        "[scoping] Start — %d pages, offset=%d, timeout=%ds",
        total_pages,
        page_offset,
        timeout_seconds,
    )
    if on_event:
        on_event({"type": "progress", "phase": "scoping",
                  "message": f"Scoping started — {total_pages} pages to analyze."})

    if total_pages <= small_doc_threshold:
        logger.info(
            "[scoping] Small doc (%d <= %d), skipping (%.1fs)",
            total_pages,
            small_doc_threshold,
            time.perf_counter() - t0,
        )
        record_stage_metrics(
            store,
            "scoping",
            summarize_stage(
                "scoping",
                t0,
                [],
                details={
                    "total_pages": total_pages,
                    "selected_pages": total_pages,
                    "selected_sections": 0,
                    "skipped": True,
                    "page_offset": page_offset,
                },
            ),
        )
        return CutPlan(
            pdf_id=req.pdf_id,
            total_pages=total_pages,
            sections=[],
            pages_to_keep=[p["page_number"] for p in pages],
            page_offset=page_offset,
            skipped=True,
        )

    toc_found, toc_text, toc_start, toc_end = find_toc_pages(pages)
    logger.info(
        "[scoping] 1/4 ToC %s (%.1fs)",
        f"found pp.{toc_start}-{toc_end}" if toc_found else "not found",
        time.perf_counter() - t0,
    )
    if on_event:
        toc_msg = (f"Table of contents found on pages {toc_start}–{toc_end}."
                   if toc_found else "No table of contents detected — using keyword scan.")
        on_event({"type": "progress", "phase": "scoping", "message": toc_msg})

    structured_toc = None
    product_info = None
    llm_sections: list[SectionInfo] = []
    rule_sections: list[SectionInfo] = []

    if toc_found and toc_text:
        first_pages = [p for p in pages if p["page_number"] <= 5]
        first_pages_text = format_text_with_pages(first_pages)

        toc_prompt = build_toc_extraction_prompt(
            toc_start_page=toc_start,
            toc_end_page=toc_end,
            total_pages=total_pages,
            toc_text=toc_text,
            first_pages_text=first_pages_text,
        )

        try:
            raw_toc, usage1 = call_openai_scoping(
                toc_prompt,
                model_name=req.model_name,
                timeout=timeout_seconds,
            )
            scoping_usage_entries.append(usage1)
            toc_entries, product_info_raw = _parse_toc_response(raw_toc)
            logger.info(
                "[scoping] 2/4 ToC extracted — %d entries, tokens=%s (%.1fs)",
                len(toc_entries),
                usage1,
                time.perf_counter() - t0,
            )

            if toc_entries:
                structured_toc = StructuredToc(
                    entries=toc_entries,
                    toc_start_page=toc_start,
                    toc_end_page=toc_end,
                )

                if product_info_raw:
                    normalized_product_info = normalize_product_info(
                        product_info_raw,
                        filename=store.get("filename", ""),
                    )
                    product_info = ProductInfo(
                        product_name=normalized_product_info.get("product_name", ""),
                        product_short_name=normalized_product_info.get("product_short_name", ""),
                        brand=normalized_product_info.get("brand", ""),
                        model=normalized_product_info.get("model", ""),
                        asset_id=normalized_product_info.get("asset_id", ""),
                        asset_type=normalized_product_info.get("asset_type", ""),
                        document_type=normalized_product_info.get("document_type", ""),
                        language=normalized_product_info.get("language", ""),
                        page_count=total_pages,
                    )
                    store["source_type"] = product_info.document_type
                    store["source_title"] = product_info.product_name
                    store["asset_identity"] = extract_asset_identity(
                        normalized_product_info,
                        fallback_name=product_info.product_name,
                        source_type=product_info.document_type,
                        filename=store.get("filename", ""),
                    )

                rule_sections = select_toc_sections(
                    toc_entries=toc_entries,
                    page_offset=page_offset,
                    total_pages=total_pages,
                )

                toc_json = json.dumps([e.model_dump() for e in toc_entries], indent=2)
                selection_prompt = build_section_selection_prompt(toc_json)

                raw_sel, usage2 = call_openai_scoping(
                    selection_prompt,
                    model_name=req.model_name,
                    timeout=timeout_seconds,
                )
                scoping_usage_entries.append(usage2)
                llm_sections = filter_llm_sections(_parse_section_response(
                    raw_sel,
                    page_offset,
                    total_pages,
                ))
                logger.info(
                    "[scoping] 3/4 Sections selected — rule=%d llm=%d, tokens=%s (%.1fs)",
                    len(rule_sections),
                    len(llm_sections),
                    usage2,
                    time.perf_counter() - t0,
                )
                for section in rule_sections:
                    logger.info(
                        "[scoping]   rule: %s pp.%d-%d (score check passed)",
                        section.name,
                        section.page_range.start,
                        section.page_range.end,
                    )
                for section in llm_sections:
                    logger.info(
                        "[scoping]   llm: %s pp.%d-%d",
                        section.name,
                        section.page_range.start,
                        section.page_range.end,
                    )
        except Exception:
            logger.exception(
                "[scoping] LLM scoping call FAILED, falling back to keywords (%.1fs)",
                time.perf_counter() - t0,
            )

    if not product_info:
        try:
            first_pages = [p for p in pages if p["page_number"] <= 5]
            first_pages_text = format_text_with_pages(first_pages)
            product_id_prompt = build_product_id_prompt(first_pages_text)
            raw_pid, usage_pid = call_openai_scoping(
                product_id_prompt,
                model_name=req.model_name,
                timeout=timeout_seconds,
            )
            scoping_usage_entries.append(usage_pid)
            try:
                pid_data = json.loads(raw_pid.strip())
            except Exception:
                import re as _re
                match = _re.search(r"\{.*\}", raw_pid, _re.DOTALL)
                pid_data = json.loads(match.group(0)) if match else {}
            if pid_data:
                normalized_pid = normalize_product_info(
                    pid_data,
                    filename=store.get("filename", ""),
                )
                product_info = ProductInfo(
                    product_name=normalized_pid.get("product_name", ""),
                    product_short_name=normalized_pid.get("product_short_name", ""),
                    brand=normalized_pid.get("brand", ""),
                    model=normalized_pid.get("model", ""),
                    asset_id=normalized_pid.get("asset_id", ""),
                    asset_type=normalized_pid.get("asset_type", ""),
                    document_type=normalized_pid.get("document_type", ""),
                    language=normalized_pid.get("language", ""),
                    page_count=total_pages,
                )
                store["source_type"] = product_info.document_type
                store["source_title"] = product_info.product_name
                store["asset_identity"] = extract_asset_identity(
                    normalized_pid,
                    fallback_name=product_info.product_name,
                    source_type=product_info.document_type,
                    filename=store.get("filename", ""),
                )
                logger.info(
                    "[scoping] Product identified from first pages: %s",
                    product_info.product_name,
                )
        except Exception:
            logger.warning(
                "[scoping] Product identification from first pages failed — using filename",
            )

    kw_sections = keyword_scan(pages)
    logger.info(
        "[scoping] Keyword scan — %d sections found across %d pages",
        len(kw_sections),
        total_pages,
    )
    if on_event:
        on_event({"type": "progress", "phase": "scoping",
                  "message": f"Keyword scan complete — {len(kw_sections)} section(s) identified."})
    for section in kw_sections:
        logger.info(
            "[scoping]   keyword: %s pp.%d-%d",
            section.name,
            section.page_range.start,
            section.page_range.end,
        )

    if not llm_sections and not rule_sections:
        merged = merge_sections([], [], kw_sections)
        logger.info(
            "[scoping] Fallback keyword scan — %d sections (%.1fs)",
            len(merged),
            time.perf_counter() - t0,
        )
        for section in kw_sections:
            logger.info(
                "[scoping]   keyword: %s pp.%d-%d",
                section.name,
                section.page_range.start,
                section.page_range.end,
            )
    else:
        merged = merge_sections(rule_sections, llm_sections, kw_sections)

    all_pages = sections_to_page_list(merged)
    filtered_pages = filter_pages_by_language(pages, all_pages)
    component_pages = sections_to_page_list([
        section for section in merged
        if is_component_inventory_section(section.name)
    ])
    restored_component_pages = sorted(set(component_pages) - set(filtered_pages))
    if restored_component_pages:
        logger.info(
            "[scoping] 4/4 Restoring %d component pages removed by language filter",
            len(restored_component_pages),
        )
        filtered_pages = sorted(set(filtered_pages) | set(restored_component_pages))

    if len(filtered_pages) < len(all_pages) * 0.5:
        logger.info(
            "[scoping] 4/4 Language filter too aggressive (%d→%d), skipping",
            len(all_pages),
            len(filtered_pages),
        )
        filtered_pages = all_pages
    else:
        logger.info(
            "[scoping] 4/4 Language filter: %d→%d pages (%.1fs)",
            len(all_pages),
            len(filtered_pages),
            time.perf_counter() - t0,
        )

    if not filtered_pages:
        filtered_pages = [p["page_number"] for p in pages]

    record_stage_metrics(
        store,
        "scoping",
        summarize_stage(
            "scoping",
            t0,
            scoping_usage_entries,
            details={
                "total_pages": total_pages,
                "selected_pages": len(filtered_pages),
                "selected_sections": len(merged),
                "skipped": False,
                "page_offset": page_offset,
            },
        ),
    )

    logger.info(
        "[scoping] Done — %d sections, %d pages to keep out of %d (%.1fs)",
        len(merged),
        len(filtered_pages),
        total_pages,
        time.perf_counter() - t0,
    )
    if on_event:
        on_event({"type": "progress", "phase": "scoping",
                  "message": f"Scoping done — {len(merged)} section(s), {len(filtered_pages)}/{total_pages} pages selected."})

    store["cut_plan"] = {
        "pdf_id": req.pdf_id,
        "total_pages": total_pages,
        "sections": [
            {
                "name": section.name,
                "start": section.page_range.start,
                "end": section.page_range.end,
                "source": section.source,
            }
            for section in merged
        ],
        "pages_to_keep": filtered_pages,
        "page_offset": page_offset,
        "toc": structured_toc.model_dump() if structured_toc else None,
        "skipped": False,
        "product_info": product_info.model_dump() if product_info else None,
    }
    if product_info:
        store["asset_identity"] = extract_asset_identity(
            product_info.model_dump(),
            fallback_name=product_info.product_name,
            source_type=product_info.document_type,
            filename=store.get("filename", ""),
        )

    return CutPlan(
        pdf_id=req.pdf_id,
        total_pages=total_pages,
        sections=merged,
        pages_to_keep=filtered_pages,
        page_offset=page_offset,
        toc=structured_toc,
        product_info=product_info,
    )


def approve_cut_plan_workflow(store: dict, req: CutPlanApproval) -> dict[str, str]:
    """Persist the operator-approved cut plan to the store."""
    sections_for_store = [
        {
            "name": section.name,
            "start": section.page_range.start,
            "end": section.page_range.end,
            "source": section.source,
        }
        for section in req.sections
    ] if req.sections else store.get("cut_plan", {}).get("sections", [])

    store["cut_plan"] = {
        "pages_to_keep": sorted(req.pages_to_keep),
        "page_offset": req.page_offset,
        "sections": sections_for_store,
    }
    return {"status": "ok"}
