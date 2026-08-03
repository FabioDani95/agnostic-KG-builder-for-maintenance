(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};

  const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

  /** Escape untrusted text before it reaches innerHTML. */
  root.escapeHtml = function escapeHtml(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, (character) => ESCAPES[character]);
  };

  /** Italian pluralisation without inventing a i18n layer. */
  root.plural = function plural(count, singular, pluralForm) {
    return `${count} ${Number(count) === 1 ? singular : pluralForm}`;
  };

  /** Replace a container's markup and rebind, keeping the rest of the frame alive. */
  root.paint = function paint(container, markup) {
    if (!container) return null;
    container.innerHTML = markup;
    return container;
  };

  /**
   * Delegate an event once per container instead of rebinding every node on
   * each repaint: selection changes must not cost a full listener rebuild.
   */
  root.delegate = function delegate(container, type, selector, handler) {
    if (!container || container[`__kg_${type}_${selector}`]) return;
    container[`__kg_${type}_${selector}`] = true;
    container.addEventListener(type, (event) => {
      const target = event.target.closest(selector);
      if (target && container.contains(target)) handler(target, event);
    });
  };

  /** Ontological vocabulary, in the operator's language. */
  root.nodeTypeLabels = {
    Asset: "Macchina",
    Component: "Componente",
    Symptom: "Sintomo",
    FailureMode: "Causa",
    CorrectiveAction: "Azione correttiva",
    ErrorCode: "Codice errore",
  };
  root.nodeTypePlural = {
    Asset: "Macchina",
    Component: "Componenti",
    Symptom: "Sintomi",
    FailureMode: "Cause",
    CorrectiveAction: "Azioni correttive",
    ErrorCode: "Codici errore",
  };
  root.relationTypeLabels = {
    HAS_COMPONENT: "comprende",
    MAY_INDICATE: "può indicare",
    AFFECTS: "interessa",
    RESOLVED_BY: "si risolve con",
    GENERATES_ERROR: "genera errore",
    INDICATES: "indica",
  };
  root.nodeTypeOrder = ["Asset", "Symptom", "ErrorCode", "FailureMode", "Component", "CorrectiveAction"];

  /**
   * A short explanation attached to a label, for the words an operator may not
   * know. Hover, focus and touch all open it; it never hides required meaning.
   */
  root.infoTip = function infoTip(id, label, explanation) {
    const safeId = root.escapeHtml(id);
    return `
      <span class="kg-info" tabindex="0" data-info-tip="${safeId}"
        aria-label="Informazioni su ${root.escapeHtml(label)}" aria-describedby="info-tip-${safeId}">
        <span class="kg-info-icon" aria-hidden="true">i</span>
        <span class="kg-info-popover" id="info-tip-${safeId}" role="tooltip">
          <strong>${root.escapeHtml(label)}</strong>
          <span>${root.escapeHtml(explanation)}</span>
        </span>
      </span>`;
  };

  /** Where a source stands, said in the operator's words. */
  root.sourceStateLabels = {
    waiting: "In attesa della struttura",
    ready: "Pronta da costruire",
    reviewing: "Da verificare",
    approved: "Verificata",
    rejected: "Da correggere",
    deferred: "Rimandata",
  };

  /** What a column was understood to mean. */
  root.roleLabels = {
    observation: "Sintomo o osservazione",
    cause: "Causa o diagnosi",
    action: "Azione eseguita",
    component: "Componente",
    error_code: "Codice errore",
    occurred_at: "Data e ora",
    outcome: "Esito",
    measurement: "Misura",
    attribute: "Altro dato",
    excluded: "Non usata",
  };

  /** Which node type a mapped column feeds, so the rail colour stays coherent. */
  root.roleNodeType = {
    observation: "Symptom",
    cause: "FailureMode",
    action: "CorrectiveAction",
    component: "Component",
    error_code: "ErrorCode",
  };

  /**
   * The engine reports machine codes. The operator must never read one: these
   * two dictionaries turn them into a short Italian title, and the engine's own
   * Italian sentence is shown underneath as the explanation.
   */
  const GAP_TITLES = {
    missing_failure_mode: "Causa non dichiarata nella riga",
    missing_diagnostic_indicator: "Sintomo o codice errore non dichiarato",
    missing_corrective_action: "Azione correttiva non dichiarata",
    ambiguous_symptom_cause_pairing: "Abbinamento sintomo–causa ambiguo",
    ambiguous_cause_component_pairing: "Abbinamento causa–componente ambiguo",
    ambiguous_cause_action_pairing: "Abbinamento causa–azione ambiguo",
    ambiguous_error_cause_pairing: "Abbinamento codice errore–causa ambiguo",
  };
  const DEFECT_TITLES = {
    extra_property: "Proprietà non prevista dalla struttura dati",
    missing_required_property: "Proprietà obbligatoria mancante",
    duplicate_id: "Identificativo ripetuto",
    relation_domain_range_mismatch: "Collegamento non ammesso tra questi tipi",
    relation_missing_source: "Collegamento senza elemento di partenza",
    relation_missing_target: "Collegamento senza elemento di arrivo",
    unresolvable_provenance: "Evidenza non risalibile alla fonte",
    missing_provenance_locator: "Evidenza senza posizione nella fonte",
    unresolved_mapping_diagnostics: "Colonna diagnostica non ancora interpretata",
  };
  root.gapTitle = (code) => GAP_TITLES[code] || "Informazione non dichiarata nella riga";
  root.defectTitle = (code) => DEFECT_TITLES[code] || "Controllo tecnico non superato";

  /**
   * A locator is the operator's way back to the original row. Render the
   * human sentence here and keep the raw fields for the technical disclosure.
   */
  root.locatorSummary = function locatorSummary(locator) {
    const data = locator || {};
    if (data.kind === "table_row") {
      const range = data.line_end && data.line_end !== data.line_start
        ? `righe ${data.line_start}–${data.line_end}`
        : `riga ${data.line_start}`;
      return `${data.table_name || data.table_id || "Tabella"} · ${range} · record ${data.record}`;
    }
    if (data.kind === "xlsx_row") return `Foglio ${data.sheet} · riga ${data.row}`;
    if (data.kind === "json_path") return `Percorso ${data.json_path}${data.line ? ` · riga ${data.line}` : ""}`;
    if (data.kind === "pdf") {
      const printed = data.printed_page ? ` (stampata ${data.printed_page})` : "";
      return `Pagina ${data.page}${printed}${data.section ? ` · ${data.section}` : ""}`;
    }
    if (data.kind === "operator_input") return "Dichiarazione dell'operatore";
    return "Posizione nella fonte";
  };
})();
