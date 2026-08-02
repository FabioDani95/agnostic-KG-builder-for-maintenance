(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  state.sources = [];
  state.sourceBusy = false;
  state.sourceError = "";
  state.sourceErrorDetail = null;

  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
  const claimLabel = {
    serial: "Numero seriale trovato",
    equipment_tag: "Codice macchina trovato",
    model: "Modello trovato",
    brand: "Marca trovata",
  };
  const outcomeHelp = {
    compatible: "L’app ha trovato nel file elementi coerenti con la macchina. Puoi proseguire.",
    uncertain: "L’app non ha trovato prove sufficienti. Controlla il file e decidi se appartiene alla macchina.",
    incompatible: "L’app ha trovato elementi in conflitto con la macchina. Il file non verrà usato finché non correggi la decisione.",
  };

  root.loadSources = async function loadSources() {
    if (!state.workspace) return;
    state.sources = await root.api(`/api/workspaces/${state.workspace.workspace.workspace_id}/sources`);
  };

  root.renderSources = function renderSources() {
    if (!state.workspace) return "";
    const fileSources = state.sources.filter((source) => source.source_kind !== "operator_input");
    const acceptedStructured = fileSources.filter(
      (source) => source.status === "accepted" && source.source_kind !== "pdf"
    );
    const hasAcceptedPdf = fileSources.some(
      (source) => source.status === "accepted" && source.source_kind === "pdf"
    );
    const hasPendingSource = fileSources.some((source) => source.status === "quarantined");
    const structuredReady = acceptedStructured.length > 0 && !hasAcceptedPdf && !hasPendingSource;
    const structuredFormats = [...new Set(
      acceptedStructured.map((source) => source.source_kind.toUpperCase())
    )].join(", ");
    const rows = fileSources.map((source) => {
      const assessment = source.active_assessment || {};
      const signals = (assessment.observed_claims || []).map((claim) =>
        `<li><strong>${escapeHtml(claimLabel[claim.claim_kind] || "Dato trovato")}</strong>: ${escapeHtml(claim.raw_value)} · pagina ${escapeHtml(claim.locator.page || "—")}<br><small>${escapeHtml(claim.locator.quote || "")}</small></li>`
      ).join("");
      const uncertain = assessment.outcome === "uncertain" && source.status === "quarantined";
      const reopen = assessment.decided_by && assessment.decided_by.kind === "operator_assertion";
      const outcome = {
        compatible: "Compatibile",
        uncertain: "Da confermare",
        incompatible: "Non compatibile",
      }[assessment.outcome] || assessment.outcome;
      const sourceStatus = {
        accepted: "Pronto",
        quarantined: "In attesa",
        excluded: "Escluso",
      }[source.status] || source.status;
      const guidance = assessment.outcome === "compatible"
        ? (
          source.source_kind === "pdf"
            ? "Apri la proposta automatica di pagine, controllala e approvala."
            : "Hai associato il file alla macchina. Non devi scegliere pagine: i file strutturati contengono righe o record. In G1 questo file è pronto."
        )
        : "Controlla il file: l’app non può ancora confermare da sola che appartenga a questa macchina.";
      return `
        <article class="foundation-source" data-source-id="${escapeHtml(source.source_id)}">
          <header>
            <div>
              <span class="source-file-type">${escapeHtml(source.source_kind.toUpperCase())}</span>
              <strong>${escapeHtml(source.file_name)}</strong>
            </div>
            <span class="source-assessment">
              <span class="pill source-${escapeHtml(assessment.outcome)}">${escapeHtml(outcome)}</span>
              ${root.infoTip(`esito-${source.source_id}`, outcome, outcomeHelp[assessment.outcome] || "Questo stato indica l’esito del controllo automatico del documento.")}
            </span>
          </header>
          <p><strong>Cosa devi fare:</strong> ${escapeHtml(guidance)} <span class="source-status-note">Stato del file: ${escapeHtml(sourceStatus)}.</span></p>
          ${signals ? `<details><summary>Vedi perché l’app ha associato il documento alla macchina</summary><ul>${signals}</ul></details>` : ""}
          ${uncertain ? `
            <p class="source-decision-note">Controlla il file e conferma soltanto se contiene dati della macchina mostrata al punto 1.</p>
            <form class="assessment-resolution">
              <label>Come hai verificato che appartiene alla macchina?
                <input name="reason" required minlength="10" placeholder="Esempio: seriale verificato nel file">
              </label>
              <label>Inserisci chi verifica<input name="operator" required placeholder="Nome o iniziali"></label>
              <button type="submit" data-action="confirm">Conferma associazione</button>
              <button type="submit" data-action="exclude">Escludi documento</button>
            </form>` : ""}
          ${reopen ? '<button class="reopen-assessment btn-ghost">Modifica la decisione</button>' : ""}
          ${source.source_kind === "pdf" && source.status === "accepted" ? `
            <button class="preview-pdf btn-primary" data-source-id="${escapeHtml(source.source_id)}"
              ${state.previewLoading ? 'disabled aria-busy="true"' : ""}>
              ${state.previewLoading ? "Analisi del PDF in corso…" : "Controlla le pagine proposte"}
            </button>` : ""}
          <details class="source-technical">
            <summary>Dettagli tecnici del file</summary>
            <p>Formato <code>${escapeHtml(source.source_kind)}</code> · Impronta digitale <code>${escapeHtml(source.sha256.slice(0, 12))}…</code> · Dimensione ${escapeHtml(source.size_bytes)} byte</p>
            <p>Classe interna <code>${escapeHtml(source.authority)}</code> · Motivi del controllo <code>${escapeHtml((assessment.reason_codes || []).join(", "))}</code></p>
          </details>
        </article>`;
    }).join("");
    return `
      <section class="foundation-card foundation-sources">
        <div class="foundation-step-heading">
          <span class="foundation-step-number">2</span>
          <div>
            <p class="kicker">Documenti della macchina</p>
            <h2>Aggiungi i documenti da controllare</h2>
            <p>Carica un documento della macchina. Se scegli un PDF, controllerai le pagine da usare. Se scegli CSV, XLSX, JSON o JSONL, confermerai che il file appartiene alla macchina.</p>
          </div>
          <span class="pill source-count">${fileSources.length ? `${fileSources.length} file` : "Nessun file"}</span>
        </div>
        <form id="source-upload">
          <label class="source-file-picker">
            <span class="label-with-info">File da caricare ${root.infoTip("formati-documento", "Formati accettati", "Puoi scegliere PDF, CSV, XLSX, JSON o JSONL. In questo passaggio selezioni le pagine dei PDF; gli altri formati restano associati alla macchina.")}</span>
            <input type="file" name="file" required accept=".pdf,.csv,.xlsx,.json,.jsonl">
            <span class="source-file-control">
              <b>Scegli un file</b>
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
          <button class="btn-primary" type="submit" ${state.sourceBusy ? "disabled" : ""}>${state.sourceBusy ? "Caricamento…" : "Carica documento"}</button>
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
        ${state.previewError ? `<p class="foundation-error" role="alert">Non è stato possibile preparare le pagine del PDF: ${escapeHtml(state.previewError)}. Puoi riprovare dallo stesso pulsante.</p>` : ""}
        ${structuredReady ? `
          <section class="structured-ready" role="status" data-testid="structured-g1-ready">
            <span class="structured-ready-check" aria-hidden="true">✓</span>
            <div>
              <p class="kicker">Preparazione G1 completata</p>
              <h3>${acceptedStructured.length === 1 ? "Il file è pronto" : "I file sono pronti"}: non ci sono pagine da scegliere</h3>
              <p>${escapeHtml(structuredFormats)} contiene righe o record, non pagine PDF. Hai completato tutto ciò che è disponibile in G1 per ${acceptedStructured.length === 1 ? "questo documento" : "questi documenti"}.</p>
              <p><strong>Passaggio successivo:</strong> la lettura e il collegamento delle righe saranno disponibili in G2. In questa schermata non devi premere altro.</p>
            </div>
            <span class="pill structured-ready-next">Righe · G2</span>
          </section>` : ""}
      </section>`;
  };

  root.bindSources = function bindSources(render) {
    const upload = document.getElementById("source-upload");
    const fileInput = upload && upload.querySelector('input[type="file"]');
    const fileName = upload && upload.querySelector("[data-source-file-name]");
    if (fileInput && fileName) {
      fileInput.addEventListener("change", () => {
        fileName.textContent = fileInput.files.length
          ? fileInput.files[0].name
          : "Nessun file selezionato";
      });
    }
    if (upload) upload.addEventListener("submit", async (event) => {
      event.preventDefault();
      state.sourceBusy = true;
      state.sourceError = "";
      state.sourceErrorDetail = null;
      render();
      try {
        const body = new FormData(event.currentTarget);
        await root.api(`/api/workspaces/${state.workspace.workspace.workspace_id}/sources`, { method: "POST", body });
        await root.loadSources();
      } catch (error) {
        state.sourceError = error.message;
        state.sourceErrorDetail = error.detail || null;
      } finally {
        state.sourceBusy = false;
        render();
      }
    });
    document.querySelectorAll(".assessment-resolution").forEach((form) => {
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const action = event.submitter.dataset.action;
        const sourceId = form.closest("[data-source-id]").dataset.sourceId;
        const values = new FormData(form);
        try {
          await root.api(`/api/sources/${sourceId}/assessment/resolve`, {
            method: "POST",
            body: {
              action,
              reason: values.get("reason"),
              observation_basis: "direct_observation",
              operator: values.get("operator"),
              evidence_seen: [state.sources.find((item) => item.source_id === sourceId).asset_assessment_id],
            },
          });
          await root.loadSources();
          render();
        } catch (error) {
          state.sourceError = error.message;
          state.sourceErrorDetail = error.detail || null;
          render();
        }
      });
    });
    document.querySelectorAll(".reopen-assessment").forEach((button) => {
      button.addEventListener("click", async () => {
        const sourceId = button.closest("[data-source-id]").dataset.sourceId;
        try {
          await root.api(`/api/sources/${sourceId}/assessment/reopen`, { method: "POST" });
          await root.loadSources();
          render();
        } catch (error) {
          state.sourceError = error.message;
          state.sourceErrorDetail = error.detail || null;
          render();
        }
      });
    });
  };
})();
