"""Visual catalog of the quality profile: page routes, verified image regions and diagram layout.

The model may propose regions and diagram paths; the system validates every box against the PDF,
hashes the rendered pixels and assigns all IDs. Nothing here creates a fact: regions and paths are
evidence the extraction may cite, checked like any other.
"""

from __future__ import annotations

import base64
import hashlib
from pathlib import Path

import fitz

from backend.kg_v3.contracts import DocumentMap, PageLabel
from backend.kg_v3.ontology import _object
from backend.kg_v3.quality_contracts import PageRoute, PathStep, SourceRegion
from backend.kg_v3.run_state import atomic_bytes, stable_id
from backend.kg_v3.source_index import add_region, add_visual_entry
from backend.kg_v3.vision import IMAGE_ZOOM, PageImages, layout_pages

ROUTE_SYSTEM = (
    "Classify this physical PDF page for diagnostic knowledge. Image density alone is not diagnostic "
    "evidence. Preserve uncertainty. Cite the supplied region if classifiable."
)
LAYOUT_SYSTEM = (
    "Locate printed diagnostic questions, outcomes, arrows and destinations. Return unrotated PDF-point "
    "bboxes. Preserve literal Yes/No; never repair an arrow using technical knowledge. A conflict is only a "
    "printed contradiction (for example an outcome label that contradicts its own question): list it with "
    "the keys of the regions involved. Missing arrowheads, continuations on other pages and other "
    "uncertainty are ambiguities, not conflicts. These are proposals; a separate verifier will judge them."
)
PATH_KEYS = ("question", "outcome", "transition", "destination")


def route_inventory(doc, policy) -> list[PageRoute]:
    """Layout statistics decide which pages are candidates for a visual reading; not relevance."""
    routes = []
    layouts = layout_pages(doc)
    for page in range(1, doc.page_count + 1):
        stats = doc.page_geometry.get(page, {})
        segments = doc.pages.get(page, [])
        text, table = bool(segments), any(s.table for s in segments)
        unreadable = stats.get("native_text_unreadable", not text)
        reasons = []
        if unreadable:
            reasons.append("NATIVE_TEXT_UNREADABLE")
        if page in layouts:
            reasons.append("SHORT_BLOCK_LAYOUT")
        if stats.get("image_area_share", 0) >= policy.visual_image_area_threshold:
            reasons.append("IMAGE_AREA_CANDIDATE")
        if stats.get("drawing_count", 0) >= policy.visual_drawing_threshold:
            reasons.append("DRAWING_DENSITY_CANDIDATE")
        if any(
            s.table and (s.table.inherited_columns or any(len(v) > 1 for v in s.table.cell_items)) for s in segments
        ):
            reasons.append("COMPLEX_TABLE")
        modes = (["TEXT"] if text else []) + (["TABLE"] if table else [])
        if reasons and (text or stats.get("image_count") or stats.get("drawing_count")):
            modes.append("VISUAL_REVIEW")
        if unreadable:
            modes.append("OCR_REVIEW")
        routes.append(
            PageRoute(
                page=page, routes=modes, reasons=reasons or ["READABLE_NATIVE_TEXT"], native_text_unreadable=unreadable
            )
        )
    return routes


def catalog_page_region(pdf, doc, index, page, *, bbox=None, kind="PAGE", outdir=None):
    """Validate PDF coordinates, render the region and register it under the hash of its pixels."""
    with fitz.open(pdf) as source:
        sheet = source[page - 1]
        bounds = sheet.rect * sheet.derotation_matrix
        # Floats always: the same box given as integers must keep the same region ID.
        unrotated = tuple(float(v) for v in (bbox or tuple(bounds)))
        clip = fitz.Rect(unrotated)
        if clip.is_empty or not bounds.contains(clip):
            raise ValueError("visual bbox outside unrotated PDF page")
        pixmap = sheet.get_pixmap(
            matrix=fitz.Matrix(IMAGE_ZOOM, IMAGE_ZOOM), clip=clip * sheet.rotation_matrix, alpha=False
        )
        data = pixmap.tobytes("png")
        sha = hashlib.sha256(data).hexdigest()
        region_id = stable_id("region", [index.identity.document_id, page, [round(v, 2) for v in unrotated], sha])
        path = Path(outdir) / "crops" / (region_id + ".png") if outdir else None
        if path:
            atomic_bytes(path, data)
        overlaps = [s.segment_id for s in doc.pages.get(page, []) if s.bbox and fitz.Rect(s.bbox).intersects(clip)]
        region = SourceRegion(
            region_id=region_id,
            document_id=index.identity.document_id,
            page=page,
            bbox=unrotated,
            page_width=bounds.width,
            page_height=bounds.height,
            render_fingerprint=sha,
            segment_ids=overlaps,
            kind=kind,
            rotation=sheet.rotation,
            image_path=str(path or ""),
        )
        return add_region(index, region), "data:image/png;base64," + base64.b64encode(data).decode()


async def classify_visual_pages(llm, pdf, doc, index, policy, outdir=None, *, state=None) -> list[PageRoute]:
    """Ask, page by page and from the image, whether a candidate page holds diagnostic knowledge."""
    records = []
    for route in route_inventory(doc, policy):
        if "VISUAL_REVIEW" not in route.routes:
            continue
        ref, image = catalog_page_region(pdf, doc, index, route.page, outdir=outdir)
        schema = _object(
            {
                "relevance": {"type": "string", "enum": ["DIAGNOSTIC", "OTHER", "UNRESOLVED"]},
                "reason": {"type": "string"},
                "evidence_ref_ids": {"type": "array", "items": {"type": "string", "enum": [ref]}},
            }
        )
        name = f"visual_route_response_{route.page}"
        try:
            response = state.load(name) if state else None
            if response is None:
                response = await llm.json(
                    name="kg_quality_visual_route",
                    schema=schema,
                    images=[image],
                    max_output_tokens=4000,
                    system=ROUTE_SYSTEM,
                    user=index.packet_text([ref]),
                )
                if state:
                    state.save(name, response)
            relevant = response.get("relevance", "UNRESOLVED")
            if relevant not in {"DIAGNOSTIC", "OTHER", "UNRESOLVED"} or ref not in response.get("evidence_ref_ids", []):
                relevant = "UNRESOLVED"
            route = route.model_copy(
                update={
                    "relevance": relevant,
                    "evidence_ref_ids": [ref],
                    "confidence_class": "VERIFIED_REVIEW" if relevant != "UNRESOLVED" else "UNCLEAR",
                    "reasons": route.reasons + [str(response.get("reason", ""))],
                }
            )
            if relevant == "DIAGNOSTIC" and not doc.pages.get(route.page):
                add_visual_entry(index, [ref])  # the extraction verifies its interpretation and scope
        except Exception as exc:
            route = route.model_copy(
                update={"evidence_ref_ids": [ref], "reasons": route.reasons + [type(exc).__name__]}
            )
        records.append(route)
    return records


def apply_visual_routes(page_map, routes, doc) -> DocumentMap:
    """A page the visual reading found diagnostic joins the map, confirmed; an unresolved one is noted."""
    by_page = {r.page: r for r in routes}
    entries = []
    for entry in page_map.entries:
        route = by_page.get(entry.page)
        if route and route.relevance == "DIAGNOSTIC":
            entry = entry.model_copy(
                update={
                    "label": PageLabel.DIAGNOSTIC,
                    "confirmed": True,
                    "evidence": sorted(set(entry.evidence + route.evidence_ref_ids)),
                }
            )
        if route and route.relevance == "UNRESOLVED":
            doc.page_geometry.setdefault(entry.page, {}).update(
                route_unresolved=True, route_reason="VISUAL_ROUTE_UNRESOLVED"
            )
        entries.append(entry)
    return DocumentMap(entries=entries)


class QualityImages(PageImages):
    """Page images of the base profile plus crops of catalogued regions."""

    def __init__(self, pdf, doc, index, *, max_images=6):
        super().__init__(pdf, doc)
        self.index = index
        self.max_images = max_images
        self.pages.update(r.page for r in index.regions.values())

    def crops(self, region_ids) -> list[str]:
        """Checksum-verified crops of catalogued regions. Above the image cap the whole pages are
        sent instead, which contain every region; more pages than the cap is an explicit error."""
        regions = [self.index.regions[r] for r in dict.fromkeys(region_ids) if r in self.index.regions]
        if len(regions) > self.max_images:
            pages = sorted({r.page for r in regions})
            if len(pages) > self.max_images:
                raise ValueError("IMAGE_PACKET_LIMIT: split evidence or defer; no silent truncation")
            return [catalog_page_region(self.pdf, self.doc, self.index, page)[1] for page in pages]
        urls = []
        for region in regions:
            path = Path(region.image_path) if region.image_path else None
            if path and path.exists():
                data = path.read_bytes()
                if hashlib.sha256(data).hexdigest() == region.render_fingerprint:
                    urls.append("data:image/png;base64," + base64.b64encode(data).decode())
                    continue
            urls.append(
                catalog_page_region(self.pdf, self.doc, self.index, region.page, bbox=region.bbox, kind=region.kind)[1]
            )
        return urls


def _layout_schema():
    text = {"type": "string"}
    region = _object(
        {
            "key": text,
            "bbox": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
            "role": {"type": "string", "enum": ["question", "outcome", "transition", "destination", "heading"]},
            "transcription": text,
        }
    )
    path = _object({"question": text, "outcome": text, "outcome_value": text, "transition": text, "destination": text})
    # A conflict is a printed contradiction tied to its regions; an unclear arrow is an ambiguity.
    conflict = _object({"description": text, "keys": {"type": "array", "items": text}})
    return _object(
        {
            "regions": {"type": "array", "items": region},
            "paths": {"type": "array", "items": path},
            "conflicts": {"type": "array", "items": conflict},
            "ambiguities": {"type": "array", "items": text},
        }
    )


async def read_visual_structure(llm, pdf, doc, index, route, outdir=None, *, state=None):
    """Catalogue the diagram of a page without text: regions, question-outcome-arrow paths, conflicts."""
    whole = route.evidence_ref_ids[0]
    _, image = catalog_page_region(pdf, doc, index, route.page, outdir=outdir)
    name = f"visual_layout_response_{route.page}"
    raw = state.load(name) if state else None
    if raw is None:
        raw = await llm.json(
            name="kg_quality_visual_layout",
            schema=_layout_schema(),
            images=[image],
            max_output_tokens=12000,
            system=LAYOUT_SYSTEM,
            user=index.packet_text([whole]),
        )
        if state:
            state.save(name, raw)
    keys = {}
    for proposal in raw.get("regions", []):
        try:
            ref, _ = catalog_page_region(
                pdf, doc, index, route.page, bbox=proposal["bbox"], kind=proposal["role"], outdir=outdir
            )
        except (KeyError, ValueError, TypeError):
            index.dispositions.append({"reason": "INVALID_VISUAL_BBOX", "proposal": proposal})
            continue
        keys[proposal["key"]] = ref
        index.evidence[ref] = index.evidence[ref].model_copy(
            update={
                "transcription": str(proposal.get("transcription", "")),
                "transcription_method": "MODEL_PROPOSAL",
                "transcription_status": "UNCHECKED",
            }
        )
    used = set()
    whole_branches = [b.branch_id for b in index.branches.values() if b.branch_anchor_refs == [whole]]
    for path in raw.get("paths", []):
        if any(path.get(k) not in keys for k in PATH_KEYS):
            index.dispositions.append({"reason": "UNRESOLVED_VISUAL_PATH", "proposal": path})
            continue
        q, o, t, d = (keys[path[k]] for k in PATH_KEYS)
        if t in used:
            continue
        used.add(t)
        step = PathStep(
            question_ref=q, outcome_ref=o, transition_ref=t, destination_ref=d, outcome_value=path["outcome_value"]
        )
        add_visual_entry(
            index,
            [t],
            heading_refs=[q, o, d, whole],
            path_steps=[step],
            diagram_id=stable_id("diagram", [index.identity.document_id, route.page]),
            scope_evidence_refs=[q, o, t, d],
        )
    if used:  # paths replace the provisional whole-page entry
        for branch_id in whole_branches:
            index.entries.pop(index.branches.pop(branch_id).entry_id, None)
        index.ref_branch.pop(whole, None)
    for conflict in raw.get("conflicts", []):
        if isinstance(conflict, str):  # responses saved before conflicts named their regions
            conflict = {"description": conflict, "keys": []}
        refs = [keys[k] for k in conflict.get("keys", []) if k in keys]
        # Only a contradiction located on specific regions quarantines the statements resting on them.
        index.dispositions.append(
            {
                "reason": "SOURCE_CONFLICT" if refs else "VISUAL_AMBIGUITY",
                "page": route.page,
                "description": conflict.get("description", ""),
                "evidence_ref_ids": refs,
            }
        )
    for note in raw.get("ambiguities", []):
        index.dispositions.append(
            {"reason": "VISUAL_AMBIGUITY", "page": route.page, "description": note, "evidence_ref_ids": []}
        )
    return raw
