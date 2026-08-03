(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  const nodeLabels = {
    Asset: "Macchina",
    Component: "Componenti",
    Symptom: "Sintomi",
    FailureMode: "Cause",
    CorrectiveAction: "Azioni",
    ErrorCode: "Codici errore",
  };
  const relationLabels = {
    HAS_COMPONENT: "comprende",
    MAY_INDICATE: "può indicare",
    AFFECTS: "interessa",
    RESOLVED_BY: "si risolve con",
    GENERATES_ERROR: "genera errore",
    INDICATES: "indica",
  };
  const typeOrder = ["Asset", "Symptom", "ErrorCode", "FailureMode", "Component", "CorrectiveAction"];

  const uiFor = (sourceId) => {
    state.g3Ui = state.g3Ui || {};
    state.g3Ui[sourceId] = state.g3Ui[sourceId] || { view: "graph", query: "", type: "all", selected: "" };
    return state.g3Ui[sourceId];
  };

  root.loadG3 = async function loadG3() {
    if (!state.workspace) return;
    state.g3Loading = true;
    state.g3Error = "";
    try {
      const workspaceId = state.workspace.workspace.workspace_id;
      state.g3 = await root.api(`/api/workspaces/${encodeURIComponent(workspaceId)}/g3/subgraphs`);
    } catch (error) {
      state.g3Error = error.message;
    } finally {
      state.g3Loading = false;
    }
  };

  const statusLabel = (source) => ({
    waiting: "Da preparare",
    ready: "Pronta",
    reviewing: "Da verificare",
    approved: "Approvato",
    rejected: "Da correggere",
    deferred: "Seconda fase",
  })[source.state] || source.state;

  const nodeMap = (graph) => Object.fromEntries(graph.nodes.map((node) => [node.node_id, node]));

  const evidenceFor = (graph, ids) => {
    const wanted = new Set(ids || []);
    return graph.evidence.filter((item) => wanted.has(item.evidence_id));
  };

  const nodeDetails = (graph, selectedId) => {
    const node = graph.nodes.find((item) => item.node_id === selectedId);
    if (!node) {
      return `<aside class="g3-node-detail is-empty"><strong>Seleziona un nodo</strong><span>Clicca sul grafo o su una riga della tabella per vedere relazioni ed evidenze.</span></aside>`;
    }
    const map = nodeMap(graph);
    const relations = graph.relations.filter((item) => item.from_id === node.node_id || item.to_id === node.node_id);
    const evidence = evidenceFor(graph, node.evidence_ids);
    return `
      <aside class="g3-node-detail" aria-live="polite">
        <header><span class="g3-type-dot type-${escapeHtml(node.node_type)}"></span><div><small>${escapeHtml(nodeLabels[node.node_type])}</small><strong>${escapeHtml(node.label)}</strong></div></header>
        <section><b>Relazioni (${relations.length})</b>${relations.length ? `<ul>${relations.map((relation) => {
          const other = map[relation.from_id === node.node_id ? relation.to_id : relation.from_id];
          return `<li><span>${escapeHtml(relationLabels[relation.relation_type] || relation.relation_type)}</span><strong>${escapeHtml(other ? other.label : "Nodo")}</strong></li>`;
        }).join("")}</ul>` : `<p>Nessuna relazione proposta.</p>`}</section>
        <section><b>Evidenze (${evidence.length})</b>${evidence.map((item) => `<div class="g3-evidence"><strong>${escapeHtml(item.label)}</strong><span>${escapeHtml(item.excerpt || "Evidenza disponibile")}</span></div>`).join("")}</section>
      </aside>`;
  };

  const graphView = (graph, ui) => {
    const groups = Object.fromEntries(typeOrder.map((type) => [type, graph.nodes.filter((node) => node.node_type === type)]));
    const lanes = [
      ["Asset"],
      ["Symptom", "ErrorCode"],
      ["FailureMode"],
      ["Component", "CorrectiveAction"],
    ];
    const maxRows = Math.max(1, ...lanes.map((types) => types.flatMap((type) => groups[type]).length));
    const height = Math.max(390, maxRows * 68 + 70);
    const laneX = [85, 295, 505, 715];
    const positions = {};
    lanes.forEach((types, laneIndex) => {
      const items = types.flatMap((type) => groups[type]);
      const available = height - 86;
      items.forEach((node, index) => {
        positions[node.node_id] = {
          x: laneX[laneIndex],
          y: 55 + ((index + 1) * available / (items.length + 1)),
        };
      });
    });
    const connected = new Set([ui.selected]);
    graph.relations.forEach((relation) => {
      if (relation.from_id === ui.selected) connected.add(relation.to_id);
      if (relation.to_id === ui.selected) connected.add(relation.from_id);
    });
    const edges = graph.relations.map((relation) => {
      const from = positions[relation.from_id];
      const to = positions[relation.to_id];
      if (!from || !to) return "";
      const highlighted = !ui.selected || relation.from_id === ui.selected || relation.to_id === ui.selected;
      return `<path class="g3-edge ${highlighted ? "is-related" : "is-muted"}" d="M ${from.x + 65} ${from.y} C ${(from.x + to.x) / 2} ${from.y}, ${(from.x + to.x) / 2} ${to.y}, ${to.x - 65} ${to.y}" marker-end="url(#g3-arrow)"><title>${escapeHtml(relationLabels[relation.relation_type] || relation.relation_type)}</title></path>`;
    }).join("");
    const nodes = graph.nodes.map((node) => {
      const position = positions[node.node_id];
      const selected = node.node_id === ui.selected;
      const muted = ui.selected && !connected.has(node.node_id);
      const label = node.label.length > 22 ? `${node.label.slice(0, 21)}…` : node.label;
      return `<g class="g3-svg-node type-${escapeHtml(node.node_type)} ${selected ? "is-selected" : ""} ${muted ? "is-muted" : ""}" transform="translate(${position.x - 65} ${position.y - 22})" role="button" tabindex="0" data-g3-node="${escapeHtml(node.node_id)}" aria-label="${escapeHtml(nodeLabels[node.node_type])}: ${escapeHtml(node.label)}">
        <rect width="130" height="44" rx="9"></rect><text x="65" y="19" text-anchor="middle">${escapeHtml(label)}</text><text class="g3-node-type" x="65" y="33" text-anchor="middle">${escapeHtml(nodeLabels[node.node_type])}</text><title>${escapeHtml(node.label)}</title>
      </g>`;
    }).join("");
    return `
      <div class="g3-graph-layout">
        <div class="g3-canvas" aria-label="Grafo navigabile della fonte">
          <div class="g3-legend">${typeOrder.filter((type) => groups[type].length).map((type) => `<span><i class="type-${type}"></i>${escapeHtml(nodeLabels[type])}</span>`).join("")}</div>
          <div class="g3-svg-scroll"><svg viewBox="0 0 800 ${height}" role="img" aria-label="${graph.nodes.length} nodi e ${graph.relations.length} relazioni"><defs><marker id="g3-arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z"></path></marker></defs>${edges}${nodes}</svg></div>
        </div>
        ${nodeDetails(graph, ui.selected)}
      </div>`;
  };

  const nodeTable = (graph, ui) => {
    const query = ui.query.trim().toLocaleLowerCase();
    const counts = Object.fromEntries(graph.nodes.map((node) => [node.node_id, graph.relations.filter((relation) => relation.from_id === node.node_id || relation.to_id === node.node_id).length]));
    const nodes = graph.nodes.filter((node) => (ui.type === "all" || node.node_type === ui.type) && (!query || node.label.toLocaleLowerCase().includes(query)));
    return `
      <form class="g3-filter" data-g3-filter><label>Cerca nodo<input type="search" name="query" value="${escapeHtml(ui.query)}" placeholder="es. pompa, perdita, E-17"></label><label>Tipo<select name="type"><option value="all">Tutti i tipi</option>${typeOrder.map((type) => `<option value="${type}" ${ui.type === type ? "selected" : ""}>${escapeHtml(nodeLabels[type])}</option>`).join("")}</select></label><button class="btn-ghost" type="submit">Filtra</button></form>
      <div class="g3-table-scroll"><table class="g3-table"><thead><tr><th>Tipo</th><th>Nodo</th><th>Relazioni</th><th>Evidenze</th></tr></thead><tbody>${nodes.length ? nodes.map((node) => `<tr class="${ui.selected === node.node_id ? "is-selected" : ""}" data-g3-node="${escapeHtml(node.node_id)}" tabindex="0"><td><span class="g3-type-label"><i class="type-${node.node_type}"></i>${escapeHtml(nodeLabels[node.node_type])}</span></td><td><strong>${escapeHtml(node.label)}</strong></td><td>${counts[node.node_id]}</td><td>${node.evidence_ids.length}</td></tr>`).join("") : `<tr><td colspan="4">Nessun nodo corrisponde ai filtri.</td></tr>`}</tbody></table></div>
      ${nodeDetails(graph, ui.selected)}`;
  };

  const relationTable = (graph, ui) => {
    const map = nodeMap(graph);
    return `<div class="g3-table-scroll"><table class="g3-table"><thead><tr><th>Da</th><th>Relazione</th><th>A</th><th>Evidenze</th></tr></thead><tbody>${graph.relations.map((relation) => `<tr><td><button type="button" data-g3-node="${escapeHtml(relation.from_id)}">${escapeHtml(map[relation.from_id]?.label || relation.from_id)}</button></td><td><span class="g3-relation-label">${escapeHtml(relationLabels[relation.relation_type] || relation.relation_type)}</span></td><td><button type="button" data-g3-node="${escapeHtml(relation.to_id)}">${escapeHtml(map[relation.to_id]?.label || relation.to_id)}</button></td><td>${relation.evidence_ids.length}</td></tr>`).join("")}</tbody></table></div>${nodeDetails(graph, ui.selected)}`;
  };

  const validationPanel = (graph) => {
    const validation = graph.validation || {};
    const gaps = graph.knowledge_gaps || [];
    const structuralIssues = validation.issues || [];
    if (graph.approval_eligible) {
      return `<section class="g3-validation is-valid"><strong>✓ Controlli ontologici e provenienza superati</strong><span>Proprietà obbligatorie complete, nessun campo extra e tutte le evidenze sono risolvibili.</span></section>`;
    }
    const messages = [...gaps.map((item) => item.message), ...structuralIssues.map((item) => item.message)];
    return `<section class="g3-validation is-blocked"><strong>Approvazione bloccata</strong><span>${escapeHtml(messages[0] || "Il sottografo non soddisfa i controlli richiesti.")}</span>${messages.length > 1 ? `<details><summary>Vedi ${messages.length} problemi rilevati</summary><ul>${messages.map((message) => `<li>${escapeHtml(message)}</li>`).join("")}</ul></details>` : ""}</section>`;
  };

  const reviewPanel = (source) => {
    const graph = source.subgraph;
    const ui = uiFor(source.source_id);
    const content = ui.view === "nodes" ? nodeTable(graph, ui) : ui.view === "relations" ? relationTable(graph, ui) : graphView(graph, ui);
    return `
      <section class="g3-review" data-g3-review="${escapeHtml(source.source_id)}">
        <nav class="g3-view-tabs" aria-label="Viste del sottografo">
          ${[["graph", "Grafo"], ["nodes", `Nodi (${graph.nodes.length})`], ["relations", `Relazioni (${graph.relations.length})`]].map(([key, label]) => `<button type="button" class="${ui.view === key ? "is-active" : ""}" data-g3-view="${key}">${escapeHtml(label)}</button>`).join("")}
        </nav>
        ${content}
        ${validationPanel(graph)}
        ${source.state === "reviewing" ? `<footer class="g3-review-actions"><div><strong>${graph.approval_eligible ? "Il sottografo rappresenta correttamente questa fonte?" : "Correggi o classifica le lacune prima di approvare"}</strong><span>${graph.approval_eligible ? "L’approvazione vale solo per questo file e non unisce ancora fonti diverse." : "Le relazioni non dimostrabili non sono state inventate e restano visibili come knowledge gap."}</span></div><button class="btn-ghost g3-reject" type="button" data-g3-decision="reject">Segnala da correggere</button>${graph.approval_eligible ? `<button class="btn-primary" type="button" data-g3-decision="approve">Approva sottografo</button>` : ""}</footer>` : source.state === "approved" ? `<p class="g3-approved-note">✓ Sottografo approvato per questa fonte</p>` : `<p class="g3-rejected-note">Da correggere: ${escapeHtml(graph.decision_note || "segnalazione registrata")}</p>`}
      </section>`;
  };

  const sourceCard = (source) => {
    const graph = source.subgraph;
    const expanded = state.g3Expanded === source.source_id || (!state.g3Expanded && source.state === "reviewing");
    const metrics = graph ? `<span>${graph.nodes.length} nodi</span><span>${graph.relations.length} relazioni</span><span>${graph.evidence_ids.length} evidenze</span><span>${graph.duplicate_nodes_consolidated + graph.duplicate_relations_consolidated} duplicati consolidati</span><span>${graph.approval_eligible ? "validazione superata" : "validazione bloccante"}</span>` : "";
    return `
      <article class="g3-source-card state-${escapeHtml(source.state)}" data-g3-source="${escapeHtml(source.source_id)}">
        <header>
          <span class="source-file-type">${escapeHtml(source.source_kind.toUpperCase())}</span>
          <div class="g3-source-title"><strong>${escapeHtml(source.source_name)}</strong><small>${escapeHtml(source.message)}</small>${metrics ? `<div class="g3-metrics">${metrics}</div>` : ""}</div>
          <span class="pill g3-status">${escapeHtml(statusLabel(source))}</span>
          ${source.state === "ready" ? `<button class="btn-primary g3-generate" type="button" data-g3-generate>Genera sottografo</button>` : graph ? `<button class="btn-ghost g3-toggle" type="button" data-g3-toggle aria-expanded="${expanded}">${expanded ? "Chiudi" : "Controlla"}</button>` : ""}
        </header>
        ${expanded && graph ? reviewPanel(source) : ""}
      </article>`;
  };

  const barrierPanel = () => {
    const barrier = state.g3.merge_barrier;
    if (barrier.state !== "ready") {
      const pending = barrier.pending_source_ids.length;
      return `<section class="g3-barrier is-locked"><span aria-hidden="true">🔒</span><div><strong>Confronto tra fonti non ancora disponibile</strong><p>${pending} ${pending === 1 ? "fonte deve" : "fonti devono"} ancora essere generata e approvata. Nessun nodo viene unito prima.</p></div></section>`;
    }
    const matches = barrier.exact_matches;
    return `<section class="g3-barrier is-ready"><span aria-hidden="true">✓</span><div><strong>Fonti pronte per il confronto</strong><p>Tutti i sottografi inclusi sono approvati. Il sistema ha trovato ${matches.length} ${matches.length === 1 ? "corrispondenza esatta" : "corrispondenze esatte"} da presentare nella revisione successiva.</p>${matches.length ? `<details><summary>Vedi le corrispondenze esatte</summary><ul>${matches.map((match) => `<li><b>${escapeHtml(nodeLabels[match.node_type])}:</b> ${escapeHtml(match.label)} <span>(${match.occurrences.map((item) => escapeHtml(item.source_name)).join(" · ")})</span></li>`).join("")}</ul></details>` : ""}</div></section>`;
  };

  root.renderG3 = function renderG3() {
    if (!state.workspace || state.g3Loading) {
      return '<main class="foundation-main"><section class="foundation-card g2-loading"><strong>Carico i sottografi…</strong><p>Ogni fonte resta separata fino alla tua approvazione.</p></section></main>';
    }
    if (state.g3Error || !state.g3) {
      return `<main class="foundation-main"><section class="foundation-card"><p class="foundation-error" role="alert">${escapeHtml(state.g3Error || "Elaborazione non disponibile")}</p><button class="btn-primary" type="button" data-g3-retry>Riprova</button></section></main>`;
    }
    return `
      <main class="foundation-main">
        <section class="foundation-card g3-card">
          <div class="foundation-step-heading"><span class="foundation-step-number">5</span><div><p class="kicker">Passo 5 · Elaborazione</p><h1>Controlla un grafo alla volta</h1><p>Ogni file genera un sottografo separato. Esplora nodi, relazioni e righe originali, poi approva soltanto quella fonte.</p></div><span class="pill g3-progress">${state.g3.counts.approved_sources}/${state.g3.counts.eligible_sources} approvati</span></div>
          <div class="g3-source-list">${state.g3.sources.map(sourceCard).join("")}</div>
          ${barrierPanel()}
          <a class="g2-back" href="/console.html?foundation=1&amp;workspace_id=${encodeURIComponent(state.workspace.workspace.workspace_id)}&amp;stage=g2">← Torna alla struttura dati</a>
          ${state.g3Error ? `<p class="foundation-error" role="alert">${escapeHtml(state.g3Error)}</p>` : ""}
        </section>
      </main>`;
  };

  root.bindG3 = function bindG3(render) {
    const run = async (action) => {
      state.g3Busy = true;
      state.g3Error = "";
      render();
      try { state.g3 = await action(); } catch (error) { state.g3Error = error.message; }
      finally { state.g3Busy = false; render(); }
    };
    document.querySelector("[data-g3-retry]")?.addEventListener("click", () => run(async () => {
      await root.loadG3();
      if (!state.g3) throw new Error(state.g3Error || "Elaborazione non disponibile");
      return state.g3;
    }));
    document.querySelectorAll("[data-g3-generate]").forEach((button) => button.addEventListener("click", () => {
      const card = button.closest("[data-g3-source]");
      state.g3Expanded = card.dataset.g3Source;
      const workspaceId = state.workspace.workspace.workspace_id;
      run(() => root.api(`/api/workspaces/${encodeURIComponent(workspaceId)}/g3/sources/${encodeURIComponent(card.dataset.g3Source)}/generate`, { method: "POST" }));
    }));
    document.querySelectorAll("[data-g3-toggle]").forEach((button) => button.addEventListener("click", () => {
      const sourceId = button.closest("[data-g3-source]").dataset.g3Source;
      state.g3Expanded = state.g3Expanded === sourceId ? "" : sourceId;
      render();
    }));
    document.querySelectorAll("[data-g3-view]").forEach((button) => button.addEventListener("click", () => {
      const sourceId = button.closest("[data-g3-review]").dataset.g3Review;
      uiFor(sourceId).view = button.dataset.g3View;
      render();
    }));
    document.querySelectorAll("[data-g3-node]").forEach((element) => {
      const select = () => {
        const sourceId = element.closest("[data-g3-review]").dataset.g3Review;
        uiFor(sourceId).selected = element.dataset.g3Node;
        render();
      };
      element.addEventListener("click", select);
      element.addEventListener("keydown", (event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); select(); } });
    });
    document.querySelector("[data-g3-filter]")?.addEventListener("submit", (event) => {
      event.preventDefault();
      const sourceId = event.currentTarget.closest("[data-g3-review]").dataset.g3Review;
      const data = new FormData(event.currentTarget);
      uiFor(sourceId).query = String(data.get("query") || "");
      uiFor(sourceId).type = String(data.get("type") || "all");
      render();
    });
    document.querySelectorAll("[data-g3-decision]").forEach((button) => button.addEventListener("click", () => {
      const sourceId = button.closest("[data-g3-review]").dataset.g3Review;
      const source = state.g3.sources.find((item) => item.source_id === sourceId);
      const action = button.dataset.g3Decision;
      let note = null;
      if (action === "reject") {
        note = window.prompt("Cosa deve essere corretto in questo sottografo?");
        if (!note || !note.trim()) return;
      }
      run(() => root.api(`/api/g3/subgraphs/${encodeURIComponent(source.subgraph.source_subgraph_revision_id)}/decision`, { method: "POST", body: { action, note } }));
    }));
  };
})();
