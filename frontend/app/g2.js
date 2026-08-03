(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;

  const escapeHtml = (value) => String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);

  const roleLabels = {
    observation: "Sintomo / osservazione",
    cause: "Causa / diagnosi",
    action: "Azione eseguita",
    component: "Componente",
    error_code: "Codice errore",
    occurred_at: "Data e ora",
    outcome: "Esito",
    measurement: "Misura",
    attribute: "Altro dato",
    excluded: "Non usare questa colonna",
  };

  const graphRoles = [
    ["component", "Componenti"],
    ["observation", "Sintomi e osservazioni"],
    ["cause", "Cause possibili"],
    ["action", "Azioni correttive"],
    ["error_code", "Codici errore"],
  ];
  const tableRoles = [
    ["occurred_at", "Data"],
    ["component", "Componente"],
    ["observation", "Sintomo / osservazione"],
    ["cause", "Causa / diagnosi"],
    ["action", "Azione"],
    ["error_code", "Codice errore"],
    ["outcome", "Esito"],
  ];

  const languageSummary = (profile) => {
    const counts = (profile.summary || {}).language_counts || {};
    const labels = {
      qualified_en: "EN pronta",
      unqualified_it: "IT conservata",
      unqualified_de: "DE conservata",
      mixed: "lingua mista conservata",
      unknown: "lingua da identificare",
    };
    const items = Object.entries(counts)
      .filter(([, count]) => Number(count) > 0)
      .map(([qualification, count]) => `${count} ${labels[qualification] || qualification}`);
    return items.length
      ? `<small class="g2-language-summary"><b>Lingue:</b> ${items.map(escapeHtml).join(" · ")}</small>`
      : "";
  };

  const columnsForRole = (mapping, role) => Object.entries(mapping)
    .filter(([, config]) => config.included && config.role === role)
    .map(([column]) => column);

  const rowValueForRole = (row, mapping, role) => columnsForRole(mapping, role)
    .map((column) => row[column])
    .filter((value) => value != null && String(value).trim() !== "")
    .map(String)
    .join(" · ");

  const graphMappingPreview = (profile) => {
    const allMappings = (profile.mapping || {}).structures || {};
    const items = graphRoles.map(([role, label]) => {
      const columns = [...new Set(Object.values(allMappings).flatMap((mapping) => columnsForRole(mapping, role)))];
      return { role, label, columns };
    }).filter((item) => item.columns.length);
    if (!items.length) return "";
    return `
      <section class="g2-graph-mapping" aria-label="Come i dati alimenteranno il grafo">
        <header>
          <div><strong>Come entreranno nel grafo</strong><span>Ogni riga diventa un’evidenza collegata al file originale.</span></div>
          <span class="g2-next-step">Grafo nel prossimo passo</span>
        </header>
        <div class="g2-graph-role-list">
          ${items.map((item) => `<div class="g2-graph-role"><b>${escapeHtml(item.label)}</b><small>${item.columns.map(escapeHtml).join(" + ")}</small></div>`).join("")}
        </div>
        <p>Qui controlli il significato delle colonne. I collegamenti tra questi elementi verranno proposti durante l’elaborazione successiva.</p>
      </section>`;
  };

  const tablePreview = (profile) => {
    const structure = (profile.structures || []).find((item) => item.included && (item.preview || []).length);
    if (!structure) return "";
    const mapping = (((profile.mapping || {}).structures || {})[structure.structure_id]) || {};
    const columns = tableRoles.filter(([role]) => columnsForRole(mapping, role).length);
    if (!columns.length) return "";
    const rows = structure.preview.slice(0, 5);
    return `
      <section class="g2-table-preview">
        <header><div><strong>Anteprima della tabella</strong><span>Prime ${rows.length} righe di ${structure.row_count}</span></div></header>
        <div class="g2-table-scroll">
          <table class="g2-data-table">
            <thead><tr>${columns.map(([, label]) => `<th>${escapeHtml(label)}</th>`).join("")}</tr></thead>
            <tbody>${rows.map((row) => `<tr>${columns.map(([role]) => {
              const value = rowValueForRole(row, mapping, role);
              return `<td title="${escapeHtml(value)}">${escapeHtml(value || "—")}</td>`;
            }).join("")}</tr>`).join("")}</tbody>
          </table>
        </div>
      </section>`;
  };

  root.loadG2 = async function loadG2(start) {
    if (!state.workspace) return;
    state.g2Loading = true;
    state.g2Error = "";
    try {
      const workspaceId = state.workspace.workspace.workspace_id;
      state.g2 = await root.api(`/api/workspaces/${encodeURIComponent(workspaceId)}/g2/preparation`, {
        method: start ? "POST" : "GET",
      });
    } catch (error) {
      state.g2Error = error.message;
    } finally {
      state.g2Loading = false;
    }
  };

  const sourceCard = (source, profile) => {
    if (source.source_kind === "pdf") {
      return `
        <article class="g2-source-card is-ready">
          <span class="source-file-type">PDF</span>
          <div><strong>${escapeHtml(source.file_name)}</strong><small>Documento controllato e pronto</small></div>
          <span class="pill g2-ready-pill">Pronto</span>
        </article>`;
    }
    if (!profile) return "";
    const ready = profile.state === "prepared";
    const count = Number(profile.summary.record_count || 0);
    const evidence = Number(profile.summary.evidence_count || 0);
    const isolated = Number(profile.summary.isolated_record_count || 0);
    const preview = ((profile.structures || [])[0] || {}).preview || [];
    const notices = (state.g2.exceptions || []).filter((item) => item.profile_id === profile.profile_id && item.severity === "warning");
    const status = profile.confirmed ? "Confermata" : ready ? "Pronta" : "Da decidere";
    return `
      <article class="g2-source-card ${ready ? "is-ready" : "is-attention"}">
        <span class="source-file-type">${escapeHtml(source.source_kind.toUpperCase())}</span>
        <div>
          <strong>${escapeHtml(profile.source_name)}</strong>
          <small>${count} ${count === 1 ? "record letto" : "record letti"}${ready ? ` · ${evidence} preparati` : " · preparazione in pausa"}${isolated ? ` · ${isolated} isolati` : ""}</small>
          ${languageSummary(profile)}
          ${isolated && notices.length ? `<p class="g2-isolation-note"><b>${isolated} ${isolated === 1 ? "riga isolata" : "righe isolate"}:</b> ${escapeHtml(notices[0].title)}. Le altre righe continuano normalmente.</p>` : ""}
          ${tablePreview(profile)}
          ${graphMappingPreview(profile)}
          ${notices.length ? `<details class="g2-preview"><summary>${notices.length === 1 ? "1 avviso gestito" : `${notices.length} avvisi gestiti`}</summary>${notices.map((item) => `<p><b>${escapeHtml(item.title)}</b><br>${escapeHtml(item.explanation)}</p>`).join("")}</details>` : ""}
          ${preview.length ? `<details class="g2-preview"><summary>Dettagli tecnici dei dati letti</summary><pre>${escapeHtml(JSON.stringify(preview.slice(0, 3), null, 2))}</pre></details>` : ""}
        </div>
        <div class="g2-source-status">
          <span class="pill ${ready ? "g2-ready-pill" : "g2-attention-pill"}">${status}</span>
          ${ready && !profile.confirmed ? `<button class="btn-primary g2-source-confirm" type="button" data-g2-confirm-profile="${escapeHtml(profile.profile_id)}" aria-label="Conferma fonte ${escapeHtml(profile.source_name)}" ${state.g2Busy ? "disabled" : ""}>Conferma</button>` : ""}
        </div>
      </article>`;
  };

  const exceptionPanel = (issue) => {
    if (!issue) return "";
    const payload = issue.payload || {};
    if (issue.exception_kind === "mapping_ambiguous") {
      const choices = payload.choices || Object.keys(roleLabels);
      return `
        <form class="g2-decision" data-g2-exception="${escapeHtml(issue.exception_id)}">
          <p class="kicker">Serve una sola scelta</p>
          <h2>${escapeHtml(issue.title)}</h2>
          <p>${escapeHtml(issue.explanation)}</p>
          ${payload.examples && payload.examples.length ? `<div class="g2-examples"><b>Esempi</b>${payload.examples.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div>` : ""}
          <label>Che informazione contiene?
            <select name="role" required>
              <option value="">Scegli…</option>
              ${choices.map((role) => `<option value="${escapeHtml(role)}">${escapeHtml(roleLabels[role] || role)}</option>`).join("")}
            </select>
          </label>
          <button class="btn-primary" type="submit" ${state.g2Busy ? "disabled" : ""}>Salva e continua</button>
        </form>`;
    }
    if (issue.exception_kind === "hidden_sheet") {
      return `
        <section class="g2-decision" data-g2-exception="${escapeHtml(issue.exception_id)}">
          <p class="kicker">Serve una sola scelta</p>
          <h2>${escapeHtml(issue.title)}</h2>
          <p>${escapeHtml(issue.explanation)}</p>
          <div class="g2-actions">
            <button class="btn-primary" type="button" data-g2-include="false" ${state.g2Busy ? "disabled" : ""}>Lascialo escluso</button>
            <button class="btn-ghost" type="button" data-g2-include="true" ${state.g2Busy ? "disabled" : ""}>Includi il foglio</button>
          </div>
        </section>`;
    }
    if (issue.severity === "warning") {
      return `
        <section class="g2-decision" data-g2-exception="${escapeHtml(issue.exception_id)}">
          <p class="kicker">Dato isolato automaticamente</p>
          <h2>${escapeHtml(issue.title)}</h2>
          <p>${escapeHtml(issue.explanation)}</p>
          <button class="btn-primary" type="button" data-g2-acknowledge ${state.g2Busy ? "disabled" : ""}>Ho capito, continua</button>
        </section>`;
    }
    return `
      <section class="g2-decision is-blocking">
        <p class="kicker">Il file va sostituito</p>
        <h2>${escapeHtml(issue.title)}</h2>
        <p>${escapeHtml(issue.explanation)}</p>
        <a class="btn-ghost" href="/console.html?foundation=1&amp;workspace_id=${encodeURIComponent(state.workspace.workspace.workspace_id)}">Torna ai documenti</a>
      </section>`;
  };

  const joinPanel = (join) => {
    if (!join) return "";
    const profiles = state.g2.profiles || [];
    const primary = profiles.find((item) => item.profile_id === join.primary_profile_id);
    const lookup = profiles.find((item) => item.profile_id === join.lookup_profile_id);
    return `
      <section class="g2-decision" data-g2-join="${escapeHtml(join.join_spec_id)}">
        <p class="kicker">Possibile collegamento trovato</p>
        <h2>Collegare questi due file?</h2>
        <p>“${escapeHtml(primary && primary.source_name)}” contiene il codice <b>${escapeHtml(join.spec.primary_key)}</b>, presente anche in “${escapeHtml(lookup && lookup.source_name)}”.</p>
        <div class="g2-join-summary">
          <span><b>${escapeHtml(join.preview.matched_records)}</b> record collegati</span>
          <span><b>${escapeHtml(join.preview.unmatched_records)}</b> record mantenuti senza collegamento</span>
        </div>
        <p class="g2-safe-note">I record senza corrispondenza restano sempre disponibili; non vengono duplicati.</p>
        <div class="g2-actions">
          <button class="btn-primary" type="button" data-g2-join-action="approve" ${state.g2Busy ? "disabled" : ""}>Collega i file</button>
          <button class="btn-ghost" type="button" data-g2-join-action="reject" ${state.g2Busy ? "disabled" : ""}>Tienili separati</button>
        </div>
      </section>`;
  };

  root.renderG2 = function renderG2() {
    if (!state.workspace || state.g2Loading) {
      return '<main class="foundation-main"><section class="foundation-card g2-loading"><strong>Preparo i dati…</strong><p>Inventario record, colonne e provenienza senza modificare i file originali.</p></section></main>';
    }
    if (state.g2Error || !state.g2) {
      return `
        <main class="foundation-main"><section class="foundation-card">
          <p class="foundation-error" role="alert">${escapeHtml(state.g2Error || "Preparazione non disponibile")}</p>
          <button class="btn-primary" type="button" data-g2-retry>Riprova</button>
        </section></main>`;
    }
    const openIssue = (state.g2.exceptions || []).find((item) => item.status === "open");
    const proposedJoin = (state.g2.joins || []).find((item) => item.status === "proposed");
    const sources = (state.sources || []).filter((item) => item.source_kind !== "operator_input");
    const cards = sources.map((source) => sourceCard(
      source,
      (state.g2.profiles || []).find((profile) => profile.source_id === source.source_id)
    )).join("");
    const ready = state.g2.can_complete;
    const pendingConfirmations = Math.max(
      0,
      Number(state.g2.counts.structured_sources || 0) - Number(state.g2.counts.confirmed_sources || 0)
    );
    return `
      <main class="foundation-main">
        <section class="foundation-card g2-card">
          <div class="foundation-step-heading">
            <span class="foundation-step-number ${state.g2.completed ? "is-complete" : ""}">${state.g2.completed ? "✓" : "4"}</span>
            <div>
              <p class="kicker">Passo 4 · Struttura dei dati</p>
              <h1>${state.g2.completed ? "Struttura dati confermata" : ready ? "Controlla come verranno usati i dati" : "Completa la struttura dei dati"}</h1>
              <p>${ready
                ? "Il sistema ha letto le tabelle e propone come trasformare le colonne in elementi utili per il grafo. Controlla l’anteprima e conferma."
                : "Il sistema interpreta tutto automaticamente e ti chiede soltanto le scelte che non può fare in modo affidabile."}</p>
            </div>
            <span class="pill ${ready ? "g2-ready-pill" : "g2-attention-pill"}">${state.g2.completed ? "Confermato" : ready ? `${pendingConfirmations} ${pendingConfirmations === 1 ? "fonte da confermare" : "fonti da confermare"}` : "1 scelta"}</span>
          </div>
          <div class="g2-source-list">${cards}</div>
          ${exceptionPanel(openIssue)}
          ${!openIssue ? joinPanel(proposedJoin) : ""}
          ${state.g2.completed ? `<section class="g2-complete"><div><strong>Le fonti sono pronte per l’elaborazione</strong><span>Nel prossimo passo controllerai un grafo separato per ogni fonte.</span></div><a class="btn-primary" href="/console.html?foundation=1&amp;workspace_id=${encodeURIComponent(state.workspace.workspace.workspace_id)}&amp;stage=g3">Continua all’elaborazione</a></section>` : ""}
          <a class="g2-back" href="/console.html?foundation=1&amp;workspace_id=${encodeURIComponent(state.workspace.workspace.workspace_id)}">← Torna ai documenti</a>
          ${state.g2Error ? `<p class="foundation-error" role="alert">${escapeHtml(state.g2Error)}</p>` : ""}
        </section>
      </main>`;
  };

  root.bindG2 = function bindG2(render) {
    const run = async (action) => {
      state.g2Busy = true;
      state.g2Error = "";
      render();
      try {
        state.g2 = await action();
      } catch (error) {
        state.g2Error = error.message;
      } finally {
        state.g2Busy = false;
        render();
      }
    };
    document.querySelector("[data-g2-retry]")?.addEventListener("click", () => run(async () => {
      await root.loadG2(true);
      if (!state.g2) throw new Error(state.g2Error || "Preparazione non disponibile");
      return state.g2;
    }));
    document.querySelector("[data-g2-exception]")?.addEventListener("submit", (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const role = new FormData(form).get("role");
      run(() => root.api(`/api/g2/exceptions/${encodeURIComponent(form.dataset.g2Exception)}/resolve`, {
        method: "POST", body: { role },
      }));
    });
    document.querySelectorAll("[data-g2-include]").forEach((button) => button.addEventListener("click", () => {
      const panel = button.closest("[data-g2-exception]");
      run(() => root.api(`/api/g2/exceptions/${encodeURIComponent(panel.dataset.g2Exception)}/resolve`, {
        method: "POST", body: { included: button.dataset.g2Include === "true", acknowledge: true },
      }));
    }));
    document.querySelector("[data-g2-acknowledge]")?.addEventListener("click", (event) => {
      const panel = event.currentTarget.closest("[data-g2-exception]");
      run(() => root.api(`/api/g2/exceptions/${encodeURIComponent(panel.dataset.g2Exception)}/resolve`, {
        method: "POST", body: { acknowledge: true },
      }));
    });
    document.querySelectorAll("[data-g2-join-action]").forEach((button) => button.addEventListener("click", () => {
      const panel = button.closest("[data-g2-join]");
      run(() => root.api(`/api/g2/joins/${encodeURIComponent(panel.dataset.g2Join)}/decision`, {
        method: "POST", body: { action: button.dataset.g2JoinAction },
      }));
    }));
    document.querySelectorAll("[data-g2-confirm-profile]").forEach((button) => button.addEventListener("click", () => {
      run(() => root.api(`/api/g2/profiles/${encodeURIComponent(button.dataset.g2ConfirmProfile)}/confirm`, {
        method: "POST",
      }));
    }));
  };
})();
