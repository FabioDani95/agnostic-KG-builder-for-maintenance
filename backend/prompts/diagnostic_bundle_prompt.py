"""Provider-neutral instructions for typed diagnostic record extraction."""

from __future__ import annotations


def build_diagnostic_bundle_prompt(*, source_type: str, source_title: str) -> str:
    """Return the semantic policy; the response shape is supplied by Pydantic."""

    return f"""You extract diagnostic records from a technical manual into a typed contract.

Source type: {source_type}
Source title: {source_title}

The input contains physical page markers and opaque [[EVIDENCE_ID: ...]] anchors. It can be
a complete scoped manual section or a system-owned RECORD_WINDOW block. For a RECORD_WINDOW,
echo its window_id and allowed_source_anchors on every candidate; the system overwrites and
verifies both fields and no evidence outside that block is allowed. For a section chunk, set
record_window_id="" and set allowed_source_anchors to exactly the anchors referenced by that
candidate. Never use an anchor that is not printed in the input. In a window, ROOT CELL
context may support only its repeated record indicator; only CURRENT ATOMIC RECORD fields
belong to the current cause/remedy branch. Each displayed FIELD value is one exact source
span. Quote the value only: never include the "FIELD n:" label, join separate fields, or
restore a sibling field omitted by the system.
Return every explicit diagnostic record and every distinct cause/remedy branch in the input.
The contract is an intermediate record representation, not the final graph.

Rules:
1. Never emit graph IDs or ontology relation names. The system owns them.
2. A diagnostic record has one or more indicators. An indicator is either an observable
   symptom or an asset-generated error/alarm code. A record may explicitly contain both;
   keep both. For a symptom set code=null and a real severity; for an error_code set its
   code and severity=null. Only an explicit not_diagnostic page disposition may use an empty
   indicator list.
3. Keep one candidate per source branch. Do not pair an indicator, cause, component or action
   from different table rows, flowchart branches or unrelated paragraphs.
4. A FailureMode is an explicit technical cause or faulty state, not a restatement of the
   symptom, an inspection result or an invented explanation. Use null when none is stated.
5. A CorrectiveAction is an explicitly restorative remedy for that failure. Checks and tests
   are not restorative unless the source says the check itself resolves the fault. Preserve
   a non-restorative check/test/inspection in inspection_steps, never in actions.
6. Set resolution_status:
   - action_stated: at least one restorative action is explicitly linked to the failure;
   - no_action_stated: the diagnostic record states a failure but no remedy;
   - check_only: it gives only diagnostic checks/verification;
   - ambiguous: the row/branch pairing cannot be established safely;
   - not_diagnostic: a candidate-looking passage is actually preventive/generic content.
7. An affected component is optional. Include it only if the branch explicitly identifies the
   affected component. category and failure.material_context are required-but-nullable: use
   null rather than manufacturing a category/context. A null category does not invalidate a
   grounded branch; the deterministic compiler supplies a neutral schema category. Do not use
   a product name as a component.
8. Evidence is edge-specific. claim_evidence proves only the claim. Each edge evidence list is
   a support set: one span may explicitly state the whole link, or several spans from the same
   record/branch may collectively establish it when a manual separates Problem, Cause and
   Remedy across blocks or pages. failure_link_evidence supports only that exact indicator to
   failure; resolution_link_evidence supports only that exact failure to action;
   affects_link_evidence supports only that exact failure to component. Include every span
   needed to establish the link and no unrelated nearby heading. Never use an action-only span
   as the sole proof of an indicator-to-failure edge.
   In a system-owned atomic table row, use the exact endpoint FIELD spans as the edge support
   set; the deterministic compiler verifies the table structure and completes their union.
9. Every quote is a short verbatim span contained in the EvidenceUnit named by source_anchor,
   on source_page. Prefer one span per EvidenceUnit. If wording crosses adjacent units, emit
   separate exact spans; never concatenate or paraphrase cells. Copy the opaque anchor exactly.
   Do not include page/anchor marker text in a quote.
10. record_anchor must be one of this candidate's claim-evidence anchors. branch_anchor must be
    one of this candidate's evidence anchors (prefer a causal edge anchor). For an explicit
    not_diagnostic disposition with no claims, set both to the candidate page's EvidenceUnit
    anchor. These anchors are source locators, not freely generated IDs.
11. Preserve source language in human-readable values and set source_language accordingly.
12. Duplicate records caused by overlapping pages must be returned identically; deterministic
    lineage and compilation will deduplicate them.
13. Account for candidate-looking passages. If one is actually generic/preventive content,
    emit a not_diagnostic candidate with empty indicators and no diagnostic claims. Return an
    empty records list only when the input contains no candidate-looking passage at all. Never
    fill a missing cause/action simply to make a complete record.
14. Every anchored candidate-looking passage in the input must occur in a record's claim/edge
    evidence, or have its own explicit not_diagnostic disposition. Do not cover only the first
    row or branch of a troubleshooting table.
15. For check_only, actions must be empty and inspection_steps must preserve each stated check
    with exact evidence. For not_diagnostic, inspection_steps and all diagnostic claims are empty.
"""
