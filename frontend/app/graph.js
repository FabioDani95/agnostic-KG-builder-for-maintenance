(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const esc = root.escapeHtml;
  const t = root.t;
  const n = root.n;

  let cercaTimer = 0;
  let explorer = null;

  const wsId = () => state.workspace.workspace.workspace_id;
  const vistaFonte = () => {
    if (!state.graph) return null;
    const attiva = root.fonteAttiva();
    if (!attiva) return null;
    return state.graph.sources.find((v) => v.source_id === attiva.source_id) || null;
  };

  /**
   * Quale elemento una lacuna riguarda davvero.
   *
   * Il motore attacca le lacune alle righe, non ai nodi. Far ereditare la
   * lacuna a ogni nodo nato da quella riga marcava anche la macchina — che
   * compare in tutte le righe — e il sintomo, quando a mancare era l'azione
   * della causa. Qui una lacuna tocca solo i tipi che ne sono l'oggetto:
   * quello che resta senza controparte.
   *
   * Macchina e componente non compaiono mai: sono sempre dichiarati, non sono
   * mai il pezzo mancante di una catena diagnostica.
   */
  const TIPI_TOCCATI = {
    missing_failure_mode: ["Symptom", "ErrorCode"],
    missing_diagnostic_indicator: ["FailureMode"],
    missing_corrective_action: ["FailureMode"],
    /* Gli abbinamenti ambigui non possono più nascere con una colonna per
       ruolo, ma la rete di sicurezza del motore resta: se ricompaiono, a
       restare senza collegamento sono i due estremi. */
    ambiguous_symptom_cause_pairing: ["Symptom", "FailureMode"],
    ambiguous_cause_component_pairing: ["FailureMode", "Component"],
    ambiguous_cause_action_pairing: ["FailureMode", "CorrectiveAction"],
    ambiguous_error_cause_pairing: ["ErrorCode", "FailureMode"],
  };

  /* ------------------------------------------------------------- modello -- */
  const costruisciModello = (grafo) => {
    const nodiPerId = new Map(grafo.nodes.map((nodo) => [nodo.node_id, nodo]));
    const evidenzePerId = new Map(grafo.evidence.map((voce) => [voce.evidence_id, voce]));
    const grado = new Map();
    const legamiPerNodo = new Map();
    grafo.relations.forEach((legame) => {
      [legame.from_id, legame.to_id].forEach((id) => {
        grado.set(id, (grado.get(id) || 0) + 1);
        if (!legamiPerNodo.has(id)) legamiPerNodo.set(id, []);
        legamiPerNodo.get(id).push(legame);
      });
    });

    /* Una lacuna è attaccata a un'evidenza; un nodo eredita le lacune delle
       righe che l'hanno prodotto, così "cosa blocca questo nodo" ha risposta. */
    const lacunePerEvidenza = new Map();
    (grafo.knowledge_gaps || []).forEach((lacuna) => {
      (lacuna.evidence_ids || []).forEach((id) => {
        if (!lacunePerEvidenza.has(id)) lacunePerEvidenza.set(id, []);
        lacunePerEvidenza.get(id).push(lacuna);
      });
    });
    const lacunePerNodo = new Map();
    grafo.nodes.forEach((nodo) => {
      const lacune = [];
      nodo.evidence_ids.forEach((id) => (lacunePerEvidenza.get(id) || []).forEach((lacuna) => {
        if (!TIPI_TOCCATI[lacuna.code]) return;
        if (!TIPI_TOCCATI[lacuna.code].includes(nodo.node_type)) return;
        if (!lacune.includes(lacuna)) lacune.push(lacuna);
      }));
      if (lacune.length) lacunePerNodo.set(nodo.node_id, lacune);
    });
    const difettiPerNodo = new Map();
    ((grafo.validation || {}).issues || []).forEach((difetto) => {
      if (!difetto.node_id) return;
      if (!difettiPerNodo.has(difetto.node_id)) difettiPerNodo.set(difetto.node_id, []);
      difettiPerNodo.get(difetto.node_id).push(difetto);
    });

    /* — filtri: valgono su tutte le viste insieme, mappa e tabelle — */
    const cerca = String(state.filters.query || "").trim().toLocaleLowerCase();
    let visibili = grafo.nodes.filter((nodo) => {
      if (state.filters.nodeType !== "all" && nodo.node_type !== state.filters.nodeType) return false;
      if (state.filters.onlyGaps && !lacunePerNodo.has(nodo.node_id) && !difettiPerNodo.has(nodo.node_id)) return false;
      if (cerca && !nodo.label.toLocaleLowerCase().includes(cerca)) return false;
      return true;
    });
    if (state.filters.relationType !== "all") {
      const estremi = new Set();
      grafo.relations.filter((l) => l.relation_type === state.filters.relationType)
        .forEach((l) => { estremi.add(l.from_id); estremi.add(l.to_id); });
      visibili = visibili.filter((nodo) => estremi.has(nodo.node_id));
    }
    if (state.filters.focus && state.selection.kind === "node" && nodiPerId.has(state.selection.id)) {
      const tieni = new Set([state.selection.id]);
      (legamiPerNodo.get(state.selection.id) || []).forEach((l) => { tieni.add(l.from_id); tieni.add(l.to_id); });
      visibili = visibili.filter((nodo) => tieni.has(nodo.node_id));
    }

    const idVisibili = new Set(visibili.map((nodo) => nodo.node_id));
    const legami = grafo.relations.filter((l) => (
      idVisibili.has(l.from_id) && idVisibili.has(l.to_id)
      && (state.filters.relationType === "all" || l.relation_type === state.filters.relationType)
    ));

    return {
      grafo, nodi: visibili, legami, nodiPerId, evidenzePerId, legamiPerNodo, grado,
      lacunePerNodo, lacunePerEvidenza, difettiPerNodo,
      nascosti: grafo.nodes.length - visibili.length,
      /* Un filtro che non può togliere niente non è un filtro: chi lo offre
         promette una selezione che non esiste. Si calcola qui, una volta, e
         lo leggono tutte le strisce che mostrano quella spunta. */
      conLacune: grafo.nodes.some((nodo) => (
        lacunePerNodo.has(nodo.node_id) || difettiPerNodo.has(nodo.node_id)
      )),
    };
  };

  const modelloDi = (vista) => (vista && vista.subgraph ? costruisciModello(vista.subgraph) : null);

  /* La spunta delle lacune, uguale nelle due strisce che la offrono. Resta
     attivabile solo se qualcosa può togliere, e resta togliibile sempre: chi
     l'ha accesa deve poterla spegnere anche dopo aver corretto l'ultima. */
  root.spuntaLacune = function spuntaLacune(modello) {
    const spenta = !modello.conLacune && !state.filters.onlyGaps;
    return `<label class="spunta ${spenta ? "spenta" : ""}"
      ${spenta ? `title="${esc(t("gr.nienteLacune"))}"` : ""}>
      <input type="checkbox" data-filtro="onlyGaps" ${state.filters.onlyGaps ? "checked" : ""}
        ${spenta ? "disabled" : ""}>${esc(t("gr.soloLacune"))}</label>`;
  };

  /* --------------------------------------------------------------- rete -- */
  const carica = async () => {
    if (!state.workspace) return;
    state.graphLoading = true;
    state.graphError = "";
    try {
      state.graph = await root.api(`/api/workspaces/${encodeURIComponent(wsId())}/g3/subgraphs`);
    } catch (errore) {
      state.graphError = errore.message;
    } finally {
      state.graphLoading = false;
    }
    /* Il numero accanto a una fonte nel menu è lo stesso in ogni fase, e viene
       dalla preparazione: qui va letta anche se questa fase non la usa, o
       arrivando dritti al grafo quel numero mancherebbe. È una lettura, non
       una preparazione: non cambia niente. */
    if (!state.structure && root.leggiPreparazione) await root.leggiPreparazione();
  };

  const esegui = async (azione) => {
    state.graphBusy = true;
    state.graphError = "";
    root.render({ regioni: ["decisione"] });
    try {
      state.graph = await azione();
      if (root.loadJourney) await root.loadJourney();
    } catch (errore) { state.graphError = errore.message; }
    finally { state.graphBusy = false; root.render(); }
  };

  /* -------------------------------------------------------------- viste -- */
  const VISTE = [
    { id: "mappa", chiave: "gr.vista.mappa" },
    { id: "catene", chiave: "gr.vista.catene" },
    { id: "elementi", chiave: "gr.vista.elementi" },
    { id: "collegamenti", chiave: "gr.vista.collegamenti" },
    { id: "righe", chiave: "gr.vista.righe" },
    { id: "manca", chiave: "gr.vista.manca" },
  ];

  const barra = (modello) => {
    const tipiRel = [...new Set(modello.grafo.relations.map((l) => l.relation_type))];
    const conteggi = {
      elementi: modello.grafo.nodes.length,
      collegamenti: modello.grafo.relations.length,
      righe: modello.grafo.evidence.length,
      manca: (modello.grafo.knowledge_gaps || []).length
        + (((modello.grafo.validation || {}).issues) || []).length,
    };
    return `
      <div class="barra">
        <div class="segmento" role="tablist">
          ${VISTE.map((vista) => `<button type="button" class="tab" role="tab" data-vista="${vista.id}"
            aria-selected="${state.view === vista.id}">${esc(t(vista.chiave))}${conteggi[vista.id] == null ? "" : ` ${conteggi[vista.id]}`}</button>`).join("")}
        </div>
        <span class="barra-spazio"></span>
        <div class="barra-gruppo">
          <label class="solo-lettori" for="kg-cerca">${esc(t("gr.cerca"))}</label>
          <input id="kg-cerca" type="search" data-cerca placeholder="${esc(t("gr.cerca"))}"
            value="${esc(state.filters.query)}">
          <label class="solo-lettori" for="kg-tipo">${esc(t("gr.tipoElemento"))}</label>
          <select id="kg-tipo" data-filtro="nodeType">
            <option value="all">${esc(t("gr.tuttiTipi"))}</option>
            ${root.ordineTipi.map((tipo) => `<option value="${tipo}" ${state.filters.nodeType === tipo ? "selected" : ""}>${esc(root.etichettaTipoPl(tipo))}</option>`).join("")}
          </select>
          <label class="solo-lettori" for="kg-rel">${esc(t("gr.tipoCollegamento"))}</label>
          <select id="kg-rel" data-filtro="relationType">
            <option value="all">${esc(t("gr.tuttiCollegamenti"))}</option>
            ${tipiRel.map((tipo) => `<option value="${tipo}" ${state.filters.relationType === tipo ? "selected" : ""}>${esc(root.etichettaRelazione(tipo))}</option>`).join("")}
          </select>
          ${root.spuntaLacune(modello)}
          <label class="spunta"><input type="checkbox" data-filtro="focus" ${state.filters.focus ? "checked" : ""}>${esc(t("gr.soloIntorno"))}</label>
        </div>
      </div>`;
  };

  const riassuntoFiltri = (modello) => (modello.nascosti
    ? `<p class="voce-meta" style="margin-bottom:12px">${esc(t("gr.nascosti", { n: modello.nascosti }))}
        <button type="button" class="btn quieto piccolo" data-azzera>${esc(t("gr.azzera"))}</button></p>`
    : "");

  /* Perché la mappa è vuota. «Nessun elemento corrisponde ai filtri» è vero
     anche quando l'unico filtro acceso non poteva corrispondere a niente: in
     quel caso la frase da dire è che lacune non ce ne sono. */
  const motivoVuoto = (modello) => {
    if (!modello.grafo.nodes.length) return t("gr.nienteElementi");
    if (state.filters.onlyGaps && !modello.conLacune) return t("gr.nienteLacune");
    return t("gr.nienteFiltriTesto");
  };

  const mappa = (modello) => {
    if (!modello.nodi.length) {
      return `<div class="lavoro-pad"><div class="vuoto">
        <strong>${esc(t("gr.nienteFiltri"))}</strong>
        <p>${esc(motivoVuoto(modello))}</p>
        ${modello.grafo.nodes.length ? `<button type="button" class="btn secondario" data-azzera>${esc(t("gr.azzera"))}</button>` : ""}
      </div></div>`;
    }
    const legenda = root.ordineTipi
      .filter((tipo) => modello.nodi.some((nodo) => nodo.node_type === tipo))
      .map((tipo) => `<span class="tipo-${tipo}"><i aria-hidden="true"></i>${esc(root.etichettaTipoPl(tipo))}</span>`)
      .join("");
    return `
      <div class="grafo" data-grafo>
        ${modello.nascosti ? `<div class="grafo-nascosti floating">
          <span>${esc(t("gr.nascosti", { n: modello.nascosti }))}</span>
          <button type="button" class="btn quieto piccolo" data-azzera>${esc(t("gr.azzera"))}</button>
        </div>` : ""}
        ${legenda ? `<div class="grafo-legenda floating">${legenda}</div>` : ""}
        <div class="grafo-comandi floating">
          <button type="button" class="btn quieto segno" data-zoom="meno" aria-label="${esc(t("gr.riduci"))}">−</button>
          <span class="grafo-zoom" data-zoom-valore>100%</span>
          <button type="button" class="btn quieto segno" data-zoom="piu" aria-label="${esc(t("gr.ingrandisci"))}">+</button>
          <button type="button" class="btn quieto piccolo" data-zoom="adatta">${esc(t("gr.adatta"))}</button>
          <button type="button" class="btn quieto piccolo" data-ridisponi title="${esc(t("gr.ridisponiTitolo"))}">${esc(t("gr.ridisponi"))}</button>
        </div>
      </div>`;
  };

  const tabellaElementi = (modello) => `
    <div class="lavoro-pad">
      ${riassuntoFiltri(modello)}
      <div class="tabella-wrap"><table class="tabella"><thead><tr>
        <th>${esc(t("gr.tipo"))}</th><th>${esc(t("gr.elemento"))}</th>
        <th class="num">${esc(t("gr.collegamentiCol"))}</th>
        <th class="num">${esc(t("gr.righeOrigineCol"))}</th>
        <th>${esc(t("gr.statoCol"))}</th>
      </tr></thead><tbody>
        ${modello.nodi.length ? modello.nodi.map((nodo) => {
          const lacuna = modello.lacunePerNodo.has(nodo.node_id);
          const difetto = modello.difettiPerNodo.has(nodo.node_id);
          return `<tr data-clic data-scegli="nodo" data-id="${esc(nodo.node_id)}"
            aria-selected="${state.selection.kind === "node" && state.selection.id === nodo.node_id}">
            <td><span class="ruolo tipo-${esc(nodo.node_type)}"><i aria-hidden="true"></i>${esc(root.etichettaTipo(nodo.node_type))}</span></td>
            <td>${esc(nodo.label)}</td>
            <td class="num">${modello.grado.get(nodo.node_id) || 0}</td>
            <td class="num">${nodo.evidence_ids.length}</td>
            <td>${difetto ? `<span class="badge errore">${esc(t("gr.difetto"))}</span>`
              : lacuna ? `<span class="badge attesa">${esc(t("gr.lacuna"))}</span>`
              : `<span class="badge">${esc(t("gr.completo"))}</span>`}</td>
          </tr>`;
        }).join("") : `<tr><td colspan="5">${esc(t("gr.nienteElementiFiltri"))}</td></tr>`}
      </tbody></table></div>
    </div>`;

  const tabellaCollegamenti = (modello) => `
    <div class="lavoro-pad">
      ${riassuntoFiltri(modello)}
      <div class="tabella-wrap"><table class="tabella"><thead><tr>
        <th>${esc(t("gr.da"))}</th><th>${esc(t("gr.collegamento"))}</th><th>${esc(t("gr.a"))}</th>
        <th class="num">${esc(t("gr.righeOrigineCol"))}</th>
      </tr></thead><tbody>
        ${modello.legami.length ? modello.legami.map((legame) => {
          const da = modello.nodiPerId.get(legame.from_id);
          const a = modello.nodiPerId.get(legame.to_id);
          return `<tr data-clic data-scegli="arco" data-id="${esc(legame.relation_id)}"
            aria-selected="${state.selection.kind === "relation" && state.selection.id === legame.relation_id}">
            <td>${esc(da ? da.label : "—")}</td>
            <td><span class="badge">${esc(root.etichettaRelazione(legame.relation_type))}</span></td>
            <td>${esc(a ? a.label : "—")}</td>
            <td class="num">${legame.evidence_ids.length}</td>
          </tr>`;
        }).join("") : `<tr><td colspan="4">${esc(t("gr.nienteCollegamentiFiltri"))}</td></tr>`}
      </tbody></table></div>
    </div>`;

  const listaRighe = (modello) => `
    <div class="lavoro-pad">
      <div class="gruppo-capo"><h3>${esc(t("gr.righeTitolo"))}</h3><p>${esc(t("gr.righeTesto"))}</p></div>
      <div class="lista" style="margin-top:12px">
        ${modello.grafo.evidence.map((voce) => {
          const lacune = modello.lacunePerEvidenza.get(voce.evidence_id) || [];
          return `<button type="button" class="voce" data-scegli="evidenza" data-id="${esc(voce.evidence_id)}"
            aria-selected="${state.selection.kind === "evidence" && state.selection.id === voce.evidence_id}">
            <span class="voce-capo"><strong>${esc(root.descriviLocator(voce.locator))}</strong>
              ${lacune.length ? `<span class="badge attesa">${esc(n(lacune.length, "isp.lacune"))}</span>` : ""}</span>
            <span class="voce-testo">${esc(voce.excerpt || t("gr.rigaSenzaTesto"))}</span>
          </button>`;
        }).join("")}
      </div>
    </div>`;

  /** Catene diagnostiche: una voce per causa, con quello che le righe provano. */
  const catene = (modello) => {
    const cause = modello.grafo.nodes.filter((nodo) => nodo.node_type === "FailureMode");
    if (!cause.length) {
      return `<div class="lavoro-pad"><div class="vuoto">
        <strong>${esc(t("gr.nienteCatene"))}</strong><p>${esc(t("gr.nienteCateneTesto"))}</p></div></div>`;
    }
    const passo = (nodo) => `<button type="button" class="catena-passo tipo-${esc(nodo.node_type)}"
      data-scegli="nodo" data-id="${esc(nodo.node_id)}"><i aria-hidden="true"></i><span>${esc(nodo.label)}</span></button>`;
    const freccia = '<span class="catena-freccia" aria-hidden="true">→</span>';

    const voci = cause.map((causa) => {
      const legami = modello.legamiPerNodo.get(causa.node_id) || [];
      const prendi = (tipo, lato) => legami.filter((l) => l.relation_type === tipo)
        .map((l) => modello.nodiPerId.get(lato === "from" ? l.from_id : l.to_id)).filter(Boolean);
      const indizi = [...prendi("MAY_INDICATE", "from"), ...prendi("INDICATES", "from")];
      const azioni = prendi("RESOLVED_BY", "to");
      const componenti = prendi("AFFECTS", "to");
      const manca = [];
      if (!indizi.length) manca.push(t("gr.senzaSintomo"));
      if (!azioni.length) manca.push(t("gr.senzaAzione"));
      return `
        <div class="voce">
          <div class="catena">
            ${indizi.length ? indizi.map(passo).join(freccia) : `<span class="catena-passo">${esc(t("gr.origineNonDichiarata"))}</span>`}
            ${freccia}${passo(causa)}${freccia}
            ${azioni.length ? azioni.map(passo).join('<span class="catena-freccia" aria-hidden="true">·</span>') : `<span class="catena-passo">${esc(t("gr.azioneNonDichiarata"))}</span>`}
          </div>
          ${componenti.length ? `<span class="voce-meta">${esc(t("gr.interessa", { n: componenti.map((c) => c.label).join(" · ") }))}</span>` : ""}
          ${manca.length ? `<span class="voce-meta">${esc(t("gr.catenaIncompleta", { n: manca.join(" · ") }))}</span>` : ""}
        </div>`;
    }).join("");

    return `<div class="lavoro-pad">
      <div class="gruppo-capo"><h3>${esc(t("gr.catenaTitolo"))}</h3><p>${esc(t("gr.catenaTesto"))}</p></div>
      <div class="lista" style="margin-top:12px">${voci}</div></div>`;
  };

  /** Le due classi che bloccano, affiancate ma mai mescolate. */
  const cosaManca = (modello) => {
    const lacune = modello.grafo.knowledge_gaps || [];
    const difetti = ((modello.grafo.validation || {}).issues) || [];
    if (!lacune.length && !difetti.length) {
      return `<div class="lavoro-pad"><div class="vuoto">
        <strong>${esc(t("gr.nienteBlocca"))}</strong><p>${esc(t("gr.nienteBloccaTesto"))}</p></div></div>`;
    }
    return `<div class="lavoro-pad">
      ${lacune.length ? `<section class="gruppo">
        <div class="gruppo-capo"><h3>${esc(t("gr.lacuneTitolo", { n: lacune.length }))}</h3>
          <p>${esc(t("gr.lacuneTesto"))}</p></div>
        <div class="lista">${lacune.map((lacuna) => {
          const id = (lacuna.evidence_ids || [])[0];
          const evidenza = id ? modello.evidenzePerId.get(id) : null;
          return `<button type="button" class="voce" ${evidenza ? `data-scegli="evidenza" data-id="${esc(id)}"` : ""}>
            <span class="voce-capo"><span class="badge attesa"><span class="punto" aria-hidden="true"></span>${esc(t("gr.lacuna"))}</span>
              <strong>${esc(root.titoloLacuna(lacuna.code))}</strong></span>
            <span class="voce-testo">${esc(lacuna.message)}</span>
            ${evidenza ? `<span class="voce-meta">${esc(root.descriviLocator(evidenza.locator))}</span>` : ""}
          </button>`;
        }).join("")}</div></section>` : ""}
      ${difetti.length ? `<section class="gruppo">
        <div class="gruppo-capo"><h3>${esc(t("gr.difettiTitolo", { n: difetti.length }))}</h3>
          <p>${esc(t("gr.difettiTesto"))}</p></div>
        <div class="lista">${difetti.map((difetto) => `
          <button type="button" class="voce" ${difetto.node_id ? `data-scegli="nodo" data-id="${esc(difetto.node_id)}"` : ""}>
            <span class="voce-capo"><span class="badge errore"><span class="punto" aria-hidden="true"></span>${esc(t("gr.difetto"))}</span>
              <strong>${esc(root.titoloDifetto(difetto.code))}</strong></span>
            <span class="voce-testo">${esc(difetto.message)}</span>
          </button>`).join("")}</div></section>` : ""}
    </div>`;
  };

  const confronto = () => {
    const barriera = state.graph.merge_barrier;
    const trovate = barriera.exact_matches || [];
    const pronto = barriera.state === "ready";
    return `<div class="lavoro-pad">
      <div class="gruppo-capo"><h3>${esc(t("gr.confronto"))}</h3><p>${esc(t("gr.confrontoTesto"))}</p></div>
      <div class="nota ${pronto ? "info" : "attesa"}" style="margin-top:12px">
        <span class="segno" aria-hidden="true">${pronto ? "i" : "?"}</span>
        <strong>${esc(pronto ? t("gr.confrontoPronto") : t("gr.confrontoNonPronto"))}</strong>
        <span>${esc(pronto ? n(trovate.length, "gr.corrispondenze")
          : t("gr.daVerificareAncora", { n: barriera.pending_source_ids.length }))}</span>
      </div>
      ${trovate.length ? `<div class="lista" style="margin-top:16px">
        ${trovate.map((voce) => `<div class="voce">
          <span class="voce-capo">
            <span class="ruolo tipo-${esc(voce.node_type)}"><i aria-hidden="true"></i>${esc(root.etichettaTipo(voce.node_type))}</span>
            <strong>${esc(voce.label)}</strong></span>
          <span class="voce-meta">${esc(t("gr.presenteIn", { n: voce.occurrences.map((o) => o.source_name).join(" · ") }))}</span>
        </div>`).join("")}</div>` : ""}
      <p class="voce-meta" style="margin-top:16px">${esc(t("gr.multilingua"))}</p>
    </div>`;
  };

  const contenuto = (vista, modello) => {
    if (state.view === "confronto") return confronto();
    if (!modello) {
      return `<div class="lavoro-pad"><div class="vuoto">
        <strong>${esc(t("gr.nonCostruito"))}</strong><p>${esc(t("gr.nonCostruitoTesto"))}</p></div></div>`;
    }
    if (state.view === "elementi") return tabellaElementi(modello);
    if (state.view === "collegamenti") return tabellaCollegamenti(modello);
    if (state.view === "righe") return listaRighe(modello);
    if (state.view === "manca") return cosaManca(modello);
    if (state.view === "catene") return catene(modello);
    return mappa(modello);
  };

  /* ------------------------------------------------------ montaggio mappa */
  const smonta = () => { if (explorer) { explorer.distruggi(); explorer = null; } };

  const montaMappa = (contenitore, vista, modello) => {
    smonta();
    const ospite = contenitore.querySelector("[data-grafo]");
    if (!ospite || !modello) return;
    explorer = root.creaExplorer(ospite, {
      chiaveFonte: vista.source_id,
      nodi: modello.nodi.map((nodo) => ({
        id: nodo.node_id, tipo: nodo.node_type, etichetta: nodo.label,
        occorrenze: nodo.evidence_ids.length,
        lacuna: modello.lacunePerNodo.has(nodo.node_id),
        difetto: modello.difettiPerNodo.has(nodo.node_id),
      })),
      archi: modello.legami.map((legame) => ({
        id: legame.relation_id, da: legame.from_id, a: legame.to_id,
        etichettaTipo: root.etichettaRelazione(legame.relation_type),
      })),
    }, {
      descrizione: t("gr.mappaDi", { n: modello.nodi.length, c: modello.legami.length }),
      etichettaTipo: root.etichettaTipo,
      testoOccorrenze: (quante) => n(quante, "isp.righeLette"),
      selezione: () => state.selection,
      onSelezione: (genere, id) => root.applicaSelezione(genere, id),
      onZoom: (k) => {
        const etichetta = contenitore.querySelector("[data-zoom-valore]");
        if (etichetta) etichetta.textContent = `${Math.round(k * 100)}%`;
      },
    });
    explorer.evidenzia(state.selection);
  };

  const ridisegnaContenuto = () => {
    const contenitore = root.appElement.querySelector('[data-regione="lavoro"] .lavoro-scorri');
    if (!contenitore) { root.render({ regioni: ["lavoro"] }); return; }
    const vista = vistaFonte();
    const modello = modelloDi(vista);
    smonta();
    root.paint(contenitore, contenuto(vista, modello));
    if (state.view === "mappa") montaMappa(contenitore, vista, modello);
  };

  /* ---------------------------------------------------------------- fase */
  root.phases.graph = {
    mostraIspettore: true,
    carica,

    titolo() {
      const vista = vistaFonte();
      if (state.view === "confronto") return { titolo: t("gr.confronto"), chips: "" };
      if (!vista) return { titolo: t("fase.graph"), chips: "" };
      const grafo = vista.subgraph;
      const tono = vista.state === "approved" ? "ok" : vista.state === "rejected" ? "errore" : "attesa";
      const chips = [
        `<span class="chip ${tono}">${esc(root.etichettaStato(vista.state))}</span>`,
        grafo ? `<span class="chip"><b>${grafo.nodes.length}</b> ${esc(t("gr.vista.elementi").toLocaleLowerCase())}</span>` : "",
        grafo ? `<span class="chip"><b>${grafo.relations.length}</b> ${esc(t("gr.vista.collegamenti").toLocaleLowerCase())}</span>` : "",
      ].filter(Boolean).join("");
      return { titolo: vista.source_name, chips };
    },

    navExtra() {
      if (!state.graph) return "";
      const barriera = state.graph.merge_barrier;
      const pronto = barriera.state === "ready";
      return `<button type="button" class="nav-item ${state.view === "confronto" ? "active" : ""}" data-confronto>
        <span class="nav-sigla" aria-hidden="true">⋈</span>
        <span class="nav-label">${esc(t("gr.confronto"))}</span>
        <span class="nav-meta">${pronto ? (barriera.exact_matches || []).length : "—"}</span>
      </button>`;
    },

    bindNav(contenitore) {
      root.delegate(contenitore, "click", "[data-confronto]", () => {
        state.view = "confronto";
        root.clearSelection();
        root.render();
      });
    },

    renderLavoro() {
      if (!state.workspace || state.graphLoading) {
        return `<div class="stato-pagina"><strong>${esc(t("gr.carico"))}</strong><p>${esc(t("gr.caricoTesto"))}</p></div>`;
      }
      if (state.graphError && !state.graph) {
        return `<div class="stato-pagina"><strong>${esc(t("gr.erroreTitolo"))}</strong>
          <p role="alert">${esc(state.graphError)}</p>
          <button type="button" class="btn primario" data-riprova>${esc(t("ui.riprova"))}</button></div>`;
      }
      if (!state.graph || !state.graph.sources.length) {
        return `<div class="stato-pagina"><strong>${esc(t("gr.nessunaFonte"))}</strong><p>${esc(t("gr.nessunaFonteTesto"))}</p></div>`;
      }
      const vista = vistaFonte();
      const modello = modelloDi(vista);
      if (vista && vista.state === "deferred") {
        return `<div class="lavoro-pad"><section class="deferred-card">
          <span class="deferred-icon" aria-hidden="true">PDF</span>
          <div><strong>${esc(t("gr.pdfDifferito"))}</strong><p>${esc(t("gr.pdfDifferitoTesto"))}</p></div>
        </section></div>`;
      }
      const testa = state.view === "confronto" ? "" : `
        <div class="intestazione-lavoro"><p>${esc(vista && vista.subgraph ? t("gr.sotto") : t("gr.nonCostruito"))}</p></div>`;
      return `${testa}
        ${modello && state.view !== "confronto" ? barra(modello) : ""}
        <div class="lavoro-scorri">${contenuto(vista, modello)}</div>`;
    },

    bindLavoro(contenitore) {
      root.delegate(contenitore, "click", "[data-riprova]", () => esegui(async () => {
        await carica();
        if (!state.graph) throw new Error(state.graphError || t("gr.erroreTitolo"));
        return state.graph;
      }));
      root.delegate(contenitore, "click", "[data-vista]", (elemento) => {
        state.view = elemento.dataset.vista;
        root.render({ regioni: ["lavoro"] });
      });
      root.delegate(contenitore, "click", "[data-scegli]", (elemento) => {
        root.applicaSelezione(elemento.dataset.scegli, elemento.dataset.id);
      });
      root.delegate(contenitore, "click", "[data-azzera]", () => {
        state.filters = { query: "", nodeType: "all", relationType: "all", onlyGaps: false, focus: false };
        root.render({ regioni: ["lavoro"] });
      });
      root.delegate(contenitore, "change", "[data-filtro]", (elemento) => {
        const chiave = elemento.dataset.filtro;
        state.filters[chiave] = elemento.type === "checkbox" ? elemento.checked : elemento.value;
        ridisegnaContenuto();
      });
      root.delegate(contenitore, "click", "[data-zoom]", (elemento) => {
        if (!explorer) return;
        const azione = elemento.dataset.zoom;
        if (azione === "adatta") explorer.inquadra();
        else explorer.zoom(azione === "piu" ? 1.25 : 1 / 1.25);
      });
      root.delegate(contenitore, "click", "[data-ridisponi]", () => { if (explorer) explorer.ridisponi(); });
      const cerca = contenitore.querySelector("[data-cerca]");
      if (cerca) {
        cerca.addEventListener("input", () => {
          window.clearTimeout(cercaTimer);
          cercaTimer = window.setTimeout(() => {
            state.filters.query = cerca.value;
            ridisegnaContenuto();
          }, 180);
        });
      }
    },

    dopoLavoro(contenitore) {
      const scorri = contenitore.querySelector(".lavoro-scorri");
      if (state.view !== "mappa" || !scorri) { smonta(); return; }
      const vista = vistaFonte();
      montaMappa(scorri, vista, modelloDi(vista));
    },

    /* Selezionare non ricostruisce la mappa: cambia solo le classi. */
    suSelezione() {
      if (state.view === "mappa" && explorer) explorer.evidenzia(state.selection);
      else ridisegnaContenuto();
    },

    renderIspettore() {
      if (state.view === "confronto") {
        return `<div class="ispettore-vuoto"><strong>${esc(t("gr.confronto"))}</strong>
          <p>${esc(t("gr.confrontoNonModifica"))}</p></div>`;
      }
      const vista = vistaFonte();
      return root.renderIspettoreGrafo(vista, modelloDi(vista) || {
        nodiPerId: new Map(), evidenzePerId: new Map(), legamiPerNodo: new Map(),
        lacunePerNodo: new Map(), lacunePerEvidenza: new Map(), difettiPerNodo: new Map(),
      });
    },

    bindIspettore(contenitore) { root.bindIspettoreGrafo(contenitore); },

    renderDecisione() {
      if (!state.graph || state.view === "confronto") return "";
      const vista = vistaFonte();
      if (!vista) return "";
      const grafo = vista.subgraph;
      const occupato = state.graphBusy ? "disabled" : "";
      const errore = state.graphError ? `<p class="campo-errore" role="alert">${esc(state.graphError)}</p>` : "";

      if (state.rejectingSourceId === vista.source_id) {
        return `<form class="decisione-nota" data-nota>
          <label class="campo"><span>${esc(t("dec.cosaCorreggere"))}</span>
            <textarea name="note" required minlength="3" placeholder="${esc(t("dec.notaP"))}"></textarea></label>
          <div class="decisione-nota-azioni">
            <button type="submit" class="btn primario" ${occupato}>${esc(t("dec.registra"))}</button>
            <button type="button" class="btn quieto" data-annulla-nota>${esc(t("ui.annulla"))}</button>
          </div>${errore}</form>`;
      }

      const riga = (titolo, testo, azioni, ostacoli) => `
        <div class="decisione-riga">
          <div class="decisione-testo" aria-live="polite"><strong>${esc(titolo)}</strong><span>${esc(testo)}</span></div>
          ${ostacoli || ""}${azioni ? `<div class="decisione-azioni">${azioni}</div>` : ""}
        </div>${errore}`;

      if (vista.state === "waiting") {
        return riga(t("dec.strutturaNonConfermata"), vista.message,
          `<button type="button" class="btn secondario" data-vai="structure">${esc(t("dec.vaiStruttura"))}</button>`);
      }
      if (vista.state === "deferred") {
        return riga(t("gr.pdfNessunaAzione"), t("gr.pdfNessunaAzioneTesto"), "");
      }
      if (!grafo) {
        return riga(t("gr.nonCostruitoTitolo"), t("gr.nonCostruitoTesto"),
          `<button type="button" class="btn primario" data-costruisci ${occupato}>${esc(state.graphBusy ? t("gr.costruendo") : t("gr.costruisci"))}</button>`);
      }
      if (vista.state === "approved") return riga(t("dec.verificata"), t("dec.garanzia"), "");
      if (vista.state === "rejected") {
        return riga(
          t("dec.segnalata"),
          grafo.decision_note || t("dec.segnalazioneRegistrata"),
          `<button type="button" class="btn primario" data-vai="structure">${esc(t("dec.rivediStruttura"))}</button>`
        );
      }

      const lacune = (grafo.knowledge_gaps || []).length;
      const difetti = (((grafo.validation || {}).issues) || []).length;
      const ostacoli = `<div class="ostacoli">
        ${lacune ? `<button type="button" class="ostacolo lacuna" data-vista="manca">${esc(n(lacune, "dec.lacuneNeiDati"))}</button>` : ""}
        ${difetti ? `<button type="button" class="ostacolo difetto" data-vista="manca">${esc(n(difetti, "dec.difettiTecnici"))}</button>` : ""}
      </div>`;
      const azioni = `
        <button type="button" class="btn pericolo" data-segnala ${occupato}>${esc(t("dec.segnala"))}</button>
        <button type="button" class="btn primario" data-approva ${grafo.approval_eligible ? occupato : "disabled"}>${esc(t("dec.conferma"))}</button>`;
      return riga(
        grafo.approval_eligible ? t("dec.domanda") : t("dec.nonVerificabile"),
        grafo.approval_eligible ? t("dec.garanzia") : t("dec.nonVerificabileTesto"),
        azioni,
        grafo.approval_eligible ? "" : ostacoli
      );
    },

    bindDecisione(contenitore) {
      root.delegate(contenitore, "click", "[data-costruisci]", () => {
        const vista = vistaFonte();
        esegui(() => root.api(
          `/api/workspaces/${encodeURIComponent(wsId())}/g3/sources/${encodeURIComponent(vista.source_id)}/generate`,
          { method: "POST" }
        ));
      });
      root.delegate(contenitore, "click", "[data-approva]", () => {
        const vista = vistaFonte();
        esegui(() => root.api(
          `/api/g3/subgraphs/${encodeURIComponent(vista.subgraph.source_subgraph_revision_id)}/decision`,
          { method: "POST", body: { action: "approve", note: null } }
        ));
      });
      root.delegate(contenitore, "click", "[data-segnala]", () => {
        state.rejectingSourceId = (vistaFonte() || {}).source_id || "";
        root.render({ regioni: ["decisione"] });
        contenitore.querySelector("textarea")?.focus();
      });
      root.delegate(contenitore, "click", "[data-annulla-nota]", () => {
        state.rejectingSourceId = "";
        root.render({ regioni: ["decisione"] });
      });
      root.delegate(contenitore, "click", "[data-vista]", (elemento) => {
        state.view = elemento.dataset.vista;
        root.render({ regioni: ["lavoro"] });
      });
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
      root.delegate(contenitore, "submit", "[data-nota]", (modulo, evento) => {
        evento.preventDefault();
        const nota = String(new FormData(modulo).get("note") || "").trim();
        if (!nota) return;
        const vista = vistaFonte();
        state.rejectingSourceId = "";
        esegui(() => root.api(
          `/api/g3/subgraphs/${encodeURIComponent(vista.subgraph.source_subgraph_revision_id)}/decision`,
          { method: "POST", body: { action: "reject", note: nota } }
        ));
      });
    },
  };

  /* ==========================================================================
     Il sottografo di una fonte, come superficie riusabile.

     Lo stesso grafo si guarda da due posti: il secondo passo dentro la fonte,
     dove il lavoro su quel file si chiude, e la fase del grafo, finché resta.
     Una sola implementazione — modello, mappa, decisione — esposta qui; chi
     la usa decide solo dove metterla e con quali parole.
     ====================================================================== */
  root.sottografo = {
    carica,
    smonta,
    vista: (sourceId) => (state.graph
      ? state.graph.sources.find((v) => v.source_id === sourceId) || null : null),
    modello: modelloDi,
    mappa,
    monta: montaMappa,

    /** Vero se la mappa è a schermo e ha assorbito la selezione da sola. */
    evidenzia(selezione) {
      if (!explorer) return false;
      explorer.evidenzia(selezione);
      return true;
    },

    /**
     * Ridisegna solo la mappa, non la pagina.
     *
     * I filtri stanno nella striscia sopra l'area che scorre: rifare tutto
     * significherebbe rifare anche loro, e chi sta scrivendo nella casella di
     * ricerca perderebbe il fuoco a ogni lettera.
     */
    ridisegna(contenitore) {
      const scorri = (contenitore || root.appElement).querySelector(".lavoro-scorri");
      const fonte = root.fonteAttiva();
      const vista = fonte ? root.sottografo.vista(fonte.source_id) : null;
      if (!scorri || !vista || !vista.subgraph) { root.render({ regioni: ["lavoro"] }); return; }
      const modello = modelloDi(vista);
      smonta();
      root.paint(scorri, mappa(modello));
      montaMappa(scorri, vista, modello);
    },

    /** I comandi che vivono sopra e dentro la mappa. */
    bindMappa(contenitore) {
      const ridisegna = () => root.sottografo.ridisegna(contenitore);
      root.delegate(contenitore, "click", "[data-scegli]", (elemento) => {
        root.applicaSelezione(elemento.dataset.scegli, elemento.dataset.id);
      });
      root.delegate(contenitore, "click", "[data-azzera]", () => {
        state.filters = { query: "", nodeType: "all", relationType: "all", onlyGaps: false, focus: false };
        root.render({ regioni: ["lavoro"] });
      });
      root.delegate(contenitore, "change", "[data-filtro]", (elemento) => {
        const chiave = elemento.dataset.filtro;
        state.filters[chiave] = elemento.type === "checkbox" ? elemento.checked : elemento.value;
        ridisegna();
      });
      root.delegate(contenitore, "click", "[data-zoom]", (elemento) => {
        if (!explorer) return;
        const azione = elemento.dataset.zoom;
        if (azione === "adatta") explorer.inquadra();
        else explorer.zoom(azione === "piu" ? 1.25 : 1 / 1.25);
      });
      root.delegate(contenitore, "click", "[data-ridisponi]", () => { if (explorer) explorer.ridisponi(); });
      const cerca = contenitore.querySelector("[data-cerca]");
      if (cerca && !cerca.dataset.legato) {
        cerca.dataset.legato = "1";
        cerca.addEventListener("input", () => {
          window.clearTimeout(cercaTimer);
          cercaTimer = window.setTimeout(() => {
            state.filters.query = cerca.value;
            ridisegna();
          }, 180);
        });
      }
    },

    /**
     * Che cosa deve fare l'operatore, dentro la fonte, su questo grafo.
     *
     * Una riga sola, in fondo alla pagina, dove sta ogni decisione di questo
     * applicativo: a sinistra perché, a destra il tasto. Mai più di un tasto
     * principale per volta.
     */
    decisione(vista, fonte) {
      const occupato = state.graphBusy ? "disabled" : "";
      const errore = state.graphError ? `<p class="campo-errore" role="alert">${esc(state.graphError)}</p>` : "";
      const riga = (titolo, testo, azioni, ostacoli) => `
        <div class="decisione-riga">
          <div class="decisione-testo" aria-live="polite"><strong>${esc(titolo)}</strong><span>${esc(testo)}</span></div>
          ${ostacoli || ""}${azioni ? `<div class="decisione-azioni">${azioni}</div>` : ""}
        </div>${errore}`;

      if (fonte.source_kind === "pdf" || (vista && vista.state === "deferred")) {
        return riga(t("gr.pdfNessunaAzione"), t("gr.pdfNessunaAzioneTesto"), "");
      }
      if (!vista || vista.state === "waiting") {
        return riga(t("fon.nonConfermata"), t("fon.nonConfermataTesto"),
          `<button type="button" class="btn primario" data-passo="lettura">${esc(t("fon.tornaLettura"))}</button>`);
      }
      const grafo = vista.subgraph;
      if (!grafo) {
        const voce = root.journeySource ? root.journeySource(vista.source_id) : null;
        const rifatto = voce && voce.graph_revision_count > 0;
        return riga(
          t(rifatto ? "fon.rifare" : "fon.daCostruire"),
          t(rifatto ? "fon.rifareTesto" : "fon.daCostruireTesto"),
          `<button type="button" class="btn primario" data-costruisci ${occupato}>${
            esc(state.graphBusy ? t("gr.costruendo") : t("gr.costruisci"))}</button>`
        );
      }
      if (state.rejectingSourceId === vista.source_id) {
        return `<form class="decisione-nota" data-nota>
          <label class="campo"><span>${esc(t("dec.cosaCorreggere"))}</span>
            <textarea name="note" required minlength="3" placeholder="${esc(t("dec.notaP"))}"></textarea></label>
          <div class="decisione-nota-azioni">
            <button type="submit" class="btn primario" ${occupato}>${esc(t("dec.registra"))}</button>
            <button type="button" class="btn quieto" data-annulla-nota>${esc(t("ui.annulla"))}</button>
          </div>${errore}</form>`;
      }
      if (vista.state === "approved") return riga(t("dec.verificata"), t("dec.garanzia"), "");
      if (vista.state === "rejected") {
        return riga(t("dec.segnalata"), grafo.decision_note || t("dec.segnalazioneRegistrata"),
          `<button type="button" class="btn primario" data-passo="lettura">${esc(t("fon.tornaLettura"))}</button>`);
      }
      const lacune = (grafo.knowledge_gaps || []).length;
      const difetti = (((grafo.validation || {}).issues) || []).length;
      /* Toccarli non porta altrove: riporta la colonna di destra alla
         panoramica, dove quegli stessi ostacoli sono elencati per esteso. */
      const ostacoli = `<div class="ostacoli">
        ${lacune ? `<button type="button" class="ostacolo lacuna" data-panoramica>${esc(n(lacune, "dec.lacuneNeiDati"))}</button>` : ""}
        ${difetti ? `<button type="button" class="ostacolo difetto" data-panoramica>${esc(n(difetti, "dec.difettiTecnici"))}</button>` : ""}
      </div>`;
      return riga(
        grafo.approval_eligible ? t("dec.domanda") : t("dec.nonVerificabile"),
        grafo.approval_eligible ? t("dec.garanzia") : t("dec.nonVerificabileTesto"),
        `<button type="button" class="btn pericolo" data-segnala ${occupato}>${esc(t("dec.segnala"))}</button>
         <button type="button" class="btn primario" data-approva ${grafo.approval_eligible ? occupato : "disabled"}>${esc(t("dec.conferma"))}</button>`,
        grafo.approval_eligible ? "" : ostacoli
      );
    },

    bindDecisione(contenitore, esecutore) {
      const corrente = () => {
        const fonte = root.fonteAttiva();
        return fonte ? root.sottografo.vista(fonte.source_id) : null;
      };
      root.delegate(contenitore, "click", "[data-costruisci]", () => {
        const vista = corrente();
        if (!vista) return;
        esecutore(() => root.api(
          `/api/workspaces/${encodeURIComponent(wsId())}/g3/sources/${encodeURIComponent(vista.source_id)}/generate`,
          { method: "POST" }
        ));
      });
      root.delegate(contenitore, "click", "[data-approva]", () => {
        const vista = corrente();
        if (!vista || !vista.subgraph) return;
        esecutore(() => root.api(
          `/api/g3/subgraphs/${encodeURIComponent(vista.subgraph.source_subgraph_revision_id)}/decision`,
          { method: "POST", body: { action: "approve", note: null } }
        ));
      });
      root.delegate(contenitore, "click", "[data-segnala]", () => {
        state.rejectingSourceId = (corrente() || {}).source_id || "";
        root.render({ regioni: ["decisione"] });
        contenitore.querySelector("textarea")?.focus();
      });
      root.delegate(contenitore, "click", "[data-annulla-nota]", () => {
        state.rejectingSourceId = "";
        root.render({ regioni: ["decisione"] });
      });
      root.delegate(contenitore, "click", "[data-panoramica]", () => {
        root.clearSelection();
        root.render({ regioni: ["ispettore"] });
      });
      root.delegate(contenitore, "submit", "[data-nota]", (modulo, evento) => {
        evento.preventDefault();
        const nota = String(new FormData(modulo).get("note") || "").trim();
        const vista = corrente();
        if (!nota || !vista || !vista.subgraph) return;
        state.rejectingSourceId = "";
        esecutore(() => root.api(
          `/api/g3/subgraphs/${encodeURIComponent(vista.subgraph.source_subgraph_revision_id)}/decision`,
          { method: "POST", body: { action: "reject", note: nota } }
        ));
      });
    },
  };
})();
