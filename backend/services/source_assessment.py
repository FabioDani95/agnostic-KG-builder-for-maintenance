"""Deterministic source-to-machine identity assessment."""

from __future__ import annotations

import re
from pathlib import Path

import fitz

from backend.domain.locators import PdfLocator
from backend.domain.sources import AssessmentOutcome, ObservedAssetClaim, SourceKind
from backend.domain.workspace import Asset, AssetIdentifier

_EXPLICIT = {
    "serial": re.compile(r"(?im)^\s*(?:serial(?:\s+number)?|s/?n)\s*[:#=-]\s*([^\r\n]+)"),
    "equipment_tag": re.compile(r"(?im)^\s*(?:equipment\s+tag|tag)\s*[:#=-]\s*([^\r\n]+)"),
    "customer_asset_id": re.compile(r"(?im)^\s*(?:asset\s+id|machine\s+id)\s*[:#=-]\s*([^\r\n]+)"),
    "model": re.compile(r"(?im)^\s*model\s*[:#=-]\s*([^\r\n]+)"),
    "brand": re.compile(r"(?im)^\s*(?:brand|manufacturer)\s*[:#=-]\s*([^\r\n]+)"),
}
_STRONG = {"serial", "equipment_tag", "customer_asset_id"}


def _normalize(value: str) -> str:
    return " ".join(str(value or "").casefold().strip().split())


def _pdf_pages(path: Path, limit: int = 5) -> list[tuple[int, str]]:
    document = fitz.open(path)
    try:
        return [
            (index + 1, str(document[index].get_text("text") or ""))
            for index in range(min(len(document), limit))
        ]
    finally:
        document.close()


def observe_asset_claims(
    *,
    path: Path,
    source_kind: SourceKind,
    asset: Asset,
    identifiers: list[AssetIdentifier],
) -> list[ObservedAssetClaim]:
    # Structured formats receive their normative row/cell/path locators from
    # their adapters in E04. Until then they remain uncertain rather than
    # receiving a fabricated PDF-like locator.
    if source_kind is not SourceKind.PDF:
        return []
    pages = _pdf_pages(path)

    namespace_by_kind = {
        item.kind: item.namespace
        for item in identifiers
        if item.kind in _STRONG
    }
    claims: list[ObservedAssetClaim] = []
    seen: set[tuple[str, str, int]] = set()
    for page_number, text in pages:
        for claim_kind, pattern in _EXPLICIT.items():
            for match in pattern.finditer(text):
                raw_value = match.group(1).strip()
                namespace = namespace_by_kind.get(claim_kind, f"observed_{claim_kind}")
                key = (claim_kind, _normalize(raw_value), page_number)
                if key in seen:
                    continue
                seen.add(key)
                quote = match.group(0).strip()
                claims.append(
                    ObservedAssetClaim(
                        claim_kind=claim_kind,
                        namespace=namespace,
                        raw_value=raw_value,
                        normalized_value=_normalize(raw_value),
                        locator=PdfLocator(
                            page=page_number,
                            quote=quote,
                            extraction_method="native_text",
                        ),
                    )
                )
        for identifier in identifiers:
            if identifier.kind not in _STRONG or _normalize(identifier.value) not in _normalize(text):
                continue
            key = (identifier.kind, _normalize(identifier.value), page_number)
            if key in seen:
                continue
            seen.add(key)
            matching_line = next(
                (line.strip() for line in text.splitlines() if _normalize(identifier.value) in _normalize(line)),
                identifier.value,
            )
            claims.append(
                ObservedAssetClaim(
                    claim_kind=identifier.kind,
                    namespace=identifier.namespace,
                    raw_value=identifier.value,
                    normalized_value=_normalize(identifier.value),
                    locator=PdfLocator(
                        page=page_number,
                        quote=matching_line,
                        extraction_method="native_text",
                    ),
                )
            )
        for claim_kind, expected in (("brand", asset.brand), ("model", asset.model)):
            key = (claim_kind, _normalize(expected), page_number)
            if key in seen or _normalize(expected) not in _normalize(text):
                continue
            seen.add(key)
            matching_line = next(
                (line.strip() for line in text.splitlines() if _normalize(expected) in _normalize(line)),
                expected,
            )
            claims.append(
                ObservedAssetClaim(
                    claim_kind=claim_kind,
                    namespace=f"manufacturer_{claim_kind}",
                    raw_value=expected,
                    normalized_value=_normalize(expected),
                    locator=PdfLocator(
                        page=page_number,
                        quote=matching_line,
                        extraction_method="native_text",
                    ),
                )
            )
    return claims


def decide_assessment(
    claims: list[ObservedAssetClaim],
    identifiers: list[AssetIdentifier],
) -> tuple[AssessmentOutcome, list[str]]:
    expected = {
        (item.kind, item.namespace): _normalize(item.value)
        for item in identifiers
        if item.kind in _STRONG
    }
    strong_matches = 0
    conflicts: list[str] = []
    for claim in claims:
        if claim.claim_kind not in _STRONG:
            continue
        expected_value = expected.get((claim.claim_kind, claim.namespace))
        if expected_value is None:
            continue
        if claim.normalized_value == expected_value:
            strong_matches += 1
        else:
            conflicts.append(claim.claim_kind.upper())
    if conflicts:
        return AssessmentOutcome.INCOMPATIBLE, [f"STRONG_IDENTIFIER_CONFLICT_{item}" for item in sorted(set(conflicts))]
    if strong_matches:
        return AssessmentOutcome.COMPATIBLE, ["STRONG_IDENTIFIER_MATCH"]
    if any(claim.claim_kind in {"brand", "model"} for claim in claims):
        return AssessmentOutcome.UNCERTAIN, ["CONTEXTUAL_IDENTITY_SIGNALS_ONLY"]
    return AssessmentOutcome.UNCERTAIN, ["NO_STRONG_IDENTIFIER"]
