"""Deterministic logic for PDF cut-plan: keyword scan, ToC detection, language filter."""

from __future__ import annotations

import re

from backend.models import PageRange, SectionInfo, TocEntry
from backend.services.ontology_semantics import infer_asset_type

# ─── Keyword scoring for fallback scoping ───

_STRONG_INCLUDE_KEYWORDS: dict[str, int] = {
    "troubleshooting": 6,
    "trouble shooting": 6,
    "diagnostic": 5,
    "diagnostics": 5,
    "diagnostica": 5,
    "diagnose": 5,
    "fault code": 6,
    "error code": 6,
    "alarm code": 6,
    "failure": 4,
    "failure mode": 5,
    "repair": 4,
    "service": 3,
    "maintenance": 3,
    "inspection": 3,
    "inspect": 3,
    "calibration": 3,
    "troubleshoot": 5,
    "error": 3,
    "fault": 3,
    "alarm": 3,
    "errori": 3,
    "allarmi": 3,
    "guasto": 3,
    "riparazione": 4,
    "manutenzione": 3,
    "fehler": 3,
    "störung": 3,
    "reparatur": 4,
    "wartung": 3,
    "problem solving": 6,
    "problem-solving": 6,
    "corrective action": 5,
    "corrective actions": 5,
    "error message": 5,
    "error messages": 5,
    "warning message": 4,
    "warning messages": 4,
    "malfunction": 4,
    "malfunctions": 4,
    "symptom": 4,
    "symptoms": 4,
    "remedy": 4,
    "remedies": 4,
    "cause": 3,
    "solution": 3,
    "solutions": 3,
    "log message": 4,
    "log messages": 4,
    "safety message": 2,
    "safety messages": 2,
    "parts list": 6,
    "parts lists": 6,
    "spare parts": 5,
    "spare part": 5,
    "exploded view": 6,
    "exploded views": 6,
    "assembly drawing": 6,
    "assembly drawings": 6,
    "bill of materials": 5,
    "wiring diagram": 5,
    "wiring diagrams": 5,
    "electrical schematic": 5,
    "electrical schematics": 5,
    "hydraulic schematic": 5,
    "hydraulic schematics": 5,
    "pneumatic schematic": 5,
    "pneumatic schematics": 5,
    "control circuit reference diagram": 5,
}

_WEAK_INCLUDE_KEYWORDS: dict[str, int] = {
    "warning": 1,
    "warnung": 1,
    "anomalia": 2,
    "inspection procedure": 2,
    "service procedure": 2,
    "check list": 1,
    "checklist": 1,
    "status": 1,
}

_EXCLUDE_KEYWORDS: dict[str, int] = {
    "all rights reserved": -8,
    "copyright": -8,
    "revision": -7,
    "revisions": -7,
    "overview of this manual": -7,
    "table of contents": -7,
    "contents": -5,
    "introduction": -4,
    "introduction to safety signals": -9,
    "safety signals in the manual": -9,
    "safety symbols on the manipulator labels": -9,
    "introduction to labels": -7,
    "types of labels": -7,
    "note describes important facts": -6,
    "tip describes": -6,
    "designation significance": -6,
    "symbol designation significance": -6,
    "safety": -2,
    "electrostatic discharge": -4,
}

_LLM_SECTION_EXCLUDE_RE = re.compile(
    r"(?i)\b("
    r"copyright|revision|revisions|overview|preface|foreword|introduction|"
    r"table\s+of\s+contents|contents|index|glossary|warranty|legal|"
    r"safety\s+signals|safety\s+symbols|labels|note|tip"
    r")\b"
)

_LLM_SECTION_INCLUDE_RE = re.compile(
    r"(?i)\b("
    r"trouble\s*shoot|diagnostic|error|alarm|fault|failure|repair|"
    r"service|maintenance|inspection|calibration|recovery|"
    r"problem|solving|malfunction|symptom|remedy|corrective|"
    r"log\s+message|warning\s+message|error\s+message"
    r")\b"
)

_COMPONENT_SECTION_INCLUDE_RE = re.compile(
    r"(?i)\b("
    r"parts?\s+lists?|spare\s+parts?|exploded(?:\s+views?)?|bill\s+of\s+materials|bom|"
    r"assembly\s+drawings?|component\s+(?:layout|location|diagram|drawing|list)|"
    r"(?:control|circuit|wiring|electrical|pneumatic|hydraulic)\s+(?:reference\s+)?diagram(?:s)?|"
    r"(?:control|wiring|electrical|pneumatic|hydraulic)\s+schematic(?:s)?"
    r")\b"
)

_TOC_OPERATION_INCLUDE_RE = re.compile(
    r"(?i)\b("
    r"replace|replacing|replacement|remove|removing|removal|install|installing|installation|"
    r"reboot|rebooting|restart|reset|verify|verifying|verification|check|checking|"
    r"inspection|inspect|inspecting|test|testing|calibration|calibrate|calibrating|"
    r"adjust|adjusting|alignment|assemble|assembling|disassemble|disassembling|"
    r"clean|cleaning|tighten|tightening|reconnect|reconnecting|"
    r"solving|problem|malfunction|symptom|remedy|corrective"
    r")\b"
)

_DOC_TYPE_RE = re.compile(
    r"(?i)\b(service|operation|operator|maintenance|instruction|user)\s+manual\b"
)
_FILENAME_CLEAN_RE = re.compile(r"(?i)\.pdf$")
_FILENAME_SEP_RE = re.compile(r"[_-]+")
_MODEL_LABEL_RE = re.compile(
    r"(?i)\bmodel\s*[:#-]?\s*([A-Za-z0-9][A-Za-z0-9./-]*(?:\s+[A-Za-z0-9][A-Za-z0-9./-]*){0,5})"
)
_NON_ID_CHARS_RE = re.compile(r"[^a-z0-9]+")

# ─── ToC detection patterns ───

_TOC_HEADER_RE = re.compile(
    r"(?i)\b(indice|sommario|table\s+of\s+contents|contents|inhalt)\b"
)
# Lines that look like ToC entries: text followed by dots/spaces then a number
_TOC_ENTRY_RE = re.compile(r".{3,}[\s.·…]{2,}\d{1,4}\s*$", re.MULTILINE)

# ─── Common supported-language words for language detection ───

_SUPPORTED_LANGUAGE_WORDS: set[str] = {
    "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "can", "could", "must",
    "and", "or", "but", "if", "when", "where", "how", "what",
    "this", "that", "these", "those", "it", "its", "for", "with",
    "from", "not", "no", "on", "in", "to", "of", "at", "by",
    "an", "a", "as", "so", "up", "out", "about", "into",
    "before", "after", "during", "between", "through", "each",
    "all", "any", "both", "more", "most", "other", "some",
    "such", "than", "too", "very", "also", "only", "then",
    "check", "replace", "remove", "install", "inspect", "adjust",
    "il", "lo", "la", "i", "gli", "le", "di", "a", "da", "in", "con",
    "su", "per", "tra", "fra", "che", "non", "piu", "più", "come",
    "quando", "dove", "manutenzione", "diagnostica", "errore", "allarme",
    "guasto", "riparazione", "controllare", "sostituire", "rimuovere",
    "der", "die", "das", "und", "oder", "nicht", "mit", "von", "zu",
    "im", "in", "auf", "für", "wie", "wenn", "wo", "wartung",
    "diagnose", "fehler", "störung", "reparatur", "prüfen",
    "ersetzen", "entfernen", "anleitung",
}


def keyword_scan(pages: list[dict]) -> list[SectionInfo]:
    """Scan pages for troubleshooting signals while suppressing front matter."""
    matching_pages: list[tuple[int, list[str], int]] = []

    for page in pages:
        text_lower = page["text"].lower()
        found, score = _keyword_page_score(text_lower, page["page_number"])
        if score > 0:
            matching_pages.append((page["page_number"], found, score))

    if not matching_pages:
        return []

    # Group contiguous pages into sections
    sections: list[SectionInfo] = []
    group_start = matching_pages[0][0]
    group_end = matching_pages[0][0]
    group_keywords: set[str] = set(matching_pages[0][1])
    group_score = matching_pages[0][2]

    for page_num, keywords, score in matching_pages[1:]:
        if page_num <= group_end + 2:  # allow 1-page gap
            group_end = page_num
            group_keywords.update(keywords)
            group_score += score
        else:
            section = _build_keyword_section(group_start, group_end, group_keywords, group_score)
            if section is not None:
                sections.append(section)
            group_start = page_num
            group_end = page_num
            group_keywords = set(keywords)
            group_score = score

    # Flush last group
    section = _build_keyword_section(group_start, group_end, group_keywords, group_score)
    if section is not None:
        sections.append(section)

    return sections


def _keyword_page_score(text_lower: str, page_number: int) -> tuple[list[str], int]:
    found: set[str] = set()
    score = 0

    for kw, weight in _STRONG_INCLUDE_KEYWORDS.items():
        if kw in text_lower:
            found.add(kw)
            score += weight

    for kw, weight in _WEAK_INCLUDE_KEYWORDS.items():
        if kw in text_lower:
            found.add(kw)
            score += weight

    for kw, weight in _EXCLUDE_KEYWORDS.items():
        if kw in text_lower:
            score += weight

    # Suppress generic safety/front-matter pages near the start of the manual.
    if page_number <= 12 and not any(
        kw in found
        for kw in (
            "troubleshooting",
            "trouble shooting",
            "diagnostic",
            "diagnostics",
            "diagnostica",
            "diagnose",
            "fault code",
            "error code",
            "alarm code",
            "repair",
            "reparatur",
        )
    ):
        score -= 4

    return sorted(found), score


def _build_keyword_section(
    start: int,
    end: int,
    keywords: set[str],
    score: int,
) -> SectionInfo | None:
    if score <= 0:
        return None
    return SectionInfo(
        name=f"Keyword match (pp. {start}-{end})",
        page_range=PageRange(start=start, end=end),
        source="keyword",
        keyword_matches=sorted(keywords),
        reasoning=(
            f"Fallback keyword score {score}; contains troubleshooting signals: "
            f"{', '.join(sorted(keywords))}"
        ),
    )


def find_toc_pages(
    pages: list[dict], max_scan: int = 15,
) -> tuple[bool, str | None, int | None, int | None]:
    """Search first N pages for a Table of Contents.

    Returns (found, toc_text, toc_start_page, toc_end_page).
    toc_start_page and toc_end_page are absolute PDF page numbers.
    """
    scan_pages = [p for p in pages if p["page_number"] <= max_scan]

    for page in scan_pages:
        text = page["text"]
        if _TOC_HEADER_RE.search(text):
            # Collect ToC text from this page and next few pages
            toc_parts: list[str] = []
            start_idx = pages.index(page)
            toc_start_page = page["page_number"]
            toc_end_page = page["page_number"]

            for toc_page in pages[start_idx : start_idx + 6]:
                toc_text = toc_page["text"]
                # Check it still looks like ToC (has entry-like lines)
                if toc_parts and not _TOC_ENTRY_RE.search(toc_text):
                    break
                toc_parts.append(
                    f"--- PAGE {toc_page['page_number']} ---\n{toc_text}"
                )
                toc_end_page = toc_page["page_number"]

            return True, "\n\n".join(toc_parts), toc_start_page, toc_end_page

    return False, None, None, None


def has_supported_language_content(text: str, threshold: float = 0.2) -> bool:
    """Check if text contains meaningful content in one supported language."""
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    if not words:
        return False
    supported_count = sum(1 for w in words if w in _SUPPORTED_LANGUAGE_WORDS)
    return supported_count / len(words) >= threshold


def filter_pages_by_language(
    pages: list[dict], page_numbers: list[int], threshold: float = 0.3,
) -> list[int]:
    """Filter page numbers to keep supported-language technical content."""
    page_map = {p["page_number"]: p["text"] for p in pages}
    return [
        pn for pn in page_numbers
        if pn in page_map and has_supported_language_content(page_map[pn], threshold)
    ]


def is_component_inventory_section(title: str) -> bool:
    """Return True when a section title is likely to enumerate physical components."""
    return bool(_COMPONENT_SECTION_INCLUDE_RE.search(_normalize_label(title)))


def normalize_product_info(raw_product_info: dict, filename: str = "") -> dict[str, str]:
    product_name = _clean_product_name(
        str(raw_product_info.get("product_name") or raw_product_info.get("name") or "")
    )
    if not product_name and filename:
        product_name = _derive_product_name_from_filename(filename)

    document_type = _normalize_label(str(raw_product_info.get("document_type", "") or ""))
    language = _normalize_label(str(raw_product_info.get("language", "") or ""))
    brand = _normalize_label(
        str(raw_product_info.get("brand") or raw_product_info.get("manufacturer") or "")
    )
    model = _normalize_label(str(raw_product_info.get("model", "") or ""))
    if not model:
        model = _extract_model_from_product_name(product_name)

    product_short_name = _clean_product_name(str(raw_product_info.get("product_short_name", "") or ""))
    if not product_short_name:
        product_short_name = _build_product_short_name(product_name, brand, model)

    asset_id = _normalize_asset_id(str(raw_product_info.get("asset_id", "") or ""))
    if not asset_id:
        asset_id = _build_asset_id(product_short_name or model or product_name)

    asset_type = _normalize_label(str(raw_product_info.get("asset_type", "") or ""))
    if not asset_type:
        asset_type = infer_asset_type(product_name or product_short_name, document_type)
    return {
        "product_name": product_name,
        "product_short_name": product_short_name,
        "brand": brand,
        "model": model,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "document_type": document_type,
        "language": language,
    }


def extract_asset_identity(
    raw_product_info: dict | None,
    *,
    fallback_name: str = "",
    source_type: str = "",
    filename: str = "",
) -> dict[str, str]:
    raw = raw_product_info or {}
    fallback_product_name = _clean_product_name(fallback_name)
    # Do not let a filename-derived product name override an explicit runtime
    # source_title. Golden markdown fixtures and some PDFs expose the canonical
    # asset name outside the scoping product_info payload.
    normalized = normalize_product_info(raw, filename="" if fallback_product_name else filename)
    raw_product_name = _clean_product_name(str(raw.get("product_name") or raw.get("name") or ""))
    product_name = raw_product_name or fallback_product_name or normalized.get("product_name")
    inferred_brand, inferred_model = _infer_brand_model_from_product_name(product_name)
    brand = normalized.get("brand", "") or inferred_brand
    model = normalized.get("model", "") or inferred_model
    raw_product_short_name = _clean_product_name(str(raw.get("product_short_name") or ""))
    product_short_name = raw_product_short_name or _build_product_short_name(
        product_name,
        brand,
        model,
    ) or normalized.get("product_short_name")
    document_type = normalized.get("document_type") or _normalize_label(source_type)
    asset_type = normalized.get("asset_type") or infer_asset_type(product_name or product_short_name, document_type)
    raw_asset_id = _normalize_asset_id(str(raw.get("asset_id") or ""))
    asset_id = raw_asset_id or _build_asset_id(product_short_name or product_name) or normalized.get("asset_id")
    return {
        "asset_id": asset_id,
        "name": product_name,
        "product_short_name": product_short_name,
        "brand": brand,
        "model": model,
        "asset_type": asset_type,
        "document_type": document_type,
    }


def select_toc_sections(
    toc_entries: list[TocEntry],
    page_offset: int,
    total_pages: int,
) -> list[SectionInfo]:
    selected: list[SectionInfo] = []
    manual_total_pages = max(1, total_pages - page_offset)

    for index, entry in enumerate(toc_entries):
        title = _normalize_label(entry.title)
        if not title:
            continue
        score = _toc_section_score(title)
        if score < 2:
            continue

        next_manual_page = manual_total_pages + 1
        for next_entry in toc_entries[index + 1:]:
            if next_entry.manual_page > entry.manual_page:
                next_manual_page = next_entry.manual_page
                break

        manual_start = max(1, entry.manual_page)
        manual_end = max(manual_start, min(next_manual_page - 1, manual_total_pages))
        abs_start = max(1, min(manual_start + page_offset, total_pages))
        abs_end = max(abs_start, min(manual_end + page_offset, total_pages))
        reasoning = f"Rule-based ToC score {score}; title indicates troubleshooting or service procedure content."
        selected.append(SectionInfo(
            name=title,
            page_range=PageRange(start=abs_start, end=abs_end),
            manual_page_range=PageRange(start=manual_start, end=manual_end),
            source="rule",
            reasoning=reasoning,
        ))

    return _stabilize_sections(selected)


def merge_sections(
    rule_sections: list[SectionInfo],
    llm_sections: list[SectionInfo],
    keyword_sections: list[SectionInfo],
) -> list[SectionInfo]:
    """Merge rule-based, LLM-proposed and keyword sections with deterministic priority."""
    merged: list[SectionInfo] = []
    covered_pages: set[int] = set()

    prioritized_groups = (
        _stabilize_sections(rule_sections),
        _stabilize_sections([
            section for section in llm_sections
            if _toc_section_score(section.name) >= 2
        ]),
        _stabilize_sections(keyword_sections),
    )

    for group_index, group in enumerate(prioritized_groups):
        for section in group:
            signature = (
                _normalize_label(section.name).lower(),
                section.page_range.start,
                section.page_range.end,
            )
            if any(
                _normalize_label(existing.name).lower() == signature[0]
                and existing.page_range.start == signature[1]
                and existing.page_range.end == signature[2]
                for existing in merged
            ):
                continue
            section_pages = set(range(section.page_range.start, section.page_range.end + 1))
            new_pages = section_pages - covered_pages
            if not new_pages and group_index > 0:
                continue
            merged.append(section)
            covered_pages.update(section_pages)

    return _stabilize_sections(merged)


def filter_llm_sections(sections: list[SectionInfo]) -> list[SectionInfo]:
    """Drop obviously irrelevant ToC sections selected by the LLM."""
    filtered: list[SectionInfo] = []
    for section in sections:
        name = section.name.strip()
        if not name:
            continue
        excluded = _LLM_SECTION_EXCLUDE_RE.search(name)
        included = _LLM_SECTION_INCLUDE_RE.search(name)
        score = _toc_section_score(name)
        if excluded and not included:
            continue
        if score < 1:
            continue
        filtered.append(section)
    return _stabilize_sections(filtered)


def sections_to_page_list(sections: list[SectionInfo]) -> list[int]:
    """Flatten all sections into a sorted, deduplicated list of page numbers."""
    pages: set[int] = set()
    for s in sections:
        pages.update(range(s.page_range.start, s.page_range.end + 1))
    return sorted(pages)


def _normalize_label(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def _clean_product_name(value: str) -> str:
    cleaned = _normalize_label(value)
    if not cleaned:
        return ""
    cleaned = _DOC_TYPE_RE.sub("", cleaned)
    cleaned = re.sub(r"(?i)\benglish|italian|german|deutsch|italiano\b", "", cleaned)
    return _normalize_label(cleaned.strip(" -_/"))


def _derive_product_name_from_filename(filename: str) -> str:
    cleaned = _FILENAME_CLEAN_RE.sub("", filename or "")
    cleaned = _FILENAME_SEP_RE.sub(" ", cleaned)
    cleaned = re.sub(r"(?i)\bservice\b|\bmanual\b|\ben\b|\bit\b|\bde\b", " ", cleaned)
    return _normalize_label(cleaned).strip()


def _extract_model_from_product_name(product_name: str) -> str:
    cleaned = _clean_product_name(product_name)
    if not cleaned:
        return ""
    match = _MODEL_LABEL_RE.search(cleaned)
    if match:
        return _normalize_label(match.group(1))
    return ""


def _infer_brand_model_from_product_name(product_name: str) -> tuple[str, str]:
    cleaned = _clean_product_name(product_name)
    parts = cleaned.split()
    if len(parts) < 2:
        return "", ""
    brand = parts[0] if re.search(r"[A-Za-z]", parts[0]) else ""
    model = parts[-1] if re.search(r"\d", parts[-1]) else ""
    return brand, model


def _build_product_short_name(product_name: str, brand: str, model: str) -> str:
    if brand and model:
        return _normalize_label(f"{brand} {model}")
    if model:
        return model
    return product_name


def _normalize_asset_id(value: str) -> str:
    lowered = _NON_ID_CHARS_RE.sub("_", str(value or "").strip().lower()).strip("_")
    if not lowered:
        return ""
    if lowered.startswith("asset_"):
        return lowered
    return f"asset_{lowered}"


def _build_asset_id(value: str) -> str:
    return _normalize_asset_id(value) or "asset_unknown"


def _toc_section_score(title: str) -> int:
    text_lower = title.lower()
    score = 0

    for kw, weight in _STRONG_INCLUDE_KEYWORDS.items():
        if kw in text_lower:
            score += weight

    for kw, weight in _WEAK_INCLUDE_KEYWORDS.items():
        if kw in text_lower:
            score += weight

    for kw, weight in _EXCLUDE_KEYWORDS.items():
        if kw in text_lower:
            score += weight

    if _TOC_OPERATION_INCLUDE_RE.search(title):
        score += 3
    if _LLM_SECTION_INCLUDE_RE.search(title):
        score += 2
    if is_component_inventory_section(title):
        score += 5
    if _LLM_SECTION_EXCLUDE_RE.search(title) and not _LLM_SECTION_INCLUDE_RE.search(title):
        score -= 6
    return score


def _stabilize_sections(sections: list[SectionInfo]) -> list[SectionInfo]:
    unique: list[SectionInfo] = []
    seen: set[tuple[str, int, int]] = set()

    for section in sorted(
        sections,
        key=lambda item: (item.page_range.start, item.page_range.end, _normalize_label(item.name).lower()),
    ):
        signature = (
            _normalize_label(section.name).lower(),
            section.page_range.start,
            section.page_range.end,
        )
        if signature in seen:
            continue
        seen.add(signature)
        unique.append(section)
    return unique
