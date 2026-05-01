/**
 * Chat UI — SSE client, message rendering, widget dispatch.
 * All user-facing text is in English.
 */

import { renderSectionsWidget } from "./widgets/sections.js?v=20260424a";
import { renderTripletWidget } from "./widgets/triplet.js?v=20260501a";
import { renderRequiredFieldsWidget } from "./widgets/required_fields.js?v=20260422d";
import { renderNodeCard } from "./widgets/node_card.js?v=20260422d";

// ── Utilities ──────────────────────────────────────────────────────────

function _debounce(fn, ms) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), ms);
    };
}

// ── State ──────────────────────────────────────────────────────────────

let _pdfId = null;
let _eventSource = null;
let _progressBubble = null;   // collapsible progress bubble currently in stream
let _currentPhase = "loaded";
let _pdfDoc = null;
let _pdfjsLib = null;
let _currentPage = 1;
let _totalPages = 0;
let _thinkingTimer = null;
let _renderedPdfPages = new Set();
let _pdfObserver = null;
let _visiblePageObserver = null;
let _pdfSearchIndex = [];
let _pdfIndexPromise = null;
let _pdfSearchMatches = [];
let _pdfSearchCursor = -1;
let _pdfSearchQuery = "";
let _streamErrorCount = 0;
let _sessionLost = false;
let _kgGraphData = null;
let _kgGraphMode = "all";
let _pendingPdfPage = null;
let _modifyWorkspaceUrl = null;
let _modifyWorkspaceOpen = false;
let _lastQuickActionsKey = "";
let _lastWidgetType = "";
let _autoExportRequested = false;
let _lastDownloadedExportKey = "";
let _lastAutoOpenedModifyKey = "";
let _assistantTypeQueue = [];
let _assistantTyping = false;

const _ASSISTANT_WORD_DELAY_MS = 18;

// ── Initialise ─────────────────────────────────────────────────────────

export async function initChat(pdfId, pdfPath, opts = {}) {
    _pdfId = pdfId;

    const chatLayout = _ensureChatLayoutShell();
    chatLayout.hidden = false;

    _ensureGraphPanel();
    _ensureModifyPanel();
    _setupInput();
    _setupPdfControls();
    _setupGraphControls();
    _setupModifyControls();
    _setupColumnResize();
    _setupStreamDelegation();
    _setPhaseLabel("loaded");
    _setSystemBusy("Starting the extraction workflow…", "scoping");
    _setPdfStatus("Loading PDF preview…", "loading");
    _syncQuickActions({ widget: "startup" });

    // Open the chat session immediately so a slow PDF render cannot leave the UI
    // looking blank while the backend is already ready to speak.
    _openStream();

    const startPromise = fetch("/chat/start/" + pdfId, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            selected_scoping_model: opts.scopingModel || null,
            selected_extraction_model: opts.extractionModel || null,
            target_language: opts.targetLanguage || "en",
            page_offset: opts.pageOffset ?? 0,
        }),
    }).catch(() => {
        _appendErrorMessage("Could not start the chat session.");
    });

    const pdfPromise = pdfPath ? _loadPdf(pdfPath) : Promise.resolve();
    await Promise.allSettled([startPromise, pdfPromise]);
}

// ── SSE stream ─────────────────────────────────────────────────────────

function _openStream() {
    if (_sessionLost || !_pdfId) return;
    if (_eventSource) _eventSource.close();
    _eventSource = new EventSource("/chat/stream/" + _pdfId);
    _eventSource.onopen = () => {
        _streamErrorCount = 0;
    };
    _eventSource.onmessage = _handleEvent;
    _eventSource.onerror = () => {
        if (_sessionLost) return;
        _streamErrorCount += 1;
        _eventSource?.close();
        if (_streamErrorCount >= 3) {
            void _probeSession();
            return;
        }
        setTimeout(_openStream, 3000);
    };
}

function _ensureChatLayoutShell() {
    let chatLayout = document.getElementById("chat-layout");
    if (chatLayout) return chatLayout;

    chatLayout = document.createElement("div");
    chatLayout.id = "chat-layout";
    chatLayout.hidden = true;
    chatLayout.innerHTML = `
        <header id="chat-bar">
            <div class="app-bar-left">
                <span class="app-bar-logo">KG</span>
                <span class="app-bar-title" id="chat-doc-title">Document</span>
            </div>
            <div class="app-bar-center" id="chat-phase-label">Scoping</div>
            <div class="app-bar-right">
                <span class="app-bar-meta" id="chat-operator"></span>
                <button id="chat-modify-btn" class="app-bar-btn" hidden>Modify</button>
                <button id="chat-audit-btn" class="app-bar-btn" hidden>Audit</button>
            </div>
        </header>
        <div class="chat-columns">
            <section class="chat-pdf-section">
                <div class="chat-pdf-toolbar">
                    <div class="chat-pdf-toolbar-row">
                        <span id="chat-pdf-status" class="chat-pdf-status" data-tone="loading">Loading PDF preview…</span>
                        <span id="chat-page-indicator" class="chat-pdf-page-indicator">Page — / —</span>
                        <div class="chat-pdf-page-nav">
                            <button id="chat-prev-page" type="button" class="btn-secondary btn-sm">&#8592; Page</button>
                            <button id="chat-next-page" type="button" class="btn-secondary btn-sm">Page &#8594;</button>
                        </div>
                    </div>
                    <div class="chat-pdf-toolbar-row">
                        <input
                            type="search"
                            id="chat-pdf-search"
                            class="chat-pdf-search-input"
                            placeholder="Search words in the PDF…"
                            autocomplete="off"
                        />
                        <button id="chat-pdf-search-btn" type="button" class="btn-secondary btn-sm">Find</button>
                        <button id="chat-pdf-prev-match" type="button" class="btn-secondary btn-sm" aria-label="Previous PDF match">&#8593;</button>
                        <button id="chat-pdf-next-match" type="button" class="btn-secondary btn-sm" aria-label="Next PDF match">&#8595;</button>
                        <span id="chat-pdf-search-meta" class="chat-pdf-search-meta">Search is ready once the PDF text is indexed.</span>
                    </div>
                </div>
                <section id="chat-graph-panel" class="chat-graph-panel" hidden>
                    <div class="chat-graph-head">
                        <div>
                            <div class="chat-graph-title">Review Graph</div>
                            <div id="chat-graph-meta" class="chat-graph-meta">Waiting for reviewed triplets…</div>
                        </div>
                        <div class="chat-graph-actions">
                            <button id="chat-graph-all" type="button" class="btn-secondary btn-sm" data-mode="all">Review graph</button>
                            <button id="chat-graph-focus" type="button" class="btn-secondary btn-sm" data-mode="focus">Current triplet</button>
                        </div>
                    </div>
                    <div id="chat-graph-canvas" class="chat-graph-canvas"></div>
                </section>
                <div id="chat-pdf-container" class="cp-pdf-container chat-pdf-container"></div>
            </section>
            <div id="chat-column-resizer" class="chat-column-resizer" role="separator" aria-orientation="vertical" aria-label="Resize manual and chatbot columns" tabindex="0"></div>
            <section class="chat-section">
                <div id="chat-stream" class="chat-stream"></div>
                <div id="chat-turn-indicator" class="chat-turn-indicator" data-mode="working">
                    <span class="chat-turn-badge" id="chat-turn-badge">System is working</span>
                    <span class="chat-turn-text" id="chat-turn-text">Starting the extraction workflow…</span>
                </div>
                <div id="chat-quick-actions" class="chat-quick-actions"></div>
                <form id="chat-input-form" class="chat-input-form">
                    <input
                        type="text"
                        id="chat-input"
                        class="chat-input"
                        placeholder="Ask a question or give an instruction…"
                        autocomplete="off"
                    />
                    <button type="submit" class="btn-primary chat-send-btn">Send</button>
                </form>
            </section>
        </div>
    `;
    document.body.appendChild(chatLayout);
    return chatLayout;
}

function _handleEvent(e) {
    let data;
    try { data = JSON.parse(e.data); } catch { return; }

    switch (data.type) {
        case "chat_delta":
            if (data.text) {
                const text = _normaliseAssistantText(data.text);
                if (text) _appendAssistantMessage(text);
            }
            break;
        case "progress":
            _updateProgressBubble(data);
            break;
        case "widget":
            _clearThinkingIndicator();
            _finishProgress();
            _renderWidget(data.widget, data.payload);
            _setAwaitingOperator(_widgetPrompt(data.widget));
            break;
        case "critique":
            _appendCritique(data);
            break;
        case "needs_input":
            _clearThinkingIndicator();
            _appendAssistantMessage(data.message || "I need some input from you.");
            _setAwaitingOperator(data.message || "I need your input before I can continue.");
            break;
        case "error":
            _clearThinkingIndicator();
            _appendErrorMessage(data.message || "An error occurred.");
            _setAwaitingOperator("The workflow stopped because of an error. Review the last message and decide the next step.");
            break;
        case "thinking":
            _showThinkingIndicator(data.message || "Preparing a response…");
            break;
        case "done":
            _finishProgress();
            _clearThinkingIndicator();
            if (document.getElementById("chat-turn-indicator")?.dataset.mode !== "operator") {
                _setAwaitingOperator();
            }
            _syncQuickActions({ widget: _lastWidgetType || "done" });
            break;
        case "stream_closed":
            break;
    }
}

// ── Message rendering ──────────────────────────────────────────────────

function _stream() {
    return document.getElementById("chat-stream");
}

function _appendAssistantMessage(text) {
    const stream = _stream();
    if (!stream) return;
    _clearThinkingIndicator();
    _finishProgress();

    const bubble = document.createElement("div");
    bubble.className = "chat-bubble chat-bubble--assistant";

    bubble.innerHTML = "";
    stream.appendChild(bubble);
    _enqueueAssistantTyping(bubble, text);
    _scrollToBottom();
}

function _enqueueAssistantTyping(bubble, text) {
    const fullText = String(text || "");
    if (!fullText) return;

    if (window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches) {
        bubble.innerHTML = _md(fullText);
        _scrollToBottom();
        return;
    }

    _assistantTypeQueue.push({ bubble, text: fullText });
    if (!_assistantTyping) {
        void _runAssistantTypingQueue();
    }
}

async function _runAssistantTypingQueue() {
    _assistantTyping = true;
    while (_assistantTypeQueue.length) {
        const item = _assistantTypeQueue.shift();
        if (!item?.bubble?.isConnected) continue;

        let rendered = "";
        for (const token of _splitAssistantTextForTyping(item.text)) {
            rendered += token;
            item.bubble.innerHTML = _md(rendered);
            _scrollToBottom();
            await _delay(_ASSISTANT_WORD_DELAY_MS);
        }
        item.bubble.innerHTML = _md(item.text);
        _scrollToBottom();
    }
    _assistantTyping = false;
}

function _splitAssistantTextForTyping(text) {
    return String(text || "").match(/\S+\s*|\s+/g) || [];
}

function _delay(ms) {
    return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function _appendUserMessage(text) {
    const stream = _stream();
    if (!stream) return;
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble chat-bubble--user";
    bubble.textContent = text;
    stream.appendChild(bubble);
    _scrollToBottom();
}

function _appendErrorMessage(text) {
    const stream = _stream();
    if (!stream) return;
    _clearThinkingIndicator();
    _finishProgress();
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble chat-bubble--error";
    bubble.textContent = "⚠ " + text;
    stream.appendChild(bubble);
    _scrollToBottom();
}

function _appendCritique(data) {
    const stream = _stream();
    if (!stream) return;
    _clearThinkingIndicator();
    _finishProgress();
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble chat-bubble--critique";
    bubble.innerHTML = `<span class="critique-icon">💡</span> ${_md(data.message || "")}`;
    if (data.suggestion) {
        const sug = document.createElement("div");
        sug.className = "critique-suggestion";
        sug.innerHTML = `<em>Suggestion:</em> ${_md(data.suggestion)}`;
        bubble.appendChild(sug);
    }

    if (Array.isArray(data.candidates) && data.candidates.length > 0) {
        const candidateList = document.createElement("div");
        candidateList.className = "critique-candidate-list";
        data.candidates.slice(0, 4).forEach((candidate) => {
            const row = document.createElement("div");
            row.className = "critique-candidate-row";
            const confidencePct = Math.round(Number(candidate.confidence || 0) * 100);
            row.innerHTML = `
                <div class="critique-candidate-main">
                    <span class="critique-candidate-relation">${_md(candidate.relation_name || "Relation")}</span>
                    <span class="critique-candidate-path">${_md(
                        `${candidate.from_label || candidate.from_id} → ${candidate.to_label || candidate.to_id}`,
                    )}</span>
                    <span class="critique-candidate-confidence">${confidencePct}%</span>
                </div>
                ${candidate.rationale ? `<div class="critique-candidate-rationale">${_md(candidate.rationale)}</div>` : ""}
            `;
            const applyBtn = document.createElement("button");
            applyBtn.className = "btn-sm btn-secondary";
            applyBtn.textContent = "Apply candidate";
            applyBtn.addEventListener("click", () => {
                applyBtn.disabled = true;
                _postAction("apply_suggested_relation", { indices: [candidate.index] });
            });
            row.appendChild(applyBtn);
            candidateList.appendChild(row);
        });
        bubble.appendChild(candidateList);
    }

    if (data.entity_id || data.issue_type || data.suggestion) {
        const explainBtn = document.createElement("button");
        explainBtn.className = "btn-sm btn-secondary";
        explainBtn.textContent = "Ask for details";
        explainBtn.addEventListener("click", () => {
            const prompt = data.entity_id
                ? `Explain this graph issue in the ontology draft for ${data.entity_id}: ${data.message || ""}`
                : `Explain this ontology issue in more detail: ${data.message || ""}`;
            _appendUserMessage(prompt);
            _sendMessage(prompt);
        });
        bubble.appendChild(explainBtn);
    }

    if (data.suggestion && (!Array.isArray(data.candidates) || data.candidates.length === 0)) {
        const applyBtn = document.createElement("button");
        applyBtn.className = "btn-sm btn-secondary";
        applyBtn.textContent = "Apply suggestion";
        applyBtn.addEventListener("click", () => _sendMessage(`Apply suggestion: ${data.suggestion}`));
        bubble.appendChild(applyBtn);
    }
    stream.appendChild(bubble);
    _scrollToBottom();
}

// ── Progress bubble ────────────────────────────────────────────────────

function _updateProgressBubble(data) {
    const stream = _stream();
    if (!stream) return;
    _clearThinkingIndicator();
    _currentPhase = data.phase || _currentPhase;
    _setPhaseLabel(_currentPhase);
    _setSystemBusy(data.message || "Working…", _currentPhase);

    if (!_progressBubble) {
        _progressBubble = document.createElement("div");
        _progressBubble.className = "chat-bubble chat-bubble--progress";
        stream.appendChild(_progressBubble);
    }

    const phase = _humanPhaseLabel(data.phase || _currentPhase);
    const msg = data.message || "";
    const total = data.total_chunks;
    const current = data.current_chunk;

    let progressBar = "";
    if (total && current !== undefined) {
        const pct = Math.round((current / total) * 100);
        progressBar = `
            <div class="progress-bar-wrap">
                <div class="progress-bar-fill" style="width:${pct}%"></div>
            </div>
            <span class="progress-pct">${pct}%</span>
        `;
    }

    _progressBubble.innerHTML = `
        <span class="progress-phase">${phase}</span>
        <span class="progress-msg">${msg}</span>
        ${progressBar}
    `;
    _scrollToBottom();
}

function _finishProgress() {
    if (_progressBubble) {
        _progressBubble.classList.add("progress--done");
        _progressBubble = null;
    }
}

// ── Thinking indicator ─────────────────────────────────────────────────
function _showThinkingIndicator(message = "Preparing a response…") {
    if (_progressBubble || _thinkingTimer) return;
    _thinkingTimer = window.setTimeout(() => {
        _thinkingTimer = null;
        if (_progressBubble) return;
        _setSystemBusy(message, _currentPhase);
    }, 180);
}

function _clearThinkingIndicator() {
    if (_thinkingTimer) {
        window.clearTimeout(_thinkingTimer);
        _thinkingTimer = null;
    }
}

// ── Widget rendering ───────────────────────────────────────────────────

function _renderWidget(widgetType, payload) {
    const stream = _stream();
    if (!stream) return;

    let el = null;
    const onAction = (action, data) => _postAction(action, data);

    // Non-sheet widgets indicate the previous interactive panel is no longer
    // the operator's focus — dismiss it so the reopen pill doesn't linger.
    const NON_SHEET_TYPES = new Set([
        "extraction_graph", "modify_workspace_sync", "export", "run_metrics",
    ]);
    if (NON_SHEET_TYPES.has(widgetType) && _sheetCurrentEl) {
        _dismissWidgetSheet();
    }

    switch (widgetType) {
        case "extraction_graph":
            _lastWidgetType = "extraction_graph";
            _showExtractionGraph(payload?.graph || payload, { mode: "all" });
            _syncQuickActions({ widget: "extraction_graph", payload });
            return;
        case "modify_workspace_sync":
            _lastWidgetType = "modify_workspace_sync";
            _refreshModifyWorkspace(payload);
            _syncQuickActions({ widget: "modify_workspace_sync", payload });
            return;
        case "sections":
            el = renderSectionsWidget(payload, onAction);
            break;
        case "ontology_review":
            el = renderOntologyReviewWidget(payload, onAction);
            break;
        case "triplet_review_start":
            // Request the first triplet from the backend via message
            _sendMessage("[system: begin triplet review]");
            return;
        case "triplet":
            el = renderTripletWidget(payload, onAction);
            _showTripletGraphFocus(payload);
            _navigateToTripletSource(payload?.triplet);
            break;
        case "required_fields":
            el = renderRequiredFieldsWidget(payload, onAction);
            break;
        case "node_draft":
            if (payload.node_type) {
                const draftNode = {
                    name: payload.normalized_name || payload.raw_text || "",
                    description: payload.normalized_description || "",
                };
                el = renderNodeCard(draftNode, payload.node_type, {
                    isDraft: true,
                    onConfirm: (node, type) => _postAction("confirm_node_manual", { node_type: type, node }),
                });
            }
            break;
        case "export":
            el = _renderExportWidget(payload);
            break;
        case "run_metrics":
            el = _renderRunMetricsWidget(payload?.metrics || payload);
            break;
    }

    if (el) {
        _lastWidgetType = widgetType;
        try {
            stream.appendChild(el);
            _decorateWidget(el);
            _syncQuickActions({ widget: widgetType, payload });
            _scrollToBottom();
        } catch (err) {
            console.error("[chat] widget render failed", widgetType, err);
            // Best-effort recovery: ensure the sheet doesn't stay in a broken
            // half-loaded state if decoration threw mid-way.
            try { _dismissWidgetSheet(); } catch (_) { /* ignore */ }
        }
    }
}

function _decorateWidget(el) {
    if (!el || !el.classList.contains("chat-widget") || el.dataset.decorated === "true") {
        return;
    }

    el.dataset.decorated = "true";
    el.classList.add("chat-widget--interactive");
    _wrapWidgetBody(el);
    _bindWidgetScroll(el.querySelector(".chat-widget-body"));

    // Determine if this widget should open in the side sheet
    const isSheetWidget = [..._SHEET_WIDGET_TYPES].some((cls) => el.classList.contains(cls));
    if (isSheetWidget) {
        // Open sheet immediately
        _openWidgetSheet(el);

        // Add a compact "open" button to the stream placeholder card
        const header = el.querySelector(".widget-header");
        if (header) {
            const openBtn = document.createElement("button");
            openBtn.className = "btn-secondary btn-sm";
            openBtn.textContent = "Open panel";
            openBtn.setAttribute("aria-label", "Reopen widget panel");
            openBtn.addEventListener("click", () => _openWidgetSheet(el));
            header.appendChild(openBtn);
        }
    } else {
        _applyDefaultWidgetSize(el);
    }
}

function _wrapWidgetBody(el) {
    if ([...el.children].some((child) => child.classList.contains("chat-widget-body"))) return;

    const children = [...el.children];
    const header = children.find((child) => child.classList.contains("widget-header")) || null;
    const actions = [...children].reverse().find((child) => child.classList.contains("widget-actions")) || null;
    const bodyChildren = children.filter((child) => child !== header && child !== actions);

    if (!bodyChildren.length) return;

    const body = document.createElement("div");
    body.className = "chat-widget-body";
    if (actions) {
        el.insertBefore(body, actions);
    } else {
        el.appendChild(body);
    }
    bodyChildren.forEach((child) => body.appendChild(child));
}

function _applyDefaultWidgetSize(el) {
    const preset = _widgetSizePreset(el);
    if (!el.style.height && preset.height) {
        el.style.height = `${preset.height}px`;
    }
}

function _widgetSizePreset(el) {
    if (el.classList.contains("chat-widget--sections")) {
        return { width: 920, height: 620 };
    }
    if (el.classList.contains("chat-widget--triplet")) {
        return { width: 860, height: 400 };
    }
    if (el.classList.contains("chat-widget--required-fields")) {
        return { width: 820, height: 340 };
    }
    if (el.classList.contains("chat-widget--ontology-review")) {
        return { width: 820, height: 300 };
    }
    if (el.classList.contains("chat-widget--node-card")) {
        return { width: 780, height: 280 };
    }
    if (el.classList.contains("chat-widget--run-metrics")) {
        return { width: 900, height: 620 };
    }
    if (el.classList.contains("chat-widget--export-metrics")) {
        return { width: 900, height: 660 };
    }
    if (el.classList.contains("chat-widget--export")) {
        return { width: 680, height: 220 };
    }
    return { width: 820, height: 320 };
}

function _bindWidgetScroll(body) {
    if (!body || body.dataset.wheelBound === "true") return;
    body.dataset.wheelBound = "true";
    body.addEventListener("wheel", (event) => {
        if (body.scrollHeight <= body.clientHeight) return;

        const scrollingDown = event.deltaY > 0;
        const scrollingUp = event.deltaY < 0;
        const atTop = body.scrollTop <= 0;
        const atBottom = Math.ceil(body.scrollTop + body.clientHeight) >= body.scrollHeight;

        if ((scrollingDown && atBottom) || (scrollingUp && atTop)) return;

        event.preventDefault();
        event.stopPropagation();
        body.scrollTop += event.deltaY;
    }, { passive: false });
}

// ── Side-sheet overlay ─────────────────────────────────────────────────
// Interactive widgets (sections, triplet, fields, ontology, node) open in
// a full-height side panel instead of being embedded in the stream.

const _SHEET_WIDGET_TYPES = new Set([
    "chat-widget--sections",
    "chat-widget--triplet",
    "chat-widget--required-fields",
    "chat-widget--ontology-review",
    "chat-widget--node-card",
]);

let _sheetCurrentEl = null;  // widget el currently loaded in the sheet (persists when closed)
let _sheetFocusReturn = null; // element to restore focus to on close
let _sheetIsOpen = false;

// Return the body/action children currently living in the sheet back to the
// originating widget element. We move children rather than clone to preserve
// listeners and contentEditable state. Safe to call when nothing is loaded.
function _restoreSheetContentToWidget() {
    if (!_sheetCurrentEl) return;
    const sheetBody = document.getElementById("widget-sheet-body");
    const sheetFooter = document.getElementById("widget-sheet-footer");
    const widgetBody = _sheetCurrentEl.querySelector(".chat-widget-body");
    const widgetActions = _sheetCurrentEl.querySelector(".widget-actions");
    if (sheetBody && widgetBody) {
        [...sheetBody.children].forEach((child) => widgetBody.appendChild(child));
    }
    if (sheetFooter && widgetActions) {
        [...sheetFooter.children].forEach((child) => widgetActions.appendChild(child));
    }
}

function _initWidgetSheet() {
    const sheet = document.getElementById("widget-sheet");
    const backdrop = document.getElementById("widget-sheet-backdrop");
    const closeBtn = document.getElementById("widget-sheet-close");
    if (!sheet || sheet.dataset.sheetInit === "true") return;
    sheet.dataset.sheetInit = "true";

    closeBtn.addEventListener("click", () => _closeWidgetSheet());
    backdrop.addEventListener("click", () => _closeWidgetSheet());
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && _sheetIsOpen) _closeWidgetSheet();
    });

    _setupSheetResize();
    _applyStoredSheetWidth();
}

// ── Sheet resize ───────────────────────────────────────────────────────

const _SHEET_MIN_PX = 360;
const _SHEET_STORAGE_KEY = "kg_widget_sheet_width_px";

function _applyStoredSheetWidth() {
    try {
        const saved = window.localStorage?.getItem(_SHEET_STORAGE_KEY);
        const px = parseInt(saved, 10);
        if (Number.isFinite(px) && px >= _SHEET_MIN_PX) {
            document.documentElement.style.setProperty("--widget-sheet-width", `${px}px`);
        }
    } catch { /* ignore */ }
}

function _sheetMaxPx() {
    return Math.max(_SHEET_MIN_PX, Math.round(window.innerWidth * 0.85));
}

function _setSheetWidthPx(px) {
    const clamped = Math.max(_SHEET_MIN_PX, Math.min(_sheetMaxPx(), Math.round(px)));
    document.documentElement.style.setProperty("--widget-sheet-width", `${clamped}px`);
    return clamped;
}

function _setupSheetResize() {
    const sheet = document.getElementById("widget-sheet");
    const handle = document.getElementById("widget-sheet-resizer");
    if (!sheet || !handle || handle.dataset.bound === "true") return;
    handle.dataset.bound = "true";

    let dragging = false;
    let lastWidth = null;

    const beginDrag = (event) => {
        if (event.pointerType === "mouse" && event.button !== 0) return;
        dragging = true;
        event.preventDefault();
        handle.setPointerCapture?.(event.pointerId);
        sheet.classList.add("is-resizing");
        document.body.classList.add("widget-sheet-resizing");

        const onMove = (moveEvent) => {
            // Sheet is anchored to right; new width is distance from cursor
            // to viewport's right edge.
            const next = window.innerWidth - moveEvent.clientX;
            requestAnimationFrame(() => {
                lastWidth = _setSheetWidthPx(next);
            });
        };

        const stop = (stopEvent) => {
            dragging = false;
            sheet.classList.remove("is-resizing");
            document.body.classList.remove("widget-sheet-resizing");
            window.removeEventListener("pointermove", onMove);
            window.removeEventListener("pointerup", stop);
            window.removeEventListener("pointercancel", stop);
            handle.releasePointerCapture?.(stopEvent.pointerId);
            if (lastWidth) {
                try { window.localStorage?.setItem(_SHEET_STORAGE_KEY, String(lastWidth)); }
                catch { /* ignore */ }
            }
        };

        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", stop);
        window.addEventListener("pointercancel", stop);
    };

    handle.addEventListener("pointerdown", beginDrag);

    handle.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const current = parseInt(getComputedStyle(document.documentElement)
            .getPropertyValue("--widget-sheet-width"), 10) || 520;
        let next = current;
        if (event.key === "ArrowLeft")  next = current + 32; // wider
        if (event.key === "ArrowRight") next = current - 32; // narrower
        if (event.key === "Home")       next = _sheetMaxPx();
        if (event.key === "End")        next = _SHEET_MIN_PX;
        const applied = _setSheetWidthPx(next);
        try { window.localStorage?.setItem(_SHEET_STORAGE_KEY, String(applied)); }
        catch { /* ignore */ }
    });

    // Re-clamp on viewport resize so the sheet never exceeds 85vw.
    window.addEventListener("resize", () => {
        const current = parseInt(getComputedStyle(document.documentElement)
            .getPropertyValue("--widget-sheet-width"), 10);
        if (Number.isFinite(current)) _setSheetWidthPx(current);
    });
}

function _openWidgetSheet(widgetEl) {
    _initWidgetSheet();

    const sheet = document.getElementById("widget-sheet");
    const backdrop = document.getElementById("widget-sheet-backdrop");
    const sheetBody = document.getElementById("widget-sheet-body");
    const sheetFooter = document.getElementById("widget-sheet-footer");
    const sheetTitle = document.getElementById("widget-sheet-title");
    const sheetMeta = document.getElementById("widget-sheet-meta");
    const sheetIcon = document.getElementById("widget-sheet-icon");
    if (!sheet || !sheetBody) return;

    const isNewWidget = widgetEl && widgetEl !== _sheetCurrentEl;

    if (isNewWidget) {
        // Move any content currently in the sheet back to its origin widget
        // before loading a new one. Otherwise innerHTML="" below would destroy
        // DOM that still belongs to the previous widget, leaving it hollow and
        // breaking subsequent renders.
        _restoreSheetContentToWidget();

        // Load new widget content into the sheet
        const header = widgetEl.querySelector(".widget-header");
        const titleEl = header?.querySelector(".widget-title");
        const metaEl = header?.querySelector(".widget-meta");
        const iconEl = header?.querySelector(".widget-icon");
        const actionsEl = widgetEl.querySelector(".widget-actions");
        const body = widgetEl.querySelector(".chat-widget-body") || widgetEl;

        sheetTitle.textContent = titleEl?.textContent || "Widget";
        if (metaEl) {
            sheetMeta.textContent = metaEl.textContent;
            sheetMeta.hidden = false;
        } else {
            sheetMeta.hidden = true;
        }
        sheetIcon.textContent = iconEl?.textContent || "";

        sheetBody.innerHTML = "";
        [...body.children].forEach((child) => sheetBody.appendChild(child));

        sheetFooter.innerHTML = "";
        if (actionsEl) {
            [...actionsEl.children].forEach((btn) => sheetFooter.appendChild(btn));
            sheetFooter.hidden = false;
        } else {
            sheetFooter.hidden = true;
        }

        _sheetCurrentEl = widgetEl;
    }

    _sheetFocusReturn = document.activeElement;
    _sheetIsOpen = true;

    // Remove close-animation class so re-open plays slide-in
    sheet.classList.remove("is-closing");
    backdrop.classList.remove("is-closing");

    sheet.classList.add("is-open");
    sheet.hidden = false;

    // Push the chat columns left so the PDF stays fully visible
    document.body.classList.add("widget-sheet-pushing");

    _updateSheetHeaderBtn();

    requestAnimationFrame(() => {
        document.getElementById("widget-sheet-close")?.focus();
    });
}

function _closeWidgetSheet() {
    const sheet = document.getElementById("widget-sheet");
    if (!sheet || !_sheetIsOpen) return;

    _sheetIsOpen = false;
    sheet.classList.remove("is-open");
    sheet.classList.add("is-closing");

    // Stop pushing the chat columns
    document.body.classList.remove("widget-sheet-pushing");

    setTimeout(() => {
        sheet.classList.remove("is-closing");
        // Keep sheet DOM loaded but hidden — content is preserved for re-open
        sheet.hidden = true;
    }, 260);

    if (_sheetFocusReturn?.isConnected) {
        _sheetFocusReturn.focus();
    }
    _sheetFocusReturn = null;

    _updateSheetHeaderBtn();
}

// Fully discard the loaded widget — used after a final action so the
// reopen pill doesn't keep advertising a stale panel.
function _dismissWidgetSheet() {
    _restoreSheetContentToWidget();
    _closeWidgetSheet();
    _sheetCurrentEl = null;
    setTimeout(() => _updateSheetHeaderBtn(), 280);
}

// Shows/hides the floating "Reopen panel" pill in #chat-bar
function _updateSheetHeaderBtn() {
    let btn = document.getElementById("sheet-reopen-btn");

    if (!_sheetCurrentEl) {
        // No widget loaded — remove button if present
        btn?.remove();
        return;
    }

    if (!btn) {
        btn = document.createElement("button");
        btn.id = "sheet-reopen-btn";
        btn.className = "sheet-reopen-btn";
        btn.setAttribute("aria-label", "Reopen panel");
        btn.addEventListener("click", () => _openWidgetSheet(_sheetCurrentEl));

        const bar = document.getElementById("chat-bar");
        if (bar) bar.appendChild(btn);
    }

    // Update label from current widget title
    const titleEl = _sheetCurrentEl.querySelector(".widget-title");
    const iconEl = _sheetCurrentEl.querySelector(".widget-icon");
    const icon = iconEl?.textContent?.trim() || "📋";
    const label = titleEl?.textContent?.trim() || "Panel";
    btn.innerHTML = `<span class="sheet-reopen-icon">${icon}</span><span class="sheet-reopen-label">${label}</span>`;

    // Show when closed, pulse when open to indicate it's active
    if (_sheetIsOpen) {
        btn.classList.remove("is-collapsed");
        btn.classList.add("is-active");
    } else {
        btn.classList.remove("is-active");
        btn.classList.add("is-collapsed");
    }
}


// ── Stream event delegation ────────────────────────────────────────────
// Single listener on #chat-stream handles all dynamic button clicks,
// including [[panel-link]] buttons injected via _md().

function _setupStreamDelegation() {
    const stream = _stream();
    if (!stream || stream.dataset.delegated === "true") return;
    stream.dataset.delegated = "true";

    stream.addEventListener("click", (e) => {
        const link = e.target.closest("[data-sheet-link]");
        if (link && _sheetCurrentEl) {
            e.preventDefault();
            _openWidgetSheet(_sheetCurrentEl);
        }
    });

    _setupInfoTipDelegation();
}

// ── Info-tip popover ───────────────────────────────────────────────────
// Single global popover shown on hover/focus of any [.info-tip] element.
// Uses position:fixed so it escapes any overflow:hidden ancestor.

function _ensureInfoTipPopover() {
    let pop = document.getElementById("info-tip-popover");
    if (pop) return pop;
    pop = document.createElement("div");
    pop.id = "info-tip-popover";
    pop.setAttribute("role", "tooltip");
    document.body.appendChild(pop);
    return pop;
}

function _showInfoTip(target) {
    const text = target?.dataset?.tip;
    if (!text) return;
    const pop = _ensureInfoTipPopover();
    pop.textContent = text;
    pop.classList.add("is-visible");
    _positionInfoTip(target, pop);
}

function _positionInfoTip(target, pop) {
    const rect = target.getBoundingClientRect();
    const padding = 8;
    // Reset to measure natural size at top-left
    pop.style.left = "0px";
    pop.style.top = "0px";
    const popRect = pop.getBoundingClientRect();
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    // Default: above the trigger, centred horizontally
    let left = rect.left + rect.width / 2 - popRect.width / 2;
    let top = rect.top - popRect.height - padding;

    // If would overflow top, flip below
    if (top < padding) {
        top = rect.bottom + padding;
    }
    // Clamp horizontally
    if (left < padding) left = padding;
    if (left + popRect.width > vw - padding) left = vw - popRect.width - padding;
    // Clamp vertically (just in case)
    if (top + popRect.height > vh - padding) top = vh - popRect.height - padding;

    pop.style.left = `${Math.round(left)}px`;
    pop.style.top = `${Math.round(top)}px`;
}

function _hideInfoTip() {
    const pop = document.getElementById("info-tip-popover");
    if (pop) pop.classList.remove("is-visible");
}

function _setupInfoTipDelegation() {
    if (document.body.dataset.infoTipBound === "true") return;
    document.body.dataset.infoTipBound = "true";

    const onEnter = (e) => {
        const tip = e.target.closest?.(".info-tip");
        if (tip) _showInfoTip(tip);
    };
    const onLeave = (e) => {
        const tip = e.target.closest?.(".info-tip");
        if (tip) _hideInfoTip();
    };

    document.addEventListener("mouseover", onEnter, true);
    document.addEventListener("mouseout", onLeave, true);
    document.addEventListener("focusin", onEnter, true);
    document.addEventListener("focusout", onLeave, true);
    window.addEventListener("scroll", _hideInfoTip, true);
    window.addEventListener("resize", _hideInfoTip);
}

// ── Column resize ──────────────────────────────────────────────────────

function _setupColumnResize() {
    const columns = document.querySelector(".chat-columns");
    const left = document.querySelector(".chat-pdf-section");
    const right = document.querySelector(".chat-section");
    const handle = document.getElementById("chat-column-resizer");
    if (!columns || !left || !right || !handle || handle.dataset.bound === "true") return;

    handle.dataset.bound = "true";
    _applyStoredColumnWidth(columns, left);
    let activeDrag = false;

    const setLeftWidth = (nextWidth) => {
        const rect = columns.getBoundingClientRect();
        const bounds = _columnWidthBounds(rect.width);
        const width = Math.max(bounds.minLeft, Math.min(bounds.maxLeft, nextWidth));
        left.style.flex = `0 0 ${width}px`;
        left.style.width = `${width}px`;
        left.style.maxWidth = "none";
        columns.style.setProperty("--chat-left-width", `${width}px`);
        return width;
    };

    const beginDrag = (event) => {
        if (activeDrag) return;
        if (event.pointerType === "mouse" && event.button !== 0) return;
        const rect = columns.getBoundingClientRect();
        if (rect.width <= 0) return;

        event.preventDefault();
        activeDrag = true;
        handle.setPointerCapture?.(event.pointerId);
        columns.classList.add("chat-columns--resizing");
        document.body.classList.add("chat-resizing-columns");

        const onMove = (moveEvent) => {
            requestAnimationFrame(() => {
                const width = setLeftWidth(moveEvent.clientX - rect.left);
                handle.setAttribute("aria-valuenow", String(Math.round(width)));
            });
        };

        const stop = () => {
            columns.classList.remove("chat-columns--resizing");
            document.body.classList.remove("chat-resizing-columns");
            activeDrag = false;
            window.removeEventListener("pointermove", onMove);
            window.removeEventListener("pointerup", stop);
            window.removeEventListener("pointercancel", stop);
            handle.releasePointerCapture?.(event.pointerId);
            _storeColumnWidth(columns, left);
        };

        window.addEventListener("pointermove", onMove);
        window.addEventListener("pointerup", stop);
        window.addEventListener("pointercancel", stop);
    };

    handle.addEventListener("pointerdown", beginDrag);
    handle.addEventListener("mousedown", (event) => {
        if (activeDrag || event.button !== 0) return;
        const rect = columns.getBoundingClientRect();
        if (rect.width <= 0) return;

        event.preventDefault();
        activeDrag = true;
        columns.classList.add("chat-columns--resizing");
        document.body.classList.add("chat-resizing-columns");

        const onMove = (moveEvent) => {
            const width = setLeftWidth(moveEvent.clientX - rect.left);
            handle.setAttribute("aria-valuenow", String(Math.round(width)));
        };
        const stop = () => {
            columns.classList.remove("chat-columns--resizing");
            document.body.classList.remove("chat-resizing-columns");
            activeDrag = false;
            window.removeEventListener("mousemove", onMove);
            window.removeEventListener("mouseup", stop);
            _storeColumnWidth(columns, left);
        };

        window.addEventListener("mousemove", onMove);
        window.addEventListener("mouseup", stop);
    });
    handle.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        const current = left.getBoundingClientRect().width;
        const rect = columns.getBoundingClientRect();
        const bounds = _columnWidthBounds(rect.width);
        let next = current;
        if (event.key === "ArrowLeft") next = current - 32;
        if (event.key === "ArrowRight") next = current + 32;
        if (event.key === "Home") next = bounds.minLeft;
        if (event.key === "End") next = bounds.maxLeft;
        setLeftWidth(next);
        _storeColumnWidth(columns, left);
    });
}

function _columnWidthBounds(totalWidth) {
    const narrow = totalWidth < 980;
    const minLeft = narrow ? 280 : 340;
    const minRight = narrow ? 320 : 420;
    return {
        minLeft,
        maxLeft: Math.max(minLeft, totalWidth - minRight - 12),
    };
}

function _applyStoredColumnWidth(columns, left) {
    const stored = Number(window.localStorage?.getItem("kg_chat_left_column_width") || 0);
    if (!stored) return;
    const rect = columns.getBoundingClientRect();
    if (!rect.width) {
        window.requestAnimationFrame(() => _applyStoredColumnWidth(columns, left));
        return;
    }
    const bounds = _columnWidthBounds(rect.width);
    const width = Math.max(bounds.minLeft, Math.min(bounds.maxLeft, stored));
    left.style.flex = `0 0 ${width}px`;
    left.style.width = `${width}px`;
    left.style.maxWidth = "none";
    columns.style.setProperty("--chat-left-width", `${width}px`);
}

function _storeColumnWidth(columns, left) {
    const rect = columns.getBoundingClientRect();
    const width = left.getBoundingClientRect().width;
    if (!rect.width || !width) return;
    try {
        window.localStorage?.setItem("kg_chat_left_column_width", String(Math.round(width)));
    } catch {
        // Ignore private-mode/localStorage errors; resizing still works for the session.
    }
}

// ── Modify workspace ───────────────────────────────────────────────────

function _ensureModifyPanel() {
    const pdfSection = document.querySelector(".chat-pdf-section");
    if (!pdfSection) return null;

    let panel = document.getElementById("chat-modify-panel");
    if (panel) return panel;

    panel = document.createElement("section");
    panel.id = "chat-modify-panel";
    panel.className = "chat-modify-panel";
    panel.hidden = true;
    panel.innerHTML = `
        <div class="chat-modify-head">
            <div>
                <div class="chat-modify-title">Modify Workspace</div>
                <div id="chat-modify-meta" class="chat-modify-meta">Inspect and edit the exported ontology graph.</div>
            </div>
            <div class="chat-modify-actions">
                <button id="chat-modify-open-tab" type="button" class="btn-secondary btn-sm">Open In Tab</button>
                <button id="chat-modify-close" type="button" class="btn-secondary btn-sm">Back To Manual</button>
            </div>
        </div>
        <iframe id="chat-modify-frame" class="chat-modify-frame" title="Modify workspace"></iframe>
    `;
    pdfSection.appendChild(panel);
    return panel;
}

function _setupModifyControls() {
    const btn = document.getElementById("chat-modify-btn");
    const panel = _ensureModifyPanel();
    if (btn && btn.dataset.bound !== "true") {
        btn.dataset.bound = "true";
        btn.addEventListener("click", () => {
            if (_modifyWorkspaceOpen) {
                _closeModifyWorkspace();
            } else if (_modifyWorkspaceUrl) {
                _openModifyWorkspace(_modifyWorkspaceUrl);
            }
        });
    }

    if (!panel || panel.dataset.bound === "true") return;
    panel.dataset.bound = "true";

    document.getElementById("chat-modify-close")?.addEventListener("click", () => {
        _closeModifyWorkspace();
    });
    document.getElementById("chat-modify-open-tab")?.addEventListener("click", () => {
        if (!_modifyWorkspaceUrl) return;
        window.open(_modifyWorkspaceUrl, "_blank", "noopener");
    });
}

function _setModifyWorkspaceAvailability(editorUrl) {
    if (editorUrl) _modifyWorkspaceUrl = editorUrl;
    const btn = document.getElementById("chat-modify-btn");
    if (!btn) return;
    btn.hidden = !_modifyWorkspaceUrl;
    btn.textContent = _modifyWorkspaceOpen ? "Manual" : "Modify";
    _syncQuickActions({ widget: "modify_workspace" });
}

function _workspaceFrameUrl(baseUrl) {
    if (!baseUrl) return "";
    const url = new URL(baseUrl, window.location.origin);
    url.searchParams.set("embed", "1");
    url.searchParams.set("refresh", String(Date.now()));
    return url.toString();
}

function _openModifyWorkspace(editorUrl) {
    const panel = _ensureModifyPanel();
    const pdfSection = document.querySelector(".chat-pdf-section");
    const frame = document.getElementById("chat-modify-frame");
    const meta = document.getElementById("chat-modify-meta");
    if (!panel || !pdfSection || !frame) return;

    _setModifyWorkspaceAvailability(editorUrl);
    if (!_modifyWorkspaceUrl) return;

    panel.hidden = false;
    pdfSection.classList.add("chat-pdf-section--modify");
    frame.src = _workspaceFrameUrl(_modifyWorkspaceUrl);
    if (meta) meta.textContent = "Inspect and edit the exported ontology graph while continuing the chat.";
    _modifyWorkspaceOpen = true;
    _setModifyWorkspaceAvailability(_modifyWorkspaceUrl);
}

function _closeModifyWorkspace() {
    const panel = document.getElementById("chat-modify-panel");
    const pdfSection = document.querySelector(".chat-pdf-section");
    if (!panel || !pdfSection) return;
    pdfSection.classList.remove("chat-pdf-section--modify");
    panel.hidden = true;
    _modifyWorkspaceOpen = false;
    _setModifyWorkspaceAvailability(_modifyWorkspaceUrl);

    // Re-show the extraction graph panel if we have data. If we don't,
    // unhide it anyway and request a fresh payload — otherwise the
    // operator stares at the bare PDF after Back-To-Manual.
    const graphPanel = document.getElementById("chat-graph-panel");
    if (graphPanel) graphPanel.hidden = false;
    if (_kgGraphData) {
        _renderExtractionGraph();
    } else {
        const canvas = document.getElementById("chat-graph-canvas");
        if (canvas) {
            canvas.innerHTML = `<div class="chat-graph-empty">No graph yet — keep reviewing triplets.</div>`;
        }
    }
}

function _refreshModifyWorkspace(payload = {}) {
    if (payload?.editor_url) {
        _setModifyWorkspaceAvailability(payload.editor_url);
    }
    if (_modifyWorkspaceOpen && _modifyWorkspaceUrl) {
        const frame = document.getElementById("chat-modify-frame");
        if (frame) {
            frame.src = _workspaceFrameUrl(_modifyWorkspaceUrl);
        }
    }
}

// ── Extraction graph panel ─────────────────────────────────────────────

function _ensureGraphPanel() {
    if (document.getElementById("chat-graph-panel")) return document.getElementById("chat-graph-panel");

    const pdfSection = document.querySelector(".chat-pdf-section");
    const pdfContainer = document.getElementById("chat-pdf-container");
    if (!pdfSection || !pdfContainer) return null;

    const panel = document.createElement("section");
    panel.id = "chat-graph-panel";
    panel.className = "chat-graph-panel";
    panel.hidden = true;
    panel.innerHTML = `
        <div class="chat-graph-head">
            <div>
                <div class="chat-graph-title">Review Graph</div>
                <div id="chat-graph-meta" class="chat-graph-meta">Waiting for reviewed triplets…</div>
            </div>
            <div class="chat-graph-actions">
                <button id="chat-graph-all" type="button" class="btn-secondary btn-sm" data-mode="all">Review graph</button>
                <button id="chat-graph-focus" type="button" class="btn-secondary btn-sm" data-mode="focus">Current triplet</button>
            </div>
        </div>
        <div id="chat-graph-canvas" class="chat-graph-canvas"></div>
    `;
    pdfSection.insertBefore(panel, pdfContainer);
    return panel;
}

function _setupGraphControls() {
    const panel = _ensureGraphPanel();
    if (!panel || panel.dataset.bound === "true") return;
    panel.dataset.bound = "true";
    panel.querySelectorAll("[data-mode]").forEach((button) => {
        button.addEventListener("click", () => {
            const mode = button.dataset.mode || "all";
            _kgGraphMode = mode;

            // If the modify workspace is in front, hide it so the graph panel
            // is visible again. The user explicitly asked to see the graph.
            if (_modifyWorkspaceOpen) _closeModifyWorkspace();

            // Force the graph panel out of any hidden state.
            const p = document.getElementById("chat-graph-panel");
            if (p) p.hidden = false;

            if (_kgGraphData) {
                _renderExtractionGraph();
            } else {
                // No cached graph data — ask the backend to send the latest one.
                _requestExtractionGraphRefresh();
            }
        });
    });
}

// Best-effort refresh: ask the backend for the current extraction graph.
// Falls back to a chat hint if no triplet has been reviewed yet.
function _requestExtractionGraphRefresh() {
    const panel = document.getElementById("chat-graph-panel");
    const canvas = document.getElementById("chat-graph-canvas");
    if (panel) panel.hidden = false;
    if (canvas) {
        canvas.innerHTML = `<div class="chat-graph-empty">Loading graph…</div>`;
    }
    // Most lifecycle phases re-emit extraction_graph on get_next_triplet.
    // If we are mid-review this will repaint; if we are pre-extraction it
    // will at least keep the panel open with the empty hint.
    _postAction("get_next_triplet", {}).catch(() => {
        if (canvas) {
            canvas.innerHTML = `<div class="chat-graph-empty">Graph will appear once triplets are available.</div>`;
        }
    });
}

function _showExtractionGraph(graph, { mode = "all" } = {}) {
    if (!graph || !Array.isArray(graph.nodes)) return;
    _kgGraphData = graph;
    _kgGraphMode = mode;
    _renderExtractionGraph();
}

function _showTripletGraphFocus(payload) {
    if (payload?.graph) {
        _showExtractionGraph(payload.graph, { mode: payload.graph.focus_node_ids?.length ? "focus" : "all" });
    }
}

function _renderExtractionGraph() {
    const panel = _ensureGraphPanel();
    const canvas = document.getElementById("chat-graph-canvas");
    const meta = document.getElementById("chat-graph-meta");
    if (!panel || !canvas || !_kgGraphData) return;

    panel.hidden = false;
    const allNodes = Array.isArray(_kgGraphData.nodes) ? _kgGraphData.nodes : [];
    const allEdges = Array.isArray(_kgGraphData.edges) ? _kgGraphData.edges : [];
    const focusNodeIds = new Set(_kgGraphData.focus_node_ids || []);
    const focusEdgeIds = new Set(_kgGraphData.focus_edge_ids || []);
    const hasFocus = focusNodeIds.size > 0;
    const renderMode = _kgGraphMode === "focus" && hasFocus ? "focus" : "all";
    _kgGraphMode = renderMode;

    const visibleNodes = renderMode === "focus"
        ? allNodes.filter((node) => focusNodeIds.has(node.id))
        : allNodes;
    const visibleIds = new Set(visibleNodes.map((node) => node.id));
    const visibleEdges = allEdges.filter((edge) => {
        if (!visibleIds.has(edge.from) || !visibleIds.has(edge.to)) return false;
        return renderMode !== "focus" || focusEdgeIds.has(edge.id) || (focusNodeIds.has(edge.from) && focusNodeIds.has(edge.to));
    });

    if (meta) {
        const focusLabel = renderMode === "focus" && _kgGraphData.focus_index != null
            ? ` · focusing triplet ${Number(_kgGraphData.focus_index) + 1}`
            : "";
        if (_kgGraphData.review_graph) {
            const approved = Number(_kgGraphData.approved_triplet_count || 0);
            const total = Number(_kgGraphData.total_triplets || _kgGraphData.triplet_count || 0);
            const preview = _kgGraphData.current_is_preview && _kgGraphData.current_triplet_index != null
                ? ` · previewing triplet ${Number(_kgGraphData.current_triplet_index) + 1}`
                : "";
            meta.textContent = `${approved}/${total} approved · ${allNodes.length} node(s), ${allEdges.length} relation(s)${preview}${focusLabel}`;
        } else {
            meta.textContent = `${allNodes.length} node(s), ${allEdges.length} relation(s)${focusLabel}`;
        }
    }
    _syncGraphModeButtons(hasFocus);

    if (!visibleNodes.length) {
        canvas.innerHTML = `<div class="chat-graph-empty">No graph nodes available yet.</div>`;
        return;
    }

    canvas.innerHTML = _buildGraphSvg(visibleNodes, visibleEdges, focusNodeIds, focusEdgeIds, renderMode, _kgGraphData);
}

function _syncGraphModeButtons(hasFocus) {
    const allBtn = document.getElementById("chat-graph-all");
    const focusBtn = document.getElementById("chat-graph-focus");
    if (allBtn) allBtn.classList.toggle("is-active", _kgGraphMode === "all");
    if (focusBtn) {
        focusBtn.classList.toggle("is-active", _kgGraphMode === "focus");
        focusBtn.disabled = !hasFocus;
    }
}

function _buildGraphSvg(nodes, edges, focusNodeIds, focusEdgeIds, mode, graphData = {}) {
    const groupOrder = ["Symptom", "FailureMode", "CorrectiveAction"];
    const groups = new Map();
    nodes.forEach((node) => {
        const group = node.group || "Node";
        if (!groups.has(group)) groups.set(group, []);
        groups.get(group).push(node);
    });
    const orderedGroups = [
        ...groupOrder.filter((group) => groups.has(group)),
        ...[...groups.keys()].filter((group) => !groupOrder.includes(group)).sort(),
    ];
    const width = Math.max(620, orderedGroups.length * 250);
    const maxGroupSize = Math.max(1, ...orderedGroups.map((group) => groups.get(group).length));
    const height = Math.max(230, maxGroupSize * 96 + 76);
    const xStep = orderedGroups.length > 1 ? (width - 180) / (orderedGroups.length - 1) : 1;
    const positions = new Map();

    orderedGroups.forEach((group, groupIndex) => {
        const items = groups.get(group);
        const x = orderedGroups.length === 1 ? width / 2 : 90 + groupIndex * xStep;
        const groupHeight = (items.length - 1) * 96;
        const startY = Math.max(72, (height - groupHeight) / 2);
        items.forEach((node, index) => {
            positions.set(node.id, { x, y: startY + index * 96 });
        });
    });

    const edgeHtml = edges.map((edge) => {
        const from = positions.get(edge.from);
        const to = positions.get(edge.to);
        if (!from || !to) return "";
        const focusClass = focusEdgeIds.has(edge.id) ? " is-focus" : "";
        const dx = Math.max(60, Math.abs(to.x - from.x) * 0.45);
        const path = `M ${from.x + 19} ${from.y} C ${from.x + dx} ${from.y}, ${to.x - dx} ${to.y}, ${to.x - 19} ${to.y}`;
        const midX = (from.x + to.x) / 2;
        const midY = (from.y + to.y) / 2 - 10;
        return `
            <path class="kg-edge${focusClass}" d="${path}" marker-end="url(#kg-arrow)"></path>
            <text class="kg-edge-label${focusClass}" x="${midX}" y="${midY}">${_escapeHtml(edge.label || "")}</text>
        `;
    }).join("");

    const nodeHtml = nodes.map((node) => {
        const pos = positions.get(node.id);
        if (!pos) return "";
        const isFocus = focusNodeIds.has(node.id);
        const focusClass = isFocus ? " is-focus" : (mode === "focus" ? "" : "");
        const previewClass = graphData.current_is_preview && isFocus ? " is-preview" : "";
        const label = _truncateGraphLabel(node.label || node.id, 30);
        const type = node.group || "Node";
        return `
            <g class="kg-node kg-node--${_classToken(type)}${focusClass}${previewClass}" transform="translate(${pos.x}, ${pos.y})">
                <circle r="18"></circle>
                <text class="kg-node-type" x="0" y="-27">${_escapeHtml(type)}</text>
                <text class="kg-node-label" x="0" y="36">${_escapeHtml(label)}</text>
            </g>
        `;
    }).join("");

    return `
        <svg class="chat-graph-svg chat-graph-svg--review" viewBox="0 0 ${width} ${height}" role="img" aria-label="Review knowledge graph">
            <defs>
                <marker id="kg-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
                    <path d="M 0 0 L 8 4 L 0 8 z" class="kg-arrow"></path>
                </marker>
            </defs>
            <rect class="kg-bg" x="0" y="0" width="${width}" height="${height}" rx="18"></rect>
            ${edgeHtml}
            ${nodeHtml}
        </svg>
    `;
}

function _classToken(value) {
    return String(value || "node").toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

function _truncateGraphLabel(value, maxLength) {
    const text = String(value || "");
    return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
}

function _navigateToTripletSource(triplet) {
    const page = _tripletSourcePage(triplet);
    if (page > 0) _scrollPdfToPage(page);
}

function _tripletSourcePage(triplet) {
    const actions = Array.isArray(triplet?.corrective_actions) ? triplet.corrective_actions : [];
    const firstActionPage = actions
        .map((action) => Number(action?.source_page || 0))
        .find((page) => page > 0);
    if (firstActionPage) return firstActionPage;

    const failureModes = Array.isArray(triplet?.failure_modes) ? triplet.failure_modes : [];
    const firstFailurePage = failureModes
        .map((failureMode) => Number(failureMode?.evidence_page || 0))
        .find((page) => page > 0);
    if (firstFailurePage) return firstFailurePage;

    return Number(triplet?.symptom?.evidence_page || 0);
}

function renderOntologyReviewWidget(payload, onAction) {
    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--ontology-review";

    const confidenceCounts = payload.confidence_counts || {};
    const previewRelations = payload.preview_relations || [];
    const topGraphIssues = payload.top_graph_issues || [];
    const nodeTypeCounts = payload.node_type_counts || {};
    const requiredFields = payload.human_required_fields || [];
    const resolutionCompletion = payload.resolution_completion || {};
    const resolutionAttempted = Number(resolutionCompletion.attempted || 0);
    const resolutionCompleted = Number(resolutionCompletion.completed || 0);
    const hardBlockerCount = requiredFields.length;

    const header = document.createElement("div");
    header.className = "widget-header";
    header.innerHTML = `
        <span class="widget-icon">🧠</span>
        <span class="widget-title">Ontology Draft Ready</span>
        <span class="widget-meta">
            ${payload.node_count || 0} nodes
            ${payload.schema_issues_count ? ` · ${payload.schema_issues_count} issue(s)` : ""}
            ${payload.human_fields_count ? ` · ${payload.human_fields_count} field(s) required` : ""}
        </span>
    `;
    wrap.appendChild(header);

    const KPI_INFO = {
        scoped_pages: "Number of PDF pages selected during scoping that feed the extraction.",
        sections: "Sections inside the scoped pages that contain diagnostic content.",
        graph_issues: "Schema-level issues detected in the draft ontology (missing relations, broken chains). Reported but not blocking — you can fix them later during triplet review.",
        suggestions: "Relations the system proposes between existing nodes. High-confidence ones are applied automatically; lower-confidence ones surface during triplet review.",
        resolution_completion: "Missing corrective actions the system tried to recover with targeted page retrieval.",
        auto_approve: "Nodes with high enough confidence to be approved automatically without operator review.",
        human_review: "Nodes that need an operator to confirm or edit them during triplet review.",
    };

    const _statCard = (label, value, infoKey) => `
        <div class="ontology-stat-card">
            <span class="ontology-stat-label">
                ${label}
                <span class="info-tip" tabindex="0" role="button" aria-label="${_escapeHtml(KPI_INFO[infoKey])}" data-tip="${_escapeHtml(KPI_INFO[infoKey])}">i</span>
            </span>
            <span class="ontology-stat-value">${value}</span>
        </div>
    `;

    const summary = document.createElement("div");
    summary.className = "ontology-review-summary";
    summary.innerHTML = `
        ${_statCard("Scoped Pages", payload.selected_pages_count || 0, "scoped_pages")}
        ${_statCard("Sections", payload.selected_sections_count || 0, "sections")}
        ${_statCard("Graph Issues", payload.graph_issues_count || 0, "graph_issues")}
        ${_statCard("Suggestions", payload.suggested_relations_count || 0, "suggestions")}
        ${_statCard("Resolved Gaps", `${resolutionCompleted}/${resolutionAttempted}`, "resolution_completion")}
        ${_statCard("Auto-Approve", confidenceCounts.auto_approve || 0, "auto_approve")}
        ${_statCard("Human Review", confidenceCounts.human_review || 0, "human_review")}
    `;
    wrap.appendChild(summary);

    const typeEntries = Object.entries(nodeTypeCounts);
    if (typeEntries.length > 0) {
        const typeStrip = document.createElement("div");
        typeStrip.className = "ontology-review-type-strip";
        typeEntries.forEach(([nodeType, count]) => {
            const pill = document.createElement("span");
            pill.className = "ontology-review-type-pill";
            pill.textContent = `${nodeType}: ${count}`;
            typeStrip.appendChild(pill);
        });
        wrap.appendChild(typeStrip);
    }

    if (requiredFields.length > 0) {
        const hint = document.createElement("p");
        hint.className = "widget-hint";
        hint.textContent = "Fill the required fields below before continuing to extraction. Suggested links are optional.";
        wrap.appendChild(hint);
        _appendRequiredFieldsForm(wrap, requiredFields, onAction);
    } else if (payload.schema_issues_count > 0) {
        const hint = document.createElement("p");
        hint.className = "widget-hint";
        hint.textContent = "Schema issues are still reported on the draft, but they do not block triplet extraction.";
        wrap.appendChild(hint);
    } else {
        const hint = document.createElement("p");
        hint.className = "widget-hint";
        hint.textContent = "Review the draft summary and optional suggested links. Extraction can start now.";
        wrap.appendChild(hint);
    }

    if (resolutionAttempted > 0) {
        const completionBlock = document.createElement("details");
        completionBlock.className = "ontology-review-issues-collapse";
        const attempts = Array.isArray(resolutionCompletion.attempts) ? resolutionCompletion.attempts : [];
        completionBlock.innerHTML = `
            <summary>
                <span>${resolutionCompleted}/${resolutionAttempted} resolution gap${resolutionAttempted === 1 ? "" : "s"} completed automatically</span>
                <span class="ontology-review-collapse-meta">Show details</span>
            </summary>
            <div class="ontology-review-issues">
                <p class="ontology-review-issues-hint">
                    The system searched targeted pages for missing corrective actions before scoring the draft.
                </p>
                ${attempts.map((attempt) => {
                    const pages = Array.isArray(attempt.pages) && attempt.pages.length
                        ? ` · pp. ${attempt.pages.join(", ")}`
                        : "";
                    return `
                        <div class="ontology-review-issue-row">
                            <span class="ontology-review-issue-type">${_escapeHtml(attempt.status || "unknown")}</span>
                            <span class="ontology-review-issue-text">${_md(`${attempt.target_id || "target"}${pages}`)}</span>
                        </div>
                    `;
                }).join("")}
            </div>
        `;
        wrap.appendChild(completionBlock);
    }

    // Suggested links: split by confidence threshold.
    // ≥70% → presented as "auto-applied" (no operator action needed here).
    // <70% → surface only count; the operator will see them during triplet review.
    const AUTO_THRESHOLD = 0.70;
    const autoLinks = previewRelations.filter((r) => Number(r.confidence || 0) >= AUTO_THRESHOLD);
    const reviewLinks = previewRelations.filter((r) => Number(r.confidence || 0) < AUTO_THRESHOLD);

    if (autoLinks.length > 0 || reviewLinks.length > 0) {
        const relationBlock = document.createElement("div");
        relationBlock.className = "ontology-review-relations";

        let html = `<div class="ontology-review-subtitle">Suggested links</div>`;

        if (autoLinks.length > 0) {
            html += `
                <div class="ontology-review-auto-summary" role="status">
                    <span class="ontology-auto-icon" aria-hidden="true">✓</span>
                    <span>
                        <strong>${autoLinks.length}</strong> high-confidence
                        ${autoLinks.length === 1 ? "link will be applied" : "links will be applied"} automatically
                        (≥${Math.round(AUTO_THRESHOLD * 100)}% confidence).
                    </span>
                </div>
                <details class="ontology-auto-details">
                    <summary>Show auto-applied links</summary>
                    ${autoLinks.map((relation) => `
                        <div class="ontology-review-relation-row ontology-review-relation-row--auto">
                            <span class="ontology-review-relation-name">${_escapeHtml(relation.relation_name)}</span>
                            <span class="ontology-review-relation-path">${_md(`${relation.from_label} → ${relation.to_label}`)}</span>
                            <span class="ontology-review-relation-confidence">${Math.round(Number(relation.confidence || 0) * 100)}%</span>
                        </div>
                    `).join("")}
                </details>
            `;
        }

        if (reviewLinks.length > 0) {
            html += `
                <div class="ontology-review-defer-note">
                    <strong>${reviewLinks.length}</strong> lower-confidence
                    ${reviewLinks.length === 1 ? "link" : "links"} will be presented during triplet review.
                </div>
            `;
        }

        relationBlock.innerHTML = html;
        wrap.appendChild(relationBlock);
    }

    // Top graph issues — operator can't act here; they'll surface during
    // triplet review. Keep them collapsed for transparency only.
    if (topGraphIssues.length > 0) {
        const issuesBlock = document.createElement("details");
        issuesBlock.className = "ontology-review-issues-collapse";
        issuesBlock.innerHTML = `
            <summary>
                <span>${payload.graph_issues_count} graph issue${payload.graph_issues_count === 1 ? "" : "s"} detected — review later</span>
                <span class="ontology-review-collapse-meta">Show details</span>
            </summary>
            <div class="ontology-review-issues">
                <p class="ontology-review-issues-hint">
                    These issues don't block extraction. You can fix them during triplet review.
                </p>
                ${topGraphIssues.map((issue) => `
                    <div class="ontology-review-issue-row">
                        <span class="ontology-review-issue-type">${issue.issue_type}</span>
                        <span class="ontology-review-issue-text">${_md(issue.description || "")}</span>
                    </div>
                `).join("")}
            </div>
        `;
        wrap.appendChild(issuesBlock);
    }

    const actions = document.createElement("div");
    actions.className = "widget-actions";
    const continueBtn = document.createElement("button");
    continueBtn.className = "btn-primary btn-sm";
    continueBtn.textContent = hardBlockerCount > 0 ? "Complete Required Items" : "Continue to Extraction";
    continueBtn.disabled = hardBlockerCount > 0;
    if (hardBlockerCount > 0) {
        continueBtn.title = `${requiredFields.length} required field(s) still need values.`;
    }
    continueBtn.addEventListener("click", () => {
        continueBtn.disabled = true;
        _dismissWidgetSheet();
        onAction("run_extraction", {});
    });
    actions.appendChild(continueBtn);
    wrap.appendChild(actions);
    return wrap;
}

function _appendRequiredFieldsForm(wrap, humanRequiredFields, onAction) {
    const form = document.createElement("div");
    form.className = "widget-fields-form ontology-required-fields";

    humanRequiredFields.slice(0, 6).forEach((field) => {
        const row = document.createElement("div");
        row.className = "field-row";

        const label = document.createElement("label");
        label.textContent = field.prompt || field.property_name || field.field_key;
        label.className = "field-label";

        let input;
        if (Array.isArray(field.allowed_values) && field.allowed_values.length) {
            input = document.createElement("select");
            field.allowed_values.forEach((value) => {
                const option = document.createElement("option");
                option.value = value;
                option.textContent = value;
                input.appendChild(option);
            });
        } else {
            input = document.createElement("input");
            input.type = "text";
            input.placeholder = field.suggested_value || `Enter ${field.property_name || "value"}...`;
            input.value = field.suggested_value || "";
        }
        input.className = "field-input";
        input.dataset.fieldKey = field.field_key;

        const submitBtn = document.createElement("button");
        submitBtn.className = "btn-sm btn-secondary";
        submitBtn.type = "button";
        submitBtn.textContent = "Set";
        submitBtn.addEventListener("click", () => {
            const value = input.value.trim();
            if (!value) return;
            submitBtn.disabled = true;
            submitBtn.textContent = "Saving...";
            onAction("fill_required_field", { field_key: field.field_key, value });
        });

        row.appendChild(label);
        row.appendChild(input);
        row.appendChild(submitBtn);
        form.appendChild(row);
    });

    if (humanRequiredFields.length > 6) {
        const more = document.createElement("p");
        more.className = "widget-empty";
        more.textContent = `... and ${humanRequiredFields.length - 6} more field(s). Fill these first and I will show the rest.`;
        form.appendChild(more);
    }

    wrap.appendChild(form);
}

function _formatMetricsDuration(seconds) {
    const safe = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(safe / 60);
    const remainder = Math.round(safe % 60);
    if (minutes === 0) return `${remainder}s`;
    return `${minutes}m ${String(remainder).padStart(2, "0")}s`;
}

function _formatMetricsNumber(value) {
    return new Intl.NumberFormat("en-US").format(Number(value) || 0);
}

function _formatMetricsUsd(value) {
    const amount = Number(value) || 0;
    return `$${amount.toFixed(amount >= 1 ? 2 : 4)}`;
}

function _buildNodeCountTable(nodesByType) {
    if (!nodesByType || Object.keys(nodesByType).length === 0) return "";
    const rows = Object.entries(nodesByType)
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => `
            <div class="kpi-stage-row">
                <div class="kpi-stage-name">${_escapeHtml(type)}</div>
                <div>${_escapeHtml(String(count))}</div>
            </div>
        `).join("");
    return `
        <div class="kpi-section">
            <div class="kpi-section-title">Node Count by Type</div>
            <div class="kpi-stage-list">${rows}</div>
        </div>
    `;
}

function _runMetricsMarkup(metrics) {
    if (!metrics) return "";

    const totals = metrics.totals || {};
    const doc = metrics.document || {};
    const review = metrics.review || {};
    const derived = metrics.derived_kpis || {};
    const stages = metrics.stages || {};
    const pricingBasis = metrics.pricing_basis || {};
    const resolutionCompletion = metrics.resolution_completion || {};
    const totalByModel = totals.by_model || {};
    const saved = Number(review.validated_triplets || 0);
    const discarded = Number(review.discarded_triplets || 0);
    const extractedTriplets = Number(review.extracted_triplets || stages.extraction?.details?.triplet_count || 0);

    const stageRows = ["scoping", "ontology", "extraction", "export"]
        .filter((name) => stages[name])
        .map((name) => {
            const stage = stages[name];
            const details = stage.details || {};
            const bits = [`${_formatMetricsDuration(stage.duration_seconds)}`];
            if (stage.llm_calls) bits.push(`${_formatMetricsNumber(stage.llm_calls)} call(s)`);
            if (stage.total_tokens) bits.push(`${_formatMetricsNumber(stage.total_tokens)} tok`);
            if (stage.estimated_cost_usd) bits.push(_formatMetricsUsd(stage.estimated_cost_usd));
            if (details.chunk_count) bits.push(`${_formatMetricsNumber(details.chunk_count)} chunk(s)`);
            if (details.retry_count != null && details.retry_count > 0) bits.push(`${_formatMetricsNumber(details.retry_count)} retry`);
            return `
                <div class="kpi-stage-row">
                    <div class="kpi-stage-name">${_escapeHtml(name)}</div>
                    <div>${_escapeHtml(bits.join(" · "))}</div>
                </div>
            `;
        }).join("");

    const modelRows = Object.entries(totalByModel)
        .sort((a, b) => (b[1].estimated_cost_usd || 0) - (a[1].estimated_cost_usd || 0))
        .map(([modelKey, modelData]) => `
            <div class="kpi-stage-row">
                <div class="kpi-stage-name">${_escapeHtml(modelData.label || modelKey)}</div>
                <div>${_escapeHtml(`${_formatMetricsUsd(modelData.estimated_cost_usd)} · ${_formatMetricsNumber(modelData.total_tokens)} tok · ${_formatMetricsNumber(modelData.llm_calls)} call(s)`)}</div>
            </div>
        `)
        .join("");

    return `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Automation Time</div>
                <div class="kpi-value">${_escapeHtml(_formatMetricsDuration(totals.duration_seconds))}</div>
                <div class="kpi-note">${_escapeHtml(_formatMetricsNumber(doc.selected_pages || 0))} selected pages out of ${_escapeHtml(_formatMetricsNumber(doc.total_pages || 0))}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Estimated Cost</div>
                <div class="kpi-value">${_escapeHtml(_formatMetricsUsd(totals.estimated_cost_usd))}</div>
                <div class="kpi-note">${_escapeHtml(pricingBasis.label || "Estimated from model pricing")}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">LLM Tokens</div>
                <div class="kpi-value">${_escapeHtml(_formatMetricsNumber(totals.total_tokens))}</div>
                <div class="kpi-note">${_escapeHtml(_formatMetricsNumber(totals.prompt_tokens))} input · ${_escapeHtml(_formatMetricsNumber(totals.completion_tokens))} output</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Review Yield</div>
                <div class="kpi-value">${_escapeHtml(_formatMetricsNumber(saved))} kept / ${_escapeHtml(_formatMetricsNumber(discarded))} dropped</div>
                <div class="kpi-note">${_escapeHtml(_formatMetricsNumber(extractedTriplets))} extracted triplet(s)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cost Per Selected Page</div>
                <div class="kpi-value">${_escapeHtml(_formatMetricsUsd(derived.cost_per_selected_page_usd))}</div>
                <div class="kpi-note">${_escapeHtml((Number(derived.pages_kept_ratio || 0) * 100).toFixed(1))}% of document kept after scoping</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cost Per Extracted Triplet</div>
                <div class="kpi-value">${_escapeHtml(_formatMetricsUsd(derived.cost_per_extracted_triplet_usd))}</div>
                <div class="kpi-note">${_escapeHtml(_formatMetricsDuration(derived.seconds_per_selected_page || 0))} per selected page</div>
            </div>
        </div>
        <div class="kpi-section">
            <div class="kpi-section-title">Stage Breakdown</div>
            <div class="kpi-stage-list">${stageRows}</div>
        </div>
        ${modelRows ? `
        <div class="kpi-section">
            <div class="kpi-section-title">Model Cost Breakdown</div>
            <div class="kpi-stage-list">${modelRows}</div>
        </div>
        ` : ""}
        ${_buildNodeCountTable(metrics.nodes_by_type)}
        ${_buildResolutionCompletionSection(resolutionCompletion)}
        ${_buildGraphCoverageSection(metrics.graph_coverage)}
    `;
}

function _buildResolutionCompletionSection(report) {
    const attempted = Number(report?.attempted || 0);
    const completed = Number(report?.completed || 0);
    const targetCount = Number(report?.target_count || 0);
    if (!attempted && !completed && !targetCount) return "";
    const reports = Array.isArray(report?.reports) ? report.reports : [];
    const attempts = Array.isArray(report?.attempts)
        ? report.attempts
        : reports.flatMap((item) => Array.isArray(item?.attempts) ? item.attempts : []);
    const rows = attempts.slice(0, 8).map((attempt) => {
        const pages = Array.isArray(attempt.pages) && attempt.pages.length
            ? ` · pp. ${attempt.pages.join(", ")}`
            : "";
        return `
            <div class="kpi-stage-row">
                <div class="kpi-stage-name">${_escapeHtml(attempt.target_id || "target")}</div>
                <div>${_escapeHtml(`${attempt.status || "unknown"}${pages}`)}</div>
            </div>
        `;
    }).join("");
    return `
        <div class="kpi-section">
            <div class="kpi-section-title">Resolution Completion</div>
            <div class="kpi-stage-list">
                <div class="kpi-stage-row">
                    <div class="kpi-stage-name">Targets</div>
                    <div>${_escapeHtml(`${completed}/${attempted || targetCount} completed`)}</div>
                </div>
                ${rows}
            </div>
        </div>
    `;
}

function _formatPct(ratio) {
    const value = Number(ratio);
    if (!Number.isFinite(value)) return "—";
    return `${(value * 100).toFixed(1)}%`;
}

function _coverageTone(ratio) {
    const value = Number(ratio);
    if (!Number.isFinite(value)) return "neutral";
    if (value >= 0.85) return "good";
    if (value >= 0.6) return "warn";
    return "bad";
}

function _coverageCard(label, ratio, note) {
    const tone = _coverageTone(ratio);
    const pct = _formatPct(ratio);
    const clamped = Math.max(0, Math.min(100, (Number(ratio) || 0) * 100));
    return `
        <div class="kpi-card kpi-card--coverage kpi-card--${tone}">
            <div class="kpi-label">${_escapeHtml(label)}</div>
            <div class="kpi-value">${_escapeHtml(pct)}</div>
            <div class="kpi-coverage-bar"><div class="kpi-coverage-bar-fill" style="width:${clamped}%"></div></div>
            <div class="kpi-note">${_escapeHtml(note || "")}</div>
        </div>
    `;
}

function _buildGraphCoverageSection(coverage) {
    if (!coverage || typeof coverage !== "object") return "";

    const chain = coverage.diagnostic_chain || {};
    const fm = coverage.failure_mode_coverage || {};
    const ca = coverage.corrective_action_coverage || {};
    const comp = coverage.component_coverage || {};
    const ec = coverage.error_code_coverage || {};
    const integrity = coverage.schema_integrity || {};

    const healthScore = Number(coverage.health_score) || 0;
    const healthTone = _coverageTone(healthScore);

    const cards = [
        _coverageCard(
            "End-to-End Diagnosis",
            chain.symptoms_end_to_end_ratio,
            `${_formatMetricsNumber(chain.symptoms_end_to_end_resolved || 0)} / ${_formatMetricsNumber(chain.symptoms_total || 0)} symptoms reach a corrective action`,
        ),
        _coverageCard(
            "Symptom → FailureMode",
            chain.symptoms_with_failure_mode_ratio,
            `${_formatMetricsNumber(chain.orphan_symptoms || 0)} orphan symptom(s)`,
        ),
        _coverageCard(
            "FailureMode → Action",
            fm.with_corrective_action_ratio,
            `${_formatMetricsNumber(fm.without_corrective_action || 0)} failure mode(s) without remediation`,
        ),
        _coverageCard(
            "FailureMode → Component",
            fm.with_component_anchor_ratio,
            `${_formatMetricsNumber(fm.without_component_anchor || 0)} not anchored to a component`,
        ),
        _coverageCard(
            "FailureMode Reachability",
            fm.reachable_from_symptom_ratio,
            `${_formatMetricsNumber(fm.orphan_upstream || 0)} failure mode(s) unreachable from any symptom`,
        ),
        _coverageCard(
            "CorrectiveAction Usage",
            ca.used_by_failure_mode_ratio,
            `${_formatMetricsNumber(ca.orphan_corrective_actions || 0)} orphan action(s)`,
        ),
        _coverageCard(
            "Component Utilization",
            comp.components_in_failure_chain_ratio,
            `${_formatMetricsNumber(comp.components_only_structural || 0)} component(s) never referenced by a failure mode`,
        ),
    ];

    if ((ec.error_codes_total || 0) > 0) {
        cards.push(_coverageCard(
            "ErrorCode Wiring",
            ec.fully_wired_ratio,
            `${_formatMetricsNumber(ec.fully_wired || 0)} / ${_formatMetricsNumber(ec.error_codes_total || 0)} wired to Asset and FailureMode`,
        ));
    }

    const breadthRows = `
        <div class="kpi-stage-row">
            <div class="kpi-stage-name">Avg CorrectiveActions per FailureMode</div>
            <div>${_escapeHtml(String(fm.avg_corrective_actions_per_failure_mode ?? 0))}</div>
        </div>
        <div class="kpi-stage-row">
            <div class="kpi-stage-name">Avg Symptoms per FailureMode</div>
            <div>${_escapeHtml(String(fm.avg_symptoms_per_failure_mode ?? 0))}</div>
        </div>
        <div class="kpi-stage-row">
            <div class="kpi-stage-name">Relationship Density (rels / non-asset node)</div>
            <div>${_escapeHtml(String(integrity.relationship_density ?? 0))}</div>
        </div>
    `;

    const integrityIssues = [];
    if ((integrity.dangling_references || 0) > 0) {
        integrityIssues.push(`${_formatMetricsNumber(integrity.dangling_references)} dangling reference(s)`);
    }
    if ((integrity.domain_range_violations || 0) > 0) {
        integrityIssues.push(`${_formatMetricsNumber(integrity.domain_range_violations)} domain/range violation(s)`);
    }
    if (Array.isArray(integrity.missing_relationship_types) && integrity.missing_relationship_types.length) {
        integrityIssues.push(`Missing relation types: ${integrity.missing_relationship_types.join(", ")}`);
    }
    const integrityLine = integrityIssues.length
        ? `<div class="kpi-section-note kpi-section-note--warn">⚠ ${_escapeHtml(integrityIssues.join(" · "))}</div>`
        : `<div class="kpi-section-note kpi-section-note--ok">✓ Schema integrity: no dangling refs, no domain/range violations.</div>`;

    return `
        <div class="kpi-section kpi-section--coverage">
            <div class="kpi-section-title">
                Graph Coverage &amp; Clarity
                <span class="kpi-health-badge kpi-health-badge--${healthTone}">Health ${_formatPct(healthScore)}</span>
            </div>
            <div class="kpi-grid kpi-grid--coverage">${cards.join("")}</div>
            <div class="kpi-section-title kpi-section-title--sub">Breadth &amp; Density</div>
            <div class="kpi-stage-list">${breadthRows}</div>
            ${integrityLine}
        </div>
    `;
}

function _renderRunMetricsWidget(metrics) {
    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--run-metrics";
    wrap.innerHTML = `
        <div class="widget-header">
            <span class="widget-icon">📊</span>
            <span class="widget-title">Extraction KPIs</span>
        </div>
        <p class="widget-hint">Complete extraction metrics recovered from the legacy summary view.</p>
        ${_runMetricsMarkup(metrics)}
    `;
    return wrap;
}

function _renderExportWidget(payload) {
    const exported = Boolean(payload?.exported);
    const editorUrl = payload?.editor_url || _modifyWorkspaceUrl || "";
    const metrics = payload?.metrics || null;
    if (editorUrl) {
        _setModifyWorkspaceAvailability(editorUrl);
    }

    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--export";
    if (exported && metrics) {
        wrap.classList.add("chat-widget--export-metrics");
    }
    wrap.innerHTML = exported
        ? `
            <div class="widget-header">
                <span class="widget-icon">Modify</span>
                <span class="widget-title">Export Complete</span>
            </div>
            <p class="widget-hint">The JSON download starts automatically. The modify workspace opens below so you can inspect and modify the graph.</p>
        `
        : `
            <div class="widget-header">
                <span class="widget-icon">Export</span>
                <span class="widget-title">Export Starting</span>
            </div>
            <p class="widget-hint">All triplets have been reviewed. Export will run automatically.</p>
        `;
    if (exported && metrics) {
        const metricsBlock = document.createElement("div");
        metricsBlock.className = "export-metrics-block";
        metricsBlock.innerHTML = _runMetricsMarkup(metrics);
        wrap.appendChild(metricsBlock);
    }
    const actions = document.createElement("div");
    actions.className = "widget-actions";

    if (!exported) {
        const btn = document.createElement("button");
        btn.className = "btn-primary btn-sm";
        btn.textContent = "Export Now";
        btn.addEventListener("click", () => {
            btn.disabled = true;
            btn.textContent = "Exporting…";
            _postAction("export_ontology", {});
        });
        actions.appendChild(btn);
        _scheduleAutoExport();
    } else {
        const inspectBtn = document.createElement("button");
        inspectBtn.className = "btn-primary btn-sm";
        inspectBtn.textContent = "Inspect / Modify Graph";
        inspectBtn.addEventListener("click", () => {
            if (editorUrl) _openModifyWorkspace(editorUrl);
        });
        actions.appendChild(inspectBtn);

        const openTabBtn = document.createElement("button");
        openTabBtn.className = "btn-secondary btn-sm";
        openTabBtn.textContent = "Open In New Tab";
        openTabBtn.addEventListener("click", () => {
            if (!editorUrl) return;
            window.open(editorUrl, "_blank", "noopener");
        });
        actions.appendChild(openTabBtn);
        _scheduleExportDownloadAndModifyOpen(payload);
    }
    wrap.appendChild(actions);
    return wrap;
}

function _scheduleAutoExport() {
    if (_autoExportRequested) return;
    _autoExportRequested = true;
    window.setTimeout(() => {
        _postAction("export_ontology", { auto: true });
    }, 120);
}

function _scheduleExportDownloadAndModifyOpen(payload = {}) {
    window.setTimeout(() => {
        _downloadExportOnce(payload);
        const editorUrl = payload?.editor_url || _modifyWorkspaceUrl;
        if (editorUrl) {
            const key = `${editorUrl}:${payload?.output_path || payload?.download_filename || ""}`;
            if (_lastAutoOpenedModifyKey !== key) {
                _lastAutoOpenedModifyKey = key;
                _openModifyWorkspace(editorUrl);
            }
        }
    }, 180);
}

function _downloadExportOnce(payload = {}) {
    if (!_pdfId) return;
    const key = `${_pdfId}:${payload?.output_path || payload?.download_filename || "latest"}`;
    if (_lastDownloadedExportKey === key) return;
    _lastDownloadedExportKey = key;

    const link = document.createElement("a");
    link.href = `/chat/download/${encodeURIComponent(_pdfId)}?t=${Date.now()}`;
    link.download = payload?.download_filename || "ontology_export.json";
    link.hidden = true;
    document.body.appendChild(link);
    link.click();
    link.remove();
}

// ── User input ─────────────────────────────────────────────────────────

function _setupInput() {
    const form = document.getElementById("chat-input-form");
    const input = document.getElementById("chat-input");
    if (!form || !input) return;

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        input.value = "";
        _appendUserMessage(text);
        _sendMessage(text);
    });
}

function _sendMessage(text) {
    if (!_pdfId) return;
    _setSystemBusy("Processing your message…", _currentPhase);
    _showThinkingIndicator("Processing your message…");
    fetch("/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pdf_id: _pdfId, message: text }),
    })
        .then(async (res) => {
            if (res.ok) return;
            if (res.status === 404) {
                _markSessionLost();
                return;
            }
            const err = await res.json().catch(() => ({}));
            _appendErrorMessage(err.detail || "Could not send message.");
        })
        .catch(() => _appendErrorMessage("Could not send message — server may be unavailable."));
}

async function _postAction(action, payload = {}) {
    if (!_pdfId) return;
    _setSystemBusy(`Running ${_humanPhaseLabel(action)}…`, _currentPhase);
    _showThinkingIndicator(`Running ${_humanPhaseLabel(action)}…`);
    try {
        const res = await fetch("/chat/action", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pdf_id: _pdfId, action, payload }),
        });
        if (!res.ok) {
            if (res.status === 404) {
                _markSessionLost();
                return;
            }
            const err = await res.json().catch(() => ({}));
            _appendErrorMessage(err.detail || "Action failed.");
        }
    } catch {
        _appendErrorMessage("Could not reach the server.");
    }
}

// ── Quick-action chips ─────────────────────────────────────────────────

export function setQuickActions(actions) {
    _renderQuickActions(actions);
}

function _renderQuickActions(actions) {
    const bar = document.getElementById("chat-quick-actions");
    if (!bar) return;
    bar.innerHTML = "";
    actions.forEach(({ label, message }) => {
        const chip = document.createElement("button");
        chip.className = "quick-chip";
        chip.textContent = label;
        chip.addEventListener("click", () => {
            _appendUserMessage(message);
            _sendMessage(message);
        });
        bar.appendChild(chip);
    });
}

function _syncQuickActions(context = {}) {
    const phase = String(_currentPhase || "loaded").toLowerCase();
    const widget = String(context.widget || "");
    const graphKey = _kgGraphData
        ? `${_kgGraphData.approved_triplet_count ?? ""}:${_kgGraphData.current_triplet_index ?? ""}:${_kgGraphData.total_triplets ?? ""}`
        : "";
    const key = `${phase}:${widget}:${Boolean(_modifyWorkspaceUrl)}:${graphKey}`;
    if (key === _lastQuickActionsKey) return;
    _lastQuickActionsKey = key;
    _renderQuickActions(_quickActionsForPhase(phase, widget));
}

function _quickActionsForPhase(phase, widget = "") {
    if (widget === "sections" || ["scoping", "propose_cut_plan", "edit_cut_plan", "approve_cut_plan"].includes(phase)) {
        return [
            { label: "Why these sections?", message: "Do these selected sections make sense for diagnostic extraction? Point out anything suspicious." },
            { label: "List selected pages", message: "Which page ranges are currently selected and why are they useful?" },
            { label: "What blocks next?", message: "What still needs to happen before ontology drafting can start?" },
        ];
    }

    if (widget === "ontology_review" || widget === "required_fields" || ["ontology_draft", "draft_ontology"].includes(phase)) {
        return [
            { label: "Required fields", message: "Which required ontology fields are still missing?" },
            { label: "Graph issues", message: "Which graph issues or weak links should I review before extraction?" },
            { label: "Ready to extract?", message: "Is the ontology draft ready for triplet extraction? Give a concrete yes/no with reasons." },
        ];
    }

    if (widget === "triplet" || ["validation", "get_next_triplet", "approve_triplet", "skip_triplet", "edit_triplet"].includes(phase)) {
        return [
            { label: "Assess triplet", message: "Assess the current triplet: does the symptom, failure mode, and corrective action chain make sense?" },
            { label: "What remains?", message: "How many triplets remain to review and how many have been approved?" },
            { label: "Re-extract source", message: "If this triplet looks weak, which source page should I re-extract and why?" },
        ];
    }

    if (["extraction", "run_extraction"].includes(phase)) {
        return [
            { label: "Extraction status", message: "What is being extracted right now and what should I expect next?" },
            { label: "Quality risks", message: "What quality risks should I watch for when triplets appear?" },
            { label: "Selected scope", message: "Which selected pages are feeding this extraction?" },
        ];
    }

    if (widget === "export" || ["export", "export_ontology"].includes(phase)) {
        return [
            { label: "Export status", message: "Is the JSON exported and where can I modify the graph now?" },
            { label: "Show KPIs", message: "Show the extraction KPIs, including cost, duration, and validated triplets." },
            { label: "Modify graph", message: "Open or explain the modify workspace for the exported graph." },
        ];
    }

    if (_modifyWorkspaceUrl || phase === "completed") {
        return [
            { label: "Inspect graph", message: "Summarize the exported graph: node counts, relationship counts, and anything suspicious." },
            { label: "Find a node", message: "How can I inspect a specific node in the modify workspace?" },
            { label: "Save version", message: "What should I check before saving a modified graph version?" },
        ];
    }

    return [
        { label: "Current phase", message: "What phase are we in and what is the next concrete action?" },
        { label: "Any blockers?", message: "What is blocking the workflow right now, if anything?" },
        { label: "What should I check?", message: "What should I review on this screen before continuing?" },
    ];
}

// ── PDF viewer ─────────────────────────────────────────────────────────

async function _loadPdf(pdfPath) {
    try {
        _pdfjsLib = await import("https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs");
        _pdfjsLib.GlobalWorkerOptions.workerSrc =
            "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";
        _pdfDoc = await _pdfjsLib.getDocument(pdfPath).promise;
        _totalPages = _pdfDoc.numPages;
        _renderedPdfPages.clear();
        _pdfSearchIndex = new Array(_totalPages + 1).fill("");
        _pdfIndexPromise = null;
        _pdfSearchMatches = [];
        _pdfSearchCursor = -1;
        _pdfSearchQuery = "";
        await _renderPdfScroller();
        _syncPdfButtons();
        _setPdfStatus(`PDF ready · ${_totalPages} page(s)`, "ready");
        _setPdfSearchMeta("Search is ready once the PDF text is indexed.");
        if (_pendingPdfPage) {
            const page = _pendingPdfPage;
            _pendingPdfPage = null;
            window.setTimeout(() => _scrollPdfToPage(page), 0);
        }
        _pdfIndexPromise = _buildPdfSearchIndex();
    } catch (e) {
        console.warn("PDF viewer error:", e);
        _setPdfStatus("PDF preview unavailable.", "error");
        _setPdfSearchMeta("Search is unavailable because the PDF preview could not load.");
    }
}

async function _renderPdfScroller() {
    const container = document.getElementById("chat-pdf-container");
    if (!container) return;

    container.innerHTML = "";
    if (_pdfObserver) _pdfObserver.disconnect();
    if (_visiblePageObserver) _visiblePageObserver.disconnect();

    const firstPage = await _pdfDoc.getPage(1);
    const viewport = firstPage.getViewport({ scale: 1.2 });

    for (let pageNum = 1; pageNum <= _totalPages; pageNum += 1) {
        const wrapper = document.createElement("div");
        wrapper.className = "pdf-page-wrapper chat-pdf-page";
        wrapper.id = `chat-pdf-page-${pageNum}`;
        wrapper.dataset.pageNum = `${pageNum}`;
        wrapper.style.minHeight = `${viewport.height}px`;
        wrapper.style.width = `${viewport.width}px`;

        const label = document.createElement("div");
        label.className = "pdf-page-label";
        label.textContent = `${pageNum} / ${_totalPages}`;

        const canvas = document.createElement("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        wrapper.appendChild(label);
        wrapper.appendChild(canvas);
        container.appendChild(wrapper);
    }

    await _renderPdfPage(1);
    _setupPdfObservers(container);
    _currentPage = 1;
    _updatePageIndicator();
}

export function navigateToPage(pageNum) {
    _scrollPdfToPage(pageNum);
}

function _setupPdfControls() {
    const searchInput = document.getElementById("chat-pdf-search");
    if (!searchInput || searchInput.dataset.bound === "true") return;

    const searchBtn = document.getElementById("chat-pdf-search-btn");
    const prevMatchBtn = document.getElementById("chat-pdf-prev-match");
    const nextMatchBtn = document.getElementById("chat-pdf-next-match");
    const prevPageBtn = document.getElementById("chat-prev-page");
    const nextPageBtn = document.getElementById("chat-next-page");

    searchInput.dataset.bound = "true";
    searchBtn?.addEventListener("click", () => { void _runPdfSearch(searchInput.value); });
    prevMatchBtn?.addEventListener("click", () => _stepPdfMatch(-1));
    nextMatchBtn?.addEventListener("click", () => _stepPdfMatch(1));
    prevPageBtn?.addEventListener("click", () => _scrollPdfToPage(_currentPage - 1));
    nextPageBtn?.addEventListener("click", () => _scrollPdfToPage(_currentPage + 1));
    searchInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            void _runPdfSearch(searchInput.value);
        }
    });
    const _debouncedSearch = _debounce((val) => {
        if (val.trim()) void _runPdfSearch(val);
        else _clearPdfSearch();
    }, 300);
    searchInput.addEventListener("input", () => _debouncedSearch(searchInput.value));
}

function _setupPdfObservers(container) {
    _pdfObserver = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                if (!entry.isIntersecting) continue;
                const pageNum = parseInt(entry.target.dataset.pageNum || "0", 10);
                if (pageNum > 0 && !_renderedPdfPages.has(pageNum)) {
                    void _renderPdfPage(pageNum);
                }
            }
        },
        { root: container, rootMargin: "700px 0px" },
    );

    _visiblePageObserver = new IntersectionObserver(
        (entries) => {
            const visible = entries
                .filter((entry) => entry.isIntersecting)
                .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
            if (!visible) return;
            const pageNum = parseInt(visible.target.dataset.pageNum || "0", 10);
            if (pageNum > 0 && pageNum !== _currentPage) {
                _currentPage = pageNum;
                _updatePageIndicator();
            }
        },
        { root: container, threshold: [0.35, 0.6, 0.85] },
    );

    [...container.children].forEach((child) => {
        if (!child.dataset?.pageNum) return;
        _pdfObserver.observe(child);
        _visiblePageObserver.observe(child);
    });
}

async function _renderPdfPage(pageNum) {
    if (!_pdfDoc || _renderedPdfPages.has(pageNum)) return;
    _renderedPdfPages.add(pageNum);

    const wrapper = document.getElementById(`chat-pdf-page-${pageNum}`);
    if (!wrapper) return;

    try {
        const page = await _pdfDoc.getPage(pageNum);
        const viewport = page.getViewport({ scale: 1.2 });
        const canvas = wrapper.querySelector("canvas");
        if (!canvas) return;

        canvas.width = viewport.width;
        canvas.height = viewport.height;
        wrapper.style.minHeight = `${viewport.height}px`;
        wrapper.style.width = `${viewport.width}px`;

        const ctx = canvas.getContext("2d");
        await page.render({ canvasContext: ctx, viewport }).promise;
    } catch (err) {
        console.warn(`Failed to render page ${pageNum}:`, err);
    }
}

async function _buildPdfSearchIndex() {
    if (!_pdfDoc) return;
    _setPdfStatus("Indexing PDF text for search…", "loading");

    for (let pageNum = 1; pageNum <= _totalPages; pageNum += 1) {
        if (_pdfSearchIndex[pageNum]) continue;
        try {
            const page = await _pdfDoc.getPage(pageNum);
            const textContent = await page.getTextContent();
            _pdfSearchIndex[pageNum] = textContent.items
                .map((item) => String(item?.str || ""))
                .join(" ")
                .toLowerCase();
        } catch (err) {
            console.warn(`Failed to index PDF page ${pageNum}:`, err);
            _pdfSearchIndex[pageNum] = "";
        }

        if (pageNum === _totalPages || pageNum % 12 === 0) {
            _setPdfSearchMeta(`Indexing PDF text… ${pageNum}/${_totalPages}`);
            await new Promise((resolve) => window.setTimeout(resolve, 0));
        }
    }

    _setPdfStatus(`PDF ready · ${_totalPages} page(s)`, "ready");
    _setPdfSearchMeta("Search the PDF by word or phrase.");
}

async function _runPdfSearch(rawQuery) {
    const query = String(rawQuery || "").trim().toLowerCase();
    if (!query) {
        _clearPdfSearch();
        return;
    }
    if (!_pdfDoc) return;

    _setPdfSearchMeta("Searching the PDF…");
    if (_pdfIndexPromise) await _pdfIndexPromise;

    _pdfSearchQuery = query;
    _pdfSearchMatches = [];
    _pdfSearchCursor = -1;

    document.querySelectorAll(".chat-pdf-page--match, .chat-pdf-page--active-match").forEach((node) => {
        node.classList.remove("chat-pdf-page--match", "chat-pdf-page--active-match");
    });

    for (let pageNum = 1; pageNum <= _totalPages; pageNum += 1) {
        if ((_pdfSearchIndex[pageNum] || "").includes(query)) {
            _pdfSearchMatches.push(pageNum);
        }
    }

    if (_pdfSearchMatches.length === 0) {
        _setPdfSearchMeta(`No matches for “${rawQuery}”.`);
        _syncPdfButtons();
        return;
    }

    _pdfSearchMatches.forEach((pageNum) => {
        document.getElementById(`chat-pdf-page-${pageNum}`)?.classList.add("chat-pdf-page--match");
    });

    const preview = _pdfSearchMatches.slice(0, 6).join(", ");
    const extra = _pdfSearchMatches.length > 6 ? ` … +${_pdfSearchMatches.length - 6}` : "";
    _setPdfSearchMeta(`${_pdfSearchMatches.length} match(es) on page(s) ${preview}${extra}.`);
    _activatePdfMatch(0);
}

function _stepPdfMatch(direction) {
    if (!_pdfSearchMatches.length) return;
    const nextIndex = (_pdfSearchCursor + direction + _pdfSearchMatches.length) % _pdfSearchMatches.length;
    _activatePdfMatch(nextIndex);
}

function _activatePdfMatch(index) {
    if (!_pdfSearchMatches.length) return;
    _pdfSearchCursor = Math.max(0, Math.min(index, _pdfSearchMatches.length - 1));

    document.querySelectorAll(".chat-pdf-page--active-match").forEach((node) => {
        node.classList.remove("chat-pdf-page--active-match");
    });

    const pageNum = _pdfSearchMatches[_pdfSearchCursor];
    const wrapper = document.getElementById(`chat-pdf-page-${pageNum}`);
    wrapper?.classList.add("chat-pdf-page--active-match");
    _scrollPdfToPage(pageNum);
    _setPdfSearchMeta(
        `Match ${_pdfSearchCursor + 1} of ${_pdfSearchMatches.length} for “${_pdfSearchQuery}” on page ${pageNum}.`,
    );
    _syncPdfButtons();
}

function _clearPdfSearch() {
    _pdfSearchQuery = "";
    _pdfSearchMatches = [];
    _pdfSearchCursor = -1;
    document.querySelectorAll(".chat-pdf-page--match, .chat-pdf-page--active-match").forEach((node) => {
        node.classList.remove("chat-pdf-page--match", "chat-pdf-page--active-match");
    });
    _setPdfSearchMeta(_pdfDoc ? "Search the PDF by word or phrase." : "Search is unavailable until the PDF loads.");
    _syncPdfButtons();
}

async function _probeSession() {
    if (_sessionLost || !_pdfId) return;
    try {
        const res = await fetch(`/chat/history/${encodeURIComponent(_pdfId)}`);
        if (res.status === 404) {
            _markSessionLost();
            return;
        }
        if (!res.ok) {
            setTimeout(_openStream, 3000);
            return;
        }
        _streamErrorCount = 0;
        _openStream();
    } catch {
        setTimeout(_openStream, 3000);
    }
}

function _markSessionLost() {
    if (_sessionLost) return;
    _sessionLost = true;
    _eventSource?.close();
    const input = document.getElementById("chat-input");
    const submit = document.querySelector("#chat-input-form button[type='submit']");
    if (input) input.disabled = true;
    if (submit) submit.disabled = true;
    _appendErrorMessage("The chat session was lost after a server reload. Reload the manual to continue.");
    _setAwaitingOperator("Session lost after server reload. Load the manual again to restore the workflow.");
}

function _scrollPdfToPage(pageNum) {
    if (!_totalPages) {
        _pendingPdfPage = pageNum;
        return;
    }
    if (pageNum < 1 || pageNum > _totalPages) return;
    const target = document.getElementById(`chat-pdf-page-${pageNum}`);
    if (!target) return;
    _currentPage = pageNum;
    _updatePageIndicator();
    void _renderPdfPage(pageNum);
    target.scrollIntoView({ behavior: "smooth", block: "start" });
}

function _updatePageIndicator() {
    const indicator = document.getElementById("chat-page-indicator");
    if (indicator) indicator.textContent = _totalPages ? `Page ${_currentPage} / ${_totalPages}` : "Page — / —";
    _syncPdfButtons();
}

function _syncPdfButtons() {
    const prevPageBtn = document.getElementById("chat-prev-page");
    const nextPageBtn = document.getElementById("chat-next-page");
    const prevMatchBtn = document.getElementById("chat-pdf-prev-match");
    const nextMatchBtn = document.getElementById("chat-pdf-next-match");

    if (prevPageBtn) prevPageBtn.disabled = !_totalPages || _currentPage <= 1;
    if (nextPageBtn) nextPageBtn.disabled = !_totalPages || _currentPage >= _totalPages;
    if (prevMatchBtn) prevMatchBtn.disabled = _pdfSearchMatches.length === 0;
    if (nextMatchBtn) nextMatchBtn.disabled = _pdfSearchMatches.length === 0;
}

function _setPdfStatus(text, tone = "neutral") {
    const el = document.getElementById("chat-pdf-status");
    if (!el) return;
    el.textContent = text;
    el.dataset.tone = tone;
}

function _setPdfSearchMeta(text) {
    const el = document.getElementById("chat-pdf-search-meta");
    if (!el) return;
    el.textContent = text;
}

function _setPhaseLabel(phase) {
    const label = document.getElementById("chat-phase-label");
    if (!label) return;
    label.textContent = _humanPhaseLabel(phase);
}

function _setTurnIndicator(mode, badge, text) {
    const root = document.getElementById("chat-turn-indicator");
    const badgeEl = document.getElementById("chat-turn-badge");
    const textEl = document.getElementById("chat-turn-text");
    if (!root || !badgeEl || !textEl) return;
    root.dataset.mode = mode;
    badgeEl.textContent = badge;
    textEl.textContent = text;
}

function _setSystemBusy(detail, phase = _currentPhase) {
    _currentPhase = phase || _currentPhase;
    _setPhaseLabel(_currentPhase);
    const label = _humanPhaseLabel(_currentPhase);
    _setTurnIndicator("working", "System is working", detail ? `${label} · ${detail}` : `${label} in progress.`);
    _syncQuickActions({ widget: "working" });
}

function _setAwaitingOperator(detail = "") {
    const fallback = "Ask about the manual, selected sections or pages, extracted ontology, triplets, or workflow status.";
    _setTurnIndicator("operator", "Your turn", detail || fallback);
    _syncQuickActions({ widget: _lastWidgetType || "operator" });
}

function _widgetPrompt(widgetType) {
    switch (widgetType) {
        case "sections":
            return "Review the section selection, scroll the PDF, or ask about the current cut plan.";
        case "required_fields":
            return "Fill the required ontology fields so extraction can continue.";
        case "triplet":
            return "Review the current triplet and decide whether to approve, edit, or skip it.";
        case "node_draft":
            return "Review the proposed node draft and confirm it if it is correct.";
        case "export":
            return "The JSON export runs automatically. The modify workspace opens as soon as the file is ready.";
        case "run_metrics":
            return "The full extraction KPIs are shown here, including duration, cost, token usage, stage breakdown, and node counts.";
        case "extraction_graph":
            return "The extraction graph is ready. Triplet review will focus it on the current symptom chain.";
        default:
            return "";
    }
}

function _humanPhaseLabel(phase) {
    const key = String(phase || "loaded").trim().toLowerCase();
    return {
        loaded: "Manual Loaded",
        scoping: "Scoping",
        propose_cut_plan: "Scoping",
        edit_cut_plan: "Scoping",
        approve_cut_plan: "Scoping",
        ontology_draft: "Ontology Draft",
        draft_ontology: "Ontology Draft",
        extraction: "Extraction",
        run_extraction: "Extraction",
        validation: "Triplet Review",
        get_next_triplet: "Triplet Review",
        approve_triplet: "Triplet Review",
        skip_triplet: "Triplet Review",
        edit_triplet: "Triplet Review",
        get_run_metrics: "KPIs",
        export: "Export",
        export_ontology: "Export",
        completed: "Completed",
    }[key] || key.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

// ── Utilities ──────────────────────────────────────────────────────────

function _scrollToBottom() {
    const stream = _stream();
    if (stream) stream.scrollTop = stream.scrollHeight;
}

function _md(text) {
    if (!text) return "";
    return _escapeHtml(text)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`(.+?)`/g, "<code>$1</code>")
        .replace(/\[\[(.+?)\]\]/g, (_m, label) =>
            `<button class="chat-panel-link" data-sheet-link="true">${label}</button>`
        )
        .replace(/\n/g, "<br>");
}

function _escapeHtml(text) {
    return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function _normaliseAssistantText(text) {
    let remaining = String(text || "");
    while (true) {
        const leadingJson = _extractLeadingJsonObject(remaining);
        if (!leadingJson) return remaining.trim();

        let parsed;
        try {
            parsed = JSON.parse(leadingJson.json);
        } catch {
            return remaining.trim();
        }

        if (!_isWidgetEnvelope(parsed)) return remaining.trim();
        remaining = leadingJson.rest;
    }
}

function _isWidgetEnvelope(value) {
    return Boolean(
        value
        && typeof value === "object"
        && value.widget
        && (value.payload || value.event === "update" || value.event === "render"),
    );
}

function _extractLeadingJsonObject(text) {
    const source = String(text || "").trimStart();
    if (!source.startsWith("{")) return null;

    let depth = 0;
    let inString = false;
    let escaped = false;

    for (let index = 0; index < source.length; index += 1) {
        const char = source[index];
        if (inString) {
            if (escaped) {
                escaped = false;
            } else if (char === "\\") {
                escaped = true;
            } else if (char === '"') {
                inString = false;
            }
            continue;
        }

        if (char === '"') {
            inString = true;
        } else if (char === "{") {
            depth += 1;
        } else if (char === "}") {
            depth -= 1;
            if (depth === 0) {
                return {
                    json: source.slice(0, index + 1),
                    rest: source.slice(index + 1),
                };
            }
        }
    }

    return null;
}
