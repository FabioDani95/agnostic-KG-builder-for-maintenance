(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  const NODE_WIDTH = 176;
  const NODE_HEIGHT = 40;
  const COLUMN_STRIDE = 268;
  const ROW_STRIDE = 56;
  const PADDING = 32;
  /* Above this many visible elements a layout stops being readable; we say so
     instead of drawing an unusable hairball and calling it a graph. */
  const CROWDED_AT = 140;

  const COLUMNS = {
    Asset: 0,
    Symptom: 1, ErrorCode: 1,
    FailureMode: 2,
    Component: 3, CorrectiveAction: 3,
  };
  const COLUMN_TITLES = ["Macchina", "Sintomi e codici errore", "Cause", "Componenti e azioni"];

  state.zoom = 1;

  /* ── Derived model ─────────────────────────────────────────────────── */

  /**
   * Build everything the three panes need from one subgraph, once per repaint:
   * the filtered element set, the indexes that make navigation instant, and the
   * gap/defect attributions that decide what blocks approval.
   */
  root.buildGraphModel = function buildGraphModel(subgraph, filters, selection) {
    const nodesById = new Map(subgraph.nodes.map((node) => [node.node_id, node]));
    const evidenceById = new Map(subgraph.evidence.map((item) => [item.evidence_id, item]));

    const degree = new Map();
    const relationsByNode = new Map();
    subgraph.relations.forEach((relation) => {
      [relation.from_id, relation.to_id].forEach((id) => {
        degree.set(id, (degree.get(id) || 0) + 1);
        if (!relationsByNode.has(id)) relationsByNode.set(id, []);
        relationsByNode.get(id).push(relation);
      });
    });

    /* A gap is attached to evidence; a node inherits the gaps of the rows that
       produced it, so "what blocks this node" is answerable from the node. */
    const gapsByNode = new Map();
    const gapsByEvidence = new Map();
    (subgraph.knowledge_gaps || []).forEach((gap) => {
      (gap.evidence_ids || []).forEach((evidenceId) => {
        if (!gapsByEvidence.has(evidenceId)) gapsByEvidence.set(evidenceId, []);
        gapsByEvidence.get(evidenceId).push(gap);
      });
    });
    subgraph.nodes.forEach((node) => {
      const gaps = [];
      node.evidence_ids.forEach((evidenceId) => {
        (gapsByEvidence.get(evidenceId) || []).forEach((gap) => {
          if (!gaps.includes(gap)) gaps.push(gap);
        });
      });
      if (gaps.length) gapsByNode.set(node.node_id, gaps);
    });

    const defectsByNode = new Map();
    ((subgraph.validation || {}).issues || []).forEach((issue) => {
      if (!issue.node_id) return;
      if (!defectsByNode.has(issue.node_id)) defectsByNode.set(issue.node_id, []);
      defectsByNode.get(issue.node_id).push(issue);
    });

    /* — Filters. They apply to every view at once, graph and tables alike. — */
    const query = String(filters.query || "").trim().toLocaleLowerCase();
    let visible = subgraph.nodes.filter((node) => {
      if (filters.nodeType !== "all" && node.node_type !== filters.nodeType) return false;
      if (filters.onlyGaps && !gapsByNode.has(node.node_id) && !defectsByNode.has(node.node_id)) return false;
      if (query && !node.label.toLocaleLowerCase().includes(query)) return false;
      return true;
    });

    if (filters.relationType !== "all") {
      const endpoints = new Set();
      subgraph.relations
        .filter((relation) => relation.relation_type === filters.relationType)
        .forEach((relation) => { endpoints.add(relation.from_id); endpoints.add(relation.to_id); });
      visible = visible.filter((node) => endpoints.has(node.node_id));
    }

    /* Focus keeps the selection and everything one step away from it. */
    if (filters.focus && selection.kind === "node" && nodesById.has(selection.id)) {
      const keep = new Set([selection.id]);
      (relationsByNode.get(selection.id) || []).forEach((relation) => {
        keep.add(relation.from_id); keep.add(relation.to_id);
      });
      visible = visible.filter((node) => keep.has(node.node_id));
    }

    const visibleIds = new Set(visible.map((node) => node.node_id));
    const relations = subgraph.relations.filter((relation) => (
      visibleIds.has(relation.from_id)
      && visibleIds.has(relation.to_id)
      && (filters.relationType === "all" || relation.relation_type === filters.relationType)
    ));

    return {
      subgraph,
      nodes: visible,
      relations,
      nodesById,
      evidenceById,
      relationsByNode,
      degree,
      gapsByNode,
      gapsByEvidence,
      defectsByNode,
      hiddenNodes: subgraph.nodes.length - visible.length,
      hiddenRelations: subgraph.relations.length - relations.length,
      crowded: visible.length + relations.length > CROWDED_AT,
    };
  };

  /* ── Layout ────────────────────────────────────────────────────────── */

  /**
   * Layered layout by ontological role, then two barycentre sweeps so edges
   * cross as little as the role order allows. Coordinates are independent of
   * the viewport: the canvas scrolls and zooms instead of squeezing rows.
   */
  const layout = (model) => {
    const columns = [[], [], [], []];
    model.nodes.forEach((node) => columns[COLUMNS[node.node_type] ?? 3].push(node));
    columns.forEach((column) => column.sort((a, b) => a.label.localeCompare(b.label, "it")));

    const order = new Map();
    const reindex = () => columns.forEach((column) => column.forEach((node, index) => order.set(node.node_id, index)));
    reindex();

    const barycentre = (node, direction) => {
      const neighbours = (model.relationsByNode.get(node.node_id) || [])
        .map((relation) => (relation.from_id === node.node_id ? relation.to_id : relation.from_id))
        .filter((id) => order.has(id))
        .filter((id) => {
          const other = model.nodesById.get(id);
          if (!other) return false;
          const delta = (COLUMNS[other.node_type] ?? 3) - (COLUMNS[node.node_type] ?? 3);
          return direction > 0 ? delta < 0 : delta > 0;
        });
      if (!neighbours.length) return order.get(node.node_id);
      return neighbours.reduce((total, id) => total + order.get(id), 0) / neighbours.length;
    };

    [1, -1, 1].forEach((direction) => {
      const sequence = direction > 0 ? [1, 2, 3] : [2, 1, 0];
      sequence.forEach((index) => {
        columns[index] = columns[index]
          .map((node) => ({ node, key: barycentre(node, direction) }))
          .sort((a, b) => a.key - b.key)
          .map((entry) => entry.node);
        reindex();
      });
    });

    const rows = Math.max(1, ...columns.map((column) => column.length));
    const positions = new Map();
    columns.forEach((column, columnIndex) => {
      const offset = (rows - column.length) / 2;
      column.forEach((node, index) => {
        positions.set(node.node_id, {
          x: PADDING + columnIndex * COLUMN_STRIDE,
          y: PADDING + 28 + (offset + index) * ROW_STRIDE,
          column: columnIndex,
        });
      });
    });

    return {
      positions,
      columns,
      width: PADDING * 2 + 3 * COLUMN_STRIDE + NODE_WIDTH,
      height: PADDING * 2 + 28 + rows * ROW_STRIDE,
    };
  };

  /* ── Rendering ─────────────────────────────────────────────────────── */

  const truncate = (label, limit) => (label.length > limit ? `${label.slice(0, limit - 1)}…` : label);

  const edgePath = (from, to) => {
    const x1 = from.x + NODE_WIDTH;
    const y1 = from.y + NODE_HEIGHT / 2;
    const x2 = to.x - 8;
    const y2 = to.y + NODE_HEIGHT / 2;
    const middle = (x1 + x2) / 2;
    return `M ${x1} ${y1} C ${middle} ${y1}, ${middle} ${y2}, ${x2} ${y2}`;
  };

  root.renderCanvas = function renderCanvas(model, selection) {
    if (!model.nodes.length) {
      return `
        <div class="kg-explorer">
          <div class="kg-work-pad">
            <div class="kg-empty">
              <strong>Nessun elemento con questi filtri</strong>
              <p>${model.subgraph.nodes.length
                ? "Il grafo contiene elementi, ma nessuno corrisponde ai filtri attivi."
                : "Questa fonte non ha prodotto nessun elemento."}</p>
              ${model.subgraph.nodes.length ? '<button type="button" class="kg-btn kg-btn-secondary" data-kg-clear-filters>Azzera i filtri</button>' : ""}
            </div>
          </div>
        </div>`;
    }

    const placed = layout(model);
    const zoom = state.zoom;

    const neighbourhood = new Set();
    if (selection.kind === "node") {
      neighbourhood.add(selection.id);
      (model.relationsByNode.get(selection.id) || []).forEach((relation) => {
        neighbourhood.add(relation.from_id); neighbourhood.add(relation.to_id);
      });
    } else if (selection.kind === "relation") {
      const relation = model.subgraph.relations.find((item) => item.relation_id === selection.id);
      if (relation) { neighbourhood.add(relation.from_id); neighbourhood.add(relation.to_id); }
    }
    const dimming = neighbourhood.size > 0;

    const edges = model.relations.map((relation) => {
      const from = placed.positions.get(relation.from_id);
      const to = placed.positions.get(relation.to_id);
      if (!from || !to) return "";
      const active = selection.kind === "relation"
        ? relation.relation_id === selection.id
        : dimming && neighbourhood.has(relation.from_id) && neighbourhood.has(relation.to_id);
      const dim = dimming && !active;
      const path = edgePath(from, to);
      const label = root.relationTypeLabels[relation.relation_type] || relation.relation_type;
      const fromLabel = (model.nodesById.get(relation.from_id) || {}).label || "";
      const toLabel = (model.nodesById.get(relation.to_id) || {}).label || "";
      return `<g class="${dim ? "kg-edge-dim" : ""}">
        <path class="kg-edge ${active ? "kg-edge-active" : ""}" d="${path}"
          marker-end="url(#kg-arrow${active ? "-active" : ""})"></path>
        <path class="kg-edge-hit" d="${path}" data-kg-relation="${escapeHtml(relation.relation_id)}" role="button"
          tabindex="-1" aria-label="${escapeHtml(`${fromLabel} ${label} ${toLabel}`)}"><title>${escapeHtml(`${fromLabel} — ${label} — ${toLabel}`)}</title></path>
      </g>`;
    }).join("");

    const focusableId = selection.kind === "node" && placed.positions.has(selection.id)
      ? selection.id
      : (placed.columns.flat()[0] || {}).node_id;

    const nodes = placed.columns.flat().map((node) => {
      const position = placed.positions.get(node.node_id);
      const selected = selection.kind === "node" && node.node_id === selection.id;
      const dim = dimming && !neighbourhood.has(node.node_id);
      const typeLabel = root.nodeTypeLabels[node.node_type] || node.node_type;
      const blocked = model.gapsByNode.has(node.node_id) || model.defectsByNode.has(node.node_id);
      const occurrences = node.evidence_ids.length;
      const description = `${typeLabel}: ${node.label}. ${root.plural(occurrences, "riga di origine", "righe di origine")}.`;
      return `
        <g class="kg-node ${selected ? "kg-node-selected" : ""} ${dim ? "kg-node-dim" : ""}"
          style="--node-type: var(--node-${escapeHtml(node.node_type)})"
          transform="translate(${position.x} ${position.y})"
          data-kg-node="${escapeHtml(node.node_id)}" role="button"
          tabindex="${node.node_id === focusableId ? "0" : "-1"}"
          aria-label="${escapeHtml(description)}" aria-pressed="${selected}">
          <rect class="kg-node-box" width="${NODE_WIDTH}" height="${NODE_HEIGHT}" rx="8"></rect>
          <rect class="kg-node-bar" x="1" y="1" width="3" height="${NODE_HEIGHT - 2}" rx="1.5"></rect>
          <text class="kg-node-label" x="14" y="18">${escapeHtml(truncate(node.label, 21))}</text>
          <text class="kg-node-type" x="14" y="31">${escapeHtml(typeLabel)}</text>
          ${blocked ? `<text class="kg-node-flag" x="${NODE_WIDTH - 12}" y="18" text-anchor="middle">!</text>` : ""}
          <title>${escapeHtml(node.label)}</title>
        </g>`;
    }).join("");

    const headers = COLUMN_TITLES.map((title, index) => (
      placed.columns[index].length
        ? `<text class="kg-node-type" x="${PADDING + index * COLUMN_STRIDE}" y="${PADDING - 6}">${escapeHtml(title)}</text>`
        : ""
    )).join("");

    const legend = root.nodeTypeOrder
      .filter((type) => model.nodes.some((node) => node.node_type === type))
      .map((type) => `<span style="--node-type: var(--node-${type})"><i aria-hidden="true"></i>${escapeHtml(root.nodeTypePlural[type])}</span>`)
      .join("");

    const notice = model.crowded
      ? `<div class="kg-canvas-overlay kg-note kg-note-info kg-floating" role="status">
          <span class="kg-note-mark" aria-hidden="true">i</span>
          <strong>Molti elementi in vista</strong>
          <span>${root.plural(model.nodes.length, "elemento", "elementi")} e ${root.plural(model.relations.length, "collegamento", "collegamenti")} insieme sono difficili da leggere. Seleziona un elemento e attiva “Solo l’intorno”, oppure filtra per tipo.</span>
        </div>`
      : "";

    return `
      <div class="kg-explorer">
        <div class="kg-canvas" data-kg-canvas tabindex="0" role="group"
          aria-label="Mappa del grafo: ${escapeHtml(`${model.nodes.length} elementi, ${model.relations.length} collegamenti`)}">
          <div class="kg-canvas-inner" style="width: ${placed.width * zoom}px; height: ${placed.height * zoom}px;">
            <svg width="${placed.width * zoom}" height="${placed.height * zoom}"
              viewBox="0 0 ${placed.width} ${placed.height}" aria-hidden="true" focusable="false">
              <defs>
                <marker id="kg-arrow" markerWidth="7" markerHeight="7" refX="6.5" refY="3.5" orient="auto">
                  <path class="kg-arrow" d="M0,0 L7,3.5 L0,7 z"></path>
                </marker>
                <marker id="kg-arrow-active" markerWidth="7" markerHeight="7" refX="6.5" refY="3.5" orient="auto">
                  <path class="kg-arrow kg-arrow-active" d="M0,0 L7,3.5 L0,7 z"></path>
                </marker>
              </defs>
              ${headers}${edges}${nodes}
            </svg>
          </div>
        </div>
        ${notice}
        ${legend ? `<div class="kg-legend kg-floating">${legend}</div>` : ""}
        <div class="kg-canvas-controls kg-floating">
          <button type="button" class="kg-btn kg-btn-quiet kg-btn-icon" data-kg-zoom="out" aria-label="Riduci">−</button>
          <span class="kg-canvas-zoom" aria-live="off">${Math.round(zoom * 100)}%</span>
          <button type="button" class="kg-btn kg-btn-quiet kg-btn-icon" data-kg-zoom="in" aria-label="Ingrandisci">+</button>
          <button type="button" class="kg-btn kg-btn-quiet kg-btn-small" data-kg-zoom="reset">Adatta</button>
        </div>
      </div>`;
  };

  /* ── Interaction ───────────────────────────────────────────────────── */

  /* Selecting repaints the canvas, which destroys the focused element. Remember
     that the operator was driving from the keyboard so focus can be handed back
     to the same node afterwards instead of falling to the document. */
  let keyboardDriven = false;

  root.bindCanvas = function bindCanvas(container, model, onSelect) {
    const canvas = container.querySelector("[data-kg-canvas]");
    if (!canvas) return;
    root.attachPan(canvas);

    canvas.addEventListener("pointerdown", () => { keyboardDriven = false; });
    canvas.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        keyboardDriven = true;
        onSelect("", "");
      }
    });

    canvas.addEventListener("click", (event) => {
      const node = event.target.closest("[data-kg-node]");
      if (node) { onSelect("node", node.dataset.kgNode); return; }
      const relation = event.target.closest("[data-kg-relation]");
      if (relation) onSelect("relation", relation.dataset.kgRelation);
    });

    /* Reading order for the keyboard: column by column, top to bottom. */
    const ordered = Array.from(canvas.querySelectorAll("[data-kg-node]"));
    const positionOf = (element) => {
      const transform = element.getAttribute("transform") || "";
      const match = transform.match(/translate\(([-\d.]+) ([-\d.]+)\)/);
      return match ? { x: Number(match[1]), y: Number(match[2]) } : { x: 0, y: 0 };
    };

    const move = (current, key) => {
      const here = positionOf(current);
      const candidates = ordered.filter((element) => element !== current).map((element) => ({
        element, ...positionOf(element),
      }));
      const pick = (filter, score) => candidates.filter(filter).sort((a, b) => score(a) - score(b))[0];
      if (key === "ArrowDown") return pick((item) => item.x === here.x && item.y > here.y, (item) => item.y);
      if (key === "ArrowUp") return pick((item) => item.x === here.x && item.y < here.y, (item) => -item.y);
      if (key === "ArrowRight") return pick((item) => item.x > here.x, (item) => (item.x - here.x) * 1000 + Math.abs(item.y - here.y));
      if (key === "ArrowLeft") return pick((item) => item.x < here.x, (item) => (here.x - item.x) * 1000 + Math.abs(item.y - here.y));
      if (key === "Home") return candidates.concat([{ element: current, ...here }]).sort((a, b) => a.x - b.x || a.y - b.y)[0];
      if (key === "End") return candidates.concat([{ element: current, ...here }]).sort((a, b) => b.x - a.x || b.y - a.y)[0];
      return null;
    };

    canvas.addEventListener("keydown", (event) => {
      const current = event.target.closest("[data-kg-node]");
      if (!current) return;
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        keyboardDriven = true;
        onSelect("node", current.dataset.kgNode);
        return;
      }
      if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      keyboardDriven = true;
      const next = move(current, event.key);
      if (!next) return;
      current.setAttribute("tabindex", "-1");
      next.element.setAttribute("tabindex", "0");
      next.element.focus();
      next.element.scrollIntoView({ block: "nearest", inline: "nearest" });
    });

    root.delegate(container, "click", "[data-kg-zoom]", (element) => {
      const action = element.dataset.kgZoom;
      const next = action === "in" ? state.zoom * 1.25 : action === "out" ? state.zoom / 1.25 : 1;
      state.zoom = Math.min(2, Math.max(0.4, Number(next.toFixed(3))));
      root.render({ regions: ["work"] });
    });
  };

  /**
   * Bring the selected element into view, and give focus back to it when the
   * operator is navigating by keyboard: a repaint must never drop them out of
   * the canvas.
   */
  root.revealSelection = function revealSelection(container) {
    if (!state.selection.id) {
      if (keyboardDriven) container.querySelector('[data-kg-node][tabindex="0"]')?.focus();
      return;
    }
    const target = container.querySelector(
      `[data-kg-node="${CSS.escape(state.selection.id)}"], [data-kg-relation="${CSS.escape(state.selection.id)}"]`
    );
    if (!target) return;
    if (target.scrollIntoView) target.scrollIntoView({ block: "nearest", inline: "nearest" });
    if (keyboardDriven && target.hasAttribute("data-kg-node")) target.focus();
  };
})();
