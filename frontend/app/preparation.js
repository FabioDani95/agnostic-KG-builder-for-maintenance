(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  state.preview = null;
  state.previewError = "";
  state.previewLoading = false;

  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  const extractionLabels = {
    native_text: "Testo nativo",
    table: "Tabella",
    ocr: "OCR",
  };
  const extractionHelp = {
    native_text: "L’app ha letto il testo già incorporato nel PDF. Non è stato necessario interpretare un’immagine.",
    table: "L’app ha riconosciuto una tabella e ne ha separato la struttura dalle singole righe.",
    ocr: "L’app ha letto una scansione tramite riconoscimento ottico. Controlla con particolare attenzione l’anteprima.",
  };

  function pageCounts(pageNumber) {
    const units = (state.preview.raw_units || []).filter((item) => Number(item.locator.page) === Number(pageNumber));
    const count = (kind) => units.filter((item) => item.unit_kind === kind).length;
    return {
      blocks: count("block"),
      tables: count("table"),
      rows: count("table_row"),
      ocr: count("ocr_region"),
    };
  }

  function pageCard(page) {
    const counts = pageCounts(page.page);
    const scope = state.preview.current_scope || {};
    const excludedReason = (scope.excluded_pages || {})[String(page.page)] || "";
    return `
      <article class="scope-page-card ${page.included ? "is-included" : "is-excluded"}" data-scope-page="${page.page}">
        <div class="scope-page-heading">
          <input id="scope-page-${page.page}" type="checkbox" name="page" value="${page.page}" ${page.included ? "checked" : ""}>
          <label for="scope-page-${page.page}">
            <strong>Pagina ${page.page}</strong>
            <span>${escapeHtml(extractionLabels[page.extraction_method] || page.extraction_method)}</span>
            ${root.infoTip(
              `lettura-pagina-${page.page}`,
              extractionLabels[page.extraction_method] || "Metodo di lettura",
              extractionHelp[page.extraction_method] || "Indica il modo in cui l’app ha letto il contenuto della pagina."
            )}
          </label>
          <span class="scope-page-status">${page.included ? "Inclusa" : "Esclusa"}</span>
        </div>
        <div class="scope-page-counts" aria-label="Contenuto rilevato nella pagina ${page.page}">
          <span><b>${counts.blocks}</b> blocchi di testo</span>
          <span><b>${counts.tables}</b> ${counts.tables === 1 ? "tabella" : "tabelle"}</span>
          <span><b>${counts.rows}</b> righe tabella</span>
          ${counts.ocr ? `<span><b>${counts.ocr}</b> regioni OCR</span>` : ""}
        </div>
        <details class="scope-page-preview">
          <summary>Vedi anteprima del contenuto</summary>
          <pre>${escapeHtml(String(page.text || "").slice(0, 1600))}</pre>
        </details>
        <label class="scope-exclusion-reason" ${page.included ? "hidden" : ""}>
          Perché escludi questa pagina?
          <input name="exclude_reason_${page.page}" value="${escapeHtml(excludedReason)}"
            placeholder="Esempio: pagina commerciale non pertinente" ${page.included ? "" : "required"}>
        </label>
      </article>`;
  }

  root.openPdfPreview = async function openPdfPreview(sourceId, render) {
    state.previewError = "";
    state.previewLoading = true;
    render();
    try {
      state.preview = await root.api(`/api/sources/${sourceId}/pdf/preview`);
      state.previewLoading = false;
      render({ scrollToId: "scope-title" });
    } catch (error) {
      state.previewError = error.message;
      state.previewLoading = false;
      render();
    }
  };

  root.renderPreparation = function renderPreparation() {
    if (!state.preview) return "";
    const scope = state.preview.current_scope;
    const pages = state.preview.pages.map(pageCard).join("");
    const includedCount = state.preview.pages.filter((page) => page.included).length;
    const excludedCount = state.preview.pages.length - includedCount;
    const operator = scope && scope.operator
      ? scope.operator
      : (state.workspace && state.workspace.assertion && state.workspace.assertion.operator) || "";
    return `
      <section class="foundation-card foundation-preparation" aria-labelledby="scope-title">
        <div class="foundation-step-heading">
          <span class="foundation-step-number">3</span>
          <div>
            <p class="kicker">Preparazione PDF</p>
            <h2 id="scope-title" tabindex="-1">Controlla le pagine proposte</h2>
            <p>La pipeline ha già letto il PDF e ha preparato una selezione iniziale. Modificala soltanto se trovi pagine non utili.</p>
          </div>
          <span class="pill scope-state ${scope ? "is-approved" : ""}">
            ${scope ? `Hai approvato la selezione · v${scope.version}` : "Devi approvare"}
          </span>
        </div>
        <form id="pdf-scope" data-source-id="${state.preview.source_id}">
          <div class="scope-toolbar">
            <strong class="label-with-info">Documento: ${state.preview.pages.length} pagine ${root.infoTip("conteggi-pagina", "Cosa viene contato", "Per ogni pagina vedi quanti blocchi di testo, tabelle e righe di tabella ha trovato l’app. Sono elementi separati che potrai controllare nel passaggio 4.")}</strong>
            <span id="scope-selection-count" aria-live="polite">${includedCount} incluse · ${excludedCount} escluse</span>
          </div>
          <div class="scope-proposal" role="status">
            <strong>${scope ? "Selezione salvata" : "Proposta automatica pronta"}</strong>
            <span>
              ${includedCount === state.preview.pages.length
                ? `La pipeline ha preselezionato tutte le ${includedCount} pagine. Non devi spuntarle una per una: controlla la proposta e approvala.`
                : `La pipeline propone ${includedCount} pagine incluse e ${excludedCount} escluse. Controlla la proposta e approvala.`}
            </span>
          </div>
          <div class="scope-action">
            <div>
              <label><span class="label-with-info">Inserisci chi approva la selezione ${root.infoTip("approvatore-pagine", "Chi approva", "Scrivi il tuo nome o le tue iniziali. L’app li conserva insieme alla scelta delle pagine.")}</span>
                <input name="operator" required value="${escapeHtml(operator)}" placeholder="Nome o iniziali">
              </label>
              <small>Quando salvi, ritroverai la scelta anche dopo aver ricaricato la pagina.</small>
            </div>
            <button class="btn-primary" type="submit">
              ${scope ? "Salva una nuova selezione" : "Approva la proposta e continua"}
            </button>
          </div>
          <div class="scope-list-heading">
            <strong>Controlla pagina per pagina</strong>
            <span>Togli la spunta solo alle pagine che non devono entrare nell’elaborazione.</span>
          </div>
          <div class="scope-page-list">${pages}</div>
        </form>
        <details class="foundation-technical">
          <summary>Dettagli tecnici dell’inventario</summary>
          <p>${state.preview.raw_units.length} elementi trovati nel PDF · ${state.preview.evidence_units.length} elementi utilizzabili nel controllo.</p>
          <p><code>RawUnit</code> indica un elemento letto dal file. <code>EvidenceUnit</code> indica un elemento ammesso nel controllo dopo la scelta delle pagine.</p>
        </details>
        ${root.renderAccounting ? root.renderAccounting(state.preview) : ""}
        ${state.previewError ? `<p class="foundation-error" role="alert">${escapeHtml(state.previewError)}</p>` : ""}
      </section>`;
  };

  root.bindPreparation = function bindPreparation(render) {
    document.querySelectorAll(".preview-pdf").forEach((button) => {
      button.addEventListener("click", () => root.openPdfPreview(button.dataset.sourceId, render));
    });
    const form = document.getElementById("pdf-scope");
    if (root.bindAccounting) root.bindAccounting();
    if (!form) return;

    const updateSelection = () => {
      const checkboxes = Array.from(form.querySelectorAll('input[name="page"]'));
      let included = 0;
      checkboxes.forEach((checkbox) => {
        const card = checkbox.closest(".scope-page-card");
        const reason = card.querySelector(".scope-exclusion-reason");
        const reasonInput = reason.querySelector("input");
        const status = card.querySelector(".scope-page-status");
        card.classList.toggle("is-included", checkbox.checked);
        card.classList.toggle("is-excluded", !checkbox.checked);
        reason.hidden = checkbox.checked;
        reasonInput.required = !checkbox.checked;
        status.textContent = checkbox.checked ? "Inclusa" : "Esclusa";
        if (checkbox.checked) included += 1;
      });
      document.getElementById("scope-selection-count").textContent =
        `${included} incluse · ${checkboxes.length - included} escluse`;
      form.querySelector('button[type="submit"]').disabled = included === 0;
    };

    form.querySelectorAll('input[name="page"]').forEach((checkbox) => {
      checkbox.addEventListener("change", updateSelection);
    });
    updateSelection();

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = new FormData(form);
      const included = values.getAll("page").map(Number);
      const allPages = state.preview.pages.map((page) => Number(page.page));
      const excluded = Object.fromEntries(
        allPages
          .filter((page) => !included.includes(page))
          .map((page) => [page, String(values.get(`exclude_reason_${page}`) || "").trim()])
      );
      state.previewError = "";
      try {
        state.preview = await root.api(`/api/sources/${form.dataset.sourceId}/pdf/scope`, {
          method: "POST",
          body: {
            included_pages: included,
            excluded_pages: excluded,
            operator: values.get("operator"),
          },
        });
        render({ scrollToId: "g1-accounting" });
      } catch (error) {
        state.previewError = error.message;
        render();
      }
    });
  };
})();
