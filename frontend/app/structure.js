(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const state = root.state;
  const escapeHtml = root.escapeHtml;

  const workspaceId = () => state.workspace.workspace.workspace_id;
  const profiles = () => (state.structure && state.structure.profiles) || [];
  const profileFor = (sourceId) => profiles().find((item) => item.source_id === sourceId) || null;
  const activeProfile = () => {
    const source = root.activeSource();
    return source ? profileFor(source.source_id) : null;
  };
  const openException = () => ((state.structure && state.structure.exceptions) || [])
    .find((item) => item.status === "open") || null;
  const proposedJoin = () => ((state.structure && state.structure.joins) || [])
    .find((item) => item.status === "proposed") || null;

  const load = async (start) => {
    if (!state.workspace) return;
    state.structureLoading = true;
    state.structureError = "";
    try {
      state.structure = await root.api(
        `/api/workspaces/${encodeURIComponent(workspaceId())}/g2/preparation`,
        { method: start === false ? "GET" : "POST" }
      );
    } catch (error) {
      state.structureError = error.message;
    } finally {
      state.structureLoading = false;
    }
  };

  const run = async (action) => {
    state.structureBusy = true;
    state.structureError = "";
    root.render({ regions: ["decision"] });
    try {
      state.structure = await action();
    } catch (error) {
      state.structureError = error.message;
    } finally {
      state.structureBusy = false;
      root.render();
    }
  };

  /* ── The one decision that needs a human, at the top of the pane ───── */

  const exceptionCard = (issue) => {
    const payload = issue.payload || {};
    const heading = `
      <h2>${escapeHtml(issue.title)}</h2>
      <p>${escapeHtml(issue.explanation)}</p>
      <p class="kg-secondary">Riguarda il file “${escapeHtml(issue.source_name)}”. È l'unica scelta aperta in questo momento.</p>`;

    if (issue.exception_kind === "mapping_ambiguous") {
      const choices = payload.choices || Object.keys(root.roleLabels);
      return `
        <form class="kg-decision-card" data-kg-exception="${escapeHtml(issue.exception_id)}">
          ${heading}
          ${(payload.examples || []).length
            ? `<div><p class="kg-caption">Valori trovati nella colonna</p><div class="kg-examples">${payload.examples.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</div></div>`
            : ""}
          <label class="kg-field" style="max-width: 24rem">
            <span>Che informazione contiene questa colonna?</span>
            <select class="kg-select" name="role" required>
              <option value="">Scegli…</option>
              ${choices.map((role) => `<option value="${escapeHtml(role)}">${escapeHtml(root.roleLabels[role] || role)}</option>`).join("")}
            </select>
          </label>
          <div class="kg-decision-card-actions">
            <button type="submit" class="kg-btn kg-btn-primary" ${state.structureBusy ? "disabled" : ""}>Salva e continua</button>
          </div>
        </form>`;
    }

    if (issue.exception_kind === "hidden_sheet") {
      return `
        <section class="kg-decision-card" data-kg-exception="${escapeHtml(issue.exception_id)}">
          ${heading}
          <div class="kg-decision-card-actions">
            <button type="button" class="kg-btn kg-btn-primary" data-kg-include="false" ${state.structureBusy ? "disabled" : ""}>Lascialo escluso</button>
            <button type="button" class="kg-btn kg-btn-secondary" data-kg-include="true" ${state.structureBusy ? "disabled" : ""}>Includi il foglio</button>
          </div>
        </section>`;
    }

    if (issue.severity === "warning") {
      return `
        <section class="kg-decision-card" data-kg-exception="${escapeHtml(issue.exception_id)}">
          ${heading}
          <div class="kg-decision-card-actions">
            <button type="button" class="kg-btn kg-btn-primary" data-kg-acknowledge ${state.structureBusy ? "disabled" : ""}>Ho capito, continua</button>
          </div>
        </section>`;
    }

    return `
      <section class="kg-decision-card">
        ${heading}
        <div class="kg-note kg-note-danger">
          <span class="kg-note-mark" aria-hidden="true">!</span>
          <strong>Questo file va sostituito</strong>
          <span>Non può essere letto in modo affidabile. Torna ai documenti, rimuovilo e caricane una versione corretta.</span>
        </div>
        <div class="kg-decision-card-actions">
          <button type="button" class="kg-btn kg-btn-secondary" data-kg-goto="documents">Vai ai documenti</button>
        </div>
      </section>`;
  };

  const joinCard = (join) => {
    const primary = profiles().find((item) => item.profile_id === join.primary_profile_id);
    const lookup = profiles().find((item) => item.profile_id === join.lookup_profile_id);
    return `
      <section class="kg-decision-card" data-kg-join="${escapeHtml(join.join_spec_id)}">
        <h2>Collegare questi due file?</h2>
        <p>“${escapeHtml(primary ? primary.source_name : "")}” contiene il codice <b>${escapeHtml(join.spec.primary_key)}</b>, presente anche in “${escapeHtml(lookup ? lookup.source_name : "")}”.</p>
        <div class="kg-examples">
          <span>${escapeHtml(root.plural(join.preview.matched_records, "record collegato", "record collegati"))}</span>
          <span>${escapeHtml(root.plural(join.preview.unmatched_records, "record senza corrispondenza", "record senza corrispondenza"))}</span>
        </div>
        <p class="kg-secondary">I record senza corrispondenza restano disponibili e non vengono duplicati.</p>
        <div class="kg-decision-card-actions">
          <button type="button" class="kg-btn kg-btn-primary" data-kg-join-action="approve" ${state.structureBusy ? "disabled" : ""}>Collega i file</button>
          <button type="button" class="kg-btn kg-btn-secondary" data-kg-join-action="reject" ${state.structureBusy ? "disabled" : ""}>Tienili separati</button>
        </div>
      </section>`;
  };

  /* ── Views on the active source ────────────────────────────────────── */

  const effectiveMapping = (profile, structureId) => (
    (((profile.mapping || {}).structures || {})[structureId]) || {}
  );

  const columnsView = (profile) => {
    const structures = (profile.structures || []).filter((item) => item.included);
    if (!structures.length) return `<div class="kg-work-pad"><div class="kg-empty"><strong>Nessuna tabella inclusa</strong><p>Questo file non contiene tabelle utilizzabili.</p></div></div>`;
    return `
      <div class="kg-work-pad">
        <div class="kg-group-head">
          <h2>Che cosa significa ogni colonna</h2>
          <p>Il significato decide che cosa entra nel grafo. Le colonne non usate restano nel file e restano consultabili, ma non generano elementi.</p>
        </div>
        ${structures.map((structure) => {
          const mapping = effectiveMapping(profile, structure.structure_id);
          return `
            <div style="margin-top: var(--space-4)">
              ${structures.length > 1 ? `<p class="kg-caption">${escapeHtml(structure.name)} · ${escapeHtml(root.plural(structure.row_count, "riga", "righe"))}</p>` : ""}
              <div class="kg-table-wrap">
                <table class="kg-table">
                  <thead><tr>
                    <th scope="col">Colonna nel file</th>
                    <th scope="col">Significato</th>
                    <th scope="col">Esempi</th>
                    <th scope="col" class="kg-num">Valori vuoti</th>
                  </tr></thead>
                  <tbody>
                    ${(structure.columns || []).map((column) => {
                      const configured = mapping[column.name];
                      const role = configured ? configured.role : column.proposed_role;
                      const used = configured ? configured.included : true;
                      const nodeType = root.roleNodeType[role];
                      return `<tr>
                        <td>${escapeHtml(column.name)}</td>
                        <td><span class="kg-role ${used && role !== "excluded" ? "" : "kg-role-excluded"}"
                          ${nodeType ? `style="--node-type: var(--node-${nodeType})"` : ""}>
                          ${nodeType ? '<i aria-hidden="true"></i>' : ""}${escapeHtml(used ? (root.roleLabels[role] || role) : "Non usata")}</span></td>
                        <td>${escapeHtml((column.examples || []).slice(0, 2).join(" · ") || "—")}</td>
                        <td class="kg-num">${Math.round(Number(column.null_rate || 0) * 100)}%</td>
                      </tr>`;
                    }).join("")}
                  </tbody>
                </table>
              </div>
            </div>`;
        }).join("")}
      </div>`;
  };

  const previewView = (profile) => {
    const structure = (profile.structures || []).find((item) => item.included && (item.preview || []).length);
    if (!structure) return `<div class="kg-work-pad"><div class="kg-empty"><strong>Nessuna anteprima</strong><p>Non ci sono righe leggibili da mostrare per questo file.</p></div></div>`;
    const mapping = effectiveMapping(profile, structure.structure_id);
    const columns = (structure.columns || []).map((column) => column.name);
    const rows = structure.preview.slice(0, 8);
    return `
      <div class="kg-work-pad">
        <div class="kg-group-head">
          <h2>Le righe come sono nel file</h2>
          <p>${escapeHtml(`Prime ${rows.length} righe di ${structure.row_count}. Nessun valore è stato modificato.`)}</p>
        </div>
        <div class="kg-table-wrap" style="margin-top: var(--space-3)">
          <table class="kg-table">
            <thead><tr>${columns.map((name) => {
              const configured = mapping[name];
              const role = configured ? configured.role : "attribute";
              const used = configured ? configured.included : true;
              return `<th scope="col">${escapeHtml(name)}<br><span class="kg-caption">${escapeHtml(used ? (root.roleLabels[role] || role) : "Non usata")}</span></th>`;
            }).join("")}</tr></thead>
            <tbody>${rows.map((row) => `<tr>${columns.map((name) => {
              const value = row[name];
              const text = value == null || String(value).trim() === "" ? "—" : String(value);
              return `<td title="${escapeHtml(text)}">${escapeHtml(text.length > 48 ? `${text.slice(0, 47)}…` : text)}</td>`;
            }).join("")}</tr>`).join("")}</tbody>
          </table>
        </div>
      </div>`;
  };

  const noticesView = (profile) => {
    const notices = ((state.structure.exceptions) || [])
      .filter((item) => item.profile_id === profile.profile_id && item.severity === "warning");
    const isolated = Number(profile.summary.isolated_record_count || 0);
    if (!notices.length && !isolated) {
      return `<div class="kg-work-pad"><div class="kg-empty"><strong>Nessun avviso</strong><p>Ogni riga di questo file è stata letta senza problemi.</p></div></div>`;
    }
    return `
      <div class="kg-work-pad">
        <div class="kg-group-head">
          <h2>Righe messe da parte</h2>
          <p>Queste righe non sono state cancellate: sono state isolate perché non erano leggibili in modo affidabile. Tutte le altre proseguono normalmente.</p>
        </div>
        <div class="kg-list" style="margin-top: var(--space-3)">
          ${notices.map((item) => `
            <div class="kg-note kg-note-warning">
              <span class="kg-note-mark" aria-hidden="true">?</span>
              <strong>${escapeHtml(item.title)}</strong>
              <span>${escapeHtml(item.explanation)}</span>
            </div>`).join("")}
        </div>
      </div>`;
  };

  const VIEWS = [
    { id: "columns", label: "Colonne" },
    { id: "preview", label: "Righe" },
    { id: "notices", label: "Avvisi" },
  ];

  const structureView = () => (VIEWS.some((item) => item.id === state.view) ? state.view : "columns");

  /* ── Phase controller ──────────────────────────────────────────────── */

  root.phases.structure = {
    label: "Struttura",
    showRail: true,
    showInspector: true,
    load: () => load(true),

    railFacts(source) {
      if (source.source_kind === "pdf") {
        return root.railFacts([{ text: "Documento pronto" }], root.railBadge("Pronta", "success"));
      }
      const profile = profileFor(source.source_id);
      if (!profile) return root.railFacts([], root.railBadge("In lettura", "warning"));
      const records = Number(profile.summary.record_count || 0);
      const isolated = Number(profile.summary.isolated_record_count || 0);
      const needsChoice = ((state.structure.exceptions) || [])
        .some((item) => item.profile_id === profile.profile_id && item.status === "open");
      const parts = [
        { text: root.plural(records, "riga letta", "righe lette") },
        isolated ? { text: root.plural(isolated, "riga isolata", "righe isolate"), tone: "blocking" } : null,
      ];
      const badge = needsChoice
        ? root.railBadge("Serve una scelta", "warning")
        : profile.confirmed
          ? root.railBadge("Confermata", "success")
          : root.railBadge(profile.state === "prepared" ? "Da confermare" : "In lettura", "warning");
      return root.railFacts(parts, badge);
    },

    renderWork() {
      if (!state.workspace || state.structureLoading) {
        return `<div class="kg-state"><strong>Leggo i file…</strong><p>Conto righe e colonne senza modificare gli originali.</p></div>`;
      }
      if (state.structureError && !state.structure) {
        return `
          <div class="kg-state">
            <strong>Non riesco a leggere i file</strong>
            <p role="alert">${escapeHtml(state.structureError)}</p>
            <button type="button" class="kg-btn kg-btn-primary" data-kg-retry>Riprova</button>
          </div>`;
      }
      if (!state.structure) return `<div class="kg-state"><strong>Nessun dato da leggere</strong><p>Carica almeno un file nella fase Documenti.</p></div>`;

      const issue = openException();
      const join = issue ? null : proposedJoin();
      const source = root.activeSource();
      const profile = activeProfile();
      const view = structureView();

      const focused = issue || join;
      const body = profile
        ? (view === "preview" ? previewView(profile) : view === "notices" ? noticesView(profile) : columnsView(profile))
        : `<div class="kg-work-pad"><div class="kg-empty">
            <strong>${escapeHtml(source && source.source_kind === "pdf" ? "Documento di testo" : "In lettura")}</strong>
            <p>${escapeHtml(source && source.source_kind === "pdf"
              ? "I documenti di testo non hanno colonne: ogni pagina è già stata preparata."
              : "Questo file non è ancora stato letto.")}</p>
          </div></div>`;

      return `
        <div class="kg-work-head">
          <div class="kg-work-head-row"><h1>${escapeHtml(source ? source.file_name : "Struttura dei dati")}</h1></div>
          <p>Controlla come sono state interpretate le colonne prima di costruire il grafo. Il sistema decide da solo quello che può decidere in modo affidabile e ti chiede solo il resto.</p>
        </div>
        ${profile ? `<div class="kg-toolbar"><div class="kg-segment" role="tablist" aria-label="Come guardare questo file">
          ${VIEWS.map((item) => `<button type="button" role="tab" data-kg-view="${item.id}" aria-selected="${view === item.id}">${escapeHtml(item.label)}</button>`).join("")}
        </div></div>` : ""}
        <div class="kg-work-scroll">
          ${focused ? `<div class="kg-work-pad" style="padding-bottom: 0">${issue ? exceptionCard(issue) : joinCard(join)}</div>` : ""}
          ${body}
        </div>`;
    },

    bindWork(container) {
      root.delegate(container, "click", "[data-kg-retry]", () => run(async () => {
        await load(true);
        if (!state.structure) throw new Error(state.structureError || "Preparazione non disponibile");
        return state.structure;
      }));
      root.delegate(container, "click", "[data-kg-view]", (element) => {
        state.view = element.dataset.kgView;
        root.render({ regions: ["work"] });
      });
      root.delegate(container, "click", "[data-kg-goto]", (element) => root.goToPhase(element.dataset.kgGoto));
      root.delegate(container, "submit", "[data-kg-exception]", (form, event) => {
        event.preventDefault();
        const role = new FormData(form).get("role");
        run(() => root.api(`/api/g2/exceptions/${encodeURIComponent(form.dataset.kgException)}/resolve`, {
          method: "POST", body: { role },
        }));
      });
      root.delegate(container, "click", "[data-kg-include]", (element) => {
        const panel = element.closest("[data-kg-exception]");
        run(() => root.api(`/api/g2/exceptions/${encodeURIComponent(panel.dataset.kgException)}/resolve`, {
          method: "POST", body: { included: element.dataset.kgInclude === "true", acknowledge: true },
        }));
      });
      root.delegate(container, "click", "[data-kg-acknowledge]", (element) => {
        const panel = element.closest("[data-kg-exception]");
        run(() => root.api(`/api/g2/exceptions/${encodeURIComponent(panel.dataset.kgException)}/resolve`, {
          method: "POST", body: { acknowledge: true },
        }));
      });
      root.delegate(container, "click", "[data-kg-join-action]", (element) => {
        const panel = element.closest("[data-kg-join]");
        run(() => root.api(`/api/g2/joins/${encodeURIComponent(panel.dataset.kgJoin)}/decision`, {
          method: "POST", body: { action: element.dataset.kgJoinAction },
        }));
      });
    },

    renderInspector() {
      const source = root.activeSource();
      const profile = activeProfile();
      if (!source) return `<div class="kg-inspector-empty"><strong>Nessuna fonte</strong><p>Carica un file per vederne la struttura.</p></div>`;
      if (!profile) {
        return `
          <div class="kg-inspector-inner">
            <div class="kg-inspector-identity">
              <span class="kg-inspector-kind">Fonte</span>
              <h2>${escapeHtml(source.file_name)}</h2>
            </div>
            <p class="kg-secondary">${escapeHtml(source.source_kind === "pdf"
              ? "Documento di testo: tutte le pagine sono già state preparate."
              : "In lettura.")}</p>
          </div>`;
      }
      const counts = profile.summary || {};
      const languages = counts.language_counts || {};
      const languageLabels = {
        qualified_en: "in inglese", unqualified_it: "in italiano", unqualified_de: "in tedesco",
        mixed: "in più lingue", unknown: "in lingua non riconosciuta",
      };
      const languageItems = Object.entries(languages).filter(([, total]) => Number(total) > 0);
      const roles = new Map();
      (profile.structures || []).filter((item) => item.included).forEach((structure) => {
        const mapping = effectiveMapping(profile, structure.structure_id);
        Object.entries(mapping).forEach(([column, config]) => {
          if (!config.included || !root.roleNodeType[config.role]) return;
          if (!roles.has(config.role)) roles.set(config.role, []);
          roles.get(config.role).push(column);
        });
      });
      return `
        <div class="kg-inspector-inner">
          <button type="button" class="kg-btn kg-btn-quiet kg-btn-small kg-inspector-close" data-kg-inspector-close>Chiudi dettaglio</button>
          <div class="kg-inspector-identity">
            <span class="kg-inspector-kind">Fonte</span>
            <h2>${escapeHtml(profile.source_name)}</h2>
          </div>
          <section class="kg-block">
            <h3>Cosa è stato letto</h3>
            <p class="kg-occurrences"><strong>${Number(counts.record_count || 0)}</strong> <span>${escapeHtml(Number(counts.record_count) === 1 ? "riga letta" : "righe lette")}</span></p>
            <p class="kg-secondary">${escapeHtml(`${root.plural(Number(counts.evidence_count || 0), "riga preparata", "righe preparate")}${Number(counts.isolated_record_count || 0) ? ` · ${root.plural(Number(counts.isolated_record_count), "riga isolata", "righe isolate")}` : ""}`)}</p>
          </section>
          ${languageItems.length ? `
            <section class="kg-block">
              <h3>Lingue trovate</h3>
              <p class="kg-secondary">${languageItems.map(([key, total]) => escapeHtml(`${total} ${languageLabels[key] || key}`)).join(" · ")}</p>
              ${languages.unknown ? `<p class="kg-secondary">Il testo originale resta comunque integro e consultabile.</p>` : ""}
            </section>` : ""}
          <section class="kg-block">
            <h3>Che cosa alimenterà il grafo</h3>
            ${roles.size ? [...roles.entries()].map(([role, columns]) => `
              <div class="kg-relation" style="--node-type: var(--node-${root.roleNodeType[role]})">
                <i aria-hidden="true"></i>
                <span>${escapeHtml(root.roleLabels[role])}</span>
                <span class="kg-relation-direction">${escapeHtml(columns.join(" + "))}</span>
              </div>`).join("") : `<p class="kg-block-empty">Nessuna colonna alimenta ancora il grafo.</p>`}
            <p class="kg-secondary">I collegamenti fra questi elementi vengono proposti nella fase successiva, solo dove le righe li dimostrano.</p>
          </section>
        </div>`;
    },

    renderDecision() {
      if (!state.structure) return "";
      const issue = openException();
      const error = state.structureError ? `<p class="kg-field-error" role="alert">${escapeHtml(state.structureError)}</p>` : "";
      if (issue) {
        return `<div class="kg-decision-row"><div class="kg-decision-text" aria-live="polite">
          <strong>Serve una tua scelta</strong>
          <span>${escapeHtml(`Una colonna di “${issue.source_name}” non può essere interpretata in modo affidabile. È l'unica domanda aperta.`)}</span>
        </div></div>${error}`;
      }
      const profile = activeProfile();
      const pending = profiles().filter((item) => !item.confirmed).length;
      if (state.structure.completed) {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>Struttura confermata</strong>
          <span>Nella fase successiva controllerai un grafo separato per ogni fonte.</span>
        </div>
        <div class="kg-decision-actions"><button type="button" class="kg-btn kg-btn-primary" data-kg-goto="graph">Vai al grafo</button></div></div>`;
      }
      if (profile && !profile.confirmed && profile.state === "prepared") {
        return `<div class="kg-decision-row"><div class="kg-decision-text">
          <strong>${escapeHtml(`Le colonne di “${profile.source_name}” sono interpretate correttamente?`)}</strong>
          <span>${escapeHtml(`La conferma vale solo per questo file. ${root.plural(pending, "file resta", "file restano")} da confermare.`)}</span>
        </div>
        <div class="kg-decision-actions">
          <button type="button" class="kg-btn kg-btn-primary" data-kg-confirm="${escapeHtml(profile.profile_id)}"
            ${state.structureBusy ? "disabled" : ""}>Conferma questo file</button>
        </div></div>${error}`;
      }
      return `<div class="kg-decision-row"><div class="kg-decision-text">
        <strong>${pending ? escapeHtml(`${root.plural(pending, "file da confermare", "file da confermare")}`) : "Tutti i file sono confermati"}</strong>
        <span>Seleziona un file nell'elenco a sinistra per controllarne le colonne.</span>
      </div></div>${error}`;
    },

    bindDecision(container) {
      root.delegate(container, "click", "[data-kg-confirm]", (element) => {
        run(() => root.api(`/api/g2/profiles/${encodeURIComponent(element.dataset.kgConfirm)}/confirm`, { method: "POST" }));
      });
      root.delegate(container, "click", "[data-kg-goto]", (element) => root.goToPhase(element.dataset.kgGoto));
    },
  };
})();
