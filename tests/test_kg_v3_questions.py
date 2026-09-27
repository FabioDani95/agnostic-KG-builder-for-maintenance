"""Questions show the reviewer every segment their statements cite."""

from __future__ import annotations

from backend.kg_v3.contracts import Segment, SegmentKind
from backend.kg_v3.questions import _excerpts
from backend.kg_v3.reader import DocumentText


def test_every_cited_segment_reaches_the_reviewer():
    # One problem with twelve listed causes, as in a symptom/cause matrix.
    segments = [Segment(segment_id=f"p3.b{index}", page=3, kind=SegmentKind.TEXT,
                        text=f"{index}. Cause number {index}", evidence_id=f"ev{index}")
                for index in range(1, 14)]
    doc = DocumentText(page_count=3, pages={3: segments})
    cites = [segment.segment_id for segment in segments]
    shown = [excerpt.segment_id for excerpt in _excerpts(doc, cites)]
    assert shown == cites
