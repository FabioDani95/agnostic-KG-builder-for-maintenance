(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  /**
   * The four phases are named after the object the operator works on. The
   * internal development checkpoints are not part of this vocabulary and never
   * reach the screen or the address bar.
   */
  const PHASE_ORDER = ["machine", "documents", "structure", "graph"];
  const PHASE_SLUGS = { machine: "macchina", documents: "documenti", structure: "struttura", graph: "grafo" };
  const PHASE_BY_SLUG = Object.fromEntries(Object.entries(PHASE_SLUGS).map(([id, slug]) => [slug, id]));
  /* Links made before the phases were renamed keep working. */
  const LEGACY_STAGES = { g2: "structure", g3: "graph", documents: "documents" };

  root.phases = root.phases || {};
  root.PHASE_ORDER = PHASE_ORDER;

  const wideScreen = window.matchMedia("(min-width: 1181px)");

  root.phaseSlug = (id) => PHASE_SLUGS[id] || PHASE_SLUGS.machine;

  root.phaseHref = function phaseHref(id, workspaceId) {
    const target = workspaceId || (state.workspace && state.workspace.workspace.workspace_id) || "";
    const query = new URLSearchParams({ foundation: "1" });
    if (target) query.set("workspace_id", target);
    if (id && id !== "machine") query.set("fase", root.phaseSlug(id));
    return `/console.html?${query.toString()}`;
  };

  root.readPhaseFromUrl = function readPhaseFromUrl() {
    const parameters = new URL(window.location.href).searchParams;
    const slug = parameters.get("fase");
    if (slug && PHASE_BY_SLUG[slug]) return PHASE_BY_SLUG[slug];
    const legacy = parameters.get("stage");
    if (legacy && LEGACY_STAGES[legacy]) return LEGACY_STAGES[legacy];
    return "machine";
  };

  /* ── Phase availability ────────────────────────────────────────────── */
  const fileSources = () => (state.sources || []).filter((source) => source.source_kind !== "operator_input");

  root.phaseStatus = function phaseStatus(id) {
    const hasWorkspace = Boolean(state.workspace);
    const hasDocuments = fileSources().length > 0;
    /* When the structure phase has not been opened this session, the graph
       snapshot still says whether every source got past it. */
    const structureDone = state.structure
      ? Boolean(state.structure.completed)
      : Boolean(state.graph && state.graph.sources.length
        && state.graph.sources.every((item) => item.state !== "waiting"));
    if (id === "machine") return { available: true, done: hasWorkspace };
    if (id === "documents") return { available: hasWorkspace, done: hasDocuments };
    if (id === "structure") return { available: hasWorkspace && hasDocuments, done: structureDone };
    if (id === "graph") {
      const built = Boolean(state.graph && state.graph.sources.some((item) => item.subgraph));
      return { available: hasWorkspace && (structureDone || state.phase === "graph"), done: built };
    }
    return { available: false, done: false };
  };

  /* ── Frame ─────────────────────────────────────────────────────────── */
  const FRAME = `
    <a class="kg-visually-hidden" href="#kg-work">Vai al contenuto</a>
    <header class="kg-topbar kg-floating" data-region="topbar"></header>
    <div class="kg-body" data-region="body">
      <aside class="kg-rail" data-region="rail" aria-label="Fonti della macchina"></aside>
      <main class="kg-work" id="kg-work" data-region="work" tabindex="-1"></main>
      <aside class="kg-inspector" data-region="inspector" aria-label="Dettaglio"></aside>
    </div>
    <footer class="kg-decision kg-floating" data-region="decision"></footer>`;

  const region = (name) => root.appElement.querySelector(`[data-region="${name}"]`);

  const renderTopbar = () => {
    const workspace = state.workspace && state.workspace.workspace;
    const asset = workspace && workspace.asset;
    const identity = asset
      ? `<strong>${escapeHtml(asset.name)}</strong><span>${escapeHtml(asset.brand)} · ${escapeHtml(asset.model)}</span>`
      : `<strong>Nuova macchina</strong><span>Non ancora salvata</span>`;
    const steps = PHASE_ORDER.map((id, index) => {
      const status = root.phaseStatus(id);
      const current = state.phase === id;
      const label = root.phases[id] ? root.phases[id].label : id;
      const mark = status.done && !current ? "✓" : String(index + 1);
      const classes = ["kg-phase", status.done ? "kg-phase-done" : ""].filter(Boolean).join(" ");
      return `<button type="button" class="${classes}" data-kg-phase="${id}"
        ${current ? 'aria-current="step"' : ""}
        ${status.available ? "" : 'aria-disabled="true"'}>
        <span class="kg-phase-mark" aria-hidden="true">${mark}</span>${escapeHtml(label)}</button>`;
    }).join("");
    return `
      <a class="kg-topbar-back" href="/home.html">← Macchine</a>
      <div class="kg-topbar-identity">${identity}</div>
      <nav class="kg-phases" aria-label="Fasi di lavoro">${steps}</nav>`;
  };

  const activePhase = () => root.phases[state.phase] || root.phases.machine;

  /**
   * Repaint only the regions that changed. Selecting a node repaints the
   * inspector and the decision bar, never the graph the operator is looking at.
   */
  root.render = function render(options) {
    const settings = options || {};
    const regions = settings.regions || ["topbar", "rail", "work", "inspector", "decision"];
    const phase = activePhase();
    const body = region("body");

    if (regions.includes("topbar")) {
      root.paint(region("topbar"), renderTopbar());
      root.delegate(region("topbar"), "click", "[data-kg-phase]", (element) => {
        const id = element.dataset.kgPhase;
        if (element.getAttribute("aria-disabled") === "true" || id === state.phase) return;
        root.goToPhase(id);
      });
    }

    const showRail = Boolean(phase.showRail) && Boolean(state.workspace);
    const wantsInspector = Boolean(phase.showInspector) && Boolean(state.workspace);
    const showInspector = wantsInspector && (wideScreen.matches || Boolean(state.selection.id));
    body.dataset.rail = showRail ? "visible" : "hidden";
    body.dataset.inspector = showInspector ? "visible" : "hidden";

    if (regions.includes("rail") && showRail) {
      root.paint(region("rail"), root.renderRail());
      root.bindRail(region("rail"));
    } else if (!showRail) {
      root.paint(region("rail"), "");
    }

    if (regions.includes("work")) {
      const container = region("work");
      root.paint(container, phase.renderWork());
      if (phase.bindWork) phase.bindWork(container);
      if (phase.afterWork) phase.afterWork(container);
    }

    if (regions.includes("inspector")) {
      const container = region("inspector");
      if (!showInspector) {
        root.paint(container, "");
      } else {
        root.paint(container, phase.renderInspector ? phase.renderInspector() : root.renderInspector());
        root.delegate(container, "click", "[data-kg-inspector-close]", () => {
          root.clearSelection();
          root.render({ regions: ["work", "inspector", "decision"] });
        });
        if (phase.bindInspector) phase.bindInspector(container);
        else root.bindInspector(container);
      }
    }

    if (regions.includes("decision")) {
      const container = region("decision");
      const markup = phase.renderDecision ? phase.renderDecision() : "";
      container.hidden = !markup;
      root.paint(container, markup);
      if (markup && phase.bindDecision) phase.bindDecision(container);
    }
  };

  /**
   * Selecting is the most frequent action. A phase that can repaint just its
   * content does so, which keeps search boxes, scroll position and keyboard
   * focus exactly where the operator left them.
   */
  root.applySelection = function applySelection(kind, id) {
    root.select(kind, id);
    const phase = activePhase();
    if (phase.onSelectionChange) phase.onSelectionChange();
    else root.render({ regions: ["work"] });
    root.render({ regions: ["inspector", "decision"] });
  };

  root.goToPhase = async function goToPhase(id) {
    if (!root.phases[id]) return;
    state.phase = id;
    root.clearSelection();
    const workspaceId = state.workspace ? state.workspace.workspace.workspace_id : "";
    window.history.pushState({ phase: id }, "", root.phaseHref(id, workspaceId));
    root.render();
    if (root.phases[id].load) {
      await root.phases[id].load();
      root.render();
    }
  };

  root.shouldMount = function shouldMount() {
    return new URL(window.location.href).searchParams.get("foundation") === "1";
  };

  root.mount = async function mount(app) {
    root.appElement = app;
    app.className = "kg-app";
    app.innerHTML = FRAME;
    state.phase = root.readPhaseFromUrl();

    wideScreen.addEventListener("change", () => root.render({ regions: ["inspector"] }));
    window.addEventListener("popstate", () => {
      state.phase = root.readPhaseFromUrl();
      root.clearSelection();
      root.render();
      const phase = root.phases[state.phase];
      if (phase && phase.load) phase.load().then(() => root.render());
    });

    root.render();

    try {
      const parameters = new URL(window.location.href).searchParams;
      const workspaceId = parameters.get("workspace_id");
      state.creatingWorkspace = parameters.get("new") === "1";
      state.workspace = state.creatingWorkspace
        ? null
        : await root.api(workspaceId ? `/api/workspaces/${encodeURIComponent(workspaceId)}` : "/api/workspace");
      if (state.workspace) await root.loadSources();
      if (!state.workspace) state.phase = "machine";
      const phase = activePhase();
      if (phase.load) await phase.load();
    } catch (error) {
      state.error = error.message;
    } finally {
      state.loading = false;
      root.render();
    }
  };
})();
