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
  /* La terza fase si chiama come quello che ci sta dentro: una fonte per
     volta, da come si legge fino al grafo che ne nasce. «Struttura» diceva
     solo il primo dei due passi. */
  const SIGLE = { machine: "macchina", documents: "documenti", structure: "fonti", graph: "grafo" };
  const DA_SIGLA = Object.fromEntries(Object.entries(SIGLE).map(([id, sigla]) => [sigla, id]));
  /* I collegamenti creati prima delle rinomine continuano a funzionare. */
  const SIGLE_VECCHIE = { struttura: "structure" };
  const VECCHIE = { g2: "structure", g3: "graph", documents: "documents" };

  root.phases = root.phases || {};
  root.FASI = FASI;

  const largo = window.matchMedia("(min-width: 1181px)");

  root.siglaFase = (id) => SIGLE[id] || SIGLE.machine;

  root.indirizzoFase = function indirizzoFase(id, workspaceId) {
    const bersaglio = workspaceId || (state.workspace && state.workspace.workspace.workspace_id) || "";
    const query = new URLSearchParams({ foundation: "1" });
    if (bersaglio) query.set("workspace_id", bersaglio);
    if (id && id !== "machine") query.set("fase", root.siglaFase(id));
    if (state.activeSourceId && id !== "machine") query.set("source_id", state.activeSourceId);
    return `/console.html?${query.toString()}`;
  };

  root.syncWorkspaceUrl = function syncWorkspaceUrl() {
    if (!state.workspace) return;
    window.history.replaceState(
      null, "", root.indirizzoFase(state.phase, state.workspace.workspace.workspace_id)
    );
  };

  root.faseDaUrl = function faseDaUrl() {
    const parametri = new URL(window.location.href).searchParams;
    const sigla = parametri.get("fase");
    if (sigla && (DA_SIGLA[sigla] || SIGLE_VECCHIE[sigla])) return DA_SIGLA[sigla] || SIGLE_VECCHIE[sigla];
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
    const projected = root.journeyPhase && root.journeyPhase(id);
    if (projected) {
      const attention = projected.attention_count || 0;
      return {
        disponibile: projected.available,
        fatta: projected.state === "complete",
        stato: projected.state,
        meta: attention
          ? `<span class="nav-attention">${attention}</span>`
          : (projected.count ? String(projected.count) : ""),
      };
    }
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
    return { disponibile: false, fatta: false, stato: "locked", meta: "" };
  };

  /* ------------------------------------------------------------- telaio -- */
  const TELAIO = `
    <a class="solo-lettori" href="#lavoro" data-salta></a>
    <aside class="sidebar">
      <div class="brand">
        <a class="brand-home" href="/home.html" data-casa>
          <span class="logo" aria-hidden="true">N</span>
          <span class="brand-text" data-marchio></span>
        </a>
        <button class="collapse" type="button" data-comprimi>«</button>
      </div>
      <nav class="nav" data-regione="nav"></nav>
    </aside>
    <main class="main">
      <header class="topbar">
        <h1 data-regione="titolo"></h1>
        <span class="spacer"></span>
        <span data-regione="chips" style="display:flex;gap:8px;align-items:center"></span>
        <div class="comandi">
          <span class="cmd-separa" aria-hidden="true"></span>
          <button class="cmd lingua" type="button" data-lingua>IT</button>
          <button class="cmd tema" type="button" data-tema>☀</button>
        </div>
      </header>
      <section data-regione="journey"></section>
      <div class="contenuto" data-regione="contenuto">
        <div class="lavoro" id="lavoro" data-regione="lavoro" tabindex="-1"></div>
        <aside class="ispettore" data-regione="ispettore" aria-label="Dettaglio"></aside>
      </div>
      <footer class="decisione" data-regione="decisione"></footer>
    </main>`;

  const regione = (nome) => root.appElement.querySelector(`[data-regione="${nome}"]`);
  const faseAttiva = () => root.phases[state.phase] || root.phases.machine;

  /* Che cosa stava descrivendo la colonna di destra all'ultimo disegno. */
  let ultimoIspettore = "";

  /* Il nome dell'applicativo sta in alto a sinistra e riporta al menu
     principale: da qualunque fase, un solo clic per tornare all'elenco delle
     macchine. La riga sotto dice su quale macchina si sta lavorando. */
  const marchio = () => {
    const workspace = state.workspace && state.workspace.workspace;
    const asset = workspace && workspace.asset;
    const sotto = asset ? asset.name : t("brand.sub");
    const casa = root.appElement.querySelector("[data-casa]");
    if (casa) {
      const titolo = asset ? `${t("brand.home")} — ${asset.name} · ${asset.brand} · ${asset.model}` : t("brand.home");
      casa.title = titolo;
      casa.setAttribute("aria-label", titolo);
    }
    return `${esc(t("brand.nome"))}<small>${esc(sotto)}</small>`;
  };

  /* Il formato del file dice più di un pallino colorato, e non chiede una
     legenda per essere capito. */
  const siglaFile = (sorgente) => {
    const punto = String(sorgente.file_name || "").lastIndexOf(".");
    const estensione = punto > 0 ? sorgente.file_name.slice(punto + 1) : "";
    return (estensione || sorgente.source_kind || "").slice(0, 4).toUpperCase();
  };

  /**
   * Come sta una fonte, nel vocabolario di colori delle fasi.
   *
   * Il dato viene dal percorso e non dalla fase aperta: la stessa fonte si
   * legge allo stesso modo da qualunque punto del menu. Verde vuol dire
   * finita — struttura risolta e sottografo verificato — e non compare prima,
   * perché è quella la sola condizione che chiude il lavoro su un documento.
   */
  const statoFonte = (sorgente) => {
    const voce = root.journeySource ? root.journeySource(sorgente.source_id) : null;
    if (!voce) return "";
    if (voce.graph_state === "approved") return "complete";
    if (voce.structure_state === "needs_attention" || voce.graph_state === "rejected") return "needs_attention";
    if (voce.structure_state === "not_applicable") return "deferred";
    if (voce.structure_state === "ready" || voce.structure_state === "confirmed") return "in_progress";
    return "";
  };

  /**
   * Il numero accanto a una fonte, uguale in ogni fase.
   *
   * Dice quante domande restano finché ce ne sono, e quante righe ha il file
   * quando non ne restano: è una proprietà del documento, non della fase da
   * cui lo si guarda. Cambiandolo da una fase all'altra, lo stesso file
   * mostrava due numeri diversi nello stesso posto del menu.
   */
  const metaFonte = (sorgente) => {
    if (sorgente.source_kind === "pdf") return "";
    const dati = state.structure || {};
    const profilo = (dati.profiles || []).find((p) => p.source_id === sorgente.source_id);
    if (!profilo) return "";
    const aperte = (dati.exceptions || []).filter((e) => (
      e.profile_id === profilo.profile_id && (e.status === "open" || e.status === "queued")
    )).length;
    if (aperte) return `<span class="nav-attention">${aperte}</span>`;
    return String(Number(profilo.summary.record_count || 0));
  };

  const navigazione = () => {
    const fase = faseAttiva();
    const fonti = state.workspace ? fileSorgenti() : [];
    const inCorso = root.fonteAttiva && root.fonteAttiva();

    /* Le fonti non sono una sezione a parte: la struttura è fatta di quelle, e
       dentro ognuna sta tutto il lavoro che la riguarda. Stanno perciò
       annidate sotto il passo che le lavora, e a dirlo basta il rientro —
       un'intestazione «Fonti» le rimetterebbe fuori. */
    const figli = fonti.map((sorgente) => {
      const attiva = inCorso && inCorso.source_id === sorgente.source_id;
      const meta = metaFonte(sorgente);
      const condizione = statoFonte(sorgente);
      const titolo = condizione
        ? `${sorgente.file_name} — ${t(`journey.state.${condizione}`)}`
        : sorgente.file_name;
      return `<button type="button" class="nav-item ${attiva ? "active" : ""}" data-fonte="${esc(sorgente.source_id)}"
        title="${esc(titolo)}" ${attiva ? 'aria-current="true"' : ""}>
        <span class="nav-sigla ${sorgente.source_kind === "pdf" ? "sigla-pdf" : "sigla-dati"}${condizione ? ` state-${esc(condizione)}` : ""}"
          aria-hidden="true">${esc(siglaFile(sorgente))}</span>
        <span class="nav-label">${esc(sorgente.file_name)}</span>
        ${meta ? `<span class="nav-meta">${meta}</span>` : ""}
      </button>`;
    }).join("") + (fase.navExtra ? fase.navExtra() : "");

    /* Finché il sottografo si costruisce nella fase del grafo, è lì che le
       fonti vanno mentre ci si lavora: un solo elenco, mai lo stesso file due
       volte nella barra. */
    const ancora = state.phase === "graph" ? "graph" : "structure";

    /* Le fasi sono un ordine, non un elenco: il numero del passo lo dice, e
       si tinge dello stato in cui quel passo si trova. Un numero riquadrato
       resta leggibile anche col menu ridotto alla sola colonna dei segni. */
    return FASI.map((id, indice) => {
      const stato = root.statoFase(id);
      const attiva = state.phase === id;
      const condizione = esc(stato.stato || (stato.fatta ? "complete" : "available"));
      return `<button type="button" class="nav-item ${attiva ? "active" : ""}" data-fase="${id}"
        ${stato.disponibile ? "" : `disabled title="${esc(t("journey.locked"))}"`} ${attiva ? 'aria-current="page"' : ""}>
        <span class="nav-passo state-${condizione}" aria-hidden="true">${String(indice + 1).padStart(2, "0")}</span>
        <span class="nav-label">${esc(t(`fase.${id}`))}</span>
        ${stato.meta ? `<span class="nav-meta">${stato.meta}</span>` : ""}
      </button>${id === ancora && figli ? `<div class="nav-figli">${figli}</div>` : ""}`;
    }).join("");
  };

  /**
   * Ridisegna solo le regioni cambiate. Selezionare un nodo tocca l'ispettore
   * e la barra della decisione, mai il grafo che l'operatore sta guardando.
   */
  root.render = function render(opzioni) {
    const impostazioni = opzioni || {};
    const regioni = impostazioni.regioni || ["nav", "titolo", "journey", "lavoro", "ispettore", "decisione"];
    const fase = faseAttiva();
    const contenuto = regione("contenuto");

    root.appElement.querySelector("[data-marchio]").innerHTML = marchio();

    if (regioni.includes("nav")) {
      root.paint(regione("nav"), navigazione());
      root.delegate(regione("nav"), "click", "[data-fase]", (elemento) => {
        if (elemento.disabled || elemento.dataset.fase === state.phase) return;
        root.vaiAllaFase(elemento.dataset.fase);
      });
      /* Una fonte è una destinazione, non un filtro della fase aperta: dalla
         macchina o dai documenti aprirla vuol dire andarci a lavorare, e il
         lavoro su una fonte comincia dalla struttura. Dove le fonti sono già
         il contenuto della fase — struttura e grafo — il clic cambia solo
         quella su cui si sta lavorando. */
      root.delegate(regione("nav"), "click", "[data-fonte]", (elemento) => {
        const sourceId = elemento.dataset.fonte;
        if (state.phase === "structure" || state.phase === "graph") {
          root.scegliFonte(sourceId);
          return;
        }
        state.activeSourceId = sourceId;
        root.vaiAllaFase("structure");
      });
      if (fase.bindNav) fase.bindNav(regione("nav"));
    }

    if (regioni.includes("titolo")) {
      const testa = fase.titolo ? fase.titolo() : { titolo: t(`fase.${state.phase}`), chips: "" };
      regione("titolo").textContent = testa.titolo;
      root.paint(regione("chips"), testa.chips || "");
      if (fase.bindChips) fase.bindChips(regione("chips"));
    }

    if (regioni.includes("journey")) {
      const contenitore = regione("journey");
      root.paint(contenitore, root.renderJourney ? root.renderJourney() : "");
      root.delegate(contenitore, "click", "[data-follow-journey]", () => root.followJourneyAction());
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
        /* Cambiando elemento cambia tutto il contenuto della colonna: lasciarla
           dove stava faceva aprire un elemento nuovo a metà di un blocco che
           parlava del precedente. Si torna in cima solo quando la selezione è
           davvero un'altra — un ridisegno qualunque non deve far perdere il
           punto a chi sta leggendo. */
        const chiave = `${state.phase}|${state.view}|${state.activeSourceId}|${state.selection.kind}|${state.selection.id}`;
        if (chiave !== ultimoIspettore) {
          ultimoIspettore = chiave;
          contenitore.scrollTop = 0;
        }
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
    const projected = root.journeyPhase && root.journeyPhase(id);
    if (projected && !projected.available) return;
    state.phase = id;
    root.clearSelection();
    state.view = id === "structure" ? "lettura" : "mappa";
    const workspaceId = state.workspace ? state.workspace.workspace.workspace_id : "";
    window.history.pushState({ fase: id }, "", root.indirizzoFase(id, workspaceId));
    if (root.rememberWorkspaceContext) root.rememberWorkspaceContext();
    root.render();
    if (root.phases[id].carica) {
      await root.phases[id].carica();
      if (root.loadJourney) await root.loadJourney();
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
    state.view = state.phase === "structure" ? "lettura" : "mappa";

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
      if (state.workspace && root.loadJourney) {
        await root.loadJourney();
        root.resolveWorkspaceContext({
          explicitPhase: parametri.has("fase") || parametri.has("stage"),
          sourceId: parametri.get("source_id") || "",
        });
        state.view = state.phase === "structure" ? "lettura" : "mappa";
        window.history.replaceState(null, "", root.indirizzoFase(
          state.phase, state.workspace.workspace.workspace_id
        ));
      }
      const fase = faseAttiva();
      if (fase.carica) await fase.carica();
      if (state.workspace && root.loadJourney) await root.loadJourney();
    } catch (errore) {
      state.error = errore.message;
    } finally {
      state.loading = false;
      root.render();
    }
  };
})();
