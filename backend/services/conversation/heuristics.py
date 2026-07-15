"""Message-intent heuristics and deterministic status replies for the chat.

Extracted from orchestrator.py (stabilization P5): everything here is
deterministic — regex/keyword intent detection, store status snapshots and
the direct replies built from them. No LLM calls, no event emission.
"""

from __future__ import annotations

import re
from typing import Any

from backend.graph.state import GraphPhase
from backend.services.conversation.tools import build_extraction_memory_snapshot


def contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def phase_label(phase: str) -> str:
    return {
        GraphPhase.LOADED.value: "manual loaded",
        GraphPhase.SCOPING.value: "scoping",
        GraphPhase.ONTOLOGY_DRAFT.value: "ontology drafting",
        GraphPhase.EXTRACTION.value: "ontology review",
        GraphPhase.VALIDATION.value: "triplet review",
        GraphPhase.EXPORT.value: "export",
        GraphPhase.COMPLETED.value: "completed",
    }.get(phase, phase)


def normalise_query(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


SCOPE_ANCHORS = (
    "manual",
    "document",
    "pdf",
    "page",
    "pages",
    "section",
    "sections",
    "toc",
    "table of contents",
    "scope",
    "scoping",
    "cut plan",
    "selected",
    "selection",
    "extraction",
    "extract",
    "ontology",
    "triplet",
    "triplets",
    "validation",
    "validate",
    "review",
    "export",
    "workflow",
    "process",
    "progress",
    "metrics",
    "metric",
    "metriche",
    "kpi",
    "kpis",
    "cost",
    "costs",
    "costo",
    "costi",
    "duration",
    "durata",
    "token",
    "tokens",
    "status",
    "phase",
    "next step",
    "node",
    "nodes",
    "relation",
    "relations",
    "graph",
    "modify",
    "modifica",
    "editor",
    "field",
    "fields",
    "asset",
    "assets",
    "component",
    "components",
    "symptom",
    "symptoms",
    "failure mode",
    "failure modes",
    "corrective action",
    "corrective actions",
    "error code",
    "error codes",
    "manuale",
    "documento",
    "pagina",
    "pagine",
    "sezione",
    "sezioni",
    "estrazione",
    "ontologia",
    "tripla",
    "triplette",
    "validazione",
    "revisione",
    "stato",
    "fase",
    "progresso",
)


PROCESS_COMMAND_PREFIXES = (
    "approve",
    "confirm",
    "continue",
    "proceed",
    "go ahead",
    "next",
    "skip",
    "discard",
    "save",
    "export",
    "resume",
    "rerun",
    "re-run",
    "re-extract",
    "reextract",
    "re-scope",
    "rescope",
    "retry",
    "yes",
    "ok",
    "okay",
    "continua",
    "procedi",
    "avanti",
    "vai avanti",
)


CONFIRM_WORDS = (
    "yes",
    "y",
    "ok",
    "okay",
    "confirm",
    "confirmed",
    "proceed",
    "go ahead",
    "continue",
    "si",
    "sì",
    "confermo",
    "procedi",
    "continua",
    "vai",
    "vai avanti",
)


CANCEL_WORDS = (
    "no",
    "nope",
    "cancel",
    "stop",
    "abort",
    "annulla",
    "ferma",
    "stoppa",
    "lascia stare",
)


RERUN_WORDS = (
    "redo",
    "rerun",
    "re-run",
    "run again",
    "restart",
    "start over",
    "repeat",
    "rifai",
    "rifare",
    "rifallo",
    "rifarla",
    "ricalcola",
    "ricomincia",
    "ripeti",
)


CONTINUE_COMMANDS = (
    "continue",
    "continue to extraction",
    "proceed",
    "go ahead",
    "next",
    "ok",
    "okay",
    "yes",
    "start extraction",
    "run extraction",
    "continua",
    "continua con extraction",
    "continua con estrazione",
    "procedi",
    "procedi con extraction",
    "procedi con estrazione",
    "avanti",
    "vai avanti",
)


def compress_page_ranges(pages: list[int]) -> str:
    ordered = sorted({int(p) for p in (pages or []) if isinstance(p, int)})
    if not ordered:
        return "none yet"

    ranges: list[str] = []
    start = prev = ordered[0]
    for page in ordered[1:]:
        if page == prev + 1:
            prev = page
            continue
        ranges.append(f"{start}" if start == prev else f"{start}-{prev}")
        start = prev = page
    ranges.append(f"{start}" if start == prev else f"{start}-{prev}")
    return ", ".join(ranges)


TRAILING_PAGE_RANGE_RE = re.compile(r"\s*\(pp?\.\s*\d+\s*[-–]\s*\d+\)\s*$", re.IGNORECASE)


def clean_section_name(name: str, start: int, end: int) -> str:
    cleaned = TRAILING_PAGE_RANGE_RE.sub("", str(name or "").strip()).strip(" -–")
    return cleaned or f"Section {start}-{end}"


def render_section_list(sections: list[dict[str, Any]], limit: int | None = None) -> str:
    if not sections:
        return "none yet"

    shown = sections if limit is None else sections[:limit]
    rendered = "; ".join(
        f"{idx}. {sec['name']} (pp. {sec['start']}-{sec['end']})"
        for idx, sec in enumerate(shown, start=1)
    )
    if limit is not None and len(sections) > limit:
        rendered += f"; … and {len(sections) - limit} more"
    return rendered


def section_facts(cut_plan: dict[str, Any], limit: int | None = 12) -> tuple[list[dict[str, Any]], str]:
    raw_sections = list(cut_plan.get("sections") or [])
    facts: list[dict[str, Any]] = []
    for sec in raw_sections:
        if not isinstance(sec, dict):
            continue
        start = int(sec.get("start") or 0)
        end = int(sec.get("end") or 0)
        facts.append({
            "name": clean_section_name(str(sec.get("name") or "Section"), start, end),
            "start": start,
            "end": end,
        })

    if not facts:
        return [], "none yet"

    return facts, render_section_list(facts, limit=limit)


def has_scope_anchor(text: str, status: dict[str, Any]) -> bool:
    if contains_any(text, SCOPE_ANCHORS):
        return True

    for section in (status.get("sections") or []):
        name = normalise_query(str(section.get("name") or ""))
        if name and name in text:
            return True

    filename = normalise_query(str(status.get("filename") or "").replace(".pdf", " "))
    filename_tokens = [token for token in filename.split() if len(token) >= 4]
    return any(token in text for token in filename_tokens[:8])


def is_short_process_command(text: str) -> bool:
    return any(text == prefix or text.startswith(f"{prefix} ") for prefix in PROCESS_COMMAND_PREFIXES)


def status_snapshot(store: dict[str, Any]) -> dict[str, Any]:
    gs = store.get("graph_state") or {}
    cut_plan = store.get("cut_plan") or {}
    pipeline_state = store.get("ontology_pipeline") or gs.get("ontology_pipeline") or {}
    selected_pages = list(cut_plan.get("pages_to_keep") or gs.get("selected_pages") or [])
    sections, rendered_sections = section_facts(cut_plan)
    rendered_sections_full = render_section_list(sections, limit=None)
    total_pages = (
        cut_plan.get("total_pages")
        or gs.get("total_pages")
        or len(store.get("pages") or [])
    )
    phase = gs.get("current_phase", GraphPhase.LOADED.value)
    return {
        "filename": store.get("filename") or gs.get("filename") or "the manual",
        "phase": phase,
        "selected_pages_count": len(selected_pages),
        "selected_pages": selected_pages,
        "selected_page_ranges": compress_page_ranges(selected_pages),
        "total_pages": int(total_pages or 0),
        "section_count": len(sections),
        "sections": sections,
        "rendered_sections": rendered_sections,
        "rendered_sections_full": rendered_sections_full,
        "next_step": gs.get("next_step"),
        "run_status": gs.get("run_status", "loaded"),
        "ontology_status": pipeline_state.get("status") if isinstance(pipeline_state, dict) else None,
        "ontology_node_count": ontology_node_count(pipeline_state),
        "schema_issue_count": len((pipeline_state or {}).get("schema_issues") or []) if isinstance(pipeline_state, dict) else 0,
        "human_required_count": len((pipeline_state or {}).get("human_required_fields") or []) if isinstance(pipeline_state, dict) else 0,
        "graph_issue_count": len((pipeline_state or {}).get("graph_issues") or []) if isinstance(pipeline_state, dict) else 0,
        "suggested_relation_count": len((pipeline_state or {}).get("suggested_relations") or []) if isinstance(pipeline_state, dict) else 0,
        "triplet_count": len(gs.get("cleaned_triplets") or []),
        "validated_triplet_count": len(store.get("validated_triplets") or []),
        "review_index": int(store.get("review_index") or 0),
        "extraction_memory": build_extraction_memory_snapshot(store, limit_per_type=5),
    }


def ontology_node_count(pipeline_state: dict[str, Any] | None) -> int:
    if not isinstance(pipeline_state, dict):
        return 0
    ontology = pipeline_state.get("ontology") or {}
    nodes = ontology.get("nodes") if isinstance(ontology, dict) else {}
    if not isinstance(nodes, dict):
        return 0
    return sum(len(items) for items in nodes.values() if isinstance(items, list))


def workflow_blockers(store: dict[str, Any]) -> tuple[list[str], str]:
    status = status_snapshot(store)
    phase = status["phase"]
    blockers: list[str] = []

    if phase == GraphPhase.LOADED.value:
        return ["Scoping has not started yet."], "Start scoping to select the diagnostic pages."

    if phase == GraphPhase.SCOPING.value:
        if status["selected_pages_count"]:
            return (
                ["The section selection still needs operator approval."],
                "Review the Section Selection widget, then approve it to draft the ontology.",
            )
        return (
            ["Scoping has not produced a section selection yet."],
            "Wait for scoping to finish or rerun scoping if it failed.",
        )

    if phase == GraphPhase.ONTOLOGY_DRAFT.value:
        if not (store.get("ontology_pipeline") or (store.get("graph_state") or {}).get("ontology_pipeline")):
            return (
                ["Ontology drafting has not produced a reviewable draft yet."],
                "Wait for ontology drafting to finish.",
            )
        if status["human_required_count"]:
            blockers.append(f"{status['human_required_count']} required ontology field(s) still need values.")
        if blockers:
            return blockers, "Fill the required fields shown in the Ontology Draft widget before continuing."
        if status["schema_issue_count"]:
            return [], (
                "Continue to Extraction. Schema issues are still reported on the draft, "
                "but they do not block triplet extraction."
            )
        return [], "Continue to Extraction. Suggested graph links are optional and do not block extraction."

    if phase in (GraphPhase.EXTRACTION.value, GraphPhase.VALIDATION.value):
        triplet_count = status["triplet_count"]
        if not triplet_count:
            return ["Triplet extraction has not produced reviewable triplets yet."], "Run extraction."
        remaining = max(0, triplet_count - status["review_index"])
        if remaining:
            return [f"{remaining} triplet(s) still need review."], "Approve, edit, or skip the next triplet."
        return [], "Triplet review is complete. Continue to export."

    if phase == GraphPhase.EXPORT.value:
        return [], "Export the ontology JSON."

    if phase == GraphPhase.COMPLETED.value:
        return [], "The workflow is complete. You can inspect or modify the exported graph."

    return [], status["next_step"] or "Continue with the current workflow step."


def workflow_status_reply(store: dict[str, Any]) -> str:
    status = status_snapshot(store)
    blockers, next_action = workflow_blockers(store)
    parts = [
        f"Current phase: **{phase_label(status['phase'])}**.",
        f"Scoping: {status['selected_pages_count']}/{status['total_pages']} page(s), {status['section_count']} section(s).",
    ]
    if status["ontology_node_count"] or status["ontology_status"]:
        parts.append(
            "Ontology: "
            f"{status['ontology_node_count']} node(s), "
            f"{status['human_required_count']} required field(s), "
            f"{status['schema_issue_count']} schema issue(s), "
            f"{status['suggested_relation_count']} suggested link(s)."
        )
    if status["triplet_count"]:
        parts.append(
            f"Triplets: {status['review_index']}/{status['triplet_count']} reviewed, "
            f"{status['validated_triplet_count']} validated."
        )
    if blockers:
        parts.append("Blocking item(s): " + " ".join(blockers))
    else:
        parts.append("No hard blocker is currently preventing the next step.")
    parts.append(f"Next step: {next_action}")
    return " ".join(parts)


def maybe_build_scope_guard_reply(store: dict[str, Any], user_message: str | None) -> str | None:
    text = normalise_query(user_message or "")
    if not text or text.startswith("[system:"):
        return None

    status = status_snapshot(store)
    if has_scope_anchor(text, status) or is_short_process_command(text):
        return None

    return (
        "I can only help with the loaded manual and this extraction workflow. "
        f"The active document is **{status['filename']}** and the current phase is {phase_label(status['phase'])}. "
        "Ask me about the document, selected pages or sections, ontology or triplets, validation, export, graph editing, or current progress."
    )


OPINION_MARKERS = (
    "think",
    "opinion",
    "sense",
    "good",
    "right",
    "correct",
    "ok to",
    "okay to",
    "should i",
    "should we",
    "do you think",
    "what do you",
    "reasonable",
    "weird",
    "strange",
    "suspicious",
    "issue",
    "problem",
    "improve",
    "better",
    "why is",
    "why are",
    "why does",
    "pensi",
    "opinione",
    "giusto",
    "sbagliato",
    "strano",
    "ha senso",
    "andare bene",
    "va bene",
    "perché",
    "perche",
)


def wants_reasoning(text: str) -> bool:
    return any(marker in text for marker in OPINION_MARKERS)


def maybe_build_direct_status_reply(store: dict[str, Any], user_message: str | None) -> str | None:
    text = normalise_query(user_message or "")
    if not text:
        return None

    # If the operator is asking for judgment/reasoning, let the LLM handle it
    # instead of short-circuiting to a canned count/fact.
    if wants_reasoning(text):
        return None

    status = status_snapshot(store)
    filename = status["filename"]
    phase = status["phase"]
    selected_pages_count = status["selected_pages_count"]
    selected_page_ranges = status["selected_page_ranges"]
    total_pages = status["total_pages"]
    section_count = status["section_count"]
    status["rendered_sections"]
    rendered_sections_full = status["rendered_sections_full"]
    next_step = status["next_step"] or "not set"

    asks_page_count = (
        ("page" in text or "pagine" in text)
        and any(token in text for token in (
            "how many",
            "number of",
            "count",
            "quante",
            "quanti",
            "how much",
        ))
        and any(token in text for token in (
            "selected",
            "keep",
            "scope",
            "selezionat",
            "ten",
            "scoping",
        ))
    )
    asks_selected_pages = (
        ("page" in text or "pagine" in text)
        and contains_any(text, (
            "which pages",
            "what pages",
            "show pages",
            "list pages",
            "selected pages",
            "quali pagine",
            "che pagine",
            "pagine selezionate",
        ))
    )
    asks_sections = contains_any(text, (
        "what sections",
        "which sections",
        "list sections",
        "show sections",
        "repeat the section",
        "repeat the sections",
        "repeat section",
        "repeat sections",
        "show section selection again",
        "repeat the selected sections",
        "repeat selected sections",
        "can you repeat the section",
        "can you repeat the sections",
        "selected sections",
        "section selection",
        "quali sezioni",
        "che sezioni",
        "sezioni selezionate",
    ))
    asks_section_count = (
        ("section" in text or "sezion" in text)
        and contains_any(text, ("how many", "number of", "count", "quante", "quanti"))
    )
    asks_manual = contains_any(text, (
        "what manual",
        "which manual",
        "what document",
        "which document",
        "manual loaded",
        "document loaded",
        "file loaded",
        "quale manuale",
        "quale documento",
        "che manuale",
        "che documento",
        "documento caricato",
        "manuale caricato",
    ))
    asks_total_pages = (
        ("page" in text or "pagine" in text)
        and contains_any(text, (
            "total",
            "in total",
            "whole document",
            "document has",
            "manual has",
            "totali",
            "totale",
            "intero documento",
            "manuale ha",
        ))
    )
    asks_progress = any(
        token in text for token in (
            "where are we",
            "show progress",
            "current progress",
            "current status",
            "what's the status",
            "whats the status",
            "which phase",
            "what phase",
            "a che punto",
            "stato",
            "fase",
            "progresso",
        )
    )
    asks_next_step = contains_any(text, (
        "next step",
        "what's next",
        "whats next",
        "what happens next",
        "cosa succede dopo",
        "prossimo step",
        "prossima fase",
        "passo successivo",
    ))
    asks_blockers = contains_any(text, (
        "what blocks",
        "what is blocking",
        "what's blocking",
        "whats blocking",
        "blocked",
        "blocker",
        "blockers",
        "what is missing",
        "what's missing",
        "whats missing",
        "missing to proceed",
        "needed to proceed",
        "what do we need",
        "cosa blocca",
        "cosa ci blocca",
        "che cosa blocca",
        "blocc",
        "cosa manca",
        "che manca",
        "manca per procedere",
        "manca per andare avanti",
        "cosa serve",
    ))

    if not any((
        asks_page_count,
        asks_selected_pages,
        asks_sections,
        asks_section_count,
        asks_manual,
        asks_total_pages,
        asks_progress,
        asks_next_step,
        asks_blockers,
    )):
        return None

    if asks_blockers:
        blockers, next_action = workflow_blockers(store)
        if blockers:
            return (
                "The workflow is currently blocked by: "
                + " ".join(blockers)
                + f" Next step: {next_action}"
            )
        return f"Nothing is blocking the workflow right now. Next step: {next_action}"

    if asks_manual:
        return f"The loaded document is **{filename}**."

    if asks_sections:
        if section_count:
            return (
                f"The current cut plan contains {section_count} section(s): {rendered_sections_full}."
            )
        return "I don't have any selected sections yet."

    if asks_section_count:
        return f"The current cut plan contains {section_count} section(s)."

    if asks_selected_pages:
        if selected_pages_count:
            return (
                f"The current cut plan covers {selected_pages_count} page(s) out of {total_pages}. "
                f"Selected page ranges: {selected_page_ranges}."
            )
        return "I don't have any selected pages yet."

    if asks_total_pages:
        return f"The loaded document has {total_pages} total page(s)."

    if phase == GraphPhase.SCOPING.value:
        if selected_pages_count:
            reply = (
                f"I'm still in scoping. The current cut plan selects {selected_pages_count} pages "
                f"out of {total_pages} total, across {section_count} section(s). "
                "That is the same count shown in the Section Selection widget."
            )
            if asks_next_step:
                reply += f" The next recorded step is: {next_step}."
            return reply
        return (
            "I'm still in scoping. I haven't locked a page selection yet — I'm still identifying "
            "the relevant sections."
        )

    if asks_next_step:
        blockers, next_action = workflow_blockers(store)
        blocker_text = " ".join(blockers) if blockers else "No hard blocker."
        return f"The current phase is {phase_label(phase)}. {blocker_text} Next step: {next_action}"

    if asks_page_count and selected_pages_count:
        return (
            f"The current workflow has {selected_pages_count} selected page(s) out of {total_pages} total."
        )

    if asks_progress:
        return workflow_status_reply(store)

    return f"The current phase is {phase_label(phase)}."


def detect_inventory_request(text: str) -> tuple[str, dict[str, Any]] | None:
    normalised = normalise_query(text)
    if not normalised:
        return None

    asks_nodes = contains_any(normalised, (
        "which nodes",
        "what nodes",
        "list nodes",
        "show nodes",
        "node types",
        "types of nodes",
        "extracted nodes",
        "extracted entities",
        "ontology nodes",
        "quali nodi",
        "che nodi",
        "nodi estratti",
        "tipi di nodi",
        "tipo di nodi",
        "tipi estratti",
        "entita estratte",
        "entità estratte",
    ))
    if asks_nodes:
        args: dict[str, Any] = {"limit": 60, "include_descriptions": False}
        type_map = {
            "asset": "Asset",
            "assets": "Asset",
            "component": "Component",
            "components": "Component",
            "symptom": "Symptom",
            "symptoms": "Symptom",
            "sintom": "Symptom",
            "failure mode": "FailureMode",
            "failure modes": "FailureMode",
            "guast": "FailureMode",
            "corrective action": "CorrectiveAction",
            "corrective actions": "CorrectiveAction",
            "azione correttiva": "CorrectiveAction",
            "azioni correttive": "CorrectiveAction",
            "error code": "ErrorCode",
            "codice errore": "ErrorCode",
        }
        for marker, node_type in type_map.items():
            if marker in normalised:
                args["node_type"] = node_type
                break
        if contains_any(normalised, ("description", "descrizione", "details", "dettagli")):
            args["include_descriptions"] = True
        return "list_extracted_nodes", args

    asks_triplets = contains_any(normalised, (
        "which triplets",
        "what triplets",
        "list triplets",
        "show triplets",
        "extracted triplets",
        "triplet chains",
        "quali triplette",
        "che triplette",
        "triplette estratte",
        "catene estratte",
    ))
    if asks_triplets:
        return "list_extracted_triplets", {"status": "all", "limit": 12}

    return None


def format_triplet_inventory_message(result: dict[str, Any]) -> str:
    if int(result.get("total_triplets") or 0) == 0:
        return "I do not have extracted triplets yet in the current workflow."
    lines = [str(result.get("message") or "Extracted triplets:")]
    for item in result.get("triplets") or []:
        symptom = item.get("symptom") or {}
        failure_modes = item.get("failure_modes") or []
        corrective_actions = item.get("corrective_actions") or []
        fm_names = ", ".join(str(fm.get("name") or fm.get("id") or "") for fm in failure_modes if fm)
        action_names = ", ".join(str(ca.get("name") or ca.get("id") or "") for ca in corrective_actions if ca)
        lines.append(
            f"{int(item.get('index', 0)) + 1}. "
            f"{symptom.get('name') or symptom.get('id') or 'Symptom'} -> "
            f"{fm_names or 'no failure mode'} -> "
            f"{action_names or 'no corrective action'} "
            f"({item.get('status')})."
        )
    if result.get("truncated"):
        lines.append("This is a compact list; ask for a smaller status or search term to narrow it.")
    return "\n".join(lines)


def is_confirm_message(text: str) -> bool:
    return text in CONFIRM_WORDS or any(text.startswith(f"{word} ") for word in CONFIRM_WORDS)


def is_cancel_message(text: str) -> bool:
    return text in CANCEL_WORDS or any(text.startswith(f"{word} ") for word in CANCEL_WORDS)


def is_continue_command(text: str) -> bool:
    if contains_any(text, ("what", "which", "where", "show", "tell", "cosa", "quale", "qual ", "a che", "?")):
        return False
    return text in CONTINUE_COMMANDS or any(text.startswith(f"{cmd} ") for cmd in CONTINUE_COMMANDS)


def detect_rerun_action(text: str, store: dict[str, Any]) -> str | None:
    if not (contains_any(text, RERUN_WORDS) or "re-scope" in text or "rescope" in text or "re-extract" in text):
        return None

    if contains_any(text, ("scope", "scoping", "cut plan", "section selection", "re-scope", "rescope", "sezioni", "scoping")):
        return "propose_cut_plan"
    if contains_any(text, ("ontology", "ontologia", "draft", "nodes", "nodi")):
        return "draft_ontology"
    if contains_any(text, ("extract", "extraction", "estrazione", "triplet", "triplets", "triplette", "re-extract")):
        return "run_extraction"

    phase = (store.get("graph_state") or {}).get("current_phase")
    if phase == GraphPhase.SCOPING.value:
        return "propose_cut_plan"
    if phase == GraphPhase.ONTOLOGY_DRAFT.value:
        return "draft_ontology"
    if phase in (GraphPhase.EXTRACTION.value, GraphPhase.VALIDATION.value):
        return "run_extraction"
    return None


def action_label(action: str) -> str:
    return {
        "propose_cut_plan": "scoping",
        "draft_ontology": "ontology drafting",
        "run_extraction": "triplet extraction",
    }.get(action, action.replace("_", " "))


def action_already_completed(action: str, store: dict[str, Any]) -> bool:
    gs = store.get("graph_state") or {}
    if action == "propose_cut_plan":
        cut_plan = store.get("cut_plan") or gs.get("cut_plan") or {}
        return bool(cut_plan.get("pages_to_keep") or cut_plan.get("sections"))
    if action == "draft_ontology":
        return bool(store.get("ontology_pipeline") or gs.get("ontology_pipeline"))
    if action == "run_extraction":
        return bool(gs.get("cleaned_triplets") or gs.get("raw_triplets"))
    return False
