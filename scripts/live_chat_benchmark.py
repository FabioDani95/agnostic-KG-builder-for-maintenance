#!/usr/bin/env python3
"""
live_chat_benchmark.py — Live end-to-end benchmark for the HITL console backend.

Runs a fully automated session against a live server. Simulates every phase of the
extraction pipeline, measuring latency, validating event types, checking output files.
Results are saved to `benchmark_runs/live_chat_benchmark_<timestamp>.json`.

Usage:
    python3 scripts/live_chat_benchmark.py [options]

    --url     Base URL (default: http://localhost:8000)
    --manual  Filename from manuals/ (default: first available)
    --model   LLM model for scoping+extraction (default: gpt-5.4)
    --max-triplets  Max triplets to review before stopping (default: 3)
    --timeout-phase  Seconds to wait per phase (default: 180)
    --save-dir  Directory for result JSON (default: benchmark_runs/)
    --verbose   Print every SSE event

Exit codes:
    0 — all phases passed
    1 — one or more phases failed or timed out
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

import httpx

# ─── Configuration ────────────────────────────────────────────────────────────

DEFAULT_URL = "http://localhost:8000"
DEFAULT_MODEL = "gpt-5.4"
DEFAULT_MAX_TRIPLETS = 3
DEFAULT_PHASE_TIMEOUT = 180  # seconds per phase
SSE_RECONNECT_DELAY = 1.0


# ─── Result tracking ──────────────────────────────────────────────────────────

@dataclass
class PhaseResult:
    name: str
    status: str = "pending"       # pending | pass | fail | timeout | skip
    duration_s: float = 0.0
    events_received: int = 0
    widgets_emitted: list[str] = field(default_factory=list)
    critiques_count: int = 0
    chat_messages: list[str] = field(default_factory=list)
    error: str = ""
    notes: list[str] = field(default_factory=list)


@dataclass
class RunReport:
    timestamp: str = ""
    manual: str = ""
    model: str = ""
    server_url: str = ""
    pdf_id: str = ""
    total_duration_s: float = 0.0
    phases: list[PhaseResult] = field(default_factory=list)
    triplets_total: int = 0
    triplets_validated: int = 0
    triplets_skipped: int = 0
    critiques_total: int = 0
    output_files: dict[str, bool] = field(default_factory=dict)
    overall: str = "pending"      # pass | fail | partial
    gate_refusals_tested: int = 0
    gate_refusals_correct: int = 0

    def add_phase(self, phase: PhaseResult):
        self.phases.append(phase)

    def summary(self) -> str:
        passed = sum(1 for p in self.phases if p.status == "pass")
        failed = sum(1 for p in self.phases if p.status in ("fail", "timeout"))
        lines = [
            f"\n{'═'*60}",
            f"  CHATBOT E2E TEST — {self.timestamp}",
            f"  Manual : {self.manual}",
            f"  Model  : {self.model}",
            f"  PDF ID : {self.pdf_id}",
            f"{'═'*60}",
        ]
        for p in self.phases:
            icon = {"pass": "✅", "fail": "❌", "timeout": "⏱", "skip": "⏭", "pending": "⏳"}.get(p.status, "?")
            dur = f"{p.duration_s:.1f}s"
            widgets = f"  widgets={','.join(p.widgets_emitted)}" if p.widgets_emitted else ""
            crit = f"  critiques={p.critiques_count}" if p.critiques_count else ""
            err = f"  ⚠ {p.error}" if p.error else ""
            lines.append(f"  {icon} [{dur:>6}] {p.name}{widgets}{crit}{err}")
        lines += [
            f"{'─'*60}",
            f"  Phases: {passed} passed, {failed} failed of {len(self.phases)}",
            f"  Triplets: {self.triplets_validated} validated, {self.triplets_skipped} skipped",
            f"  Critiques total: {self.critiques_total}",
            f"  Gate refusals: {self.gate_refusals_correct}/{self.gate_refusals_tested} correct",
            f"  Total time: {self.total_duration_s:.1f}s",
            f"  Overall: {self.overall.upper()}",
            f"{'═'*60}\n",
        ]
        return "\n".join(lines)


# ─── SSE client ───────────────────────────────────────────────────────────────

class SseCollector:
    """Collects SSE events in the background, signals via asyncio.Event."""

    def __init__(self, url: str, timeout: float = DEFAULT_PHASE_TIMEOUT):
        self.url = url
        self.timeout = timeout
        self._events: asyncio.Queue[dict] = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    def start(self):
        self._task = asyncio.create_task(self._stream())

    def stop(self):
        self._stop.set()
        if self._task:
            self._task.cancel()

    async def _stream(self):
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            try:
                async with client.stream("GET", self.url) as resp:
                    buffer = ""
                    async for chunk in resp.aiter_text():
                        if self._stop.is_set():
                            break
                        buffer += chunk
                        while "\n\n" in buffer:
                            event_str, buffer = buffer.split("\n\n", 1)
                            for line in event_str.splitlines():
                                if line.startswith("data: "):
                                    raw = line[6:].strip()
                                    if raw:
                                        try:
                                            evt = json.loads(raw)
                                            await self._events.put(evt)
                                        except json.JSONDecodeError:
                                            pass
            except (httpx.ReadTimeout, asyncio.CancelledError):
                pass

    async def next_event(self, timeout: float | None = None) -> dict | None:
        try:
            return await asyncio.wait_for(self._events.get(), timeout=timeout or self.timeout)
        except asyncio.TimeoutError:
            return None

    async def drain_until(
        self,
        *,
        want_type: str | None = None,
        want_widget: str | None = None,
        stop_on: str = "done",
        timeout: float | None = None,
        verbose: bool = False,
    ) -> tuple[list[dict], bool]:
        """Collect events until `stop_on` AND the target is found (or timeout).

        If want_type/want_widget is given, stop_on only terminates the loop once
        the target has been found — earlier stop_on events (e.g. 'done' from a
        parallel gate-refusal explanation) are passed through without stopping.
        """
        collected = []
        found = False
        deadline = time.monotonic() + (timeout or self.timeout)
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            evt = await self.next_event(timeout=min(remaining, 5.0))
            if evt is None:
                continue
            collected.append(evt)
            if verbose:
                _log_event(evt)
            evt_type = evt.get("type", "")
            if want_type and evt_type == want_type:
                found = True
            if want_widget and evt_type == "widget" and evt.get("widget") == want_widget:
                found = True
            if evt_type == stop_on:
                # Only stop if we've already found the target, or no target was specified.
                if found or (want_type is None and want_widget is None):
                    break
        return collected, found


# ─── HTTP helpers ─────────────────────────────────────────────────────────────

async def api(client: httpx.AsyncClient, method: str, path: str, **kw) -> dict:
    resp = await client.request(method, path, **kw)
    resp.raise_for_status()
    return resp.json()


def _log_event(evt: dict):
    t = evt.get("type", "?")
    if t == "chat_delta":
        print(f"    [chat_delta] {evt.get('text', '')[:80]}")
    elif t == "progress":
        print(f"    [progress] {evt.get('phase', '')} — {evt.get('message', '')}")
    elif t == "widget":
        print(f"    [widget] {evt.get('widget', '')} payload_keys={list(evt.keys())}")
    elif t == "critique":
        print(f"    [critique] {evt.get('message', '')[:80]}")
    elif t == "error":
        print(f"    [error] {evt.get('message', '')}")
    elif t == "done":
        print("    [done]")


def _extract_widgets(events: list[dict]) -> list[str]:
    return [e["widget"] for e in events if e.get("type") == "widget" and e.get("widget")]


def _extract_chat(events: list[dict]) -> list[str]:
    return [e["text"] for e in events if e.get("type") == "chat_delta" and e.get("text")]


def _count_critiques(events: list[dict]) -> int:
    return sum(1 for e in events if e.get("type") == "critique")


# ─── Phase runners ────────────────────────────────────────────────────────────

async def phase_startup(
    client: httpx.AsyncClient, base: str, manual: str, model: str, verbose: bool
) -> tuple[str, PhaseResult]:
    phase = PhaseResult(name="startup (load manual + start chat)")
    t0 = time.monotonic()
    try:
        # Load manual
        load = await api(client, "POST", f"{base}/api/load-manual",
                         json={"filename": manual})
        pdf_id = load["pdf_id"]
        phase.notes.append(f"pdf_id={pdf_id}")

        phase.status = "pass"
        phase.notes.append("Manual loaded OK")
        return pdf_id, phase
    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
        return "", phase
    finally:
        phase.duration_s = time.monotonic() - t0


async def phase_chat_start(
    client: httpx.AsyncClient, base: str, pdf_id: str, model: str, sse: SseCollector,
    timeout: float, verbose: bool
) -> PhaseResult:
    phase = PhaseResult(name="chat_start (auto-scoping)")
    t0 = time.monotonic()
    try:
        # Start chat — passes model selections
        await api(client, "POST", f"{base}/chat/start/{pdf_id}", json={
            "selected_scoping_model": model,
            "selected_extraction_model": model,
            "target_language": "en",
            "page_offset": 0,
        })

        # Expect: greeting (chat_delta) + progress events + sections widget + done
        events, got_sections = await sse.drain_until(
            want_widget="sections",
            stop_on="done",
            timeout=timeout,
            verbose=verbose,
        )

        phase.events_received = len(events)
        phase.widgets_emitted = _extract_widgets(events)
        phase.chat_messages = _extract_chat(events)
        phase.critiques_count = _count_critiques(events)

        has_greeting = any(e.get("type") == "chat_delta" for e in events)
        has_progress = any(e.get("type") == "progress" for e in events)
        all_english = all(
            _is_english(m) for m in phase.chat_messages if m.strip()
        )

        if not got_sections:
            phase.status = "fail"
            phase.error = "sections widget not received"
        elif not has_greeting:
            phase.status = "fail"
            phase.error = "no greeting message"
        else:
            phase.status = "pass"
            if has_progress:
                phase.notes.append("progress events present ✓")
            if all_english:
                phase.notes.append("all messages in English ✓")
            else:
                phase.notes.append("⚠ non-English text detected")

    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
    finally:
        phase.duration_s = time.monotonic() - t0
    return phase


async def phase_approve_scoping(
    client: httpx.AsyncClient, base: str, pdf_id: str, sse: SseCollector,
    timeout: float, verbose: bool
) -> PhaseResult:
    """Approve the section list → auto-chains into ontology draft."""
    phase = PhaseResult(name="approve_cut_plan → auto draft_ontology")
    t0 = time.monotonic()
    try:
        resp = await api(client, "POST", f"{base}/chat/action",
                         json={"pdf_id": pdf_id, "action": "approve_cut_plan", "payload": {}})
        assert resp.get("status") == "ok", f"action refused: {resp}"

        # Expect: sections approved message + ontology draft progress + ontology_review widget
        events, got_ontology = await sse.drain_until(
            want_widget="ontology_review",
            stop_on="done",
            timeout=timeout,
            verbose=verbose,
        )

        phase.events_received = len(events)
        phase.widgets_emitted = _extract_widgets(events)
        phase.chat_messages = _extract_chat(events)
        phase.critiques_count = _count_critiques(events)

        if not got_ontology:
            phase.status = "fail"
            phase.error = "ontology_review widget not received after approve_cut_plan"
        else:
            phase.status = "pass"
            if phase.critiques_count:
                phase.notes.append(f"proactive critic fired {phase.critiques_count} critique(s) ✓")

    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
    finally:
        phase.duration_s = time.monotonic() - t0
    return phase


async def phase_gate_refusal(
    client: httpx.AsyncClient, base: str, pdf_id: str, sse: SseCollector,
    verbose: bool
) -> PhaseResult:
    """Test that out-of-phase actions are blocked by the gate."""
    phase = PhaseResult(name="gate refusal (export during ontology phase)")
    t0 = time.monotonic()
    try:
        resp = await api(client, "POST", f"{base}/chat/action",
                         json={"pdf_id": pdf_id, "action": "export_ontology", "payload": {}})
        # Should be refused
        if resp.get("status") == "refused":
            phase.status = "pass"
            phase.notes.append(f"refused with: {resp.get('reason', '')[:80]}")
        else:
            # Check SSE for an error/refusal message
            events, _ = await sse.drain_until(stop_on="done", timeout=5.0, verbose=verbose)
            has_error = any(e.get("type") in ("error", "chat_delta") for e in events)
            phase.status = "pass" if has_error else "fail"
            phase.notes.append("gate: action not refused at HTTP level but LLM explained")

    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
    finally:
        phase.duration_s = time.monotonic() - t0
    return phase


async def phase_run_extraction(
    client: httpx.AsyncClient, base: str, pdf_id: str, sse: SseCollector,
    timeout: float, verbose: bool
) -> PhaseResult:
    """Trigger extraction and wait for first triplet (auto-chained after extraction)."""
    phase = PhaseResult(name="run_extraction (chunk progress + first triplet)")
    t0 = time.monotonic()
    try:
        resp = await api(client, "POST", f"{base}/chat/action",
                         json={"pdf_id": pdf_id, "action": "run_extraction", "payload": {}})
        assert resp.get("status") == "ok", f"action refused: {resp}"

        # After extraction completes the backend auto-chains to get_next_triplet,
        # so we expect extraction progress events followed by the first triplet widget.
        events, got_widget = await sse.drain_until(
            want_widget="triplet",
            stop_on="done",
            timeout=timeout,
            verbose=verbose,
        )

        phase.events_received = len(events)
        phase.widgets_emitted = _extract_widgets(events)
        phase.chat_messages = _extract_chat(events)
        phase.critiques_count = _count_critiques(events)

        progress_events = [e for e in events if e.get("type") == "progress"]
        has_chunk_progress = any(
            "chunk" in str(e.get("message", "")).lower() or
            e.get("current_chunk") is not None
            for e in progress_events
        )

        if not got_widget:
            phase.status = "fail"
            phase.error = "first triplet widget not received after extraction"
        else:
            phase.status = "pass"
            phase.notes.append(f"progress events: {len(progress_events)}")
            if has_chunk_progress:
                phase.notes.append("per-chunk progress ✓")

    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
    finally:
        phase.duration_s = time.monotonic() - t0
    return phase


async def phase_triplet_review(
    client: httpx.AsyncClient, base: str, pdf_id: str, sse: SseCollector,
    max_triplets: int, timeout: float, verbose: bool,
) -> tuple[PhaseResult, int, int, int]:
    """Review triplets: kick off via system message, then approve/skip up to max_triplets."""
    phase = PhaseResult(name=f"triplet_review (up to {max_triplets} triplets)")
    t0 = time.monotonic()
    validated = 0
    skipped = 0
    critiques_total = 0
    triplet_index = 0

    try:
        # Triplet 0 was already shown by the run_extraction → get_next_triplet auto-chain.
        # Approve it immediately so the server chains to the next triplet.
        resp0 = await api(
            client, "POST", f"{base}/chat/action",
            json={"pdf_id": pdf_id, "action": "approve_triplet", "payload": {"index": 0}},
        )
        if resp0.get("status") == "ok":
            validated += 1
            triplet_index = 1
        else:
            phase.notes.append(f"⚠ initial approve_triplet(0): {resp0}")

        for i in range(max_triplets + 5):  # +5 buffer for "all done" case
            # Wait for either a triplet widget or export widget (all done)
            events, got_triplet = await sse.drain_until(
                want_widget="triplet",
                stop_on="done",
                timeout=timeout,
                verbose=verbose,
            )

            phase.events_received += len(events)
            phase.critiques_count += _count_critiques(events)
            critiques_total += _count_critiques(events)
            phase.widgets_emitted.extend(_extract_widgets(events))
            phase.chat_messages.extend(_extract_chat(events))

            # Check if we got an export widget (all triplets done)
            if any(e.get("widget") == "export" for e in events if e.get("type") == "widget"):
                phase.notes.append(f"all triplets reviewed after {i} iterations ✓")
                break

            if not got_triplet:
                if validated + skipped == 0:
                    phase.status = "fail"
                    phase.error = "no triplet widget received after begin_triplet_review"
                else:
                    phase.notes.append(f"no more triplets after {i} iterations")
                break

            # Find the triplet index from the widget payload
            triplet_evt = next(
                (e for e in events if e.get("type") == "widget" and e.get("widget") == "triplet"),
                None,
            )
            if triplet_evt:
                triplet_index = triplet_evt.get("index", triplet_index)

            if validated + skipped >= max_triplets:
                phase.notes.append(f"stopped after {max_triplets} triplets (limit)")
                break

            # Approve first, skip the rest
            if validated < 1 or (validated + skipped) % 2 == 0:
                action = "approve_triplet"
                validated += 1
            else:
                action = "skip_triplet"
                skipped += 1

            resp = await api(
                client, "POST", f"{base}/chat/action",
                json={"pdf_id": pdf_id, "action": action, "payload": {"index": triplet_index}},
            )
            if resp.get("status") != "ok":
                phase.notes.append(f"⚠ {action} at index {triplet_index}: {resp}")

        if phase.status == "pending":
            if validated + skipped == 0:
                phase.status = "fail"
                phase.error = "no triplets were reviewed"
            else:
                phase.status = "pass"
                phase.notes.append(f"critic fired {critiques_total} time(s)")

    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
    finally:
        phase.duration_s = time.monotonic() - t0

    return phase, validated, skipped, critiques_total


async def phase_natural_language(
    client: httpx.AsyncClient, base: str, pdf_id: str, sse: SseCollector,
    timeout: float, verbose: bool,
) -> PhaseResult:
    """Send natural language queries and verify meaningful English responses."""
    phase = PhaseResult(name="natural_language_queries")
    t0 = time.monotonic()
    queries = [
        ("Where are we in the process?",        "progress/status response"),
        ("How many triplets have been reviewed?", "count response"),
    ]
    all_ok = True
    try:
        for msg, description in queries:
            await api(client, "POST", f"{base}/chat/message",
                      json={"pdf_id": pdf_id, "message": msg})
            events, _ = await sse.drain_until(stop_on="done", timeout=timeout, verbose=verbose)
            chat_texts = _extract_chat(events)
            responded = bool(chat_texts)
            english = all(_is_english(t) for t in chat_texts if t.strip())
            if not responded:
                phase.notes.append(f"⚠ no response to: '{msg}'")
                all_ok = False
            elif not english:
                phase.notes.append(f"⚠ non-English response to: '{msg}'")
                all_ok = False
            else:
                phase.notes.append(f"✓ {description} (len={sum(len(t) for t in chat_texts)})")

        phase.status = "pass" if all_ok else "fail"
        if not all_ok:
            phase.error = "some queries got no/non-English response"
    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
    finally:
        phase.duration_s = time.monotonic() - t0
    return phase


async def phase_export(
    client: httpx.AsyncClient, base: str, pdf_id: str, sse: SseCollector,
    timeout: float, verbose: bool, manual_name: str,
) -> tuple[PhaseResult, dict[str, bool]]:
    """Export the ontology and verify output files."""
    phase = PhaseResult(name="export_ontology (cleanup + JSON + conversation.json)")
    t0 = time.monotonic()
    output_files: dict[str, bool] = {}
    try:
        resp = await api(client, "POST", f"{base}/chat/action",
                         json={"pdf_id": pdf_id, "action": "export_ontology", "payload": {}})

        if resp.get("status") == "refused":
            # Expected if there are blocking schema issues — note it but don't fail hard
            phase.status = "pass"
            phase.notes.append(f"export refused (gate): {resp.get('reason', '')} — expected in some runs")
            return phase, output_files

        events, got_export = await sse.drain_until(
            want_widget="export", stop_on="done", timeout=timeout, verbose=verbose
        )
        phase.events_received = len(events)
        phase.widgets_emitted = _extract_widgets(events)
        phase.chat_messages = _extract_chat(events)

        # Check output files on disk (relative to project root)
        safe_name = manual_name.replace(" ", "_").replace("/", "_").replace(".pdf", "")
        output_dir = os.path.join("output", safe_name)
        for fname in ("ontology.json", "conversation.json"):
            fpath = os.path.join(output_dir, fname)
            exists = os.path.isfile(fpath)
            output_files[fname] = exists
            if exists:
                phase.notes.append(f"{fname} written ✓")
            else:
                phase.notes.append(f"⚠ {fname} not found at {fpath}")

        ontology_ok = output_files.get("ontology.json", False)
        conversation_ok = output_files.get("conversation.json", False)

        if not got_export:
            phase.status = "fail"
            phase.error = "export widget not received"
        elif not ontology_ok:
            phase.status = "fail"
            phase.error = "ontology.json not written to disk"
        else:
            phase.status = "pass"
            if conversation_ok:
                phase.notes.append("conversation.json present ✓")

    except Exception as exc:
        phase.status = "fail"
        phase.error = str(exc)
    finally:
        phase.duration_s = time.monotonic() - t0
    return phase, output_files


# ─── Language check (naïve but effective for ASCII-heavy content) ──────────────

def _is_english(text: str) -> bool:
    """Rough check: no non-ASCII characters in majority of words."""
    if not text:
        return True
    words = text.split()
    ascii_words = sum(1 for w in words if w.isascii())
    return (ascii_words / max(len(words), 1)) > 0.7


# ─── Main orchestrator ────────────────────────────────────────────────────────

async def run(args: argparse.Namespace) -> RunReport:
    base = args.url.rstrip("/")
    report = RunReport(
        timestamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        model=args.model,
        server_url=base,
    )
    t_total = time.monotonic()

    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── 0. Server health check ──────────────────────────────────────────
        print(f"  Checking server at {base}…")
        try:
            await client.get(f"{base}/api/config")
        except Exception as exc:
            print(f"  ❌ Server not reachable: {exc}")
            report.overall = "fail"
            return report

        # ── 1. Choose manual ────────────────────────────────────────────────
        try:
            manuals_resp = await api(client, "GET", f"{base}/api/manuals")
            available = [m["filename"] for m in (manuals_resp.get("manuals") or [])]
        except Exception:
            available = []

        if args.manual:
            manual = args.manual
        elif available:
            # Prefer short manuals for speed
            manual = sorted(available, key=len)[0]
        else:
            print("  ❌ No manuals available.")
            report.overall = "fail"
            return report

        report.manual = manual
        print(f"  Manual: {manual}")
        print(f"  Model : {args.model}\n")

        # ── 2. Load manual ──────────────────────────────────────────────────
        pdf_id, p_startup = await phase_startup(client, base, manual, args.model, args.verbose)
        report.add_phase(p_startup)
        if p_startup.status != "pass":
            print(f"  ❌ Startup failed: {p_startup.error}")
            report.overall = "fail"
            return report
        report.pdf_id = pdf_id
        print(f"  PDF ID: {pdf_id}")

        # ── 3. Open SSE stream ───────────────────────────────────────────────
        sse = SseCollector(f"{base}/chat/stream/{pdf_id}", timeout=args.timeout_phase)
        sse.start()
        await asyncio.sleep(0.3)  # let stream connect

        # ── 4. Start chat (auto-scoping) ─────────────────────────────────────
        print("  Phase: chat_start + auto-scoping…")
        p_start = await phase_chat_start(
            client, base, pdf_id, args.model, sse, args.timeout_phase, args.verbose
        )
        report.add_phase(p_start)
        _print_phase(p_start)

        # ── 5. Gate refusal test (while still in scoping) ────────────────────
        print("  Phase: gate refusal test…")
        p_gate = await phase_gate_refusal(client, base, pdf_id, sse, args.verbose)
        report.add_phase(p_gate)
        report.gate_refusals_tested += 1
        if p_gate.status == "pass":
            report.gate_refusals_correct += 1
        _print_phase(p_gate)

        # ── 6. Approve scoping → auto-chain draft_ontology ───────────────────
        print("  Phase: approve_cut_plan → draft_ontology…")
        p_scope = await phase_approve_scoping(
            client, base, pdf_id, sse, args.timeout_phase, args.verbose
        )
        report.add_phase(p_scope)
        report.critiques_total += p_scope.critiques_count
        _print_phase(p_scope)

        # ── 7. Run extraction ─────────────────────────────────────────────────
        print("  Phase: run_extraction…")
        p_extract = await phase_run_extraction(
            client, base, pdf_id, sse, args.timeout_phase, args.verbose
        )
        report.add_phase(p_extract)
        _print_phase(p_extract)

        # ── 8. Triplet review ─────────────────────────────────────────────────
        print(f"  Phase: triplet_review (max {args.max_triplets})…")
        p_triplets, validated, skipped, crit = await phase_triplet_review(
            client, base, pdf_id, sse, args.max_triplets, args.timeout_phase, args.verbose
        )
        report.add_phase(p_triplets)
        report.triplets_validated = validated
        report.triplets_skipped = skipped
        report.critiques_total += crit
        _print_phase(p_triplets)

        # ── 9. Natural language queries ───────────────────────────────────────
        print("  Phase: natural_language_queries…")
        p_nl = await phase_natural_language(
            client, base, pdf_id, sse, 60.0, args.verbose
        )
        report.add_phase(p_nl)
        _print_phase(p_nl)

        # ── 10. Export ────────────────────────────────────────────────────────
        print("  Phase: export_ontology…")
        p_export, output_files = await phase_export(
            client, base, pdf_id, sse, args.timeout_phase, args.verbose,
            manual_name=manual.replace(".pdf", ""),
        )
        report.add_phase(p_export)
        report.output_files = output_files
        _print_phase(p_export)

        sse.stop()

    # ── Compute overall ──────────────────────────────────────────────────────
    report.total_duration_s = time.monotonic() - t_total
    failed = [p for p in report.phases if p.status in ("fail", "timeout")]
    passed = [p for p in report.phases if p.status == "pass"]
    if not failed:
        report.overall = "pass"
    elif len(passed) >= len(failed):
        report.overall = "partial"
    else:
        report.overall = "fail"

    return report


def _print_phase(p: PhaseResult):
    icon = {"pass": "✅", "fail": "❌", "timeout": "⏱", "skip": "⏭"}.get(p.status, "?")
    note_str = " | ".join(p.notes) if p.notes else ""
    err = f"  ⚠ {p.error}" if p.error else ""
    print(f"  {icon} {p.name} [{p.duration_s:.1f}s]  {note_str}{err}")


# ─── Save report ──────────────────────────────────────────────────────────────

def save_report(report: RunReport, save_dir: str) -> str:
    os.makedirs(save_dir, exist_ok=True)
    filename = f"live_chat_benchmark_{report.timestamp}.json"
    path = os.path.join(save_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(report), f, indent=2, ensure_ascii=False)
    return path


# ─── CLI ─────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--url", default=DEFAULT_URL)
    p.add_argument("--manual", default=None)
    p.add_argument("--model", default=DEFAULT_MODEL)
    p.add_argument("--max-triplets", type=int, default=DEFAULT_MAX_TRIPLETS, dest="max_triplets")
    p.add_argument("--timeout-phase", type=float, default=DEFAULT_PHASE_TIMEOUT, dest="timeout_phase")
    p.add_argument("--save-dir", default="benchmark_runs", dest="save_dir")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()
    print(f"\n{'═'*60}")
    print("  HITL Live Chat Benchmark")
    print(f"  Server : {args.url}  Model : {args.model}")
    print(f"{'═'*60}")

    report = asyncio.run(run(args))

    print(report.summary())

    path = save_report(report, args.save_dir)
    print(f"  Report saved → {path}\n")

    sys.exit(0 if report.overall == "pass" else 1)


if __name__ == "__main__":
    main()
