// PDF.js setup
const pdfjsLib = await import("https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs");
pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";

// ─── Auto-fill date ───
const dateInput = document.getElementById("extraction-date");
dateInput.value = new Date().toISOString().split("T")[0];

// ─── Load model lists from config.yaml via API ───
(async function loadModelConfig() {
    try {
        const res = await fetch("/api/config");
        if (!res.ok) return;
        const cfg = await res.json();

        function populateSelect(selectId, models) {
            const select = document.getElementById(selectId);
            if (!select || !models || models.length === 0) return;
            select.innerHTML = "";
            for (const m of models) {
                const opt = document.createElement("option");
                opt.value = m.id;
                opt.textContent = m.label;
                if (m.default) opt.selected = true;
                select.appendChild(opt);
            }
        }

        populateSelect("scoping-model", cfg.scoping_models);
        populateSelect("llm-model", cfg.extraction_models);

        // Populate advanced settings fields from config
        const thresholdInput = document.getElementById("small-doc-threshold");
        const retriesInput = document.getElementById("reflective-max-retries");
        const severitySelect = document.getElementById("reflective-severity");
        const pipelineModeEl = document.getElementById("pipeline-mode");
        if (thresholdInput && cfg.small_doc_threshold != null)
            thresholdInput.value = cfg.small_doc_threshold;
        if (retriesInput && cfg.reflective_loop?.max_retries != null)
            retriesInput.value = cfg.reflective_loop.max_retries;
        if (severitySelect && cfg.reflective_loop?.retry_on_severity)
            severitySelect.value = cfg.reflective_loop.retry_on_severity;
        if (pipelineModeEl && cfg.pipeline?.mode) {
            pipelineModeEl.value = cfg.pipeline.mode;
        }
    } catch (e) {
        console.warn("Could not load model config, using HTML defaults", e);
    }
})();

// ─── Load manual list from backend ───
(async function loadAvailableManuals() {
    const manualSelect = document.getElementById("manual-select");
    if (!manualSelect) return;

    try {
        const res = await fetch("/api/manuals");
        if (!res.ok) throw new Error("Could not list manuals");
        const data = await res.json();
        const manuals = data.manuals || [];

        manualSelect.innerHTML = "";
        if (manuals.length === 0) {
            const opt = document.createElement("option");
            opt.value = "";
            opt.textContent = "No manuals available";
            manualSelect.appendChild(opt);
            return;
        }

        for (const manual of manuals) {
            const opt = document.createElement("option");
            opt.value = manual.filename;
            opt.textContent = manual.filename;
            manualSelect.appendChild(opt);
        }
    } catch (err) {
        manualSelect.innerHTML = "";
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "Failed to load manuals";
        manualSelect.appendChild(opt);
        console.warn("Could not load manual list", err);
    }
})();

// ─── State ───
const state = {
    pdfId: null,
    sourceType: "",
    sourceTitle: "",
    modelName: "",
    targetLanguage: "en",
    triplets: [],
    currentIndex: 0,
    validatedTriplets: [],
    pdfDoc: null,
    totalPages: 0,
    // Cut plan state
    cutPlan: null,
    selectedPages: new Set(),
    cutPlanSections: [],
    uploadFilename: "",
    operator: "",
    extractionDate: "",
    scopingModel: "",
    pdfLoaded: false,
    productInfo: null,
    pageOffset: 0,
    ontologyDraft: null,
    ontologyPagesToKeep: null,
    extractionInProgress: false,
    tripletsExtracted: false,
    exportCompleted: false,
    autoExportTriggered: false,
    runMetrics: null,

    // ─── Multi-agent / run tracking ───
    runId: null,                    // from UploadResponse.run_id
    pipelineMode: "classic",        // "classic" | "multi_agent"
    supervisorStatus: null,         // last /multi-agent/status payload
    supervisorAudit: null,          // last /multi-agent/audit payload
    statusPollTimer: null,          // interval handle for active polling

    // ─── Confidence UI state ───
    confidenceSort: "score_asc",    // "score_asc" | "type"
    showAutoApproved: false,        // collapsed by default
    nodeDecisions: {},              // "type::id" -> "approved" | "rejected" | "skipped"

    // ─── Escalations (client-synthesized until backend EscalationMessage lands) ───
    escalations: [],                // list of EscalationMessage objects
    escalationDecisions: {},        // escalation_id -> chosen option
};

const statusActivity = {
    upload: null,
    cutPlan: null,
    ontology: null,
};

/**
 * Client-side contract for supervisor escalations. Frozen shape — when the
 * backend ships a real EscalationMessage Pydantic model the only change here
 * is swapping `synthesizeEscalations()` for `result.escalations`.
 *
 * @typedef {Object} EscalationMessage
 * @property {string} escalation_id   stable key, e.g. "esc-fm_channel_2-unplugged"
 * @property {string} phase           GraphPhase value when raised
 * @property {string} agent           agent that raised it (or "graph_reasoning")
 * @property {string} severity        "blocking" | "warning" | "info"
 * @property {string} issue           short human sentence
 * @property {string[]} options       ["approve_as_is","reject_node","provide_correction","skip"]
 * @property {Object} context         { node_type, node_id, score, suggested_relation?, issue_code? }
 */

// ─── API client wrapper ───
// Thin layer: existing direct fetch() callsites are left alone; new code uses api.*
const api = {
    async _json(method, path, body) {
        const opts = { method, headers: {} };
        if (body !== undefined) {
            opts.headers["Content-Type"] = "application/json";
            opts.body = JSON.stringify(body);
        }
        const res = await fetch(path, opts);
        if (!res.ok) {
            let detail = res.statusText;
            try { const payload = await res.json(); if (payload?.detail) detail = payload.detail; } catch {}
            throw new Error(`${method} ${path} ${res.status}: ${detail}`);
        }
        return await res.json();
    },
    getConfig()                 { return this._json("GET",  "/api/config"); },
    postConfig(overrides)       { return this._json("POST", "/api/config", overrides); },
    multiAgentStatus(runId)     { return this._json("GET",  `/multi-agent/status/${encodeURIComponent(runId)}`); },
    multiAgentAudit(runId)      { return this._json("GET",  `/multi-agent/audit/${encodeURIComponent(runId)}`); },
};

// ─── DOM Elements ───
const uploadScreen = document.getElementById("upload-screen");
const uploadForm = document.getElementById("upload-form");
const uploadBtn = document.getElementById("upload-btn");
const uploadStatus = document.getElementById("upload-status");
const cutPlanScreen = document.getElementById("cut-plan-screen");
const ontologyScreen = document.getElementById("ontology-screen");
const mainLayout = document.getElementById("main-layout");
const pdfContainer = document.getElementById("pdf-container");
const ontologyPdfContainer = document.getElementById("ontology-pdf-container");
const pdfTitle = document.getElementById("pdf-title");
const symContainer = document.getElementById("symptom-table-container");
const fmContainer = document.getElementById("fm-table-container");
const caContainer = document.getElementById("ca-table-container");
const tripletCardContainer = document.getElementById("triplet-card-container");
const tripletCounter = document.getElementById("triplet-counter");
const reviewProgressBar = document.getElementById("review-progress-bar");
const reviewProgressLabel = document.getElementById("review-progress-label");
const reviewStatSaved = document.getElementById("review-stat-saved");
const reviewStatDiscarded = document.getElementById("review-stat-discarded");
const actionButtons = document.getElementById("action-buttons");
const discardBtn = document.getElementById("discard-btn");
const saveBtn = document.getElementById("save-btn");
const summary = document.getElementById("summary");
const summaryText = document.getElementById("summary-text");
const summaryExportStatus = document.getElementById("summary-export-status");
const summaryKpis = document.getElementById("summary-kpis");
const generateBtn = document.getElementById("generate-btn");
const openGraphEditorBtn = document.getElementById("open-graph-editor-btn");
const appBarOperator = document.getElementById("app-bar-operator");
const appBarDate = document.getElementById("app-bar-date");

// Cut plan DOM
const cpPdfContainer = document.getElementById("cp-pdf-container");
const cpDocTitle = document.getElementById("cp-doc-title");
const sectionCards = document.getElementById("section-cards");
const cpPageCounter = document.getElementById("cp-page-counter");
const offsetInput = document.getElementById("offset-input");
const cpApproveBtn = document.getElementById("cp-approve-btn");
const cpSkipBtn = document.getElementById("cp-skip-btn");
const cpStatus = document.getElementById("cp-status");
const addRangeBtn = document.getElementById("add-range-btn");
const addRangeForm = document.getElementById("add-range-form");
const rangeStart = document.getElementById("range-start");
const rangeEnd = document.getElementById("range-end");
const rangeName = document.getElementById("range-name");
const rangeConfirmBtn = document.getElementById("range-confirm-btn");
const rangeCancelBtn = document.getElementById("range-cancel-btn");
const ontologyDocTitle = document.getElementById("ontology-doc-title");
const ontologySummaryCard = document.getElementById("ontology-summary-card");
const ontologyGuidance = document.getElementById("ontology-guidance");
const ontologyIssuesBlock = document.getElementById("ontology-issues-block");
const ontologyIssues = document.getElementById("ontology-issues");
const ontologyFieldsBlock = document.getElementById("ontology-fields-block");
const ontologyFields = document.getElementById("ontology-fields");
const ontologyStatus = document.getElementById("ontology-status");
const ontologyContinueBtn = document.getElementById("ontology-continue-btn");
const ontologyRerunBtn = document.getElementById("ontology-rerun-btn");
// Graph reasoning DOM
const graphIssuesBlock = document.getElementById("graph-issues-block");
const graphIssuesList = document.getElementById("graph-issues");
const suggestedRelationsBlock = document.getElementById("suggested-relations-block");
const suggestedRelationsList = document.getElementById("suggested-relations-list");
const suggestedRelationsCount = document.getElementById("suggested-relations-count");
const suggestedRelationsBulk = document.getElementById("suggestion-bulk-actions");
const applySuggestionsBtn = document.getElementById("apply-suggestions-btn");
const rejectAllSuggestionsBtn = document.getElementById("reject-all-suggestions-btn");

// ─── Confidence / multi-agent / escalation DOM ───
const phaseStrip = document.getElementById("phase-strip");
const auditDrawer = document.getElementById("audit-drawer");
const auditDrawerToggle = document.getElementById("audit-drawer-toggle");
const auditDrawerClose = auditDrawer?.querySelector(".audit-drawer-close");
const auditEntriesCount = document.getElementById("audit-entries-count");
const auditTokenLedger = document.getElementById("audit-token-ledger");
const auditPhaseHistory = document.getElementById("audit-phase-history");
const auditSupervisorLog = document.getElementById("audit-supervisor-log");
const ontologyNodesBlock = document.getElementById("ontology-nodes-block");
const ontologyNodesList = document.getElementById("ontology-nodes-list");
const ontologyNodesCount = document.getElementById("ontology-nodes-count");
const ontologyNodesSort = document.getElementById("ontology-nodes-sort");
const showAutoApprovedCheckbox = document.getElementById("show-auto-approved");
const bulkApproveBtn = document.getElementById("bulk-approve-btn");
const escalationsBlock = document.getElementById("escalations-block");
const escalationsList = document.getElementById("escalations-list");
const escalationsCount = document.getElementById("escalations-count");
const pipelineModeSelect = document.getElementById("pipeline-mode");

// ─── Advanced / Research view toggle (ontology screen) ───
// All confidence/graph-reasoning/escalation blocks live inside a <details>
// element. The operator-facing core view shows only Status + Required
// Information. Power users / researchers can expand the panel to access the
// full diagnostic surface; their preference is persisted across sessions.
const ontologyAdvancedPanel = document.getElementById("ontology-advanced-panel");
if (ontologyAdvancedPanel) {
    const ADVANCED_PANEL_KEY = "ontology.advancedPanel.open";
    try {
        const stored = localStorage.getItem(ADVANCED_PANEL_KEY);
        ontologyAdvancedPanel.open = stored === "true";
    } catch {
        ontologyAdvancedPanel.open = false;
    }
    ontologyAdvancedPanel.addEventListener("toggle", () => {
        try {
            localStorage.setItem(ADVANCED_PANEL_KEY, String(ontologyAdvancedPanel.open));
        } catch {
            /* localStorage unavailable — best-effort persistence */
        }
    });
}

// ─── Upload Flow ───

uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    state.scopingModel = document.getElementById("scoping-model").value;
    state.modelName = document.getElementById("llm-model").value;
    state.targetLanguage = document.getElementById("graph-language").value;
    state.operator = document.getElementById("operator-name").value.trim();
    state.extractionDate = dateInput.value;
    // The user enters the absolute PDF page where manual page 1 appears.
    // offset = (PDF page of manual p.1) - 1
    const manualPage1PdfPage = parseInt(document.getElementById("startup-page-offset").value) || 1;
    state.pageOffset = Math.max(0, manualPage1PdfPage - 1);

    // Send advanced settings to backend before starting the pipeline
    const advancedOverrides = {};
    const threshVal = parseInt(document.getElementById("small-doc-threshold")?.value);
    const retriesVal = parseInt(document.getElementById("reflective-max-retries")?.value);
    const severityVal = document.getElementById("reflective-severity")?.value;
    const pipelineModeVal = pipelineModeSelect?.value;
    if (!isNaN(threshVal)) advancedOverrides.small_doc_threshold = threshVal;
    if (!isNaN(retriesVal)) advancedOverrides.max_retries = retriesVal;
    if (severityVal) advancedOverrides.retry_on_severity = severityVal;
    if (pipelineModeVal) {
        advancedOverrides.pipeline_mode = pipelineModeVal;
        state.pipelineMode = pipelineModeVal;
    }
    if (Object.keys(advancedOverrides).length > 0) {
        try {
            await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(advancedOverrides),
            });
        } catch (e) {
            console.warn("Could not apply advanced config overrides", e);
        }
    }

    const selectedManual = document.getElementById("manual-select").value;

    if (!selectedManual) {
        showStatus("Select a manual before starting.", "error");
        return;
    }

    uploadBtn.disabled = true;
    showStatus(`Loading "${selectedManual}" from library...`, "loading");

    try {
        // Step 1: Load selected manual
        const loadRes = await fetch("/api/load-manual", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ filename: selectedManual }),
        });
        if (!loadRes.ok) {
            const err = await loadRes.json();
            throw new Error(err.detail || "Load failed");
        }
        const loadData = await loadRes.json();
        state.pdfId = loadData.pdf_id;
        state.uploadFilename = loadData.filename;
        state.runId = loadData.run_id || null;

        // Step 2: Request cut plan (scoping)
        showStatus("Analyzing document structure...", "loading");
        const cpRes = await fetch("/cut-plan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pdf_id: state.pdfId, model_name: state.scopingModel, page_offset: state.pageOffset }),
        });
        if (!cpRes.ok) {
            const err = await cpRes.json();
            throw new Error(err.detail || "Cut plan failed");
        }
        const cutPlan = await cpRes.json();
        state.cutPlan = cutPlan;

        // Store asset/document info from scoping
        if (cutPlan.product_info) {
            state.productInfo = cutPlan.product_info;
            state.sourceType = cutPlan.product_info.document_type || "";
            state.sourceTitle = cutPlan.product_info.product_name || "";
        }

        if (cutPlan.skipped) {
            showStatus("Preparing ontology draft before human review...", "loading");
            await startOntologyStage(null);
        } else {
            enterCutPlanScreen(cutPlan);
        }

    } catch (err) {
        showStatus(err.message, "error");
        uploadBtn.disabled = false;
    }
});

function showStatus(msg, type) {
    renderStatus(uploadStatus, msg, type);
}

function showCpStatus(msg, type) {
    renderStatus(cpStatus, msg, type);
}

function showOntologyStatus(msg, type) {
    renderStatus(ontologyStatus, msg, type);
}

function renderStatus(el, msg, type, meta = "") {
    el.hidden = false;
    const baseClass = el.id === "upload-status" ? "status-bar" : "cp-status-inline";
    const normalizedType = type === "error" ? "error" : type === "success" ? "success" : "loading";
    el.className = `${baseClass} ${normalizedType}`;
    const textNode = el.querySelector(".status-text");
    const metaNode = el.querySelector(".status-meta");
    const progress = el.querySelector(".status-progress");

    if (textNode) textNode.textContent = msg;
    if (metaNode) {
        metaNode.hidden = !meta;
        metaNode.textContent = meta || "";
    }
    if (progress) progress.hidden = normalizedType !== "loading";
}

function formatElapsedLabel(startTime) {
    const elapsed = Math.max(0, Math.round((Date.now() - startTime) / 1000));
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function stopStatusActivity(key) {
    const activity = statusActivity[key];
    if (!activity) return;
    if (activity.messageTimer) clearInterval(activity.messageTimer);
    if (activity.clockTimer) clearInterval(activity.clockTimer);
    statusActivity[key] = null;
}

function startStatusActivity(key, el, messages) {
    stopStatusActivity(key);

    const activity = {
        startTime: Date.now(),
        messageIndex: 0,
        messages: [...messages],
        messageTimer: null,
        clockTimer: null,
    };
    statusActivity[key] = activity;

    const syncStatus = () => {
        renderStatus(el, activity.messages[activity.messageIndex], "loading", formatElapsedLabel(activity.startTime));
    };

    syncStatus();
    activity.clockTimer = setInterval(syncStatus, 1000);
    activity.messageTimer = setInterval(() => {
        activity.messageIndex = Math.min(activity.messageIndex + 1, activity.messages.length - 1);
        syncStatus();
    }, 15000);

    return activity;
}

// ─── Cut Plan Screen ───

function enterCutPlanScreen(cutPlan) {
    console.log("[cutplan] enterCutPlanScreen called");

    // 1. Hide upload screen, show cut plan screen
    uploadScreen.hidden = true;
    cutPlanScreen.hidden = false;

    // 2. Populate UI (all synchronous, instant)
    cpDocTitle.textContent = state.uploadFilename;
    state.selectedPages = new Set(cutPlan.pages_to_keep);
    state.cutPlanSections = cutPlan.sections.map(s => ({ ...s }));
    // Show the PDF page where manual page 1 appears (= offset + 1)
    offsetInput.value = cutPlan.page_offset + 1;

    // Display asset/document info if available
    const productInfoBlock = document.getElementById("cp-product-info");
    if (cutPlan.product_info) {
        document.getElementById("cp-product-name").textContent = cutPlan.product_info.product_name || "\u2014";
        document.getElementById("cp-doc-type").textContent = cutPlan.product_info.document_type || "\u2014";
        document.getElementById("cp-language").textContent = cutPlan.product_info.language || "\u2014";
        document.getElementById("cp-page-total").textContent = cutPlan.total_pages;
        productInfoBlock.hidden = false;
    }

    renderTocTable(cutPlan.toc);
    renderSectionCards();
    rebuildSelectedPages();
    updatePageCounter();
    showCpStatus("Loading PDF preview...", "loading");

    console.log("[cutplan] UI populated, scheduling PDF load");

    // 3. Defer PDF loading to a separate macrotask so the browser paints first.
    state.pdfLoaded = false;
    setTimeout(() => {
        console.log("[cutplan] Starting PDF load");
        loadPdfLazy(state.pdfId, cpPdfContainer)
            .then(() => {
                state.pdfLoaded = true;
                cpStatus.hidden = true;
                console.log("[cutplan] PDF loaded");
            })
            .catch((err) => {
                console.error("[cutplan] PDF load failed:", err);
                showCpStatus("PDF preview failed — you can still approve the cut plan", "error");
            });
    }, 50);
}

function renderTocTable(toc) {
    const block = document.getElementById("cp-toc-block");
    const container = document.getElementById("cp-toc-table");
    if (!toc || !toc.entries || toc.entries.length === 0) {
        block.hidden = true;
        return;
    }
    block.hidden = false;

    const offset = getOffsetFromInput();
    let html = '<table class="toc-table"><thead><tr>';
    html += '<th>Title</th><th>Manual Pg</th><th>PDF Pg</th>';
    html += '</tr></thead><tbody>';
    for (const entry of toc.entries) {
        const absPg = entry.manual_page + offset;
        html += `<tr class="toc-row" data-abs-page="${absPg}">`;
        html += `<td>${esc(entry.title)}</td>`;
        html += `<td class="cell-mono">${entry.manual_page}</td>`;
        html += `<td class="cell-mono">${absPg}</td>`;
        html += `</tr>`;
    }
    html += '</tbody></table>';
    container.innerHTML = html;

    // Click row to scroll PDF
    container.querySelectorAll(".toc-row").forEach(row => {
        row.addEventListener("click", () => {
            const pg = parseInt(row.dataset.absPage, 10);
            if (pg > 0) scrollToCpPage(pg);
        });
    });
}

function rebuildSelectedPages() {
    state.selectedPages = new Set();
    for (const section of state.cutPlanSections) {
        for (let i = section.page_range.start; i <= section.page_range.end; i++) {
            state.selectedPages.add(i);
        }
    }
}

function updatePageCounter() {
    const total = state.cutPlan ? state.cutPlan.total_pages : 0;
    const sections = state.cutPlanSections.length;
    cpPageCounter.textContent = `${state.selectedPages.size} / ${total} pages selected (${sections} sections)`;
}

function scrollToCpPage(pageNum) {
    const el = cpPdfContainer.querySelector(`#cp-pdf-page-${pageNum}`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderSectionCards() {
    sectionCards.innerHTML = "";
    const offset = getOffsetFromInput();

    state.cutPlanSections.forEach((section, idx) => {
        const card = document.createElement("div");
        card.className = "section-card";

        card.addEventListener("click", (e) => {
            if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") return;
            scrollToCpPage(section.page_range.start);
        });

        // Header: name + badge + remove
        const header = document.createElement("div");
        header.className = "section-card-header";

        const name = document.createElement("span");
        name.className = "section-card-name";
        name.textContent = section.name;

        const badge = document.createElement("span");
        badge.className = `section-badge ${section.source}`;
        badge.textContent = section.source.toUpperCase();

        const removeBtn = document.createElement("button");
        removeBtn.className = "section-card-remove";
        removeBtn.textContent = "\u00d7";
        removeBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            removeSection(idx);
        });

        header.appendChild(name);
        header.appendChild(badge);
        header.appendChild(removeBtn);
        card.appendChild(header);

        // Page range — edit manual pages, derive absolute
        const range = document.createElement("div");
        range.className = "section-card-range";

        const hasManual = section.manual_page_range != null;
        const manualStart = hasManual ? section.manual_page_range.start : section.page_range.start - offset;
        const manualEnd = hasManual ? section.manual_page_range.end : section.page_range.end - offset;

        range.appendChild(document.createTextNode("Manual pp. "));

        const startInput = document.createElement("input");
        startInput.type = "number";
        startInput.value = manualStart;
        startInput.min = 1;
        startInput.addEventListener("change", () => {
            const newManualStart = Math.max(1, parseInt(startInput.value) || 1);
            startInput.value = newManualStart;
            if (!section.manual_page_range) {
                section.manual_page_range = { start: newManualStart, end: manualEnd };
            } else {
                section.manual_page_range.start = newManualStart;
            }
            section.page_range.start = Math.max(1, Math.min(newManualStart + offset, state.cutPlan.total_pages));
            rebuildSelectedPages();
            updatePageCounter();
            updateAbsDisplay();
        });

        const endInput = document.createElement("input");
        endInput.type = "number";
        endInput.value = manualEnd;
        endInput.min = 1;
        endInput.addEventListener("change", () => {
            const newManualEnd = Math.max(parseInt(startInput.value) || 1, parseInt(endInput.value) || 1);
            endInput.value = newManualEnd;
            if (!section.manual_page_range) {
                section.manual_page_range = { start: manualStart, end: newManualEnd };
            } else {
                section.manual_page_range.end = newManualEnd;
            }
            section.page_range.end = Math.max(section.page_range.start, Math.min(newManualEnd + offset, state.cutPlan.total_pages));
            rebuildSelectedPages();
            updatePageCounter();
            updateAbsDisplay();
        });

        range.appendChild(startInput);
        range.appendChild(document.createTextNode(" \u2013 "));
        range.appendChild(endInput);

        const absSpan = document.createElement("span");
        absSpan.className = "section-card-abs";
        absSpan.textContent = ` | PDF pp. ${section.page_range.start}\u2013${section.page_range.end}`;
        range.appendChild(absSpan);

        function updateAbsDisplay() {
            absSpan.textContent = ` | PDF pp. ${section.page_range.start}\u2013${section.page_range.end}`;
        }

        card.appendChild(range);

        if (section.keyword_matches && section.keyword_matches.length > 0) {
            const kw = document.createElement("div");
            kw.className = "section-card-keywords";
            kw.textContent = `Keywords: ${section.keyword_matches.join(", ")}`;
            card.appendChild(kw);
        }

        if (section.reasoning) {
            const reasoning = document.createElement("div");
            reasoning.className = "section-card-reasoning";
            reasoning.textContent = section.reasoning;
            card.appendChild(reasoning);
        }

        sectionCards.appendChild(card);
    });
}

function removeSection(idx) {
    state.cutPlanSections.splice(idx, 1);
    rebuildSelectedPages();
    renderSectionCards();
    updatePageCounter();
}

// offsetInput shows "PDF page where manual page 1 appears" = offset + 1.
// This helper converts it back to the internal offset (0-based).
function getOffsetFromInput() {
    return Math.max(0, (parseInt(offsetInput.value) || 1) - 1);
}

// Offset live update — recalculate absolute pages from manual pages
offsetInput.addEventListener("input", () => {
    const newOffset = getOffsetFromInput();
    const total = state.cutPlan ? state.cutPlan.total_pages : Infinity;

    for (const section of state.cutPlanSections) {
        if (section.manual_page_range) {
            section.page_range.start = Math.max(1, Math.min(section.manual_page_range.start + newOffset, total));
            section.page_range.end = Math.max(section.page_range.start, Math.min(section.manual_page_range.end + newOffset, total));
        }
    }

    rebuildSelectedPages();
    renderTocTable(state.cutPlan?.toc);
    renderSectionCards();
    updatePageCounter();
});

// Add range
addRangeBtn.addEventListener("click", () => {
    addRangeForm.hidden = false;
    addRangeBtn.hidden = true;
    rangeStart.value = "";
    rangeEnd.value = "";
    rangeName.value = "";
    rangeStart.focus();
});

rangeCancelBtn.addEventListener("click", () => {
    addRangeForm.hidden = true;
    addRangeBtn.hidden = false;
});

rangeConfirmBtn.addEventListener("click", () => {
    const manualStart = parseInt(rangeStart.value);
    const manualEnd = parseInt(rangeEnd.value);
    if (!manualStart || !manualEnd || manualStart > manualEnd || manualStart < 1) return;

    const offset = getOffsetFromInput();
    const total = state.cutPlan ? state.cutPlan.total_pages : Infinity;
    const absStart = Math.max(1, Math.min(manualStart + offset, total));
    const absEnd = Math.max(absStart, Math.min(manualEnd + offset, total));
    const sectionName = rangeName.value.trim() || `User selection (manual pp. ${manualStart}-${manualEnd})`;

    state.cutPlanSections.push({
        name: sectionName,
        page_range: { start: absStart, end: absEnd },
        manual_page_range: { start: manualStart, end: manualEnd },
        source: "user",
        keyword_matches: [],
        reasoning: "Manually added by operator",
    });

    rebuildSelectedPages();
    renderSectionCards();
    updatePageCounter();
    addRangeForm.hidden = true;
    addRangeBtn.hidden = false;
});

// Skip cut plan
cpSkipBtn.addEventListener("click", async () => {
    cpSkipBtn.disabled = true;
    cpApproveBtn.disabled = true;
    try {
        showCpStatus("Preparing ontology draft before human review...", "loading");
        await startOntologyStage(null);
    } catch (err) {
        showCpStatus(err.message, "error");
    } finally {
        // Always re-enable: if startOntologyStage advanced the screen, the
        // buttons are no longer visible anyway. If it failed, the operator
        // must be able to retry without a stale disabled state.
        cpSkipBtn.disabled = false;
        cpApproveBtn.disabled = false;
    }
});

// Approve cut plan
cpApproveBtn.addEventListener("click", async () => {
    if (state.selectedPages.size === 0) {
        showCpStatus("Select at least one page.", "error");
        return;
    }

    cpApproveBtn.disabled = true;
    cpSkipBtn.disabled = true;
    showCpStatus("Approving cut plan...", "loading");

    try {
        const pagesToKeep = Array.from(state.selectedPages).sort((a, b) => a - b);

        const approveRes = await fetch("/cut-plan/approve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pdf_id: state.pdfId,
                pages_to_keep: pagesToKeep,
                page_offset: getOffsetFromInput(),
                sections: state.cutPlanSections.map(s => ({
                    name: s.name,
                    page_range: s.page_range,
                    source: s.source || "",
                })),
            }),
        });
        if (!approveRes.ok) {
            const err = await approveRes.json();
            throw new Error(err.detail || "Approval failed");
        }

        showCpStatus("Preparing ontology draft before human review...", "loading");
        await startOntologyStage(pagesToKeep);

    } catch (err) {
        showCpStatus(err.message, "error");
    } finally {
        cpApproveBtn.disabled = false;
        cpSkipBtn.disabled = false;
    }
});

// ─── Ontology pre-review ───

function movePdfPages(fromContainer, toContainer, fromPrefix, toPrefix) {
    if (!fromContainer || !toContainer || fromContainer.children.length === 0) return;
    while (fromContainer.firstChild) {
        const child = fromContainer.firstChild;
        if (child.id && child.id.startsWith(fromPrefix)) {
            child.id = child.id.replace(fromPrefix, toPrefix);
        }
        toContainer.appendChild(child);
    }
}

async function startOntologyStage(pagesToKeep) {
    if (!state.sourceTitle) state.sourceTitle = state.uploadFilename;
    if (!state.sourceType) state.sourceType = state.productInfo?.document_type || "manual";
    state.ontologyPagesToKeep = pagesToKeep;
    state.extractionInProgress = false;
    state.tripletsExtracted = false;
    state.triplets = [];
    enterOntologyScreen();
    await runOntologyDraft(pagesToKeep);
}

function enterOntologyScreen() {
    uploadScreen.hidden = true;
    cutPlanScreen.hidden = true;
    mainLayout.hidden = true;
    ontologyScreen.hidden = false;
    ontologyDocTitle.textContent = state.sourceTitle || state.uploadFilename;
    ontologySummaryCard.innerHTML = "";
    ontologyIssues.innerHTML = "";
    ontologyFields.innerHTML = "";
    ontologyIssuesBlock.hidden = true;
    ontologyFieldsBlock.hidden = true;
    graphIssuesBlock.hidden = true;
    suggestedRelationsBlock.hidden = true;
    suggestedRelationsList.innerHTML = "";
    suggestedRelationsBulk.hidden = true;

    // Multi-agent observability: start polling + reveal audit button in multi_agent mode
    if (state.pipelineMode === "multi_agent" && state.runId) {
        if (auditDrawerToggle) auditDrawerToggle.hidden = false;
        startStatusPolling();
    } else {
        if (auditDrawerToggle) auditDrawerToggle.hidden = true;
        if (phaseStrip) {
            phaseStrip.classList.add("is-hidden");
            phaseStrip.innerHTML = "";
        }
        stopStatusPolling();
    }

    if (cpPdfContainer.children.length > 0 && ontologyPdfContainer.children.length === 0) {
        movePdfPages(cpPdfContainer, ontologyPdfContainer, "cp-pdf-page-", "ontology-pdf-page-");
        setupPdfObserver(ontologyPdfContainer);
        state.pdfLoaded = true;
    } else if (!state.pdfLoaded) {
        showOntologyStatus("Loading PDF preview...", "loading");
        loadPdfLazy(state.pdfId, ontologyPdfContainer)
            .then(() => {
                state.pdfLoaded = true;
                ontologyStatus.hidden = true;
            })
            .catch((err) => {
                showOntologyStatus(`PDF preview failed: ${err.message}`, "error");
            });
    }
}

function renderOntologyDraft(result) {
    state.ontologyDraft = result;
    const hasSchemaIssues = result.schema_issues.length > 0;
    const hasHumanInputs = result.human_required_fields.length > 0;
    const hasSuggestions = (result.suggested_relations || []).length > 0;
    const extractionRunning = state.extractionInProgress;

    // Node count summary — clarify these are ontology nodes, NOT diagnostic triplets
    const totalNodes = Object.values(result.ontology.nodes || {}).reduce((s, arr) => s + arr.length, 0);
    const nodeCounts = Object.entries(result.ontology.nodes || {})
        .filter(([, items]) => items.length > 0)
        .map(([name, items]) => `${name}: ${items.length}`)
        .join(" · ");

    const retryBadge = result.retry_count > 0
        ? ` <span class="badge-count" title="Reflective loop retries">${result.retry_count} retr${result.retry_count === 1 ? "y" : "ies"}</span>`
        : "";

    // Status label — map internal codes to human-readable
    const statusLabels = {
        "ready": "Ready",
        "needs_human": "Needs input",
        "needs_human_review": "Needs review",
        "blocked": "Schema issues",
    };
    const statusLabel = statusLabels[result.status] || result.status;

    ontologySummaryCard.innerHTML = `
        <div class="ontology-summary-grid">
            <div class="ontology-summary-item">
                <div class="ontology-summary-label">Status</div>
                <div class="ontology-summary-value">${esc(statusLabel)}${retryBadge}</div>
            </div>
            <div class="ontology-summary-item">
                <div class="ontology-summary-label">Ontology nodes</div>
                <div class="ontology-summary-value">${totalNodes}</div>
            </div>
            <div class="ontology-summary-item">
                <div class="ontology-summary-label">Relations</div>
                <div class="ontology-summary-value">${result.ontology.relations.length}</div>
            </div>
            <div class="ontology-summary-item">
                <div class="ontology-summary-label">Fields to fill</div>
                <div class="ontology-summary-value">${result.human_required_fields.length}</div>
            </div>
        </div>
        ${nodeCounts ? `<div class="ontology-field-reason" style="margin-top:0.55rem">${esc(nodeCounts)}</div>` : ""}
        <div class="ontology-field-reason" style="margin-top:0.3rem;color:var(--text-dim);font-style:italic;">
            ${extractionRunning
                ? "Step 2 of 2 in progress. Diagnostic triplets are already being extracted."
                : "Step 1 of 2 complete. Diagnostic triplets will be extracted in step 2 after you press the button below."}
        </div>
    `;

    // Confidence strip lives in the Advanced / Research panel — hidden from the
    // operator-facing core view, surfaced only when the strip has content.
    const confidenceStripHtml = renderConfidenceStrip(result.confidence_report);
    const confidenceBlock = document.getElementById("ontology-confidence-block");
    const confidenceStripContainer = document.getElementById("ontology-confidence-strip");
    if (confidenceBlock && confidenceStripContainer) {
        if (confidenceStripHtml) {
            confidenceStripContainer.innerHTML = confidenceStripHtml;
            confidenceBlock.hidden = false;
        } else {
            confidenceStripContainer.innerHTML = "";
            confidenceBlock.hidden = true;
        }
    }

    // ─── Guidance: single, clear next-action message ───
    let guidanceHtml = "";
    if (extractionRunning) {
        guidanceHtml = `
            <div class="ontology-guidance-line optional">
                <strong>Extraction in progress.</strong> The LLM is already processing the next step. Human validation will open automatically when ready.
            </div>
        `;
    } else if (hasHumanInputs) {
        guidanceHtml = `
            <div class="ontology-guidance-line actionable">
                Fill in the <strong>${result.human_required_fields.length} required field${result.human_required_fields.length > 1 ? "s" : ""}</strong> below, then press <strong>Apply &amp; Continue</strong>.
                All fields must be filled before you can proceed.
            </div>
        `;
    } else if (hasSchemaIssues) {
        guidanceHtml = `
            <div class="ontology-guidance-line blocking">
                The ontology has <strong>${result.schema_issues.length} schema issue${result.schema_issues.length > 1 ? "s" : ""}</strong> that cannot be fixed here.
                You can still continue — triplet extraction will proceed, but some ontology context may be incomplete.
            </div>
        `;
    } else {
        guidanceHtml = `
            <div class="ontology-guidance-line optional">
                <strong>Ready.</strong> No action required &mdash; press <strong>Extract Triplets &amp; Start Validation</strong> to continue.
                ${hasSuggestions ? `<br><span class="guidance-secondary">${result.suggested_relations.length} optional graph suggestion${result.suggested_relations.length > 1 ? "s are" : " is"} available in the Advanced / Research view if you want to inspect them first.</span>` : ""}
            </div>
        `;
    }
    ontologyGuidance.innerHTML = guidanceHtml;

    // ─── Required human input fields — always visible if present, no collapsing ───
    ontologyFieldsBlock.hidden = !hasHumanInputs;
    if (hasHumanInputs) {
        ontologyFields.innerHTML = `<div class="ontology-list">${result.human_required_fields.map(field => `
            <div class="ontology-field-card">
                <label>${esc(field.property_name)}${field.reason ? ` <span class="ontology-field-reason-inline">(${esc(field.reason)})</span>` : ""}</label>
                <input
                    type="text"
                    data-ontology-field="${esc(field.field_key)}"
                    value="${esc(field.suggested_value || "")}"
                    placeholder="${esc(field.prompt || field.property_name)}"
                >
            </div>
        `).join("")}</div>`;
        ontologyContinueBtn.textContent = "Apply & Continue";
    } else {
        ontologyFields.innerHTML = "";
        ontologyContinueBtn.textContent = "Extract Triplets & Start Validation";
    }
    syncOntologyActionButtons();

    // ─── Automatic checks — collapsed by default, expandable ───
    const allIssues = [...result.semantic_issues, ...result.schema_issues];
    ontologyIssuesBlock.hidden = allIssues.length === 0;
    if (allIssues.length > 0) {
        const errorCount = allIssues.filter(i => i.severity === "error").length;
        const warnCount = allIssues.length - errorCount;
        const summary = [errorCount > 0 ? `${errorCount} error${errorCount > 1 ? "s" : ""}` : null, warnCount > 0 ? `${warnCount} warning${warnCount > 1 ? "s" : ""}` : null].filter(Boolean).join(", ");
        const issueListId = "ontology-issues-detail";
        ontologyIssues.innerHTML = `
            <button class="ontology-issues-toggle" aria-expanded="false" aria-controls="${issueListId}">
                Show details (${summary})
            </button>
            <div id="${issueListId}" class="ontology-list" hidden>${allIssues.map(issue => `
                <div class="ontology-issue-card ${issue.severity === "error" ? "error" : "warning"}">
                    <div class="ontology-issue-head">
                        <span class="ontology-issue-code">${esc(issue.code || "issue")}</span>
                        <span class="ontology-issue-severity">${esc(issue.severity || "warning")}</span>
                    </div>
                    <div class="ontology-issue-body">${esc(issue.message || "")}</div>
                    ${issue.fix_hint ? `<div class="ontology-field-reason">${esc(issue.fix_hint)}</div>` : ""}
                </div>
            `).join("")}</div>
        `;
        // Toggle handler
        const toggleBtn = ontologyIssues.querySelector(".ontology-issues-toggle");
        const detailDiv = ontologyIssues.querySelector(`#${issueListId}`);
        toggleBtn.addEventListener("click", () => {
            const expanded = toggleBtn.getAttribute("aria-expanded") === "true";
            toggleBtn.setAttribute("aria-expanded", String(!expanded));
            detailDiv.hidden = expanded;
            toggleBtn.textContent = expanded ? `Show details (${summary})` : `Hide details`;
        });
    } else {
        ontologyIssues.innerHTML = "";
    }

    // ─── Graph issues — collapsed, secondary info ───
    const graphIssues = result.graph_issues || [];
    graphIssuesBlock.hidden = graphIssues.length === 0;
    if (graphIssues.length > 0) {
        graphIssuesList.innerHTML = graphIssues.map(issue => `
            <div class="graph-issue-card ${esc(issue.issue_type)}">
                <div class="graph-issue-type">${esc(issue.issue_type)}</div>
                <div class="graph-issue-desc">${esc(issue.description)}</div>
                ${issue.suggested_fix ? `<div class="graph-issue-fix">${esc(issue.suggested_fix)}</div>` : ""}
            </div>
        `).join("");
    } else {
        graphIssuesList.innerHTML = "";
    }

    // ─── Suggested relations ───
    renderSuggestedRelations(result.suggested_relations || []);

    // ─── New agentic panels: confidence-aware node list + escalations ───
    state.escalations = synthesizeEscalations(result);
    renderOntologyNodes(result);
    renderEscalations(state.escalations, graphIssues);
}

function syncOntologyActionButtons() {
    const hasHumanInputs = state.ontologyDraft?.human_required_fields?.length > 0;
    const extractionRunning = state.extractionInProgress;

    ontologyContinueBtn.hidden = extractionRunning;
    ontologyContinueBtn.disabled = extractionRunning;
    ontologyRerunBtn.hidden = extractionRunning || !hasHumanInputs;
    ontologyRerunBtn.disabled = extractionRunning;
}

function renderSuggestedRelations(suggestions) {
    if (!suggestions || suggestions.length === 0) {
        suggestedRelationsBlock.hidden = true;
        suggestedRelationsList.innerHTML = "";
        suggestedRelationsBulk.hidden = true;
        suggestedRelationsCount.textContent = "";
        return;
    }

    suggestedRelationsBlock.hidden = false;
    suggestedRelationsCount.textContent = suggestions.length;
    suggestedRelationsBulk.hidden = false;

    suggestedRelationsList.innerHTML = "";
    suggestions.forEach((s, idx) => {
        const card = document.createElement("div");
        card.className = "suggestion-card";
        card.dataset.idx = idx;
        card.dataset.decision = "pending"; // pending | accepted | rejected

        const pct = Math.round((s.confidence || 0) * 100);
        card.innerHTML = `
            <div class="suggestion-card-head">
                <span class="suggestion-rel-name">${esc(s.relation_name)}</span>
                <span class="suggestion-from">${esc(s.from_label || s.from_id)}</span>
                <span class="suggestion-arrow">→</span>
                <span class="suggestion-to">${esc(s.to_label || s.to_id)}</span>
                <span class="suggestion-confidence">${pct}% confidence</span>
            </div>
            ${s.rationale ? `<div class="suggestion-rationale">${esc(s.rationale)}</div>` : ""}
            <div class="suggestion-actions">
                <button class="btn-primary btn-sm" data-action="accept" data-idx="${idx}">Accept</button>
                <button class="btn-secondary btn-sm" data-action="reject" data-idx="${idx}">Reject</button>
            </div>
        `;
        suggestedRelationsList.appendChild(card);
    });

    suggestedRelationsList.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-action]");
        if (!btn) return;
        const idx = parseInt(btn.dataset.idx, 10);
        const action = btn.dataset.action;
        const card = suggestedRelationsList.querySelector(`.suggestion-card[data-idx="${idx}"]`);
        if (!card) return;
        card.dataset.decision = action === "accept" ? "accepted" : "rejected";
        card.classList.toggle("accepted", action === "accept");
        card.classList.toggle("rejected", action === "reject");
    }, { once: false });
}

// ═══════════════════════════════════════════════════════════
// CONFIDENCE-AWARE ONTOLOGY REVIEW (Block 2)
// ═══════════════════════════════════════════════════════════

function bucketForScore(score, thetaHigh, thetaLow, autoRejectEnabled) {
    if (score == null || Number.isNaN(score)) return "mid";
    if (score >= thetaHigh) return "high";
    if (autoRejectEnabled && score < thetaLow) return "low";
    return "mid";
}

function classificationToBucket(classification) {
    if (classification === "auto_approve") return "high";
    if (classification === "auto_reject") return "low";
    return "mid"; // human_review
}

function renderConfidenceStrip(report) {
    if (!report || !report.entries || report.entries.length === 0) return "";
    const counts = report.counts || {};
    const high = counts.auto_approve || 0;
    const mid  = counts.human_review || 0;
    const low  = counts.auto_reject || 0;
    const total = high + mid + low;
    if (total === 0) return "";
    const pctHigh = Math.round((high / total) * 100);
    const thetaHigh = typeof report.theta_high === "number" ? report.theta_high.toFixed(2) : "—";
    const thetaLow = typeof report.theta_low === "number" ? report.theta_low.toFixed(2) : "—";
    return `
        <div class="confidence-strip">
            <span class="confidence-strip-label">Confidence</span>
            <span class="confidence-pill high"><span class="dot"></span>${high} auto-approve</span>
            <span class="confidence-pill mid"><span class="dot"></span>${mid} human review</span>
            ${report.auto_reject_enabled ? `<span class="confidence-pill low"><span class="dot"></span>${low} auto-reject</span>` : ""}
            <span class="confidence-threshold-note">${pctHigh}% ≥ θ<sub>high</sub>=${thetaHigh}${report.auto_reject_enabled ? ` · θ<sub>low</sub>=${thetaLow}` : ""}</span>
        </div>
    `;
}

// Flatten ontology.nodes (keyed by type, each value is a list of dicts) into a
// flat list of entries indexable by `${type}::${id}`.
function flattenOntologyNodes(ontology) {
    const out = [];
    const nodesByType = ontology?.nodes || {};
    for (const [nodeType, items] of Object.entries(nodesByType)) {
        for (const item of (items || [])) {
            const id = item.id || item.node_id || "";
            if (!id) continue;
            // Try a few common label fields the backend emits
            const label =
                item.name ||
                item.label ||
                item.description ||
                item.title ||
                "";
            out.push({ node_type: nodeType, node_id: id, label, props: item });
        }
    }
    return out;
}

function indexConfidenceByKey(report) {
    const idx = {};
    for (const entry of (report?.entries || [])) {
        idx[`${entry.node_type}::${entry.node_id}`] = entry;
    }
    return idx;
}

function signalChipClass(value) {
    if (value == null || Number.isNaN(value)) return "sig-mid";
    if (value >= 0.8) return "sig-high";
    if (value < 0.4) return "sig-low";
    return "sig-mid";
}

function renderOntologyNodes(result) {
    const report = result?.confidence_report;
    if (!report || !report.entries || report.entries.length === 0) {
        ontologyNodesBlock.hidden = true;
        ontologyNodesList.innerHTML = "";
        ontologyNodesCount.textContent = "";
        return;
    }

    ontologyNodesBlock.hidden = false;

    // Join ontology nodes with confidence entries
    const flat = flattenOntologyNodes(result.ontology);
    const confByKey = indexConfidenceByKey(report);

    // Any confidence entries that aren't already in flat (rare) get added as label-less rows
    const seen = new Set(flat.map(n => `${n.node_type}::${n.node_id}`));
    for (const entry of report.entries) {
        const key = `${entry.node_type}::${entry.node_id}`;
        if (!seen.has(key)) {
            flat.push({ node_type: entry.node_type, node_id: entry.node_id, label: "", props: {} });
        }
    }

    const enriched = flat.map(n => {
        const key = `${n.node_type}::${n.node_id}`;
        const conf = confByKey[key] || null;
        return { ...n, key, conf };
    }).filter(n => n.conf); // only show nodes that the backend scored

    // Bucket by classification
    const buckets = { high: [], mid: [], low: [] };
    for (const n of enriched) {
        buckets[classificationToBucket(n.conf.classification)].push(n);
    }

    // Sort within each bucket
    const sortMode = state.confidenceSort;
    const sorter = (a, b) => {
        if (sortMode === "type") {
            const byType = a.node_type.localeCompare(b.node_type);
            if (byType !== 0) return byType;
        }
        return (a.conf.score ?? 0) - (b.conf.score ?? 0);
    };
    buckets.mid.sort(sorter);
    buckets.low.sort(sorter);
    buckets.high.sort(sorter);

    ontologyNodesCount.textContent = enriched.length;

    // Render in order: human_review (most urgent) → auto_reject (if enabled) → auto_approve (collapsed)
    const groups = [
        { bucket: "mid", title: "Human review",  items: buckets.mid, collapsed: false },
    ];
    if (report.auto_reject_enabled && buckets.low.length > 0) {
        groups.push({ bucket: "low", title: "Auto-reject", items: buckets.low, collapsed: false });
    }
    if (buckets.high.length > 0) {
        groups.push({
            bucket: "high",
            title: "Auto-approve",
            items: buckets.high,
            collapsed: !state.showAutoApproved,
        });
    }

    ontologyNodesList.innerHTML = groups.map(g => {
        if (g.items.length === 0) return "";
        const cards = g.items.map(n => renderNodeCard(n, g.bucket)).join("");
        return `
            <details class="ontology-nodes-group" data-bucket="${g.bucket}" ${g.collapsed ? "" : "open"}>
                <summary class="ontology-nodes-group-head">
                    ${esc(g.title)}
                    <span class="ontology-nodes-group-count">${g.items.length}</span>
                </summary>
                <div class="ontology-nodes-group-body">${cards}</div>
            </details>
        `;
    }).join("");
}

function renderNodeCard(node, bucket) {
    const conf = node.conf;
    const decisionKey = node.key;
    const decision = state.nodeDecisions[decisionKey] || null;
    const scoreFixed = (conf.score ?? 0).toFixed(2);

    const signalsHtml = Object.entries(conf.signals || {}).map(([name, val]) => {
        const v = Number(val).toFixed(2);
        return `<span class="signal-chip ${signalChipClass(val)}">${esc(name)} ${v}</span>`;
    }).join(" ");

    const penaltiesHtml = Object.entries(conf.penalties || {}).map(([name, val]) => {
        const v = Number(val).toFixed(2);
        return `<span class="signal-chip">−${v} ${esc(name)}</span>`;
    }).join(" ");

    const reasonsText = (conf.reasons || []).join(" · ");

    const decisionBadge = decision
        ? `<span class="node-decision-badge ${decision}">${decision}</span>`
        : "";

    return `
        <div class="node-card bucket-${bucket} ${decision ? `decision-${decision}` : ""}" data-node-key="${esc(decisionKey)}">
            <div class="node-card-head">
                <span class="node-type-pill">${esc(node.node_type)}</span>
                <span class="node-id">${esc(node.node_id)}</span>
                <span class="node-score"><span class="dot"></span>${scoreFixed}</span>
                ${decisionBadge}
            </div>
            ${node.label ? `<div class="node-label-line">${esc(node.label)}</div>` : ""}
            ${signalsHtml ? `<div class="node-signals"><span class="node-signals-label">Signals</span><span>${signalsHtml}</span></div>` : ""}
            ${reasonsText ? `<div class="node-reasons"><span class="node-reasons-label">Reasons</span><span>${esc(reasonsText)}</span></div>` : ""}
            ${penaltiesHtml ? `<div class="node-penalties"><span class="node-penalties-label">Penalties</span><span>${penaltiesHtml}</span></div>` : ""}
            <div class="node-actions">
                <button class="btn-success btn-sm" data-node-action="approved" data-node-key="${esc(decisionKey)}">Approve</button>
                <button class="btn-danger  btn-sm" data-node-action="rejected" data-node-key="${esc(decisionKey)}">Reject</button>
                <button class="btn-secondary btn-sm" data-node-action="skipped" data-node-key="${esc(decisionKey)}">Skip</button>
            </div>
        </div>
    `;
}

// Wire ontology-nodes controls ONCE at module load; delegated click handler.
if (ontologyNodesList) {
    ontologyNodesList.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-node-action]");
        if (!btn) return;
        const action = btn.dataset.nodeAction;
        const key = btn.dataset.nodeKey;
        if (!key) return;
        // Toggle: clicking the same action clears it
        if (state.nodeDecisions[key] === action) {
            delete state.nodeDecisions[key];
        } else {
            state.nodeDecisions[key] = action;
        }
        if (state.ontologyDraft) renderOntologyNodes(state.ontologyDraft);
    });
}
if (ontologyNodesSort) {
    ontologyNodesSort.addEventListener("change", () => {
        state.confidenceSort = ontologyNodesSort.value;
        if (state.ontologyDraft) renderOntologyNodes(state.ontologyDraft);
    });
}
if (showAutoApprovedCheckbox) {
    showAutoApprovedCheckbox.addEventListener("change", () => {
        state.showAutoApproved = showAutoApprovedCheckbox.checked;
        if (state.ontologyDraft) renderOntologyNodes(state.ontologyDraft);
    });
}
if (bulkApproveBtn) {
    bulkApproveBtn.addEventListener("click", () => {
        const report = state.ontologyDraft?.confidence_report;
        if (!report) return;
        for (const entry of (report.entries || [])) {
            if (entry.classification === "auto_approve") {
                state.nodeDecisions[`${entry.node_type}::${entry.node_id}`] = "approved";
            }
        }
        renderOntologyNodes(state.ontologyDraft);
    });
}

// ═══════════════════════════════════════════════════════════
// MULTI-AGENT OBSERVABILITY (Block 3)
// ═══════════════════════════════════════════════════════════

// Operator-facing display steps fold the 11 backend GraphPhase values into 6.
const DISPLAY_PHASES = [
    { key: "scoping",        label: "Scoping",        backend: ["scoping"] },
    { key: "ontology_draft", label: "Ontology Draft", backend: ["ontology_draft"] },
    { key: "extraction",     label: "Extraction",     backend: ["extraction"] },
    { key: "validation",     label: "Validation",     backend: ["validation", "coverage", "grounding", "conflict_resolution", "refinement"] },
    { key: "export",         label: "Export",         backend: ["export"] },
    { key: "done",           label: "Done",           backend: ["completed"] },
];

function displayKeyForBackendPhase(phase) {
    if (!phase) return null;
    for (const dp of DISPLAY_PHASES) {
        if (dp.backend.includes(phase)) return dp.key;
    }
    return null;
}

function renderPhaseStrip(statusPayload) {
    if (!phaseStrip) return;
    if (state.pipelineMode !== "multi_agent" || !statusPayload) {
        phaseStrip.classList.add("is-hidden");
        phaseStrip.innerHTML = "";
        return;
    }

    const currentBackend = statusPayload.current_phase || "loaded";
    const history = Array.isArray(statusPayload.phase_history) ? statusPayload.phase_history : [];
    const visitedBackend = new Set(history.map(h => h.phase).filter(Boolean));
    visitedBackend.add(currentBackend);

    const currentDisplayKey = displayKeyForBackendPhase(currentBackend);

    // Determine done / active / pending per display phase.
    // "done" = all backend phases visited AND the display step is earlier than current.
    // "active" = current step.
    // "pending" = everything after.
    const currentIdx = DISPLAY_PHASES.findIndex(d => d.key === currentDisplayKey);

    const stepsHtml = DISPLAY_PHASES.map((dp, idx) => {
        let cls = "pending";
        let stateLabel = "pending";
        if (idx < currentIdx) { cls = "done"; stateLabel = "done"; }
        else if (idx === currentIdx) {
            if (statusPayload.run_status === "completed" && dp.key === "done") { cls = "done"; stateLabel = "done"; }
            else { cls = "active"; stateLabel = "active"; }
        }
        // If current backend is COMPLETED, mark all as done.
        if (currentBackend === "completed") { cls = "done"; stateLabel = "done"; }

        return `
            <div class="phase-step ${cls}">
                <div class="phase-step-dot"></div>
                <div class="phase-step-label">
                    <span class="phase-step-name">${esc(dp.label)}</span>
                    <span class="phase-step-state">${stateLabel}</span>
                </div>
            </div>
        `;
    }).join("");

    // Progress percent + token count in the meta slot
    const progress = typeof statusPayload.progress_percent === "number" ? `${statusPayload.progress_percent}%` : "—";
    const totalTokens = sumTokenLedger(statusPayload.token_ledger);
    const metaHtml = `
        <div class="phase-strip-meta">
            <span><strong>progress</strong> ${progress}</span>
            <span><strong>tokens</strong> ${formatTokenCount(totalTokens)}</span>
            <span><strong>run</strong> ${esc(statusPayload.run_status || "—")}</span>
        </div>
    `;

    phaseStrip.innerHTML = stepsHtml + metaHtml;
    phaseStrip.classList.remove("is-hidden");
}

function sumTokenLedger(ledger) {
    if (!ledger) return 0;
    let total = 0;
    if (Array.isArray(ledger)) {
        for (const row of ledger) total += Number(row.tokens || row.tokens_used || 0);
    } else if (typeof ledger === "object") {
        for (const v of Object.values(ledger)) {
            if (typeof v === "number") total += v;
            else if (v && typeof v === "object") total += Number(v.tokens || v.tokens_used || 0);
        }
    }
    return total;
}

function formatTokenCount(n) {
    if (!n) return "0";
    if (n < 1000) return String(n);
    if (n < 1e6) return `${(n / 1000).toFixed(1)}k`;
    return `${(n / 1e6).toFixed(2)}M`;
}

// ─── Status polling ───
function stopStatusPolling() {
    if (state.statusPollTimer) {
        clearInterval(state.statusPollTimer);
        state.statusPollTimer = null;
    }
}

async function pollSupervisorStatusOnce() {
    if (!state.runId || state.pipelineMode !== "multi_agent") return;
    try {
        const payload = await api.multiAgentStatus(state.runId);
        state.supervisorStatus = payload;
        renderPhaseStrip(payload);
        // Show audit button now that we have a run
        if (auditDrawerToggle) auditDrawerToggle.hidden = false;
        if (payload.run_status === "completed" || payload.run_status === "awaiting_operator") {
            stopStatusPolling();
        }
    } catch (e) {
        console.warn("multi-agent status poll failed:", e.message);
    }
}

function startStatusPolling() {
    if (!state.runId || state.pipelineMode !== "multi_agent") return;
    stopStatusPolling();
    // Fetch once immediately so the phase strip appears without a 2s delay
    pollSupervisorStatusOnce();
    state.statusPollTimer = setInterval(pollSupervisorStatusOnce, 2000);
}

// ─── Audit drawer ───
async function openAuditDrawer() {
    if (!auditDrawer || !state.runId || state.pipelineMode !== "multi_agent") return;
    auditDrawer.classList.add("open");
    auditDrawer.setAttribute("aria-hidden", "false");
    if (auditDrawerToggle) auditDrawerToggle.setAttribute("aria-expanded", "true");
    try {
        const payload = await api.multiAgentAudit(state.runId);
        state.supervisorAudit = payload;
        renderAuditDrawer(payload);
    } catch (e) {
        console.warn("multi-agent audit fetch failed:", e.message);
        if (auditTokenLedger) auditTokenLedger.innerHTML = `<div class="node-label-line" style="color:var(--conf-low)">Failed to load audit trail: ${esc(e.message)}</div>`;
    }
}

function closeAuditDrawer() {
    if (!auditDrawer) return;
    auditDrawer.classList.remove("open");
    auditDrawer.setAttribute("aria-hidden", "true");
    if (auditDrawerToggle) auditDrawerToggle.setAttribute("aria-expanded", "false");
}

function renderAuditDrawer(audit) {
    if (!audit) return;

    // Token ledger
    const ledger = audit.token_ledger || {};
    const ledgerRows = [];
    if (Array.isArray(ledger)) {
        for (const row of ledger) {
            ledgerRows.push([row.agent || row.name || "—", Number(row.tokens || 0), Number(row.llm_calls || 0)]);
        }
    } else if (typeof ledger === "object") {
        for (const [agent, info] of Object.entries(ledger)) {
            if (typeof info === "number") ledgerRows.push([agent, info, 0]);
            else if (info && typeof info === "object") ledgerRows.push([agent, Number(info.tokens || info.tokens_used || 0), Number(info.llm_calls || info.calls || 0)]);
        }
    }
    auditTokenLedger.innerHTML = ledgerRows.length
        ? ledgerRows.map(([agent, tokens, calls]) =>
            `<div class="audit-token-row"><span class="agent">${esc(agent)}</span><span class="val">${formatTokenCount(tokens)} tok · ${calls} calls</span></div>`
        ).join("")
        : `<div class="node-label-line">No token usage recorded yet.</div>`;

    // Phase history
    const history = Array.isArray(audit.phase_history) ? audit.phase_history : [];
    auditPhaseHistory.innerHTML = history.length
        ? history.map(h => `
            <li class="audit-phase-item">
                <div class="phase-title">
                    <span>${esc(h.phase || "—")}</span>
                    <span>→</span>
                    <span>${esc(h.agent || "—")}</span>
                    <span class="phase-timestamp">${esc(shortTime(h.timestamp))}</span>
                </div>
                ${h.decision ? `<div class="phase-detail">${esc(h.decision)}</div>` : ""}
                <div class="phase-meta">
                    <span>tokens ${formatTokenCount(Number(h.tokens_used || 0))}</span>
                    <span>llm ${Number(h.llm_calls || 0)}</span>
                </div>
            </li>
        `).join("")
        : `<li class="audit-phase-item"><div class="phase-detail">No phase history recorded yet.</div></li>`;

    // Supervisor decisions
    const supLog = Array.isArray(audit.supervisor_log) ? audit.supervisor_log : [];
    auditSupervisorLog.innerHTML = supLog.length
        ? supLog.map(s => `
            <li class="audit-sup-item">
                <div class="sup-title">
                    <span>${esc(s.phase_from || "—")}</span>
                    <span>→</span>
                    <span>${esc(s.phase_to || "—")}</span>
                    <span class="sup-timestamp">${esc(shortTime(s.timestamp))}</span>
                </div>
                ${s.reasoning ? `<div class="sup-detail">${esc(s.reasoning)}</div>` : ""}
                <div class="sup-meta">
                    <span>${esc(s.decision_type || "deterministic")}</span>
                    ${s.next_agent ? `<span>→ ${esc(s.next_agent)}</span>` : ""}
                    ${s.state_snapshot_hash ? `<span class="sup-hash-chip">${esc(s.state_snapshot_hash)}</span>` : ""}
                </div>
            </li>
        `).join("")
        : `<li class="audit-sup-item"><div class="sup-detail">No supervisor decisions recorded yet.</div></li>`;

    if (auditEntriesCount) auditEntriesCount.textContent = String(history.length + supLog.length);
}

function shortTime(iso) {
    if (!iso) return "";
    try {
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return String(iso);
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch { return String(iso); }
}

if (auditDrawerToggle) {
    auditDrawerToggle.addEventListener("click", () => {
        if (auditDrawer?.classList.contains("open")) closeAuditDrawer();
        else openAuditDrawer();
    });
}
if (auditDrawerClose) auditDrawerClose.addEventListener("click", closeAuditDrawer);

// ═══════════════════════════════════════════════════════════
// ESCALATION CARDS (Block 4) — contract-first synthesizer
// ═══════════════════════════════════════════════════════════

function synthesizeEscalations(result) {
    if (!result) return [];
    const escalations = [];
    const report = result.confidence_report;
    const thetaHigh = report?.theta_high ?? 0.8;
    const thetaLow  = report?.theta_low ?? 0.45;

    // 1) Low-confidence nodes → node-level escalations
    //    Trigger on any human_review node comfortably below θ_high.
    const suggestedByNode = {};
    for (const sr of (result.suggested_relations || [])) {
        const fkey = `${sr.from_type}::${sr.from_id}`;
        const tkey = `${sr.to_type}::${sr.to_id}`;
        (suggestedByNode[fkey] = suggestedByNode[fkey] || []).push(sr);
        (suggestedByNode[tkey] = suggestedByNode[tkey] || []).push(sr);
    }

    for (const entry of (report?.entries || [])) {
        if (entry.classification !== "human_review") continue;
        if (entry.score >= thetaHigh - 0.10) continue; // leave borderline scores out of escalation UI
        const severity = entry.score < thetaLow ? "blocking" : "warning";
        const topReason = (entry.reasons && entry.reasons[0]) || "Low confidence score";
        const key = `${entry.node_type}::${entry.node_id}`;
        const suggested = (suggestedByNode[key] || [])[0] || null;
        escalations.push({
            escalation_id: `esc-${entry.node_type.toLowerCase()}-${entry.node_id}`,
            phase: "ontology_draft",
            agent: "GroundingAgent",
            severity,
            issue: `${entry.node_type} ${entry.node_id} has low confidence (${entry.score.toFixed(2)}). ${topReason}`,
            options: ["approve_as_is", "reject_node", "provide_correction", "skip"],
            context: {
                node_type: entry.node_type,
                node_id: entry.node_id,
                score: entry.score,
                suggested_relation: suggested,
            },
        });
    }

    // 2) Critical graph structure issues → graph-level escalations
    for (const gi of (result.graph_issues || [])) {
        if (!["broken_chain", "cycle"].includes(gi.issue_type)) continue;
        escalations.push({
            escalation_id: `esc-graph-${gi.issue_type}-${(escalations.length + 1).toString().padStart(3, "0")}`,
            phase: "ontology_draft",
            agent: "graph_reasoning",
            severity: "blocking",
            issue: gi.description || `Graph ${gi.issue_type}`,
            options: ["approve_as_is", "skip"],
            context: {
                issue_code: gi.issue_type,
                affected_nodes: gi.affected_nodes || [],
                suggested_fix: gi.suggested_fix || "",
            },
        });
    }

    return escalations;
}

function renderEscalations(escalations, graphIssues) {
    if (!escalationsBlock || !escalationsList) return;
    if (!escalations || escalations.length === 0) {
        escalationsBlock.hidden = true;
        escalationsList.innerHTML = "";
        escalationsCount.textContent = "";
        return;
    }

    escalationsBlock.hidden = false;
    escalationsCount.textContent = escalations.length;

    // Dedup graph-issue escalations against existing graph-issues cards
    // (dim the raw list entry when a matching escalation exists).
    const supersededIssues = new Set(
        escalations
            .filter(e => e.context?.issue_code)
            .map(e => `${e.context.issue_code}::${e.issue}`)
    );
    if (graphIssuesList) {
        const cards = graphIssuesList.querySelectorAll(".graph-issue-card");
        cards.forEach(card => {
            const issueType = card.classList.contains("broken_chain") ? "broken_chain"
                            : card.classList.contains("cycle") ? "cycle"
                            : card.classList.contains("orphan") ? "orphan"
                            : card.classList.contains("missing_relation") ? "missing_relation"
                            : "";
            const desc = card.querySelector(".graph-issue-desc")?.textContent || "";
            if (supersededIssues.has(`${issueType}::${desc}`)) {
                card.classList.add("superseded");
            }
        });
    }

    escalationsList.innerHTML = escalations.map(e => renderEscalationCard(e)).join("");
}

function renderEscalationCard(e) {
    const decision = state.escalationDecisions[e.escalation_id] || null;
    const sev = e.severity || "warning";
    const suggested = e.context?.suggested_relation;
    const scoreFragment = typeof e.context?.score === "number"
        ? ` · score ${e.context.score.toFixed(2)}` : "";

    const contextLines = [];
    if (e.context?.node_type && e.context?.node_id) {
        contextLines.push(`node: ${e.context.node_type}/${e.context.node_id}`);
    }
    if (suggested) {
        contextLines.push(`suggested: ${suggested.relation_name} → ${suggested.to_label || suggested.to_id}`);
    }
    if (e.context?.affected_nodes?.length) {
        contextLines.push(`affected: ${e.context.affected_nodes.join(", ")}`);
    }
    if (e.context?.suggested_fix) {
        contextLines.push(`fix: ${e.context.suggested_fix}`);
    }

    const optionButtons = (e.options || []).map(opt => {
        const label = opt.replace(/_/g, " ");
        const btnClass =
            opt === "approve_as_is" ? "btn-success" :
            opt === "reject_node"   ? "btn-danger"  :
            "btn-secondary";
        return `<button class="${btnClass} btn-sm" data-escalation-id="${esc(e.escalation_id)}" data-escalation-option="${esc(opt)}">${esc(label)}</button>`;
    }).join("");

    return `
        <div class="escalation-card ${sev} ${decision ? "resolved" : ""}" data-escalation-id="${esc(e.escalation_id)}">
            <div class="escalation-head">
                <span class="escalation-severity-pill">${esc(sev)}</span>
                <span class="escalation-meta">${esc(e.phase)} · ${esc(e.agent)}${scoreFragment}</span>
                <span class="escalation-id">${esc(e.escalation_id)}</span>
            </div>
            <div class="escalation-issue">${esc(e.issue)}</div>
            ${contextLines.length ? `<div class="escalation-context">${contextLines.map(esc).join("<br>")}</div>` : ""}
            ${decision
                ? `<div class="escalation-decision-chip">decided: ${esc(decision.replace(/_/g, " "))}</div>`
                : `<div class="escalation-actions">${optionButtons}</div>`
            }
        </div>
    `;
}

if (escalationsList) {
    escalationsList.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-escalation-id]");
        if (!btn) return;
        const id = btn.dataset.escalationId;
        const option = btn.dataset.escalationOption;
        if (!id || !option) return;
        state.escalationDecisions[id] = option;
        // Also mirror the decision into node-level state when the escalation is node-scoped
        const esc_item = state.escalations.find(x => x.escalation_id === id);
        if (esc_item?.context?.node_type && esc_item?.context?.node_id) {
            const key = `${esc_item.context.node_type}::${esc_item.context.node_id}`;
            if (option === "approve_as_is") state.nodeDecisions[key] = "approved";
            else if (option === "reject_node") state.nodeDecisions[key] = "rejected";
            else if (option === "skip") state.nodeDecisions[key] = "skipped";
            if (state.ontologyDraft) renderOntologyNodes(state.ontologyDraft);
        }
        const graphIssues = state.ontologyDraft?.graph_issues || [];
        renderEscalations(state.escalations, graphIssues);
    });
}

async function runOntologyDraft(pagesToKeep) {
    ontologyContinueBtn.disabled = true;
    ontologyRerunBtn.disabled = true;
    ontologyRerunBtn.hidden = true;

    const heartbeatMsgs = [
        "Generating ontology draft and running automatic checks...",
        "Still working — LLM is extracting ontology nodes...",
        "Still working — running semantic validation...",
        "Still working — running graph reasoning...",
        "Still working — this may take a few minutes for large documents...",
    ];
    startStatusActivity("ontology", ontologyStatus, heartbeatMsgs);

    let res;
    try {
        res = await fetch("/ontology/draft", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pdf_id: state.pdfId,
                source_type: state.sourceType,
                source_title: state.sourceTitle,
                model_name: state.modelName,
                pages_to_keep: pagesToKeep,
                target_language: state.targetLanguage,
            }),
        });
    } finally {
        stopStatusActivity("ontology");
    }

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Ontology draft failed");
    }
    const result = await res.json();
    renderOntologyDraft(result);
    showOntologyStatus(
        result.human_required_fields.length > 0
            ? `Step 1 done. Fill in the ${result.human_required_fields.length} required field${result.human_required_fields.length > 1 ? "s" : ""} below, then press Apply & Continue to start triplet extraction (step 2).`
            : result.schema_issues.length > 0
            ? "Step 1 done (with schema issues). Press the button below to start triplet extraction (step 2, this will take a few minutes)."
            : "Step 1 done. Press the button below to start triplet extraction (step 2, this will take a few minutes).",
        result.human_required_fields.length > 0 ? "loading" : result.schema_issues.length > 0 ? "error" : "success",
    );
    ontologyRerunBtn.disabled = false;
}

function collectOntologyAnswers() {
    if (!state.ontologyDraft) return [];
    return state.ontologyDraft.human_required_fields.map((field) => {
        const input = document.querySelector(`[data-ontology-field="${field.field_key}"]`);
        return {
            field_key: field.field_key,
            value: input ? input.value.trim() : "",
        };
    });
}

ontologyRerunBtn.addEventListener("click", async () => {
    if (state.extractionInProgress) return;
    try {
        await runOntologyDraft(state.ontologyPagesToKeep);
    } catch (err) {
        showOntologyStatus(err.message, "error");
        syncOntologyActionButtons();
    }
});

ontologyContinueBtn.addEventListener("click", async () => {
    if (state.extractionInProgress) return;
    ontologyContinueBtn.disabled = true;
    ontologyRerunBtn.disabled = true;
    try {
        if (state.ontologyDraft && state.ontologyDraft.human_required_fields.length > 0) {
            const answers = collectOntologyAnswers();

            // Highlight empty required fields and block with visual feedback
            const missing = answers.filter(a => !a.value);
            if (missing.length > 0) {
                missing.forEach(a => {
                    const input = document.querySelector(`[data-ontology-field="${a.field_key}"]`);
                    if (input) {
                        input.classList.add("input-error");
                        input.addEventListener("input", () => input.classList.remove("input-error"), { once: true });
                    }
                });
                showOntologyStatus(`Fill in all ${missing.length} required field${missing.length > 1 ? "s" : ""} before continuing (highlighted above).`, "error");
                syncOntologyActionButtons();
                // Scroll to first empty field
                const firstEmpty = document.querySelector(`[data-ontology-field="${missing[0].field_key}"]`);
                if (firstEmpty) firstEmpty.scrollIntoView({ behavior: "smooth", block: "center" });
                return;
            }

            showOntologyStatus("Applying required asset metadata...", "loading");
            const reviewRes = await fetch("/ontology/review", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    pdf_id: state.pdfId,
                    answers,
                    model_name: state.modelName,
                }),
            });
            if (!reviewRes.ok) {
                const err = await reviewRes.json();
                throw new Error(err.detail || "Ontology review failed");
            }
            const reviewed = await reviewRes.json();
            const shouldAutoStartExtraction = reviewed.human_required_fields.length === 0 && !state.tripletsExtracted;
            if (shouldAutoStartExtraction) {
                state.extractionInProgress = true;
            }
            renderOntologyDraft(reviewed);
            if (reviewed.human_required_fields.length > 0) {
                showOntologyStatus("Some fields could not be applied. Please review and re-fill them.", "error");
                syncOntologyActionButtons();
                return;
            }
        }

        // If triplets were already extracted (e.g. user fixed ontology fields after extraction),
        // go straight to validation without re-running the LLM.
        if (state.tripletsExtracted && state.triplets.length > 0) {
            transitionToMainLayout();
            return;
        }

        const extractionStartMessage = state.ontologyDraft?.schema_issues?.length > 0
            ? "Ontology schema issues remain, but triplet extraction will continue so you do not lose this run."
            : "Extracting diagnostic triads for human validation...";
        showOntologyStatus(extractionStartMessage, "loading");
        await runExtraction(state.ontologyPagesToKeep, { alreadyLocked: state.extractionInProgress });
    } catch (err) {
        state.extractionInProgress = false;
        if (state.ontologyDraft) renderOntologyDraft(state.ontologyDraft);
        showOntologyStatus(err.message, "error");
        syncOntologyActionButtons();
    }
});

// ─── Graph Reasoning — Apply / Reject suggestions ───

rejectAllSuggestionsBtn.addEventListener("click", () => {
    suggestedRelationsList.querySelectorAll(".suggestion-card").forEach(card => {
        card.dataset.decision = "rejected";
        card.classList.add("rejected");
        card.classList.remove("accepted");
    });
});

applySuggestionsBtn.addEventListener("click", async () => {
    if (!state.ontologyDraft) return;

    const acceptedCards = [...suggestedRelationsList.querySelectorAll(".suggestion-card[data-decision='accepted']")];
    if (acceptedCards.length === 0) {
        showOntologyStatus("No suggestions accepted — select at least one before applying.", "error");
        return;
    }

    const allSuggestions = state.ontologyDraft.suggested_relations || [];
    const accepted = acceptedCards.map(card => allSuggestions[parseInt(card.dataset.idx, 10)]).filter(Boolean);

    applySuggestionsBtn.disabled = true;
    rejectAllSuggestionsBtn.disabled = true;
    showOntologyStatus(`Applying ${accepted.length} accepted relation(s)...`, "loading");

    try {
        const res = await fetch("/ontology/apply-suggestions", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pdf_id: state.pdfId,
                accepted_suggestions: accepted,
            }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Apply suggestions failed");
        }
        const updated = await res.json();
        renderOntologyDraft(updated);
        const applyMessage = updated.schema_issues.length > 0
            ? `${accepted.length} relation(s) applied, but blocking schema issues still remain.`
            : updated.human_required_fields.length > 0
            ? `${accepted.length} relation(s) applied. Required human input is still needed below.`
            : `${accepted.length} relation(s) applied. You can continue to human validation.`;
        showOntologyStatus(applyMessage, updated.schema_issues.length > 0 ? "error" : "success");
    } catch (err) {
        showOntologyStatus(err.message, "error");
    } finally {
        applySuggestionsBtn.disabled = false;
        rejectAllSuggestionsBtn.disabled = false;
    }
});

// ─── Extraction helpers ───

async function runExtraction(pagesToKeep, { alreadyLocked = false } = {}) {
    if (state.extractionInProgress && !alreadyLocked) {
        return;
    }
    if (!alreadyLocked) {
        state.extractionInProgress = true;
        if (state.ontologyDraft) renderOntologyDraft(state.ontologyDraft);
        else syncOntologyActionButtons();
    }

    const extractMsgs = [
        "Extracting diagnostic triads from selected pages...",
        "Still working — LLM is processing page chunks...",
        "Still working — merging and deduplicating results...",
        "Still working — this may take a few minutes for large documents...",
    ];
    startStatusActivity("ontology", ontologyStatus, extractMsgs);

    let extractRes;
    try {
        extractRes = await fetch("/extract-tables", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pdf_id: state.pdfId,
                source_type: state.sourceType,
                source_title: state.sourceTitle,
                model_name: state.modelName,
                pages_to_keep: pagesToKeep,
                target_language: state.targetLanguage,
            }),
        });
    } finally {
        stopStatusActivity("ontology");
    }

    if (!extractRes.ok) {
        const err = await extractRes.json();
        throw new Error(err.detail || "Extraction failed");
    }
    const extractData = await extractRes.json();
    state.triplets = extractData.triplets;

    if (state.triplets.length === 0) {
        throw new Error("No diagnostic triads found in the document.");
    }

    state.tripletsExtracted = true;
    state.extractionInProgress = false;
    transitionToMainLayout();
}

function transitionToMainLayout() {
    // Move PDF canvases from ontology viewer to main viewer if already loaded.
    if (ontologyPdfContainer.children.length > 0 && pdfContainer.children.length === 0) {
        movePdfPages(ontologyPdfContainer, pdfContainer, "ontology-pdf-page-", "pdf-page-");
    }

    uploadScreen.hidden = true;
    cutPlanScreen.hidden = true;
    ontologyScreen.hidden = true;
    mainLayout.hidden = false;
    pdfTitle.textContent = state.sourceTitle || state.uploadFilename;
    appBarOperator.textContent = state.operator || "";
    appBarDate.textContent = state.extractionDate || "";

    // Leaving the Ontology screen: stop polling and close any open drawer
    stopStatusPolling();
    closeAuditDrawer();

    state.currentIndex = 0;
    state.validatedTriplets = [];
    state.exportCompleted = false;
    state.autoExportTriggered = false;

    // If PDF wasn't loaded yet (small doc path), load it now
    if (!state.pdfLoaded) {
        loadPdfLazy(state.pdfId, pdfContainer).then(() => {
            state.pdfLoaded = true;
            displayCurrentTriplet();
        });
    } else {
        // Re-attach observer to the new container since pages were moved
        setupPdfObserver(pdfContainer);
        displayCurrentTriplet();
    }
}

// ─── PDF Viewer (lazy rendering via IntersectionObserver) ───

const renderedPages = new Set();

async function loadPdfLazy(pdfId, container) {
    const url = `/pdf/${pdfId}`;
    state.pdfDoc = await pdfjsLib.getDocument(url).promise;
    state.totalPages = state.pdfDoc.numPages;
    container.innerHTML = "";
    renderedPages.clear();

    const prefix = container === cpPdfContainer
        ? "cp-pdf-page-"
        : container === ontologyPdfContainer
            ? "ontology-pdf-page-"
            : "pdf-page-";

    // Get dimensions from first page for placeholder sizing
    const firstPage = await state.pdfDoc.getPage(1);
    const scale = 1.5;
    const vp = firstPage.getViewport({ scale });

    // Create lightweight placeholders for all pages (no rendering yet)
    for (let i = 1; i <= state.totalPages; i++) {
        const wrapper = document.createElement("div");
        wrapper.className = "pdf-page-wrapper";
        wrapper.id = `${prefix}${i}`;
        wrapper.dataset.pageNum = i;
        wrapper.style.minHeight = `${vp.height}px`;
        wrapper.style.width = `${vp.width}px`;

        const label = document.createElement("div");
        label.className = "pdf-page-label";
        label.textContent = `${i} / ${state.totalPages}`;

        const canvas = document.createElement("canvas");
        canvas.width = vp.width;
        canvas.height = vp.height;

        wrapper.appendChild(label);
        wrapper.appendChild(canvas);
        container.appendChild(wrapper);
    }

    // Render only the first page immediately
    await renderPage(1, container);

    // Set up lazy observer for the rest
    setupPdfObserver(container);
}

function setupPdfObserver(container) {
    // Disconnect any previous observer
    if (container._pdfObserver) {
        container._pdfObserver.disconnect();
    }

    const observer = new IntersectionObserver(
        (entries) => {
            for (const entry of entries) {
                if (entry.isIntersecting) {
                    const pageNum = parseInt(entry.target.dataset.pageNum, 10);
                    if (!renderedPages.has(pageNum)) {
                        renderPage(pageNum, container);
                    }
                }
            }
        },
        { root: container, rootMargin: "600px 0px" }
    );

    for (const child of container.children) {
        if (child.dataset && child.dataset.pageNum) {
            observer.observe(child);
        }
    }

    container._pdfObserver = observer;
}

async function renderPage(pageNum, container) {
    if (renderedPages.has(pageNum)) return;
    renderedPages.add(pageNum);

    const prefix = container === cpPdfContainer
        ? "cp-pdf-page-"
        : container === ontologyPdfContainer
            ? "ontology-pdf-page-"
            : "pdf-page-";
    const wrapper = document.getElementById(`${prefix}${pageNum}`);
    if (!wrapper) return;

    try {
        const page = await state.pdfDoc.getPage(pageNum);
        const scale = 1.5;
        const viewport = page.getViewport({ scale });
        const canvas = wrapper.querySelector("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        const ctx = canvas.getContext("2d");
        await page.render({ canvasContext: ctx, viewport }).promise;
    } catch (err) {
        console.warn(`Failed to render page ${pageNum}:`, err);
    }
}

function scrollToPage(pageNum) {
    const el = document.getElementById(`pdf-page-${pageNum}`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ─── Triplet Display ───

function updateReviewProgress() {
    const total = state.triplets.length;
    const done = state.currentIndex;
    const saved = state.validatedTriplets.length;
    const discarded = done - saved;
    const pct = total > 0 ? Math.round((done / total) * 100) : 0;

    if (reviewProgressBar) reviewProgressBar.style.width = `${pct}%`;
    if (reviewProgressLabel) reviewProgressLabel.textContent = `${done} / ${total}`;
    if (reviewStatSaved) {
        reviewStatSaved.textContent = saved > 0 ? `✓ ${saved}` : "";
        reviewStatSaved.hidden = saved === 0;
    }
    if (reviewStatDiscarded) {
        reviewStatDiscarded.textContent = discarded > 0 ? `✗ ${discarded}` : "";
        reviewStatDiscarded.hidden = discarded === 0;
    }
}

function displayCurrentTriplet() {
    const idx = state.currentIndex;
    const total = state.triplets.length;

    updateReviewProgress();

    if (idx >= total) {
        discardBtn.disabled = false;
        saveBtn.disabled = false;
        showSummary();
        return;
    }

    const triplet = state.triplets[idx];

    // A: render the hierarchical triplet card
    if (tripletCardContainer) {
        tripletCardContainer.innerHTML = buildTripletCard(triplet, idx);
        // Trigger enter animation on next frame
        requestAnimationFrame(() => {
            const card = tripletCardContainer.querySelector(".triplet-card");
            if (card) card.classList.add("triplet-card--visible");
        });
    }

    // Scroll PDF to the first corrective action source page
    if (triplet.corrective_actions.length > 0) {
        const page = triplet.corrective_actions[0].source_page;
        if (page > 0 && page <= state.totalPages) scrollToPage(page);
    }

    discardBtn.disabled = false;
    saveBtn.disabled = false;
    actionButtons.hidden = false;
    summary.hidden = true;
}

// ─── A: Hierarchical triplet card ───
// Renders a single triplet as a chain card: Symptom → FailureModes → CorrectiveActions.
// Uses data-field attributes compatible with collectEditsFromDom.

function buildTripletCard(triplet, idx) {
    const sym = triplet.symptom;
    const fms = triplet.failure_modes || [];
    const cas = triplet.corrective_actions || [];

    // severity badge colour
    const sevClass = { high: "sev-high", medium: "sev-medium", low: "sev-low" }[
        (sym.severity || "").toLowerCase()
    ] || "sev-unknown";

    let html = `<div class="triplet-card">`;

    // ── Symptom block ──
    html += `
        <div class="tc-block tc-symptom">
            <div class="tc-block-label">
                <span class="tc-label-badge tc-label-symptom">Symptom</span>
                <span class="tc-id">${esc(sym.symptom_id)}</span>
                <span class="tc-severity ${sevClass}">${esc(sym.severity || "—")}</span>
            </div>
            <div class="tc-fields">
                <div class="tc-field">
                    <span class="tc-field-label">Name</span>
                    <span class="tc-field-value" contenteditable="true" data-field="sym-0-1">${esc(String(sym.name || ""))}</span>
                </div>
                <div class="tc-field tc-field-wide">
                    <span class="tc-field-label">Description</span>
                    <span class="tc-field-value" contenteditable="true" data-field="sym-0-2">${esc(String(sym.description || ""))}</span>
                </div>
            </div>
        </div>`;

    // ── Connector ──
    html += `<div class="tc-connector"><span class="tc-connector-arrow">&#8595;</span></div>`;

    // ── Failure Modes ──
    html += `<div class="tc-block tc-failures">`;
    html += `<div class="tc-block-label"><span class="tc-label-badge tc-label-fm">Failure Modes</span><span class="tc-count">${fms.length}</span></div>`;
    if (fms.length === 0) {
        html += `<p class="tc-empty">No failure modes extracted</p>`;
    } else {
        fms.forEach((fm, fi) => {
            html += `
                <div class="tc-sub-item">
                    <div class="tc-sub-header">
                        <span class="tc-id">${esc(fm.failure_mode_id)}</span>
                    </div>
                    <div class="tc-fields">
                        <div class="tc-field">
                            <span class="tc-field-label">Name</span>
                            <span class="tc-field-value" contenteditable="true" data-field="fm-${fi}-1">${esc(String(fm.name || ""))}</span>
                        </div>
                        <div class="tc-field tc-field-wide">
                            <span class="tc-field-label">Description</span>
                            <span class="tc-field-value" contenteditable="true" data-field="fm-${fi}-2">${esc(String(fm.description || ""))}</span>
                        </div>
                        ${fm.material_context ? `
                        <div class="tc-field">
                            <span class="tc-field-label">Material context</span>
                            <span class="tc-field-value" contenteditable="true" data-field="fm-${fi}-3">${esc(String(fm.material_context))}</span>
                        </div>` : ""}
                    </div>
                </div>`;
        });
    }
    html += `</div>`;

    // ── Connector ──
    html += `<div class="tc-connector"><span class="tc-connector-arrow">&#8595;</span></div>`;

    // ── Corrective Actions ──
    html += `<div class="tc-block tc-actions">`;
    html += `<div class="tc-block-label"><span class="tc-label-badge tc-label-ca">Corrective Actions</span><span class="tc-count">${cas.length}</span></div>`;
    if (cas.length === 0) {
        html += `<p class="tc-empty">No corrective actions extracted</p>`;
    } else {
        cas.forEach((ca, ci) => {
            html += `
                <div class="tc-sub-item">
                    <div class="tc-sub-header">
                        <span class="tc-id">${esc(ca.action_id)}</span>
                        <span class="page-link tc-page-link" data-page="${ca.source_page}">p.${ca.source_page}</span>
                    </div>
                    <div class="tc-fields">
                        <div class="tc-field">
                            <span class="tc-field-label">Name</span>
                            <span class="tc-field-value" contenteditable="true" data-field="ca-${ci}-1">${esc(String(ca.name || ""))}</span>
                        </div>
                        <div class="tc-field tc-field-wide">
                            <span class="tc-field-label">Description</span>
                            <span class="tc-field-value" contenteditable="true" data-field="ca-${ci}-2">${esc(String(ca.description || ""))}</span>
                        </div>
                        <div class="tc-field tc-field-wide">
                            <span class="tc-field-label">Instruction</span>
                            <span class="tc-field-value" contenteditable="true" data-field="ca-${ci}-3">${esc(String(ca.instruction_text || ""))}</span>
                        </div>
                    </div>
                </div>`;
        });
    }
    html += `</div>`;

    html += `</div>`; // .triplet-card
    return html;
}

// Legacy table builders kept for any future reuse
function buildEditableTable(headers, rows, editableFlags, prefix) {
    if (rows.length === 0) return '<p style="color:var(--text-dim);font-size:0.75rem;">No data</p>';
    let html = "<table><thead><tr>";
    headers.forEach(h => html += `<th>${esc(h)}</th>`);
    html += "</tr></thead><tbody>";
    rows.forEach((row, ri) => {
        html += "<tr>";
        row.forEach((cell, ci) => {
            if (editableFlags[ci]) {
                html += `<td contenteditable="true" data-field="${prefix}-${ri}-${ci}">${esc(String(cell))}</td>`;
            } else {
                html += `<td class="cell-readonly">${esc(String(cell))}</td>`;
            }
        });
        html += "</tr>";
    });
    html += "</tbody></table>";
    return html;
}

function buildCaTable(actions) {
    if (actions.length === 0) return '<p style="color:var(--text-dim);font-size:0.75rem;">No data</p>';
    let html = "<table><thead><tr>";
    ["ID", "Name", "Description", "Instruction", "Pg"].forEach(h => html += `<th>${esc(h)}</th>`);
    html += "</tr></thead><tbody>";
    actions.forEach((ca, ri) => {
        html += "<tr>";
        html += `<td class="cell-readonly">${esc(ca.action_id)}</td>`;
        html += `<td contenteditable="true" data-field="ca-${ri}-1">${esc(ca.name)}</td>`;
        html += `<td contenteditable="true" data-field="ca-${ri}-2">${esc(ca.description)}</td>`;
        html += `<td contenteditable="true" data-field="ca-${ri}-3">${esc(ca.instruction_text)}</td>`;
        html += `<td class="cell-readonly"><span class="page-link" data-page="${ca.source_page}">${ca.source_page}</span></td>`;
        html += "</tr>";
    });
    html += "</tbody></table>";
    return html;
}

caContainer.addEventListener("click", (e) => {
    const link = e.target.closest(".page-link");
    if (link) {
        const page = parseInt(link.dataset.page, 10);
        if (page > 0 && page <= state.totalPages) scrollToPage(page);
    }
});

// Page-link clicks inside the new triplet card
if (tripletCardContainer) {
    tripletCardContainer.addEventListener("click", (e) => {
        const link = e.target.closest(".tc-page-link");
        if (link) {
            const page = parseInt(link.dataset.page, 10);
            if (page > 0 && page <= state.totalPages) scrollToPage(page);
        }
    });
}

// ─── Triplet review keyboard navigation ───
//
// Rationale: contenteditable cells are editable by default, but TAB inside one
// inserts a tab character instead of moving focus. Operators reviewing dozens
// of triplets need to fly through fields with the keyboard alone — so we
// intercept TAB / Shift+TAB to walk the editable cells in DOM order across
// Symptom → FailureModes → CorrectiveActions, and bind Ctrl/Cmd+Enter to
// Save & Next, Ctrl/Cmd+Backspace to Discard.

function getEditableCellsInOrder() {
    // The new triplet card uses span[contenteditable] inside .triplet-card.
    // Fall back to the legacy td[contenteditable] containers if the card is absent.
    if (tripletCardContainer && tripletCardContainer.querySelector('[contenteditable="true"]')) {
        return [...tripletCardContainer.querySelectorAll('[contenteditable="true"]')];
    }
    return [
        ...symContainer.querySelectorAll('td[contenteditable="true"]'),
        ...fmContainer.querySelectorAll('td[contenteditable="true"]'),
        ...caContainer.querySelectorAll('td[contenteditable="true"]'),
    ];
}

function moveFocusBetweenCells(currentCell, direction) {
    const cells = getEditableCellsInOrder();
    const idx = cells.indexOf(currentCell);
    if (idx === -1) return false;
    const nextIdx = idx + direction;
    if (nextIdx < 0 || nextIdx >= cells.length) return false;
    const next = cells[nextIdx];
    next.focus();
    // Place caret at end of the new cell so the operator can keep typing.
    const range = document.createRange();
    range.selectNodeContents(next);
    range.collapse(false);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    return true;
}

function handleTripletKeydown(e) {
    const cell = e.target.closest('[contenteditable="true"]');

    // Save & Next: Ctrl/Cmd+Enter (works inside a cell or anywhere on the screen)
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        if (saveBtn && !saveBtn.disabled && !mainLayout.hidden) {
            e.preventDefault();
            if (cell) cell.blur(); // commit any pending IME composition
            advanceTriplet({ keep: true });
        }
        return;
    }

    // Discard: Ctrl/Cmd+Backspace
    if ((e.ctrlKey || e.metaKey) && (e.key === "Backspace" || e.key === "Delete")) {
        if (discardBtn && !discardBtn.disabled && !mainLayout.hidden) {
            e.preventDefault();
            if (cell) cell.blur();
            advanceTriplet({ keep: false });
        }
        return;
    }

    // TAB navigation only meaningful when focus is on an editable cell
    if (!cell) return;

    if (e.key === "Tab") {
        const direction = e.shiftKey ? -1 : 1;
        if (moveFocusBetweenCells(cell, direction)) {
            e.preventDefault();
        }
        return;
    }

    // Enter (without modifiers) inside a cell: keep the new line behaviour off
    // for single-line fields like Name and Severity to avoid messy multi-line
    // values. Plain Enter commits and moves to the next cell.
    if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
        e.preventDefault();
        moveFocusBetweenCells(cell, 1);
    }
}

// Bind the keydown handler at the document level so it survives table
// re-renders (the tables are rebuilt on every triplet, but the handler
// listens on a stable parent).
document.addEventListener("keydown", (e) => {
    if (mainLayout.hidden) return;
    handleTripletKeydown(e);
});

function esc(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

function formatDuration(seconds) {
    const safe = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(safe / 60);
    const remainder = Math.round(safe % 60);
    if (minutes === 0) return `${remainder}s`;
    return `${minutes}m ${String(remainder).padStart(2, "0")}s`;
}

function formatNumber(value) {
    return new Intl.NumberFormat("en-US").format(Number(value) || 0);
}

function formatUsd(value) {
    const amount = Number(value) || 0;
    return `$${amount.toFixed(amount >= 1 ? 2 : 4)}`;
}

function renderRunMetrics(metrics) {
    state.runMetrics = metrics;
    if (!metrics) {
        summaryKpis.hidden = true;
        summaryKpis.innerHTML = "";
        return;
    }

    const totals = metrics.totals || {};
    const doc = metrics.document || {};
    const derived = metrics.derived_kpis || {};
    const stages = metrics.stages || {};
    const pricingBasis = metrics.pricing_basis || {};
    const totalByModel = totals.by_model || {};
    const saved = state.validatedTriplets.length;
    const discarded = state.triplets.length - saved;

    const stageRows = ["scoping", "ontology", "extraction", "export"]
        .filter(name => stages[name])
        .map((name) => {
            const stage = stages[name];
            const details = stage.details || {};
            const bits = [
                `${formatDuration(stage.duration_seconds)}`
            ];
            if (stage.llm_calls) bits.push(`${formatNumber(stage.llm_calls)} call(s)`);
            if (stage.total_tokens) bits.push(`${formatNumber(stage.total_tokens)} tok`);
            if (stage.estimated_cost_usd) bits.push(formatUsd(stage.estimated_cost_usd));
            if (details.chunk_count) bits.push(`${formatNumber(details.chunk_count)} chunk(s)`);
            if (details.retry_count != null && details.retry_count > 0) bits.push(`${formatNumber(details.retry_count)} retry`);
            return `
                <div class="kpi-stage-row">
                    <div class="kpi-stage-name">${esc(name)}</div>
                    <div>${esc(bits.join(" · "))}</div>
                </div>
            `;
        }).join("");

    const modelRows = Object.entries(totalByModel)
        .sort((a, b) => (b[1].estimated_cost_usd || 0) - (a[1].estimated_cost_usd || 0))
        .map(([modelKey, modelData]) => `
            <div class="kpi-stage-row">
                <div class="kpi-stage-name">${esc(modelData.label || modelKey)}</div>
                <div>${esc(`${formatUsd(modelData.estimated_cost_usd)} · ${formatNumber(modelData.total_tokens)} tok · ${formatNumber(modelData.llm_calls)} call(s)`)}</div>
            </div>
        `)
        .join("");

    summaryKpis.hidden = false;
    summaryKpis.innerHTML = `
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Total Automation Time</div>
                <div class="kpi-value">${esc(formatDuration(totals.duration_seconds))}</div>
                <div class="kpi-note">${esc(formatNumber(doc.selected_pages || 0))} selected pages out of ${esc(formatNumber(doc.total_pages || 0))}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Estimated Cost</div>
                <div class="kpi-value">${esc(formatUsd(totals.estimated_cost_usd))}</div>
                <div class="kpi-note">${esc(pricingBasis.label || "Estimated from model pricing")}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">LLM Tokens</div>
                <div class="kpi-value">${esc(formatNumber(totals.total_tokens))}</div>
                <div class="kpi-note">${esc(formatNumber(totals.prompt_tokens))} input · ${esc(formatNumber(totals.completion_tokens))} output</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Review Yield</div>
                <div class="kpi-value">${esc(formatNumber(saved))} kept / ${esc(formatNumber(discarded))} dropped</div>
                <div class="kpi-note">${esc(formatNumber(stages.extraction?.details?.triplet_count || state.triplets.length || 0))} extracted triplet(s)</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cost Per Selected Page</div>
                <div class="kpi-value">${esc(formatUsd(derived.cost_per_selected_page_usd))}</div>
                <div class="kpi-note">${esc((Number(derived.pages_kept_ratio || 0) * 100).toFixed(1))}% of document kept after scoping</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cost Per Extracted Triplet</div>
                <div class="kpi-value">${esc(formatUsd(derived.cost_per_extracted_triplet_usd))}</div>
                <div class="kpi-note">${esc(formatDuration(derived.seconds_per_selected_page || 0))} per selected page</div>
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
        ${buildNodeCountTable(metrics.nodes_by_type)}
    `;
}

function buildNodeCountTable(nodesByType) {
    if (!nodesByType || Object.keys(nodesByType).length === 0) return "";
    const rows = Object.entries(nodesByType)
        .sort((a, b) => b[1] - a[1])
        .map(([type, count]) => `
            <div class="kpi-stage-row">
                <div class="kpi-stage-name">${esc(type)}</div>
                <div>${esc(String(count))}</div>
            </div>
        `).join("");
    return `
        <div class="kpi-section">
            <div class="kpi-section-title">Node Count by Type</div>
            <div class="kpi-stage-list">${rows}</div>
        </div>
    `;
}

async function refreshRunMetrics() {
    if (!state.pdfId) return;
    const res = await fetch(`/run-metrics/${encodeURIComponent(state.pdfId)}`);
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Could not load run metrics");
    }
    const metrics = await res.json();
    renderRunMetrics(metrics);
}

// ─── Collect inline edits ───

function collectEditsFromDom() {
    const triplet = state.triplets[state.currentIndex];

    const symName = getEditedValue("sym-0-1");
    const symDesc = getEditedValue("sym-0-2");
    const symSev = getEditedValue("sym-0-3");
    if (symName !== null) triplet.symptom.name = symName;
    if (symDesc !== null) triplet.symptom.description = symDesc;
    if (symSev !== null) triplet.symptom.severity = symSev;

    triplet.failure_modes.forEach((fm, i) => {
        const name = getEditedValue(`fm-${i}-1`);
        const desc = getEditedValue(`fm-${i}-2`);
        const mat = getEditedValue(`fm-${i}-3`);
        if (name !== null) fm.name = name;
        if (desc !== null) fm.description = desc;
        if (mat !== null) fm.material_context = mat;
    });

    triplet.corrective_actions.forEach((ca, i) => {
        const name = getEditedValue(`ca-${i}-1`);
        const desc = getEditedValue(`ca-${i}-2`);
        const instr = getEditedValue(`ca-${i}-3`);
        if (name !== null) ca.name = name;
        if (desc !== null) ca.description = desc;
        if (instr !== null) ca.instruction_text = instr;
    });
}

function getEditedValue(field) {
    const el = document.querySelector(`[data-field="${field}"]`);
    return el ? el.textContent.trim() : null;
}

// ─── Validation Buttons ───

// Re-entrance guard: even if displayCurrentTriplet re-enables the buttons
// synchronously, we never want a single click to advance the index twice.
let tripletAdvanceInFlight = false;

function advanceTriplet({ keep }) {
    if (tripletAdvanceInFlight) return;
    if (discardBtn.disabled || saveBtn.disabled) return;
    tripletAdvanceInFlight = true;
    try {
        discardBtn.disabled = true;
        saveBtn.disabled = true;
        if (keep) {
            collectEditsFromDom();
            state.validatedTriplets.push(state.triplets[state.currentIndex]);
        }
        state.currentIndex++;
        displayCurrentTriplet();
    } finally {
        tripletAdvanceInFlight = false;
    }
}

discardBtn.addEventListener("click", () => advanceTriplet({ keep: false }));
saveBtn.addEventListener("click", () => advanceTriplet({ keep: true }));

// ─── Summary & Export ───

function showSummary() {
    actionButtons.hidden = true;
    if (tripletCardContainer) tripletCardContainer.innerHTML = "";
    symContainer.innerHTML = "";
    fmContainer.innerHTML = "";
    caContainer.innerHTML = "";

    // Progress bar: fill to 100% on completion
    if (reviewProgressBar) reviewProgressBar.style.width = "100%";
    if (reviewProgressBar) reviewProgressBar.style.background = "var(--success)";
    if (reviewProgressLabel) reviewProgressLabel.textContent = "Done";

    const saved = state.validatedTriplets.length;
    const discarded = state.triplets.length - saved;
    summaryText.textContent = `${saved} triplet(s) validated, ${discarded} discarded.`;
    summaryExportStatus.textContent = saved === 0 ? "No validated triplets to export." : "Preparing automatic JSON download...";
    summaryKpis.hidden = true;
    summaryKpis.innerHTML = "";
    summary.hidden = false;
    generateBtn.hidden = saved === 0;
    openGraphEditorBtn.hidden = !state.exportCompleted;

    if (saved > 0 && !state.autoExportTriggered) {
        state.autoExportTriggered = true;
        exportOntology({ auto: true });
    }
}

async function exportOntology({ auto = false } = {}) {
    generateBtn.disabled = true;
    summaryExportStatus.textContent = auto
        ? "Preparing automatic JSON download..."
        : "Generating JSON export...";

    try {
        const res = await fetch("/generate-json", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                pdf_id: state.pdfId,
                validated_triplets: state.validatedTriplets,
                target_language: state.targetLanguage,
            }),
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail?.message || err.detail || "JSON generation failed");
        }

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const disposition = res.headers.get("Content-Disposition") || "";
        const match = disposition.match(/filename=([^;]+)/i);
        const filename = match ? match[1].trim().replace(/^\"|\"$/g, "") : "ontology_export.json";
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        state.exportCompleted = true;
        openGraphEditorBtn.hidden = false;
        let metricsNote = "";
        try {
            await refreshRunMetrics();
        } catch (metricsErr) {
            console.warn("Could not refresh run metrics", metricsErr);
            metricsNote = " KPI summary unavailable.";
        }
        summaryExportStatus.textContent = auto
            ? `JSON downloaded automatically. You can now open the graph editor.${metricsNote}`
            : `JSON downloaded. You can open the graph editor.${metricsNote}`;
    } catch (err) {
        summaryExportStatus.textContent = `Export failed: ${err.message}`;
        alert("Error: " + err.message);
    } finally {
        generateBtn.disabled = false;
    }
}

generateBtn.addEventListener("click", async () => {
    await exportOntology({ auto: false });
});

openGraphEditorBtn.addEventListener("click", () => {
    const target = state.pdfId ? `/graph-editor/${encodeURIComponent(state.pdfId)}` : "/graph-editor";
    window.open(target, "_blank", "noopener");
});
