(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const app = document.getElementById("app");
  const escapeHtml = root.escapeHtml;

  /** Internal workspace states, said in the operator's words. */
  const STATUS = {
    sources_required: { label: "Documenti da caricare", tone: "warning" },
    preparation_required: { label: "Lettura in corso", tone: "warning" },
    ready: { label: "Pronta", tone: "success" },
    processing: { label: "Elaborazione in corso", tone: "warning" },
    paused: { label: "In pausa", tone: "" },
    failed_resumable: { label: "Da riprendere", tone: "warning" },
    failed_terminal: { label: "Errore", tone: "danger" },
    awaiting_review: { label: "Da verificare", tone: "warning" },
    ready_to_publish: { label: "Verificata", tone: "success" },
  };

  const render = (machines, error = "", loading = false) => {
    const cards = machines.map((machine) => {
      const status = STATUS[machine.status] || { label: machine.status, tone: "" };
      const documents = root.plural(machine.document_count, "documento", "documenti");
      const updated = new Date(machine.updated_at).toLocaleString("it-IT", {
        day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
      });
      return `
        <a class="kg-home-card" href="/console.html?foundation=1&workspace_id=${encodeURIComponent(machine.workspace_id)}">
          <span class="kg-home-card-main">
            <strong>${escapeHtml(machine.asset_name)}</strong>
            <span class="kg-secondary">${escapeHtml(machine.brand)} · ${escapeHtml(machine.model)} · ${escapeHtml(documents)}</span>
          </span>
          <span class="kg-home-card-side">
            <span class="kg-caption">${escapeHtml(updated)}</span>
            <span class="kg-badge ${status.tone ? `kg-badge-${status.tone}` : ""}">
              <span class="kg-badge-dot" aria-hidden="true"></span>${escapeHtml(status.label)}</span>
          </span>
        </a>`;
    }).join("");

    app.innerHTML = `
      <header class="kg-topbar kg-floating" style="grid-template-columns: minmax(0, 1fr)">
        <span class="kg-label">Maintenance KG Builder</span>
      </header>
      <main class="kg-home">
        <div class="kg-home-inner">
          <div class="kg-home-head">
            <div>
              <h1>Macchine</h1>
              <p>Apri una macchina per continuare dal punto in cui l'hai lasciata.</p>
            </div>
            <a class="kg-btn kg-btn-primary" href="/console.html?foundation=1&new=1">Nuova macchina</a>
          </div>
          ${error ? `
            <div class="kg-note kg-note-danger" role="alert">
              <span class="kg-note-mark" aria-hidden="true">!</span>
              <strong>Non riesco a caricare l'elenco</strong>
              <span>${escapeHtml(error)}</span>
            </div>` : ""}
          <div class="kg-home-list">
            ${loading ? `<p class="kg-secondary">Carico l'elenco…</p>` : cards || `
              <div class="kg-empty">
                <strong>Nessuna macchina</strong>
                <p>Configura la prima macchina per iniziare a costruirne il grafo.</p>
                <a class="kg-btn kg-btn-primary" href="/console.html?foundation=1&new=1">Configura la prima macchina</a>
              </div>`}
          </div>
        </div>
      </main>`;
  };

  render([], "", true);
  root.api("/api/workspaces")
    .then((machines) => render(machines))
    .catch((error) => render([], error.message));
})();
