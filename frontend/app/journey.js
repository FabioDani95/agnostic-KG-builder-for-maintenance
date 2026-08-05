(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const esc = root.escapeHtml;
  const t = root.t;

  const wsId = () => state.workspace && state.workspace.workspace.workspace_id;
  const contextKey = () => `kg.workspace-context.${wsId() || "new"}`;

  root.journeyPhase = (id) => (
    state.journey && state.journey.phases.find((item) => item.phase === id)
  ) || null;

  root.journeySource = (sourceId) => (
    state.journey && state.journey.sources.find((item) => item.source_id === sourceId)
  ) || null;

  root.loadJourney = async function loadJourney() {
    if (!wsId()) { state.journey = null; return null; }
    state.journeyLoading = true;
    state.journeyError = "";
    try {
      state.journey = await root.api(`/api/workspaces/${encodeURIComponent(wsId())}/journey`);
      return state.journey;
    } catch (error) {
      state.journeyError = error.message;
      throw error;
    } finally {
      state.journeyLoading = false;
    }
  };

  root.rememberWorkspaceContext = function rememberWorkspaceContext() {
    if (!wsId()) return;
    localStorage.setItem(contextKey(), JSON.stringify({
      phase: state.phase,
      sourceId: state.activeSourceId || "",
      view: state.view,
    }));
  };

  const savedContext = () => {
    try { return JSON.parse(localStorage.getItem(contextKey()) || "null"); }
    catch (_) { return null; }
  };

  const activeSourceIds = () => new Set(
    ((state.journey && state.journey.sources) || [])
      .filter((item) => item.lifecycle === "active")
      .map((item) => item.source_id)
  );

  root.resolveWorkspaceContext = function resolveWorkspaceContext(params) {
    if (!state.journey) return;
    const options = params || {};
    const ids = activeSourceIds();
    const action = state.journey.next_action;
    const saved = savedContext();
    const explicitSource = options.sourceId && ids.has(options.sourceId) ? options.sourceId : "";
    const actionNeedsWork = action && action.code !== "workspace_ready";
    const savedSource = saved && ids.has(saved.sourceId) ? saved.sourceId : "";

    if (explicitSource) state.activeSourceId = explicitSource;
    else if (actionNeedsWork && action.source_id && ids.has(action.source_id)) state.activeSourceId = action.source_id;
    else if (savedSource) state.activeSourceId = savedSource;
    else if (!ids.has(state.activeSourceId)) state.activeSourceId = ids.values().next().value || "";

    const recommended = action && root.journeyPhase(action.phase);
    const requested = root.journeyPhase(state.phase);
    if (options.explicitPhase && requested && !requested.available) {
      state.phase = recommended && recommended.available ? action.phase : "machine";
    } else if (!options.explicitPhase) {
      const savedPhase = saved && root.journeyPhase(saved.phase);
      if (actionNeedsWork && recommended && recommended.available) state.phase = action.phase;
      else if (savedPhase && savedPhase.available) state.phase = saved.phase;
      else if (recommended && recommended.available) state.phase = action.phase;
    }
  };

  root.refreshWorkspaceContext = async function refreshWorkspaceContext(options) {
    if (!wsId()) return;
    const settings = options || {};
    await root.caricaFonti();
    await root.loadJourney();
    if (root.phases.graph && root.phases.graph.carica) await root.phases.graph.carica();
    const ids = activeSourceIds();
    if (settings.preferredSourceId && ids.has(settings.preferredSourceId)) {
      state.activeSourceId = settings.preferredSourceId;
    } else if (!ids.has(state.activeSourceId)) {
      const recommended = state.journey.next_action.source_id;
      state.activeSourceId = ids.has(recommended) ? recommended : (ids.values().next().value || "");
    }
    root.rememberWorkspaceContext();
    if (root.syncWorkspaceUrl) root.syncWorkspaceUrl();
  };

  root.followJourneyAction = function followJourneyAction() {
    const action = state.journey && state.journey.next_action;
    if (!action) return;
    if (action.source_id) state.activeSourceId = action.source_id;
    root.vaiAllaFase(action.phase);
  };

  root.journeyActionText = function journeyActionText(action) {
    if (!action) return "";
    return t(`journey.action.${action.code}`, { f: action.source_name || "" });
  };

  root.renderJourney = function renderJourney() {
    if (!state.workspace || !state.journey) return "";
    const workspace = state.workspace.workspace;
    const source = root.fonteAttiva && root.fonteAttiva();
    const phase = root.journeyPhase(state.phase);
    const action = state.journey.next_action;
    const actionIsHere = action.phase === state.phase
      && (!action.source_id || action.source_id === (source && source.source_id));
    const stateLabel = t(`journey.state.${(phase && phase.state) || "available"}`);
    return `
      <div class="journey-context" aria-label="${esc(t("journey.position"))}">
        <div class="journey-path">
          <span>${esc(workspace.asset.name)}</span><i aria-hidden="true">›</i>
          <strong>${esc(t(`fase.${state.phase}`))}</strong>
          ${source && state.phase !== "machine" ? `<i aria-hidden="true">›</i><span class="journey-source" title="${esc(source.file_name)}">${esc(source.file_name)}</span>` : ""}
        </div>
        <div class="journey-next">
          <span class="journey-state state-${esc((phase && phase.state) || "available")}"><i aria-hidden="true"></i>${esc(stateLabel)}</span>
          <span class="journey-next-copy"><b>${esc(actionIsHere ? t("journey.here") : t("journey.next"))}</b> ${esc(root.journeyActionText(action))}</span>
          ${action.code !== "workspace_ready" && !actionIsHere ? `<button type="button" class="btn quieto piccolo" data-follow-journey>${esc(t("journey.go"))}</button>` : ""}
        </div>
      </div>`;
  };
})();
