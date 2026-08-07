(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const esc = root.escapeHtml;
  const t = root.t;
  const n = root.n;

  state.sourceBusy = false;
  state.sourceError = "";
  state.sourceErrorDetail = null;
  state.sourceSelectionValid = false;

  const ESTENSIONI = new Set(["pdf", "csv", "xlsx", "json", "jsonl"]);
  const AUTORITA = ["normative", "observational", "operational", "informal"];
  const impronte = new WeakMap();

  /* --------------------------------------------------------- fonti attive */
  root.fileSorgenti = () => (state.sources || []).filter((s) => s.source_kind !== "operator_input");

  root.fonteAttiva = function fonteAttiva() {
    const fonti = root.fileSorgenti();
    if (!fonti.length) return null;
    return fonti.find((f) => f.source_id === state.activeSourceId) || fonti[0];
  };

  root.scegliFonte = function scegliFonte(sourceId) {
    if (state.activeSourceId === sourceId) return;
    state.activeSourceId = sourceId;
    root.clearSelection();
    state.rejectingSourceId = "";
    if (state.view === "confronto") state.view = "mappa";
    if (root.rememberWorkspaceContext) root.rememberWorkspaceContext();
    if (root.syncWorkspaceUrl) root.syncWorkspaceUrl();
    root.render();
  };

  root.caricaFonti = async function caricaFonti() {
    if (!state.workspace) return;
    state.sources = await root.api(`/api/workspaces/${state.workspace.workspace.workspace_id}/sources`);
  };

  /* ------ controlli lato browser: un file inutilizzabile non parte mai ---- */
  const problema = (titolo, causa, azione, dettaglio) => ({
    titolo,
    dettaglio: { causa, invariato: t("err.invariato"), azione, tecnico: dettaglio, ritenta: t("err.ritenta") },
  });

  const estensione = (nome) => {
    const parti = String(nome || "").toLowerCase().split(".");
    return parti.length > 1 ? parti.pop() : "";
  };

  const impronta = async (file) => {
    if (!impronte.has(file)) {
      impronte.set(file, window.crypto.subtle.digest("SHA-256", await file.arrayBuffer()).then((buffer) => (
        Array.from(new Uint8Array(buffer), (byte) => byte.toString(16).padStart(2, "0")).join("")
      )));
    }
    return impronte.get(file);
  };

  const controlla = async (files) => {
    const rifiutato = files.find((file) => !ESTENSIONI.has(estensione(file.name)));
    if (rifiutato) {
      return problema(t("err.formato"), t("err.formatoCausa", { f: rifiutato.name }), t("err.formatoAzione"),
        `UNSUPPORTED_SOURCE_SUFFIX .${estensione(rifiutato.name) || "missing"}`);
    }
    const attive = new Map(root.fileSorgenti().filter((s) => s.sha256).map((s) => [s.sha256, s]));
    const scelte = new Map();
    for (const file of files) {
      const digest = await impronta(file);
      const gia = attive.get(digest);
      if (gia) {
        return problema(t("err.duplicato"), t("err.duplicatoCausa", { f: file.name, g: gia.file_name }),
          t("err.duplicatoAzione"), `DUPLICATE_SOURCE_SHA256 ${digest}`);
      }
      if (scelte.has(digest)) {
        return problema(t("err.dueVolte"), t("err.dueVolteCausa", { f: file.name, g: scelte.get(digest) }),
          t("err.dueVolteAzione"), `DUPLICATE_SELECTION_SHA256 ${digest}`);
      }
      scelte.set(digest, file.name);
    }
    return null;
  };

  /* Un foglio in miniatura invece di un'icona generica: righe di testo per un
     manuale, un reticolo di celle per una tabella. Dice che cosa si sta per
     aprire prima di aprirlo. */
  const FOGLIO = {
    testo: `<path d="M9 15h18M9 21h18M9 27h13"/>`,
    tabella: `<path d="M7 15h22M7 22h22M7 29h22M15 11v24M23 11v24"/>`,
  };

  const anteprima = (fonte) => {
    const tabellare = fonte.source_kind !== "pdf";
    const indirizzo = `/visore.html?workspace_id=${encodeURIComponent(state.workspace.workspace.workspace_id)}`
      + `&source_id=${encodeURIComponent(fonte.source_id)}`;
    return `
      <a class="anteprima-doc ${tabellare ? "sigla-dati" : "sigla-pdf"}" href="${esc(indirizzo)}"
        target="_blank" rel="noopener">
        <span class="anteprima-foglio" aria-hidden="true">
          <svg viewBox="0 0 44 56" fill="none" stroke="currentColor" stroke-width="1.6"
            stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 4h24l12 12v36H4z" opacity=".55"/>
            <path d="M28 4v12h12" opacity=".55"/>
            ${tabellare ? FOGLIO.tabella : FOGLIO.testo}
          </svg>
        </span>
        <span class="anteprima-testo">
          <b>${esc(t("doc.apri"))}</b>
          <small>${esc(t("doc.apriNota"))}</small>
        </span>
        <span class="anteprima-freccia" aria-hidden="true">↗</span>
      </a>`;
  };

  const bloccoErrore = () => (state.sourceError ? `
    <div class="nota errore" role="alert" style="margin-top:14px">
      <span class="segno" aria-hidden="true">!</span>
      <strong>${esc(state.sourceError)}</strong>
      ${state.sourceErrorDetail ? `<span>
        ${esc(state.sourceErrorDetail.causa)}<br>
        <b>${esc(t("err.etichettaInvariato"))}</b> ${esc(state.sourceErrorDetail.invariato)}<br>
        <b>${esc(t("err.etichettaAzione"))}</b> ${esc(state.sourceErrorDetail.azione)}<br>
        ${esc(state.sourceErrorDetail.ritenta)}
        <details class="disclosure"><summary>${esc(t("err.dettaglio"))}</summary>
          <pre class="grezzo">${esc(state.sourceErrorDetail.tecnico)}</pre></details>
      </span>` : ""}
    </div>` : "");

  /* --------------------------------------------------------------- fase -- */
  root.phases.documents = {
    mostraIspettore: true,

    titolo: () => ({
      titolo: t("doc.titolo"),
      chips: `<span class="chip"><b>${root.fileSorgenti().length}</b> ${esc(t("nav.fonti").toLocaleLowerCase())}</span>`,
    }),

    renderLavoro() {
      if (!state.workspace) {
        return `<div class="stato-pagina"><strong>${esc(t("doc.primaMacchina"))}</strong>
          <p>${esc(t("doc.primaMacchinaTesto"))}</p>
          <button type="button" class="btn primario" data-vai="machine">${esc(t("doc.vaiMacchina"))}</button></div>`;
      }
      const fonti = root.fileSorgenti();
      const archiviate = ((state.journey && state.journey.sources) || [])
        .filter((item) => item.lifecycle === "archived");
      const notice = state.notice ? `
        <div class="notice-success" role="status">
          <span class="notice-icon" aria-hidden="true">✓</span>
          <span><strong>${esc(state.notice.title)}</strong><small>${esc(state.notice.body || "")}</small></span>
          <button type="button" class="notice-close" data-close-notice aria-label="${esc(t("ui.chiudi"))}">×</button>
        </div>` : "";
      /* Caricare è l'azione della fase: il modulo è la prima cosa che si vede
         e la più grande, non una riga di controlli sopra un elenco. */
      return `
        <div class="lavoro-scorri"><div class="lavoro-pad">
          ${notice}
          <form class="caricamento zona entra" id="source-upload">
            <label class="selettore-file">
              <span class="con-info">${esc(t("doc.file"))} ${root.info("formati-documento", t("doc.file"), t("doc.fileI"))}</span>
              <input type="file" name="file" required multiple accept=".pdf,.csv,.xlsx,.json,.jsonl"
                ${state.sourceBusy ? "disabled" : ""}>
              <span class="controllo-file"><b>${esc(t("doc.scegli"))}</b>
                <small data-nome-file>${esc(t("doc.nessunFile"))}</small></span>
            </label>
            <label class="campo">
              <span class="con-info">${esc(t("doc.tipo"))} ${root.info("tipo-documento", t("doc.tipo"), t("doc.tipoI"))}</span>
              <select name="authority">
                ${AUTORITA.map((valore) => `<option value="${valore}">${esc(t(`aut.${valore}`))}</option>`).join("")}
              </select>
            </label>
            <button type="submit" class="btn primario"
              ${(state.sourceBusy || !state.sourceSelectionValid) ? "disabled" : ""}>${
              state.sourceBusy ? `<span class="rotella" aria-hidden="true"></span>` : ""
            }${esc(state.sourceBusy ? t("doc.caricando") : t("doc.carica"))}</button>
          </form>
          ${/* aria-live e non role="status": la regione di stato della fase è
                una sola, quella delle notifiche, e due si contendono la voce. */
            state.sourceBusy
              ? `<p class="lavorazione" aria-live="polite">${esc(t("doc.lavorazione"))}</p>` : ""}
          ${bloccoErrore()}
          <div class="lista" style="margin-top:16px">
            ${fonti.length ? fonti.map((fonte) => `
              <div class="documento entra">
                <div class="documento-identita">
                  <strong>${esc(fonte.file_name)}</strong>
                  <small>${esc(String(fonte.source_kind).toUpperCase())} · ${esc(t(`aut.${fonte.authority}`))}</small>
                </div>
                <div class="documento-azioni">
                  <button type="button" class="btn quieto piccolo" data-ispeziona="${esc(fonte.source_id)}"
                    aria-label="${esc(t("doc.dettagliFile", { f: fonte.file_name }))}">${esc(t("ui.dettagli"))}</button>
                  <button type="button" class="btn pericolo piccolo togli" data-source-id="${esc(fonte.source_id)}"
                    aria-label="${esc(t("doc.archiviaFile", { f: fonte.file_name }))}"
                    ${state.sourceBusy ? "disabled" : ""}>${esc(t("ui.archivia"))}</button>
                </div>
              </div>`).join("")
              : `<div class="vuoto"><strong>${esc(t("doc.vuoto"))}</strong><p>${esc(t("doc.vuotoTesto"))}</p></div>`}
          </div>
          ${archiviate.length ? `<section class="archivio-fonti">
            <button type="button" class="archivio-toggle" data-archivio-toggle aria-expanded="false">
              <span>${esc(t("doc.archiviate"))}</span><span>${archiviate.length}</span>
            </button>
            <div class="archivio-lista" hidden>
              ${archiviate.map((fonte) => `<div class="documento archiviato">
                <div class="documento-identita">
                  <strong title="${esc(fonte.source_name)}">${esc(fonte.source_name)}</strong>
                  <small>${esc(String(fonte.source_kind).toUpperCase())} · ${fonte.graph_revision_count ? esc(t("doc.grafoConservato")) : esc(t("doc.nessunGrafoConservato"))}</small>
                </div>
                <button type="button" class="btn secondario piccolo" data-restore-source="${esc(fonte.source_id)}" ${state.sourceBusy ? "disabled" : ""}>${esc(t("ui.ripristina"))}</button>
              </div>`).join("")}
            </div>
          </section>` : ""}
        </div></div>`;
    },

    bindLavoro(contenitore) {
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
      root.delegate(contenitore, "click", "[data-ispeziona]", (elemento) => {
        root.scegliFonte(elemento.dataset.ispeziona);
        root.applicaSelezione("source", elemento.dataset.ispeziona);
      });
      root.delegate(contenitore, "click", "[data-close-notice]", () => {
        state.notice = null;
        root.render({ regioni: ["lavoro"] });
      });
      root.delegate(contenitore, "click", "[data-archivio-toggle]", (elemento) => {
        const lista = contenitore.querySelector(".archivio-lista");
        const aperto = elemento.getAttribute("aria-expanded") === "true";
        elemento.setAttribute("aria-expanded", String(!aperto));
        if (lista) lista.hidden = aperto;
      });

      const modulo = contenitore.querySelector("#source-upload");
      if (!modulo) return;
      const input = modulo.querySelector('input[type="file"]');
      const nome = modulo.querySelector("[data-nome-file]");
      const invia = modulo.querySelector('button[type="submit"]');

      input.addEventListener("change", async () => {
        const files = Array.from(input.files || []);
        state.sourceSelectionValid = false;
        invia.disabled = true;
        if (!files.length) { nome.textContent = t("doc.nessunFile"); return; }
        nome.textContent = t("doc.controllo");
        let guaio;
        try { guaio = await controlla(files); } catch (errore) {
          guaio = problema(t("err.impronta"), t("err.improntaCausa"), t("err.improntaAzione"),
            `CLIENT_FILE_DIGEST_FAILED ${errore.message}`);
        }
        if (guaio) {
          state.sourceError = guaio.titolo;
          state.sourceErrorDetail = guaio.dettaglio;
          input.value = "";
          root.render({ regioni: ["lavoro"] });
          return;
        }
        state.sourceError = "";
        state.sourceErrorDetail = null;
        contenitore.querySelector(".nota.errore")?.remove();
        state.sourceSelectionValid = true;
        invia.disabled = false;
        nome.textContent = files.length > 1 ? t("doc.nFile", { n: files.length }) : files[0].name;
      });

      modulo.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const files = Array.from(input.files || []);
        const authority = modulo.querySelector('[name="authority"]').value;
        if (!files.length) return;
        const guaio = await controlla(files);
        if (guaio) {
          state.sourceSelectionValid = false;
          state.sourceError = guaio.titolo;
          state.sourceErrorDetail = guaio.dettaglio;
          input.value = "";
          root.render({ regioni: ["lavoro"] });
          return;
        }
        state.sourceBusy = true;
        state.sourceSelectionValid = false;
        state.sourceError = "";
        state.sourceErrorDetail = null;
        root.render({ regioni: ["lavoro"] });
        try {
          const caricate = [];
          for (const file of files) {
            const corpo = new FormData();
            corpo.append("file", file);
            corpo.append("authority", authority);
            const registration = await root.api(`/api/workspaces/${state.workspace.workspace.workspace_id}/sources`, { method: "POST", body: corpo });
            caricate.push(registration.source.source_id);
          }
          state.structure = null;
          await root.refreshWorkspaceContext({ preferredSourceId: caricate[0] });
          const nuove = state.sources.filter((item) => caricate.includes(item.source_id));
          const nuova = nuove[0];
          const soloPdf = nuove.length > 0 && nuove.every((item) => item.source_kind === "pdf");
          const conPdf = nuove.some((item) => item.source_kind === "pdf");
          let corpoNotice;
          if (nuove.length === 1 && soloPdf) corpoNotice = t("doc.oraPdf", { f: nuova.file_name });
          else if (soloPdf) corpoNotice = t("doc.oraPdfGenerico");
          else if (conPdf) corpoNotice = t("doc.oraFontiMiste");
          else corpoNotice = nuova
            ? t("doc.oraStruttura", { f: nuova.file_name })
            : t("doc.oraStrutturaGenerico");
          state.notice = {
            title: t(caricate.length === 1 ? "doc.caricatoOk" : "doc.caricatiOk", { n: caricate.length }),
            body: corpoNotice,
          };
        } catch (errore) {
          state.sourceError = errore.message;
          state.sourceErrorDetail = errore.detail ? {
            causa: errore.detail.cause, invariato: errore.detail.preserved,
            azione: errore.detail.action, tecnico: errore.detail.technical_detail,
            ritenta: errore.detail.retryability,
          } : null;
        } finally {
          state.sourceBusy = false;
          root.render();
        }
      });

      root.delegate(contenitore, "click", ".togli", async (elemento) => {
        const sourceId = elemento.dataset.sourceId;
        const fonte = state.sources.find((s) => s.source_id === sourceId);
        const confirmed = await root.confirmAction({
          title: t("doc.archiviaTitolo", { f: fonte ? fonte.file_name : "" }),
          body: t("doc.archiviaCorpo"),
          detail: t("doc.archiviaDettaglio"),
          confirmLabel: t("doc.archiviaConferma"),
          cancelLabel: t("ui.annulla"),
          tone: "danger",
        });
        if (!confirmed) return;
        state.sourceBusy = true;
        state.sourceError = "";
        state.sourceErrorDetail = null;
        elemento.disabled = true;
        try {
          await root.api(`/api/sources/${sourceId}`, { method: "DELETE" });
          state.structure = null;
          await root.refreshWorkspaceContext();
          state.notice = { title: t("doc.archiviatoOk"), body: t("doc.archiviatoOkTesto") };
        } catch (errore) {
          state.sourceError = errore.message;
        } finally {
          state.sourceBusy = false;
          root.render();
        }
      });
      root.delegate(contenitore, "click", "[data-restore-source]", async (elemento) => {
        state.sourceBusy = true;
        state.sourceError = "";
        root.render({ regioni: ["lavoro"] });
        try {
          const source = await root.api(`/api/sources/${encodeURIComponent(elemento.dataset.restoreSource)}/restore`, { method: "POST" });
          state.structure = null;
          await root.refreshWorkspaceContext({ preferredSourceId: source.source_id });
          state.notice = { title: t("doc.ripristinatoOk"), body: t("doc.ripristinatoOkTesto", { f: source.file_name }) };
        } catch (errore) {
          state.sourceError = errore.message;
        } finally {
          state.sourceBusy = false;
          root.render();
        }
      });
    },

    renderIspettore() {
      const fonte = root.fonteAttiva();
      if (!fonte) {
        return `<div class="ispettore-vuoto"><strong>${esc(t("doc.nessunDettaglio"))}</strong>
          <p>${esc(t("doc.nessunDettaglioTesto"))}</p></div>`;
      }
      return `
        <div class="ispettore-dentro">
          <button type="button" class="btn quieto piccolo chiudi-ispettore" data-chiudi-ispettore>${esc(t("ui.chiudiDettaglio"))}</button>
          <div class="ispettore-identita">
            <span class="ispettore-tipo">${esc(t("isp.documento"))}</span>
            <h3>${esc(fonte.file_name)}</h3>
          </div>
          ${anteprima(fonte)}
          <section class="blocco"><h4>${esc(t("doc.comeUsato"))}</h4>
            <p>${esc(t(`aut.${fonte.authority}.d`))}</p></section>
          <section class="blocco"><h4>${esc(t("doc.dimensione"))}</h4>
            <p>${esc(`${(Number(fonte.size_bytes || 0) / 1024).toFixed(1)} kB`)}</p></section>
          <details class="disclosure"><summary>${esc(t("doc.tecnici"))}</summary>
            <p class="blocco-vuoto">${esc(t("doc.impronta"))}</p>
            <pre class="grezzo">${esc(fonte.sha256)}</pre></details>
        </div>`;
    },

    renderDecisione() {
      if (!state.workspace) return "";
      const fonti = root.fileSorgenti();
      const totale = fonti.length;
      if (!totale) {
        return `<div class="decisione-riga"><div class="decisione-testo">
          <strong>${esc(t("doc.nessunCaricato"))}</strong><span>${esc(t("doc.nessunCaricatoTesto"))}</span></div></div>`;
      }
      const soloPdf = fonti.every((fonte) => fonte.source_kind === "pdf");
      const conPdf = fonti.some((fonte) => fonte.source_kind === "pdf");
      const prossimo = soloPdf ? t("doc.prossimoPdf") : conPdf ? t("doc.prossimoMisto") : t("doc.prossimo");
      return `<div class="decisione-riga">
        <div class="decisione-testo"><strong>${esc(n(totale, "doc.caricati"))}</strong>
          <span>${esc(prossimo)}</span></div>
        <div class="decisione-azioni">
          <button type="button" class="btn primario" data-vai="structure">${esc(t(soloPdf ? "doc.continuaPdf" : "doc.continua"))}</button>
        </div></div>`;
    },

    bindDecisione(contenitore) {
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
    },
  };
})();
