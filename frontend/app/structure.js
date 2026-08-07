(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const esc = root.escapeHtml;
  const t = root.t;
  const n = root.n;

  const wsId = () => state.workspace.workspace.workspace_id;
  const profili = () => (state.structure && state.structure.profiles) || [];
  const profiloDi = (sourceId) => profili().find((p) => p.source_id === sourceId) || null;
  const profiloAttivo = () => {
    const fonte = root.fonteAttiva();
    return fonte ? profiloDi(fonte.source_id) : null;
  };
  const eccezioni = () => (state.structure && state.structure.exceptions) || [];
  const eccezioneAperta = () => eccezioni().find((e) => e.status === "open") || null;
  const joinProposto = () => ((state.structure && state.structure.joins) || [])
    .find((j) => j.status === "proposed") || null;

  /**
   * I due passi dentro una fonte.
   *
   * Prima si decide come il file va letto, poi si guarda che cosa ne nasce.
   * Non sono due schede fra cui scegliere: sono un ordine, e ognuno si chiude
   * con una sola azione. La cornice non sa niente del tipo di fonte — un PDF
   * percorre gli stessi due passi con dentro altre cose, e un passo nuovo
   * (la modifica del grafo, quando arriverà) si aggiunge qui senza toccare
   * il resto.
   */
  const PASSI = ["lettura", "esito"];
  const passoCorrente = () => (PASSI.includes(state.view) ? state.view : "lettura");

  const vistaGrafo = () => {
    const fonte = root.fonteAttiva();
    return fonte && root.sottografo ? root.sottografo.vista(fonte.source_id) : null;
  };

  const carica = async () => {
    if (!state.workspace) return;
    state.structureLoading = true;
    state.structureError = "";
    state.ruoloCeduto = null;
    try {
      state.structure = await root.api(
        `/api/workspaces/${encodeURIComponent(wsId())}/g2/preparation`, { method: "POST" }
      );
      /* Il secondo passo vive nella stessa pagina del primo: il suo stato si
         carica insieme, o passando da un passo all'altro si vedrebbe un buco. */
      if (root.sottografo) await root.sottografo.carica();
    } catch (errore) {
      state.structureError = errore.message;
    } finally {
      state.structureLoading = false;
    }
  };

  /* La sola lettura della preparazione, senza avviarne una: la usa la fase del
     grafo per avere il numero di righe da mettere nel menu accanto a ogni
     fonte. Se non riesce, il menu resta senza numero e nient'altro cambia. */
  root.leggiPreparazione = async function leggiPreparazione() {
    if (!state.workspace) return;
    try {
      state.structure = await root.api(`/api/workspaces/${encodeURIComponent(wsId())}/g2/preparation`);
    } catch (_) { /* il menu resta senza numero */ }
  };

  const esegui = async (azione) => {
    state.structureBusy = true;
    state.structureError = "";
    // Repaint the work pane as well: its mapping controls become disabled
    // while the server invalidates and rebuilds evidence. Leaving the old DOM
    // active allowed several changes to race and supersede each other's run.
    root.render({ regioni: ["lavoro", "decisione"] });
    try {
      state.structure = await azione();
      /* Cambiare la lettura ritira la conferma e mette da parte il grafo
         costruito su quella precedente: il secondo passo va riletto, o
         continuerebbe a mostrare un grafo che non vale più. */
      if (root.sottografo) await root.sottografo.carica();
      if (root.loadJourney) await root.loadJourney();
    } catch (errore) {
      state.structureError = errore.message;
      /* Se il cambio non è andato a segno, nessuno ha ceduto niente. */
      state.ruoloCeduto = null;
    }
    finally { state.structureBusy = false; root.render(); }
  };

  const eseguiGrafo = async (azione) => {
    state.graphBusy = true;
    state.graphError = "";
    root.render({ regioni: ["decisione"] });
    try {
      state.graph = await azione();
      if (root.loadJourney) await root.loadJourney();
    } catch (errore) { state.graphError = errore.message; }
    finally { state.graphBusy = false; root.render(); }
  };

  /* Quante domande restano su questo file. Il conto è sul profilo a cui la
     domanda appartiene, non sulla fonte a schermo: sono la stessa cosa quando
     l'operatore risponde, ma la formula resta vera anche se non lo fossero. */
  const contaDomande = (problema) => {
    const tutte = eccezioni().filter((e) => e.profile_id === problema.profile_id);
    const risposte = tutte.filter((e) => e.status !== "open" && e.status !== "queued").length;
    return { indice: risposte + 1, totale: tutte.length };
  };

  const domandeAperte = (profilo) => eccezioni().filter((e) => (
    e.profile_id === profilo.profile_id && (e.status === "open" || e.status === "queued")
  ));

  /* Le domande che riguardano una colonna diventano quella colonna, accesa
     nella tabella. Restano carte solo quelle che una colonna non ce l'hanno —
     un foglio intero da includere, un avviso sul file. */
  const domandeSuColonne = (profilo) => {
    const per = new Map();
    domandeAperte(profilo).forEach((problema) => {
      const carico = problema.payload || {};
      if (problema.exception_kind !== "mapping_ambiguous" || !carico.column) return;
      per.set(`${carico.structure_id}::${carico.column}`, problema);
    });
    return per;
  };

  /* ---------- domande che non appartengono a una colonna: restano carte ---- */
  const cartaEccezione = (problema) => {
    const carico = problema.payload || {};
    const conto = contaDomande(problema);
    const testa = `
      <p class="voce-meta">${esc(t("str.domandaDi", { i: conto.indice, t: conto.totale }))}</p>
      <h3 style="margin:0;font-size:17px;font-weight:640;letter-spacing:-.02em">${esc(problema.title)}</h3>
      <p>${esc(problema.explanation)}</p>
      <p class="voce-meta">${esc(t("str.riguarda", { f: problema.source_name }))}</p>`;

    if (problema.exception_kind === "hidden_sheet") {
      return `<section class="card entra" data-eccezione="${esc(problema.exception_id)}" style="display:grid;gap:12px">
        ${testa}
        <div style="display:flex;gap:9px;flex-wrap:wrap">
          <button type="button" class="btn primario" data-includi="false" ${state.structureBusy ? "disabled" : ""}>${esc(t("str.lasciaEscluso"))}</button>
          <button type="button" class="btn secondario" data-includi="true" ${state.structureBusy ? "disabled" : ""}>${esc(t("str.includiFoglio"))}</button>
        </div></section>`;
    }
    if (problema.severity === "warning") {
      return `<section class="card entra" data-eccezione="${esc(problema.exception_id)}" style="display:grid;gap:12px">
        ${testa}
        <div><button type="button" class="btn primario" data-preso ${state.structureBusy ? "disabled" : ""}>${esc(t("str.hoCapito"))}</button></div>
      </section>`;
    }
    if (carico.choices && carico.choices.length) {
      return `<form class="card entra" data-eccezione="${esc(problema.exception_id)}" style="display:grid;gap:12px">
        ${testa}
        <label class="campo" style="max-width:24rem"><span>${esc(t("str.cheContiene"))}</span>
          <select name="role" required>
            <option value="">${esc(t("str.scegli"))}</option>
            ${carico.choices.map((r) => `<option value="${esc(r)}">${esc(root.etichettaRuolo(r))}</option>`).join("")}
          </select></label>
        <div><button type="submit" class="btn primario" ${state.structureBusy ? "disabled" : ""}>${esc(t("str.salvaContinua"))}</button></div>
      </form>`;
    }
    return `<section class="card entra" style="display:grid;gap:12px">
      ${testa}
      <div class="nota errore"><span class="segno" aria-hidden="true">!</span>
        <strong>${esc(t("str.daSostituire"))}</strong><span>${esc(t("str.daSostituireTesto"))}</span></div>
      <div><button type="button" class="btn secondario" data-vai="documents">${esc(t("str.vaiDocumenti"))}</button></div>
    </section>`;
  };

  const cartaJoin = (join) => {
    const primo = profili().find((p) => p.profile_id === join.primary_profile_id);
    const secondo = profili().find((p) => p.profile_id === join.lookup_profile_id);
    return `<section class="card entra" data-join="${esc(join.join_spec_id)}" style="display:grid;gap:12px">
      <h3 style="margin:0;font-size:17px;font-weight:640;letter-spacing:-.02em">${esc(t("str.collegare"))}</h3>
      <p>${esc(t("str.collegareTesto", {
        a: primo ? primo.source_name : "", k: join.spec.primary_key, b: secondo ? secondo.source_name : "",
      }))}</p>
      <div style="display:flex;gap:7px;flex-wrap:wrap">
        <span class="badge">${esc(t("str.collegati", { n: join.preview.matched_records }))}</span>
        <span class="badge">${esc(t("str.nonCollegati", { n: join.preview.unmatched_records }))}</span>
      </div>
      <p class="voce-meta">${esc(t("str.collegareNota"))}</p>
      <div style="display:flex;gap:9px;flex-wrap:wrap">
        <button type="button" class="btn primario" data-join-azione="approve" ${state.structureBusy ? "disabled" : ""}>${esc(t("str.collega"))}</button>
        <button type="button" class="btn secondario" data-join-azione="reject" ${state.structureBusy ? "disabled" : ""}>${esc(t("str.separati"))}</button>
      </div></section>`;
  };

  /* ------------------------------------------- passo 1 · come si legge ---- */
  const mappaturaDi = (profilo, structureId) => (((profilo.mapping || {}).structures || {})[structureId]) || {};

  /* L'ordine è quello con cui l'operatore ragiona: prima i ruoli che
     alimentano il grafo, poi i contorni, infine le due uscite. */
  const RUOLI = [
    "observation", "cause", "action", "component", "error_code",
    "occurred_at", "measurement", "outcome", "attribute", "excluded",
  ];
  /* Ruoli assegnati che non producono un elemento proprio: viaggiano con gli
     elementi come dettaglio. Vanno mostrati lo stesso, altrimenti l'operatore
     non sa che fine ha fatto la colonna della data. */
  const CONTORNO = ["occurred_at", "measurement", "outcome"];

  /**
   * Che cosa fa ogni colonna di questa fonte, letto una volta sola.
   *
   * Lo chiedono in due: «Che cosa resta fuori», in coda alla tabella, e la
   * colonna di destra. Contarle in due posti diversi era il modo più sicuro
   * di far dire due numeri diversi alla stessa pagina.
   */
  const letturaColonne = (profilo) => {
    const alimenta = new Map();
    const contorno = new Map();
    const dato = [];
    const escluse = [];
    let totale = 0;
    (profilo.structures || []).filter((s) => s.included).forEach((struttura) => {
      const mappa = mappaturaDi(profilo, struttura.structure_id);
      (struttura.columns || []).forEach((colonna) => {
        const config = mappa[colonna.name];
        const ruolo = config ? config.role : colonna.proposed_role;
        const usata = config ? config.included : true;
        totale += 1;
        if (!usata || ruolo === "excluded") { escluse.push(colonna.name); return; }
        const dove = root.tipoDaRuolo[ruolo] ? alimenta : CONTORNO.includes(ruolo) ? contorno : null;
        if (!dove) { dato.push(colonna.name); return; }
        if (!dove.has(ruolo)) dove.set(ruolo, []);
        dove.get(ruolo).push(colonna.name);
      });
    });
    return { alimenta, contorno, dato, escluse, totale, fuori: dato.length + escluse.length };
  };

  /* Quale colonna tiene già un significato: serve a dire, subito dopo, chi lo
     ha perso. Il vincolo lo applica il motore; qui si racconta soltanto — e
     vale per ogni significato tranne i due che non ne sono uno. */
  const esclusivo = (ruolo) => ruolo && ruolo !== "attribute" && ruolo !== "excluded";
  const chiTiene = (profilo, structureId, ruolo, esclusa) => {
    if (!profilo || !esclusivo(ruolo)) return "";
    const mappa = mappaturaDi(profilo, structureId);
    const trovata = Object.entries(mappa)
      .find(([colonna, config]) => colonna !== esclusa && config.included && config.role === ruolo);
    return trovata ? trovata[0] : "";
  };

  /* Si legge la mappatura di adesso, prima che il motore la cambi: dopo, chi
     teneva il significato non lo tiene più e non ci sarebbe più niente da
     dire. */
  const segnaCeduto = (structureId, colonna, ruolo) => {
    const perdente = chiTiene(profiloAttivo(), structureId, ruolo, colonna);
    state.ruoloCeduto = perdente ? { struttura: structureId, colonna: perdente, ruolo } : null;
  };

  /* La domanda aperta è una riga della tabella che si apre sul posto: la
     colonna di cui si parla è lì sopra, in mezzo a tutte le altre, e la
     risposta si dà una volta sola invece che due. */
  const rigaDomanda = (problema) => {
    const carico = problema.payload || {};
    const conto = contaDomande(problema);
    const scelte = carico.choices || RUOLI;
    return `<tr class="domanda-corpo"><td colspan="4">
      <form class="domanda entra" data-eccezione="${esc(problema.exception_id)}">
        <p class="voce-meta">${esc(t("str.domandaDi", { i: conto.indice, t: conto.totale }))}</p>
        <h4>${esc(problema.title)}</h4>
        <p>${esc(problema.explanation)}</p>
        ${(carico.examples || []).length ? `<div class="domanda-valori">
          <p class="voce-meta">${esc(t("str.valoriTrovati"))}</p>
          <div>${carico.examples.map((v) => `<span class="codice">${esc(v)}</span>`).join("")}</div>
        </div>` : ""}
        <div class="domanda-azione">
          <label class="campo"><span>${esc(t("str.cheContiene"))}</span>
            <select name="role" required ${state.structureBusy ? "disabled" : ""}>
              <option value="">${esc(t("str.scegli"))}</option>
              ${scelte.map((r) => `<option value="${esc(r)}">${esc(root.etichettaRuolo(r))}</option>`).join("")}
            </select></label>
          <button type="submit" class="btn primario" ${state.structureBusy ? "disabled" : ""}>${esc(t("str.salvaContinua"))}</button>
        </div>
      </form>
    </td></tr>`;
  };

  const cellaRuolo = (struttura, colonna, config) => {
    const ruolo = config ? config.role : colonna.proposed_role;
    const usata = config ? config.included : true;
    const effettivo = usata ? ruolo : "excluded";
    const tipo = root.tipoDaRuolo[effettivo];
    return `
      <span class="ruolo-cella ${tipo ? `tipo-${tipo}` : ""}">
        <i aria-hidden="true" class="${tipo ? "" : "spento"}"></i>
        <label class="solo-lettori" for="ruolo-${esc(struttura.structure_id)}-${esc(colonna.name)}">${esc(t("str.ruoloDi", { c: colonna.name }))}</label>
        <select id="ruolo-${esc(struttura.structure_id)}-${esc(colonna.name)}"
          data-ruolo data-struttura="${esc(struttura.structure_id)}" data-colonna="${esc(colonna.name)}"
          ${state.structureBusy ? "disabled" : ""}>
          ${RUOLI.map((r) => `<option value="${r}" ${effettivo === r ? "selected" : ""}>${esc(root.etichettaRuolo(r))}</option>`).join("")}
        </select>
      </span>`;
  };

  /* Fuori dal grafo non restano solo delle righe: restano soprattutto delle
     colonne. Dirlo solo delle righe faceva leggere «niente resta fuori» a chi
     stava per confermare un file in cui tredici colonne su venti non
     diventano niente. */
  const restaFuori = (profilo) => {
    const avvisi = eccezioni()
      .filter((e) => e.profile_id === profilo.profile_id && e.severity === "warning");
    const isolate = Number(profilo.summary.isolated_record_count || 0);
    const lettura = letturaColonne(profilo);
    if (!avvisi.length && !isolate && !lettura.fuori) {
      return `<p class="resta-fuori-niente">${esc(t("fon.restaFuoriNiente"))}</p>`;
    }
    return `<section class="resta-fuori">
      <h4>${esc(t("fon.restaFuori"))}</h4>
      ${lettura.fuori ? `<div class="nota attesa"><span class="segno" aria-hidden="true">?</span>
        <strong>${esc(n(lettura.fuori, "fon.colonneFuori", { t: lettura.totale }))}</strong>
        <span>${esc([
          lettura.dato.length ? t("fon.colonneDato", { c: lettura.dato.join(" · ") }) : "",
          lettura.escluse.length ? t("fon.colonneEscluse", { c: lettura.escluse.join(" · ") }) : "",
        ].filter(Boolean).join(" "))}</span></div>` : ""}
      ${isolate ? `<div class="nota attesa"><span class="segno" aria-hidden="true">?</span>
        <strong>${esc(t("str.messeDaParte"))}</strong>
        <span>${esc(`${n(isolate, "str.righeIsolate")}. ${t("str.messeDaParteTesto")}`)}</span></div>` : ""}
      ${avvisi.map((avviso) => `<div class="nota attesa">
        <span class="segno" aria-hidden="true">?</span>
        <strong>${esc(avviso.title)}</strong><span>${esc(avviso.explanation)}</span></div>`).join("")}
      <p class="voce-meta">${esc(t("fon.restaFuoriTesto"))}</p>
    </section>`;
  };

  /**
   * I tipi di elemento dell'ontologia, e la colonna che li produce.
   *
   * Una riga per tipo, sempre tutte: quelle senza colonna dicono «libero», ed
   * è l'informazione che mancava — un tipo senza colonna è una parte del grafo
   * che non nascerà, e prima non se ne sapeva niente.
   *
   * La macchina non è in tabella perché non si assegna: la dichiara la scheda
   * della macchina, non una colonna di questo file.
   */
  const RUOLO_DA_TIPO = Object.fromEntries(
    Object.entries(root.tipoDaRuolo).map(([ruolo, tipo]) => [tipo, ruolo])
  );

  const tabellaElementi = (lettura) => `
    <table class="tabella-elementi">
      <thead><tr>
        <th>${esc(t("gr.tipoElemento"))}</th><th>${esc(t("str.colonnaNel"))}</th>
      </tr></thead>
      <tbody>
        ${root.ordineTipi.filter((tipo) => RUOLO_DA_TIPO[tipo]).map((tipo) => {
          const colonne = lettura.alimenta.get(RUOLO_DA_TIPO[tipo]);
          return `<tr class="${colonne ? "" : "libero"}">
            <td><span class="ruolo tipo-${tipo}"><i aria-hidden="true"></i>${esc(root.etichettaTipo(tipo))}</span></td>
            <td>${esc(colonne ? colonne.join(" + ") : t("str.ruoloLibero"))}</td>
          </tr>`;
        }).join("")}
      </tbody>
    </table>`;

  /* Chi ha appena perso un significato lo dice dalla propria riga, dopo il
     cambio e non prima: la domanda era che cosa fa questa colonna, e la
     risposta arriva dove la colonna sta. */
  const rigaCeduta = (struttura, colonna) => {
    const ceduto = state.ruoloCeduto;
    if (!ceduto || ceduto.struttura !== struttura.structure_id || ceduto.colonna !== colonna.name) return "";
    return `<tr class="domanda-corpo"><td colspan="4">
      <p class="nota-ceduta entra">
        <strong>${esc(t("str.ruoloCeduto", { c: colonna.name, r: root.etichettaRuolo(ceduto.ruolo) }))}</strong>
        <span>${esc(t("str.ruoloCedutoTesto"))}</span>
      </p>
    </td></tr>`;
  };

  const corpoLettura = (fonte, profilo) => {
    if (!profilo) {
      return `<div class="vuoto"><strong>${esc(t("stato.inLettura"))}</strong>
        <p>${esc(t("str.inLetturaTesto"))}</p></div>`;
    }
    const strutture = (profilo.structures || []).filter((s) => s.included);
    if (!strutture.length) {
      return `<div class="vuoto"><strong>${esc(t("str.nienteTabelle"))}</strong><p>${esc(t("str.nienteTabelleTesto"))}</p></div>`;
    }
    const domande = domandeSuColonne(profilo);
    return `
      <div class="gruppo-capo"><h3>${esc(t("str.colonneTitolo"))}</h3><p>${esc(t("str.colonneTesto"))}</p>
        <p>${esc(t("str.unRuoloUnaColonna"))}</p></div>
      ${strutture.map((struttura) => {
        const mappa = mappaturaDi(profilo, struttura.structure_id);
        return `<div style="margin-top:14px">
          ${strutture.length > 1 ? `<p class="voce-meta">${esc(struttura.name)} · ${esc(n(struttura.row_count, "str.righeLette"))}</p>` : ""}
          <div class="tabella-wrap"><table class="tabella tabella-lettura"><thead><tr>
            <th>${esc(t("str.colonnaNel"))}</th><th>${esc(t("str.significato"))}</th>
            <th>${esc(t("str.esempi"))}</th><th class="num">${esc(t("str.vuoti"))}</th>
          </tr></thead><tbody>
            ${(struttura.columns || []).map((colonna) => {
              const problema = domande.get(`${struttura.structure_id}::${colonna.name}`);
              const aperta = problema && problema.status === "open";
              const classe = aperta ? "riga-domanda" : problema ? "riga-in-coda" : "";
              const significato = problema
                ? `<span class="segna-domanda ${aperta ? "" : "in-coda"}">${esc(t(aperta ? "fon.serveRisposta" : "fon.inAttesa"))}</span>`
                : cellaRuolo(struttura, colonna, mappa[colonna.name]);
              return `<tr class="${classe}">
                <td>${esc(colonna.name)}</td>
                <td>${significato}</td>
                <td>${esc((colonna.examples || []).slice(0, 2).join(" · ") || "—")}</td>
                <td class="num">${Math.round(Number(colonna.null_rate || 0) * 100)}%</td>
              </tr>${aperta ? rigaDomanda(problema) : rigaCeduta(struttura, colonna)}`;
            }).join("")}
          </tbody></table></div></div>`;
      }).join("")}
      ${restaFuori(profilo)}`;
  };

  /* ------------------------------------- passo 2 · che cosa ne nasce ------ */
  const modelloCorrente = () => {
    const vista = vistaGrafo();
    return vista && root.sottografo ? root.sottografo.modello(vista) : null;
  };

  const nonConfermata = () => `<div class="lavoro-pad"><div class="vuoto">
    <strong>${esc(t("fon.nonConfermata"))}</strong><p>${esc(t("fon.nonConfermataTesto"))}</p>
    <button type="button" class="btn primario" data-passo="lettura">${esc(t("fon.tornaLettura"))}</button>
  </div></div>`;

  const esitoRimandato = () => `<div class="lavoro-pad"><section class="deferred-card">
    <span class="deferred-icon" aria-hidden="true">…</span>
    <div><strong>${esc(t("gr.pdfDifferito"))}</strong><p>${esc(t("gr.pdfDifferitoTesto"))}</p></div>
  </section></div>`;

  const corpoEsito = (fonte) => {
    /* Se il grafo non si è potuto leggere, dirlo: "conferma prima la lettura"
       manderebbe l'operatore a rifare una cosa già fatta. */
    if (!state.graph && state.graphError) {
      return `<div class="lavoro-pad"><div class="stato-pagina">
        <strong>${esc(t("gr.erroreTitolo"))}</strong>
        <p role="alert">${esc(state.graphError)}</p>
        <button type="button" class="btn primario" data-riprova>${esc(t("ui.riprova"))}</button></div></div>`;
    }
    const vista = vistaGrafo();
    if (!vista || vista.state === "waiting") {
      if (fonte.source_kind === "pdf") {
        return `<div class="lavoro-pad"><div class="vuoto">
          <strong>${esc(t("gr.pdfPreparazione"))}</strong><p>${esc(t("gr.pdfPreparazioneTesto"))}</p>
        </div></div>`;
      }
      return nonConfermata();
    }
    if (vista.state === "deferred") return esitoRimandato();
    if (!vista.subgraph) {
      /* Se un grafo c'era già ed è sparito, è stata una scelta dell'operatore
         a farlo sparire: va detto, non lasciato indovinare. */
      const voce = root.journeySource ? root.journeySource(fonte.source_id) : null;
      const rifatto = voce && voce.graph_revision_count > 0;
      const testo = rifatto
        ? (fonte.source_kind === "pdf" ? "fon.pdfRifareTesto" : "fon.rifareTesto")
        : (fonte.source_kind === "pdf" ? "fon.pdfDaCostruireTesto" : "fon.daCostruireTesto");
      return `<div class="lavoro-pad"><div class="vuoto">
        <strong>${esc(t(rifatto ? "fon.rifare" : "fon.daCostruire"))}</strong>
        <p>${esc(t(testo))}</p>
      </div></div>`;
    }
    return `${root.sottografo.ambito(vista)}${root.sottografo.mappa(root.sottografo.modello(vista))}`;
  };

  /**
   * Che cosa si mette dentro ogni passo, per tipo di fonte.
   *
   * La cornice — la striscia dei passi, l'area che scorre, la riga della
   * decisione in fondo — è la stessa per tutti: cambia solo il contenuto. Il
   * documento di testo ha già il suo posto qui, e oggi ci dice che cosa è
   * stato letto e perché il grafo arriva più avanti; quando il motore saprà
   * costruirlo, si riempiono queste due funzioni e non si tocca altro.
   */
  const letturaPdf = () => `<div class="vuoto">
    <strong>${esc(t("str.pdfTitolo"))}</strong><p>${esc(t("str.pdfTesto"))}</p></div>`;

  const CONTENUTO = {
    dati: { lettura: corpoLettura, esito: corpoEsito },
    pdf: { lettura: letturaPdf, esito: corpoEsito },
  };
  const contenutoDi = (fonte) => CONTENUTO[fonte.source_kind === "pdf" ? "pdf" : "dati"];

  /* ----------------------------------------------------- striscia passi -- */
  const statoPasso = (id, fonte, profilo) => {
    if (id === "lettura") {
      const aperte = profilo ? domandeAperte(profilo).length : 0;
      if (aperte) return `<span class="nav-attention">${aperte}</span>`;
      return profilo && profilo.confirmed ? `<span class="passo-fatto" aria-hidden="true">✓</span>` : "";
    }
    const vista = vistaGrafo();
    if (!vista || vista.state === "waiting") return `<span class="passo-chiuso" aria-hidden="true">·</span>`;
    if (!vista.subgraph) return "";
    return `<span class="passo-conto">${vista.subgraph.nodes.length}</span>`;
  };

  const striscia = (fonte, profilo) => {
    const passo = passoCorrente();
    const mostraFiltri = passo === "esito" && vistaGrafo() && vistaGrafo().subgraph;
    const modello = mostraFiltri ? modelloCorrente() : null;
    const tipi = modello
      ? root.ordineTipi.filter((tipo) => modello.grafo.nodes.some((nodo) => nodo.node_type === tipo))
      : [];
    return `<div class="barra">
      <div class="segmento passi" role="tablist">
        ${PASSI.map((id) => `<button type="button" class="tab" role="tab" data-passo="${id}"
          aria-selected="${passo === id}">${esc(t(`fon.passo.${id}`))}${statoPasso(id, fonte, profilo)}</button>`).join("")}
      </div>
      ${mostraFiltri ? `<span class="barra-spazio"></span>
      <div class="barra-gruppo">
        <label class="solo-lettori" for="kg-cerca">${esc(t("gr.cerca"))}</label>
        <input id="kg-cerca" type="search" data-cerca placeholder="${esc(t("gr.cerca"))}" value="${esc(state.filters.query)}">
        <label class="solo-lettori" for="kg-tipo">${esc(t("gr.tipoElemento"))}</label>
        <select id="kg-tipo" data-filtro="nodeType">
          <option value="all">${esc(t("gr.tuttiTipi"))}</option>
          ${tipi.map((tipo) => `<option value="${tipo}" ${state.filters.nodeType === tipo ? "selected" : ""}>${esc(root.etichettaTipoPl(tipo))}</option>`).join("")}
        </select>
        ${root.spuntaLacune(modello)}
      </div>` : ""}
    </div>`;
  };

  /* ---------------------------------------------------------------- fase */
  root.phases.structure = {
    mostraIspettore: true,
    carica,

    titolo() {
      const fonte = root.fonteAttiva();
      if (!fonte) return { titolo: t("str.titoloVuoto"), chips: "" };
      if (passoCorrente() === "esito") {
        const vista = vistaGrafo();
        const grafo = vista && vista.subgraph;
        const tono = !vista ? "" : vista.state === "approved" ? "ok"
          : vista.state === "rejected" ? "errore" : "attesa";
        return {
          titolo: fonte.file_name,
          chips: [
            vista ? `<span class="chip ${tono}">${esc(root.etichettaStato(vista.state))}</span>` : "",
            grafo ? `<span class="chip"><b>${grafo.nodes.length}</b> ${esc(t("gr.vista.elementi").toLocaleLowerCase())}</span>` : "",
            grafo ? `<span class="chip"><b>${grafo.relations.length}</b> ${esc(t("gr.vista.collegamenti").toLocaleLowerCase())}</span>` : "",
            root.sottografo ? root.sottografo.chipAmbito(grafo) : "",
          ].filter(Boolean).join(""),
        };
      }
      const profilo = profiloAttivo();
      const chips = profilo
        ? `<span class="chip ${profilo.confirmed ? "ok" : "attesa"}">${esc(profilo.confirmed ? t("stato.confermata") : t("stato.daConfermare"))}</span>
           <span class="chip"><b>${Number(profilo.summary.record_count || 0)}</b> ${esc(t("str.vista.righe").toLocaleLowerCase())}</span>`
        : "";
      return { titolo: fonte.file_name, chips };
    },

    renderLavoro() {
      if (!state.workspace || state.structureLoading) {
        return `<div class="stato-pagina"><strong>${esc(t("str.leggo"))}</strong><p>${esc(t("str.leggoTesto"))}</p></div>`;
      }
      /* Una rilettura fallita rende bugiardo tutto quello che c'è a schermo: i
         dati mostrati sono quelli di prima, e rispondere alla domanda non ha
         effetto. Va detto, non nascosto dietro l'ultima istantanea riuscita —
         era questo a sembrare un ciclo infinito. */
      if (state.structureError) {
        return `<div class="stato-pagina"><strong>${esc(t("str.erroreTitolo"))}</strong>
          <p role="alert">${esc(state.structureError)}</p>
          <p>${esc(t("str.erroreTesto"))}</p>
          <button type="button" class="btn primario" data-riprova>${esc(t("ui.riprova"))}</button></div>`;
      }
      if (!state.structure) {
        return `<div class="stato-pagina"><strong>${esc(t("str.nienteDati"))}</strong><p>${esc(t("str.nienteDatiTesto"))}</p></div>`;
      }

      const fonte = root.fonteAttiva();
      if (!fonte) {
        return `<div class="stato-pagina"><strong>${esc(t("str.titoloVuoto"))}</strong>
          <p>${esc(t("str.selezionaFonte"))}</p></div>`;
      }
      const profilo = profiloAttivo();
      const passo = passoCorrente();

      const contenuto = contenutoDi(fonte);

      if (passo === "esito") {
        const conMappa = vistaGrafo() && vistaGrafo().subgraph;
        return `
          ${conMappa ? `<div class="intestazione-lavoro"><p>${esc(t("fon.mappaSotto"))}</p></div>` : ""}
          ${striscia(fonte, profilo)}
          <div class="lavoro-scorri">${contenuto.esito(fonte, profilo)}</div>`;
      }

      /* Una domanda che riguarda una colonna è quella colonna, accesa nella
         tabella. Restano carte in cima solo quelle che una colonna non ce
         l'hanno: un foglio da includere, un avviso, un file da sostituire.
         E solo se riguardano questa fonte: la pagina di un file non è il posto
         dove si risponde per un altro. */
      const problema = eccezioneAperta();
      const mia = problema && profilo && problema.profile_id === profilo.profile_id;
      const join = joinProposto();
      const mioJoin = join && profilo
        && [join.primary_profile_id, join.lookup_profile_id].includes(profilo.profile_id);
      const carta = mia && !(problema.exception_kind === "mapping_ambiguous" && (problema.payload || {}).column)
        ? cartaEccezione(problema)
        : mia ? "" : (mioJoin ? cartaJoin(join) : "");

      return `
        <div class="intestazione-lavoro"><p>${esc(t(fonte.source_kind === "pdf" ? "str.sottoPdf" : "str.sotto"))}</p></div>
        ${striscia(fonte, profilo)}
        <div class="lavoro-scorri"><div class="lavoro-pad">
          ${carta}${carta ? '<div style="height:18px"></div>' : ""}
          ${contenuto.lettura(fonte, profilo)}
        </div></div>`;
    },

    bindLavoro(contenitore) {
      root.delegate(contenitore, "click", "[data-riprova]", () => esegui(async () => {
        await carica();
        if (!state.structure) throw new Error(state.structureError || t("str.erroreTitolo"));
        return state.structure;
      }));
      root.delegate(contenitore, "click", "[data-passo]", (elemento) => {
        if (elemento.dataset.passo === passoCorrente()) return;
        state.view = elemento.dataset.passo;
        root.clearSelection();
        if (root.rememberWorkspaceContext) root.rememberWorkspaceContext();
        root.render();
      });
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
      root.delegate(contenitore, "submit", "[data-eccezione]", (modulo, evento) => {
        evento.preventDefault();
        const role = new FormData(modulo).get("role");
        /* Chi ha appena risposto sta rispondendo: il fuoco va sulla domanda
           dopo, non torna in cima alla pagina. */
        state.seguiDomanda = true;
        const problema = eccezioni().find((e) => e.exception_id === modulo.dataset.eccezione);
        const carico = (problema && problema.payload) || {};
        segnaCeduto(carico.structure_id, carico.column, role);
        esegui(() => root.api(`/api/g2/exceptions/${encodeURIComponent(modulo.dataset.eccezione)}/resolve`,
          { method: "POST", body: { role } }));
      });
      root.delegate(contenitore, "click", "[data-includi]", (elemento) => {
        const pannello = elemento.closest("[data-eccezione]");
        esegui(() => root.api(`/api/g2/exceptions/${encodeURIComponent(pannello.dataset.eccezione)}/resolve`,
          { method: "POST", body: { included: elemento.dataset.includi === "true", acknowledge: true } }));
      });
      root.delegate(contenitore, "click", "[data-preso]", (elemento) => {
        const pannello = elemento.closest("[data-eccezione]");
        esegui(() => root.api(`/api/g2/exceptions/${encodeURIComponent(pannello.dataset.eccezione)}/resolve`,
          { method: "POST", body: { acknowledge: true } }));
      });
      root.delegate(contenitore, "change", "[data-ruolo]", (elemento) => {
        const profilo = profiloAttivo();
        if (!profilo) return;
        segnaCeduto(elemento.dataset.struttura, elemento.dataset.colonna, elemento.value);
        esegui(() => root.api(`/api/g2/profiles/${encodeURIComponent(profilo.profile_id)}/columns`, {
          method: "POST",
          body: {
            structure_id: elemento.dataset.struttura,
            column: elemento.dataset.colonna,
            role: elemento.value,
          },
        }));
      });
      root.delegate(contenitore, "click", "[data-join-azione]", (elemento) => {
        const pannello = elemento.closest("[data-join]");
        esegui(() => root.api(`/api/g2/joins/${encodeURIComponent(pannello.dataset.join)}/decision`,
          { method: "POST", body: { action: elemento.dataset.joinAzione } }));
      });

      /* — il secondo passo: la mappa e i suoi filtri — */
      if (root.sottografo) root.sottografo.bindMappa(contenitore);
    },

    dopoLavoro(contenitore) {
      const scorri = contenitore.querySelector(".lavoro-scorri");
      if (passoCorrente() === "lettura") {
        if (root.sottografo) root.sottografo.smonta();
        /* La domanda è una riga in mezzo alle altre, e dopo ogni risposta la
           tabella si ridisegna: senza questo, la domanda successiva resterebbe
           sotto lo schermo e l'operatore dovrebbe andarsela a cercare. Si
           scorre il riquadro, non la pagina — la testata deve restare dov'è. */
        const riga = contenitore.querySelector("tr.riga-domanda");
        if (scorri && riga) {
          /* Al fotogramma dopo: appena dipinta, la pagina non ha ancora
             l'altezza definitiva e il riquadro non è ancora scorrevole, così
             lo spostamento andrebbe perso. */
          window.requestAnimationFrame(() => {
            if (!scorri.isConnected || !riga.isConnected) return;
            const alto = riga.getBoundingClientRect().top
              - scorri.getBoundingClientRect().top + scorri.scrollTop;
            scorri.scrollTop = Math.max(0, alto - 80);
            if (state.seguiDomanda) {
              state.seguiDomanda = false;
              contenitore.querySelector(".domanda select")?.focus({ preventScroll: true });
            }
          });
        }
        return;
      }
      if (!root.sottografo) return;
      const vista = vistaGrafo();
      if (!scorri || !vista || !vista.subgraph) {
        root.sottografo.smonta();
        return;
      }
      root.sottografo.monta(scorri, vista, root.sottografo.modello(vista));
    },

    /* Selezionare non ricostruisce la mappa: cambia solo le classi. */
    suSelezione() {
      if (passoCorrente() === "esito" && root.sottografo && root.sottografo.evidenzia(state.selection)) return;
      root.render({ regioni: ["lavoro"] });
    },

    renderIspettore() {
      const fonte = root.fonteAttiva();
      const profilo = profiloAttivo();
      if (!fonte) {
        return `<div class="ispettore-vuoto"><strong>${esc(t("doc.nessunDettaglio"))}</strong>
          <p>${esc(t("doc.nessunDettaglioTesto"))}</p></div>`;
      }
      if (passoCorrente() === "esito") {
        const vista = vistaGrafo();
        return root.renderIspettoreGrafo(vista, modelloCorrente() || {
          nodiPerId: new Map(), evidenzePerId: new Map(), legamiPerNodo: new Map(),
          lacunePerNodo: new Map(), lacunePerEvidenza: new Map(), difettiPerNodo: new Map(),
        });
      }
      if (!profilo) {
        return `<div class="ispettore-dentro">
          <div class="ispettore-identita"><span class="ispettore-tipo">${esc(t("isp.fonte"))}</span>
            <h3>${esc(fonte.file_name)}</h3></div>
          <p class="blocco-vuoto">${esc(fonte.source_kind === "pdf" ? t("str.pdfTesto") : t("str.inLetturaTesto"))}</p>
        </div>`;
      }
      const conti = profilo.summary || {};
      const lettura = letturaColonne(profilo);
      const contorno = lettura.contorno;
      /* Righe lette, righe preparate e righe in una lingua sono quasi sempre
         lo stesso numero. Scritti uno sotto l'altro sembravano tre fatti
         diversi e non se ne capiva nessuno: il numero è uno — quante righe ha
         il file — e accanto va solo quello che da lui non si deduce, cioè in
         che lingua sono e quante sono rimaste da parte. */
      const righe = Number(conti.record_count || 0);
      const isolate = Number(conti.isolated_record_count || 0);
      const lingue = Object.entries(conti.language_counts || {}).filter(([, v]) => Number(v) > 0);
      const inLingua = lingue.length === 1
        ? t("str.tutteInLingua", { l: t(`str.lingua.${lingue[0][0]}`) })
        : lingue.map(([chiave, quante]) => `${quante} ${t(`str.lingua.${chiave}`)}`).join(" · ");
      const coda = [inLingua, isolate ? n(isolate, "str.righeIsolate") : ""].filter(Boolean).join(" · ");
      return `
        <div class="ispettore-dentro">
          <button type="button" class="btn quieto piccolo chiudi-ispettore" data-chiudi-ispettore>${esc(t("ui.chiudiDettaglio"))}</button>
          <div class="ispettore-identita"><span class="ispettore-tipo">${esc(t("isp.fonte"))}</span>
            <h3>${esc(profilo.source_name)}</h3></div>
          <section class="blocco"><h4>${esc(t("str.cosaLetto"))}</h4>
            <p class="occorrenze"><strong>${righe}</strong>
              <span>${esc(t(righe === 1 ? "str.etichettaRighe1" : "str.etichettaRighe"))}</span></p>
            ${coda ? `<p>${esc(coda)}</p>` : ""}
            ${(conti.language_counts || {}).unknown ? `<p>${esc(t("str.testoIntegro"))}</p>` : ""}
          </section>
          <section class="blocco"><h4>${esc(t("str.alimenta"))}</h4>
            ${tabellaElementi(lettura)}
            <p>${esc(t("str.macchinaSempre"))}</p>
            <p>${esc(t("str.alimentaNota"))}</p></section>
          ${contorno.size ? `<section class="blocco"><h4>${esc(t("str.contorno"))}</h4>
            ${[...contorno.entries()].map(([ruolo, colonne]) => `
              <div class="riga-legame">
                <i aria-hidden="true" style="background:var(--muted-2)"></i>
                <span class="nome">${esc(root.etichettaRuolo(ruolo))}</span>
                <span class="coda">${esc(colonne.join(" + "))}</span></div>`).join("")}
            <p>${esc(t("str.contornoNota"))}</p></section>` : ""}
        </div>`;
    },

    bindIspettore(contenitore) {
      if (passoCorrente() === "esito") root.bindIspettoreGrafo(contenitore);
    },

    renderDecisione() {
      if (!state.structure) return "";
      const fonte = root.fonteAttiva();
      if (!fonte) return "";
      if (passoCorrente() === "esito") {
        return root.sottografo ? root.sottografo.decisione(vistaGrafo(), fonte) : "";
      }

      const errore = state.structureError ? `<p class="campo-errore" role="alert">${esc(state.structureError)}</p>` : "";
      const profilo = profiloAttivo();
      const problema = eccezioneAperta();
      /* Dentro una fonte si parla di quella fonte: una domanda aperta su un
         altro file non è la decisione di questa pagina, e dirla qui manderebbe
         l'operatore a cercare una colonna che qui non c'è. */
      if (problema && profilo && problema.profile_id === profilo.profile_id) {
        const conto = contaDomande(problema);
        return `<div class="decisione-riga"><div class="decisione-testo" aria-live="polite">
          <strong>${esc(`${t("str.serveScelta")} · ${t("str.domandaDi", { i: conto.indice, t: conto.totale })}`)}</strong>
          <span>${esc(t("str.serveSceltaTesto", { f: problema.source_name }))}</span></div></div>${errore}`;
      }
      if (!profilo) {
        const pdf = fonte.source_kind === "pdf";
        return `<div class="decisione-riga"><div class="decisione-testo">
          <strong>${esc(pdf ? t("str.pdfPronto") : t("stato.inLettura"))}</strong>
          <span>${esc(pdf ? t("fon.pdfProntoTesto") : t("str.inLetturaTesto"))}</span></div>
          ${pdf ? `<div class="decisione-azioni">
            <button type="button" class="btn primario" data-passo="esito">${esc(t("fon.passo.esito"))}</button>
          </div>` : ""}</div>${errore}`;
      }
      const mancanti = profili().filter((p) => !p.confirmed).length;
      if (profilo && !profilo.confirmed && profilo.state === "prepared") {
        return `<div class="decisione-riga">
          <div class="decisione-testo"><strong>${esc(t("str.domandaConferma", { f: profilo.source_name }))}</strong>
            <span>${esc(t("str.confermaTesto", { r: n(mancanti, "str.restano") }))}</span></div>
          <div class="decisione-azioni">
            <button type="button" class="btn primario" data-conferma="${esc(profilo.profile_id)}"
              ${state.structureBusy ? "disabled" : ""}>${esc(t("str.confermaFile"))}</button>
          </div></div>${errore}`;
      }
      if (profilo && profilo.confirmed) {
        return `<div class="decisione-riga">
          <div class="decisione-testo"><strong>${esc(t("str.confermata"))}</strong>
            <span>${esc(t("str.confermataTesto"))}</span></div>
          <div class="decisione-azioni">
            <button type="button" class="btn primario" data-passo="esito">${esc(t("fon.passo.esito"))}</button>
          </div></div>${errore}`;
      }
      return `<div class="decisione-riga"><div class="decisione-testo">
        <strong>${esc(mancanti ? t("str.daConfermare", { n: mancanti }) : t("str.tuttiConfermati"))}</strong>
        <span>${esc(t("str.selezionaFonte"))}</span></div></div>${errore}`;
    },

    bindDecisione(contenitore) {
      root.delegate(contenitore, "click", "[data-conferma]", (elemento) => {
        esegui(() => root.api(`/api/g2/profiles/${encodeURIComponent(elemento.dataset.conferma)}/confirm`, { method: "POST" }));
      });
      root.delegate(contenitore, "click", "[data-passo]", (elemento) => {
        state.view = elemento.dataset.passo;
        root.clearSelection();
        if (root.rememberWorkspaceContext) root.rememberWorkspaceContext();
        root.render();
      });
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
      if (root.sottografo) root.sottografo.bindDecisione(contenitore, eseguiGrafo);
    },
  };
})();
