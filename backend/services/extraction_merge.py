"""Merge and deduplicate chunked extraction results."""

from __future__ import annotations

import logging
from collections import OrderedDict

from backend.models import (
    CorrectiveAction,
    ExtractionResult,
    FailureMode,
    Severity,
    Symptom,
    Triplet,
)
from backend.services.extraction_grounding_filters import _clean_triplet, _normalize_text
from backend.services.ontology_semantics import (
    build_semantic_key,
    corrective_actions_match,
    failure_modes_match,
    informative_instruction_steps,
    is_failure_mode_candidate,
    prefer_more_informative_text,
    semantic_tokens,
    symptoms_match,
)

logger = logging.getLogger(__name__)


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


