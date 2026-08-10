(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const esc = root.escapeHtml;
  const t = root.t;
  const n = root.n;

  const chiudi = `<button type="button" class="btn quieto piccolo chiudi-ispettore" data-chiudi-ispettore>${esc(t("ui.chiudiDettaglio"))}</button>`;

  const vuoto = (titolo, testo) => `
    <div class="ispettore-vuoto"><strong>${esc(titolo)}</strong><p>${esc(testo)}</p></div>`;

  const pastiglia = (tipo, etichetta) => `
    <span class="ispettore-tipo tipo-${esc(tipo)}"><i aria-hidden="true"></i>${esc(etichetta)}</span>`;

  /** Blocco 2 — la revisione non sparisce mai dalla vista: niente è definitivo. */
  const blocoRevisione = (fonte) => {
    const tono = fonte.state === "approved" ? "ok" : fonte.state === "rejected" ? "errore" : "attesa";
    const journey = root.journeySource ? root.journeySource(fonte.source_id) : null;
    const versioni = journey && journey.graph_revision_count;
    return `
      <section class="blocco">
        <h4>${esc(t("isp.statoVerifica"))}${versioni ? `<span>${esc(t(versioni === 1 ? "isp.versione1" : "isp.versioni", { n: versioni }))}</span>` : ""}</h4>
        <span class="badge ${tono}"><span class="punto" aria-hidden="true"></span>${esc(root.etichettaStato(fonte.state))}</span>
        <p>${esc(t(`isp.stato.${fonte.state}`))}</p>
        ${fonte.subgraph.supersedes ? `<p class="version-note">${esc(t("isp.sostituisce"))}</p>` : ""}
      </section>`;
  };

  /** Blocco 3 — ogni riga porta all'elemento dall'altra parte del collegamento. */
  const bloccoLegami = (modello, nodoId) => {
    const legami = modello.legamiPerNodo.get(nodoId) || [];
    if (!legami.length) {
      return `<section class="blocco"><h4>${esc(t("isp.collegamenti"))}</h4>
        <p class="blocco-vuoto">${esc(t("isp.nessunCollegamento"))}</p></section>`;
    }
    const gruppi = new Map();
    legami.forEach((legame) => {
      const uscente = legame.from_id === nodoId;
      const altro = modello.nodiPerId.get(uscente ? legame.to_id : legame.from_id);
      if (!altro) return;
      const etichetta = root.etichettaRelazione(legame.relation_type);
      const chiave = `${etichetta}|${uscente}`;
      if (!gruppi.has(chiave)) gruppi.set(chiave, { etichetta, uscente, voci: [] });
      gruppi.get(chiave).voci.push({ legame, altro });
    });
    const corpo = [...gruppi.values()].map((gruppo) => `
      <div class="gruppo-legami">
        <span>${esc(gruppo.uscente ? gruppo.etichetta : t("isp.inEntrata", { r: gruppo.etichetta }))}</span>
        ${gruppo.voci.map(({ legame, altro }) => `
          <button type="button" class="riga-legame tipo-${esc(altro.node_type)}"
            data-scegli="nodo" data-id="${esc(altro.node_id)}">
            <i aria-hidden="true"></i>
            <span class="nome">${esc(altro.label)}</span>
            <span class="coda">${esc(n(legame.evidence_ids.length, "isp.righeLette").replace(/^\d+\s/, ""))}</span>
          </button>`).join("")}
      </div>`).join("");
    return `<section class="blocco"><h4>${esc(t("isp.collegamenti"))} <span>${legami.length}</span></h4>${corpo}</section>`;
  };

  /**
   * Blocco 3-bis — la catena diagnostica, che è il modo in cui un manutentore
   * racconta un guasto: da che cosa lo si riconosce, che cosa tocca, come si
   * risolve. Le relazioni una per una dicono se un collegamento esiste; la
   * catena dice se il racconto sta in piedi, ed è lì che si verifica davvero.
   */
  const catenaDi = (modello, causa) => {
    const legami = modello.legamiPerNodo.get(causa.node_id) || [];
    const prendi = (tipo, lato) => legami.filter((l) => l.relation_type === tipo)
      .map((l) => modello.nodiPerId.get(lato === "from" ? l.from_id : l.to_id)).filter(Boolean);
    return {
      causa,
      indizi: [...prendi("MAY_INDICATE", "from"), ...prendi("INDICATES", "from")],
      azioni: prendi("RESOLVED_BY", "to"),
      componenti: prendi("AFFECTS", "to"),
    };
  };

  const passoCatena = (nodo, corrente) => `
    <button type="button" class="catena-passo tipo-${esc(nodo.node_type)} ${corrente === nodo.node_id ? "qui" : ""}"
      data-scegli="nodo" data-id="${esc(nodo.node_id)}">
      <i aria-hidden="true"></i><span>${esc(nodo.label)}</span></button>`;

  /**
   * Una catena è una scheda con un capo: la causa.
   *
   * Impilate senza capo si leggevano come un elenco unico, e la causa aveva lo
   * stesso aspetto degli altri passi — non si capiva dove finiva una storia e
   * dove cominciava la successiva. Qui la causa sta in testa, e sotto stanno i
   * due lati del racconto, ciascuno con il suo nome.
   */
  const lato = (etichetta, nodi, vuota, corrente) => `
    <div class="catena-lato">
      <span class="catena-etichetta">${esc(etichetta)}</span>
      <div class="catena-passi">
        ${nodi.length
          ? nodi.map((nodo) => passoCatena(nodo, corrente)).join("")
          : `<span class="catena-passo vuoto">${esc(vuota)}</span>`}
      </div>
    </div>`;

  const scheda = (catena, corrente) => {
    const manca = [];
    if (!catena.indizi.length) manca.push(t("gr.senzaSintomo"));
    if (!catena.azioni.length) manca.push(t("gr.senzaAzione"));
    return `<article class="catena-scheda">
      <div class="catena-capo">${passoCatena(catena.causa, corrente)}</div>
      ${lato(t("gr.catenaRiconosce"), catena.indizi, t("gr.origineNonDichiarata"), corrente)}
      ${lato(t("gr.catenaRisolve"), catena.azioni, t("gr.azioneNonDichiarata"), corrente)}
      ${catena.componenti.length
        ? `<div class="catena-lato"><span class="catena-etichetta">${esc(t("gr.catenaInteressa"))}</span>
            <div class="catena-passi">${catena.componenti.map((nodo) => passoCatena(nodo, corrente)).join("")}</div>
          </div>` : ""}
      ${manca.length ? `<p class="voce-meta">${esc(t("gr.catenaIncompleta", { n: manca.join(" · ") }))}</p>` : ""}
    </article>`;
  };

  /** Le catene che riguardano un elemento: la sua, se è una causa; quelle in
      cui compare, se è un sintomo, un codice, un'azione o un componente.
      Le cause fra cui scegliere sono quelle visibili: filtrare la mappa fino a
      zero e trovare qui tutte le catene di prima faceva leggere due grafi
      diversi affiancati. I passi dentro una catena non si filtrano invece
      mai: una storia mutilata non è una storia più corta, è una falsa. */
  const bloccoCatene = (modello, nodo) => {
    const cause = modello.nodi.filter((voce) => voce.node_type === "FailureMode");
    const scelte = !nodo ? cause : nodo.node_type === "FailureMode" ? [nodo] : cause.filter((causa) => (
      (modello.legamiPerNodo.get(causa.node_id) || [])
        .some((l) => l.from_id === nodo.node_id || l.to_id === nodo.node_id)
    ));
    if (!scelte.length) {
      return `<section class="blocco"><h4>${esc(t("gr.catenaTitolo"))}</h4>
        <p class="blocco-vuoto">${esc(t("gr.nienteCatene"))}</p></section>`;
    }
    return `<section class="blocco">
      <h4>${esc(t("gr.catenaTitolo"))} <span>${scelte.length}</span></h4>
      ${scelte.map((causa) => scheda(catenaDi(modello, causa), nodo ? nodo.node_id : "")).join("")}
      ${nodo ? "" : `<p>${esc(t("gr.catenaTesto"))}</p>`}
    </section>`;
  };

  /** Blocco 4 — quante righe distinte sono state consolidate in questa voce. */
  const bloccoOccorrenze = (quante, chiave) => `
    <section class="blocco">
      <h4>${esc(t("isp.occorrenze"))}</h4>
      <p class="occorrenze"><strong>${quante}</strong> <span>${esc(t(quante === 1 ? `${chiave}1` : chiave))}</span></p>
    </section>`;

  /** Blocco 5 — la strada di ritorno alla riga originale, sempre. */
  const bloccoEvidenze = (modello, ids, titolo) => {
    const voci = (ids || []).map((id) => modello.evidenzePerId.get(id)).filter(Boolean);
    if (!voci.length) {
      return `<section class="blocco"><h4>${esc(titolo)}</h4><p class="blocco-vuoto">${esc(t("isp.nessunaRiga"))}</p></section>`;
    }
    return `
      <section class="blocco">
        <h4>${esc(titolo)} <span>${voci.length}</span></h4>
        ${voci.map((voce) => `
          <button type="button" class="evidenza" data-scegli="evidenza" data-id="${esc(voce.evidence_id)}"
            aria-selected="${state.selection.kind === "evidence" && state.selection.id === voce.evidence_id}">
            <span class="dove">${esc(root.descriviLocator(voce.locator))}</span>
            <span class="testo">${esc(voce.excerpt || t("gr.rigaSenzaTesto"))}</span>
          </button>`).join("")}
      </section>`;
  };

  /** Blocco 6 — le due classi che bloccano, distinte e mai mescolate. */
  const bloccoOstacoli = (lacune, difetti) => {
    if (!lacune.length && !difetti.length) {
      return `<section class="blocco"><h4>${esc(t("isp.cosaManca"))}</h4>
        <p class="blocco-vuoto">${esc(t("isp.nienteBlocca"))}</p></section>`;
    }
    const riga = (tono, segno, titolo, messaggio) => `
      <div class="nota ${tono}">
        <span class="segno" aria-hidden="true">${segno}</span>
        <strong>${esc(titolo)}</strong>
        <span>${esc(messaggio)}</span>
      </div>`;
    return `
      <section class="blocco">
        <h4>${esc(t("isp.cosaManca"))}</h4>
        ${lacune.length ? `<p>${esc(t("isp.lacuneNota"))}</p>` : ""}
        ${lacune.map((l) => riga("attesa", "?", root.titoloLacuna(l.code), l.message)).join("")}
        ${difetti.length ? `<p>${esc(t("isp.difettiNota"))}</p>` : ""}
        ${difetti.map((d) => riga("errore", "!", root.titoloDifetto(d.code), d.message)).join("")}
      </section>`;
  };

  /* Panoramica della fonte, quando non c'è niente di selezionato.
     Il censimento conta quello che si vede: era l'unico posto della pagina in
     cui i filtri non arrivavano, e la mappa poteva dire «nessun elemento»
     mentre qui accanto restavano tutti i conteggi di prima. */
  const panoramica = (fonte, modello) => {
    const grafo = fonte.subgraph;
    const unite = grafo.duplicate_nodes_consolidated + grafo.duplicate_relations_consolidated;
    const conteggi = root.ordineTipi
      .map((tipo) => ({ tipo, totale: modello.nodi.filter((nodo) => nodo.node_type === tipo).length }))
      .filter((voce) => voce.totale);
    return `
      <div class="ispettore-dentro">
        ${chiudi}
        <div class="ispettore-identita">
          <span class="ispettore-tipo">${esc(t("isp.fonte"))}</span>
          <h3>${esc(fonte.source_name)}</h3>
        </div>
        ${blocoRevisione(fonte)}
        <section class="blocco">
          <h4>${esc(t("isp.costruito"))}</h4>
          ${conteggi.length ? conteggi.map((voce) => `
            <button type="button" class="riga-legame tipo-${voce.tipo}" data-filtra-tipo="${voce.tipo}">
              <i aria-hidden="true"></i>
              <span class="nome">${esc(root.etichettaTipoPl(voce.tipo))}</span>
              <span class="coda">${voce.totale}</span>
            </button>`).join("") : `<p class="blocco-vuoto">${esc(t("gr.nienteFiltri"))}</p>`}
          ${modello.nascosti ? `<p class="voce-meta">${esc(t("gr.nascosti", { n: modello.nascosti }))}
            <button type="button" class="btn quieto piccolo" data-azzera>${esc(t("gr.azzera"))}</button></p>` : ""}
        </section>
        <section class="blocco">
          <h4>${esc(t("isp.letto"))}</h4>
          <p>${esc(t("isp.lettoTesto", {
            r: n(grafo.evidence.length, "isp.righeLette"),
            c: n(grafo.relations.length, "isp.collegamentiN"),
          }))}</p>
          ${unite ? `<p>${esc(n(unite, "isp.ripetizioni"))}</p>` : ""}
        </section>
        ${bloccoOstacoli(grafo.knowledge_gaps || [], ((grafo.validation || {}).issues) || [])}
        ${bloccoCatene(modello, null)}
      </div>`;
  };

  root.renderIspettoreGrafo = function renderIspettoreGrafo(fonte, modello) {
    if (fonte && fonte.state === "deferred") {
      return vuoto(t("gr.pdfDifferito"), t("gr.pdfDifferitoTesto"));
    }
    if (!fonte || !fonte.subgraph) return vuoto(t("isp.nessunGrafo"), t("isp.nessunGrafoTesto"));
    const scelta = state.selection;

    if (scelta.kind === "node") {
      const nodo = modello.nodiPerId.get(scelta.id);
      if (!nodo) return panoramica(fonte, modello);
      return `
        <div class="ispettore-dentro">
          ${chiudi}
          <div class="ispettore-identita">
            ${pastiglia(nodo.node_type, root.etichettaTipo(nodo.node_type))}
            <h3>${esc(nodo.label)}</h3>
          </div>
          ${blocoRevisione(fonte)}
          ${bloccoLegami(modello, nodo.node_id)}
          ${bloccoCatene(modello, nodo)}
          ${bloccoOccorrenze(nodo.evidence_ids.length, "isp.occorrenzeNodo")}
          ${bloccoEvidenze(modello, nodo.evidence_ids, t("isp.righeOrigine"))}
          ${bloccoOstacoli(modello.lacunePerNodo.get(nodo.node_id) || [], modello.difettiPerNodo.get(nodo.node_id) || [])}
        </div>`;
    }

    if (scelta.kind === "relation") {
      const legame = fonte.subgraph.relations.find((voce) => voce.relation_id === scelta.id);
      if (!legame) return panoramica(fonte, modello);
      const da = modello.nodiPerId.get(legame.from_id);
      const a = modello.nodiPerId.get(legame.to_id);
      const supporti = legame.evidence_refs || [];
      return `
        <div class="ispettore-dentro">
          ${chiudi}
          <div class="ispettore-identita">
            <span class="ispettore-tipo">${esc(t("gr.collegamento"))}</span>
            <h3>${esc(root.etichettaRelazione(legame.relation_type))}</h3>
          </div>
          ${blocoRevisione(fonte)}
          <section class="blocco">
            <h4>${esc(t("isp.fraQuali"))}</h4>
            ${[da, a].filter(Boolean).map((nodo, indice) => `
              <button type="button" class="riga-legame tipo-${esc(nodo.node_type)}"
                data-scegli="nodo" data-id="${esc(nodo.node_id)}">
                <i aria-hidden="true"></i>
                <span class="nome">${esc(nodo.label)}</span>
                <span class="coda">${esc(t(indice === 0 ? "isp.daL" : "isp.aL"))}</span>
              </button>`).join("")}
          </section>
          ${supporti.length ? `<section class="blocco">
            <h4>${esc(t("isp.supportoRelazione"))} <span>${supporti.length}</span></h4>
            ${supporti.map((supporto) => `<button type="button" class="evidenza"
              data-scegli="evidenza" data-id="${esc(supporto.evidence_id)}">
              <span class="dove">${esc(supporto.source_anchor)}</span>
              <span class="testo">${esc(supporto.quote)}</span>
            </button>`).join("")}
          </section>` : ""}
          ${bloccoOccorrenze(legame.evidence_ids.length, "isp.occorrenzeArco")}
          ${bloccoEvidenze(modello, legame.evidence_ids, t("isp.righeOrigine"))}
        </div>`;
    }

    if (scelta.kind === "evidence") {
      const evidenza = modello.evidenzePerId.get(scelta.id);
      if (!evidenza) return panoramica(fonte, modello);
      const prodotti = fonte.subgraph.nodes.filter((nodo) => nodo.evidence_ids.includes(evidenza.evidence_id));
      const lacune = modello.lacunePerEvidenza.get(evidenza.evidence_id) || [];
      return `
        <div class="ispettore-dentro">
          ${chiudi}
          <div class="ispettore-identita">
            <span class="ispettore-tipo">${esc(t("isp.rigaOrigine"))}</span>
            <h3>${esc(root.descriviLocator(evidenza.locator))}</h3>
          </div>
          ${blocoRevisione(fonte)}
          <section class="blocco">
            <h4>${esc(t("isp.testoLetto"))}</h4>
            <p class="evidenza-testo" style="color:var(--text)">${esc(evidenza.excerpt || t("gr.rigaSenzaTesto"))}</p>
          </section>
          <section class="blocco">
            <h4>${esc(t("isp.haProdotto"))} <span>${prodotti.length}</span></h4>
            ${prodotti.length ? prodotti.map((nodo) => `
              <button type="button" class="riga-legame tipo-${esc(nodo.node_type)}"
                data-scegli="nodo" data-id="${esc(nodo.node_id)}">
                <i aria-hidden="true"></i>
                <span class="nome">${esc(nodo.label)}</span>
                <span class="coda">${esc(root.etichettaTipo(nodo.node_type))}</span>
              </button>`).join("") : `<p class="blocco-vuoto">${esc(t("isp.nienteProdotto"))}</p>`}
          </section>
          ${bloccoOstacoli(lacune, [])}
          <details class="disclosure">
            <summary>${esc(t("isp.datiRiga"))}</summary>
            <pre class="grezzo">${esc(JSON.stringify(evidenza.locator, null, 2))}</pre>
          </details>
        </div>`;
    }

    return panoramica(fonte, modello);
  };

  root.bindIspettoreGrafo = function bindIspettoreGrafo(contenitore) {
    root.delegate(contenitore, "click", "[data-scegli]", (elemento) => {
      root.applicaSelezione(elemento.dataset.scegli, elemento.dataset.id);
    });
    root.delegate(contenitore, "click", "[data-filtra-tipo]", (elemento) => {
      state.filters.nodeType = elemento.dataset.filtraTipo;
      /* Dentro la fonte la mappa è già a schermo: cambiare vista qui
         cancellerebbe il passo su cui l'operatore sta lavorando. */
      if (state.phase === "graph") state.view = "mappa";
      root.render({ regioni: ["lavoro", "ispettore"] });
    });
    /* Se i filtri si leggono da qui, da qui si tolgono. */
    root.delegate(contenitore, "click", "[data-azzera]", () => {
      state.filters = { query: "", nodeType: "all", relationType: "all", onlyGaps: false, focus: false };
      root.render({ regioni: ["lavoro", "ispettore"] });
    });
  };
})();
