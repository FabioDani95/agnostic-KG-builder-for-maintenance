window.__kgPdfjsPromise = import("https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.min.mjs")
    .then((pdfjsLib) => {
        pdfjsLib.GlobalWorkerOptions.workerSrc =
            "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.4.168/pdf.worker.min.mjs";
        return pdfjsLib;
    })
    .catch((err) => {
        console.warn("PDF.js preload failed; chat viewer will retry on demand.", err);
        return null;
    });

const dateInput = document.getElementById("extraction-date");
dateInput.value = new Date().toISOString().split("T")[0];

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

const state = {
    pdfId: null,
    modelName: "",
    targetLanguage: "en",
    uploadFilename: "",
    operator: "",
    extractionDate: "",
    scopingModel: "",
    pageOffset: 0,
    runId: null,
};

// ── Chat layout bootstrap ──────────────────────────────────────────────
async function _enterChatLayout(pdfId, filename, operator) {
    // Read model selections from the startup form
    const uploadScreen = document.getElementById("upload-screen");
    const scopingModel = document.getElementById("scoping-model")?.value || null;
    const extractionModel = document.getElementById("llm-model")?.value || null;
    const targetLang = document.getElementById("graph-language")?.value || "en";
    const manualPage1PdfPage = parseInt(document.getElementById("startup-page-offset")?.value) || 1;
    const pageOffset = Math.max(0, manualPage1PdfPage - 1);

    // Dynamically import chat.js and boot, passing model selections directly to the
    // /chat/start endpoint so the store is correctly initialised before scoping runs.
    const { initChat } = await import("/chat.js?v=20260501a");
    await initChat(pdfId, `/pdf/${pdfId}`, {
        scopingModel,
        extractionModel,
        targetLanguage: targetLang,
        pageOffset,
    });

    // Set header info after initChat so the chat shell can be injected on the fly
    // if an older cached HTML document is still mounted in the browser.
    const titleEl = document.getElementById("chat-doc-title");
    if (titleEl) titleEl.textContent = filename || "Document";
    const opEl = document.getElementById("chat-operator");
    if (opEl && operator) opEl.textContent = operator;

    if (uploadScreen) uploadScreen.hidden = true;
}

const uploadForm = document.getElementById("upload-form");
const uploadBtn = document.getElementById("upload-btn");
const uploadStatus = document.getElementById("upload-status");


uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    state.scopingModel = document.getElementById("scoping-model").value;
    state.modelName = document.getElementById("llm-model").value;
    state.targetLanguage = document.getElementById("graph-language").value;
    state.operator = document.getElementById("operator-name").value.trim();
    state.extractionDate = dateInput.value;
    const manualPage1PdfPage = parseInt(document.getElementById("startup-page-offset").value) || 1;
    state.pageOffset = Math.max(0, manualPage1PdfPage - 1);

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

        // ── Chat-first HITL transition ──────────────────────────────────
        // Store operator settings so the chat backend can use them
        try {
            await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    selected_scoping_model: state.scopingModel,
                    selected_extraction_model: state.modelName,
                    target_language: state.targetLanguage,
                    operator: state.operator,
                    page_offset: state.pageOffset,
                }),
            });
        } catch (_) {}

        // Persist operator info to the store via the chat start endpoint
        await _enterChatLayout(state.pdfId, loadData.filename, state.operator);
        return; // no further legacy logic needed

    } catch (err) {
        showStatus(err.message, "error");
        uploadBtn.disabled = false;
    }
});

function showStatus(msg, type) {
    renderStatus(uploadStatus, msg, type);
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
