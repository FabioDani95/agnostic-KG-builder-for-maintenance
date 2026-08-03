(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  const identified = () => {
    const workspace = state.workspace.workspace;
    const asset = workspace.asset;
    const identifiers = workspace.identifiers || [];
    const find = (kind) => identifiers.find((item) => item.kind === kind);
    const serial = find("serial");
    const tag = find("equipment_tag");
    return `
      <div class="kg-work-head">
        <div class="kg-work-head-row"><h1>${escapeHtml(asset.name)}</h1></div>
        <p>Questa è la macchina su cui stai lavorando. Tutti i documenti e tutto il grafo appartengono solo a lei.</p>
      </div>
      <div class="kg-work-scroll"><div class="kg-work-pad">
        <dl class="kg-summary">
          <div><dt>Marca</dt><dd>${escapeHtml(asset.brand)}</dd></div>
          <div><dt>Modello</dt><dd>${escapeHtml(asset.model)}</dd></div>
          ${serial ? `<div><dt>Numero seriale</dt><dd>${escapeHtml(serial.value)}</dd></div>` : ""}
          ${tag ? `<div><dt>Codice macchina</dt><dd>${escapeHtml(tag.value)}</dd></div>` : ""}
          ${asset.asset_type ? `<div><dt>Tipo di macchina</dt><dd>${escapeHtml(asset.asset_type)}</dd></div>` : ""}
        </dl>
        <p class="kg-body kg-work-reading" style="margin-top: var(--space-4)">${escapeHtml(asset.description)}</p>
        <details class="kg-disclosure" style="margin-top: var(--space-5)">
          <summary>Dati tecnici interni</summary>
          <p class="kg-secondary">Codice della macchina nel sistema</p>
          <pre class="kg-evidence-raw">${escapeHtml(asset.asset_id)}</pre>
          <p class="kg-secondary">Codice della pratica</p>
          <pre class="kg-evidence-raw">${escapeHtml(workspace.workspace_id)}</pre>
        </details>
      </div></div>`;
  };

  const onboarding = () => `
    <div class="kg-work-head">
      <div class="kg-work-head-row"><h1>Identifica la macchina</h1></div>
      <p>Inserisci i dati della targhetta e conferma l'identità. Solo dopo potrai caricare i documenti che la riguardano.</p>
    </div>
    <div class="kg-work-scroll"><div class="kg-work-pad">
      <form id="machine-onboarding" class="kg-form">
        <div class="kg-form-legend"><strong>1. Dati identificativi</strong><span>Copiali dalla targhetta o dal registro ufficiale della macchina.</span></div>
        <div class="kg-form-grid">
          <label class="kg-field"><span class="kg-label-with-info">Nome macchina ${root.infoTip("nome-macchina", "Nome macchina", "Usa il nome con cui riconosci la macchina nello stabilimento, per esempio “Pressa idraulica linea 7”.")}</span>
            <input class="kg-input" name="name" required autocomplete="off" placeholder="Esempio: Pressa idraulica linea 7"></label>
          <label class="kg-field"><span>Marca o costruttore</span>
            <input class="kg-input" name="brand" required autocomplete="off" placeholder="Esempio: ExampleWorks"></label>
          <label class="kg-field"><span>Modello</span>
            <input class="kg-input" name="model" required autocomplete="off" placeholder="Esempio: HP-700"></label>
          <label class="kg-field"><span class="kg-label-with-info">Tipo di macchina (facoltativo) ${root.infoTip("tipo-macchina", "Tipo di macchina", "Descrivi la famiglia della macchina, per esempio pressa idraulica, tornio CNC o compressore.")}</span>
            <input class="kg-input" name="asset_type" autocomplete="off" placeholder="Esempio: pressa idraulica"></label>
          <label class="kg-field"><span class="kg-label-with-info">Numero seriale ${root.infoTip("numero-seriale", "Numero seriale", "Inserisci il numero assegnato dal costruttore. Di solito lo trovi sulla targhetta accanto a “Serial”, “S/N” o “Matricola”.")}</span>
            <input class="kg-input" name="serial" autocomplete="off" placeholder="Esempio: HP7-000042"></label>
          <label class="kg-field"><span class="kg-label-with-info">Codice macchina (facoltativo) ${root.infoTip("codice-macchina", "Codice macchina", "Inserisci il codice interno usato nel tuo impianto, chiamato anche equipment tag o asset tag.")}</span>
            <input class="kg-input" name="equipment_tag" autocomplete="off" placeholder="Esempio: PRESS-07"></label>
          <label class="kg-field kg-wide"><span>Descrizione breve</span>
            <textarea class="kg-textarea" name="description" required rows="3" placeholder="Dove si trova e a cosa serve questa macchina?"></textarea></label>
        </div>
        <div class="kg-form-legend"><strong>2. Conferma dei dati</strong><span>Indica come hai verificato l'identità della macchina e chi lo ha fatto.</span></div>
        <div class="kg-form-grid">
          <label class="kg-field kg-wide"><span>Come hai verificato questi dati?</span>
            <textarea class="kg-textarea" name="reason" required minlength="10" rows="2" placeholder="Esempio: dati letti direttamente dalla targhetta della macchina"></textarea></label>
          <label class="kg-field"><span class="kg-label-with-info">Dove hai verificato i dati? ${root.infoTip("fonte-verifica", "Fonte della verifica", "Scegli la fonte che hai effettivamente controllato: targhetta, macchina osservata direttamente oppure registro dell’operatore.")}</span>
            <select class="kg-select" name="observation_basis">
              <option value="nameplate">Targhetta macchina</option>
              <option value="direct_observation">Osservazione diretta</option>
              <option value="operator_record">Registro operatore</option>
            </select></label>
          <label class="kg-field"><span class="kg-label-with-info">Chi conferma ${root.infoTip("operatore-conferma", "Chi conferma", "Scrivi il tuo nome o le tue iniziali. Servono a rendere tracciabile la conferma.")}</span>
            <input class="kg-input" name="operator" required autocomplete="off" placeholder="Nome o iniziali"></label>
        </div>
        ${state.error ? `<div class="kg-note kg-note-danger" role="alert"><span class="kg-note-mark" aria-hidden="true">!</span><strong>Non riesco a salvare</strong><span>${escapeHtml(state.error)}</span></div>` : ""}
      </form>
    </div></div>`;

  root.phases.machine = {
    label: "Macchina",
    showRail: false,
    showInspector: false,

    renderWork() {
      if (state.loading) return `<div class="kg-state"><strong>Carico i dati salvati…</strong></div>`;
      return state.workspace ? identified() : onboarding();
    },

    bindWork(container) {
      const form = container.querySelector("#machine-onboarding");
      if (!form) return;
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const values = new FormData(form);
        const identifiers = [];
        const push = (name, namespace, kind) => {
          const value = String(values.get(name) || "").trim();
          if (value) identifiers.push({ namespace, value, kind });
        };
        push("serial", "manufacturer_serial", "serial");
        push("equipment_tag", "equipment_tag", "equipment_tag");

        state.busy = true;
        state.error = "";
        root.render({ regions: ["decision"] });
        try {
          state.workspace = await root.api(state.creatingWorkspace ? "/api/workspaces" : "/api/workspace", {
            method: "POST",
            body: {
              asset: {
                name: values.get("name"),
                description: values.get("description"),
                brand: values.get("brand"),
                model: values.get("model"),
                asset_type: values.get("asset_type") || null,
              },
              identifiers,
              assertion: {
                reason: values.get("reason"),
                observation_basis: values.get("observation_basis"),
                operator: values.get("operator"),
              },
            },
          });
          state.creatingWorkspace = false;
          window.history.replaceState(null, "", root.phaseHref("machine", state.workspace.workspace.workspace_id));
          await root.loadSources();
        } catch (error) {
          state.error = error.message;
        } finally {
          state.busy = false;
          root.render();
        }
      });
    },

    renderDecision() {
      if (state.loading) return "";
      if (state.workspace) {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>Macchina confermata</strong>
          <span>Ora puoi caricare i documenti che la riguardano.</span>
        </div>
        <div class="kg-decision-actions">
          <button type="button" class="kg-btn kg-btn-primary" data-kg-goto="documents">Continua ai documenti</button>
        </div></div>`;
      }
      return `<div class="kg-decision-row"><div class="kg-decision-text">
        <strong>Dopo il salvataggio</strong>
        <span>Passerai ai documenti, dove potrai caricare e classificare i file della macchina.</span>
      </div>
      <div class="kg-decision-actions">
        <button type="submit" form="machine-onboarding" class="kg-btn kg-btn-primary"
          ${state.busy ? "disabled" : ""}>${state.busy ? "Salvataggio…" : "Salva macchina e continua"}</button>
      </div></div>`;
    },

    bindDecision(container) {
      root.delegate(container, "click", "[data-kg-goto]", (element) => root.goToPhase(element.dataset.kgGoto));
    },
  };
})();
