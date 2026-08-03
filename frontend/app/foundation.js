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
    const initialParameters = new URL(window.location.href).searchParams;
    root.state.stage = ["g2", "g3"].includes(initialParameters.get("stage"))
      ? initialParameters.get("stage") : "documents";
    function render(options = {}) {
      const currentMain = app.querySelector(".foundation-main");
      const previousScrollTop = currentMain ? currentMain.scrollTop : 0;
      const hasWorkspace = Boolean(root.state.workspace);
      const fileSources = (root.state.sources || []).filter((source) => source.source_kind !== "operator_input");
      const acceptedSources = fileSources.filter((source) => source.status === "accepted");
      const documentsDone = acceptedSources.length > 0;
      const inG2 = root.state.stage === "g2";
      const inG3 = root.state.stage === "g3";
      const g2Done = inG3 || Boolean(root.state.g2 && root.state.g2.completed);
      const g3Done = Boolean(root.state.g3 && root.state.g3.merge_barrier.state === "ready");
      const flowStep = (number, title, done, current, locked = false) => `
        <div class="foundation-flow-step ${done ? "is-done" : ""} ${current ? "is-current" : ""} ${locked ? "is-locked" : ""}"
          data-flow-step="${number}" ${locked ? 'aria-disabled="true"' : ""}>
          <span>${done ? "✓" : locked ? "–" : number}</span><small>${title}</small>
        </div>`;
      app.innerHTML = `
        <header class="c-header">
          <a class="foundation-home-link" href="/home.html">← Workspace</a>
          <strong>Maintenance KG Builder</strong>
          <span class="pill foundation-pill">${inG3 ? "Elaborazione" : inG2 ? "Struttura dei dati" : "Caricamento documenti"}</span>
        </header>
        <nav class="foundation-flow" aria-label="Percorso di preparazione">
          ${flowStep(1, "Macchina", hasWorkspace, !hasWorkspace)}
          <i></i>
          ${flowStep(2, "Caricamento", documentsDone, hasWorkspace && !documentsDone && !inG2)}
          <i></i>
          ${flowStep(3, "Controllo file", documentsDone, false, !documentsDone)}
          <i></i>
          ${flowStep(4, "Struttura dati", g2Done, inG2, !documentsDone)}
          <i></i>
          ${flowStep(5, "Elaborazione", g3Done, inG3, !g2Done && !inG3)}
          <i></i>
          ${flowStep(6, "Revisione", false, false, !g3Done)}
        </nav>
        ${inG3 && root.renderG3 ? root.renderG3() : inG2 && root.renderG2 ? root.renderG2() : root.renderMachine()}`;
      if (inG3 && root.bindG3) {
        root.bindG3(render);
      } else if (inG2 && root.bindG2) {
        root.bindG2(render);
      } else {
        root.bindMachine(render);
        root.bindSources(render);
      }
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
      const parameters = new URL(window.location.href).searchParams;
      const workspaceId = parameters.get("workspace_id");
      root.state.creatingWorkspace = parameters.get("new") === "1";
      root.state.workspace = root.state.creatingWorkspace
        ? null
        : await root.api(
          workspaceId ? `/api/workspaces/${encodeURIComponent(workspaceId)}` : "/api/workspace"
        );
      await root.loadSources();
      if (root.state.stage === "g2" && root.loadG2) {
        await root.loadG2(true);
      } else if (root.state.stage === "g3" && root.loadG3) {
        await root.loadG3();
      }
    } catch (error) {
      root.state.error = error.message;
    } finally {
      root.state.loading = false;
      render();
    }
  };
})();
