"""Advisory heuristic that detects tautological (Symptom, FailureMode) pairs.

The ontology prompt instructs the LLM to extract Symptoms as *observable* events
and FailureModes as *stative causes*, but in practice the model often emits
paraphrases: SYM "Alarm displayed" + FM "A fault occurs". The pair is
structurally valid, semantically useless.

This service runs as an advisory pass after semantic validation. For each
MAY_INDICATE edge it evaluates three cheap heuristics:

  * sim_score        — Jaccard overlap on normalized tokens of name+description
  * cause_token      — FailureMode description contains a recognized causal cue
                       (broken, loose, worn, dead, misaligned, ...)
  * eventive_predicate — Symptom uses an eventive predicate (is displayed,
                       develops, occurs, appears). We only care about this to
                       confirm the Symptom is behaving like a Symptom.

If sim_score is high AND the FailureMode has no causal token, we emit a
PipelineIssue with code=`symptom_failure_duplicate`. The issue is consumed by
the existing reflective loop (semantic_issues → re_extract).

No LLM call. Cost: O(n) over MAY_INDICATE edges.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from backend.models import OntologyInstance, PipelineIssue


_CAUSE_TOKENS: frozenset[str] = frozenset({
    "broken", "loose", "misaligned", "dead", "worn", "disconnected",
    "out of adjustment", "incorrect", "dirty", "saturated", "depleted",
    "cracked", "overheated", "obstructed", "blocked", "leaking",
    "phased incorrectly", "out of tolerance", "faulty", "defective",
    "short circuited", "short-circuited", "open circuit", "corroded",
    "contaminated", "missing", "damaged", "unstable", "stuck",
    "seized", "jammed", "fractured", "bent", "deformed", "warped",
    "pinched", "severed", "burnt", "burned", "melted", "oxidized",
    "deteriorated", "ruptured", "clogged",
    "incorrectly", "improperly", "insufficient",
    "low", "high", "exceeds", "below",
    "aged", "expired", "worn out", "worn-out",
})


_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")


def _normalize_tokens(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(str(text or ""))]


def _jaccard(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    set_a = set(a)
    set_b = set(b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def _cause_tokens_in(text: str) -> set[str]:
    lowered = str(text or "").lower()
    hits: set[str] = set()
    if not lowered:
        return hits
    for token in _CAUSE_TOKENS:
        if " " in token:
            if token in lowered:
                hits.add(token)
        else:
            if re.search(rf"\b{re.escape(token)}\b", lowered):
                hits.add(token)
    return hits


def _contains_cause_token(text: str) -> bool:
    return bool(_cause_tokens_in(text))


def _has_distinctive_cause_token(failure_text: str, symptom_text: str) -> bool:
    """True iff the failure mode mentions a causal token the symptom does not.

    The Symptom and FailureMode can share a word like "damaged" — that doesn't
    count as causal context, because it's the same observation restated.
    A real FailureMode adds *new* stative/causal information.
    """
    failure_tokens = _cause_tokens_in(failure_text)
    symptom_tokens = _cause_tokens_in(symptom_text)
    return bool(failure_tokens - symptom_tokens)


@dataclass
class PairReport:
    symptom_id: str
    symptom_name: str
    failure_mode_id: str
    failure_mode_name: str
    sim_score: float
    has_cause_token: bool


def evaluate_type_consistency(
    ontology: OntologyInstance,
    *,
    similarity_threshold: float = 0.85,
) -> tuple[list[PipelineIssue], list[PairReport]]:
    """Return (issues, reports) for MAY_INDICATE pairs on the given ontology.

    Each PairReport documents a scored pair. An issue is emitted only when
    sim_score >= similarity_threshold AND the FailureMode text lacks any
    recognized causal token, signalling a likely tautological duplicate.
    """
    symptoms_by_id: dict[str, dict] = {
        str(node.get("symptom_id", "")).strip(): node
        for node in ontology.nodes.get("Symptom", [])
        if isinstance(node, dict) and node.get("symptom_id")
    }
    failure_modes_by_id: dict[str, dict] = {
        str(node.get("failure_mode_id", "")).strip(): node
        for node in ontology.nodes.get("FailureMode", [])
        if isinstance(node, dict) and node.get("failure_mode_id")
    }

    issues: list[PipelineIssue] = []
    reports: list[PairReport] = []

    for relation in ontology.relations:
        if relation.name != "MAY_INDICATE":
            continue
        symptom = symptoms_by_id.get(str(relation.from_id).strip())
        failure = failure_modes_by_id.get(str(relation.to_id).strip())
        if not symptom or not failure:
            continue

        symptom_text = f"{symptom.get('name', '')} {symptom.get('description', '')}"
        failure_text = (
            f"{failure.get('name', '')} "
            f"{failure.get('description', '')} "
            f"{failure.get('material_context', '')}"
        )
        sim_score = _jaccard(_normalize_tokens(symptom_text), _normalize_tokens(failure_text))
        has_cause_token = _has_distinctive_cause_token(failure_text, symptom_text)
        report = PairReport(
            symptom_id=str(relation.from_id).strip(),
            symptom_name=str(symptom.get("name", "")),
            failure_mode_id=str(relation.to_id).strip(),
            failure_mode_name=str(failure.get("name", "")),
            sim_score=round(sim_score, 3),
            has_cause_token=has_cause_token,
        )
        reports.append(report)

        if sim_score >= similarity_threshold and not has_cause_token:
            issues.append(PipelineIssue(
                severity="error",
                code="symptom_failure_duplicate",
                message=(
                    f"FailureMode '{failure.get('name', '')}' (id={relation.to_id}) "
                    f"is a lexical restatement of Symptom '{symptom.get('name', '')}' "
                    f"(id={relation.from_id}) with no stative/causal description "
                    f"(similarity={sim_score:.2f})."
                ),
                target_type="FailureMode",
                target_id=str(relation.to_id).strip(),
                property_name="description",
                fix_hint=(
                    "Rewrite the FailureMode in causal form — name a component AND a "
                    "stative condition (worn, loose, misaligned, dead, disconnected, "
                    "out of adjustment, ...). If the source text does not support a "
                    "real causal statement, REMOVE this FailureMode and its MAY_INDICATE "
                    "edge instead of restating the symptom."
                ),
            ))

    return issues, reports
