"""Offline atomic fact/branch scoring. Historical gold and scorer remain untouched."""

from __future__ import annotations

import argparse
import json
import random
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pydantic import Field  # noqa: E402

from backend.kg_v3.quality_contracts import QualityContract  # noqa: E402
from backend.kg_v3.run_state import atomic_json, digest, file_hash, stable_id  # noqa: E402


def normal(value):
    # Preserve negation, symbols, units, direction, codes and leading zeros.
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


class GoldFact(QualityContract):
    fact_id: str
    relation_type: str
    subject: dict
    object: dict
    conditions: list[dict] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    epistemic_status: str = "EXPLICIT"
    adjudication_status: str = "ADJUDICATED"
    original_claim_ids: list[str] = Field(default_factory=list)


class GoldObligation(QualityContract):
    obligation_id: str
    fact_id: str
    branch_id: str
    original_claim_ids: list[str]


class GoldBranch(QualityContract):
    branch_id: str
    obligation_ids: list[str]
    anchor_segments: list[str]
    required_context: list[dict] = Field(default_factory=list)
    adjudication_status: str = "ADJUDICATED"


def fact_meaning(fact):
    def endpoint(e):
        return {k: normal(e.get(k, "")) for k in ("type", "name", "code", "kind", "denotation_status")}

    return {
        "relation": fact["relation_type"],
        "subject": endpoint(fact["subject"]),
        "object": endpoint(fact["object"]),
        "conditions": sorted(
            [{k: normal(c.get(k, "")) for k in ("kind", "text", "scope")} for c in fact.get("conditions", [])],
            key=digest,
        ),
        "epistemic_status": fact.get("epistemic_status", "EXPLICIT"),
    }


def project_gold(gold, adjudication=None):
    """Exact dedup only. Compound/ambiguous gold awaits a separate human decision."""
    adjudication = adjudication or {}
    facts, obligations, branches, excluded = {}, {}, {}, []
    expanded = [
        {**original, **part}
        for original in gold.get("claims", [])
        for part in adjudication.get("split_claims", {}).get(original["claim_id"], [{}])
    ]
    for original in expanded:
        claim = {**original, **adjudication.get("claim_overrides", {}).get(original["claim_id"], {})}
        branch_id, claim_id = claim["branch_id"], claim["claim_id"]
        conditions = claim.get("typed_conditions") or []
        ambiguous = (
            bool(claim.get("conditions") and not conditions) or claim.get("adjudication_status") == "NOT_ADJUDICATED"
        )
        indicator = {
            "type": "ErrorCode" if claim.get("code") else "Symptom",
            "name": claim.get("indicator", ""),
            "code": claim.get("code", ""),
            "kind": "",
            "denotation_status": "STATED",
        }
        failure = {
            "type": "FailureMode",
            "name": claim.get("failure", ""),
            "code": "",
            "kind": "",
            "denotation_status": "STATED" if claim.get("failure_stated", True) else "INFERRED",
        }
        action = {
            "type": "CorrectiveAction",
            "name": claim.get("action", ""),
            "kind": claim.get("action_kind", ""),
            "code": "",
            "denotation_status": "STATED",
        }
        pieces = []
        if indicator["name"] and failure["name"]:
            pieces.append(
                (
                    "INDICATES" if indicator["code"] else "MAY_INDICATE",
                    indicator,
                    failure,
                    claim.get("indicator_segments", []) + claim.get("failure_segments", []),
                )
            )
        elif indicator["name"]:
            pieces.append(("MENTION", indicator, indicator, claim.get("indicator_segments", [])))
        if action["name"]:
            if failure["name"]:
                pieces.append(
                    (
                        "RESOLVED_BY",
                        failure,
                        action,
                        claim.get("failure_segments", []) + claim.get("action_segments", []),
                    )
                )
            else:
                pieces.append(("MENTION", action, action, claim.get("action_segments", [])))
        if claim.get("component"):
            if claim.get("affects_adjudicated") is True and failure["name"]:
                component = {
                    "type": "Component",
                    "name": claim["component"],
                    "code": "",
                    "kind": "",
                    "denotation_status": "STATED",
                }
                pieces.append(
                    (
                        "AFFECTS",
                        failure,
                        component,
                        claim.get("failure_segments", []) + claim.get("component_segments", []),
                    )
                )
            else:
                excluded.append({"claim_id": claim_id, "field": "component", "reason": "NOT_ADJUDICATED_AS_AFFECTS"})
        if not pieces:
            excluded.append({"claim_id": claim_id, "reason": "NO_ASSERTED_FACT"})
        branch = branches.setdefault(
            branch_id,
            {
                "obligation_ids": [],
                "anchor_segments": set(),
                "required_context": conditions,
                "adjudication_status": "ADJUDICATED",
            },
        )
        if ambiguous:
            branch["adjudication_status"] = "NOT_ADJUDICATED"
        for relation, left, right, evidence in pieces:
            body = {
                "relation_type": relation,
                "subject": left,
                "object": right,
                "conditions": conditions,
                "evidence": sorted(set(evidence)),
                "epistemic_status": "INFERRED_FROM_TEXT"
                if failure["name"] and failure["denotation_status"] == "INFERRED"
                else "EXPLICIT",
                "adjudication_status": "NOT_ADJUDICATED" if ambiguous else "ADJUDICATED",
            }
            fact_id = stable_id("gold_fact", body)
            if fact_id not in facts:
                facts[fact_id] = GoldFact(fact_id=fact_id, **body, original_claim_ids=[claim_id]).model_dump(
                    mode="json"
                )
            else:
                facts[fact_id]["original_claim_ids"] = sorted(set(facts[fact_id]["original_claim_ids"] + [claim_id]))
            oid = stable_id("obligation", [fact_id, branch_id])
            obligation = obligations.setdefault(
                oid,
                GoldObligation(
                    obligation_id=oid, fact_id=fact_id, branch_id=branch_id, original_claim_ids=[claim_id]
                ).model_dump(mode="json"),
            )
            obligation["original_claim_ids"] = sorted(set(obligation["original_claim_ids"] + [claim_id]))
            branch["obligation_ids"].append(oid)
            branch["anchor_segments"].update(evidence)
    projected_branches = [
        GoldBranch(
            branch_id=b,
            **{
                **v,
                "anchor_segments": sorted(v["anchor_segments"]),
                "obligation_ids": sorted(set(v["obligation_ids"])),
            },
        ).model_dump(mode="json")
        for b, v in sorted(branches.items())
    ]
    entity_facts = {}
    for fact in facts.values():
        branches_ = sorted({o["branch_id"] for o in obligations.values() if o["fact_id"] == fact["fact_id"]})
        for end in [fact["subject"], fact["object"]]:
            if end["denotation_status"] in {"PLACEHOLDER", "TEST_CONTEXT", "UNRESOLVED"}:
                continue
            body = {
                "relation_type": "MENTION",
                "subject": end,
                "object": end,
                "conditions": [],
                "evidence": fact["evidence"],
                "epistemic_status": "INFERRED_FROM_TEXT" if end["denotation_status"] == "INFERRED" else "EXPLICIT",
                "adjudication_status": fact["adjudication_status"],
            }
            key = stable_id("gold_entity", [fact_meaning(body), body["evidence"]])
            if key not in entity_facts:
                entity_facts[key] = {**body, "fact_id": key, "branch_ids": branches_}
            else:
                entity_facts[key]["branch_ids"] = sorted(set(entity_facts[key]["branch_ids"] + branches_))
    return {
        "version": "kg-quality-gold-projection-1",
        "gold_sha256": digest(gold),
        "adjudication_sha256": digest(adjudication),
        "facts": sorted(facts.values(), key=lambda f: f["fact_id"]),
        "obligations": sorted(obligations.values(), key=lambda o: o["obligation_id"]),
        "branches": projected_branches,
        "excluded": excluded,
        "entity_facts": sorted(entity_facts.values(), key=lambda e: e["fact_id"]),
        "scope_exhaustive": bool(gold.get("scope_exhaustive", False)),
        "scope_pages": gold.get("pages", []),
    }


def predicted_facts(quality):
    index = quality["source_index"]
    public = set(quality["public_assertion_ids"])
    facts = {}
    for candidate in quality["candidates"]:
        a = candidate["assertion"]
        if a["assertion_id"] not in public:
            continue
        p = candidate["proposals"][0]
        evidence = sorted(
            {
                index["evidence"][r]["segment_id"] or index["evidence"][r]["region_id"]
                for r in a["certificate"]["evidence_ref_ids"]
            }
        )
        body = {
            "relation_type": a["relation_type"],
            "subject": p["source"],
            "object": p["target"],
            "conditions": a["conditions"],
            "evidence": evidence,
            "epistemic_status": a["certificate"]["epistemic_status"],
            "pages": sorted({index["evidence"][r]["page"] for r in a["certificate"]["evidence_ref_ids"]}),
            "method": p.get("extraction_method", "PRIMARY"),
            "trigger": p.get("review_trigger") or "PRIMARY",
            "modalities": p.get("evidence_modalities", ["TEXT"]),
            "manual": index["identity"]["document_id"],
        }
        key = stable_id("pred_fact", [fact_meaning(body), evidence])
        fact = facts.setdefault(key, {**body, "fact_id": key, "occurrences": []})
        fact["occurrences"].append(
            {
                "assertion_id": a["assertion_id"],
                "branch_id": a["branch_id"],
                "scope_status": a["scope_status"],
                "evidence": evidence,
            }
        )
        # Entity observations are evaluated separately; placeholders are not factual causes.
        for end in (p["source"], p["target"]):
            if end.get("denotation_status") in {"PLACEHOLDER", "TEST_CONTEXT", "UNRESOLVED"}:
                continue
            mention_body = {
                **body,
                "relation_type": "MENTION",
                "subject": end,
                "object": end,
                "conditions": [],
                "epistemic_status": "INFERRED_FROM_TEXT" if end.get("denotation_status") == "INFERRED" else "EXPLICIT",
            }
            mention_key = stable_id("pred_fact", [fact_meaning(mention_body), evidence])
            entity = facts.setdefault(mention_key, {**mention_body, "fact_id": mention_key, "occurrences": []})
            entity["occurrences"].append(fact["occurrences"][-1])
    return sorted(facts.values(), key=lambda f: f["fact_id"])


def align_branches(gold, quality, adjudication=None):
    explicit = (adjudication or {}).get("branch_alignment", {})
    index = quality["source_index"]
    rows = []
    for branch in gold["branches"]:
        bid = branch["branch_id"]
        if bid in explicit:
            mapping = explicit[bid]
            ids = mapping.get("branch_ids", [])
            valid = ids and all(b in index["branches"] for b in ids) and mapping.get("evidence")
            rows.append(
                {
                    "gold_branch_id": bid,
                    "branch_ids": ids if valid else [],
                    "status": mapping.get("status", "AMBIGUOUS") if valid else "INCOMPATIBLE",
                    "reason": "VERSIONED_ADJUDICATION",
                }
            )
            continue
        gold_refs = set(branch["anchor_segments"])
        candidates = []
        for b in index["branches"].values():
            refs = {index["evidence"][r]["segment_id"] for r in b["branch_anchor_refs"] + b["scope_evidence_refs"]}
            if (
                b.get("scope_status") in {"VERIFIED_STRUCTURE", "VERIFIED_REVIEW"}
                and refs - {""}
                and refs - {""} <= gold_refs
            ):
                candidates.append(b["branch_id"])
        rows.append(
            {
                "gold_branch_id": bid,
                "branch_ids": candidates if len(candidates) == 1 else [],
                "status": "VERIFIED" if len(candidates) == 1 else "AMBIGUOUS" if candidates else "INCOMPATIBLE",
                "reason": "UNIQUE_DOCUMENT_ANCHORS" if len(candidates) == 1 else "ANCHOR_ALIGNMENT_UNRESOLVED",
            }
        )
    return rows


def compatible_obligations(gold, g, prediction, alignment):
    mappings = {r["gold_branch_id"]: set(r["branch_ids"]) for r in alignment if r["status"] == "VERIFIED"}
    covered = []
    for o in gold["obligations"]:
        if o["fact_id"] != g["fact_id"]:
            continue
        branches = mappings.get(o["branch_id"], set())
        if any(
            p["branch_id"] in branches and p.get("scope_status") in {"VERIFIED_STRUCTURE", "VERIFIED_REVIEW"}
            for p in prediction["occurrences"]
        ):
            covered.append(o["obligation_id"])
    return covered


def maximum_matching(edges):
    """Min-cost augmenting paths: cardinality, obligations, then stable ID ties."""
    # Pure Python unit-capacity flow; no extra dependency or greedy partial reuse.
    gs = sorted({g for g, _, _ in edges})
    ps = sorted({p for _, p, _ in edges})
    if not gs or not ps:
        return {}
    graph = defaultdict(list)

    def arc(a, b, cost):
        graph[a].append([b, 1, cost, len(graph[b])])
        graph[b].append([a, 0, -cost, len(graph[a]) - 1])

    for g in gs:
        arc("source", ("g", g), 0)
    for p in ps:
        arc(("p", p), "sink", 0)
    scale = (len(gs) * len(ps) + 1) * (min(len(gs), len(ps)) + 1)
    for n, (g, p, obligations) in enumerate(sorted(edges)):
        arc(("g", g), ("p", p), -obligations * scale + n)
    while True:
        distance, parent = {"source": 0}, {}
        # Bellman-Ford on the residual graph, stable iteration order.
        for _ in range(len(graph)):
            changed = False
            for a in list(graph):
                if a not in distance:
                    continue
                for i, edge in enumerate(graph[a]):
                    b, cap, cost, _ = edge
                    if cap and (b not in distance or distance[a] + cost < distance[b]):
                        distance[b], parent[b], changed = distance[a] + cost, (a, i), True
            if not changed:
                break
        if "sink" not in parent:
            break
        b = "sink"
        while b != "source":
            a, i = parent[b]
            edge = graph[a][i]
            edge[1] -= 1
            graph[b][edge[3]][1] += 1
            b = a
    result = {}
    for g in gs:
        for b, cap, cost, reverse in graph[("g", g)]:
            if isinstance(b, tuple) and b[0] == "p" and cap == 0:
                result[g] = b[1]
    return result


def score(gold, predictions, alignment, judgments=None):
    judgments = judgments or {}
    gs = [g for g in gold["facts"] if g["adjudication_status"] == "ADJUDICATED"]
    edges, bindings, candidates = [], {}, []
    for g in gs:
        for p in predictions:
            if p["relation_type"] != g["relation_type"]:
                continue
            obligations = compatible_obligations(gold, g, p, alignment)
            if not obligations:
                continue
            exact = fact_meaning(g) == fact_meaning(p) and bool(set(g["evidence"]) & set(p["evidence"]))
            key = g["fact_id"] + "|" + p["fact_id"]
            judgment = judgments.get("equivalences", {}).get(key)
            hard_compatible = all(
                normal(g[side].get("type", "")) == normal(p[side].get("type", ""))
                and normal(g[side].get("code", "")) == normal(p[side].get("code", ""))
                and normal(g[side].get("kind", "")) == normal(p[side].get("kind", ""))
                for side in ("subject", "object")
            )
            equivalent = exact or judgment == "EQUIVALENT" and hard_compatible
            candidates.append(
                {
                    "gold_fact_id": g["fact_id"],
                    "prediction_fact_id": p["fact_id"],
                    "selection_reason": "VERIFIED_SCOPE_AND_TYPE",
                    "verdict": "EXACT" if exact else judgment or "UNJUDGED",
                }
            )
            if equivalent:
                edges.append((g["fact_id"], p["fact_id"], len(obligations)))
                bindings[(g["fact_id"], p["fact_id"])] = obligations
    matching = maximum_matching(edges)
    satisfied = {o for g, p in matching.items() for o in bindings[(g, p)]}
    matched = set(matching.values())
    confirmed_branches = [b for b in gold["branches"] if b["adjudication_status"] == "ADJUDICATED"]
    complete = [
        b["branch_id"] for b in confirmed_branches if b["obligation_ids"] and set(b["obligation_ids"]) <= satisfied
    ]
    triple_gs = [g for g in gs if g["relation_type"] != "MENTION"]
    triple_preds = [p for p in predictions if p["relation_type"] != "MENTION"]
    triple_matched = {
        g: p for g, p in matching.items() if next(f for f in gs if f["fact_id"] == g)["relation_type"] != "MENTION"
    }

    def classify(p):
        if p["fact_id"] in matched:
            return "TP"
        judgment = judgments.get("precision", {}).get(p["fact_id"], "UNJUDGED")
        if judgment == "UNSUPPORTED":
            return "UNSUPPORTED"
        if judgment in {"AMBIGUOUS", "UNKNOWN"}:
            return judgment
        if (
            gold.get("scope_exhaustive")
            and set(p.get("pages", [])) <= set(gold.get("scope_pages", []))
            and p.get("pages")
        ):
            return "FP"
        return "UNJUDGED"

    states = {p["fact_id"]: classify(p) for p in triple_preds}
    fp = sum(v in {"FP", "UNSUPPORTED"} for v in states.values())
    tp, fn = len(triple_matched), len(triple_gs) - len(triple_matched)
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    fully_judged = all(v in {"TP", "FP", "UNSUPPORTED"} for v in states.values())
    f1 = (
        2 * tp / (2 * tp + fp + fn)
        if fully_judged and (gold.get("scope_exhaustive") or not predictions) and 2 * tp + fp + fn
        else None
    )
    entity_gs = [
        g
        for g in gold.get("entity_facts", gs)
        if g["relation_type"] == "MENTION" and g.get("adjudication_status") == "ADJUDICATED"
    ]
    entity_ps = [p for p in predictions if p["relation_type"] == "MENTION"]
    entity_edges = []
    verified_map = {r["gold_branch_id"]: set(r["branch_ids"]) for r in alignment if r["status"] == "VERIFIED"}
    for g in entity_gs:
        branches_ = set().union(*(verified_map.get(b, set()) for b in g.get("branch_ids", [])))
        for p in entity_ps:
            if (
                fact_meaning(g) == fact_meaning(p)
                and set(g["evidence"]) & set(p["evidence"])
                and any(
                    o["branch_id"] in branches_ and o.get("scope_status") in {"VERIFIED_STRUCTURE", "VERIFIED_REVIEW"}
                    for o in p["occurrences"]
                )
            ):
                entity_edges.append((g["fact_id"], p["fact_id"], 1))
    entity_matching = maximum_matching(entity_edges)

    def breakdown(gvalues, pvalues, matching_, field):
        categories = sorted({field(v) for v in gvalues + pvalues})
        result = {}
        for category in categories:
            gg = {v["fact_id"] for v in gvalues if field(v) == category}
            pp = [v for v in pvalues if field(v) == category]
            n = sum(g in matching_ for g in gg)
            errors = sum(classify(v) in {"FP", "UNSUPPORTED"} for v in pp)
            unknown = sum(classify(v) in {"UNJUDGED", "AMBIGUOUS", "UNKNOWN"} for v in pp)
            result[category] = {
                "tp": n,
                "fp": errors,
                "fn": len(gg) - n,
                "gold_denominator": len(gg),
                "prediction_denominator": len(pp),
                "unjudged_or_ambiguous": unknown,
                "precision_judged": n / (n + errors) if n + errors else None,
                "recall": n / len(gg) if gg else None,
            }
        return result

    return {
        "definition": "atomic facts, one-to-one matching, verified branch applicability; not historical_branch_score",
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision_judged": precision,
        "precision_global": precision if fully_judged else None,
        "recall": recall,
        "f1": f1,
        "prediction_denominator": len(triple_preds),
        "non_factual_bridges": sum(p.get("epistemic_status") in {"STRUCTURAL_PLACEHOLDER", "UNRESOLVED", "SYSTEM_DERIVED"} for p in predictions),
        "gold_denominator": len(triple_gs),
        "unjudged": sum(v == "UNJUDGED" for v in states.values()),
        "ambiguous": sum(v in {"AMBIGUOUS", "UNKNOWN"} for v in states.values()),
        "unsupported": sum(v == "UNSUPPORTED" for v in states.values()),
        "entity_tp": len(entity_matching),
        "entity_gold_denominator": len(entity_gs),
        "entity_prediction_denominator": len(entity_ps),
        "entity_matching": entity_matching,
        "by_entity_type": breakdown(entity_gs, entity_ps, entity_matching, lambda v: v["subject"]["type"]),
        "by_relation": breakdown(triple_gs, triple_preds, triple_matched, lambda v: v["relation_type"]),
        "by_action_kind": breakdown(
            triple_gs, triple_preds, triple_matched, lambda v: v["object"].get("kind") or "NONE"
        ),
        "by_epistemic_status": breakdown(triple_gs, triple_preds, triple_matched, lambda v: v["epistemic_status"]),
        "by_evidence_modality": breakdown(
            triple_gs, triple_preds, triple_matched, lambda v: "+".join(v.get("modalities", ["TEXT"]))
        ),
        "branch_complete": len(complete),
        "branch_denominator": len(confirmed_branches),
        "branch_recall": len(complete) / len(confirmed_branches) if confirmed_branches else None,
        "excluded_gold_facts": len(gold["facts"]) - len(gs),
        "excluded_gold_branches": len(gold["branches"]) - len(confirmed_branches),
        "matching": matching,
        "satisfied_obligations": sorted(satisfied),
        "complete_branches": sorted(complete),
        "missing_fact_ids": sorted(g["fact_id"] for g in gs if g["fact_id"] not in matching),
        "prediction_states": states,
        "candidate_judgments": candidates,
        "alignment": alignment,
    }


def precision_sample(predictions, *, per_stratum=10, seed=1729):
    rng, strata, output = random.Random(seed), defaultdict(list), []
    for p in predictions:
        key = (
            p.get("method", "PRIMARY"),
            p.get("epistemic_status", ""),
            tuple(p.get("modalities", ["TEXT"])),
            p["relation_type"],
            p.get("manual", ""),
        )
        strata[key].append(p)
    for key, values in sorted(strata.items()):
        ordered = sorted(values, key=lambda p: p["fact_id"])
        n = min(per_stratum, len(ordered))
        for p in rng.sample(ordered, n):
            output.append(
                {
                    "fact_id": p["fact_id"],
                    "stratum": list(key),
                    "inclusion_probability": n / len(ordered),
                    "population": len(ordered),
                    "judgment": "UNJUDGED",
                    "fact": p,
                }
            )
    return output


def weighted_support_precision(sample):
    supported = judged = total = 0.0
    for row in sample:
        probability = row["inclusion_probability"]
        if not 0 < probability <= 1:
            raise ValueError("invalid inclusion probability")
        weight = 1 / probability
        total += weight
        if row["judgment"] in {"SUPPORTED", "UNSUPPORTED"}:
            judged += weight
            if row["judgment"] == "SUPPORTED":
                supported += weight
    return {
        "estimate_judged": supported / judged if judged else None,
        "lower_bound": supported / total if total else None,
        "upper_bound": (supported + total - judged) / total if total else None,
        "weighted_judged": judged,
        "weighted_population": total,
        "estimand": "source support precision under stratified probability sampling",
    }


def paired_bootstrap(documents, *, seed=1729, replicates=10000):
    rng = random.Random(seed)
    names = sorted(documents)
    if len(names) < 2:
        return {"status": "INCONCLUSIVE", "reason": "INSUFFICIENT_DOCUMENT_CLUSTERS"}
    diffs = []
    for _ in range(replicates):
        selected = rng.choices(names, k=len(names))
        differences = []
        for name in selected:
            data = documents[name]
            # Paired rows preserve reused judgments and extraction repetitions.
            strata = defaultdict(list)
            for row in data:
                strata[digest(row.get("stratum", []))].append(row)
            rows = [r for values in strata.values() for r in rng.choices(values, k=len(values))]
            base = weighted_support_precision([{**r, "judgment": r["baseline"]} for r in rows])["estimate_judged"]
            candidate = weighted_support_precision([{**r, "judgment": r["candidate"]} for r in rows])["estimate_judged"]
            if base is not None and candidate is not None:
                differences.append(candidate - base)
        if differences:
            diffs.append(sum(differences) / len(differences))
    if not diffs:
        return {"status": "INCONCLUSIVE", "reason": "NO_COMPLETED_JUDGMENTS"}
    diffs.sort()
    lower = diffs[int(0.05 * len(diffs))]
    return {
        "status": "NON_INFERIOR" if lower >= -0.02 else "NOT_ESTABLISHED",
        "lower_one_sided_95": lower,
        "seed": seed,
        "replicates": replicates,
        "document_clusters": len(names),
    }


def legacy_predictions(graph, adjudication=None, *, graph_sha256=""):
    """Descriptive historical facts; only separate source adjudication grants scope.

    This function never creates new graph certificates or certified paths.
    """
    adjudication = adjudication or {}
    if adjudication.get("legacy_fact_reviews") and adjudication.get("graph_sha256") != graph_sha256:
        raise ValueError("legacy adjudication belongs to a different graph")
    nodes = {n["id"]: n for n in graph["nodes"]}
    facts = {}
    branches = {}
    for edge in graph["edges"]:
        if edge["type"] not in {"INDICATES", "MAY_INDICATE", "RESOLVED_BY", "AFFECTS"} or edge.get("tier") == "red":
            continue
        for n, occurrence in enumerate(edge.get("occurrences", [])):
            oid = stable_id("legacy_occurrence", [graph_sha256, edge["id"], n, occurrence])
            review = adjudication.get("legacy_fact_reviews", {}).get(oid, {})
            refs = sorted({r["segment_id"] for r in occurrence.get("evidence", []) if r.get("segment_id")})
            verified = (
                review.get("verdict") == "SUPPORTED"
                and review.get("reviewer")
                and review.get("scope_evidence")
                and review.get("branch_ids")
            )

            def end(node, side):
                status = review.get(side + "_denotation_status", "LEGACY_UNCLASSIFIED")
                if status not in {
                    "STATED",
                    "INFERRED",
                    "PLACEHOLDER",
                    "TEST_CONTEXT",
                    "UNRESOLVED",
                    "LEGACY_UNCLASSIFIED",
                }:
                    raise ValueError("invalid adjudicated legacy denotation")
                return {
                    "type": node["type"],
                    "name": node["name"],
                    "code": node.get("properties", {}).get("code", ""),
                    "kind": node.get("properties", {}).get("action_kind", ""),
                    "denotation_status": status,
                }

            body = {
                "relation_type": edge["type"],
                "subject": end(nodes[edge["from"]], "subject"),
                "object": end(nodes[edge["to"]], "object"),
                "conditions": review.get("typed_conditions", occurrence.get("conditions", [])),
                "evidence": refs,
                "epistemic_status": review.get("epistemic_status", "LEGACY_UNCLASSIFIED"),
                "method": "LEGACY",
                "modalities": ["TEXT"],
                "pages": sorted({e["page"] for e in occurrence.get("evidence", [])}),
            }
            key = stable_id("pred_fact", [fact_meaning(body), refs])
            fact = facts.setdefault(key, {**body, "fact_id": key, "occurrences": []})
            for b in review.get("branch_ids", []) if verified else ["LEGACY_UNKNOWN"]:
                fact["occurrences"].append(
                    {
                        "assertion_id": oid,
                        "branch_id": b,
                        "scope_status": "VERIFIED_REVIEW" if verified else "LEGACY_UNKNOWN",
                        "evidence": refs,
                    }
                )
                branches[b] = {
                    "branch_id": b,
                    "scope_status": "VERIFIED_REVIEW" if verified else "LEGACY_UNKNOWN",
                    "adjudication": review if verified else {},
                }
    return sorted(facts.values(), key=lambda f: f["fact_id"]), branches


def structural_metrics(graph):
    """Declared graph universes; semantic merge/split error needs adjudication."""
    nodes = {n.get("node_id", n.get("id")): n for n in graph.get("nodes", [])}
    variants = {}
    for yellow in (False, True):
        for derived in (False, True):
            accepted = {"green", "yellow"} if yellow else {"green"}
            edges = [
                e for e in graph.get("edges", []) if e.get("tier") in accepted and (derived or not e.get("derived"))
            ]
            used = {e.get("source", e.get("from")) for e in edges} | {e.get("target", e.get("to")) for e in edges}
            adjacency = {n: set() for n in used if n in nodes}
            for edge in edges:
                a, b = edge.get("source", edge.get("from")), edge.get("target", edge.get("to"))
                if a in adjacency and b in adjacency:
                    adjacency[a].add(b)
                    adjacency[b].add(a)
            remaining, sizes = set(adjacency), []
            while remaining:
                stack, seen = [min(remaining)], set()
                while stack:
                    node = stack.pop()
                    if node not in seen:
                        seen.add(node)
                        stack.extend(adjacency[node] - seen)
                remaining -= seen
                sizes.append(len(seen))
            label = ("green+yellow" if yellow else "green") + ("+derived" if derived else "-derived")
            variants[label] = {
                "universe": "incident nodes of retained edges in this supplied representation",
                "nodes": len(adjacency),
                "edges": len(edges),
                "weak_components": len(sizes),
                "lcc_nodes": max(sizes, default=0),
                "lcc_share": max(sizes) / sum(sizes) if sizes else None,
                "small_component_node_share": sum(n for n in sizes if n <= 3) / sum(sizes) if sizes else None,
            }
    return {
        "views": variants,
        "nodes_before_pruning": len(nodes),
        "false_merges_adjudicated": None,
        "false_splits_adjudicated": None,
        "semantic_duplicates_adjudicated": None,
    }


def evaluation_bundle(gold, quality, adjudication=None, judgments=None):
    projected = project_gold(gold, adjudication)
    predictions = predicted_facts(quality)
    metrics = score(projected, predictions, align_branches(projected, quality, adjudication), judgments)
    sample = precision_sample([p for p in predictions if p["relation_type"] != "MENTION"])
    supplied = (judgments or {}).get("source_support_sample", {})
    sample = [{**row, "judgment": supplied.get(row["fact_id"], "UNJUDGED")} for row in sample]
    triggers = sorted({row['fact'].get('trigger', 'PRIMARY') for row in sample if row['fact'].get('method') != 'PRIMARY'})
    by_trigger = {trigger: weighted_support_precision([row for row in sample if row['fact'].get('trigger') == trigger]) for trigger in triggers}
    merge_rows = [pair for concept in quality.get('concepts', []) for pair in concept.get('equivalence_decisions', [])]
    merge_reviews = (judgments or {}).get('merge_reviews', {})
    merged_support = [{'inclusion_probability': 1, 'judgment': merge_reviews.get(stable_id('merge_decision', pair), 'UNJUDGED')}
                      for pair in merge_rows]
    return {
        "gold_projection": projected,
        'delta_source_precision_by_trigger': by_trigger,
        'merge_source_precision': weighted_support_precision(merged_support),
        "predictions": predictions,
        "metrics": metrics,
        "precision_sample": sample,
        "source_support_precision": weighted_support_precision(sample),
        "structural": structural_metrics(quality),
        "coverage": quality.get("coverage", {}),
        "validation": quality.get("validation", {}),
        "unmeasured": {
            "human_minutes": None,
            "visual_router_precision": None,
            "visual_router_recall": None,
            "merge_semantic_precision": None,
        },
        "annotation_status": "PENDING" if any(r["judgment"] == "UNJUDGED" for r in sample) else "JUDGED",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold", type=Path, required=True)
    parser.add_argument("--quality-run", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--judgments", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("output exists; use a new path")
    from backend.kg_v3.export import load_quality

    loaded = load_quality(args.quality_run)
    if loaded["binding_status"] != "VERIFIED":
        parser.error("verified quality sidecar required")
    gold = json.loads(args.gold.read_text())
    adjudication = json.loads(args.adjudication.read_text()) if args.adjudication else {}
    if adjudication and adjudication.get("gold_sha256") != file_hash(args.gold):
        parser.error("adjudication is not bound to this gold file")
    projected = project_gold(gold, adjudication)
    predictions = predicted_facts(loaded["quality"])
    judgments = json.loads(args.judgments.read_text()) if args.judgments else {}
    result = score(projected, predictions, align_branches(projected, loaded["quality"], adjudication), judgments)
    atomic_json(
        args.out,
        {
            **evaluation_bundle(gold, loaded["quality"], adjudication, judgments),
            "inputs": {"gold": file_hash(args.gold), "sidecar": file_hash(args.quality_run / "ingestion_quality.json")},
        },
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
