import logging

from httpx import Timeout

from backend.app_config import get_extraction_config, get_scoping_config
from backend.config import settings
from backend.models import (
    ExtractionResult,
)
from backend.prompts.extraction_prompt import (
    build_existing_id_catalog_block,
    build_extraction_prompt,
    build_seed_rows_block,
)
from backend.services.extraction_grounding_filters import (  # noqa: F401  (re-exported)
    _filter_extraction_result_by_source_support,
    _fragment_supported_by_page,
    _normalize_action_against_source,
)
from backend.services.extraction_merge import (
    _merge_extraction_results,
    _promote_misclassified_failure_modes,
)
from backend.services.extraction_parsing import parse_extraction
from backend.services.llm_gateway import chat_reasoning_kwargs, chat_temperature_kwargs, get_client
from backend.services.llm_guardrails import (
    enforce_llm_limits,
    llm_timeout_message,
    resolve_guardrails,
)
from backend.services.run_metrics import aggregate_usage, usage_from_response

logger = logging.getLogger(__name__)


def call_openai_scoping(
    prompt_text: str,
    model_name: str | None = None,
    timeout: int | None = None,
    reasoning_effort: str | None = None,
) -> tuple[str, dict]:
    """Send scoping/cut-plan request to OpenAI and return (raw_response, token_usage)."""
    cfg = resolve_guardrails(
        get_scoping_config(),
        default_timeout=120,
        default_max_output_tokens=2200,
    )
    if timeout is not None:
        cfg["timeout_seconds"] = timeout
    enforce_llm_limits(
        phase="Scoping",
        cfg=cfg,
        system_text=prompt_text,
    )

    client = get_client(timeout=Timeout(cfg["timeout_seconds"], connect=10.0), max_retries=0)
    try:
        resolved_model = model_name or settings.MODEL_NAME
        response = client.chat.completions.create(
            model=resolved_model,
            **chat_reasoning_kwargs(resolved_model, reasoning_effort),
            messages=[
                {"role": "system", "content": prompt_text},
            ],
            **chat_temperature_kwargs(resolved_model, 0.0),
            max_completion_tokens=cfg["max_output_tokens"],
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "timeout" in msg:
            raise RuntimeError(llm_timeout_message("Scoping", cfg["timeout_seconds"])) from exc
        raise RuntimeError(f"Scoping failed before completion: {exc}") from exc
    usage = usage_from_response(response, "scoping")
    logger.info("[llm] Scoping call — model=%s, tokens=%s",
                response.model, usage)
    return response.choices[0].message.content, usage


def call_openai(
    text_with_pages: str,
    source_type: str,
    source_title: str,
    target_language: str,
    model_name: str | None = None,
    timeout: int | None = None,
    section_context: str = "",
    ontology_draft: dict | None = None,
) -> tuple[str, dict]:
    """Send extraction request to OpenAI and return (raw_response, token_usage)."""
    cfg = resolve_guardrails(
        get_extraction_config(),
        default_timeout=300,
        default_max_output_tokens=6500,
    )
    if timeout is not None:
        cfg["timeout_seconds"] = timeout

    system_prompt = build_extraction_prompt(
        source_type,
        source_title,
        existing_id_catalog_block=build_existing_id_catalog_block(ontology_draft),
        seed_rows_block=build_seed_rows_block(ontology_draft),
    )

    # Build user message: section context header + page text
    user_message = text_with_pages
    if section_context:
        user_message = section_context + "\n\n" + text_with_pages

    enforce_llm_limits(
        phase="Extraction",
        cfg=cfg,
        system_text=system_prompt,
        user_text=user_message,
    )
    client = get_client(timeout=Timeout(cfg["timeout_seconds"], connect=10.0))
    try:
        resolved_model = model_name or settings.MODEL_NAME
        response = client.chat.completions.create(
            model=resolved_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            **chat_temperature_kwargs(resolved_model, 0.0),
            max_completion_tokens=cfg["max_output_tokens"],
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "timeout" in msg:
            raise RuntimeError(llm_timeout_message("Extraction", cfg["timeout_seconds"])) from exc
        raise RuntimeError(f"Extraction failed before completion: {exc}") from exc
    usage = usage_from_response(response, "extraction")
    logger.info("[llm] Extraction call — model=%s, tokens=%s",
                response.model, usage)
    return response.choices[0].message.content, usage


def _split_page_chunks(pages: list[dict], max_pages: int, overlap: int, max_chars: int) -> list[list[dict]]:
    if not pages:
        return []

    pages_sorted = sorted(pages, key=lambda item: item["page_number"])
    runs: list[list[dict]] = []
    current_run = [pages_sorted[0]]

    for page in pages_sorted[1:]:
        if page["page_number"] == current_run[-1]["page_number"] + 1:
            current_run.append(page)
        else:
            runs.append(current_run)
            current_run = [page]
    runs.append(current_run)

    chunks: list[list[dict]] = []
    safe_max_pages = max(1, max_pages)
    safe_overlap = max(0, min(overlap, safe_max_pages - 1))

    for run in runs:
        start = 0
        while start < len(run):
            end = min(start + safe_max_pages, len(run))
            chunk = run[start:end]

            while len(chunk) > 1:
                chunk_text = "\n\n".join(
                    [f"--- PAGE {page['page_number']} ---\n{page['text']}" for page in chunk]
                )
                if len(chunk_text) <= max_chars:
                    break
                end -= 1
                chunk = run[start:end]

            chunks.append(chunk)
            if end >= len(run):
                break
            start = max(start + 1, end - safe_overlap)

    return chunks


def _build_section_context(chunk_pages: list[dict], sections: list[dict]) -> str:
    """Build a section context header for a chunk based on which sections overlap its pages."""
    if not sections:
        return ""
    chunk_page_nums = {p["page_number"] for p in chunk_pages}
    matching: list[str] = []
    for s in sections:
        section_pages = set(range(s["start"], s["end"] + 1))
        if section_pages & chunk_page_nums:
            matching.append(f"- {s['name']} (pp. {s['start']}-{s['end']}, source: {s.get('source', '?')})")
    if not matching:
        return ""
    header = "## DOCUMENT CONTEXT\n"
    header += "The pages below belong to the following manual sections:\n"
    header += "\n".join(matching)
    header += "\n\nUse this context to better interpret the content. "
    header += "Focus extraction on diagnostic information relevant to these sections."
    return header


def extract_triplets_chunked(
    pages: list[dict],
    source_type: str,
    source_title: str,
    target_language: str,
    model_name: str | None = None,
    sections: list[dict] | None = None,
    ontology_draft: dict | None = None,
    on_event=None,
    hint: str = "",
) -> ExtractionResult:
    cfg = get_extraction_config()
    chunks = _split_page_chunks(
        pages=pages,
        max_pages=int(cfg.get("chunk_max_pages", 4)),
        overlap=int(cfg.get("chunk_page_overlap", 1)),
        max_chars=int(cfg.get("chunk_max_chars", 12000)),
    )

    if not chunks:
        empty = ExtractionResult(
            triplets=[],
            raw_symptom_table="",
            raw_failure_mode_table="",
            raw_corrective_action_table="",
        )
        return empty, {
            "chunk_count": 0,
            **aggregate_usage([]),
        }

    logger.info("[extraction] Split %d pages into %d chunk(s)", len(pages), len(chunks))
    if on_event:
        on_event({
            "type": "progress",
            "phase": "extraction",
            "message": f"Starting extraction: {len(pages)} pages split into {len(chunks)} chunk(s).",
            "total_chunks": len(chunks),
            "current_chunk": 0,
        })

    chunk_results: list[ExtractionResult] = []
    usage_entries: list[dict] = []

    for idx, chunk in enumerate(chunks, start=1):
        text_with_pages = "\n\n".join(
            [f"--- PAGE {page['page_number']} ---\n{page['text']}" for page in chunk]
        )
        section_context = _build_section_context(chunk, sections or [])
        if hint:
            hint_block = (
                "## OPERATOR HINT\n"
                f"The operator expects to find the following in these pages: {hint}\n"
                "Prioritize extracting diagnostic information related to this hint, "
                "but do not invent content that is not supported by the page text."
            )
            section_context = f"{section_context}\n\n{hint_block}" if section_context else hint_block
        page_text_by_page = {page["page_number"]: page["text"] for page in chunk}
        raw_response, usage = call_openai(
            text_with_pages=text_with_pages,
            source_type=source_type,
            source_title=source_title,
            target_language=target_language,
            model_name=model_name,
            section_context=section_context,
            ontology_draft=ontology_draft,
        )
        usage_entries.append(usage)
        parsed = parse_extraction(raw_response, source_type, source_title)
        parsed = _promote_misclassified_failure_modes(parsed)
        parsed = _filter_extraction_result_by_source_support(
            parsed,
            page_text_by_page,
            drop_incomplete=False,
        )
        triplet_count = len(parsed.triplets)
        logger.info(
            "[extraction] Chunk %d/%d pages=%s-%s → %d triplet(s)",
            idx,
            len(chunks),
            chunk[0]["page_number"],
            chunk[-1]["page_number"],
            triplet_count,
        )
        if on_event:
            on_event({
                "type": "progress",
                "phase": "extraction",
                "message": (
                    f"Chunk {idx}/{len(chunks)}, "
                    f"pages {chunk[0]['page_number']}–{chunk[-1]['page_number']} "
                    f"→ {triplet_count} triplet(s)."
                ),
                "total_chunks": len(chunks),
                "current_chunk": idx,
                "triplets_in_chunk": triplet_count,
            })
        chunk_results.append(parsed)

    merged = _merge_extraction_results(chunk_results)
    logger.info("[extraction] Merged chunk results → %d triplet(s)", len(merged.triplets))
    if on_event:
        on_event({
            "type": "progress",
            "phase": "extraction",
            "message": f"Extraction complete — {len(merged.triplets)} triplet(s) found.",
            "total_chunks": len(chunks),
            "current_chunk": len(chunks),
            "total_triplets": len(merged.triplets),
        })
    return merged, {
        "chunk_count": len(chunks),
        **aggregate_usage(usage_entries),
    }
