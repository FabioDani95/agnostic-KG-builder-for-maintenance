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
from typing import Any

from httpx import Timeout

from backend.app_config import get_chat_config
from backend.graph.state import GraphPhase
from backend.graph.store import seed_conversation_state
from backend.services.conversation import actions as action_service
from backend.services.conversation import events as evt_bus
from backend.services.llm_gateway import get_async_client
from backend.services.conversation.gate import check as gate_check
from backend.services.conversation.heuristics import (
    action_already_completed as _action_already_completed,
    action_label as _action_label,
    clean_section_name as _clean_section_name,
    compress_page_ranges as _compress_page_ranges,
    detect_inventory_request as _detect_inventory_request,
    detect_rerun_action as _detect_rerun_action,
    format_triplet_inventory_message as _format_triplet_inventory_message,
    is_cancel_message as _is_cancel_message,
    is_confirm_message as _is_confirm_message,
    is_continue_command as _is_continue_command,
    maybe_build_direct_status_reply as _maybe_build_direct_status_reply,
    maybe_build_scope_guard_reply as _maybe_build_scope_guard_reply,
    normalise_query as _normalise_query,
    phase_label as _phase_label,
    status_snapshot as _status_snapshot,
    workflow_blockers as _workflow_blockers,
)
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
        resolution = result.get("resolution_completion") or {}
        if resolution:
            summary["resolution_completed"] = resolution.get("completed", 0)
            summary["resolution_attempted"] = resolution.get("attempted", 0)
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

    async def _run_one(tool_name: str) -> dict[str, Any]:
        on_event(evt_bus.progress_event(tool_name, f"Running {tool_name}..."))
        result = await dispatch(tool_name, {}, store, on_event)
        conversation.setdefault("tool_calls", []).append({
            "tool": tool_name,
            "args": {},
            "result": result,
            "deterministic": True,
        })
        action_service.emit_widget_result(result, on_event)
        message = _strip_leading_widget_payload(str(result.get("message") or ""))
        if message:
            _append_message(conversation, "assistant", message)
            on_event(evt_bus.chat_delta_event(message))
        return result

    result = await _run_one(action)
    next_tool = action_service.CHAIN_ON_SUCCESS.get(action)
    if next_tool and result.get("status") == "ok":
        preamble = action_service.CHAIN_PREAMBLE.get(action, "")
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

    client = get_async_client(timeout=Timeout(float(cfg.get("timeout", 30)), connect=10.0))

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
                # If the result includes a widget, emit it (validated)
                action_service.emit_widget_result(
                    tool_result, on_event, include_triplet_review_start=True,
                )

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
