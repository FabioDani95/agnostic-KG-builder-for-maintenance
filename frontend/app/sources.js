(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  state.sourceBusy = false;
  state.sourceError = "";
  state.sourceErrorDetail = null;
  state.sourceSelectionValid = false;

  const supportedExtensions = new Set(["pdf", "csv", "xlsx", "json", "jsonl"]);
  const fileDigests = new WeakMap();

  const AUTHORITY_LABELS = {
    normative: "Normativa",
    observational: "Osservazionale",
    operational: "Operativa",
    informal: "Informale",
  };

  /* ── Client-side checks: a file the operator cannot use never leaves the
        browser, and the error says what is still intact. ───────────────── */

  const selectionError = (title, cause, action, technicalDetail) => ({
    title,
    detail: {
      cause,
      preserved: "Il file non è stato inviato e i documenti già caricati non sono stati modificati.",
      action,
      technical_detail: technicalDetail,
      retryability: "Puoi scegliere subito un altro file.",
    },
  });

  const extensionOf = (fileName) => {
    const parts = String(fileName || "").toLowerCase().split(".");
    return parts.length > 1 ? parts.pop() : "";
  };

  const digestFile = async (file) => {
    if (!fileDigests.has(file)) {
      fileDigests.set(file, window.crypto.subtle.digest("SHA-256", await file.arrayBuffer()).then((buffer) => (
        Array.from(new Uint8Array(buffer), (byte) => byte.toString(16).padStart(2, "0")).join("")
      )));
    }
    return fileDigests.get(file);
  };

  const validateSelection = async (files) => {
    const unsupported = files.find((file) => !supportedExtensions.has(extensionOf(file.name)));
    if (unsupported) {
      return selectionError(
        "Formato non supportato",
        `“${unsupported.name}” non è un file ammesso.`,
        "Scegli un file PDF, CSV, XLSX, JSON o JSONL.",
        `UNSUPPORTED_SOURCE_SUFFIX .${extensionOf(unsupported.name) || "missing"}`
      );
    }
    const activeByDigest = new Map(
      root.fileSources().filter((source) => source.sha256).map((source) => [source.sha256, source])
    );
    const selectedByDigest = new Map();
    for (const file of files) {
      const digest = await digestFile(file);
      const activeSource = activeByDigest.get(digest);
      if (activeSource) {
        return selectionError(
          "Documento già caricato",
          `“${file.name}” coincide con “${activeSource.file_name}”, già presente nell’elenco.`,
          "Non serve caricarlo di nuovo. Se vuoi sostituirlo, rimuovi prima il documento presente.",
          `DUPLICATE_SOURCE_SHA256 ${digest}`
        );
      }
      if (selectedByDigest.has(digest)) {
        return selectionError(
          "Documento selezionato due volte",
          `“${file.name}” e “${selectedByDigest.get(digest)}” hanno lo stesso contenuto.`,
          "Mantieni una sola copia nella selezione e riprova.",
          `DUPLICATE_SELECTION_SHA256 ${digest}`
        );
      }
      selectedByDigest.set(digest, file.name);
    }
    return null;
  };

  root.loadSources = async function loadSources() {
    if (!state.workspace) return;
    state.sources = await root.api(`/api/workspaces/${state.workspace.workspace.workspace_id}/sources`);
  };

  /* ── Phase controller ──────────────────────────────────────────────── */

  const errorBlock = () => (state.sourceError ? `
    <div class="kg-note kg-note-danger" role="alert">
      <span class="kg-note-mark" aria-hidden="true">!</span>
      <strong>${escapeHtml(state.sourceError)}</strong>
      ${state.sourceErrorDetail ? `
        <span>${escapeHtml(state.sourceErrorDetail.cause)}</span>
        <span><b>Cosa è rimasto invariato:</b> ${escapeHtml(state.sourceErrorDetail.preserved)}</span>
        <span><b>Cosa puoi fare:</b> ${escapeHtml(state.sourceErrorDetail.action)}</span>
        <span>${escapeHtml(state.sourceErrorDetail.retryability)}</span>
        <details class="kg-disclosure"><summary>Dettaglio tecnico</summary>
          <pre class="kg-evidence-raw">${escapeHtml(state.sourceErrorDetail.technical_detail)}</pre></details>` : ""}
    </div>` : "");

  root.phases.documents = {
    label: "Documenti",
    showRail: true,
    showInspector: true,

    railFacts(source) {
      return root.railFacts(
        [{ text: AUTHORITY_LABELS[source.authority] || "Documento" }],
        root.railBadge("Caricato", "success")
      );
    },

    renderWork() {
      if (!state.workspace) {
        return `<div class="kg-state"><strong>Prima identifica la macchina</strong>
          <p>I documenti appartengono a una macchina: salvala per poterli caricare.</p>
          <button type="button" class="kg-btn kg-btn-primary" data-kg-goto="machine">Vai alla macchina</button></div>`;
      }
      const sources = root.fileSources();
      return `
        <div class="kg-work-head">
          <div class="kg-work-head-row"><h1>Documenti della macchina</h1></div>
          <p>Carica i manuali e i registri che riguardano questa macchina. Un documento già presente viene bloccato prima dell'invio.</p>
        </div>
        <div class="kg-work-scroll"><div class="kg-work-pad">
          <form class="kg-upload" id="source-upload">
            <label class="kg-file-picker">
              <span class="kg-label-with-info">File da caricare ${root.infoTip("formati-documento", "Formati accettati", "Puoi scegliere uno o più file PDF, CSV, XLSX, JSON o JSONL.")}</span>
              <input type="file" name="file" required multiple accept=".pdf,.csv,.xlsx,.json,.jsonl">
              <span class="kg-file-control">
                <b>Scegli file</b>
                <small data-source-file-name>Nessun file selezionato</small>
              </span>
            </label>
            <label class="kg-field">
              <span class="kg-label-with-info">Che tipo di documento è? ${root.infoTip("tipo-documento", "Tipo di documento", "Normativa: prescrive regole. Osservazionale: registra misure o controlli. Operativa: descrive attività da eseguire. Informale: contiene appunti o indicazioni non ufficiali.")}</span>
              <select class="kg-select" name="authority">
                ${Object.entries(AUTHORITY_LABELS).map(([value, label]) => `<option value="${value}">${escapeHtml(label)}</option>`).join("")}
              </select>
            </label>
            <button type="submit" class="kg-btn kg-btn-primary"
              ${(state.sourceBusy || !state.sourceSelectionValid) ? "disabled" : ""}>${state.sourceBusy ? "Caricamento…" : "Carica documento"}</button>
          </form>
          ${errorBlock()}
          <div class="kg-list" style="margin-top: var(--space-4)">
            ${sources.length ? sources.map((source) => `
              <div class="kg-doc" data-source-id="${escapeHtml(source.source_id)}">
                <div class="kg-doc-identity">
                  <strong>${escapeHtml(source.file_name)}</strong>
                  <span class="kg-caption">${escapeHtml(String(source.source_kind).toUpperCase())} · ${escapeHtml(AUTHORITY_LABELS[source.authority] || source.authority)}</span>
                </div>
                <div class="kg-doc-actions">
                  <button type="button" class="kg-btn kg-btn-quiet kg-btn-small" data-kg-inspect="${escapeHtml(source.source_id)}"
                    aria-label="Dettagli di ${escapeHtml(source.file_name)}">Dettagli</button>
                  <button type="button" class="kg-btn kg-btn-danger kg-btn-small source-remove" data-source-id="${escapeHtml(source.source_id)}"
                    aria-label="Rimuovi file ${escapeHtml(source.file_name)}"
                    ${state.sourceBusy ? "disabled" : ""}>Rimuovi</button>
                </div>
              </div>`).join("")
              : `<div class="kg-empty"><strong>Nessun documento</strong><p>Scegli un file qui sopra per iniziare.</p></div>`}
          </div>
        </div></div>`;
    },

    bindWork(container) {
      root.delegate(container, "click", "[data-kg-goto]", (element) => root.goToPhase(element.dataset.kgGoto));
      root.delegate(container, "click", "[data-kg-inspect]", (element) => {
        root.setActiveSource(element.dataset.kgInspect);
        root.applySelection("source", element.dataset.kgInspect);
      });

      const upload = container.querySelector("#source-upload");
      if (!upload) return;
      const fileInput = upload.querySelector('input[type="file"]');
      const fileName = upload.querySelector("[data-source-file-name]");
      const submitButton = upload.querySelector('button[type="submit"]');

      fileInput.addEventListener("change", async () => {
        const files = Array.from(fileInput.files || []);
        state.sourceSelectionValid = false;
        submitButton.disabled = true;
        if (!files.length) { fileName.textContent = "Nessun file selezionato"; return; }
        fileName.textContent = "Controllo dei file…";
        let issue;
        try {
          issue = await validateSelection(files);
        } catch (error) {
          issue = selectionError(
            "Impossibile controllare il file",
            "Il browser non è riuscito a calcolare l’impronta del documento.",
            "Seleziona nuovamente il file e riprova.",
            `CLIENT_FILE_DIGEST_FAILED ${error.message}`
          );
        }
        if (issue) {
          state.sourceError = issue.title;
          state.sourceErrorDetail = issue.detail;
          fileInput.value = "";
          root.render({ regions: ["work"] });
          return;
        }
        state.sourceError = "";
        state.sourceErrorDetail = null;
        container.querySelector(".kg-note-danger")?.remove();
        state.sourceSelectionValid = true;
        submitButton.disabled = false;
        fileName.textContent = files.length > 1 ? `${files.length} file selezionati` : files[0].name;
      });

      upload.addEventListener("submit", async (event) => {
        event.preventDefault();
        const files = Array.from(fileInput.files || []);
        const authority = upload.querySelector('[name="authority"]').value;
        if (!files.length) return;
        const issue = await validateSelection(files);
        if (issue) {
          state.sourceSelectionValid = false;
          state.sourceError = issue.title;
          state.sourceErrorDetail = issue.detail;
          fileInput.value = "";
          root.render({ regions: ["work"] });
          return;
        }
        state.sourceBusy = true;
        state.sourceSelectionValid = false;
        state.sourceError = "";
        state.sourceErrorDetail = null;
        root.render({ regions: ["work"] });
        try {
          for (const file of files) {
            const body = new FormData();
            body.append("file", file);
            body.append("authority", authority);
            await root.api(`/api/workspaces/${state.workspace.workspace.workspace_id}/sources`, { method: "POST", body });
          }
          await root.loadSources();
        } catch (error) {
          state.sourceError = error.message;
          state.sourceErrorDetail = error.detail || null;
        } finally {
          state.sourceBusy = false;
          root.render();
        }
      });

      root.delegate(container, "click", ".source-remove", async (element) => {
        const sourceId = element.dataset.sourceId;
        const source = state.sources.find((item) => item.source_id === sourceId);
        const label = source && source.file_name ? source.file_name : "questo file";
        if (!window.confirm(`Rimuovere “${label}”? Potrai ricaricarlo in seguito.`)) return;
        state.sourceBusy = true;
        state.sourceError = "";
        state.sourceErrorDetail = null;
        element.disabled = true;
        try {
          await root.api(`/api/sources/${sourceId}`, { method: "DELETE" });
          await root.loadSources();
        } catch (error) {
          state.sourceError = error.message;
          state.sourceErrorDetail = error.detail || null;
        } finally {
          state.sourceBusy = false;
          root.render();
        }
      });
    },

    renderInspector() {
      const source = root.activeSource();
      if (!source) {
        return `<div class="kg-inspector-empty"><strong>Nessun documento</strong><p>Carica un file per vederne i dettagli.</p></div>`;
      }
      return `
        <div class="kg-inspector-inner">
          <button type="button" class="kg-btn kg-btn-quiet kg-btn-small kg-inspector-close" data-kg-inspector-close>Chiudi dettaglio</button>
          <div class="kg-inspector-identity">
            <span class="kg-inspector-kind">Documento</span>
            <h2>${escapeHtml(source.file_name)}</h2>
          </div>
          <section class="kg-block">
            <h3>Come sarà usato</h3>
            <p class="kg-secondary">${escapeHtml({
              normative: "Documento normativo: prescrive regole e prevale sulle osservazioni.",
              observational: "Documento osservazionale: registra misure e controlli reali.",
              operational: "Documento operativo: descrive attività da eseguire.",
              informal: "Documento informale: contiene appunti non ufficiali.",
            }[source.authority] || "Documento della macchina.")}</p>
          </section>
          <section class="kg-block">
            <h3>Dimensione</h3>
            <p class="kg-secondary">${escapeHtml(`${(Number(source.size_bytes || 0) / 1024).toFixed(1)} kB`)}</p>
          </section>
          <details class="kg-disclosure">
            <summary>Dati tecnici del file</summary>
            <p class="kg-secondary">Impronta digitale del contenuto</p>
            <pre class="kg-evidence-raw">${escapeHtml(source.sha256)}</pre>
          </details>
        </div>`;
    },

    renderDecision() {
      if (!state.workspace) return "";
      const total = root.fileSources().length;
      if (!total) {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>Nessun documento caricato</strong>
          <span>Serve almeno un file per costruire il grafo di questa macchina.</span>
        </div></div>`;
      }
      return `<div class="kg-decision-row"><div class="kg-decision-text">
        <strong>${escapeHtml(root.plural(total, "documento caricato", "documenti caricati"))}</strong>
        <span>Il passo successivo mostra come tabelle e colonne sono state interpretate, prima di costruire qualsiasi grafo.</span>
      </div>
      <div class="kg-decision-actions">
        <button type="button" class="kg-btn kg-btn-primary" data-kg-goto="structure">Continua alla struttura</button>
      </div></div>`;
    },

    bindDecision(container) {
      root.delegate(container, "click", "[data-kg-goto]", (element) => root.goToPhase(element.dataset.kgGoto));
    },
  };
})();
