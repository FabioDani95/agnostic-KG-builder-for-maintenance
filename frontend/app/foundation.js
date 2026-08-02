(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  root.infoTip = function infoTip(id, label, explanation) {
    const safeId = escapeHtml(id);
    return `
      <span class="info-tip" tabindex="0" data-info-tip="${safeId}"
        aria-label="Informazioni su ${escapeHtml(label)}"
        aria-describedby="info-tip-${safeId}">
        <span class="info-tip-icon" aria-hidden="true">i</span>
        <span class="info-tip-popover" id="info-tip-${safeId}" role="tooltip">
          <strong>${escapeHtml(label)}</strong>
          <span>${escapeHtml(explanation)}</span>
        </span>
      </span>`;
  };

  root.shouldMount = function shouldMount() {
    return new URL(window.location.href).searchParams.get("foundation") === "1";
  };
  root.mount = async function mount(app) {
    app.classList.add("foundation-shell");
    function render(options = {}) {
      const currentMain = app.querySelector(".foundation-main");
      const previousScrollTop = currentMain ? currentMain.scrollTop : 0;
      const hasWorkspace = Boolean(root.state.workspace);
      const fileSources = (root.state.sources || []).filter((source) => source.source_kind !== "operator_input");
      const acceptedSources = fileSources.filter((source) => source.status === "accepted");
      const acceptedPdfs = acceptedSources.filter((source) => source.source_kind === "pdf");
      const acceptedStructured = acceptedSources.filter((source) => source.source_kind !== "pdf");
      const hasPendingSource = fileSources.some((source) => source.status === "quarantined");
      const documentsDone = acceptedSources.length > 0 && !hasPendingSource;
      const structuredOnlyDone = documentsDone
        && acceptedPdfs.length === 0
        && acceptedStructured.length > 0;
      const hasApprovedScope = Boolean(root.state.preview && root.state.preview.current_scope);
      const hasAccounting = Boolean(root.state.preview && root.state.preview.accounting);
      const flowStep = (number, title, done, current, locked = false) => `
        <div class="foundation-flow-step ${done ? "is-done" : ""} ${current ? "is-current" : ""} ${locked ? "is-locked" : ""}"
          data-flow-step="${number}" ${locked ? 'aria-disabled="true"' : ""}>
          <span>${done ? "✓" : locked ? "–" : number}</span><small>${title}</small>
        </div>`;
      const finalSteps = structuredOnlyDone
        ? `
          ${flowStep(3, "File pronto", true, false)}
          <i></i>
          ${flowStep(4, "Righe · G2", false, false, true)}`
        : `
          ${flowStep(3, "Pagine", hasApprovedScope, documentsDone && !hasApprovedScope)}
          <i></i>
          ${flowStep(4, "Controllo", false, hasAccounting)}`;
      app.innerHTML = `
        <header class="c-header">
          <strong>Maintenance KG Builder</strong>
          <span class="pill foundation-pill">Preparazione documenti · G1</span>
        </header>
        <nav class="foundation-flow" aria-label="Percorso di preparazione">
          ${flowStep(1, "Macchina", hasWorkspace, !hasWorkspace)}
          <i></i>
          ${flowStep(2, "Documenti", documentsDone, hasWorkspace && !documentsDone)}
          <i></i>
          ${finalSteps}
        </nav>
        ${root.renderMachine()}`;
      root.bindMachine(render);
      root.bindSources(render);
      root.bindPreparation(render);
      document.querySelectorAll(".info-tip").forEach((tip) => {
        tip.addEventListener("pointerdown", (event) => event.stopPropagation());
        tip.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
          tip.focus();
        });
      });
      const nextMain = app.querySelector(".foundation-main");
      const scrollTarget = options.scrollToId
        ? document.getElementById(options.scrollToId)
        : null;
      if (nextMain && scrollTarget) {
        const moveToTarget = () => {
          const mainRect = nextMain.getBoundingClientRect();
          const targetRect = scrollTarget.getBoundingClientRect();
          nextMain.scrollTop += targetRect.top - mainRect.top - 20;
          if (typeof scrollTarget.focus === "function") {
            scrollTarget.focus({ preventScroll: true });
          }
        };
        moveToTarget();
        window.requestAnimationFrame(moveToTarget);
      } else if (nextMain && previousScrollTop > 0) {
        const restoreScroll = () => {
          nextMain.scrollTop = Math.min(
            previousScrollTop,
            Math.max(0, nextMain.scrollHeight - nextMain.clientHeight)
          );
        };
        restoreScroll();
        window.requestAnimationFrame(restoreScroll);
      }
    }
    render();
    try {
      root.state.workspace = await root.api("/api/workspace");
      await root.loadSources();
    } catch (error) {
      root.state.error = error.message;
    } finally {
      root.state.loading = false;
      render();
    }
  };
})();
