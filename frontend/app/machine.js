(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const esc = root.escapeHtml;
  const t = root.t;

  const identificata = () => {
    const workspace = state.workspace.workspace;
    const asset = workspace.asset;
    const trova = (genere) => (workspace.identifiers || []).find((i) => i.kind === genere);
    const seriale = trova("serial");
    const targa = trova("equipment_tag");
    const voce = (etichetta, valore) => (valore
      ? `<div><dt>${esc(etichetta)}</dt><dd>${esc(valore)}</dd></div>` : "");
    return `
      <div class="intestazione-lavoro"><p>${esc(t("mac.suQuesta"))}</p></div>
      <div class="lavoro-scorri"><div class="lavoro-pad">
        <dl class="riepilogo entra">
          ${voce(t("mac.marcaL"), asset.brand)}
          ${voce(t("mac.modelloL"), asset.model)}
          ${voce(t("mac.serialeL"), seriale && seriale.value)}
          ${voce(t("mac.codiceL"), targa && targa.value)}
          ${voce(t("mac.tipoL"), asset.asset_type)}
        </dl>
        <p class="lavoro-lettura entra" style="margin-top:18px">${esc(asset.description)}</p>
        <details class="disclosure entra" style="margin-top:22px">
          <summary>${esc(t("mac.tecnici"))}</summary>
          <p class="blocco-vuoto">${esc(t("mac.codiceMacchina"))}</p>
          <pre class="grezzo">${esc(asset.asset_id)}</pre>
          <p class="blocco-vuoto">${esc(t("mac.codicePratica"))}</p>
          <pre class="grezzo">${esc(workspace.workspace_id)}</pre>
        </details>
      </div></div>`;
  };

  const campo = (nome, chiave, opzioni) => {
    const config = opzioni || {};
    /* L'identificativo del riquadro informativo è stabile e semantico: è un
       aggancio documentato, non il nome del campo del modulo. */
    const info = config.info ? ` ${root.info(config.id || nome, t(chiave), t(config.info))}` : "";
    const obbligatorio = config.required
      ? ` <small class="campo-obbligatorio">${esc(t("ui.obbligatorio"))}</small>`
      : "";
    const etichetta = `<span class="${config.info ? "con-info" : ""}">${esc(t(chiave))}${info}${obbligatorio}</span>`;
    const controllo = config.area
      ? `<textarea name="${nome}" ${config.required ? 'required aria-required="true"' : ""} ${config.min ? `minlength="${config.min}"` : ""}
          rows="${config.rows || 3}" placeholder="${esc(t(config.p))}"></textarea>`
      : `<input name="${nome}" ${config.required ? 'required aria-required="true"' : ""} autocomplete="off" placeholder="${esc(t(config.p))}">`;
    return `<label class="campo ${config.largo ? "largo" : ""}">${etichetta}${controllo}</label>`;
  };

  const modulo = () => `
    <div class="intestazione-lavoro"><p>${esc(t("mac.sotto"))}</p></div>
    <div class="lavoro-scorri"><div class="lavoro-pad">
      <form id="machine-onboarding" class="modulo entra">
        <div class="modulo-legenda"><strong>${esc(t("mac.sezione1"))}</strong><span>${esc(t("mac.sezione1d"))}</span></div>
        <div class="modulo-griglia">
          ${campo("name", "mac.nome", { required: true, p: "mac.nomeP", info: "mac.nomeI", id: "nome-macchina" })}
          ${campo("brand", "mac.marca", { required: true, p: "mac.marcaP" })}
          ${campo("model", "mac.modello", { required: true, p: "mac.modelloP" })}
          ${campo("asset_type", "mac.tipo", { p: "mac.tipoP", info: "mac.tipoI", id: "tipo-macchina" })}
          ${campo("serial", "mac.seriale", { p: "mac.serialeP", info: "mac.serialeI", id: "numero-seriale" })}
          ${campo("equipment_tag", "mac.codice", { p: "mac.codiceP", info: "mac.codiceI", id: "codice-macchina" })}
          ${campo("description", "mac.descrizione", { required: true, area: true, p: "mac.descrizioneP", largo: true })}
        </div>
        <div class="modulo-legenda"><strong>${esc(t("mac.sezione2"))}</strong><span>${esc(t("mac.sezione2d"))}</span></div>
        <div class="modulo-griglia">
          ${campo("reason", "mac.verifica", { required: true, area: true, rows: 2, min: 10, p: "mac.verificaP", largo: true })}
          <label class="campo"><span class="con-info">${esc(t("mac.dove"))} ${root.info("fonte-verifica", t("mac.dove"), t("mac.doveI"))}</span>
            <select name="observation_basis">
              <option value="nameplate">${esc(t("mac.dove.nameplate"))}</option>
              <option value="direct_observation">${esc(t("mac.dove.direct_observation"))}</option>
              <option value="operator_record">${esc(t("mac.dove.operator_record"))}</option>
            </select></label>
          ${campo("operator", "mac.chi", { required: true, p: "mac.chiP", info: "mac.chiI", id: "operatore-conferma" })}
        </div>
        ${state.error ? `<div class="nota errore" role="alert"><span class="segno" aria-hidden="true">!</span>
          <strong>${esc(t("mac.erroreSalva"))}</strong><span>${esc(state.error)}</span></div>` : ""}
      </form>
    </div></div>`;

  root.phases.machine = {
    mostraFonti: false,
    mostraIspettore: false,

    titolo: () => ({
      titolo: state.workspace ? state.workspace.workspace.asset.name : t("mac.titolo"),
      chips: state.workspace ? `<span class="chip ok"><span class="punto"></span>${esc(t("mac.confermata"))}</span>` : "",
    }),

    renderLavoro() {
      if (state.loading) return `<div class="stato-pagina"><strong>${esc(t("ui.caricamento"))}</strong></div>`;
      return state.workspace ? identificata() : modulo();
    },

    bindLavoro(contenitore) {
      const form = contenitore.querySelector("#machine-onboarding");
      if (!form) return;
      form.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        const valori = new FormData(form);
        const identificativi = [];
        const aggiungi = (nome, spazio, genere) => {
          const valore = String(valori.get(nome) || "").trim();
          if (valore) identificativi.push({ namespace: spazio, value: valore, kind: genere });
        };
        aggiungi("serial", "manufacturer_serial", "serial");
        aggiungi("equipment_tag", "equipment_tag", "equipment_tag");

        state.busy = true;
        state.error = "";
        root.render({ regioni: ["decisione"] });
        try {
          state.workspace = await root.api(state.creatingWorkspace ? "/api/workspaces" : "/api/workspace", {
            method: "POST",
            body: {
              asset: {
                name: valori.get("name"), description: valori.get("description"),
                brand: valori.get("brand"), model: valori.get("model"),
                asset_type: valori.get("asset_type") || null,
              },
              identifiers: identificativi,
              assertion: {
                reason: valori.get("reason"),
                observation_basis: valori.get("observation_basis"),
                operator: valori.get("operator"),
              },
            },
          });
          state.creatingWorkspace = false;
          window.history.replaceState(null, "", root.indirizzoFase("machine", state.workspace.workspace.workspace_id));
          await root.caricaFonti();
        } catch (errore) {
          state.error = errore.message;
        } finally {
          state.busy = false;
          root.render();
        }
      });
    },

    renderDecisione() {
      if (state.loading) return "";
      if (state.workspace) {
        return `<div class="decisione-riga">
          <div class="decisione-testo"><strong>${esc(t("mac.confermata"))}</strong><span>${esc(t("mac.confermataTesto"))}</span></div>
          <div class="decisione-azioni"><button type="button" class="btn primario" data-vai="documents">${esc(t("mac.continua"))}</button></div>
        </div>`;
      }
      return `<div class="decisione-riga">
        <div class="decisione-testo"><strong>${esc(t("mac.dopo"))}</strong><span>${esc(t("mac.dopoTesto"))}</span></div>
        <div class="decisione-azioni">
          <button type="submit" form="machine-onboarding" class="btn primario"
            ${state.busy ? "disabled" : ""}>${esc(state.busy ? t("mac.salvataggio") : t("mac.salva"))}</button>
        </div></div>`;
    },

    bindDecisione(contenitore) {
      root.delegate(contenitore, "click", "[data-vai]", (elemento) => root.vaiAllaFase(elemento.dataset.vai));
    },
  };
})();
