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
  const eccezioneAperta = () => ((state.structure && state.structure.exceptions) || [])
    .find((e) => e.status === "open") || null;
  const joinProposto = () => ((state.structure && state.structure.joins) || [])
    .find((j) => j.status === "proposed") || null;

  const carica = async () => {
    if (!state.workspace) return;
    state.structureLoading = true;
    state.structureError = "";
    try {
      state.structure = await root.api(
        `/api/workspaces/${encodeURIComponent(wsId())}/g2/preparation`, { method: "POST" }
      );
    } catch (errore) {
      state.structureError = errore.message;
    } finally {
      state.structureLoading = false;
    }
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
      if (root.loadJourney) await root.loadJourney();
    } catch (errore) { state.structureError = errore.message; }
    finally { state.structureBusy = false; root.render(); }
  };

  /* Quante domande restano su questo file. Il conto è sul profilo a cui la
     domanda appartiene, non sulla fonte a schermo: sono la stessa cosa quando
     l'operatore risponde, ma la formula resta vera anche se non lo fossero. */
  const contaDomande = (problema) => {
    const tutte = ((state.structure && state.structure.exceptions) || [])
      .filter((e) => e.profile_id === problema.profile_id);
    const risposte = tutte.filter((e) => e.status !== "open" && e.status !== "queued").length;
    return { indice: risposte + 1, totale: tutte.length };
  };

  /* ------- l'unica decisione che richiede un umano, in cima al pannello --- */
  const cartaEccezione = (problema) => {
    const carico = problema.payload || {};
    const conto = contaDomande(problema);
    const testa = `
      <p class="voce-meta">${esc(t("str.domandaDi", { i: conto.indice, t: conto.totale }))}</p>
      <h3 style="margin:0;font-size:17px;font-weight:640;letter-spacing:-.02em">${esc(problema.title)}</h3>
      <p>${esc(problema.explanation)}</p>
      <p class="voce-meta">${esc(t("str.riguarda", { f: problema.source_name }))}</p>`;

    if (problema.exception_kind === "mapping_ambiguous") {
      const scelte = carico.choices || [];
      return `<form class="card entra" data-eccezione="${esc(problema.exception_id)}" style="display:grid;gap:12px">
        ${testa}
        ${(carico.examples || []).length ? `<div>
          <p class="voce-meta">${esc(t("str.valoriTrovati"))}</p>
          <div style="display:flex;gap:7px;flex-wrap:wrap;margin-top:6px">
            ${carico.examples.map((v) => `<span class="codice">${esc(v)}</span>`).join("")}</div></div>` : ""}
        <label class="campo" style="max-width:24rem"><span>${esc(t("str.cheContiene"))}</span>
          <select name="role" required>
            <option value="">${esc(t("str.scegli"))}</option>
            ${scelte.map((r) => `<option value="${esc(r)}">${esc(root.etichettaRuolo(r))}</option>`).join("")}
          </select></label>
        <div><button type="submit" class="btn primario" ${state.structureBusy ? "disabled" : ""}>${esc(t("str.salvaContinua"))}</button></div>
      </form>`;
    }
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

  /* ------------------------------------------------------------- viste -- */
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

  const vistaColonne = (profilo) => {
    const strutture = (profilo.structures || []).filter((s) => s.included);
    if (!strutture.length) {
      return `<div class="vuoto"><strong>${esc(t("str.nienteTabelle"))}</strong><p>${esc(t("str.nienteTabelleTesto"))}</p></div>`;
    }
    return `
      <div class="gruppo-capo"><h3>${esc(t("str.colonneTitolo"))}</h3><p>${esc(t("str.colonneTesto"))}</p>
        <p>${esc(t("str.unRuoloUnaColonna"))}</p></div>
      ${strutture.map((struttura) => {
        const mappa = mappaturaDi(profilo, struttura.structure_id);
        return `<div style="margin-top:14px">
          ${strutture.length > 1 ? `<p class="voce-meta">${esc(struttura.name)} · ${esc(n(struttura.row_count, "str.righeLette"))}</p>` : ""}
          <div class="tabella-wrap"><table class="tabella"><thead><tr>
            <th>${esc(t("str.colonnaNel"))}</th><th>${esc(t("str.significato"))}</th>
            <th>${esc(t("str.esempi"))}</th><th class="num">${esc(t("str.vuoti"))}</th>
          </tr></thead><tbody>
            ${(struttura.columns || []).map((colonna) => {
              const config = mappa[colonna.name];
              const ruolo = config ? config.role : colonna.proposed_role;
              const usata = config ? config.included : true;
              const effettivo = usata ? ruolo : "excluded";
              const tipo = root.tipoDaRuolo[effettivo];
              return `<tr>
                <td>${esc(colonna.name)}</td>
                <td>
                  <span class="ruolo-cella ${tipo ? `tipo-${tipo}` : ""}">
                    <i aria-hidden="true" class="${tipo ? "" : "spento"}"></i>
                    <label class="solo-lettori" for="ruolo-${esc(struttura.structure_id)}-${esc(colonna.name)}">${esc(t("str.ruoloDi", { c: colonna.name }))}</label>
                    <select id="ruolo-${esc(struttura.structure_id)}-${esc(colonna.name)}"
                      data-ruolo data-struttura="${esc(struttura.structure_id)}" data-colonna="${esc(colonna.name)}"
                      ${state.structureBusy ? "disabled" : ""}>
                      ${RUOLI.map((r) => `<option value="${r}" ${effettivo === r ? "selected" : ""}>${esc(root.etichettaRuolo(r))}</option>`).join("")}
                    </select>
                  </span>
                </td>
                <td>${esc((colonna.examples || []).slice(0, 2).join(" · ") || "—")}</td>
                <td class="num">${Math.round(Number(colonna.null_rate || 0) * 100)}%</td>
              </tr>`;
            }).join("")}
          </tbody></table></div></div>`;
      }).join("")}`;
  };

  const vistaRighe = (profilo) => {
    const struttura = (profilo.structures || []).find((s) => s.included && (s.preview || []).length);
    if (!struttura) {
      return `<div class="vuoto"><strong>${esc(t("str.nienteAnteprima"))}</strong><p>${esc(t("str.nienteAnteprimaTesto"))}</p></div>`;
    }
    const mappa = mappaturaDi(profilo, struttura.structure_id);
    const colonne = (struttura.columns || []).map((c) => c.name);
    const righe = struttura.preview.slice(0, 10);
    return `
      <div class="gruppo-capo"><h3>${esc(t("str.righeTitolo"))}</h3>
        <p>${esc(t("str.righeTesto", { n: righe.length, t: struttura.row_count }))}</p></div>
      <div class="tabella-wrap" style="margin-top:12px"><table class="tabella"><thead><tr>
        ${colonne.map((nome) => {
          const config = mappa[nome];
          const ruolo = config ? config.role : "attribute";
          const usata = config ? config.included : true;
          return `<th>${esc(nome)}<br><span style="font-weight:400;text-transform:none;letter-spacing:0">${esc(usata ? root.etichettaRuolo(ruolo) : t("ruolo.nonUsata"))}</span></th>`;
        }).join("")}
      </tr></thead><tbody>
        ${righe.map((riga) => `<tr>${colonne.map((nome) => {
          const valore = riga[nome];
          const testo = valore == null || String(valore).trim() === "" ? "—" : String(valore);
          return `<td title="${esc(testo)}">${esc(testo.length > 52 ? `${testo.slice(0, 51)}…` : testo)}</td>`;
        }).join("")}</tr>`).join("")}
      </tbody></table></div>`;
  };

  const vistaAvvisi = (profilo) => {
    const avvisi = ((state.structure.exceptions) || [])
      .filter((e) => e.profile_id === profilo.profile_id && e.severity === "warning");
    const isolate = Number(profilo.summary.isolated_record_count || 0);
    if (!avvisi.length && !isolate) {
      return `<div class="vuoto"><strong>${esc(t("str.nienteAvvisi"))}</strong><p>${esc(t("str.nienteAvvisiTesto"))}</p></div>`;
    }
    return `
      <div class="gruppo-capo"><h3>${esc(t("str.messeDaParte"))}</h3><p>${esc(t("str.messeDaParteTesto"))}</p></div>
      <div class="lista" style="margin-top:12px">
        ${avvisi.map((avviso) => `<div class="nota attesa">
          <span class="segno" aria-hidden="true">?</span>
          <strong>${esc(avviso.title)}</strong><span>${esc(avviso.explanation)}</span></div>`).join("")}
      </div>`;
  };

  const VISTE = [
    { id: "colonne", chiave: "str.vista.colonne" },
    { id: "righe", chiave: "str.vista.righe" },
    { id: "avvisi", chiave: "str.vista.avvisi" },
  ];
  const vistaCorrente = () => (VISTE.some((v) => v.id === state.view) ? state.view : "colonne");

  /* ---------------------------------------------------------------- fase */
  root.phases.structure = {
    mostraFonti: true,
    mostraIspettore: true,
    carica,

    titolo() {
      const fonte = root.fonteAttiva();
      const profilo = profiloAttivo();
      const chips = profilo
        ? `<span class="chip ${profilo.confirmed ? "ok" : "attesa"}"><span class="punto"></span>${esc(profilo.confirmed ? t("stato.confermata") : t("stato.daConfermare"))}</span>
           <span class="chip"><b>${Number(profilo.summary.record_count || 0)}</b> ${esc(t("str.vista.righe").toLocaleLowerCase())}</span>`
        : "";
      return { titolo: fonte ? fonte.file_name : t("str.titoloVuoto"), chips };
    },

    metaFonte(sorgente) {
      if (sorgente.source_kind === "pdf") return "✓";
      const profilo = profiloDi(sorgente.source_id);
      if (!profilo) return "";
      const serve = ((state.structure.exceptions) || [])
        .some((e) => e.profile_id === profilo.profile_id && e.status === "open");
      if (serve) return `<span style="color:var(--amber)">!</span>`;
      return profilo.confirmed ? "✓" : String(Number(profilo.summary.record_count || 0));
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

      const problema = eccezioneAperta();
      const join = problema ? null : joinProposto();
      const fonte = root.fonteAttiva();
      const profilo = profiloAttivo();
      const vista = vistaCorrente();

      const corpo = profilo
        ? (vista === "righe" ? vistaRighe(profilo) : vista === "avvisi" ? vistaAvvisi(profilo) : vistaColonne(profilo))
        : `<div class="vuoto">
            <strong>${esc(fonte && fonte.source_kind === "pdf" ? t("str.pdfTitolo") : t("stato.inLettura"))}</strong>
            <p>${esc(fonte && fonte.source_kind === "pdf" ? t("str.pdfTesto") : t("str.inLetturaTesto"))}</p></div>`;

      return `
        <div class="intestazione-lavoro"><p>${esc(t("str.sotto"))}</p></div>
        ${profilo ? `<div class="barra"><div class="segmento" role="tablist">
          ${VISTE.map((v) => `<button type="button" class="tab" role="tab" data-vista="${v.id}"
            aria-selected="${vista === v.id}">${esc(t(v.chiave))}</button>`).join("")}
        </div></div>` : ""}
        <div class="lavoro-scorri"><div class="lavoro-pad">
          ${problema ? cartaEccezione(problema) : join ? cartaJoin(join) : ""}
          ${problema || join ? '<div style="height:18px"></div>' : ""}
          ${corpo}
        </div></div>`;
    },

    bindLavoro(contenitore) {
      root.delegate(contenitore, "click", "[data-riprova]", () => esegui(async () => {
        await carica();
        if (!state.structure) throw new Error(state.structureError || t("str.erroreTitolo"));
        return state.structure;
      }));
      root.delegate(contenitore, "click", "[data-vista]", (elemento) => {
        state.view = elemento.dataset.vista;
        root.render({ regioni: ["lavoro"] });
      });
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
      root.delegate(contenitore, "submit", "[data-eccezione]", (modulo, evento) => {
        evento.preventDefault();
        const role = new FormData(modulo).get("role");
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
    },

    renderIspettore() {
      const fonte = root.fonteAttiva();
      const profilo = profiloAttivo();
      if (!fonte) {
        return `<div class="ispettore-vuoto"><strong>${esc(t("doc.nessunDettaglio"))}</strong>
          <p>${esc(t("doc.nessunDettaglioTesto"))}</p></div>`;
      }
      if (!profilo) {
        return `<div class="ispettore-dentro">
          <div class="ispettore-identita"><span class="ispettore-tipo">${esc(t("isp.fonte"))}</span>
            <h3>${esc(fonte.file_name)}</h3></div>
          <p class="blocco-vuoto">${esc(fonte.source_kind === "pdf" ? t("str.pdfTesto") : t("str.inLetturaTesto"))}</p>
        </div>`;
      }
      const conti = profilo.summary || {};
      const lingue = Object.entries(conti.language_counts || {}).filter(([, v]) => Number(v) > 0);
      const ruoli = new Map();
      const contorno = new Map();
      (profilo.structures || []).filter((s) => s.included).forEach((struttura) => {
        Object.entries(mappaturaDi(profilo, struttura.structure_id)).forEach(([colonna, config]) => {
          if (!config.included) return;
          const dove = root.tipoDaRuolo[config.role] ? ruoli
            : CONTORNO.includes(config.role) ? contorno : null;
          if (!dove) return;
          if (!dove.has(config.role)) dove.set(config.role, []);
          dove.get(config.role).push(colonna);
        });
      });
      return `
        <div class="ispettore-dentro">
          <button type="button" class="btn quieto piccolo chiudi-ispettore" data-chiudi-ispettore>${esc(t("ui.chiudiDettaglio"))}</button>
          <div class="ispettore-identita"><span class="ispettore-tipo">${esc(t("isp.fonte"))}</span>
            <h3>${esc(profilo.source_name)}</h3></div>
          <section class="blocco"><h4>${esc(t("str.cosaLetto"))}</h4>
            <p class="occorrenze"><strong>${Number(conti.record_count || 0)}</strong>
              <span>${esc(t(Number(conti.record_count) === 1 ? "str.righeLette1" : "str.righeLette", { n: "" }).replace(/^\s*\d*\s*/, ""))}</span></p>
            <p>${esc(n(Number(conti.evidence_count || 0), "str.righePreparate"))}${Number(conti.isolated_record_count || 0)
              ? ` · ${esc(n(Number(conti.isolated_record_count), "str.righeIsolate"))}` : ""}</p></section>
          ${lingue.length ? `<section class="blocco"><h4>${esc(t("str.lingue"))}</h4>
            <p>${lingue.map(([chiave, quante]) => esc(`${quante} ${t(`str.lingua.${chiave}`)}`)).join(" · ")}</p>
            ${(conti.language_counts || {}).unknown ? `<p>${esc(t("str.testoIntegro"))}</p>` : ""}</section>` : ""}
          <section class="blocco"><h4>${esc(t("str.alimenta"))}</h4>
            ${ruoli.size ? [...ruoli.entries()].map(([ruolo, colonne]) => `
              <div class="riga-legame tipo-${root.tipoDaRuolo[ruolo]}">
                <i aria-hidden="true"></i><span class="nome">${esc(root.etichettaRuolo(ruolo))}</span>
                <span class="coda">${esc(colonne.join(" + "))}</span></div>`).join("")
              : `<p class="blocco-vuoto">${esc(t("str.alimentaVuoto"))}</p>`}
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

    renderDecisione() {
      if (!state.structure) return "";
      const problema = eccezioneAperta();
      const errore = state.structureError ? `<p class="campo-errore" role="alert">${esc(state.structureError)}</p>` : "";
      if (problema) {
        const conto = contaDomande(problema);
        return `<div class="decisione-riga"><div class="decisione-testo" aria-live="polite">
          <strong>${esc(`${t("str.serveScelta")} · ${t("str.domandaDi", { i: conto.indice, t: conto.totale })}`)}</strong>
          <span>${esc(t("str.serveSceltaTesto", { f: problema.source_name }))}</span></div></div>${errore}`;
      }
      const profilo = profiloAttivo();
      const mancanti = profili().filter((p) => !p.confirmed).length;
      if (state.structure.completed) {
        return `<div class="decisione-riga">
          <div class="decisione-testo"><strong>${esc(t("str.confermata"))}</strong><span>${esc(t("str.confermataTesto"))}</span></div>
          <div class="decisione-azioni"><button type="button" class="btn primario" data-vai="graph">${esc(t("str.vaiGrafo"))}</button></div>
        </div>`;
      }
      if (profilo && !profilo.confirmed && profilo.state === "prepared") {
        return `<div class="decisione-riga">
          <div class="decisione-testo"><strong>${esc(t("str.domandaConferma", { f: profilo.source_name }))}</strong>
            <span>${esc(t("str.confermaTesto", { r: n(mancanti, "str.restano") }))}</span></div>
          <div class="decisione-azioni">
            <button type="button" class="btn primario" data-conferma="${esc(profilo.profile_id)}"
              ${state.structureBusy ? "disabled" : ""}>${esc(t("str.confermaFile"))}</button>
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
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
    },
  };
})();
