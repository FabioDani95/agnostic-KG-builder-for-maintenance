"""Deterministic Component + ErrorCode candidate mining from page-annotated text.

Pre-LLM pass that surfaces likely Component nouns and alarm/error tokens found
in the text. The result is injected into the ontology-draft system prompt as a
"checklist floor" so the LLM does not start from zero: it keeps recall up
without giving up precision, because every mined candidate still has to be
confirmed against the source text by the LLM.

Extraction is intentionally conservative and driven by a lexical whitelist of
common mechanical / electrical / control components plus regex patterns for
alphanumeric alarm codes (e.g. "C0330", "H0216", "Alarm 215") and natural
language alarm phrases ("low air alarm", "timeout in ...").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_COMPONENT_LEXICON: tuple[str, ...] = (
    "valve", "solenoid", "solenoid valve",
    "motor", "servomotor", "servo motor", "spindle motor",
    "encoder", "absolute encoder", "resolver",
    "arm", "robot arm", "atc arm", "atc",
    "ballscrew", "ball screw", "leadscrew", "lead screw",
    "waycover", "way cover", "way covers",
    "spindle", "spindle bearing", "spindle drive",
    "pump", "hydraulic pump", "coolant pump", "lubrication pump",
    "sensor", "proximity sensor", "current sensor", "pressure sensor",
    "thermistor", "thermocouple", "limit switch",
    "connector", "cable", "harness",
    "bearing", "gear", "gearbox",
    "battery", "power supply", "fuse", "relay", "contactor",
    "pcb", "board", "driver",
    "gasket", "seal", "o-ring", "o ring",
    "filter", "regulator",
    "fan", "cooling fan",
    "brake", "clutch",
    "door", "cover", "panel", "window",
    "controller", "cpu", "plc",
    "hand", "gripper", "end effector",
    "axis", "joint",
    "nozzle", "head", "print head",
    "belt", "timing belt",
    "chuck", "collet",
    "tool changer", "tool magazine",
    "pneumatic cylinder", "pneumatic valve",
    "air regulator", "air filter",
    "heater", "heating element",
    "lamp", "led",
    "buzzer", "horn",
)


_COMPONENT_STOPWORDS: frozenset[str] = frozenset({
    "system", "machine", "robot", "unit", "assembly", "equipment", "device",
    "manual", "section", "chapter", "page", "figure", "table", "step",
    "procedure", "operation", "function", "feature", "parameter",
})


_ERROR_CODE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b([A-Z]\d{3,4}(?:-\d+)?)\b"),                     # C0330, H0216, H0712-1
    re.compile(r"\b(E\d{2,4})\b"),                                  # E504
    re.compile(r"\b(Alarm\s+\d{1,4})\b", re.IGNORECASE),            # Alarm 215
    re.compile(r"\b(Error\s+\d{1,4})\b", re.IGNORECASE),            # Error 42
    re.compile(r"\b(Fault\s+\d{1,4})\b", re.IGNORECASE),            # Fault 7
)


_ALARM_PHRASE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"\b(timeout in [a-z][a-z]{2,20}(?:\s[a-z]+)?)", re.IGNORECASE),
    re.compile(r"\b(low\s+\w+\s+alarm)\b", re.IGNORECASE),
    re.compile(r"\b(high\s+\w+\s+alarm)\b", re.IGNORECASE),
    re.compile(r"\balarm\s+['\"]([^'\"]{3,60})['\"]", re.IGNORECASE),
    re.compile(r"\b((?:[a-z]+\s){1,2}alarm)\b", re.IGNORECASE),
)


_ALARM_PHRASE_NOISE_PREFIXES: tuple[str, ...] = (
    "is ", "are ", "was ", "were ", "be ", "been ", "been a ",
    "a ", "an ", "the ", "this ", "that ", "when ", "when a ",
    "if ", "if a ", "triggers the ", "triggers a ",
)


_PAGE_MARKER_RE = re.compile(r"---\s*PAGE\s+(\d+)\s*---", re.IGNORECASE)

# An alphanumeric token only counts as an error-code candidate when the nearby
# text presents it as an alarm/error/fault indication. This keeps part numbers
# from exploded views / parts lists (e.g. "W262") and referenced standards
# (e.g. "ANSI Z136") out of the candidate list.
_ERROR_CONTEXT_RE = re.compile(
    r"(?i)\b("
    r"alarm|error|fault|alert|trouble|warning|diagnos|self-diagnosis|"
    r"display|displayed|code|f-code|abnormal|malfunction|fail"
    r")"
)
_ERROR_CONTEXT_WINDOW_CHARS = 160
_STANDARD_REFERENCE_RE = re.compile(r"(?i)\b(ansi|iso|iec|en|ul|din|nfpa|astm)\b")


def _has_error_context(segment: str, start: int, end: int) -> bool:
    window_start = max(0, start - _ERROR_CONTEXT_WINDOW_CHARS)
    window_end = min(len(segment), end + _ERROR_CONTEXT_WINDOW_CHARS)
    window = segment[window_start:window_end]
    if _STANDARD_REFERENCE_RE.search(segment[window_start:start]):
        return False
    return _ERROR_CONTEXT_RE.search(window) is not None


@dataclass
class ComponentCandidate:
    term: str
    pages: set[int] = field(default_factory=set)
    mention_count: int = 0


@dataclass
class ErrorCodeCandidate:
    token: str
    pages: set[int] = field(default_factory=set)
    mention_count: int = 0


@dataclass
class MiningResult:
    components: list[ComponentCandidate]
    error_codes: list[ErrorCodeCandidate]

    def is_empty(self) -> bool:
        return not self.components and not self.error_codes

    def to_summary(self) -> dict:
        return {
            "component_count": len(self.components),
            "error_code_count": len(self.error_codes),
            "component_terms": [c.term for c in self.components],
            "error_code_tokens": [e.token for e in self.error_codes],
        }


def _iter_page_segments(text: str) -> list[tuple[int, str]]:
    """Yield (page_number, text) segments using --- PAGE N --- markers."""
    segments: list[tuple[int, str]] = []
    matches = list(_PAGE_MARKER_RE.finditer(text))
    if not matches:
        return [(0, text)]
    for index, match in enumerate(matches):
        page_number = int(match.group(1))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        segments.append((page_number, text[start:end]))
    return segments


def _normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip().lower())


def _component_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term)
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def _is_valid_component_term(term: str) -> bool:
    if not term or len(term) < 3:
        return False
    lowered = term.strip().lower()
    if lowered in _COMPONENT_STOPWORDS:
        return False
    return True


def mine_candidates(
    text_with_pages: str,
    *,
    max_components: int = 40,
    max_error_codes: int = 30,
) -> MiningResult:
    """Scan page-annotated text and return component + error-code candidates."""
    if not text_with_pages or not text_with_pages.strip():
        return MiningResult(components=[], error_codes=[])

    component_index: dict[str, ComponentCandidate] = {}
    error_index: dict[str, ErrorCodeCandidate] = {}

    component_patterns = [
        (term, _component_pattern(term))
        for term in _COMPONENT_LEXICON
        if _is_valid_component_term(term)
    ]

    for page_number, segment in _iter_page_segments(text_with_pages):
        for term, pattern in component_patterns:
            hits = pattern.findall(segment)
            if not hits:
                continue
            key = _normalize_term(term)
            candidate = component_index.setdefault(key, ComponentCandidate(term=term))
            candidate.mention_count += len(hits)
            if page_number:
                candidate.pages.add(page_number)

        for pattern in _ERROR_CODE_PATTERNS:
            for match in pattern.finditer(segment):
                token = match.group(1).strip()
                if not token:
                    continue
                if not _has_error_context(segment, match.start(1), match.end(1)):
                    continue
                key = token.upper()
                candidate = error_index.setdefault(key, ErrorCodeCandidate(token=token))
                candidate.mention_count += 1
                if page_number:
                    candidate.pages.add(page_number)

        for pattern in _ALARM_PHRASE_PATTERNS:
            for match in pattern.findall(segment):
                phrase = match.strip().rstrip(".,;:")
                lowered = phrase.lower()
                for noise in _ALARM_PHRASE_NOISE_PREFIXES:
                    if lowered.startswith(noise):
                        phrase = phrase[len(noise):].strip()
                        lowered = phrase.lower()
                if not phrase or len(phrase) > 60 or len(phrase) < 5:
                    continue
                if phrase.lower() in {"alarm", "an alarm", "the alarm"}:
                    continue
                key = phrase.lower()
                candidate = error_index.setdefault(key, ErrorCodeCandidate(token=phrase))
                candidate.mention_count += 1
                if page_number:
                    candidate.pages.add(page_number)

    components = sorted(
        component_index.values(),
        key=lambda item: (-item.mention_count, item.term),
    )[:max_components]
    error_codes = sorted(
        error_index.values(),
        key=lambda item: (-item.mention_count, item.token),
    )[:max_error_codes]
    return MiningResult(components=components, error_codes=error_codes)


def render_candidates_prompt_block(result: MiningResult) -> str:
    """Render the mining result as a prompt block to inject into ontology draft.

    Returns an empty string when there is nothing to inject so callers can skip
    the section entirely.
    """
    if result.is_empty():
        return ""

    lines: list[str] = ["## DETECTED CANDIDATES (include these in the ontology if supported)"]
    if result.components:
        lines.append("### Components mined from text")
        for candidate in result.components:
            pages = sorted(candidate.pages)
            pages_str = f", pages: {pages}" if pages else ""
            lines.append(
                f"- {candidate.term.title()} (mentions: {candidate.mention_count}{pages_str})"
            )
    if result.error_codes:
        lines.append("### Error codes / alarm signatures mined from text")
        for candidate in result.error_codes:
            pages = sorted(candidate.pages)
            pages_str = f" (page(s): {pages})" if pages else ""
            lines.append(f'- "{candidate.token}"{pages_str}')
    lines.append("")
    lines.append(
        "Treat the list above as a RECALL FLOOR, not a ground-truth list: "
        "include each item as a Component or ErrorCode node ONLY if the text "
        "genuinely describes it. Do not fabricate extra detail."
    )
    return "\n".join(lines)
