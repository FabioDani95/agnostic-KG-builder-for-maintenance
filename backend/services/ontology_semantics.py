from __future__ import annotations

import re
from difflib import SequenceMatcher


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_WHITESPACE_RE = re.compile(r"\s+")
_STEP_NUMBER_RE = re.compile(r"(?:(?<=^)|(?<=[\n\r])|(?<=\.\s))\d+\.\s+")
_ACTION_STEP_SPLIT_RE = _STEP_NUMBER_RE
_GENERIC_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
    "manual", "service", "system", "unit", "device",
}
_GENERIC_ASSET_NAME_RE = re.compile(
    r"(?i)\b(asset|technical asset|machine|robot system|system|equipment|device)\b"
)
_GENERIC_PRODUCT_TYPE_RE = re.compile(
    r"(?i)\b(manual|service manual|operation manual|technical asset|asset|system)\b"
)
_REPAIR_ACTION_RE = re.compile(
    r"(?i)\b("
    r"replace|repair|clean|tighten|adjust|align|calibrate|lubricat|"
    r"remove|install|reconnect|reseat|reset|reboot|restart|swap|"
    r"secure|retighten|repair|update|restore|torque"
    r")\b"
)
_VERIFICATION_ONLY_RE = re.compile(
    r"(?i)\b("
    r"verify|verification|check|inspect|inspection|test|testing|"
    r"confirm|validation|measure|measurement"
    r")\b"
)
_IMPERATIVE_FAILURE_RE = re.compile(
    r"(?i)^\s*("
    r"check|inspect|replace|remove|install|verify|test|tighten|"
    r"clean|adjust|calibrate|restart|reboot|measure"
    r")\b"
)
_PROCEDURE_OUTCOME_RE = re.compile(
    r"(?i)\b("
    r"verification failed|test failed|inspection failed|check failed|"
    r"did not pass|does not pass|failed verification|failed test|"
    r"calibration failed|alignment failed"
    r")\b"
)
_OBSERVATION_RE = re.compile(
    r"(?i)\b("
    r"alarm|error|warning|displayed|shown|appears|unable|cannot|does not|"
    r"won't|will not|not moving|no power|stops|stopped|abnormal|"
    r"noise|vibration|leak|low|high|fluctuat"
    r")\b"
)
_CAUSE_RE = re.compile(
    r"(?i)\b("
    r"broken|damaged|worn|wear|faulty|failed|defective|loose|"
    r"misaligned|contaminat|corrod|disconnected|open circuit|short|"
    r"overheat|leakage|pressure loss|power supply failure|connector issue"
    r")\b"
)
_LOW_SIGNAL_ACTION_STEP_RE = re.compile(
    r"(?i)^\s*("
    r"verify\b.*(?:fault|problem|issue).*(?:fixed|resolved)|"
    r"verify\b.*(?:repair|replacement|action)|"
    r"restart this guide(?: if necessary)?|"
    r"refer to (?:the )?plant documentation.*"
    r")\s*$"
)
_ASSET_TYPE_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?i)\bcontrol\s+box\b|\bcontrol\s+cabinet\b|\bcontroller\b"), "control box"),
    (re.compile(r"(?i)\bteach\s+pendant\b"), "teach pendant"),
    (re.compile(r"(?i)\brobot\s+arm\b|\bmanipulator\b"), "robot arm"),
    (re.compile(r"(?i)\bcobot\b"), "cobot"),
    (re.compile(r"(?i)\brobot\b|\bur\s+series\b"), "robot system"),
)


def normalize_semantic_text(value: str) -> str:
    lowered = str(value or "").strip().lower()
    lowered = lowered.replace("/", " ")
    lowered = re.sub(r"[^a-z0-9\s.-]", " ", lowered)
    return _WHITESPACE_RE.sub(" ", lowered).strip()


def semantic_tokens(value: str) -> list[str]:
    tokens = [
        token for token in _TOKEN_RE.findall(normalize_semantic_text(value))
        if token not in _GENERIC_STOPWORDS and len(token) > 1
    ]
    return tokens


def build_semantic_key(*parts: str, max_tokens: int = 10) -> str:
    seen: set[str] = set()
    ordered: list[str] = []
    for part in parts:
        for token in semantic_tokens(part):
            if token in seen:
                continue
            seen.add(token)
            ordered.append(token)
            if len(ordered) >= max_tokens:
                return " ".join(ordered)
    return " ".join(ordered)


def instruction_steps(value: str) -> list[str]:
    raw = str(value or "").replace("\r", "\n").strip()
    if not raw:
        return []
    if _ACTION_STEP_SPLIT_RE.search(raw):
        parts = [
            part.strip(" -\n\t")
            for part in _ACTION_STEP_SPLIT_RE.split(raw)
            if part.strip(" -\n\t")
        ]
        if parts:
            return parts
    return [part.strip() for part in re.split(r"[\n;]+", raw) if part.strip()]


def informative_instruction_steps(value: str) -> list[str]:
    steps = instruction_steps(value)
    informative = [step for step in steps if not _LOW_SIGNAL_ACTION_STEP_RE.match(step)]
    return informative or steps


def semantically_equivalent(
    left: str,
    right: str,
    *,
    min_ratio: float = 0.84,
    min_overlap: float = 0.67,
) -> bool:
    left_norm = normalize_semantic_text(left)
    right_norm = normalize_semantic_text(right)
    if not left_norm or not right_norm:
        return False
    if left_norm == right_norm:
        return True

    left_tokens = set(semantic_tokens(left_norm))
    right_tokens = set(semantic_tokens(right_norm))
    if left_tokens and right_tokens:
        shared = left_tokens & right_tokens
        overlap = len(shared) / max(1, min(len(left_tokens), len(right_tokens)))
        if overlap >= min_overlap:
            return True
    else:
        overlap = 0.0

    ratio = SequenceMatcher(a=left_norm, b=right_norm).ratio()
    if ratio >= min_ratio:
        return True
    return overlap >= min_overlap * 0.85 and ratio >= 0.70


def prefer_more_informative_text(existing: str, candidate: str) -> str:
    existing_norm = normalize_semantic_text(existing)
    candidate_norm = normalize_semantic_text(candidate)
    if not candidate_norm:
        return existing
    if not existing_norm:
        return candidate

    existing_tokens = set(semantic_tokens(existing_norm))
    candidate_tokens = set(semantic_tokens(candidate_norm))
    if existing_tokens and candidate_tokens:
        if existing_tokens < candidate_tokens:
            return candidate
        if candidate_tokens < existing_tokens:
            return existing

    if len(candidate_norm) > len(existing_norm):
        return candidate
    return existing


def infer_asset_type(source_title: str, source_type: str = "", current_value: str = "") -> str:
    candidates = [str(current_value or "").strip(), str(source_title or "").strip(), str(source_type or "").strip()]
    for candidate in candidates:
        if candidate and not _GENERIC_PRODUCT_TYPE_RE.search(candidate):
            for pattern, asset_type in _ASSET_TYPE_HINTS:
                if pattern.search(candidate):
                    return asset_type
            return normalize_semantic_text(candidate)

    for candidate in candidates:
        for pattern, asset_type in _ASSET_TYPE_HINTS:
            if pattern.search(candidate):
                return asset_type
    return "technical asset"


def _looks_generic_asset_name(value: str) -> bool:
    normalized = normalize_semantic_text(value)
    if not normalized:
        return True
    if _GENERIC_ASSET_NAME_RE.fullmatch(normalized):
        return True
    return len(semantic_tokens(normalized)) <= 1 and _GENERIC_ASSET_NAME_RE.search(normalized) is not None


def normalize_asset_node(
    asset_node: dict[str, object],
    source_title: str,
    source_type: str,
    asset_identity: dict[str, object] | None = None,
) -> dict[str, object]:
    normalized = dict(asset_node)
    identity = asset_identity or {}
    canonical_id = str(identity.get("asset_id", "") or "").strip()
    canonical_name = str(identity.get("name") or identity.get("product_name") or source_title or "").strip()
    canonical_brand = str(identity.get("brand", "") or "").strip()
    canonical_model = str(identity.get("model") or identity.get("product_short_name") or "").strip()
    canonical_asset_type = str(identity.get("asset_type", "") or "").strip()

    if canonical_id:
        normalized["asset_id"] = canonical_id

    preferred_name = canonical_name or str(source_title or "").strip()
    current_name = str(normalized.get("name", "") or "").strip()
    if preferred_name and asset_identity:
        normalized["name"] = preferred_name
    elif preferred_name:
        preferred_tokens = set(semantic_tokens(preferred_name))
        current_tokens = set(semantic_tokens(current_name))
        is_more_specific = (
            preferred_tokens
            and current_tokens
            and current_tokens < preferred_tokens
            and len(preferred_tokens) >= len(current_tokens) + 1
        )
        if _looks_generic_asset_name(current_name) or is_more_specific:
            normalized["name"] = preferred_name

    if canonical_brand:
        normalized["brand"] = canonical_brand
    if canonical_model:
        normalized["model"] = canonical_model
    if not str(normalized.get("description", "") or "").strip():
        normalized["description"] = str(normalized.get("name", "") or preferred_name or "").strip()
    normalized["asset_type"] = infer_asset_type(
        source_title=str(source_title or ""),
        source_type=str(source_type or ""),
        current_value=canonical_asset_type or str(normalized.get("asset_type", "") or ""),
    )
    return normalized


def is_failure_mode_candidate(name: str, description: str, material_context: str) -> bool:
    combined = " ".join([name or "", description or "", material_context or ""]).strip()
    if not normalize_semantic_text(combined):
        return False
    if _IMPERATIVE_FAILURE_RE.search(name or ""):
        return False
    if _PROCEDURE_OUTCOME_RE.search(combined):
        return False
    if _VERIFICATION_ONLY_RE.search(combined) and not _CAUSE_RE.search(combined):
        return False
    if _OBSERVATION_RE.search(combined) and not (_CAUSE_RE.search(combined) or normalize_semantic_text(material_context)):
        return False
    return True


def is_corrective_action_candidate(name: str, description: str, instruction_text: str) -> bool:
    normalized_instruction = normalize_semantic_text(instruction_text)
    if not normalized_instruction:
        return False
    combined = " ".join([name or "", description or "", instruction_text or ""])
    has_repair_signal = _REPAIR_ACTION_RE.search(combined) is not None
    has_verification_signal = _VERIFICATION_ONLY_RE.search(combined) is not None
    has_steps = _STEP_NUMBER_RE.search(instruction_text or "") is not None
    if has_verification_signal and not has_repair_signal:
        return False
    return has_repair_signal or has_steps


def symptoms_match(
    left_name: str,
    left_description: str,
    right_name: str,
    right_description: str,
) -> bool:
    left_key = build_semantic_key(left_name, left_description)
    right_key = build_semantic_key(right_name, right_description)
    return left_key == right_key or semantically_equivalent(
        f"{left_name} {left_description}",
        f"{right_name} {right_description}",
        min_ratio=0.78,
        min_overlap=0.70,
    )


def failure_modes_match(
    left_name: str,
    left_description: str,
    left_material_context: str,
    right_name: str,
    right_description: str,
    right_material_context: str,
) -> bool:
    text_matches = semantically_equivalent(
        f"{left_name} {left_description}",
        f"{right_name} {right_description}",
        min_ratio=0.76,
        min_overlap=0.64,
    ) or build_semantic_key(left_name, left_description) == build_semantic_key(
        right_name,
        right_description,
    )
    if not text_matches:
        return False

    context_matches = (
        not normalize_semantic_text(left_material_context)
        or not normalize_semantic_text(right_material_context)
        or semantically_equivalent(left_material_context, right_material_context, min_ratio=0.76, min_overlap=0.60)
    )
    if context_matches:
        return True

    return semantically_equivalent(
        left_name,
        right_name,
        min_ratio=0.70,
        min_overlap=0.66,
    )


def infer_component_match_for_failure_mode(
    failure_mode_name: str,
    failure_mode_description: str,
    failure_mode_material_context: str,
    components: list[dict],
    *,
    min_score: float = 0.72,
    ambiguity_margin: float = 0.08,
) -> str:
    ranked: list[tuple[float, str]] = []

    for component in components:
        component_id = str(component.get("component_id", "")).strip()
        component_name = str(component.get("name", "")).strip()
        component_description = str(component.get("description", "")).strip()
        if not component_id or not component_name:
            continue

        score = _failure_mode_component_score(
            failure_mode_name=failure_mode_name,
            failure_mode_description=failure_mode_description,
            failure_mode_material_context=failure_mode_material_context,
            component_name=component_name,
            component_description=component_description,
        )
        if score > 0:
            ranked.append((score, component_id))

    if not ranked:
        return ""

    ranked.sort(reverse=True)
    best_score, best_component_id = ranked[0]
    if best_score < min_score:
        return ""
    if len(ranked) > 1 and ranked[1][0] >= best_score - ambiguity_margin:
        return ""
    return best_component_id


def _failure_mode_component_score(
    *,
    failure_mode_name: str,
    failure_mode_description: str,
    failure_mode_material_context: str,
    component_name: str,
    component_description: str,
) -> float:
    failure_parts = [
        str(failure_mode_material_context or "").strip(),
        str(failure_mode_name or "").strip(),
        str(failure_mode_description or "").strip(),
        " ".join(
            part for part in (
                str(failure_mode_name or "").strip(),
                str(failure_mode_description or "").strip(),
                str(failure_mode_material_context or "").strip(),
            )
            if part
        ).strip(),
    ]
    component_parts = [
        str(component_name or "").strip(),
        str(component_description or "").strip(),
        " ".join(
            part for part in (
                str(component_name or "").strip(),
                str(component_description or "").strip(),
            )
            if part
        ).strip(),
    ]

    best = 0.0
    for failure_text in failure_parts:
        failure_norm = normalize_semantic_text(failure_text)
        if not failure_norm:
            continue
        failure_tokens = set(semantic_tokens(failure_norm))

        for component_text in component_parts:
            component_norm = normalize_semantic_text(component_text)
            if not component_norm:
                continue
            if component_norm in failure_norm or failure_norm in component_norm:
                best = max(best, 0.98)
            if semantically_equivalent(
                failure_norm,
                component_norm,
                min_ratio=0.74,
                min_overlap=0.66,
            ):
                best = max(best, 0.92)

            component_tokens = set(semantic_tokens(component_norm))
            if not failure_tokens or not component_tokens:
                continue
            overlap = len(failure_tokens & component_tokens) / max(1, min(len(failure_tokens), len(component_tokens)))
            best = max(best, overlap)

    return best


def corrective_actions_match(
    left_name: str,
    left_description: str,
    left_instruction_text: str,
    right_name: str,
    right_description: str,
    right_instruction_text: str,
) -> bool:
    left_steps = informative_instruction_steps(left_instruction_text)
    right_steps = informative_instruction_steps(right_instruction_text)
    if build_semantic_key(left_name, left_description, *left_steps) == build_semantic_key(
        right_name,
        right_description,
        *right_steps,
    ):
        return True

    if semantically_equivalent(
        f"{left_name} {left_description} {' '.join(left_steps)}",
        f"{right_name} {right_description} {' '.join(right_steps)}",
        min_ratio=0.74,
        min_overlap=0.62,
    ):
        return True

    return semantically_equivalent(
        f"{left_name} {left_description} {left_instruction_text}",
        f"{right_name} {right_description} {right_instruction_text}",
        min_ratio=0.76,
        min_overlap=0.65,
    )
