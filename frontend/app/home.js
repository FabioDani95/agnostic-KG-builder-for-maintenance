(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const app = document.getElementById("app");
  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
  const statusLabels = {
    sources_required: "Documenti da caricare",
    preparation_required: "Preparazione in corso",
    ready: "Pronto",
    processing: "In elaborazione",
    paused: "In pausa",
    failed_resumable: "Da riprendere",
    failed_terminal: "Errore",
    awaiting_review: "In revisione",
    ready_to_publish: "Pronto da pubblicare",
  };

  const render = (workspaces, error = "", loading = false) => {
    const cards = workspaces.map((workspace) => {
      const href = `/console.html?foundation=1&workspace_id=${encodeURIComponent(workspace.workspace_id)}`;
      const documents = workspace.document_count === 1
        ? "1 documento caricato"
        : `${workspace.document_count} documenti caricati`;
      return `
        <article class="workspace-home-card">
          <div class="workspace-home-card-top">
            <span class="pill workspace-home-status">${escapeHtml(statusLabels[workspace.status] || workspace.status)}</span>
            <span class="workspace-home-updated">Aggiornato ${escapeHtml(new Date(workspace.updated_at).toLocaleString("it-IT"))}</span>
          </div>
          <h2>${escapeHtml(workspace.asset_name)}</h2>
          <p>${escapeHtml(workspace.brand)} · ${escapeHtml(workspace.model)}</p>
          <div class="workspace-home-meta">
            <strong>${escapeHtml(documents)}</strong>
            <code>${escapeHtml(workspace.workspace_id)}</code>
          </div>
          <a class="btn-primary workspace-home-open" href="${escapeHtml(href)}">Apri workspace</a>
        </article>`;
    }).join("");

    app.innerHTML = `
      <header class="c-header">
        <strong>Maintenance KG Builder</strong>
        <span class="pill foundation-pill">Workspace</span>
      </header>
      <main class="workspace-home-main">
        <section class="workspace-home-heading">
          <div class="workspace-home-heading-top">
            <div><p class="kicker">Home</p><h1>I tuoi workspace</h1></div>
            <a class="btn-primary workspace-home-open" href="/console.html?foundation=1&new=1">+ Nuovo workspace</a>
          </div>
          <p>Apri un workspace per continuare dal suo stato aggiornato.</p>
        </section>
        ${error ? `<div class="foundation-error" role="alert"><strong>Impossibile caricare i workspace</strong><p>${escapeHtml(error)}</p></div>` : ""}
        <section class="workspace-home-list">
          ${loading ? '<div class="workspace-home-empty"><p>Carico i workspace…</p></div>' : cards || `
            <div class="workspace-home-empty">
              <h2>Nessun workspace disponibile</h2>
              <p>Configura la prima macchina per iniziare.</p>
              <a class="btn-primary workspace-home-open" href="/console.html?foundation=1">Configura workspace</a>
            </div>`}
        </section>
      </main>`;
  };

  render([], "", true);
  root.api("/api/workspaces")
    .then((workspaces) => render(workspaces))
    .catch((error) => render([], error.message));
})();
