(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[character]);
  }

  root.renderMachine = function renderMachine() {
    const state = root.state;
    if (state.loading) return '<main class="foundation-main"><p>Carico i dati salvati…</p></main>';
    if (state.workspace) {
      const workspace = state.workspace.workspace;
      const asset = workspace.asset;
      const identifiers = workspace.identifiers || [];
      const serial = identifiers.find((item) => item.kind === "serial");
      const equipmentTag = identifiers.find((item) => item.kind === "equipment_tag");
      return `
        <main class="foundation-main">
          <section class="foundation-card">
            <div class="foundation-step-heading">
              <span class="foundation-step-number is-complete">✓</span>
              <div>
                <p class="kicker">Passo 1 completato · Macchina</p>
                <h1>${escapeHtml(asset.name)}</h1>
                <p>Hai confermato questa macchina. Ora puoi caricare i documenti che la riguardano.</p>
              </div>
              <span class="pill machine-state">Confermata</span>
            </div>
            <dl class="foundation-summary">
              <div><dt>Marca</dt><dd>${escapeHtml(asset.brand)}</dd></div>
              <div><dt>Modello</dt><dd>${escapeHtml(asset.model)}</dd></div>
              ${serial ? `<div><dt>Numero seriale</dt><dd>${escapeHtml(serial.value)}</dd></div>` : ""}
              ${equipmentTag ? `<div><dt>Codice macchina</dt><dd>${escapeHtml(equipmentTag.value)}</dd></div>` : ""}
              ${asset.asset_type ? `<div><dt>Tipo macchina</dt><dd>${escapeHtml(asset.asset_type)}</dd></div>` : ""}
            </dl>
            <p>${escapeHtml(asset.description)}</p>
            <details class="foundation-technical">
              <summary>Dati tecnici e identificativi interni</summary>
              <p>Identificativo macchina <code>${escapeHtml(asset.asset_id)}</code></p>
              <p>Identificativo pratica <code>${escapeHtml(workspace.workspace_id)}</code></p>
              <p>Stato interno <code>${escapeHtml(workspace.status)}</code> · Versione struttura dati <code>${escapeHtml(workspace.ontology_sha256.slice(0, 12))}…</code></p>
            </details>
          </section>
          ${root.renderSources ? root.renderSources() : ""}
          ${root.renderPreparation ? root.renderPreparation() : ""}
        </main>`;
    }
    return `
      <main class="foundation-main">
        <form id="machine-onboarding" class="foundation-card">
          <div class="foundation-step-heading">
            <span class="foundation-step-number">1</span>
            <div>
              <p class="kicker">Macchina</p>
              <h1>Identifica la macchina</h1>
              <p>Inserisci i dati della targhetta e conferma l’identità della macchina. Solo dopo potrai caricare i documenti che la riguardano.</p>
            </div>
            <span class="pill machine-state is-pending">Da completare</span>
          </div>
          <div class="foundation-grid">
            <p class="form-section-title wide"><strong>1. Inserisci i dati identificativi</strong><span>Copiali dalla targhetta o dal registro ufficiale della macchina.</span></p>
            <label><span class="label-with-info">Nome macchina ${root.infoTip("nome-macchina", "Nome macchina", "Usa il nome con cui riconosci la macchina nello stabilimento, per esempio “Pressa idraulica linea 7”.")}</span><input name="name" required autocomplete="off" placeholder="Esempio: Pressa idraulica linea 7"></label>
            <label>Marca / costruttore<input name="brand" required autocomplete="off" placeholder="Esempio: ExampleWorks"></label>
            <label>Modello<input name="model" required autocomplete="off" placeholder="Esempio: HP-700"></label>
            <label><span class="label-with-info">Tipo di macchina (opzionale) ${root.infoTip("tipo-macchina", "Tipo di macchina", "Descrivi la famiglia della macchina, per esempio pressa idraulica, tornio CNC o compressore.")}</span><input name="asset_type" autocomplete="off" placeholder="Esempio: pressa idraulica"></label>
            <label><span class="label-with-info">Numero seriale ${root.infoTip("numero-seriale", "Numero seriale", "Inserisci il numero assegnato dal costruttore. Di solito lo trovi sulla targhetta accanto a “Serial”, “S/N” o “Matricola”.")}</span><input name="serial" autocomplete="off" placeholder="Esempio: HP7-000042"></label>
            <label><span class="label-with-info">Codice macchina (opzionale) ${root.infoTip("codice-macchina", "Codice macchina", "Inserisci il codice interno usato nel tuo impianto, chiamato anche equipment tag o asset tag.")}</span><input name="equipment_tag" autocomplete="off" placeholder="Esempio: PRESS-07"></label>
            <label class="wide">Descrizione breve<textarea name="description" required rows="3" placeholder="Dove si trova e a cosa serve questa macchina?"></textarea></label>
            <p class="form-section-title wide"><strong>2. Conferma i dati</strong><span>Indica come hai verificato l’identità della macchina e chi lo ha fatto.</span></p>
            <label class="wide">Come hai verificato questi dati?<textarea name="reason" required minlength="10" rows="2" placeholder="Esempio: dati letti direttamente dalla targhetta della macchina"></textarea></label>
            <label><span class="label-with-info">Dove hai verificato i dati? ${root.infoTip("fonte-verifica", "Fonte della verifica", "Scegli la fonte che hai effettivamente controllato: targhetta, macchina osservata direttamente oppure registro dell’operatore.")}</span>
              <select name="observation_basis">
                <option value="nameplate">Targhetta macchina</option>
                <option value="direct_observation">Osservazione diretta</option>
                <option value="operator_record">Registro operatore</option>
              </select>
            </label>
            <label><span class="label-with-info">Inserisci chi conferma ${root.infoTip("operatore-conferma", "Chi conferma", "Scrivi il tuo nome o le tue iniziali. Servono a rendere tracciabile la conferma.")}</span><input name="operator" required autocomplete="off" placeholder="Nome o iniziali"></label>
          </div>
          ${state.error ? `<p class="foundation-error" role="alert">${escapeHtml(state.error)}</p>` : ""}
          <div class="machine-onboarding-action">
            <div>
              <strong>Dopo il salvataggio</strong>
              <span>Passerai al punto 2, dove potrai caricare e classificare i documenti della macchina.</span>
            </div>
            <button class="btn-primary" type="submit" ${state.busy ? "disabled" : ""}>${state.busy ? "Salvataggio…" : "Salva macchina e continua"}</button>
          </div>
        </form>
      </main>`;
  };

  root.bindMachine = function bindMachine(render) {
    const form = document.getElementById("machine-onboarding");
    if (!form) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const values = new FormData(form);
      const identifiers = [];
      if (String(values.get("serial") || "").trim()) {
        identifiers.push({ namespace: "manufacturer_serial", value: String(values.get("serial")).trim(), kind: "serial" });
      }
      if (String(values.get("equipment_tag") || "").trim()) {
        identifiers.push({ namespace: "equipment_tag", value: String(values.get("equipment_tag")).trim(), kind: "equipment_tag" });
      }
      root.state.busy = true;
      root.state.error = "";
      render();
      try {
        root.state.workspace = await root.api("/api/workspace", {
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
      } catch (error) {
        root.state.error = error.message;
      } finally {
        root.state.busy = false;
        render();
      }
    });
  };
})();
