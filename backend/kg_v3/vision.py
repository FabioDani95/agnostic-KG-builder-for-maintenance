"""Page images where the layout carries meaning, and the opt-in visual check of table relations."""

from __future__ import annotations

import base64
from pathlib import Path

import fitz

from backend.kg_v3.checker import statement
from backend.kg_v3.contracts import Tier, VerifierVerdict, Witness
from backend.kg_v3.ontology import verification_schema
from backend.kg_v3.prompts import VERIFY_PROMPT

LAYOUT_MIN_SEGMENTS = 8
LAYOUT_SHORT_CHARS = 40
LAYOUT_SHORT_SHARE = 0.5
IMAGE_ZOOM = 1.3
MAX_IMAGES = 6


def layout_pages(doc) -> set[int]:
    """Pages whose text layer is broken into many short pieces: flowcharts, labelled diagrams.

    Tables are read in place by the reader and do not count. The rule looks only at
    the length of text segments, never at their words.
    """

    pages = set()
    for page, segments in doc.pages.items():
        text = [segment for segment in segments if segment.table is None]
        short = sum(len(segment.text) <= LAYOUT_SHORT_CHARS for segment in text)
        if len(text) >= LAYOUT_MIN_SEGMENTS and short >= LAYOUT_SHORT_SHARE * len(text):
            pages.add(page)
    return pages


class PageImages:
    """Images of layout pages, and where each text segment sits on them.

    The model reads the arrows and boxes on the image and cites the segments by ID;
    the position (per cent of width and height) ties an ID to its place on the image.
    """

    def __init__(self, pdf: Path, doc) -> None:
        self.pdf = Path(pdf)
        self.doc = doc
        self.pages = layout_pages(doc)
        self._images: dict[int, str] = {}
        self._sizes: dict[int, tuple[float, float]] = {}

    def _render(self, page: int) -> None:
        with fitz.open(self.pdf) as source:
            sheet = source[page - 1]
            pixmap = sheet.get_pixmap(matrix=fitz.Matrix(IMAGE_ZOOM, IMAGE_ZOOM), alpha=False)
            self._images[page] = "data:image/png;base64," + base64.b64encode(pixmap.tobytes("png")).decode()
            self._sizes[page] = (sheet.rect.width, sheet.rect.height)

    def for_segments(self, segment_ids) -> tuple[list[str], dict[str, str]]:
        segments = self.doc.segments(list(segment_ids))
        pages = sorted({segment.page for segment in segments} & self.pages)[:MAX_IMAGES]
        for page in pages:
            if page not in self._images:
                self._render(page)
        marks = {}
        for segment in segments:
            if segment.page in pages and segment.bbox:
                width, height = self._sizes[segment.page]
                marks[segment.segment_id] = (f" @{round(100 * segment.bbox[0] / width)},"
                                             f"{round(100 * segment.bbox[1] / height)}")
        return [self._images[page] for page in pages], marks


def table_dependent(doc, relation) -> bool:
    return any(s.table and (s.table.confirmed_inherited_columns or any(len(v) > 1 for v in s.table.cell_items))
               for s in doc.segments(relation.assertion.certificate.segment_ids))


def row_images(pdf, doc, cites) -> list[str]:
    images = []
    with fitz.open(pdf) as source:
        for segment in doc.segments(cites):
            if not segment.table or not segment.bbox:
                continue
            page = source[segment.page - 1]
            # Full row width with modest vertical context. True spanning cells are
            # already included in the geometric row box supplied by the reader.
            rect = fitz.Rect(segment.bbox) + (-8, -18, 8, 18)
            rect &= page.rect
            if rect.is_empty:
                continue
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), clip=rect, alpha=False)
            images.append('data:image/png;base64,' + base64.b64encode(pix.tobytes('png')).decode())
    return images[:3]


async def visual_check(checker, doc, relations, pdf, *, limit=12):
    selected = [r for r in relations if r.assertion.tier is Tier.GREEN and table_dependent(doc, r)][:max(0, limit)]
    replacements, records = {}, []
    for relation in selected:
        cert = relation.assertion.certificate
        images = row_images(pdf, doc, cert.segment_ids)
        if not images:
            records.append({'id': relation.assertion.assertion_id, 'status': 'no_crop'})
            continue
        data = await checker.llm.json(name='kg_v3_visual_verify', schema=verification_schema(['S1']),
            system=VERIFY_PROMPT + '\nCheck row and list alignment on the supplied PDF crops as well as text.',
            user=f'Statement S1: {statement(checker.spec, relation.proposals[0])}\nCited text:\n'
                 + checker._evidence_text(doc, cert.segment_ids), images=images, max_output_tokens=1500)
        raw = next((v.get('verdict') for v in data.get('verdicts', []) if v.get('id') == 'S1'), 'unclear')
        verdict = VerifierVerdict(raw)
        witnesses = [w for w in cert.witnesses if w is not Witness.VERIFIER]
        if verdict is VerifierVerdict.SUPPORTED:
            witnesses.append(Witness.VERIFIER)
        updated = cert.model_copy(update={'witnesses': witnesses, 'verifier_verdict': verdict,
            'notes': cert.notes + [f'PDF crop verification: {verdict.value}']})
        replacements[relation.assertion.assertion_id] = relation.model_copy(update={
            'assertion': relation.assertion.model_copy(update={'certificate': updated})})
        records.append({'id': relation.assertion.assertion_id, 'status': verdict.value,
                        'segments': cert.segment_ids, 'crops': len(images)})
    return [replacements.get(r.assertion.assertion_id, r) for r in relations], records
