"""Strict, scoped, one-to-one diagnostic scoring, independent of production.

Semantic equivalences are explicit annotations. No lexical threshold can turn a
negation, different code, different branch or inspection into a match.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value))).strip().casefold()


def canonical(value: str, equivalents: dict[str, str]) -> str:
    value = normalized(value)
    return equivalents.get(value, value)


def branch_signature(branch: dict[str, Any], equivalents: dict[str, str]) -> tuple:
    def term(value):
        return canonical(value, equivalents)
    return (
        tuple(sorted(term(v) for v in branch.get("symptoms", []))),
        tuple(sorted(normalized(v) for v in branch.get("codes", []))),
        term(branch.get("failure", "")), term(branch.get("component", "")),
        tuple((term(v["text"]), v["polarity"], v["applies_to"], v.get("step_index")) for v in branch.get("conditions", [])),
        tuple(term(v) for v in branch.get("inspections", [])),
        tuple(term(v) for v in branch.get("actions", [])),
        branch.get("resolution_status"),
    )


def score_branches(gold: dict, predictions: list[dict], *, allow_proposed: bool = False) -> dict:
    validated = gold.get("validation_status") == "technician_validated"
    if not validated and not allow_proposed:
        return {"status": "pending_technician_validation", "semantic_precision": None, "semantic_recall": None}
    if validated and not gold.get("adjudication", {}).get("reviewer_id"):
        raise ValueError("Technician validation requires an auditable reviewer identity")
    refs = gold.get("branches", [])
    if validated and any(not ref.get("source_occurrence_id") for ref in refs):
        raise ValueError("Validated gold requires independently annotated source occurrence identities")
    scope = set(gold["scope_pages"])
    exhaustive = bool(gold.get("scope_exhaustive"))
    equivalences = {normalized(k): normalized(v) for k, v in gold.get("equivalences", {}).items()}
    in_scope, outside, boundary = [], [], []
    for prediction in predictions:
        pages = set(prediction.get("pages", []))
        roots = set(prediction.get("root_pages", []))
        if roots:
            if roots <= scope:
                in_scope.append(prediction)
            elif roots & scope:
                boundary.append(prediction)
            else:
                outside.append(prediction)
        elif not pages or (pages & scope and not pages <= scope):
            boundary.append(prediction)
        elif pages & scope:
            in_scope.append(prediction)
        else:
            outside.append(prediction)
    published = [p for p in in_scope if p.get("disposition") == "publish"]
    signatures = [branch_signature(item, equivalences) for item in refs]
    neighbours = {
        i: [j for j, signature in enumerate(signatures)
            if branch_signature(pred, equivalences) == signature
            and (not refs[j].get("source_occurrence_id") or pred.get("source_occurrence_id") == refs[j]["source_occurrence_id"])
            and set(pred.get("pages", [])) & set(refs[j].get("pages", []))]
        for i, pred in enumerate(published)
    }
    # Maximum-cardinality bipartite assignment. A duplicate prediction cannot
    # earn credit for the same reference a second time.
    assigned: dict[int, int] = {}
    def augment(i, seen):
        for j in neighbours[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in assigned or augment(assigned[j], seen):
                assigned[j] = i
                return True
        return False
    for i in neighbours:
        augment(i, set())
    matches = [{"reference_id": refs[j]["branch_id"], "prediction_id": published[i]["branch_id"]} for j, i in sorted(assigned.items())]
    matched_predictions = set(assigned.values())
    # Exact signatures form a lower-bound screen, not semantic adjudication.
    # Human judgments of the unmatched predictions are required for precision.
    return {
        "status": "strict_screen_expert_gold" if validated else "exploratory_proposed_annotations",
        "matching_policy": "source_occurrence_exact_or_annotated_equivalence_one_to_one_v2",
        "matches": matches, "matched_branches": len(matches), "reference_branches": len(refs),
        "autonomous_exact_recall_lower_bound": len(matches) / len(refs) if refs else None,
        "semantic_precision": None, "semantic_recall": None,
        "unmatched_predictions_requiring_adjudication": [p["branch_id"] for i, p in enumerate(published) if i not in matched_predictions],
        "unmatched_references": [r["branch_id"] for j, r in enumerate(refs) if j not in assigned],
        "in_scope_dispositions": dict(Counter(p.get("disposition") for p in in_scope)),
        "outside_scope_unscored": len(outside), "boundary_or_missing_scope_unscored": len(boundary),
        "scope_exhaustive": exhaustive,
        "unmatched_prediction_is_automatic_false_positive": False,
        "diagnostic_accounting_is_recall": False,
    }


def load_gold(path: Path) -> dict:
    return json.loads(path.read_text())
