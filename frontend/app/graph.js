(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  let searchTimer = 0;

  const workspaceId = () => state.workspace.workspace.workspace_id;
  const sourceView = () => {
    if (!state.graph) return null;
    const active = root.activeSource();
    if (!active) return null;
    return state.graph.sources.find((item) => item.source_id === active.source_id) || null;
  };

  const modelFor = (view) => (
    view && view.subgraph ? root.buildGraphModel(view.subgraph, state.filters, state.selection) : null
  );

  const load = async () => {
    if (!state.workspace) return;
    state.graphLoading = true;
    state.graphError = "";
    try {
      state.graph = await root.api(`/api/workspaces/${encodeURIComponent(workspaceId())}/g3/subgraphs`);
    } catch (error) {
      state.graphError = error.message;
    } finally {
      state.graphLoading = false;
    }
  };

  const run = async (action) => {
    state.graphBusy = true;
    state.graphError = "";
    root.render({ regions: ["decision"] });
    try {
      state.graph = await action();
    } catch (error) {
      state.graphError = error.message;
    } finally {
      state.graphBusy = false;
      root.render();
    }
  };

  /* ── Views ─────────────────────────────────────────────────────────── */

  const VIEWS = [
    { id: "graph", label: "Mappa" },
    { id: "chains", label: "Catene diagnostiche" },
    { id: "nodes", label: "Elementi" },
    { id: "relations", label: "Collegamenti" },
    { id: "evidence", label: "Righe di origine" },
    { id: "blockers", label: "Cosa manca" },
  ];

  const toolbar = (model) => {
    const relationTypes = [...new Set(model.subgraph.relations.map((item) => item.relation_type))];
    const counts = {
      graph: null,
      chains: null,
      nodes: model.subgraph.nodes.length,
      relations: model.subgraph.relations.length,
      evidence: model.subgraph.evidence.length,
      blockers: (model.subgraph.knowledge_gaps || []).length + (((model.subgraph.validation || {}).issues) || []).length,
    };
    const tabs = VIEWS.map((view) => `
      <button type="button" data-kg-view="${view.id}" role="tab"
        aria-selected="${state.view === view.id}">${escapeHtml(view.label)}${counts[view.id] == null ? "" : ` ${counts[view.id]}`}</button>`).join("");

    return `
      <div class="kg-toolbar">
        <div class="kg-segment" role="tablist" aria-label="Come guardare questa fonte">${tabs}</div>
        <span class="kg-toolbar-spacer"></span>
        <div class="kg-toolbar-group">
          <label class="kg-visually-hidden" for="kg-search">Cerca un elemento</label>
          <input id="kg-search" class="kg-input kg-toolbar-search" type="search" data-kg-search
            placeholder="Cerca un elemento" value="${escapeHtml(state.filters.query)}">
          <label class="kg-visually-hidden" for="kg-type">Tipo di elemento</label>
          <select id="kg-type" class="kg-select kg-toolbar-select" data-kg-filter="nodeType">
            <option value="all">Tutti i tipi</option>
            ${root.nodeTypeOrder.map((type) => `<option value="${type}" ${state.filters.nodeType === type ? "selected" : ""}>${escapeHtml(root.nodeTypePlural[type])}</option>`).join("")}
          </select>
          <label class="kg-visually-hidden" for="kg-relation">Tipo di collegamento</label>
          <select id="kg-relation" class="kg-select kg-toolbar-select" data-kg-filter="relationType">
            <option value="all">Tutti i collegamenti</option>
            ${relationTypes.map((type) => `<option value="${type}" ${state.filters.relationType === type ? "selected" : ""}>${escapeHtml(root.relationTypeLabels[type] || type)}</option>`).join("")}
          </select>
          <label class="kg-toolbar-check">
            <input type="checkbox" data-kg-filter="onlyGaps" ${state.filters.onlyGaps ? "checked" : ""}>
            Solo con lacune
          </label>
          <label class="kg-toolbar-check">
            <input type="checkbox" data-kg-filter="focus" ${state.filters.focus ? "checked" : ""}>
            Solo l’intorno
          </label>
        </div>
      </div>`;
  };

  const filterSummary = (model) => (
    model.hiddenNodes || model.hiddenRelations
      ? `<p class="kg-secondary">${escapeHtml(`${root.plural(model.hiddenNodes, "elemento nascosto", "elementi nascosti")} dai filtri attivi.`)}
          <button type="button" class="kg-btn kg-btn-quiet kg-btn-small" data-kg-clear-filters>Azzera i filtri</button></p>`
      : ""
  );

  const nodesTable = (model) => `
    <div class="kg-work-pad">
      ${filterSummary(model)}
      <div class="kg-table-wrap">
        <table class="kg-table">
          <thead><tr>
            <th scope="col">Tipo</th><th scope="col">Elemento</th>
            <th scope="col" class="kg-num">Collegamenti</th>
            <th scope="col" class="kg-num">Righe di origine</th>
            <th scope="col">Stato</th>
          </tr></thead>
          <tbody>
            ${model.nodes.length ? model.nodes.map((node) => {
              const blocked = model.gapsByNode.has(node.node_id);
              const broken = model.defectsByNode.has(node.node_id);
              return `<tr data-selectable data-kg-select="node" data-kg-id="${escapeHtml(node.node_id)}"
                aria-selected="${state.selection.kind === "node" && state.selection.id === node.node_id}">
                <td><span class="kg-role" style="--node-type: var(--node-${escapeHtml(node.node_type)})"><i aria-hidden="true"></i>${escapeHtml(root.nodeTypeLabels[node.node_type])}</span></td>
                <td>${escapeHtml(node.label)}</td>
                <td class="kg-num">${model.degree.get(node.node_id) || 0}</td>
                <td class="kg-num">${node.evidence_ids.length}</td>
                <td>${broken
                  ? '<span class="kg-badge kg-badge-danger">Difetto tecnico</span>'
                  : blocked
                    ? '<span class="kg-badge kg-badge-warning">Lacuna</span>'
                    : '<span class="kg-badge">Completo</span>'}</td>
              </tr>`;
            }).join("") : `<tr><td colspan="5">Nessun elemento con questi filtri.</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>`;

  const relationsTable = (model) => `
    <div class="kg-work-pad">
      ${filterSummary(model)}
      <div class="kg-table-wrap">
        <table class="kg-table">
          <thead><tr>
            <th scope="col">Da</th><th scope="col">Collegamento</th><th scope="col">A</th>
            <th scope="col" class="kg-num">Righe di origine</th>
          </tr></thead>
          <tbody>
            ${model.relations.length ? model.relations.map((relation) => {
              const from = model.nodesById.get(relation.from_id);
              const to = model.nodesById.get(relation.to_id);
              return `<tr data-selectable data-kg-select="relation" data-kg-id="${escapeHtml(relation.relation_id)}"
                aria-selected="${state.selection.kind === "relation" && state.selection.id === relation.relation_id}">
                <td>${escapeHtml(from ? from.label : "—")}</td>
                <td><span class="kg-badge">${escapeHtml(root.relationTypeLabels[relation.relation_type] || relation.relation_type)}</span></td>
                <td>${escapeHtml(to ? to.label : "—")}</td>
                <td class="kg-num">${relation.evidence_ids.length}</td>
              </tr>`;
            }).join("") : `<tr><td colspan="4">Nessun collegamento con questi filtri.</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>`;

  const evidenceList = (model) => `
    <div class="kg-work-pad">
      <div class="kg-group-head">
        <h2>Ogni riga letta da questo file</h2>
        <p>Il grafo non contiene niente che non venga da una di queste righe. Selezionane una per vedere che cosa ha prodotto.</p>
      </div>
      <div class="kg-list" style="margin-top: var(--space-3)">
        ${model.subgraph.evidence.map((item) => {
          const gaps = model.gapsByEvidence.get(item.evidence_id) || [];
          return `<button type="button" class="kg-item" data-kg-select="evidence" data-kg-id="${escapeHtml(item.evidence_id)}"
            aria-selected="${state.selection.kind === "evidence" && state.selection.id === item.evidence_id}">
            <span class="kg-item-head">
              <strong>${escapeHtml(root.locatorSummary(item.locator))}</strong>
              ${gaps.length ? `<span class="kg-badge kg-badge-warning">${escapeHtml(root.plural(gaps.length, "lacuna", "lacune"))}</span>` : ""}
            </span>
            <span class="kg-item-text">${escapeHtml(item.excerpt || "Riga senza testo leggibile")}</span>
          </button>`;
        }).join("")}
      </div>
    </div>`;

  /** Diagnostic chains: one entry per cause, with everything the rows proved. */
  const chainsView = (model) => {
    const causes = model.subgraph.nodes.filter((node) => node.node_type === "FailureMode");
    if (!causes.length) {
      return `<div class="kg-work-pad"><div class="kg-empty">
        <strong>Nessuna catena diagnostica</strong>
        <p>Questa fonte non ha dichiarato nessuna causa, quindi non esiste ancora un percorso da un sintomo a un'azione.</p>
      </div></div>`;
    }
    const chip = (node, direction) => `
      <button type="button" class="kg-chain-step" data-kg-select="node" data-kg-id="${escapeHtml(node.node_id)}"
        style="--node-type: var(--node-${escapeHtml(node.node_type)})">
        <i aria-hidden="true"></i>${escapeHtml(node.label)}
      </button>${direction || ""}`;

    const entries = causes.map((cause) => {
      const related = model.relationsByNode.get(cause.node_id) || [];
      const pick = (type, side) => related
        .filter((relation) => relation.relation_type === type)
        .map((relation) => model.nodesById.get(side === "from" ? relation.from_id : relation.to_id))
        .filter(Boolean);
      const indicators = [...pick("MAY_INDICATE", "from"), ...pick("INDICATES", "from")];
      const actions = pick("RESOLVED_BY", "to");
      const components = pick("AFFECTS", "to");
      const missing = [];
      if (!indicators.length) missing.push("nessun sintomo o codice errore collegato");
      if (!actions.length) missing.push("nessuna azione correttiva collegata");
      return `
        <div class="kg-item" aria-selected="${state.selection.kind === "node" && state.selection.id === cause.node_id}">
          <div class="kg-chain">
            ${indicators.length ? indicators.map((node) => chip(node)).join('<span class="kg-chain-arrow" aria-hidden="true">→</span>') : '<span class="kg-chain-step">Origine non dichiarata</span>'}
            <span class="kg-chain-arrow" aria-hidden="true">→</span>
            ${chip(cause)}
            <span class="kg-chain-arrow" aria-hidden="true">→</span>
            ${actions.length ? actions.map((node) => chip(node)).join('<span class="kg-chain-arrow" aria-hidden="true">·</span>') : '<span class="kg-chain-step">Azione non dichiarata</span>'}
          </div>
          ${components.length ? `<span class="kg-item-meta">Interessa: ${components.map((node) => escapeHtml(node.label)).join(" · ")}</span>` : ""}
          ${missing.length ? `<span class="kg-item-meta">Catena incompleta: ${escapeHtml(missing.join(" e "))}.</span>` : ""}
        </div>`;
    }).join("");

    return `
      <div class="kg-work-pad">
        <div class="kg-group-head">
          <h2>Dal sintomo all'azione</h2>
          <p>Una catena per ogni causa dichiarata dai dati. Le catene incomplete non sono errori: i dati non dichiarano quel passaggio.</p>
        </div>
        <div class="kg-list" style="margin-top: var(--space-3)">${entries}</div>
      </div>`;
  };

  /** The two blocking classes, side by side but never mixed. */
  const blockersView = (model) => {
    const gaps = model.subgraph.knowledge_gaps || [];
    const defects = ((model.subgraph.validation || {}).issues) || [];
    if (!gaps.length && !defects.length) {
      return `<div class="kg-work-pad"><div class="kg-empty">
        <strong>Niente blocca questa fonte</strong>
        <p>Tutti i controlli tecnici sono superati e i dati non hanno lasciato informazioni indispensabili non dichiarate.</p>
      </div></div>`;
    }
    const gapGroup = gaps.length ? `
      <section class="kg-group">
        <div class="kg-group-head">
          <h2>Lacune nei dati · ${gaps.length}</h2>
          <p>I dati letti sono validi, ma non dichiarano queste informazioni. Il sistema non le inventa: restano lacune finché una fonte non le dichiara.</p>
        </div>
        <div class="kg-list">
          ${gaps.map((gap) => {
            const evidenceId = (gap.evidence_ids || [])[0];
            const evidence = evidenceId ? model.evidenceById.get(evidenceId) : null;
            return `<button type="button" class="kg-item" ${evidence ? `data-kg-select="evidence" data-kg-id="${escapeHtml(evidenceId)}"` : ""}>
              <span class="kg-item-head">
                <span class="kg-badge kg-badge-warning"><span class="kg-badge-dot" aria-hidden="true"></span>Lacuna</span>
                <strong>${escapeHtml(root.gapTitle(gap.code))}</strong>
              </span>
              <span class="kg-item-text">${escapeHtml(gap.message)}</span>
              ${evidence ? `<span class="kg-item-meta">${escapeHtml(root.locatorSummary(evidence.locator))}</span>` : ""}
            </button>`;
          }).join("")}
        </div>
      </section>` : "";

    const defectGroup = defects.length ? `
      <section class="kg-group">
        <div class="kg-group-head">
          <h2>Difetti tecnici · ${defects.length}</h2>
          <p>Il grafo costruito non rispetta la struttura dati concordata. Non è una lacuna dei dati: va corretto prima di procedere.</p>
        </div>
        <div class="kg-list">
          ${defects.map((issue) => `
            <button type="button" class="kg-item" ${issue.node_id ? `data-kg-select="node" data-kg-id="${escapeHtml(issue.node_id)}"` : ""}>
              <span class="kg-item-head">
                <span class="kg-badge kg-badge-danger"><span class="kg-badge-dot" aria-hidden="true"></span>Difetto tecnico</span>
                <strong>${escapeHtml(root.defectTitle(issue.code))}</strong>
              </span>
              <span class="kg-item-text">${escapeHtml(issue.message)}</span>
            </button>`).join("")}
        </div>
      </section>` : "";

    return `<div class="kg-work-pad">${gapGroup}${defectGroup}</div>`;
  };

  const comparisonView = () => {
    const barrier = state.graph.merge_barrier;
    const matches = barrier.exact_matches || [];
    const ready = barrier.state === "ready";
    return `
      <div class="kg-work-pad">
        <div class="kg-group-head">
          <h2>Confronto tra fonti</h2>
          <p>Niente viene unito automaticamente. Qui vedi soltanto dove due fonti usano esattamente la stessa parola: l'unione è una decisione umana successiva, e oggi non è ancora disponibile.</p>
        </div>
        <div class="kg-note ${ready ? "kg-note-info" : "kg-note-warning"}" style="margin-top: var(--space-3)">
          <span class="kg-note-mark" aria-hidden="true">${ready ? "i" : "?"}</span>
          <strong>${ready ? "Tutte le fonti incluse sono state verificate" : "Confronto non ancora disponibile"}</strong>
          <span>${ready
            ? escapeHtml(`${root.plural(matches.length, "corrispondenza esatta trovata", "corrispondenze esatte trovate")}. Nessun elemento è stato unito.`)
            : escapeHtml(`${root.plural(barrier.pending_source_ids.length, "fonte deve", "fonti devono")} ancora essere costruita e verificata.`)}</span>
        </div>
        ${matches.length ? `
          <div class="kg-list" style="margin-top: var(--space-4)">
            ${matches.map((match) => `
              <div class="kg-item">
                <span class="kg-item-head">
                  <span class="kg-role" style="--node-type: var(--node-${escapeHtml(match.node_type)})"><i aria-hidden="true"></i>${escapeHtml(root.nodeTypeLabels[match.node_type])}</span>
                  <strong>${escapeHtml(match.label)}</strong>
                </span>
                <span class="kg-item-meta">Presente in: ${match.occurrences.map((item) => escapeHtml(item.source_name)).join(" · ")}</span>
              </div>`).join("")}
          </div>` : ""}
        <p class="kg-secondary" style="margin-top: var(--space-4)">Le formulazioni equivalenti in lingue diverse restano elementi distinti: il sistema non traduce e non applica sinonimi.</p>
      </div>`;
  };

  const content = (view, model) => {
    if (state.view === "comparison") return comparisonView();
    if (!model) {
      return `<div class="kg-work-pad"><div class="kg-empty">
        <strong>Il grafo di questa fonte non è ancora stato costruito</strong>
        <p>Costruiscilo dalla barra in basso: il sistema legge le righe già preparate e propone elementi e collegamenti, senza inventarne.</p>
      </div></div>`;
    }
    if (state.view === "nodes") return nodesTable(model);
    if (state.view === "relations") return relationsTable(model);
    if (state.view === "evidence") return evidenceList(model);
    if (state.view === "blockers") return blockersView(model);
    if (state.view === "chains") return chainsView(model);
    return root.renderCanvas(model, state.selection);
  };

  /* ── Phase controller ──────────────────────────────────────────────── */

  const repaintContent = () => {
    const container = root.appElement.querySelector('[data-region="work-content"]');
    if (!container) { root.render({ regions: ["work"] }); return; }
    const view = sourceView();
    const model = modelFor(view);
    root.paint(container, content(view, model));
    if (model && state.view === "graph") {
      root.bindCanvas(container, model, (kind, id) => root.applySelection(kind, id));
      root.revealSelection(container);
    }
  };

  root.phases.graph = {
    label: "Grafo",
    showRail: true,
    showInspector: true,
    load,

    railFacts(source) {
      const view = state.graph && state.graph.sources.find((item) => item.source_id === source.source_id);
      if (!view) return root.railFacts([], root.railBadge("In preparazione", "warning"));
      const subgraph = view.subgraph;
      const parts = subgraph ? [
        { text: root.plural(subgraph.nodes.length, "elemento", "elementi") },
        { text: root.plural(subgraph.relations.length, "collegamento", "collegamenti") },
        (subgraph.knowledge_gaps || []).length
          ? { text: root.plural(subgraph.knowledge_gaps.length, "lacuna", "lacune"), tone: "blocking" } : null,
        (((subgraph.validation || {}).issues) || []).length
          ? { text: root.plural(subgraph.validation.issues.length, "difetto tecnico", "difetti tecnici"), tone: "broken" } : null,
      ] : [];
      const tone = view.state === "approved" ? "success" : view.state === "rejected" ? "danger" : "warning";
      return root.railFacts(parts, root.railBadge(root.sourceStateLabels[view.state] || view.state, tone));
    },

    railFoot() {
      if (!state.graph) return "";
      const barrier = state.graph.merge_barrier;
      const ready = barrier.state === "ready";
      return `
        <button type="button" class="kg-source" data-kg-comparison aria-current="${state.view === "comparison"}">
          <span class="kg-source-name"><span>Confronto tra fonti</span></span>
          <span class="kg-source-facts"><span>${ready
            ? escapeHtml(root.plural((barrier.exact_matches || []).length, "corrispondenza proposta", "corrispondenze proposte"))
            : "Non ancora disponibile"}</span></span>
        </button>`;
    },

    renderWork() {
      if (!state.workspace || state.graphLoading) {
        return `<div class="kg-state"><strong>Carico i grafi…</strong><p>Ogni fonte resta separata dalle altre.</p></div>`;
      }
      if (state.graphError && !state.graph) {
        return `
          <div class="kg-state">
            <strong>Non riesco a caricare i grafi</strong>
            <p role="alert">${escapeHtml(state.graphError)}</p>
            <button type="button" class="kg-btn kg-btn-primary" data-kg-retry>Riprova</button>
          </div>`;
      }
      if (!state.graph || !state.graph.sources.length) {
        return `<div class="kg-state"><strong>Nessuna fonte da elaborare</strong><p>Carica almeno un file e confermane la struttura.</p></div>`;
      }
      const view = sourceView();
      const model = modelFor(view);
      const heading = state.view === "comparison"
        ? { title: "Confronto tra fonti", text: "Nessuna unione automatica: qui vedi solo le coincidenze proposte." }
        : {
          title: view ? view.source_name : "Grafo",
          text: view && view.subgraph
            ? "Ogni elemento e ogni collegamento risale alle righe che lo dichiarano. Selezionane uno per vederle."
            : "Il grafo di questa fonte non è ancora stato costruito.",
        };
      return `
        <div class="kg-work-head">
          <div class="kg-work-head-row"><h1>${escapeHtml(heading.title)}</h1></div>
          <p>${escapeHtml(heading.text)}</p>
        </div>
        ${model && state.view !== "comparison" ? toolbar(model) : ""}
        <div class="kg-work-scroll" data-region="work-content">${content(view, model)}</div>`;
    },

    bindWork(container) {
      root.delegate(container, "click", "[data-kg-retry]", () => run(async () => {
        await load();
        if (!state.graph) throw new Error(state.graphError || "Elaborazione non disponibile");
        return state.graph;
      }));
      root.delegate(container, "click", "[data-kg-view]", (element) => {
        state.view = element.dataset.kgView;
        root.render({ regions: ["work"] });
      });
      root.delegate(container, "click", "[data-kg-select]", (element) => {
        root.applySelection(element.dataset.kgSelect, element.dataset.kgId);
      });
      root.delegate(container, "click", "[data-kg-clear-filters]", () => {
        state.filters = { query: "", nodeType: "all", relationType: "all", onlyGaps: false, focus: false };
        root.render({ regions: ["work"] });
      });
      root.delegate(container, "change", "[data-kg-filter]", (element) => {
        const key = element.dataset.kgFilter;
        state.filters[key] = element.type === "checkbox" ? element.checked : element.value;
        repaintContent();
      });
      const search = container.querySelector("[data-kg-search]");
      if (search) {
        search.addEventListener("input", () => {
          window.clearTimeout(searchTimer);
          searchTimer = window.setTimeout(() => {
            state.filters.query = search.value;
            repaintContent();
          }, 160);
        });
      }
    },

    afterWork(container) {
      const view = sourceView();
      const model = modelFor(view);
      const scroll = container.querySelector('[data-region="work-content"]');
      if (model && state.view === "graph" && scroll) {
        root.bindCanvas(scroll, model, (kind, id) => root.applySelection(kind, id));
        root.revealSelection(scroll);
      }
    },

    onSelectionChange: repaintContent,

    renderInspector() {
      if (state.view === "comparison") {
        return `<div class="kg-inspector-empty"><strong>Confronto tra fonti</strong><p>Le corrispondenze proposte non modificano nessun grafo.</p></div>`;
      }
      const view = sourceView();
      return root.renderGraphInspector(view, modelFor(view) || {
        nodesById: new Map(), evidenceById: new Map(), relationsByNode: new Map(),
        gapsByNode: new Map(), gapsByEvidence: new Map(), defectsByNode: new Map(),
      });
    },

    bindInspector(container) { root.bindGraphInspector(container); },

    renderDecision() {
      if (!state.graph || state.view === "comparison") return "";
      const view = sourceView();
      if (!view) return "";
      const subgraph = view.subgraph;
      const busy = state.graphBusy ? "disabled" : "";
      const guarantee = "Vale solo per questa fonte: non unisce le fonti e non pubblica niente.";
      const error = state.graphError
        ? `<p class="kg-field-error" role="alert">${escapeHtml(state.graphError)}</p>` : "";

      if (state.rejectingSourceId === view.source_id) {
        return `
          <form class="kg-decision-note" data-kg-reject-form>
            <label class="kg-field">
              <span>Che cosa deve essere corretto in questa fonte?</span>
              <textarea class="kg-textarea" name="note" required minlength="3"
                placeholder="Esempio: la colonna delle azioni contiene note libere, non azioni"></textarea>
            </label>
            <div class="kg-decision-note-actions">
              <button type="submit" class="kg-btn kg-btn-primary" ${busy}>Registra la segnalazione</button>
              <button type="button" class="kg-btn kg-btn-quiet" data-kg-reject-cancel>Annulla</button>
            </div>
            ${error}
          </form>`;
      }

      if (view.state === "waiting") {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>Struttura dei dati non ancora confermata</strong>
          <span>${escapeHtml(view.message)}</span>
        </div>
        <div class="kg-decision-actions"><button type="button" class="kg-btn kg-btn-secondary" data-kg-goto="structure">Vai alla struttura</button></div></div>`;
      }

      if (!subgraph) {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>Grafo non ancora costruito</strong>
          <span>Il sistema userà solo le righe già preparate di questa fonte.</span>
        </div>
        <div class="kg-decision-actions">
          <button type="button" class="kg-btn kg-btn-primary" data-kg-build ${busy}>${state.graphBusy ? "Costruisco…" : "Costruisci il grafo"}</button>
        </div></div>${error}`;
      }

      if (view.state === "approved") {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>Fonte verificata</strong><span>${escapeHtml(guarantee)}</span>
        </div></div>`;
      }
      if (view.state === "rejected") {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>Segnalata da correggere</strong>
          <span>${escapeHtml(subgraph.decision_note || "Segnalazione registrata.")}</span>
        </div></div>`;
      }

      const gaps = (subgraph.knowledge_gaps || []).length;
      const defects = (((subgraph.validation || {}).issues) || []).length;
      const blockers = `
        <div class="kg-decision-blockers">
          ${gaps ? `<button type="button" class="kg-decision-blocker kg-blocker-gap" data-kg-view="blockers">${escapeHtml(root.plural(gaps, "lacuna nei dati", "lacune nei dati"))}</button>` : ""}
          ${defects ? `<button type="button" class="kg-decision-blocker kg-blocker-defect" data-kg-view="blockers">${escapeHtml(root.plural(defects, "difetto tecnico", "difetti tecnici"))}</button>` : ""}
        </div>`;

      return `
        <div class="kg-decision-row">
          <div class="kg-decision-text" aria-live="polite">
            <strong>${subgraph.approval_eligible
              ? "Questo grafo rappresenta correttamente la fonte?"
              : "Non ancora verificabile"}</strong>
            <span>${subgraph.approval_eligible
              ? escapeHtml(guarantee)
              : "La verifica resta bloccata finché queste voci non sono risolte. È una protezione: nessun collegamento è stato inventato per riempirle."}</span>
          </div>
          ${subgraph.approval_eligible ? "" : blockers}
          <div class="kg-decision-actions">
            <button type="button" class="kg-btn kg-btn-danger" data-kg-reject ${busy}>Segnala da correggere</button>
            <button type="button" class="kg-btn kg-btn-primary" data-kg-approve
              ${subgraph.approval_eligible ? busy : "disabled"}>Conferma la verifica</button>
          </div>
        </div>
        ${error}`;
    },

    bindDecision(container) {
      root.delegate(container, "click", "[data-kg-build]", () => {
        const view = sourceView();
        run(() => root.api(
          `/api/workspaces/${encodeURIComponent(workspaceId())}/g3/sources/${encodeURIComponent(view.source_id)}/generate`,
          { method: "POST" }
        ));
      });
      root.delegate(container, "click", "[data-kg-approve]", () => {
        const view = sourceView();
        run(() => root.api(
          `/api/g3/subgraphs/${encodeURIComponent(view.subgraph.source_subgraph_revision_id)}/decision`,
          { method: "POST", body: { action: "approve", note: null } }
        ));
      });
      root.delegate(container, "click", "[data-kg-reject]", () => {
        state.rejectingSourceId = (sourceView() || {}).source_id || "";
        root.render({ regions: ["decision"] });
        container.querySelector("textarea")?.focus();
      });
      root.delegate(container, "click", "[data-kg-reject-cancel]", () => {
        state.rejectingSourceId = "";
        root.render({ regions: ["decision"] });
      });
      root.delegate(container, "click", "[data-kg-view]", (element) => {
        state.view = element.dataset.kgView;
        root.render({ regions: ["work"] });
      });
      root.delegate(container, "click", "[data-kg-goto]", (element) => root.goToPhase(element.dataset.kgGoto));
      root.delegate(container, "submit", "[data-kg-reject-form]", (form, event) => {
        event.preventDefault();
        const note = String(new FormData(form).get("note") || "").trim();
        if (!note) return;
        const view = sourceView();
        state.rejectingSourceId = "";
        run(() => root.api(
          `/api/g3/subgraphs/${encodeURIComponent(view.subgraph.source_subgraph_revision_id)}/decision`,
          { method: "POST", body: { action: "reject", note } }
        ));
      });
    },

    bindRail(container) {
      root.delegate(container, "click", "[data-kg-comparison]", () => {
        state.view = "comparison";
        root.clearSelection();
        root.render({ regions: ["rail", "work", "inspector", "decision"] });
      });
    },
  };
})();
