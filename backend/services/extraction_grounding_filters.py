"""Filter extracted content against the source page text (anti-hallucination)."""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher

from backend.models import CorrectiveAction, ExtractionResult, FailureMode, Triplet
from backend.services.ontology_semantics import (
    build_semantic_key,
    informative_instruction_steps,
    instruction_steps,
    is_corrective_action_candidate,
    is_failure_mode_candidate,
    normalize_semantic_text,
    prefer_more_informative_text,
    semantic_tokens,
    semantically_equivalent,
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
