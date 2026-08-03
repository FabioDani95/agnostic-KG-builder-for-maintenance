(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  const closeButton = `
    <button type="button" class="kg-btn kg-btn-quiet kg-btn-small kg-inspector-close" data-kg-inspector-close>
      Chiudi dettaglio
    </button>`;

  const empty = (title, text) => `
    <div class="kg-inspector-empty">
      <strong>${escapeHtml(title)}</strong>
      <p>${escapeHtml(text)}</p>
    </div>`;

  root.renderInspector = () => empty("Nessun dettaglio", "Seleziona un elemento per vederne il contenuto.");
  root.bindInspector = () => {};

  const typeSwatch = (nodeType, label) => `
    <span class="kg-inspector-kind" style="--node-type: var(--node-${escapeHtml(nodeType)})">
      <i aria-hidden="true"></i>${escapeHtml(label)}
    </span>`;

  /** Block 2 — the review never disappears from view: nothing here is final. */
  const reviewBlock = (source) => {
    const label = root.sourceStateLabels[source.state] || source.state;
    const tone = source.state === "approved" ? "success" : source.state === "rejected" ? "danger" : "warning";
    const explanation = {
      reviewing: "Il grafo di questa fonte è in verifica. Non è unito ad altre fonti e non è pubblicato.",
      approved: "Hai verificato questa fonte. Resta separata dalle altre finché non decidi tu.",
      rejected: "Hai segnalato questa fonte da correggere.",
      ready: "Il grafo di questa fonte non è ancora stato costruito.",
      waiting: "Conferma prima la struttura dei dati di questa fonte.",
      deferred: "Questa fonte è stata rimandata a una fase successiva.",
    }[source.state] || "";
    return `
      <section class="kg-block">
        <h3>Stato della verifica</h3>
        <span class="kg-badge kg-badge-${tone}"><span class="kg-badge-dot" aria-hidden="true"></span>${escapeHtml(label)}</span>
        <p class="kg-secondary">${escapeHtml(explanation)}</p>
      </section>`;
  };

  /** Block 3 — every relation row navigates to the element at the other end. */
  const relationsBlock = (model, nodeId) => {
    const relations = model.relationsByNode.get(nodeId) || [];
    if (!relations.length) {
      return `<section class="kg-block"><h3>Collegamenti</h3><p class="kg-block-empty">Nessun collegamento dimostrato da questa fonte.</p></section>`;
    }
    const grouped = new Map();
    relations.forEach((relation) => {
      const outgoing = relation.from_id === nodeId;
      const otherId = outgoing ? relation.to_id : relation.from_id;
      const other = model.nodesById.get(otherId);
      if (!other) return;
      const label = root.relationTypeLabels[relation.relation_type] || relation.relation_type;
      const key = `${label}|${outgoing ? "out" : "in"}`;
      if (!grouped.has(key)) grouped.set(key, { label, outgoing, items: [] });
      grouped.get(key).items.push({ relation, other });
    });
    const groups = [...grouped.values()].map((group) => `
      <div class="kg-relation-group">
        <span>${escapeHtml(group.outgoing ? group.label : `${group.label} (in entrata)`)}</span>
        ${group.items.map(({ relation, other }) => `
          <button type="button" class="kg-relation" data-kg-select="node" data-kg-id="${escapeHtml(other.node_id)}"
            style="--node-type: var(--node-${escapeHtml(other.node_type)})">
            <i aria-hidden="true"></i>
            <span>${escapeHtml(other.label)}</span>
            <span class="kg-relation-direction">${escapeHtml(root.nodeTypeLabels[other.node_type])} · ${root.plural(relation.evidence_ids.length, "riga", "righe")}</span>
          </button>`).join("")}
      </div>`).join("");
    return `<section class="kg-block"><h3>Collegamenti <span class="kg-caption">${relations.length}</span></h3>${groups}</section>`;
  };

  /** Block 4 — how many distinct rows were consolidated into this claim. */
  const occurrencesBlock = (count, singular, plural) => `
    <section class="kg-block">
      <h3>Occorrenze consolidate</h3>
      <p class="kg-occurrences"><strong>${count}</strong> <span>${escapeHtml(count === 1 ? singular : plural)}</span></p>
    </section>`;

  /** Block 5 — the way back to the original row, always. */
  const evidenceBlock = (model, evidenceIds, heading) => {
    const items = (evidenceIds || []).map((id) => model.evidenceById.get(id)).filter(Boolean);
    if (!items.length) {
      return `<section class="kg-block"><h3>${escapeHtml(heading)}</h3><p class="kg-block-empty">Nessuna riga collegata.</p></section>`;
    }
    return `
      <section class="kg-block">
        <h3>${escapeHtml(heading)} <span class="kg-caption">${items.length}</span></h3>
        ${items.map((item) => `
          <button type="button" class="kg-evidence" data-kg-select="evidence" data-kg-id="${escapeHtml(item.evidence_id)}"
            aria-selected="${state.selection.kind === "evidence" && state.selection.id === item.evidence_id}">
            <span class="kg-evidence-where">${escapeHtml(root.locatorSummary(item.locator))}</span>
            <span class="kg-evidence-text">${escapeHtml(item.excerpt || "Riga senza testo leggibile")}</span>
          </button>`).join("")}
      </section>`;
  };

  /** Block 6 — the two blocking classes, told apart and never merged. */
  const blockersBlock = (model, gaps, defects) => {
    if (!gaps.length && !defects.length) {
      return `<section class="kg-block"><h3>Cosa manca</h3><p class="kg-block-empty">Niente blocca questo elemento.</p></section>`;
    }
    const gapItems = gaps.map((gap) => `
      <div class="kg-note kg-note-warning">
        <span class="kg-note-mark" aria-hidden="true">?</span>
        <strong>${escapeHtml(root.gapTitle(gap.code))}</strong>
        <span>${escapeHtml(gap.message)}</span>
      </div>`).join("");
    const defectItems = defects.map((issue) => `
      <div class="kg-note kg-note-danger">
        <span class="kg-note-mark" aria-hidden="true">!</span>
        <strong>${escapeHtml(root.defectTitle(issue.code))}</strong>
        <span>${escapeHtml(issue.message)}</span>
      </div>`).join("");
    return `
      <section class="kg-block">
        <h3>Cosa manca</h3>
        ${gaps.length ? `<p class="kg-secondary">I dati sono validi ma non dichiarano questa informazione.</p>${gapItems}` : ""}
        ${defects.length ? `<p class="kg-secondary">Controlli tecnici non superati sulla struttura dati.</p>${defectItems}` : ""}
      </section>`;
  };

  /* ── Whole-source overview, shown when nothing is selected ─────────── */
  const sourceOverview = (source, model) => {
    const subgraph = source.subgraph;
    const consolidated = subgraph.duplicate_nodes_consolidated + subgraph.duplicate_relations_consolidated;
    const counts = root.nodeTypeOrder
      .map((type) => ({ type, total: subgraph.nodes.filter((node) => node.node_type === type).length }))
      .filter((entry) => entry.total);
    return `
      <div class="kg-inspector-inner">
        ${closeButton}
        <div class="kg-inspector-identity">
          <span class="kg-inspector-kind">Fonte</span>
          <h2>${escapeHtml(source.source_name)}</h2>
        </div>
        ${reviewBlock(source)}
        <section class="kg-block">
          <h3>Cosa è stato costruito</h3>
          ${counts.map((entry) => `
            <button type="button" class="kg-relation" data-kg-filter-type="${entry.type}"
              style="--node-type: var(--node-${entry.type})">
              <i aria-hidden="true"></i>
              <span>${escapeHtml(root.nodeTypePlural[entry.type])}</span>
              <span class="kg-relation-direction kg-tnum">${entry.total}</span>
            </button>`).join("")}
        </section>
        <section class="kg-block">
          <h3>Cosa è stato letto</h3>
          <p class="kg-secondary">${escapeHtml(`${root.plural(subgraph.evidence.length, "riga letta", "righe lette")} · ${root.plural(subgraph.relations.length, "collegamento", "collegamenti")}`)}</p>
          ${consolidated
            ? `<p class="kg-secondary">${escapeHtml(root.plural(consolidated, "ripetizione unita", "ripetizioni unite"))} in elementi già presenti. Nessuna riga è stata scartata.</p>`
            : ""}
        </section>
        ${blockersBlock(model, subgraph.knowledge_gaps || [], ((subgraph.validation || {}).issues || []))}
      </div>`;
  };

  /* ── Entry point for the graph phase ───────────────────────────────── */
  root.renderGraphInspector = function renderGraphInspector(source, model) {
    if (!source || !source.subgraph) {
      return empty("Nessun grafo", "Costruisci il grafo di questa fonte per esplorarlo.");
    }
    const selection = state.selection;

    if (selection.kind === "node") {
      const node = model.nodesById.get(selection.id);
      if (!node) return sourceOverview(source, model);
      return `
        <div class="kg-inspector-inner">
          ${closeButton}
          <div class="kg-inspector-identity">
            ${typeSwatch(node.node_type, root.nodeTypeLabels[node.node_type] || node.node_type)}
            <h2>${escapeHtml(node.label)}</h2>
          </div>
          ${reviewBlock(source)}
          ${relationsBlock(model, node.node_id)}
          ${occurrencesBlock(node.evidence_ids.length, "riga di questa fonte lo dichiara", "righe di questa fonte lo dichiarano")}
          ${evidenceBlock(model, node.evidence_ids, "Righe di origine")}
          ${blockersBlock(model, model.gapsByNode.get(node.node_id) || [], model.defectsByNode.get(node.node_id) || [])}
        </div>`;
    }

    if (selection.kind === "relation") {
      const relation = source.subgraph.relations.find((item) => item.relation_id === selection.id);
      if (!relation) return sourceOverview(source, model);
      const from = model.nodesById.get(relation.from_id);
      const to = model.nodesById.get(relation.to_id);
      const label = root.relationTypeLabels[relation.relation_type] || relation.relation_type;
      return `
        <div class="kg-inspector-inner">
          ${closeButton}
          <div class="kg-inspector-identity">
            <span class="kg-inspector-kind">Collegamento</span>
            <h2>${escapeHtml(label)}</h2>
          </div>
          ${reviewBlock(source)}
          <section class="kg-block">
            <h3>Fra quali elementi</h3>
            ${[from, to].filter(Boolean).map((node, index) => `
              <button type="button" class="kg-relation" data-kg-select="node" data-kg-id="${escapeHtml(node.node_id)}"
                style="--node-type: var(--node-${escapeHtml(node.node_type)})">
                <i aria-hidden="true"></i>
                <span>${escapeHtml(node.label)}</span>
                <span class="kg-relation-direction">${escapeHtml(index === 0 ? "da" : "a")}</span>
              </button>`).join("")}
          </section>
          ${occurrencesBlock(relation.evidence_ids.length, "riga lo dimostra", "righe lo dimostrano")}
          ${evidenceBlock(model, relation.evidence_ids, "Righe di origine")}
        </div>`;
    }

    if (selection.kind === "evidence") {
      const evidence = model.evidenceById.get(selection.id);
      if (!evidence) return sourceOverview(source, model);
      const produced = source.subgraph.nodes.filter((node) => node.evidence_ids.includes(evidence.evidence_id));
      const gaps = model.gapsByEvidence.get(evidence.evidence_id) || [];
      return `
        <div class="kg-inspector-inner">
          ${closeButton}
          <div class="kg-inspector-identity">
            <span class="kg-inspector-kind">Riga di origine</span>
            <h2>${escapeHtml(root.locatorSummary(evidence.locator))}</h2>
          </div>
          ${reviewBlock(source)}
          <section class="kg-block">
            <h3>Testo letto</h3>
            <p class="kg-evidence-text">${escapeHtml(evidence.excerpt || "Riga senza testo leggibile")}</p>
          </section>
          <section class="kg-block">
            <h3>Ha prodotto <span class="kg-caption">${produced.length}</span></h3>
            ${produced.length
              ? produced.map((node) => `
                <button type="button" class="kg-relation" data-kg-select="node" data-kg-id="${escapeHtml(node.node_id)}"
                  style="--node-type: var(--node-${escapeHtml(node.node_type)})">
                  <i aria-hidden="true"></i>
                  <span>${escapeHtml(node.label)}</span>
                  <span class="kg-relation-direction">${escapeHtml(root.nodeTypeLabels[node.node_type])}</span>
                </button>`).join("")
              : `<p class="kg-block-empty">Questa riga non ha prodotto nessun elemento.</p>`}
          </section>
          ${blockersBlock(model, gaps, [])}
          <details class="kg-disclosure">
            <summary>Dati tecnici della riga</summary>
            <pre class="kg-evidence-raw">${escapeHtml(JSON.stringify(evidence.locator, null, 2))}</pre>
          </details>
        </div>`;
    }

    return sourceOverview(source, model);
  };

  root.bindGraphInspector = function bindGraphInspector(container) {
    root.delegate(container, "click", "[data-kg-select]", (element) => {
      root.applySelection(element.dataset.kgSelect, element.dataset.kgId);
    });
    root.delegate(container, "click", "[data-kg-filter-type]", (element) => {
      state.filters.nodeType = element.dataset.kgFilterType;
      state.view = "graph";
      root.render({ regions: ["work", "inspector"] });
    });
  };
})();
