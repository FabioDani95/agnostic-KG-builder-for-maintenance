(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  const outcomeLabel = {
    processed: "Elaborate",
    duplicate: "Duplicate",
    excluded: "Escluse",
    quarantined: "Da controllare",
    failed: "Fallite",
  };
  const outcomeHelp = {
    processed: "Elementi letti e conservati correttamente.",
    duplicate: "Elementi già presenti e quindi non conteggiati due volte.",
    excluded: "Elementi che hai escluso scegliendo le pagine.",
    quarantined: "Elementi messi da parte perché richiedono una verifica prima di poter essere usati.",
    failed: "Elementi che l’app non è riuscita a elaborare.",
  };
  const unitLabel = {
    block: "Blocchi di testo",
    table: "Tabelle rilevate",
    table_row: "Righe delle tabelle",
    ocr_region: "Regioni OCR",
  };
  const unitHelp = {
    block: "Testo letto direttamente dalla pagina.",
    table: "Contenitori strutturali delle tabelle trovate.",
    table_row: "Righe strutturate, con numero di tabella e di riga.",
    ocr_region: "Testo recuperato tramite riconoscimento ottico.",
  };
  const runLabel = {
    awaiting_review: "Pronto per il tuo controllo",
    processing: "Elaborazione in corso",
    ready: "Pronto per l’elaborazione",
    failed_resumable: "Interrotto, puoi riprovare",
    failed_terminal: "Interrotto, serve una nuova elaborazione",
  };

  function metric(label, value, outcome) {
    return `
      <div class="accounting-metric outcome-${escapeHtml(outcome)}">
        <strong>${escapeHtml(value)}</strong>
        <span class="label-with-info">${escapeHtml(label)} ${root.infoTip(`esito-${outcome}`, label, outcomeHelp[outcome] || "Esito assegnato dall’app a questi elementi.")}</span>
      </div>`;
  }

  function typeCounts(items) {
    const count = (kind) => items.filter((item) => item.unit_kind === kind).length;
    return {
      block: count("block"),
      table: count("table"),
      table_row: count("table_row"),
      ocr_region: count("ocr_region"),
    };
  }

  function rawUnitCard(item) {
    const disposition = item.disposition || {};
    const locator = item.locator || {};
    const quote = String(locator.quote || "").slice(0, 500);
    const searchable = [
      item.unit_kind,
      locator.page,
      locator.table_index,
      locator.row_index,
      disposition.outcome,
      disposition.reason_code,
      quote,
    ].join(" ").toLocaleLowerCase();
    const location = [
      `Pagina ${locator.page || "—"}`,
      locator.table_index ? `Tabella ${locator.table_index}` : null,
      locator.row_index ? `Riga ${locator.row_index}` : null,
    ].filter(Boolean).join(" · ");
    return `
      <article class="raw-unit-card" data-raw-search="${escapeHtml(searchable)}">
        <header>
          <span class="raw-unit-location">${escapeHtml(location)}</span>
          <span class="raw-unit-outcome outcome-${escapeHtml(disposition.outcome || "unclassified")}">
            ${escapeHtml(outcomeLabel[disposition.outcome] || "Non classificata")}
          </span>
        </header>
        <p>${escapeHtml(quote)}</p>
        <details>
          <summary>Dettagli tecnici</summary>
          <code>${escapeHtml(item.raw_unit_id)}</code>
          <p>${escapeHtml(disposition.reason_code || "")}</p>
        </details>
      </article>`;
  }

  function pageDetail(report, pageNumber) {
    const allPageUnits = report.raw_units.filter(
      (item) => Number(item.locator.page) === Number(pageNumber)
    );
    const children = allPageUnits.filter((item) => item.parent_raw_unit_id);
    const counts = typeCounts(children);
    const groups = ["block", "table", "table_row", "ocr_region"]
      .filter((kind) => counts[kind] > 0)
      .map((kind) => {
        const items = children.filter((item) => item.unit_kind === kind);
        return `
          <details class="raw-unit-group" data-unit-kind="${kind}">
            <summary>
              <span><strong>${escapeHtml(unitLabel[kind])}</strong><small>${escapeHtml(unitHelp[kind])}</small></span>
              <b>${items.length}</b>
            </summary>
            <div class="raw-unit-list">${items.map(rawUnitCard).join("")}</div>
          </details>`;
      }).join("");
    return `
      <div class="accounting-page-detail-heading">
        <div>
          <p class="kicker">Dettaglio pagina</p>
          <h4>Pagina ${escapeHtml(pageNumber)}</h4>
          <p>In questa pagina l’app ha trovato ${children.length} elementi: ${counts.block} blocchi di testo, ${counts.table} ${counts.table === 1 ? "tabella" : "tabelle"}, ${counts.table_row} righe${counts.ocr_region ? ` e ${counts.ocr_region} regioni lette con OCR` : ""}.</p>
        </div>
        <label class="accounting-search">
          Cerca in questa pagina
          <input type="search" placeholder="Parola, codice, tabella o riga" data-accounting-search>
        </label>
      </div>
      <p class="accounting-search-status" aria-live="polite">Apri una categoria oppure cerca un testo.</p>
      <div class="raw-unit-groups">${groups}</div>`;
  }

  function actionableFailure(item) {
    const disposition = item.disposition || {};
    const error = disposition.error || {};
    return `
      <article class="accounting-error">
        <strong>${escapeHtml(error.title || "Errore di elaborazione")}</strong>
        <p><b>Dove si trova:</b> ${escapeHtml(error.object_ref || item.raw_unit_id)}</p>
        <p><b>Perché è successo:</b> ${escapeHtml(error.cause || "Causa non disponibile")}</p>
        <p><b>Cosa è rimasto invariato:</b> ${escapeHtml(error.preserved || "Elementi e tentativi precedenti")}</p>
        <p><b>Cosa puoi fare:</b> ${escapeHtml(error.action || "Controlla il dettaglio e riprova")}</p>
        <details><summary>Dettaglio tecnico copiabile</summary><code>${escapeHtml(error.technical_detail || error.code || "")}</code></details>
        <small>Possibilità di riprovare: ${escapeHtml(disposition.retryability || "not_retryable")}</small>
      </article>`;
  }

  root.renderAccounting = function renderAccounting(preview) {
    const report = preview && preview.accounting;
    const run = preview && preview.run;
    if (!report || !run) return "";
    const source = report.sources[0] || {
      outcomes: {},
      top_level: {},
      child_aggregate: {},
      parent_groups: [],
    };
    const metrics = Object.entries(source.outcomes || {}).map(([outcome, value]) =>
      metric(outcomeLabel[outcome] || outcome, value, outcome)
    ).join("");
    const pageButtons = (source.parent_groups || [])
      .sort((left, right) => Number(left.parent_locator.page) - Number(right.parent_locator.page))
      .map((group) => {
        const page = Number(group.parent_locator.page);
        const children = report.raw_units.filter(
          (item) => item.parent_raw_unit_id === group.parent_raw_unit_id
        );
        const counts = typeCounts(children);
        return `
          <button class="accounting-page-button" type="button" data-accounting-page="${page}">
            <span>Pagina ${page}</span>
            <strong>${group.inventory} elementi</strong>
            <small>${counts.block} blocchi · ${counts.table} ${counts.table === 1 ? "tabella" : "tabelle"} · ${counts.table_row} righe</small>
            <em>${group.balanced ? "✓ Completa" : "⚠ Da controllare"}</em>
          </button>`;
      }).join("");
    const attention = report.attention || {};
    const retryable = attention.retryable_same_run || [];
    const newRun = attention.new_run_required || [];
    const terminal = attention.terminal_failures || [];
    const totalFailures = retryable.length + newRun.length + terminal.length;
    return `
      <section id="g1-accounting" class="accounting-report" tabindex="-1" aria-live="polite" data-testid="g1-accounting">
        <div class="foundation-step-heading">
          <span class="foundation-step-number">4</span>
          <div>
            <p class="kicker">Controllo del documento</p>
            <h3>Controlla che l’app abbia letto tutto</h3>
            <p>Scegli una pagina e confronta ciò che l’app ha trovato con il documento originale. Apri i dettagli tecnici soltanto se ti servono.</p>
          </div>
          <span class="pill accounting-state">${escapeHtml(runLabel[run.state] || run.state)}</span>
        </div>
        <div class="accounting-verdict ${report.balanced && report.unclassified_total === 0 ? "is-success" : "is-warning"}">
          <strong>${report.balanced && report.unclassified_total === 0 ? "✓ Controllo superato" : "⚠ Controllo richiesto"}</strong>
          <span>L’app ha assegnato un esito a ${source.classified} di ${source.inventory} elementi · ${report.unclassified_total} senza esito</span>
        </div>
        <div class="accounting-scope">
          <span class="accounting-scope-item"><b>${escapeHtml(source.top_level.inventory || 0)}</b> <span class="label-with-info">pagine del PDF ${root.infoTip("pagine-pdf", "Pagine del PDF", "È il numero delle pagine originali che hai incluso nel passaggio 3.")}</span></span>
          <span class="accounting-scope-item"><b>${escapeHtml(source.child_aggregate.inventory || 0)}</b> <span class="label-with-info">elementi trovati ${root.infoTip("elementi-trovati", "Elementi trovati", "Sono i blocchi di testo, le tabelle, le righe e le eventuali regioni OCR individuate dentro le pagine.")}</span></span>
          <span class="accounting-scope-item"><b>${escapeHtml(report.unclassified_total)}</b> <span class="label-with-info">senza esito ${root.infoTip("senza-esito", "Elementi senza esito", "Devono essere zero: significa che ogni elemento trovato è stato elaborato, escluso, riconosciuto come duplicato, messo da controllare oppure fallito.")}</span></span>
          <span class="accounting-scope-item"><b>${report.balanced ? "Sì" : "No"}</b> <span class="label-with-info">totali verificati ${root.infoTip("totali-verificati", "Totali verificati", "“Sì” significa che il numero degli elementi trovati coincide con la somma di tutti gli esiti mostrati qui sotto.")}</span></span>
        </div>
        <div class="accounting-metrics" aria-label="Esiti dell’elaborazione">${metrics}</div>
        <section class="accounting-page-picker" aria-labelledby="page-picker-title">
          <div>
            <p class="kicker">Esplora il risultato</p>
            <h4 id="page-picker-title">Scegli una delle ${source.top_level.inventory} pagine</h4>
          </div>
          <div class="accounting-page-buttons">${pageButtons}</div>
        </section>
        <div class="accounting-page-detail" data-accounting-page-detail>
          <p class="accounting-empty-state">↑ Seleziona una pagina per vedere blocchi, tabelle e righe.</p>
        </div>
        <section class="accounting-attention">
          <h4>${totalFailures ? "Elementi che richiedono attenzione" : "Nessun errore da gestire"}</h4>
          ${totalFailures ? `
            <details ${retryable.length ? "open" : ""}><summary>Puoi riprovare (${retryable.length})</summary>${retryable.map(actionableFailure).join("") || "<p>Nessun elemento.</p>"}</details>
            <details ${newRun.length ? "open" : ""}><summary>Serve una nuova elaborazione (${newRun.length})</summary>${newRun.map(actionableFailure).join("") || "<p>Nessun elemento.</p>"}</details>
            <details ${terminal.length ? "open" : ""}><summary>Errori che non puoi riprovare (${terminal.length})</summary>${terminal.map(actionableFailure).join("") || "<p>Nessun elemento.</p>"}</details>
          ` : `<p>Puoi continuare il controllo pagina per pagina.</p>`}
          <p class="label-with-info">${escapeHtml((attention.quarantined || []).length)} elementi da controllare ${root.infoTip("elementi-quarantena", "Elementi da controllare", "L’app li ha messi da parte perché non sono abbastanza affidabili per essere usati automaticamente.")} · ${escapeHtml((attention.excluded || []).length)} esclusi.</p>
        </section>
        <details class="foundation-technical">
          <summary>Dati tecnici dell’elaborazione</summary>
          <p>Identificativo elaborazione <code>${escapeHtml(run.run_id)}</code></p>
          <p>Identificativo documento <code>${escapeHtml(source.source_id)}</code></p>
          <p>Impronta del registro dei conteggi <code>${escapeHtml(report.ledger_hash)}</code></p>
        </details>
      </section>`;
  };

  function bindPageSearch(detail) {
    const search = detail.querySelector("[data-accounting-search]");
    if (!search) return;
    search.addEventListener("input", () => {
      const query = search.value.trim().toLocaleLowerCase();
      const cards = Array.from(detail.querySelectorAll(".raw-unit-card"));
      let visible = 0;
      cards.forEach((card) => {
        const matches = !query || card.dataset.rawSearch.includes(query);
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      detail.querySelectorAll(".raw-unit-group").forEach((group) => {
        const groupMatches = Array.from(group.querySelectorAll(".raw-unit-card"))
          .some((card) => !card.hidden);
        group.hidden = !groupMatches;
        if (query && groupMatches) group.open = true;
      });
      detail.querySelector(".accounting-search-status").textContent = query
        ? `${visible} risultati per “${search.value.trim()}”.`
        : "Apri una categoria oppure cerca un testo.";
    });
  }

  root.bindAccounting = function bindAccounting() {
    const report = root.state.preview && root.state.preview.accounting;
    const detail = document.querySelector("[data-accounting-page-detail]");
    if (!report || !detail) return;
    document.querySelectorAll("[data-accounting-page]").forEach((button) => {
      button.addEventListener("click", () => {
        document.querySelectorAll("[data-accounting-page]").forEach((item) => {
          item.classList.toggle("is-selected", item === button);
        });
        detail.innerHTML = pageDetail(report, Number(button.dataset.accountingPage));
        bindPageSearch(detail);
      });
    });
  };
})();
