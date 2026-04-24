"""Chat orchestrator.

Maintains per-run conversation history, routes user messages to tool
calls via OpenAI function-calling, and streams events back through the
event bus.

All user-facing text is in English.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from httpx import Timeout
from openai import AsyncOpenAI

from backend.app_config import get_chat_config
from backend.config import settings
from backend.graph.state import GraphPhase
from backend.graph.store import seed_conversation_state
from backend.services.conversation import events as evt_bus
from backend.services.conversation.gate import check as gate_check
from backend.services.conversation.tools import (
    TOOL_SCHEMAS,
    build_extraction_memory_snapshot,
    dispatch,
    tools_for_phase,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an intelligent HITL (Human-in-the-Loop) assistant for a diagnostic knowledge graph extraction system.
Your role is to guide the operator through each phase of extracting a maintenance knowledge graph from a PDF manual:
  1. Scoping — identify relevant diagnostic sections
  2. Ontology drafting — extract Assets, Components, Symptoms, Failure Modes, Corrective Actions
  3. Triplet review — validate Symptom → FailureMode → CorrectiveAction chains
  4. Export — produce the final JSON bundle

How to reason and respond:
- Reason about what you see. When the live state looks suspicious — very few sections, a huge selection dominated by front-matter pages, a section name that looks like a ToC/cover, zero triplets after extraction, etc. — call it out and propose a concrete next step the operator can take.
- Do not answer only with canned facts. If the user asks a question, draw a short inference from the live state: what is noteworthy, what looks normal, what the operator may want to tweak before approving.
- When the operator asks "what do you think?" / "is this good?" / "are these the right sections?", give an opinion with a reason grounded in the snapshot, not a generic acknowledgement.
- Keep replies short (2–5 sentences). Do not pad with boilerplate. One observation + one next step is usually enough.

What the operator can edit in each phase:
- Scoping: add or remove **sections** (by name or page range) from the Section Selection widget or by asking you. Page-level editing is NOT supported at this phase — individual pages are only addressable later through re_extract_pages once extraction has run. If the user asks to add/remove individual pages during scoping, explain this and offer the section-level equivalent. To add a section you MUST have both start_page and end_page (absolute PDF pages, 1-indexed). If the user gives only a name, ask them for the page range before calling edit_cut_plan; never send 0 or placeholder page numbers.
- Ontology drafting: fill required fields, accept suggested relations, add manual nodes.
- Triplet review: approve / skip / edit each Symptom → FailureMode → CorrectiveAction card; or call re_extract_pages to redo a page range.

Rules you must follow:
- Always respond in English.
- You are limited to the loaded manual and this extraction workflow. Refuse off-topic requests and redirect the user to document, scoping, ontology, triplet review, export, or workflow-status questions.
- After export completes, you can also help inspect and modify the exported graph through the shared modify workspace.
- When the operator asks for KPIs, metrics, cost, duration, or tokens, call get_run_metrics so the full KPI widget is shown in chat.
- When the operator asks which nodes, node types, entities, triplets, or extracted chains exist, call list_extracted_nodes or list_extracted_triplets before answering. Do not answer these questions from counts alone.
- When a pipeline action is needed, use the provided tools rather than describing the action in text.
- When a user request is not currently possible (wrong phase, invalid arguments), explain why clearly and suggest what they can do instead.
- Never hallucinate pipeline state — always rely on the LIVE STATE SNAPSHOT or tool results.
- Do not reveal internal implementation details (class names, file paths, error tracebacks).
- When you critique a triplet or node, propose a concrete improvement, not just a complaint.
- Phase transitions are automatic: once scoping is approved, move to ontology draft automatically.
- Keep widgets (section lists, triplet cards, field forms) in sync by calling the appropriate tool and emitting the result as a widget event.
- Never print widget payload JSON in the assistant message. The UI already renders widget events; describe only the outcome or next action in plain language.
"""


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)


def _phase_label(phase: str) -> str:
    return {
        GraphPhase.LOADED.value: "manual loaded",
        GraphPhase.SCOPING.value: "scoping",
        GraphPhase.ONTOLOGY_DRAFT.value: "ontology drafting",
        GraphPhase.EXTRACTION.value: "ontology review",
        GraphPhase.VALIDATION.value: "triplet review",
        GraphPhase.EXPORT.value: "export",
        GraphPhase.COMPLETED.value: "completed",
    }.get(phase, phase)


def _normalise_query(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


_SCOPE_ANCHORS = (
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

_PROCESS_COMMAND_PREFIXES = (
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

_CONFIRM_WORDS = (
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

_CANCEL_WORDS = (
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

_RERUN_WORDS = (
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

_CONTINUE_COMMANDS = (
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


def _compress_page_ranges(pages: list[int]) -> str:
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


_TRAILING_PAGE_RANGE_RE = re.compile(r"\s*\(pp?\.\s*\d+\s*[-–]\s*\d+\)\s*$", re.IGNORECASE)


def _clean_section_name(name: str, start: int, end: int) -> str:
    cleaned = _TRAILING_PAGE_RANGE_RE.sub("", str(name or "").strip()).strip(" -–")
    return cleaned or f"Section {start}-{end}"


def _render_section_list(sections: list[dict[str, Any]], limit: int | None = None) -> str:
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


def _section_facts(cut_plan: dict[str, Any], limit: int | None = 12) -> tuple[list[dict[str, Any]], str]:
    raw_sections = list(cut_plan.get("sections") or [])
    facts: list[dict[str, Any]] = []
    for sec in raw_sections:
        if not isinstance(sec, dict):
            continue
        start = int(sec.get("start") or 0)
        end = int(sec.get("end") or 0)
        facts.append({
            "name": _clean_section_name(str(sec.get("name") or "Section"), start, end),
            "start": start,
            "end": end,
        })

    if not facts:
        return [], "none yet"

    return facts, _render_section_list(facts, limit=limit)


def _has_scope_anchor(text: str, status: dict[str, Any]) -> bool:
    if _contains_any(text, _SCOPE_ANCHORS):
        return True

    for section in (status.get("sections") or []):
        name = _normalise_query(str(section.get("name") or ""))
        if name and name in text:
            return True

    filename = _normalise_query(str(status.get("filename") or "").replace(".pdf", " "))
    filename_tokens = [token for token in filename.split() if len(token) >= 4]
    return any(token in text for token in filename_tokens[:8])


def _is_short_process_command(text: str) -> bool:
    return any(text == prefix or text.startswith(f"{prefix} ") for prefix in _PROCESS_COMMAND_PREFIXES)


def _status_snapshot(store: dict[str, Any]) -> dict[str, Any]:
    gs = store.get("graph_state") or {}
    cut_plan = store.get("cut_plan") or {}
    pipeline_state = store.get("ontology_pipeline") or gs.get("ontology_pipeline") or {}
    selected_pages = list(cut_plan.get("pages_to_keep") or gs.get("selected_pages") or [])
    sections, rendered_sections = _section_facts(cut_plan)
    rendered_sections_full = _render_section_list(sections, limit=None)
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
        "selected_page_ranges": _compress_page_ranges(selected_pages),
        "total_pages": int(total_pages or 0),
        "section_count": len(sections),
        "sections": sections,
        "rendered_sections": rendered_sections,
        "rendered_sections_full": rendered_sections_full,
        "next_step": gs.get("next_step"),
        "run_status": gs.get("run_status", "loaded"),
        "ontology_status": pipeline_state.get("status") if isinstance(pipeline_state, dict) else None,
        "ontology_node_count": _ontology_node_count(pipeline_state),
        "schema_issue_count": len((pipeline_state or {}).get("schema_issues") or []) if isinstance(pipeline_state, dict) else 0,
        "human_required_count": len((pipeline_state or {}).get("human_required_fields") or []) if isinstance(pipeline_state, dict) else 0,
        "graph_issue_count": len((pipeline_state or {}).get("graph_issues") or []) if isinstance(pipeline_state, dict) else 0,
        "suggested_relation_count": len((pipeline_state or {}).get("suggested_relations") or []) if isinstance(pipeline_state, dict) else 0,
        "triplet_count": len(gs.get("cleaned_triplets") or []),
        "validated_triplet_count": len(store.get("validated_triplets") or []),
        "review_index": int(store.get("review_index") or 0),
        "extraction_memory": build_extraction_memory_snapshot(store, limit_per_type=5),
    }


def _ontology_node_count(pipeline_state: dict[str, Any] | None) -> int:
    if not isinstance(pipeline_state, dict):
        return 0
    ontology = pipeline_state.get("ontology") or {}
    nodes = ontology.get("nodes") if isinstance(ontology, dict) else {}
    if not isinstance(nodes, dict):
        return 0
    return sum(len(items) for items in nodes.values() if isinstance(items, list))


def _workflow_blockers(store: dict[str, Any]) -> tuple[list[str], str]:
    status = _status_snapshot(store)
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


def _workflow_status_reply(store: dict[str, Any]) -> str:
    status = _status_snapshot(store)
    blockers, next_action = _workflow_blockers(store)
    parts = [
        f"Current phase: **{_phase_label(status['phase'])}**.",
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


def _build_live_state_message(store: dict[str, Any]) -> dict[str, str]:
    status = _status_snapshot(store)
    memory = status["extraction_memory"]
    return {
        "role": "system",
        "content": (
            "LIVE STATE SNAPSHOT — authoritative facts for this turn.\n"
            f"filename: {status['filename']}\n"
            f"phase: {_phase_label(status['phase'])}\n"
            f"run_status: {status['run_status']}\n"
            f"next_step: {status['next_step'] or 'not set'}\n"
            f"total_pages: {status['total_pages']}\n"
            f"selected_pages_count: {status['selected_pages_count']}\n"
            f"selected_page_ranges: {status['selected_page_ranges']}\n"
            f"selected_sections_count: {status['section_count']}\n"
            f"selected_sections: {status['rendered_sections']}\n"
            f"selected_sections_full: {status['rendered_sections_full']}\n"
            f"extracted_node_count: {memory['node_count']}\n"
            f"extracted_node_type_counts: {json.dumps(memory['node_type_counts'], ensure_ascii=False, sort_keys=True)}\n"
            f"extracted_node_preview_by_type: {json.dumps(memory['node_preview_by_type'], ensure_ascii=False, sort_keys=True)}\n"
            f"triplet_count: {status['triplet_count']}\n"
            f"validated_triplet_count: {status['validated_triplet_count']}\n"
            f"triplet_review_index: {status['review_index']}\n"
            "When the user asks about current state, counts, sections, selected pages, document identity, "
            "workflow step, or a compact preview of extracted nodes, answer strictly from this snapshot. "
            "For full node or triplet lists, call the inventory tools instead of guessing."
        ),
    }


def _strip_leading_widget_payload(text: str) -> str:
    """Remove accidentally copied widget-update JSON from assistant text."""
    remaining = text or ""
    decoder = json.JSONDecoder()
    while True:
        stripped = remaining.lstrip()
        if not stripped.startswith("{"):
            return stripped.strip()
        try:
            parsed, end = decoder.raw_decode(stripped)
        except json.JSONDecodeError:
            return remaining.strip()
        if not (
            isinstance(parsed, dict)
            and parsed.get("widget")
            and ("payload" in parsed or parsed.get("event") in {"update", "render"})
        ):
            return remaining.strip()
        remaining = stripped[end:]


def _summarise_tool_result_for_followup(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:
    """Keep tool-result context useful without giving the LLM large UI payloads to echo."""
    if not isinstance(result, dict):
        return {"status": "ok", "tool": tool_name}

    widget = result.get("widget")
    if not widget:
        return result

    summary: dict[str, Any] = {
        "status": result.get("status", "ok"),
        "tool": tool_name,
        "widget_rendered": widget,
        "assistant_instruction": "Do not print widget JSON. The UI has already rendered this widget.",
    }
    if result.get("message"):
        summary["message"] = result["message"]

    if widget == "sections":
        sections = [sec for sec in (result.get("sections") or []) if isinstance(sec, dict)]
        pages = [page for page in (result.get("pages_to_keep") or []) if isinstance(page, int)]
        preview_sections = []
        for sec in sections[:8]:
            start = int(sec.get("start") or 0)
            end = int(sec.get("end") or 0)
            preview_sections.append({
                "name": _clean_section_name(str(sec.get("name") or "Section"), start, end),
                "start": start,
                "end": end,
            })
        summary.update({
            "section_count": len(sections),
            "selected_page_count": len(pages),
            "total_pages": result.get("total_pages"),
            "selected_page_ranges": _compress_page_ranges(pages),
            "preview_sections": preview_sections,
            "remaining_sections_count": max(0, len(sections) - len(preview_sections)),
            "next_action": "Ask the operator to review the Section Selection widget and approve or edit it.",
        })
        product_info = result.get("product_info")
        if isinstance(product_info, dict):
            summary["product_info"] = {
                key: product_info.get(key)
                for key in ("product_name", "document_type")
                if product_info.get(key)
            }
        return summary

    if widget == "ontology_review":
        for key in (
            "node_count",
            "selected_pages_count",
            "selected_sections_count",
            "graph_issues_count",
            "human_fields_count",
            "suggested_relations_count",
        ):
            if key in result:
                summary[key] = result.get(key)
        summary["next_action"] = "Ask the operator to review the Ontology Draft widget."
        return summary

    if widget == "run_metrics":
        metrics = result.get("metrics") or {}
        totals = metrics.get("totals") or {}
        review = metrics.get("review") or {}
        summary.update({
            "duration_seconds": totals.get("duration_seconds", 0),
            "estimated_cost_usd": totals.get("estimated_cost_usd", 0),
            "llm_calls": totals.get("llm_calls", 0),
            "total_tokens": totals.get("total_tokens", 0),
            "validated_triplets": review.get("validated_triplets", 0),
            "discarded_triplets": review.get("discarded_triplets", 0),
            "next_action": "Point the operator to the KPI widget for the full extraction metrics.",
        })
        return summary

    if widget == "triplet":
        for key in ("index", "total", "current_index", "total_triplets"):
            if key in result:
                summary[key] = result.get(key)
        summary["next_action"] = "Ask the operator to review the current triplet card."
        return summary

    return summary


def _default_tool_followup_text(executed_tools: list[tuple[str, dict[str, Any]]]) -> str:
    for tool_name, result in reversed(executed_tools):
        if not isinstance(result, dict):
            continue
        if result.get("message"):
            return str(result["message"])
        if result.get("widget") == "sections":
            return "Section selection is ready. Review the widget to adjust or approve the selected sections."
        if result.get("widget") == "ontology_review":
            return "Ontology draft is ready. Review the widget before continuing."
        if result.get("widget") == "run_metrics":
            return "The extraction KPI summary is ready in the chat."
        if result.get("widget") == "triplet":
            return "The next triplet is ready for review."
        if result.get("status") == "ok":
            return f"{tool_name.replace('_', ' ').title()} completed."
    return ""


def _maybe_build_scope_guard_reply(store: dict[str, Any], user_message: str | None) -> str | None:
    text = _normalise_query(user_message or "")
    if not text or text.startswith("[system:"):
        return None

    status = _status_snapshot(store)
    if _has_scope_anchor(text, status) or _is_short_process_command(text):
        return None

    return (
        "I can only help with the loaded manual and this extraction workflow. "
        f"The active document is **{status['filename']}** and the current phase is {_phase_label(status['phase'])}. "
        "Ask me about the document, selected pages or sections, ontology or triplets, validation, export, graph editing, or current progress."
    )


_OPINION_MARKERS = (
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


def _wants_reasoning(text: str) -> bool:
    return any(marker in text for marker in _OPINION_MARKERS)


def _maybe_build_direct_status_reply(store: dict[str, Any], user_message: str | None) -> str | None:
    text = _normalise_query(user_message or "")
    if not text:
        return None

    # If the operator is asking for judgment/reasoning, let the LLM handle it
    # instead of short-circuiting to a canned count/fact.
    if _wants_reasoning(text):
        return None

    status = _status_snapshot(store)
    filename = status["filename"]
    phase = status["phase"]
    selected_pages_count = status["selected_pages_count"]
    selected_page_ranges = status["selected_page_ranges"]
    total_pages = status["total_pages"]
    section_count = status["section_count"]
    rendered_sections = status["rendered_sections"]
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
        and _contains_any(text, (
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
    asks_sections = _contains_any(text, (
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
        and _contains_any(text, ("how many", "number of", "count", "quante", "quanti"))
    )
    asks_manual = _contains_any(text, (
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
        and _contains_any(text, (
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
    asks_next_step = _contains_any(text, (
        "next step",
        "what's next",
        "whats next",
        "what happens next",
        "cosa succede dopo",
        "prossimo step",
        "prossima fase",
        "passo successivo",
    ))
    asks_blockers = _contains_any(text, (
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
        blockers, next_action = _workflow_blockers(store)
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
        blockers, next_action = _workflow_blockers(store)
        blocker_text = " ".join(blockers) if blockers else "No hard blocker."
        return f"The current phase is {_phase_label(phase)}. {blocker_text} Next step: {next_action}"

    if asks_page_count and selected_pages_count:
        return (
            f"The current workflow has {selected_pages_count} selected page(s) out of {total_pages} total."
        )

    if asks_progress:
        return _workflow_status_reply(store)

    return f"The current phase is {_phase_label(phase)}."


def _detect_inventory_request(text: str) -> tuple[str, dict[str, Any]] | None:
    normalised = _normalise_query(text)
    if not normalised:
        return None

    asks_nodes = _contains_any(normalised, (
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
        if _contains_any(normalised, ("description", "descrizione", "details", "dettagli")):
            args["include_descriptions"] = True
        return "list_extracted_nodes", args

    asks_triplets = _contains_any(normalised, (
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


def _format_triplet_inventory_message(result: dict[str, Any]) -> str:
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


async def _maybe_handle_inventory_request(
    store: dict[str, Any],
    conversation: dict[str, Any],
    user_message: str | None,
    on_event,
) -> bool:
    detected = _detect_inventory_request(user_message or "")
    if not detected:
        return False

    tool_name, args = detected
    ok, gate_reason = gate_check(tool_name, args, store)
    if not ok:
        reply = gate_reason
    else:
        on_event(evt_bus.progress_event(tool_name, f"Running {tool_name}..."))
        result = await dispatch(tool_name, args, store, on_event)
        conversation.setdefault("tool_calls", []).append({
            "tool": tool_name,
            "args": args,
            "result": result,
            "deterministic": True,
        })
        if tool_name == "list_extracted_triplets":
            reply = _format_triplet_inventory_message(result)
        else:
            reply = str(result.get("message") or "No extracted-node inventory is available yet.")

    _append_message(conversation, "assistant", reply)
    on_event(evt_bus.chat_delta_event(reply))
    on_event(evt_bus.done_event())
    return True


def _phase_greeting(store: dict) -> str:
    gs = store.get("graph_state") or {}
    phase = gs.get("current_phase", GraphPhase.LOADED.value)
    filename = store.get("filename", "the manual")
    if phase == GraphPhase.LOADED.value:
        return (
            f"Hello! I've loaded **{filename}**. "
            "I'll start scoping it now — identifying diagnostic sections and selecting relevant pages."
        )
    elif phase == GraphPhase.SCOPING.value:
        return f"Resuming scoping for **{filename}**. Let me check the current cut plan."
    elif phase == GraphPhase.ONTOLOGY_DRAFT.value:
        return "Ontology drafting is in progress. I'll update you on the current status."
    elif phase == GraphPhase.EXTRACTION.value:
        return "The ontology draft is ready for your review."
    elif phase == GraphPhase.VALIDATION.value:
        return "Triplets are ready for review. Let's go through them together."
    elif phase == GraphPhase.EXPORT.value:
        return "All triplets reviewed. Ready to export the final ontology."
    elif phase == GraphPhase.COMPLETED.value:
        return "Export complete. You can now inspect and modify the exported graph."
    return f"Resuming session for **{filename}**."


def _is_confirm_message(text: str) -> bool:
    return text in _CONFIRM_WORDS or any(text.startswith(f"{word} ") for word in _CONFIRM_WORDS)


def _is_cancel_message(text: str) -> bool:
    return text in _CANCEL_WORDS or any(text.startswith(f"{word} ") for word in _CANCEL_WORDS)


def _is_continue_command(text: str) -> bool:
    if _contains_any(text, ("what", "which", "where", "show", "tell", "cosa", "quale", "qual ", "a che", "?")):
        return False
    return text in _CONTINUE_COMMANDS or any(text.startswith(f"{cmd} ") for cmd in _CONTINUE_COMMANDS)


def _detect_rerun_action(text: str, store: dict[str, Any]) -> str | None:
    if not (_contains_any(text, _RERUN_WORDS) or "re-scope" in text or "rescope" in text or "re-extract" in text):
        return None

    if _contains_any(text, ("scope", "scoping", "cut plan", "section selection", "re-scope", "rescope", "sezioni", "scoping")):
        return "propose_cut_plan"
    if _contains_any(text, ("ontology", "ontologia", "draft", "nodes", "nodi")):
        return "draft_ontology"
    if _contains_any(text, ("extract", "extraction", "estrazione", "triplet", "triplets", "triplette", "re-extract")):
        return "run_extraction"

    phase = (store.get("graph_state") or {}).get("current_phase")
    if phase == GraphPhase.SCOPING.value:
        return "propose_cut_plan"
    if phase == GraphPhase.ONTOLOGY_DRAFT.value:
        return "draft_ontology"
    if phase in (GraphPhase.EXTRACTION.value, GraphPhase.VALIDATION.value):
        return "run_extraction"
    return None


def _action_label(action: str) -> str:
    return {
        "propose_cut_plan": "scoping",
        "draft_ontology": "ontology drafting",
        "run_extraction": "triplet extraction",
    }.get(action, action.replace("_", " "))


def _action_already_completed(action: str, store: dict[str, Any]) -> bool:
    gs = store.get("graph_state") or {}
    if action == "propose_cut_plan":
        cut_plan = store.get("cut_plan") or gs.get("cut_plan") or {}
        return bool(cut_plan.get("pages_to_keep") or cut_plan.get("sections"))
    if action == "draft_ontology":
        return bool(store.get("ontology_pipeline") or gs.get("ontology_pipeline"))
    if action == "run_extraction":
        return bool(gs.get("cleaned_triplets") or gs.get("raw_triplets"))
    return False


def _reset_downstream_for_action(action: str, store: dict[str, Any]) -> None:
    gs = store.setdefault("graph_state", {})
    if action in {"propose_cut_plan", "draft_ontology"}:
        store.pop("ontology_pipeline", None)
        gs["ontology_pipeline"] = None
        gs["ontology_draft"] = None
        gs["ontology_issues"] = []
        gs["human_required_fields"] = []
        gs["suggested_relations"] = []
        gs["schema_compliant"] = False
    if action in {"propose_cut_plan", "draft_ontology", "run_extraction"}:
        gs["raw_triplets"] = []
        gs["cleaned_triplets"] = []
        gs["extraction_chunks"] = []
        store["validated_triplets"] = []
        store["review_index"] = 0


def _next_action_for_continue(store: dict[str, Any]) -> tuple[str | None, str | None]:
    status = _status_snapshot(store)
    phase = status["phase"]

    if phase == GraphPhase.LOADED.value:
        return "propose_cut_plan", None

    if phase == GraphPhase.SCOPING.value:
        if status["selected_pages_count"]:
            return "approve_cut_plan", None
        return None, "Scoping has not produced a section selection yet. Wait for scoping to finish first."

    if phase == GraphPhase.ONTOLOGY_DRAFT.value:
        blockers, next_action = _workflow_blockers(store)
        if blockers:
            return None, " ".join(blockers) + f" Next step: {next_action}"
        return "run_extraction", None

    if phase in (GraphPhase.EXTRACTION.value, GraphPhase.VALIDATION.value):
        if status["triplet_count"]:
            return "get_next_triplet", None
        return "run_extraction", None

    if phase == GraphPhase.EXPORT.value:
        return "export_ontology", None

    if phase == GraphPhase.COMPLETED.value:
        return None, "The workflow is already complete. There is no next step to run."

    return None, f"I do not know how to continue automatically from phase '{phase}'."


async def _run_deterministic_action(
    action: str,
    store: dict[str, Any],
    conversation: dict[str, Any],
    on_event,
    *,
    reset_downstream: bool = False,
) -> None:
    if reset_downstream:
        _reset_downstream_for_action(action, store)

    chain_on_success = {
        "approve_cut_plan": "draft_ontology",
        "run_extraction": "get_next_triplet",
    }
    chain_preamble = {
        "approve_cut_plan": "Section selection confirmed. Starting ontology draft now...",
        "run_extraction": "",
    }

    async def _run_one(tool_name: str) -> dict[str, Any]:
        on_event(evt_bus.progress_event(tool_name, f"Running {tool_name}..."))
        result = await dispatch(tool_name, {}, store, on_event)
        conversation.setdefault("tool_calls", []).append({
            "tool": tool_name,
            "args": {},
            "result": result,
            "deterministic": True,
        })
        if result.get("widget") and result["widget"] not in ("triplet_review_start",):
            on_event(evt_bus.widget_event(
                result["widget"],
                {k: v for k, v in result.items() if k != "widget"},
            ))
        message = _strip_leading_widget_payload(str(result.get("message") or ""))
        if message:
            _append_message(conversation, "assistant", message)
            on_event(evt_bus.chat_delta_event(message))
        return result

    result = await _run_one(action)
    next_tool = chain_on_success.get(action)
    if next_tool and result.get("status") == "ok":
        preamble = chain_preamble.get(action, "")
        if preamble:
            _append_message(conversation, "assistant", preamble)
            on_event(evt_bus.chat_delta_event(preamble))
        await _run_one(next_tool)


async def _maybe_handle_pending_or_process_command(
    pdf_id: str,
    store: dict[str, Any],
    conversation: dict[str, Any],
    user_message: str | None,
    on_event,
) -> bool:
    text = _normalise_query(user_message or "")
    if not text or text.startswith("[system:"):
        return False

    pending = conversation.get("pending_confirmation")
    if isinstance(pending, dict):
        if _is_confirm_message(text):
            conversation.pop("pending_confirmation", None)
            action = str(pending.get("action") or "")
            if action:
                message = f"Confirmed. Re-running {_action_label(action)} now."
                _append_message(conversation, "assistant", message)
                on_event(evt_bus.chat_delta_event(message))
                await _run_deterministic_action(
                    action,
                    store,
                    conversation,
                    on_event,
                    reset_downstream=True,
                )
                on_event(evt_bus.done_event())
                return True
        if _is_cancel_message(text):
            conversation.pop("pending_confirmation", None)
            message = "Cancelled. I will keep the current workflow state unchanged."
            _append_message(conversation, "assistant", message)
            on_event(evt_bus.chat_delta_event(message))
            on_event(evt_bus.done_event())
            return True

    rerun_action = _detect_rerun_action(text, store)
    if rerun_action and _action_already_completed(rerun_action, store):
        label = _action_label(rerun_action)
        conversation["pending_confirmation"] = {
            "kind": "rerun_completed_step",
            "action": rerun_action,
        }
        message = (
            f"{label.capitalize()} has already been completed. Re-running it will replace this step's "
            "current results and clear downstream results that depend on it. Confirm if you want me to rerun it."
        )
        _append_message(conversation, "assistant", message)
        on_event(evt_bus.chat_delta_event(message))
        on_event(evt_bus.done_event())
        return True

    if _is_continue_command(text):
        action, blocked_reason = _next_action_for_continue(store)
        if not action:
            message = blocked_reason or "I cannot continue automatically from the current workflow state."
            _append_message(conversation, "assistant", message)
            on_event(evt_bus.chat_delta_event(message))
            on_event(evt_bus.done_event())
            return True
        await _run_deterministic_action(action, store, conversation, on_event)
        on_event(evt_bus.done_event())
        return True

    return False


def _build_messages(conversation: dict, store: dict[str, Any], new_user_message: str | None = None) -> list[dict]:
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        _build_live_state_message(store),
    ]
    for msg in (conversation.get("messages") or []):
        messages.append(msg)
    if new_user_message:
        messages.append({"role": "user", "content": new_user_message})
    return messages


def _append_message(conversation: dict, role: str, content: str, **extra) -> None:
    msg = {"role": role, "content": content, **extra}
    conversation.setdefault("messages", []).append(msg)


async def handle_message(
    pdf_id: str,
    store: dict[str, Any],
    user_message: str | None,
    *,
    auto_start: bool = False,
) -> None:
    """Process one user turn (or the initial auto-start turn).

    Emits events to the event bus for the SSE stream.
    """
    conversation = seed_conversation_state(store)
    cfg = get_chat_config()

    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=Timeout(float(cfg.get("timeout", 30)), connect=10.0),
    )

    on_event = evt_bus.make_on_event(pdf_id)
    gs = store.get("graph_state") or {}
    phase = gs.get("current_phase", GraphPhase.LOADED.value)

    # On auto-start or first message, prepend a greeting
    if auto_start and not conversation.get("messages"):
        greeting = _phase_greeting(store)
        _append_message(conversation, "assistant", greeting)
        on_event(evt_bus.chat_delta_event(greeting))

    if user_message:
        _append_message(conversation, "user", user_message)

        if await _maybe_handle_pending_or_process_command(
            pdf_id,
            store,
            conversation,
            user_message,
            on_event,
        ):
            return

        if await _maybe_handle_inventory_request(
            store,
            conversation,
            user_message,
            on_event,
        ):
            return

        direct_reply = _maybe_build_direct_status_reply(store, user_message)
        if direct_reply:
            _append_message(conversation, "assistant", direct_reply)
            on_event(evt_bus.chat_delta_event(direct_reply))
            on_event(evt_bus.done_event())
            return

        scope_guard_reply = _maybe_build_scope_guard_reply(store, user_message)
        if scope_guard_reply:
            _append_message(conversation, "assistant", scope_guard_reply)
            on_event(evt_bus.chat_delta_event(scope_guard_reply))
            on_event(evt_bus.done_event())
            return

        on_event(evt_bus.chat_delta_event(""))  # typing indicator start

    # Retrieve applicable tools for this phase
    available_tools = tools_for_phase(phase)

    messages = _build_messages(conversation, store, None)  # user message already appended above

    on_event({"type": evt_bus.EVT_THINKING, "message": ""})

    # LLM call (with tool-calling enabled)
    try:
        response = await client.chat.completions.create(
            model=cfg.get("model", "gpt-4o-mini"),
            messages=messages,
            tools=available_tools,
            tool_choice="auto",
            max_completion_tokens=int(cfg.get("max_output_tokens", 1500)),
            temperature=0.3,
        )
    except Exception as exc:
        logger.error("LLM orchestrator error: %s", exc)
        err_msg = "I'm having trouble connecting to the language model. Please try again in a moment."
        _append_message(conversation, "assistant", err_msg)
        on_event(evt_bus.chat_delta_event(err_msg))
        on_event(evt_bus.done_event())
        return

    choice = response.choices[0]
    finish_reason = choice.finish_reason
    assistant_msg = choice.message

    # If the model wants to call tools
    if finish_reason == "tool_calls" and assistant_msg.tool_calls:
        # Build the assistant tool-call dict for the API — do NOT append to history yet.
        # We only append once we also have the tool results, so the history always stays
        # in a valid state (assistant w/ tool_calls must be followed by tool messages).
        assistant_tool_call_dict = {
            "role": "assistant",
            "content": assistant_msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in assistant_msg.tool_calls
            ],
        }

        tool_results = []
        executed_tools: list[tuple[str, dict[str, Any]]] = []
        for tc in assistant_msg.tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            # Gate check
            ok, gate_reason = gate_check(tool_name, args, store)
            if not ok:
                tool_result = {"status": "refused", "reason": gate_reason}
                conversation.setdefault("tool_calls", []).append({
                    "tool": tool_name, "args": args, "result": tool_result, "gated": True,
                })
            else:
                # Dispatch the tool
                on_event(evt_bus.progress_event(tool_name, f"Running {tool_name}…"))
                tool_result = await dispatch(tool_name, args, store, on_event)
                conversation.setdefault("tool_calls", []).append({
                    "tool": tool_name, "args": args, "result": tool_result,
                })
                # If the result includes a widget, emit it
                if tool_result.get("widget"):
                    on_event(evt_bus.widget_event(
                        tool_result["widget"],
                        {k: v for k, v in tool_result.items() if k != "widget"},
                    ))

            executed_tools.append((tool_name, tool_result))
            tool_results.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(
                    _summarise_tool_result_for_followup(tool_name, tool_result),
                    default=str,
                ),
            })

        # Feed tool results back to the LLM for a natural-language follow-up
        messages_with_results = _build_messages(conversation, store, None) + [assistant_tool_call_dict] + tool_results

        try:
            followup = await client.chat.completions.create(
                model=cfg.get("model", "gpt-4o-mini"),
                messages=messages_with_results,
                max_completion_tokens=int(cfg.get("max_output_tokens", 1500)),
                temperature=0.3,
            )
            final_text = _strip_leading_widget_payload(followup.choices[0].message.content or "")
        except Exception as exc:
            logger.error("Follow-up LLM call failed: %s", exc)
            final_text = ""
        if not final_text:
            final_text = _default_tool_followup_text(executed_tools)

        # Now persist the complete sequence to history (tool_calls + tool msgs + reply)
        # This keeps the history valid for all future turns.
        conversation.setdefault("messages", []).append(assistant_tool_call_dict)
        for tr in tool_results:
            conversation["messages"].append(tr)
        _append_message(conversation, "assistant", final_text)

        if final_text:
            on_event(evt_bus.chat_delta_event(final_text))

    else:
        # Plain text response
        final_text = _strip_leading_widget_payload(assistant_msg.content or "")
        _append_message(conversation, "assistant", final_text)
        if final_text:
            on_event(evt_bus.chat_delta_event(final_text))

    on_event(evt_bus.done_event())

    # Auto-advance: if scoping just finished, immediately propose drafting ontology
    _auto_advance(pdf_id, store, on_event)


def _auto_advance(pdf_id: str, store: dict, on_event) -> None:
    """Check if a phase just completed and trigger the next step automatically."""
    gs = store.get("graph_state") or {}
    phase = gs.get("current_phase", "")
    # After cut-plan approval (state transitions to ONTOLOGY_DRAFT), auto-trigger draft
    # This is handled in the approve_cut_plan tool result → frontend re-triggers
    pass  # Extend in later phases as needed
