"""The judge audit reads the judge's own votes from its archive and keeps the sheet blind."""

from __future__ import annotations

import hashlib
import random

from scripts.kg_v3_evaluate import build_pairs, pair_line
from scripts.kg_v3_judge_audit import pair_votes, render, sample


def _claim():
    return {"claim_id": "R1.1", "branch_id": "R1", "indicator": "No heat", "code": "", "failure": "",
            "failure_stated": False, "indicator_segments": ["p18.b1"], "failure_segments": [],
            "action": "Replace the fuse", "action_kind": "repair", "action_segments": ["p21.b2"],
            "component": "", "component_segments": [], "conditions": "se il fusibile è aperto"}


def _edges():
    common = {"trusted": True, "record": "u1:A.R1", "conditions": []}
    return [{**common, "type": "MAY_INDICATE", "source": "s", "target": "c", "source_name": "No heat",
             "target_name": "Fuse open", "source_stated": True, "target_stated": False, "segments": {"p18.b1"}},
            {**common, "type": "RESOLVED_BY", "source": "c", "target": "a", "source_name": "Fuse open",
             "target_name": "Replace the fuse", "source_stated": False, "target_stated": True, "segments": {"p21.b2"}}]


def test_votes_come_from_the_archived_judge_batch_of_the_same_text():
    pairs, keys = build_pairs([_claim()], _edges())
    assert [kind for _, kind, _ in keys] == ["indicator", "action"]
    user = "\n".join(pair_line(f"P{i}", relation, group) for i, (relation, group) in enumerate(pairs, start=1))
    archive = {hashlib.sha1(user.encode()).hexdigest(): [
        {"answers": [{"id": "P1", "answer": "same"}, {"id": "P2", "answer": "different"}]},
        {"answers": [{"id": "P1", "answer": "same"}, {"id": "P2", "answer": "same"}]},
        {"answers": [{"id": "P1", "answer": "different"}, {"id": "P2", "answer": "different"}]}]}
    assert pair_votes(pairs, archive) == [2, 1]
    assert pair_votes(pairs, {}) == [None, None]


def test_the_sheet_never_shows_the_judge_verdict_and_every_manual_is_sampled():
    pairs, _ = build_pairs([_claim()], _edges())
    relation, group = pairs[1]
    item = {"manual": "m", "run": "v3_r1", "claim": "R1.1", "kind": "action", "judge": "different", "votes_same": 1,
            "reference": relation, "claim_data": _claim(), "graph_problems": ["No heat"],
            "extracted": [{**edge, "segments": sorted(edge["segments"]), "target_kind": "repair"} for edge in group]}
    text = "\n".join(render(item, 1, {"p21.b2": (21, "Replace the fuse.")}, "Oven"))
    assert "different" not in text and "votes" not in text and "- Giudizio: `?`" in text
    assert "Ramo del gold: problema «No heat»" in text and "«Replace the fuse» (riparazione)" in text
    pools = {"a": ([{**item, "claim": f"R{i}"} for i in range(10)], [item]),
             "b": ([{**item, "manual": "b", "claim": "R1"}, {**item, "manual": "b", "claim": "R2"}], [])}
    chosen = sample(pools, 5, 1, random.Random(1))
    assert sum(entry["manual"] == "b" for entry in chosen) == 2 and len(chosen) == 6
