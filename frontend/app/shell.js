(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const esc = root.escapeHtml;
  const t = root.t;

  /* Le quattro fasi hanno il nome dell'oggetto su cui si lavora. I checkpoint
     interni di sviluppo non fanno parte di questo vocabolario e non compaiono
     né a schermo né nella barra degli indirizzi. */
  const FASI = ["machine", "documents", "structure", "graph"];
  const SIGLE = { machine: "macchina", documents: "documenti", structure: "struttura", graph: "grafo" };
  const DA_SIGLA = Object.fromEntries(Object.entries(SIGLE).map(([id, sigla]) => [sigla, id]));
  /* I collegamenti creati prima della rinomina continuano a funzionare. */
  const VECCHIE = { g2: "structure", g3: "graph", documents: "documents" };

  const ICONE = {
    machine: "M4 7h16M4 12h16M4 17h16",
    documents: "M6 3h8l4 4v14H6zM14 3v4h4",
    structure: "M4 5h16M4 12h16M4 19h16M9 5v14M15 5v14",
    graph: "M5 6a2 2 0 104 0 2 2 0 10-4 0M15 5a2 2 0 104 0 2 2 0 10-4 0M9 18a2 2 0 104 0 2 2 0 10-4 0M8.6 7.6l5.8-1.2M8.2 8.7l2.6 7.6",
  };

  root.phases = root.phases || {};
  root.FASI = FASI;

  const largo = window.matchMedia("(min-width: 1181px)");

  root.siglaFase = (id) => SIGLE[id] || SIGLE.machine;

  root.indirizzoFase = function indirizzoFase(id, workspaceId) {
    const bersaglio = workspaceId || (state.workspace && state.workspace.workspace.workspace_id) || "";
    const query = new URLSearchParams({ foundation: "1" });
    if (bersaglio) query.set("workspace_id", bersaglio);
    if (id && id !== "machine") query.set("fase", root.siglaFase(id));
    return `/console.html?${query.toString()}`;
  };

  root.faseDaUrl = function faseDaUrl() {
    const parametri = new URL(window.location.href).searchParams;
    const sigla = parametri.get("fase");
    if (sigla && DA_SIGLA[sigla]) return DA_SIGLA[sigla];
    const vecchia = parametri.get("stage");
    if (vecchia && VECCHIE[vecchia]) return VECCHIE[vecchia];
    return "machine";
  };

  const fileSorgenti = () => (state.sources || []).filter((s) => s.source_kind !== "operator_input");

  /**
   * Stato di una fase, e che cosa mostrarne accanto al nome.
   *
   * Non una spunta: una spunta dice "fatto" e si legge come "chiuso", mentre
   * ogni fase resta modificabile — si aggiungono documenti, si cambia il
   * significato di una colonna, si ricostruisce un grafo. Il numero dice invece
   * che cosa c'è dentro, ed è l'informazione che serve davvero passando da una
   * fase all'altra.
   */
  root.statoFase = function statoFase(id) {
    const conWorkspace = Boolean(state.workspace);
    const documenti = fileSorgenti().length;
    const strutturaFatta = state.structure
      ? Boolean(state.structure.completed)
      : Boolean(state.graph && state.graph.sources.length
        && state.graph.sources.every((v) => v.state !== "waiting"));

    if (id === "machine") return { disponibile: true, fatta: conWorkspace, meta: "" };
    if (id === "documents") {
      return { disponibile: conWorkspace, fatta: documenti > 0, meta: documenti ? String(documenti) : "" };
    }
    if (id === "structure") {
      const righe = state.structure
        ? (state.structure.counts || {}).records || 0
        : 0;
      const daFare = state.structure
        ? (state.structure.exceptions || []).filter((e) => e.status === "open" || e.status === "queued").length
        : 0;
      return {
        disponibile: conWorkspace && documenti > 0,
        fatta: strutturaFatta,
        meta: daFare ? `<span style="color:var(--amber)">${daFare}</span>` : (righe ? String(righe) : ""),
      };
    }
    if (id === "graph") {
      const costruiti = state.graph ? state.graph.sources.filter((v) => v.subgraph) : [];
      const elementi = costruiti.reduce((totale, v) => totale + v.subgraph.nodes.length, 0);
      return {
        disponibile: conWorkspace && (strutturaFatta || state.phase === "graph"),
        fatta: costruiti.length > 0,
        meta: elementi ? String(elementi) : "",
      };
    }
    return { disponibile: false, fatta: false, meta: "" };
  };

  /* ------------------------------------------------------------- telaio -- */
  const TELAIO = `
    <a class="solo-lettori" href="#lavoro" data-salta></a>
    <aside class="sidebar">
      <div class="brand">
        <div class="logo" aria-hidden="true">KG</div>
        <div class="brand-text" data-marchio></div>
        <button class="collapse" type="button" data-comprimi>«</button>
      </div>
      <nav class="nav" data-regione="nav"></nav>
      <div class="sidebar-controls">
        <div class="sidebar-toggles">
          <button class="toggle-btn lingua" type="button" data-lingua>IT</button>
          <button class="toggle-btn tema" type="button" data-tema>☀</button>
        </div>
      </div>
    </aside>
    <main class="main">
      <header class="topbar">
        <h1 data-regione="titolo"></h1>
        <span class="spacer"></span>
        <span data-regione="chips" style="display:flex;gap:8px;align-items:center"></span>
      </header>
      <div class="contenuto" data-regione="contenuto">
        <div class="lavoro" id="lavoro" data-regione="lavoro" tabindex="-1"></div>
        <aside class="ispettore" data-regione="ispettore" aria-label="Dettaglio"></aside>
      </div>
      <footer class="decisione" data-regione="decisione"></footer>
    </main>`;

  const regione = (nome) => root.appElement.querySelector(`[data-regione="${nome}"]`);
  const faseAttiva = () => root.phases[state.phase] || root.phases.machine;

  const marchio = () => {
    const workspace = state.workspace && state.workspace.workspace;
    const asset = workspace && workspace.asset;
    if (!asset) return `${esc(t("home.nuova"))}<small>${esc(t("brand.sub"))}</small>`;
    return `${esc(asset.name)}<small>${esc(`${asset.brand} · ${asset.model}`)}</small>`;
  };

  const navigazione = () => {
    const fasi = FASI.map((id) => {
      const stato = root.statoFase(id);
      const attiva = state.phase === id;
      return `<button type="button" class="nav-item ${attiva ? "active" : ""}" data-fase="${id}"
        ${stato.disponibile ? "" : "disabled"} ${attiva ? 'aria-current="page"' : ""}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="${ICONE[id]}"/></svg>
        <span class="nav-label">${esc(t(`fase.${id}`))}</span>
        ${stato.meta ? `<span class="nav-meta">${stato.meta}</span>` : ""}
      </button>`;
    }).join("");

    const fase = faseAttiva();
    if (!fase.mostraFonti || !state.workspace) return `<div class="nav-group">${esc(t("nav.fasi"))}</div>${fasi}`;

    const fonti = fileSorgenti().map((sorgente) => {
      const attiva = root.fonteAttiva() && root.fonteAttiva().source_id === sorgente.source_id;
      const meta = fase.metaFonte ? fase.metaFonte(sorgente) : "";
      return `<button type="button" class="nav-item ${attiva ? "active" : ""}" data-fonte="${esc(sorgente.source_id)}"
        title="${esc(sorgente.file_name)}">
        <span class="nav-punto" style="--tipo:${sorgente.source_kind === "pdf" ? "var(--violet)" : "var(--cyan)"}"></span>
        <span class="nav-label">${esc(sorgente.file_name)}</span>
        ${meta ? `<span class="nav-meta">${meta}</span>` : ""}
      </button>`;
    }).join("");

    const extra = fase.navExtra ? fase.navExtra() : "";
    return `
      <div class="nav-group">${esc(t("nav.fasi"))}</div>${fasi}
      <div class="nav-group">${esc(t("nav.fonti"))}</div>
      ${fonti || `<div class="nav-item" style="cursor:default"><span class="nav-label">—</span></div>`}
      ${extra}`;
  };

  /**
   * Ridisegna solo le regioni cambiate. Selezionare un nodo tocca l'ispettore
   * e la barra della decisione, mai il grafo che l'operatore sta guardando.
   */
  root.render = function render(opzioni) {
    const impostazioni = opzioni || {};
    const regioni = impostazioni.regioni || ["nav", "titolo", "lavoro", "ispettore", "decisione"];
    const fase = faseAttiva();
    const contenuto = regione("contenuto");

    root.appElement.querySelector("[data-marchio]").innerHTML = marchio();

    if (regioni.includes("nav")) {
      root.paint(regione("nav"), navigazione());
      root.delegate(regione("nav"), "click", "[data-fase]", (elemento) => {
        if (elemento.disabled || elemento.dataset.fase === state.phase) return;
        root.vaiAllaFase(elemento.dataset.fase);
      });
      root.delegate(regione("nav"), "click", "[data-fonte]", (elemento) => {
        root.scegliFonte(elemento.dataset.fonte);
      });
      if (fase.bindNav) fase.bindNav(regione("nav"));
    }

    if (regioni.includes("titolo")) {
      const testa = fase.titolo ? fase.titolo() : { titolo: t(`fase.${state.phase}`), chips: "" };
      regione("titolo").textContent = testa.titolo;
      root.paint(regione("chips"), testa.chips || "");
      if (fase.bindChips) fase.bindChips(regione("chips"));
    }

    const vuoleIspettore = Boolean(fase.mostraIspettore) && Boolean(state.workspace);
    const mostraIspettore = vuoleIspettore && (largo.matches || Boolean(state.selection.id));
    contenuto.dataset.ispettore = mostraIspettore ? "aperto" : "chiuso";
    regione("ispettore").hidden = !mostraIspettore;

    if (regioni.includes("lavoro")) {
      const contenitore = regione("lavoro");
      root.paint(contenitore, fase.renderLavoro());
      if (fase.bindLavoro) fase.bindLavoro(contenitore);
      if (fase.dopoLavoro) fase.dopoLavoro(contenitore);
    }

    if (regioni.includes("ispettore")) {
      const contenitore = regione("ispettore");
      if (!mostraIspettore) root.paint(contenitore, "");
      else {
        root.paint(contenitore, fase.renderIspettore ? fase.renderIspettore() : "");
        root.delegate(contenitore, "click", "[data-chiudi-ispettore]", () => {
          root.clearSelection();
          root.render({ regioni: ["lavoro", "ispettore", "decisione"] });
        });
        if (fase.bindIspettore) fase.bindIspettore(contenitore);
      }
    }

    if (regioni.includes("decisione")) {
      const contenitore = regione("decisione");
      const markup = fase.renderDecisione ? fase.renderDecisione() : "";
      contenitore.hidden = !markup;
      root.paint(contenitore, markup);
      if (markup && fase.bindDecisione) fase.bindDecisione(contenitore);
    }
  };

  /** Selezionare è l'azione più frequente: deve costare il meno possibile. */
  root.applicaSelezione = function applicaSelezione(genere, id) {
    const generi = { nodo: "node", arco: "relation", evidenza: "evidence", "": "" };
    root.select(generi[genere] != null ? generi[genere] : genere, id);
    const fase = faseAttiva();
    if (fase.suSelezione) fase.suSelezione();
    else root.render({ regioni: ["lavoro"] });
    root.render({ regioni: ["ispettore", "decisione"] });
  };

  root.vaiAllaFase = async function vaiAllaFase(id) {
    if (!root.phases[id]) return;
    state.phase = id;
    root.clearSelection();
    state.view = id === "structure" ? "colonne" : "mappa";
    const workspaceId = state.workspace ? state.workspace.workspace.workspace_id : "";
    window.history.pushState({ fase: id }, "", root.indirizzoFase(id, workspaceId));
    root.render();
    if (root.phases[id].carica) {
      await root.phases[id].carica();
      root.render();
    }
  };

  /* ------------------------------------------------------- lingua e tema -- */
  const applicaLingua = () => {
    const bottone = root.appElement.querySelector("[data-lingua]");
    bottone.textContent = root.siglaLingua();
    bottone.title = t("ui.lingua");
    bottone.setAttribute("aria-label", bottone.title);
    root.appElement.querySelector("[data-salta]").textContent = t("ui.vaiContenuto");
    applicaCompressa(root.appElement.classList.contains("collapsed"));
    applicaTema(document.documentElement.dataset.theme);
  };

  function applicaTema(modo) {
    document.documentElement.dataset.theme = modo;
    const bottone = root.appElement.querySelector("[data-tema]");
    bottone.textContent = modo === "dark" ? "☾" : "☀";
    bottone.title = t(modo === "dark" ? "ui.temaChiaro" : "ui.temaScuro");
    bottone.setAttribute("aria-label", bottone.title);
    localStorage.setItem("kg.theme", modo);
  }

  function applicaCompressa(compressa) {
    root.appElement.classList.toggle("collapsed", compressa);
    const bottone = root.appElement.querySelector("[data-comprimi]");
    bottone.textContent = compressa ? "»" : "«";
    bottone.title = t(compressa ? "ui.apriMenu" : "ui.chiudiMenu");
    bottone.setAttribute("aria-label", bottone.title);
    localStorage.setItem("kg.collapsed", compressa ? "1" : "0");
  }

  root.shouldMount = function shouldMount() {
    return new URL(window.location.href).searchParams.get("foundation") === "1";
  };

  root.mount = async function mount(app) {
    root.appElement = app;
    app.className = "app";
    app.innerHTML = TELAIO;
    state.phase = root.faseDaUrl();
    state.view = state.phase === "structure" ? "colonne" : "mappa";

    app.querySelector("[data-lingua]").onclick = () => {
      root.cambiaLingua();
      applicaLingua();
      root.render();
    };
    app.querySelector("[data-tema]").onclick = () =>
      applicaTema(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
    app.querySelector("[data-comprimi]").onclick = () =>
      applicaCompressa(!app.classList.contains("collapsed"));

    applicaTema(localStorage.getItem("kg.theme")
      || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
    applicaCompressa(localStorage.getItem("kg.collapsed") === "1");
    applicaLingua();

    largo.addEventListener("change", () => root.render({ regioni: ["ispettore"] }));
    window.addEventListener("popstate", () => {
      state.phase = root.faseDaUrl();
      root.clearSelection();
      root.render();
      const fase = root.phases[state.phase];
      if (fase && fase.carica) fase.carica().then(() => root.render());
    });

    root.render();

    try {
      const parametri = new URL(window.location.href).searchParams;
      const workspaceId = parametri.get("workspace_id");
      state.creatingWorkspace = parametri.get("new") === "1";
      state.workspace = state.creatingWorkspace
        ? null
        : await root.api(workspaceId ? `/api/workspaces/${encodeURIComponent(workspaceId)}` : "/api/workspace");
      if (state.workspace) await root.caricaFonti();
      if (!state.workspace) state.phase = "machine";
      const fase = faseAttiva();
      if (fase.carica) await fase.carica();
    } catch (errore) {
      state.error = errore.message;
    } finally {
      state.loading = false;
      root.render();
    }
  };
})();
