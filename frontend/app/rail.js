(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  /** Only real files are sources the operator navigates; operator assertions are not. */
  root.fileSources = () => (state.sources || []).filter((source) => source.source_kind !== "operator_input");

  /** The source every pane is currently describing. */
  root.activeSource = function activeSource() {
    const sources = root.fileSources();
    if (!sources.length) return null;
    return sources.find((item) => item.source_id === state.activeSourceId) || sources[0];
  };

  root.setActiveSource = function setActiveSource(sourceId) {
    if (state.activeSourceId === sourceId) return;
    state.activeSourceId = sourceId;
    root.clearSelection();
    state.rejectingSourceId = "";
    root.render({ regions: ["rail", "work", "inspector", "decision"] });
  };

  const stateBadge = (label, tone) => `
    <span class="kg-source-state">
      <span class="kg-badge kg-badge-${tone}"><span class="kg-badge-dot" aria-hidden="true"></span>${escapeHtml(label)}</span>
    </span>`;

  root.renderRail = function renderRail() {
    const sources = root.fileSources();
    const phase = root.phases[state.phase] || {};
    const active = root.activeSource();
    const items = sources.map((source) => {
      const current = active && active.source_id === source.source_id;
      const facts = phase.railFacts ? phase.railFacts(source) : "";
      return `
        <button type="button" class="kg-source" data-kg-source="${escapeHtml(source.source_id)}"
          aria-current="${current ? "true" : "false"}">
          <span class="kg-source-name">
            <span class="kg-source-kind">${escapeHtml(String(source.source_kind).toUpperCase())}</span>
            <span>${escapeHtml(source.file_name)}</span>
          </span>
          ${facts}
        </button>`;
    }).join("");

    const foot = phase.railFoot ? phase.railFoot() : "";
    return `
      <div class="kg-rail-head">
        <h2>Fonti · ${root.plural(sources.length, "file", "file")}</h2>
      </div>
      ${sources.length
        ? `<div class="kg-rail-list">${items}</div>`
        : `<p class="kg-rail-empty">Nessun file caricato. Aggiungine uno nella fase Documenti.</p>`}
      ${foot ? `<div class="kg-rail-foot">${foot}</div>` : ""}`;
  };

  root.bindRail = function bindRail(container) {
    root.delegate(container, "click", "[data-kg-source]", (element) => {
      root.setActiveSource(element.dataset.kgSource);
    });
    const phase = root.phases[state.phase] || {};
    if (phase.bindRail) phase.bindRail(container);
  };

  /** Shared fact row builders, so every phase says the same things the same way. */
  root.railFacts = function railFacts(parts, badge) {
    const facts = parts.filter(Boolean).map((part) => (
      `<span class="${part.tone ? `kg-fact-${part.tone}` : ""}">${escapeHtml(part.text)}</span>`
    )).join("");
    return `${facts ? `<span class="kg-source-facts">${facts}</span>` : ""}${badge || ""}`;
  };

  root.railBadge = stateBadge;
})();
