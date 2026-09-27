"""Opt-in visual verification of already-green list/merged-cell relations."""

from __future__ import annotations

import base64

import fitz

from backend.kg_v3.checker import statement
from backend.kg_v3.contracts import Tier, VerifierVerdict, Witness
from backend.kg_v3.ontology import verification_schema
from backend.kg_v3.prompts import VERIFY_PROMPT


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
