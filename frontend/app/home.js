(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const app = document.getElementById("app");
  const esc = root.escapeHtml;
  const t = root.t;

  const TONO = {
    ready: "ok", ready_to_publish: "ok",
    failed_terminal: "errore",
    sources_required: "attesa", preparation_required: "attesa", processing: "attesa",
    failed_resumable: "attesa", awaiting_review: "attesa",
  };
  const PHASE_SLUG = { machine: "macchina", documents: "documenti", structure: "fonti", graph: "grafo" };

  /* Il segno del comando è disegnato, non scritto: un carattere "+" resta
     appeso alla sua linea di base e non sta mai al centro del bersaglio. */
  const PIU = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
    stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`;

  /* Fondale della pagina d'ingresso: una rete di nodi su un reticolo tecnico,
     che non rappresenta nessuna macchina in particolare. Dice di che cosa si
     occupa Nexus prima ancora che ci sia un grafo da guardare. */
  const SCENA = `
    <div class="home-scena" aria-hidden="true">
      <svg viewBox="0 0 1200 300" preserveAspectRatio="xMidYMax slice" fill="none">
        <defs>
          <linearGradient id="dissolvenza" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stop-color="#fff" stop-opacity="0"/>
            <stop offset=".45" stop-color="#fff" stop-opacity=".45"/>
            <stop offset="1" stop-color="#fff" stop-opacity="1"/>
          </linearGradient>
          <mask id="sfuma"><rect width="1200" height="300" fill="url(#dissolvenza)"/></mask>
        </defs>
        <g mask="url(#sfuma)">
          <g stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round" opacity=".9">
            <path d="M40 280H150l40-40h140l40-40h100"/>
            <path d="M120 300v-38l38-38h128l36-36h98l36-36h112"/>
            <path d="M300 300v-24l30-30h100"/>
            <path d="M560 300h100l40-40h120"/>
            <path d="M690 300v-54l40-40h130l40-40h110"/>
            <path d="M840 300v-30l36-36h104l36-36h144"/>
            <path d="M960 300h120l40-40h80"/>
          </g>
          <g fill="currentColor">
            <circle cx="150" cy="280" r="3"/><circle cx="190" cy="240" r="3"/>
            <circle cx="330" cy="240" r="3"/><circle cx="286" cy="224" r="3"/>
            <circle cx="322" cy="188" r="3"/><circle cx="430" cy="246" r="3"/>
            <circle cx="456" cy="152" r="3"/><circle cx="660" cy="280" r="3"/>
            <circle cx="700" cy="260" r="3"/><circle cx="730" cy="206" r="3"/>
            <circle cx="860" cy="206" r="3"/><circle cx="980" cy="234" r="3"/>
            <circle cx="1016" cy="198" r="3"/><circle cx="1080" cy="280" r="3"/>
          </g>
          <g class="nodi-vivi" fill="currentColor">
            <circle cx="470" cy="200" r="4.5"/><circle cx="568" cy="152" r="4.5"/>
            <circle cx="1010" cy="166" r="4.5"/>
          </g>
          <g class="aloni" fill="none" stroke="currentColor" stroke-width="1">
            <circle cx="470" cy="200" r="11"/>
            <circle cx="568" cy="152" r="11" style="animation-delay:1.5s"/>
            <circle cx="1010" cy="166" r="11" style="animation-delay:3s"/>
          </g>
        </g>
      </svg>
    </div>`;

  const applicaTema = (modo) => {
    document.documentElement.dataset.theme = modo;
    localStorage.setItem("kg.theme", modo);
    const bottone = app.querySelector("[data-tema]");
    if (bottone) {
      bottone.textContent = modo === "dark" ? "☾" : "☀";
      bottone.title = t(modo === "dark" ? "ui.temaChiaro" : "ui.temaScuro");
      bottone.setAttribute("aria-label", bottone.title);
    }
  };

  const COLONNE = ["macchina", "marca", "modello", "documenti", "stato", "aggiornato"];

  const disegna = (macchine, errore = "", caricando = false) => {
    /* Una macchina è una riga di tabella: ogni informazione ha la sua colonna,
       incolonnata con quella delle altre macchine. Si confrontano tre impianti
       con lo sguardo, senza rileggere la stessa cosa scritta in tre modi. */
    const righe = macchine.map((macchina) => {
      const tono = TONO[macchina.status] || "";
      const aggiornato = new Date(macchina.updated_at).toLocaleString(
        root.lingua() === "en" ? "en-GB" : "it-IT",
        { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }
      );
      const query = new URLSearchParams({ foundation: "1", workspace_id: macchina.workspace_id });
      if (macchina.recommended_phase && macchina.recommended_phase !== "machine") {
        query.set("fase", PHASE_SLUG[macchina.recommended_phase]);
      }
      if (macchina.recommended_source_id) query.set("source_id", macchina.recommended_source_id);
      return `
        <a class="riga-macchina entra" href="/console.html?${esc(query.toString())}">
          <span class="cella nome" data-col="${esc(t("home.col.macchina"))}">${esc(macchina.asset_name)}</span>
          <span class="cella" data-col="${esc(t("home.col.marca"))}">${esc(macchina.brand)}</span>
          <span class="cella modello" data-col="${esc(t("home.col.modello"))}">${esc(macchina.model)}</span>
          <span class="cella numero" data-col="${esc(t("home.col.documenti"))}">${esc(String(macchina.document_count))}</span>
          <span class="cella stato ${tono}" data-col="${esc(t("home.col.stato"))}">
            <i aria-hidden="true"></i><b>${esc(t(`wstato.${macchina.status}`))}</b>
          </span>
          <span class="cella quando" data-col="${esc(t("home.col.aggiornato"))}">${esc(aggiornato)}</span>
          <span class="cella freccia" aria-hidden="true">›</span>
        </a>`;
    }).join("");

    const intestazione = `
      <div class="testa-tabella" aria-hidden="true">
        ${COLONNE.map((chiave) => `<span class="cella">${esc(t(`home.col.${chiave}`))}</span>`).join("")}
        <span class="cella"></span>
      </div>`;

    app.innerHTML = `
      <main class="main" style="width:100%">
        <header class="topbar">
          <h1 class="marchio-app">
            <span class="logo" aria-hidden="true">N</span>
            <span class="marchio-nome">${esc(t("brand.nome"))}<small>${esc(t("brand.sub"))}</small></span>
          </h1>
          <span class="spacer"></span>
          <div class="comandi">
            <a class="cmd forte" href="/console.html?foundation=1&new=1"
              title="${esc(t("home.nuova"))}" aria-label="${esc(t("home.nuova"))}">${PIU}</a>
            <span class="cmd-separa" aria-hidden="true"></span>
            <button class="cmd lingua" type="button" data-lingua>${esc(root.siglaLingua())}</button>
            <button class="cmd tema" type="button" data-tema>☀</button>
          </div>
        </header>
        <div class="lavoro home-lavoro">
          ${SCENA}
          <div class="home-scorri"><div class="elenco-macchine">
            <div class="elenco-capo">
              <h2>${esc(t("home.titolo"))}</h2>
            </div>
            ${errore ? `<div class="nota errore" role="alert"><span class="segno" aria-hidden="true">!</span>
              <strong>${esc(t("home.errore"))}</strong><span>${esc(errore)}</span></div>` : ""}
            ${caricando ? `<p class="voce-meta">${esc(t("ui.caricamento"))}</p>` : righe ? `
              <div class="tabella-macchine">${intestazione}${righe}</div>` : `
              <div class="vuoto"><strong>${esc(t("home.vuoto"))}</strong><p>${esc(t("home.vuotoTesto"))}</p>
                <a class="btn primario" href="/console.html?foundation=1&new=1">${esc(t("home.nuova"))}</a></div>`}
          </div></div>
        </div>
      </main>`;

    app.querySelector("[data-lingua]").onclick = () => {
      root.cambiaLingua();
      disegna(macchine, errore, caricando);
    };
    app.querySelector("[data-lingua]").title = t("ui.lingua");
    app.querySelector("[data-tema]").onclick = () =>
      applicaTema(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
    applicaTema(document.documentElement.dataset.theme
      || localStorage.getItem("kg.theme")
      || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  };

  disegna([], "", true);
  root.api("/api/workspaces")
    .then((macchine) => disegna(macchine))
    .catch((errore) => disegna([], errore.message));
})();
