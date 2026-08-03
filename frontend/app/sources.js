(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  state.sources = [];
  state.sourceBusy = false;
  state.sourceError = "";
  state.sourceErrorDetail = null;
  state.sourceSelectionValid = false;

  const supportedExtensions = new Set(["pdf", "csv", "xlsx", "json", "jsonl"]);
  const fileDigests = new WeakMap();

  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

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
      state.sources
        .filter((source) => source.source_kind !== "operator_input" && source.sha256)
        .map((source) => [source.sha256, source])
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

  root.renderSources = function renderSources() {
    if (!state.workspace) return "";
    const fileSources = state.sources.filter((source) => source.source_kind !== "operator_input");
    const rows = fileSources.map((source) => {
      return `
        <article class="foundation-source" data-source-id="${escapeHtml(source.source_id)}">
          <header>
            <div class="source-identity">
              <span class="source-file-type">${escapeHtml(source.source_kind.toUpperCase())}</span>
              <strong>${escapeHtml(source.file_name)}</strong>
            </div>
            <div class="source-actions">
              <span class="pill source-ready">Caricato</span>
              <button class="source-remove" type="button" data-source-id="${escapeHtml(source.source_id)}"
                aria-label="Rimuovi file ${escapeHtml(source.file_name)}" title="Rimuovi file"
                ${state.sourceBusy ? "disabled" : ""}>×</button>
            </div>
          </header>
          <details class="source-technical">
            <summary>Dettagli tecnici del file</summary>
            <p>Formato <code>${escapeHtml(source.source_kind)}</code> · Impronta digitale <code>${escapeHtml(source.sha256.slice(0, 12))}…</code> · Dimensione ${escapeHtml(source.size_bytes)} byte</p>
            <p>Classe interna <code>${escapeHtml(source.authority)}</code></p>
          </details>
        </article>`;
    }).join("");
    return `
      <section class="foundation-card foundation-sources">
        <div class="foundation-step-heading">
          <span class="foundation-step-number">2</span>
          <div>
            <p class="kicker">Documenti della macchina</p>
            <h2>Aggiungi i documenti</h2>
            <p>Carica tutti i file che vuoi. Il sistema accetta i formati supportati e blocca subito un documento già presente.</p>
          </div>
          <span class="pill source-count">${fileSources.length ? `${fileSources.length} file` : "Nessun file"}</span>
        </div>
        <form id="source-upload">
          <label class="source-file-picker">
            <span class="label-with-info">File da caricare ${root.infoTip("formati-documento", "Formati accettati", "Puoi scegliere uno o più file PDF, CSV, XLSX, JSON o JSONL.")}</span>
            <input type="file" name="file" required multiple accept=".pdf,.csv,.xlsx,.json,.jsonl">
            <span class="source-file-control">
              <b>Scegli file</b>
              <small data-source-file-name>Nessun file selezionato</small>
            </span>
          </label>
          <label class="source-authority"><span class="label-with-info">Che tipo di documento è? ${root.infoTip("tipo-documento", "Tipo di documento", "Normativa: prescrive regole. Osservazionale: registra misure o controlli. Operativa: descrive attività da eseguire. Informale: contiene appunti o indicazioni non ufficiali.")}</span>
            <select name="authority">
              <option value="normative">Normativa</option>
              <option value="observational">Osservazionale</option>
              <option value="operational">Operativa</option>
              <option value="informal">Informale</option>
            </select>
          </label>
          <button class="btn-primary" type="submit" ${(state.sourceBusy || !state.sourceSelectionValid) ? "disabled" : ""}>${state.sourceBusy ? "Caricamento…" : "Carica documento"}</button>
        </form>
        ${state.sourceError ? `
          <div class="foundation-error" role="alert">
            <strong>${escapeHtml(state.sourceError)}</strong>
            ${state.sourceErrorDetail ? `
              <p>${escapeHtml(state.sourceErrorDetail.cause)}</p>
              <p><b>Cosa è rimasto invariato:</b> ${escapeHtml(state.sourceErrorDetail.preserved)}</p>
              <p><b>Cosa puoi fare:</b> ${escapeHtml(state.sourceErrorDetail.action)}</p>
              <details><summary>Dettaglio tecnico</summary><code>${escapeHtml(state.sourceErrorDetail.technical_detail)}</code></details>
              <small>${escapeHtml(state.sourceErrorDetail.retryability)}</small>` : ""}
          </div>` : ""}
        <div class="foundation-source-list">${rows || '<p class="foundation-empty">Non hai ancora caricato documenti. Scegli un file qui sopra per iniziare.</p>'}</div>
        ${fileSources.length ? `
          <div class="documents-next-action">
            <div>
              <strong>I documenti ci sono</strong>
              <span>Il prossimo passo mostra come tabelle e colonne verranno interpretate prima di costruire il grafo.</span>
            </div>
            <a class="btn-primary" href="/console.html?foundation=1&amp;workspace_id=${encodeURIComponent(state.workspace.workspace.workspace_id)}&amp;stage=g2">Continua alla struttura dati</a>
          </div>` : ""}
      </section>`;
  };

  root.bindSources = function bindSources(render) {
    const upload = document.getElementById("source-upload");
    const fileInput = upload && upload.querySelector('input[type="file"]');
    const fileName = upload && upload.querySelector("[data-source-file-name]");
    const submitButton = upload && upload.querySelector('button[type="submit"]');
    if (fileInput && fileName) {
      fileInput.addEventListener("change", async () => {
        const files = Array.from(fileInput.files || []);
        state.sourceSelectionValid = false;
        if (submitButton) submitButton.disabled = true;
        if (!files.length) {
          fileName.textContent = "Nessun file selezionato";
          return;
        }
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
          render();
          return;
        }
        state.sourceError = "";
        state.sourceErrorDetail = null;
        document.querySelector(".foundation-error")?.remove();
        state.sourceSelectionValid = true;
        if (submitButton) submitButton.disabled = false;
        fileName.textContent = files.length > 1
          ? `${files.length} file selezionati`
          : files[0].name;
      });
    }
    if (upload) upload.addEventListener("submit", async (event) => {
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
        render();
        return;
      }
      state.sourceBusy = true;
      state.sourceSelectionValid = false;
      state.sourceError = "";
      state.sourceErrorDetail = null;
      render();
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
        render();
      }
    });
    document.querySelectorAll(".source-remove").forEach((button) => {
      button.addEventListener("click", async () => {
        const sourceId = button.dataset.sourceId;
        const source = state.sources.find((item) => item.source_id === sourceId);
        const fileName = source && source.file_name ? source.file_name : "questo file";
        if (!window.confirm(`Rimuovere “${fileName}”? Potrai ricaricarlo in seguito.`)) return;
        state.sourceBusy = true;
        state.sourceError = "";
        state.sourceErrorDetail = null;
        button.disabled = true;
        try {
          await root.api(`/api/sources/${sourceId}`, { method: "DELETE" });
          await root.loadSources();
        } catch (error) {
          state.sourceError = error.message;
          state.sourceErrorDetail = error.detail || null;
        } finally {
          state.sourceBusy = false;
          render();
        }
      });
    });
  };
})();
