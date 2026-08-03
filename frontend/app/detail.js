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
    return `
      <section class="blocco">
        <h4>${esc(t("isp.statoVerifica"))}</h4>
        <span class="badge ${tono}"><span class="punto" aria-hidden="true"></span>${esc(root.etichettaStato(fonte.state))}</span>
        <p>${esc(t(`isp.stato.${fonte.state}`))}</p>
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

  /* Panoramica della fonte, quando non c'è niente di selezionato. */
  const panoramica = (fonte, modello) => {
    const grafo = fonte.subgraph;
    const unite = grafo.duplicate_nodes_consolidated + grafo.duplicate_relations_consolidated;
    const conteggi = root.ordineTipi
      .map((tipo) => ({ tipo, totale: grafo.nodes.filter((nodo) => nodo.node_type === tipo).length }))
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
          ${conteggi.map((voce) => `
            <button type="button" class="riga-legame tipo-${voce.tipo}" data-filtra-tipo="${voce.tipo}">
              <i aria-hidden="true"></i>
              <span class="nome">${esc(root.etichettaTipoPl(voce.tipo))}</span>
              <span class="coda">${voce.totale}</span>
            </button>`).join("")}
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
      </div>`;
  };

  root.renderIspettoreGrafo = function renderIspettoreGrafo(fonte, modello) {
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
      state.view = "mappa";
      root.render({ regioni: ["lavoro", "ispettore"] });
    });
  };
})();
