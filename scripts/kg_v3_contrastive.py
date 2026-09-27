"""Reviewable contrast candidates; reuse semantic KPI witnesses, with no duplicate judge calls."""
from __future__ import annotations

import json
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

from backend.kg_v3.checker import normalize_name


def generate(claims: list[dict], threshold: float = .72) -> dict:
    pairs = []
    for field, kind in (("failure", "FailureMode"), ("indicator", "Symptom")):
        entries = {}
        for claim in claims:
            name = claim.get(field, "")
            if not name or (field == "indicator" and claim.get("code")):
                continue
            entry = entries.setdefault(normalize_name(name), {"name": name, "claim_ids": []})
            entry["claim_ids"].append(claim["claim_id"])
        for (a, left), (b, right) in combinations(entries.items(), 2):
            similarity = SequenceMatcher(None, a, b).ratio()
            if similarity >= threshold:
                pairs.append({"type": kind, "left": left, "right": right,
                              "lexical_similarity": round(similarity, 4), "review": "pending"})
    pairs.sort(key=lambda item: (-item["lexical_similarity"], item["type"], item["left"]["name"]))
    return {"status": "candidates_for_Fabio_review", "threshold": threshold,
            "note": "Lexical neighbours are not necessarily semantically different. Set review to keep/drop after checking the PDF.",
            "pairs": [{"id": f"C{i}", **pair} for i, pair in enumerate(pairs, 1)]}


def write_candidates(path: Path, claims: list[dict]) -> dict:
    if path.exists():  # human decisions must survive subsequent evaluation
        return json.loads(path.read_text())
    data = generate(claims)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return data


def score_contrasts(contrasts: dict, witnesses: dict) -> dict:
    details = []
    for pair in contrasts["pairs"]:
        if pair.get("review") == "drop":
            continue
        sides = []
        for side in ("left", "right"):
            sets = [set(witnesses.get(cid, {}).get(pair["type"], [])) for cid in pair[side]["claim_ids"]]
            sides.append(set.intersection(*sets) if sets else set())
        kept = bool(sides[0] and sides[1] and not (sides[0] & sides[1]))
        details.append({"id": pair["id"], "kept": kept, "review": pair.get("review", "pending"),
                        "left_nodes_with_own_actions": sorted(sides[0]),
                        "right_nodes_with_own_actions": sorted(sides[1])})
    return {"contrastive_pairs_kept": [sum(item["kept"] for item in details), len(details)],
            "contrastive_reviewed_pairs_kept": [sum(item["kept"] for item in details if item["review"] == "keep"),
                                                 sum(item["review"] == "keep" for item in details)],
            "contrastive_status": "provisional" if any(item["review"] == "pending" for item in details) else "reviewed",
            "contrastive_details": details}
