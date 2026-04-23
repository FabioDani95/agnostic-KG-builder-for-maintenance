import logging
import re
from collections import OrderedDict
from difflib import SequenceMatcher

from httpx import Timeout
from openai import OpenAI

from backend.config import settings
from backend.models import (
    Symptom, FailureMode, CorrectiveAction, Triplet,
    ExtractionResult, Severity,
)
from backend.prompts.extraction_prompt import (
    build_existing_id_catalog_block,
    build_extraction_prompt,
    build_seed_rows_block,
)
from backend.app_config import get_scoping_config, get_extraction_config
from backend.services.llm_guardrails import (
    enforce_llm_limits,
    llm_timeout_message,
    resolve_guardrails,
)
from backend.services.run_metrics import aggregate_usage, usage_from_response
from backend.services.ontology_semantics import (
    build_semantic_key,
    corrective_actions_match,
    failure_modes_match,
    informative_instruction_steps,
    instruction_steps,
    is_corrective_action_candidate,
    is_failure_mode_candidate,
    normalize_semantic_text,
    prefer_more_informative_text,
    semantic_tokens,
    semantically_equivalent,
    symptoms_match,
)

logger = logging.getLogger(__name__)
_PAGE_TEXT_SEGMENT_RE = re.compile(r"[\n.;:]+")
_LOW_SIGNAL_ACTION_STEP_RE = re.compile(
    r"(?i)^\s*("
    r"verify\b.*(?:fault|problem|issue).*(?:fixed|resolved)|"
    r"verify\b.*(?:repair|replacement|action)|"
    r"restart this guide(?: if necessary)?|"
    r"refer to (?:the )?plant documentation.*"
    r")\s*$"
)


def call_openai_scoping(
    prompt_text: str,
    model_name: str | None = None,
    timeout: int | None = None,
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

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=Timeout(cfg["timeout_seconds"], connect=10.0),
    )
    try:
        response = client.chat.completions.create(
            model=model_name or settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": prompt_text},
            ],
            temperature=0.0,
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
    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=Timeout(cfg["timeout_seconds"], connect=10.0),
    )
    try:
        response = client.chat.completions.create(
            model=model_name or settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.0,
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


def _parse_table_rows(table_text: str) -> list[list[str]]:
    """Parse a Markdown table into a list of row values (excluding header and separator)."""
    lines = [l.strip() for l in table_text.strip().split("\n") if l.strip()]
    rows = []
    for line in lines:
        if line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # Skip separator rows (---|---|---)
            if cells and all(re.match(r"^-+:?$|^:?-+:?$", c) for c in cells):
                continue
            rows.append(cells)
    # First row is header, rest are data
    return rows


def _split_tables(raw: str) -> tuple[str, str, str]:
    """Split the raw LLM output into three table strings."""
    # Find tables by looking for the header patterns
    symptom_match = re.search(
        r"(\| *symptom_id.*?\n(?:\|.*\n)*)", raw, re.IGNORECASE
    )
    failure_match = re.search(
        r"(\| *failure_mode_id.*?\n(?:\|.*\n)*)", raw, re.IGNORECASE
    )
    action_match = re.search(
        r"(\| *action_id.*?\n(?:\|.*\n)*)", raw, re.IGNORECASE
    )

    return (
        symptom_match.group(1) if symptom_match else "",
        failure_match.group(1) if failure_match else "",
        action_match.group(1) if action_match else "",
    )


def _parse_severity(val: str) -> Severity:
    """Parse severity string, defaulting to Medium if invalid."""
    val_clean = val.strip().capitalize()
    try:
        return Severity(val_clean)
    except ValueError:
        return Severity.MEDIUM


def _parse_page_cell(val: str) -> int:
    match = re.search(r"\d+", str(val or ""))
    if not match:
        return 0
    try:
        return int(match.group(0))
    except ValueError:
        return 0


def parse_extraction(raw: str, source_type: str, source_title: str) -> ExtractionResult:
    """Parse the raw LLM response into structured ExtractionResult."""
    sym_table, fm_table, ca_table = _split_tables(raw)

    # Parse Symptoms
    sym_rows = _parse_table_rows(sym_table)
    symptoms: list[Symptom] = []
    for row in sym_rows[1:]:  # skip header
        if len(row) >= 4:
            evidence_page = _parse_page_cell(row[4]) if len(row) >= 5 else 0
            symptoms.append(Symptom(
                symptom_id=row[0],
                name=row[1],
                description=row[2],
                severity=_parse_severity(row[3]),
                evidence_page=evidence_page,
            ))

    # Parse FailureModes
    fm_rows = _parse_table_rows(fm_table)
    failure_modes: list[FailureMode] = []
    for row in fm_rows[1:]:
        if len(row) >= 5:
            evidence_page = _parse_page_cell(row[5]) if len(row) >= 6 else 0
            failure_modes.append(FailureMode(
                failure_mode_id=row[0],
                name=row[1],
                description=row[2],
                material_context=row[3],
                linked_symptom_id=row[4],
                evidence_page=evidence_page,
            ))

    # Parse CorrectiveActions
    ca_rows = _parse_table_rows(ca_table)
    corrective_actions: list[CorrectiveAction] = []
    for row in ca_rows[1:]:
        if len(row) >= 8:
            try:
                page = int(row[6])
            except ValueError:
                page = 0
            corrective_actions.append(CorrectiveAction(
                action_id=row[0],
                name=row[1],
                description=row[2],
                instruction_text=row[3],
                source_type=row[4] if row[4] else source_type,
                source_title=row[5] if row[5] else source_title,
                source_page=page,
                linked_failure_mode_id=row[7],
            ))

    # Group into triplets
    triplets = _group_into_triplets(symptoms, failure_modes, corrective_actions)

    return ExtractionResult(
        triplets=triplets,
        raw_symptom_table=sym_table,
        raw_failure_mode_table=fm_table,
        raw_corrective_action_table=ca_table,
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _page_text_segments(page_text: str) -> list[str]:
    segments = [
        normalize_semantic_text(segment)
        for segment in _PAGE_TEXT_SEGMENT_RE.split(str(page_text or ""))
    ]
    return [segment for segment in segments if segment]


def _fragment_supported_by_page(fragment: str, page_text: str) -> bool:
    fragment_norm = normalize_semantic_text(fragment)
    page_norm = normalize_semantic_text(page_text)
    if not fragment_norm or not page_norm:
        return False
    if fragment_norm in page_norm:
        return True

    fragment_tokens = set(semantic_tokens(fragment_norm))
    if len(fragment_tokens) < 2:
        return False

    for segment in _page_text_segments(page_text):
        if not segment:
            continue
        if build_semantic_key(fragment_norm) == build_semantic_key(segment):
            return True
        if semantically_equivalent(fragment_norm, segment, min_ratio=0.72, min_overlap=0.66):
            return True
        segment_tokens = set(semantic_tokens(segment))
        if not segment_tokens:
            continue
        overlap = len(fragment_tokens & segment_tokens) / len(fragment_tokens)
        if overlap >= 0.90:
            return True
        if overlap >= 0.68 and SequenceMatcher(a=fragment_norm, b=segment).ratio() >= 0.58:
            return True

    page_tokens = set(semantic_tokens(page_norm))
    if page_tokens:
        overlap = len(fragment_tokens & page_tokens) / len(fragment_tokens)
        return overlap >= 0.92
    return False


def _format_numbered_steps(steps: list[str]) -> str:
    return " ".join(f"{idx}. {step.strip()}" for idx, step in enumerate(steps, start=1) if step.strip())


def _normalize_action_against_source(
    action: CorrectiveAction,
    page_text_by_page: dict[int, str],
) -> CorrectiveAction | None:
    page_text = page_text_by_page.get(action.source_page, "")
    if not page_text:
        return None

    raw_steps = instruction_steps(action.instruction_text)
    informative_steps = informative_instruction_steps(action.instruction_text)
    supported_steps = [step for step in raw_steps if _fragment_supported_by_page(step, page_text)]
    supported_informative_steps = [
        step for step in informative_steps
        if not _LOW_SIGNAL_ACTION_STEP_RE.match(step) and _fragment_supported_by_page(step, page_text)
    ]
    name_supported = _fragment_supported_by_page(action.name, page_text)
    description_supported = _fragment_supported_by_page(action.description, page_text)

    if raw_steps and not supported_informative_steps and not (name_supported and description_supported):
        return None
    if not raw_steps and not (name_supported or description_supported):
        return None

    normalized = action.model_copy(deep=True)
    if supported_steps and len(supported_steps) < len(raw_steps):
        normalized.instruction_text = _format_numbered_steps(supported_steps)
    if supported_informative_steps and not description_supported:
        normalized.description = prefer_more_informative_text(
            normalized.description,
            supported_informative_steps[0],
        )
    return normalized


def _filter_extraction_result_by_source_support(
    result: ExtractionResult,
    page_text_by_page: dict[int, str],
    *,
    drop_incomplete: bool = True,
) -> tuple[ExtractionResult, dict]:
    """Drop CorrectiveActions not supported by their cited source page.

    `drop_incomplete` controls whether a triplet left without a valid
    CorrectiveAction after pruning is discarded (legacy behaviour, default) or
    kept for downstream cross-chunk reconciliation.
    """
    filtered_triplets: list[Triplet] = []
    total_actions = 0
    dropped_actions = 0

    for triplet in result.triplets:
        normalized_actions: list[CorrectiveAction] = []
        for action in triplet.corrective_actions:
            total_actions += 1
            normalized = _normalize_action_against_source(action, page_text_by_page)
            if normalized is None:
                dropped_actions += 1
                continue
            normalized_actions.append(normalized)

        cleaned = _clean_triplet(
            Triplet(
                symptom=triplet.symptom,
                failure_modes=triplet.failure_modes,
                corrective_actions=normalized_actions,
            ),
            require_complete=drop_incomplete,
        )
        if cleaned is not None:
            filtered_triplets.append(cleaned)

    if dropped_actions:
        logger.info(
            "[extraction] Source verification pruned %d/%d corrective action(s)",
            dropped_actions,
            total_actions,
        )

    return ExtractionResult(
        triplets=filtered_triplets,
        raw_symptom_table=result.raw_symptom_table,
        raw_failure_mode_table=result.raw_failure_mode_table,
        raw_corrective_action_table=result.raw_corrective_action_table,
    )


def _severity_rank(value: Severity) -> int:
    order = {
        Severity.LOW: 1,
        Severity.MEDIUM: 2,
        Severity.HIGH: 3,
        Severity.CRITICAL: 4,
    }
    return order.get(value, 0)


def _symptom_key(symptom: Symptom) -> tuple[str, str]:
    return (
        build_semantic_key(symptom.name, symptom.description),
        _normalize_text(symptom.name),
    )


def _failure_mode_key(failure_mode: FailureMode) -> tuple[str, str, str]:
    return (
        build_semantic_key(
            failure_mode.name,
            failure_mode.description,
            failure_mode.material_context,
        ),
        _normalize_text(failure_mode.name),
        _normalize_text(failure_mode.material_context),
    )


def _corrective_action_key(action: CorrectiveAction) -> tuple[str, str, str, int]:
    instruction_signature = " ".join(informative_instruction_steps(action.instruction_text))
    return (
        build_semantic_key(action.name, action.description, instruction_signature or action.instruction_text),
        _normalize_text(action.name),
        _normalize_text(action.source_title),
        action.source_page,
    )


def _format_id(prefix: str, index: int) -> str:
    return f"{prefix}-{index:03d}"


def _merge_symptom_fields(existing: Symptom, candidate: Symptom) -> None:
    existing.name = prefer_more_informative_text(existing.name, candidate.name)
    existing.description = prefer_more_informative_text(existing.description, candidate.description)
    if _severity_rank(candidate.severity) > _severity_rank(existing.severity):
        existing.severity = candidate.severity


def _merge_failure_mode_fields(existing: FailureMode, candidate: FailureMode) -> None:
    existing.name = prefer_more_informative_text(existing.name, candidate.name)
    existing.description = prefer_more_informative_text(existing.description, candidate.description)
    existing.material_context = prefer_more_informative_text(
        existing.material_context,
        candidate.material_context,
    )


def _merge_corrective_action_fields(existing: CorrectiveAction, candidate: CorrectiveAction) -> None:
    existing.name = prefer_more_informative_text(existing.name, candidate.name)
    existing.description = prefer_more_informative_text(existing.description, candidate.description)
    existing.instruction_text = prefer_more_informative_text(
        existing.instruction_text,
        candidate.instruction_text,
    )
    if candidate.source_page and (existing.source_page == 0 or candidate.source_page < existing.source_page):
        existing.source_page = candidate.source_page
    if not existing.source_type and candidate.source_type:
        existing.source_type = candidate.source_type
    if not existing.source_title and candidate.source_title:
        existing.source_title = candidate.source_title


def _find_matching_failure_mode(
    buckets: OrderedDict[tuple[str, str, str], dict],
    candidate: FailureMode,
) -> tuple[str, str, str] | None:
    for key, fm_bucket in buckets.items():
        existing = fm_bucket["failure_mode"]
        if failure_modes_match(
            existing.name,
            existing.description,
            existing.material_context,
            candidate.name,
            candidate.description,
            candidate.material_context,
        ):
            return key
    return None


def _find_matching_action(
    actions: OrderedDict[tuple[str, str, str, int], CorrectiveAction],
    candidate: CorrectiveAction,
) -> tuple[str, str, str, int] | None:
    for key, existing in actions.items():
        if corrective_actions_match(
            existing.name,
            existing.description,
            existing.instruction_text,
            candidate.name,
            candidate.description,
            candidate.instruction_text,
        ):
            return key
    return None


def _clean_triplet(triplet: Triplet, *, require_complete: bool = True) -> Triplet | None:
    """Prune invalid FailureModes and CorrectiveActions from a triplet.

    When `require_complete=True` (default, preserves legacy per-chunk and merge
    semantics), a triplet that ends up without BOTH a valid FailureMode AND a
    valid CorrectiveAction is dropped. When `require_complete=False`, a triplet
    survives as long as it retains at least one valid FailureMode OR one valid
    CorrectiveAction — useful across chunk boundaries where a Symptom may be
    introduced in one chunk and its corrective procedure may live in another.
    """
    valid_failure_modes: list[FailureMode] = []
    valid_actions: list[CorrectiveAction] = []
    kept_failure_mode_ids: set[str] = set()

    for failure_mode in triplet.failure_modes:
        if not is_failure_mode_candidate(
            failure_mode.name,
            failure_mode.description,
            failure_mode.material_context,
        ):
            continue
        valid_failure_modes.append(failure_mode)
        kept_failure_mode_ids.add(failure_mode.failure_mode_id)

    for action in triplet.corrective_actions:
        linked_id = action.linked_failure_mode_id
        link_unresolved = bool(linked_id) and linked_id not in kept_failure_mode_ids
        if require_complete and link_unresolved:
            # Strict mode: drop any CA whose linked FailureMode did not survive.
            continue
        if not is_corrective_action_candidate(
            action.name,
            action.description,
            action.instruction_text,
        ):
            continue
        valid_actions.append(action)

    if require_complete:
        if not valid_failure_modes or not valid_actions:
            return None
    else:
        if not valid_failure_modes and not valid_actions:
            return None

    cleaned_symptom = triplet.symptom.model_copy(deep=True)
    cleaned_symptom.name = cleaned_symptom.name.strip()
    cleaned_symptom.description = cleaned_symptom.description.strip()
    return Triplet(
        symptom=cleaned_symptom,
        failure_modes=valid_failure_modes,
        corrective_actions=valid_actions,
    )


def _promote_misclassified_failure_modes(result: ExtractionResult) -> ExtractionResult:
    """Rescue FailureModes that are actually observations.

    If a FailureMode fails `is_failure_mode_candidate` but reads like an
    observation (matches the Symptom heuristic), promote it into the Symptom
    list attached to the same parent Symptom — so coverage is preserved instead
    of being silently dropped downstream by `_clean_triplet`.

    Corrective actions whose only linked FailureMode was promoted are re-linked
    to the synthesised Symptom via an empty `linked_failure_mode_id` so that
    cross-chunk reconciliation can still pair them with a real FailureMode
    when one exists.
    """
    from backend.services.ontology_semantics import _OBSERVATION_RE  # local import keeps module boundary clean

    new_triplets: list[Triplet] = []
    for triplet in result.triplets:
        kept_fms: list[FailureMode] = []
        promoted_fm_ids: set[str] = set()
        promoted_symptoms: list[Symptom] = []
        parent_symptom = triplet.symptom
        parent_severity = parent_symptom.severity if parent_symptom else Severity.MEDIUM

        for fm in triplet.failure_modes:
            is_valid = is_failure_mode_candidate(fm.name, fm.description, fm.material_context)
            if is_valid:
                kept_fms.append(fm)
                continue
            combined = f"{fm.name} {fm.description} {fm.material_context}".strip()
            if combined and _OBSERVATION_RE.search(combined):
                promoted_fm_ids.add(fm.failure_mode_id)
                promoted_symptoms.append(Symptom(
                    symptom_id=fm.failure_mode_id or "",
                    name=(fm.name or "").strip(),
                    description=(fm.description or fm.name or "").strip(),
                    severity=parent_severity,
                    evidence_page=fm.evidence_page,
                ))

        if not promoted_fm_ids and not promoted_symptoms:
            new_triplets.append(triplet)
            continue

        fixed_actions: list[CorrectiveAction] = []
        for action in triplet.corrective_actions:
            if action.linked_failure_mode_id in promoted_fm_ids:
                updated = action.model_copy(deep=True)
                updated.linked_failure_mode_id = ""
                fixed_actions.append(updated)
            else:
                fixed_actions.append(action)

        new_triplets.append(Triplet(
            symptom=parent_symptom,
            failure_modes=kept_fms,
            corrective_actions=fixed_actions,
        ))

        for promoted in promoted_symptoms:
            new_triplets.append(Triplet(
                symptom=promoted,
                failure_modes=[],
                corrective_actions=[],
            ))

    if len(new_triplets) == len(result.triplets):
        return result
    logger.info(
        "[extraction] Promoted %d observation-like FailureMode(s) to Symptoms",
        len(new_triplets) - len(result.triplets),
    )
    return ExtractionResult(
        triplets=new_triplets,
        raw_symptom_table=result.raw_symptom_table,
        raw_failure_mode_table=result.raw_failure_mode_table,
        raw_corrective_action_table=result.raw_corrective_action_table,
    )


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


def _find_global_failure_mode_for_action(
    buckets: OrderedDict[tuple[str, str], dict],
    action: CorrectiveAction,
) -> tuple[tuple[str, str], tuple[str, str, str]] | None:
    """Best-effort cross-chunk lookup: find a FailureMode bucket whose text is
    semantically close to the CorrectiveAction's own name/description/steps.

    Returns (sym_key, fm_key) when a confident match exists; otherwise None.
    Used when a CA references a `linked_failure_mode_id` that was emitted in a
    different chunk and cannot be resolved locally.
    """
    action_text = " ".join([
        str(action.name or ""),
        str(action.description or ""),
        " ".join(informative_instruction_steps(action.instruction_text or "")),
    ]).strip()
    if not action_text:
        return None
    action_tokens = set(semantic_tokens(action_text))
    if len(action_tokens) < 2:
        return None

    best_match: tuple[float, tuple[str, str], tuple[str, str, str]] | None = None
    for sym_key, bucket in buckets.items():
        for fm_key, fm_bucket in bucket["failure_modes"].items():
            fm = fm_bucket["failure_mode"]
            fm_text = f"{fm.name} {fm.description} {fm.material_context}".strip()
            fm_tokens = set(semantic_tokens(fm_text))
            if not fm_tokens:
                continue
            shared = action_tokens & fm_tokens
            if not shared:
                continue
            overlap = len(shared) / max(1, min(len(action_tokens), len(fm_tokens)))
            if overlap < 0.5:
                continue
            if best_match is None or overlap > best_match[0]:
                best_match = (overlap, sym_key, fm_key)

    if best_match is None:
        return None
    return best_match[1], best_match[2]


def _merge_extraction_results(results: list[ExtractionResult]) -> ExtractionResult:
    """Reconcile per-chunk extraction results into a single consolidated result.

    Policy:
    - Orphan Symptoms (no FM, no CA) are preserved when they survive cleanup
      via the relaxed `_clean_triplet` path. They are still dropped here because
      a standalone Symptom carries no diagnostic value on its own.
    - Symptoms with at least one valid FailureMode OR at least one valid
      CorrectiveAction survive, enabling cross-chunk coverage when the Symptom
      lives in chunk A and its repair procedure lives in chunk B.
    - CorrectiveActions whose `linked_failure_mode_id` cannot be resolved
      inside their originating chunk are attempted against the global FM pool
      via semantic similarity before being discarded.
    """
    merged: OrderedDict[tuple[str, str], dict] = OrderedDict()
    deferred_actions: list[tuple[CorrectiveAction, tuple[str, str] | None]] = []

    for result in results:
        for triplet in result.triplets:
            cleaned_triplet = _clean_triplet(triplet, require_complete=False)
            if cleaned_triplet is None:
                continue

            sym_key = _symptom_key(cleaned_triplet.symptom)
            bucket = merged.get(sym_key)
            if bucket is None:
                for existing_key, existing_bucket in merged.items():
                    existing_symptom = existing_bucket["symptom"]
                    if symptoms_match(
                        existing_symptom.name,
                        existing_symptom.description,
                        cleaned_triplet.symptom.name,
                        cleaned_triplet.symptom.description,
                    ):
                        sym_key = existing_key
                        bucket = existing_bucket
                        break
            if bucket is None:
                bucket = {
                    "symptom": cleaned_triplet.symptom.model_copy(deep=True),
                    "failure_modes": OrderedDict(),
                }
                merged[sym_key] = bucket
            else:
                _merge_symptom_fields(bucket["symptom"], cleaned_triplet.symptom)

            fm_key_by_id: dict[str, tuple[str, str, str]] = {}
            for failure_mode in cleaned_triplet.failure_modes:
                fm_key = _failure_mode_key(failure_mode)
                match_key = _find_matching_failure_mode(bucket["failure_modes"], failure_mode)
                if match_key is not None:
                    fm_key = match_key
                fm_bucket = bucket["failure_modes"].get(fm_key)
                if fm_bucket is None:
                    fm_bucket = {
                        "failure_mode": failure_mode.model_copy(deep=True),
                        "corrective_actions": OrderedDict(),
                    }
                    bucket["failure_modes"][fm_key] = fm_bucket
                else:
                    _merge_failure_mode_fields(fm_bucket["failure_mode"], failure_mode)
                fm_key_by_id[failure_mode.failure_mode_id] = fm_key

            for action in cleaned_triplet.corrective_actions:
                fm_key = fm_key_by_id.get(action.linked_failure_mode_id) if action.linked_failure_mode_id else None
                if fm_key is None:
                    deferred_actions.append((action.model_copy(deep=True), sym_key))
                    continue
                ca_key = _corrective_action_key(action)
                action_bucket = bucket["failure_modes"][fm_key]["corrective_actions"]
                match_key = _find_matching_action(action_bucket, action)
                if match_key is not None:
                    _merge_corrective_action_fields(action_bucket[match_key], action)
                    continue
                action_bucket[ca_key] = action.model_copy(deep=True)

    # Second pass: try to re-attach CAs whose link was not resolvable within a
    # single chunk (cross-chunk reconciliation).
    unresolved_action_count = 0
    for action, origin_sym_key in deferred_actions:
        target = _find_global_failure_mode_for_action(merged, action)
        if target is None:
            unresolved_action_count += 1
            continue
        target_sym_key, target_fm_key = target
        action_bucket = merged[target_sym_key]["failure_modes"][target_fm_key]["corrective_actions"]
        match_key = _find_matching_action(action_bucket, action)
        if match_key is not None:
            _merge_corrective_action_fields(action_bucket[match_key], action)
            continue
        action_bucket[_corrective_action_key(action)] = action
    if deferred_actions:
        logger.info(
            "[extraction] Cross-chunk CA reconciliation: %d/%d deferred action(s) reattached",
            len(deferred_actions) - unresolved_action_count,
            len(deferred_actions),
        )

    triplets: list[Triplet] = []
    symptom_index = 1
    failure_mode_index = 1
    action_index = 1

    for bucket in merged.values():
        has_fm = bool(bucket["failure_modes"])
        has_any_action = any(
            fm_bucket["corrective_actions"]
            for fm_bucket in bucket["failure_modes"].values()
        )
        if not has_fm and not has_any_action:
            continue

        symptom = bucket["symptom"].model_copy(deep=True)
        symptom.symptom_id = _format_id("SYM", symptom_index)
        symptom_index += 1

        failure_modes: list[FailureMode] = []
        corrective_actions: list[CorrectiveAction] = []
        fm_id_by_key: dict[tuple[str, str, str], str] = {}

        for fm_key, fm_bucket in bucket["failure_modes"].items():
            failure_mode = fm_bucket["failure_mode"].model_copy(deep=True)
            failure_mode.failure_mode_id = _format_id("FM", failure_mode_index)
            failure_mode.linked_symptom_id = symptom.symptom_id
            failure_mode_index += 1
            fm_id_by_key[fm_key] = failure_mode.failure_mode_id
            failure_modes.append(failure_mode)

        for fm_key, fm_bucket in bucket["failure_modes"].items():
            linked_failure_mode_id = fm_id_by_key[fm_key]
            for action in fm_bucket["corrective_actions"].values():
                corrective_action = action.model_copy(deep=True)
                corrective_action.action_id = _format_id("CA", action_index)
                corrective_action.linked_failure_mode_id = linked_failure_mode_id
                action_index += 1
                corrective_actions.append(corrective_action)

        triplets.append(Triplet(
            symptom=symptom,
            failure_modes=failure_modes,
            corrective_actions=corrective_actions,
        ))

    return ExtractionResult(
        triplets=triplets,
        raw_symptom_table="\n\n".join(
            result.raw_symptom_table.strip() for result in results if result.raw_symptom_table.strip()
        ),
        raw_failure_mode_table="\n\n".join(
            result.raw_failure_mode_table.strip() for result in results if result.raw_failure_mode_table.strip()
        ),
        raw_corrective_action_table="\n\n".join(
            result.raw_corrective_action_table.strip() for result in results if result.raw_corrective_action_table.strip()
        ),
    )


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


def _group_into_triplets(
    symptoms: list[Symptom],
    failure_modes: list[FailureMode],
    corrective_actions: list[CorrectiveAction],
) -> list[Triplet]:
    """Group flat lists into Symptom-based triplets."""
    triplets = []
    for sym in symptoms:
        linked_fms = [fm for fm in failure_modes if fm.linked_symptom_id == sym.symptom_id]
        linked_cas = []
        for fm in linked_fms:
            linked_cas.extend(
                ca for ca in corrective_actions if ca.linked_failure_mode_id == fm.failure_mode_id
            )
        triplets.append(Triplet(
            symptom=sym,
            failure_modes=linked_fms,
            corrective_actions=linked_cas,
        ))
    return triplets
