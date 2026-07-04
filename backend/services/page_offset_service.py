"""Deterministic printed-page-number offset detection.

Service manuals are paginated by their PRINTED page numbers (the ToC says
"Troubleshooting ... page 16"), but the pipeline slices PHYSICAL pages of the
PDF. When cover sheets or unnumbered front matter precede printed page 1, the
two indexes diverge by a constant offset and every ToC-derived section lands
on the wrong physical pages.

Historically the offset was a request parameter defaulting to 0 that no UI
ever set — so the mismatch was silently active on any real PDF with front
matter. This module detects the offset from the document itself, using two
independent, LLM-free signals:

1. Printed page labels: standalone numbers in the first/last lines of each
   physical page ("16", "- 16 -", "Page 16", "16/48"). Each label votes
   physical_index - printed_number.
2. ToC anchoring: for each ToC entry, find the physical page(s) whose text
   contains the entry title; each hit votes physical_index - printed_target.
   This measures exactly the quantity the offset is used for, so when both
   signals are confident and disagree, ToC anchoring wins.

Both signals use majority voting with minimum-support and consistency
thresholds; when neither is confident the detector falls back to offset 0
(the previous behaviour) and says so in its report.

Everything here is pure and deterministic: no I/O, no LLM calls.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

# Printed page labels seen in real manuals: "16", "- 16 -", "– 16 –",
# "Page 16", "Page 16 of 48", "16/48", "16 / 48".
_LABEL_PATTERNS = (
    re.compile(r"^[\-–—]?\s*(\d{1,4})\s*[\-–—]?$"),
    re.compile(r"^(?:page|pagina|seite|página|стр\.?)\s+(\d{1,4})(?:\s*(?:of|di|de|von|/)\s*\d{1,4})?$", re.IGNORECASE),
    re.compile(r"^(\d{1,4})\s*/\s*\d{1,4}$"),
)

# How many head/tail lines of a page may carry the printed label.
_EDGE_LINES = 3

# Plausible offsets: a few negative (front matter trimmed from the PDF) up to
# dozens of positive (covers, legal pages, translated front matter).
_MIN_OFFSET = -10
_MAX_OFFSET = 50

_MIN_LABEL_VOTES = 3
_MIN_TOC_VOTES = 2
_MIN_CONSISTENCY = 0.6


def _normalize_text(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def _printed_labels(page_text: str) -> list[int]:
    lines = [line.strip() for line in str(page_text or "").splitlines() if line.strip()]
    edge_lines = lines[:_EDGE_LINES] + lines[-_EDGE_LINES:]
    labels: list[int] = []
    for line in edge_lines:
        for pattern in _LABEL_PATTERNS:
            match = pattern.match(line)
            if match:
                labels.append(int(match.group(1)))
                break
    return labels


def _vote_result(votes: Counter, *, min_votes: int, source: str) -> dict[str, Any]:
    total = sum(votes.values())
    if not total:
        return {"offset": None, "source": source, "confidence": 0.0, "votes": {}, "total_votes": 0}
    offset, count = votes.most_common(1)[0]
    confidence = count / total
    detected = offset if (count >= min_votes and confidence >= _MIN_CONSISTENCY) else None
    return {
        "offset": detected,
        "source": source,
        "confidence": round(confidence, 4),
        "votes": {str(key): value for key, value in sorted(votes.items())},
        "total_votes": total,
    }


def detect_offset_from_page_labels(pages: list[dict[str, Any]]) -> dict[str, Any]:
    """Majority vote of (physical index − printed label) across all pages."""
    total_pages = len(pages)
    votes: Counter = Counter()
    for page in pages:
        physical = int(page.get("page_number") or 0)
        if physical <= 0:
            continue
        for printed in set(_printed_labels(page.get("text", ""))):
            if not 1 <= printed <= total_pages + abs(_MIN_OFFSET):
                continue
            offset = physical - printed
            if _MIN_OFFSET <= offset <= _MAX_OFFSET:
                votes[offset] += 1
    return _vote_result(votes, min_votes=_MIN_LABEL_VOTES, source="page_labels")


def detect_offset_from_toc(
    pages: list[dict[str, Any]],
    toc_entries: list[Any],
    *,
    toc_page_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Majority vote of (physical page containing the entry title − printed target).

    Pages inside `toc_page_range` are excluded from anchoring: the ToC itself
    contains every title, so it would vote for its own physical position.
    """
    skip_start, skip_end = toc_page_range or (0, -1)
    normalized_pages = [
        (int(page.get("page_number") or 0), _normalize_text(page.get("text", "")))
        for page in pages
    ]
    votes: Counter = Counter()
    for entry in toc_entries:
        title = getattr(entry, "title", None)
        manual_page = getattr(entry, "manual_page", None)
        if title is None and isinstance(entry, dict):
            title = entry.get("title")
            manual_page = entry.get("manual_page")
        title_norm = _normalize_text(title or "")
        try:
            printed = int(manual_page or 0)
        except (TypeError, ValueError):
            continue
        # Short titles ("Index", "6-2") anchor everywhere; require substance.
        if printed <= 0 or len(title_norm) < 8:
            continue
        for physical, page_norm in normalized_pages:
            if physical <= 0 or skip_start <= physical <= skip_end:
                continue
            if title_norm not in page_norm:
                continue
            offset = physical - printed
            if _MIN_OFFSET <= offset <= _MAX_OFFSET:
                # A title at the top of the page is a section heading, not a
                # cross-reference: weight it double.
                weight = 2 if title_norm in page_norm[:300] else 1
                votes[offset] += weight
    return _vote_result(votes, min_votes=_MIN_TOC_VOTES, source="toc_anchoring")


def detect_page_offset(
    pages: list[dict[str, Any]],
    toc_entries: list[Any] | None = None,
    *,
    toc_page_range: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """Combine both signals; fall back to 0 (legacy behaviour) when unsure.

    Returns {"offset", "source", "confidence", "label_detection", "toc_detection"}.
    """
    label_detection = detect_offset_from_page_labels(pages)
    toc_detection = (
        detect_offset_from_toc(pages, toc_entries, toc_page_range=toc_page_range)
        if toc_entries
        else {"offset": None, "source": "toc_anchoring", "confidence": 0.0, "votes": {}, "total_votes": 0}
    )

    if toc_detection["offset"] is not None:
        chosen, source, confidence = toc_detection["offset"], "toc_anchoring", toc_detection["confidence"]
    elif label_detection["offset"] is not None:
        chosen, source, confidence = label_detection["offset"], "page_labels", label_detection["confidence"]
    else:
        chosen, source, confidence = 0, "default", 0.0

    return {
        "offset": int(chosen),
        "source": source,
        "confidence": confidence,
        "agreement": (
            label_detection["offset"] == toc_detection["offset"]
            if label_detection["offset"] is not None and toc_detection["offset"] is not None
            else None
        ),
        "label_detection": label_detection,
        "toc_detection": toc_detection,
    }


_TOC_LINE_RE = re.compile(r"^(.*?)[\s.·…_-]{3,}\s*(\d{1,4})\s*$")


def parse_toc_entries_from_text(toc_text: str) -> list[dict[str, Any]]:
    """Cheap regex ToC parse ("Title ..... 53") for LLM-free detection/testing."""
    entries: list[dict[str, Any]] = []
    for raw_line in str(toc_text or "").splitlines():
        line = raw_line.strip()
        match = _TOC_LINE_RE.match(line)
        if not match:
            continue
        title = match.group(1).strip(" .·…_-")
        if len(title) < 4:
            continue
        entries.append({"title": title, "manual_page": int(match.group(2))})
    return entries
