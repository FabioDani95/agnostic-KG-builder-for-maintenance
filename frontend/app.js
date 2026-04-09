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
        if (thresholdInput && cfg.small_doc_threshold != null)
            thresholdInput.value = cfg.small_doc_threshold;
        if (retriesInput && cfg.reflective_loop?.max_retries != null)
            retriesInput.value = cfg.reflective_loop.max_retries;
        if (severitySelect && cfg.reflective_loop?.retry_on_severity)
            severitySelect.value = cfg.reflective_loop.retry_on_severity;
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
};

const statusActivity = {
    upload: null,
    cutPlan: null,
    ontology: null,
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
const tripletCounter = document.getElementById("triplet-counter");
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
    if (!isNaN(threshVal)) advancedOverrides.small_doc_threshold = threshVal;
    if (!isNaN(retriesVal)) advancedOverrides.max_retries = retriesVal;
    if (severityVal) advancedOverrides.retry_on_severity = severityVal;
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
                <strong>Ready.</strong> ${hasSuggestions ? `You can review ${result.suggested_relations.length} optional graph suggestion${result.suggested_relations.length > 1 ? "s" : ""} below, or go straight to` : "Proceed to"} human validation.
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

function displayCurrentTriplet() {
    const idx = state.currentIndex;
    const total = state.triplets.length;

    if (idx >= total) {
        showSummary();
        return;
    }

    const triplet = state.triplets[idx];
    tripletCounter.textContent = `Triplet ${idx + 1} / ${total}`;

    symContainer.innerHTML = buildEditableTable(
        ["ID", "Name", "Description", "Severity"],
        [[triplet.symptom.symptom_id, triplet.symptom.name, triplet.symptom.description, triplet.symptom.severity]],
        [false, true, true, true], "sym"
    );

    fmContainer.innerHTML = buildEditableTable(
        ["ID", "Name", "Description", "Material Context"],
        triplet.failure_modes.map(fm => [fm.failure_mode_id, fm.name, fm.description, fm.material_context]),
        [false, true, true, true], "fm"
    );

    caContainer.innerHTML = buildCaTable(triplet.corrective_actions);

    if (triplet.corrective_actions.length > 0) {
        const page = triplet.corrective_actions[0].source_page;
        if (page > 0 && page <= state.totalPages) scrollToPage(page);
    }

    discardBtn.disabled = false;
    saveBtn.disabled = false;
    actionButtons.hidden = false;
    summary.hidden = true;
}

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

discardBtn.addEventListener("click", () => {
    discardBtn.disabled = true;
    saveBtn.disabled = true;
    state.currentIndex++;
    displayCurrentTriplet();
});

saveBtn.addEventListener("click", () => {
    discardBtn.disabled = true;
    saveBtn.disabled = true;
    collectEditsFromDom();
    state.validatedTriplets.push(state.triplets[state.currentIndex]);
    state.currentIndex++;
    displayCurrentTriplet();
});

// ─── Summary & Export ───

function showSummary() {
    actionButtons.hidden = true;
    symContainer.innerHTML = "";
    fmContainer.innerHTML = "";
    caContainer.innerHTML = "";
    tripletCounter.textContent = "Review Complete";

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
