(function () {
  "use strict";
  const root = window.KGFoundation = window.KGFoundation || {};
  const t = root.t;

  const FUGHE = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

  /** Ogni testo non fidato passa da qui prima di finire in innerHTML. */
  root.escapeHtml = function escapeHtml(valore) {
    return String(valore == null ? "" : valore).replace(/[&<>"']/g, (carattere) => FUGHE[carattere]);
  };
  const esc = root.escapeHtml;

  /** Sostituisce il contenuto di un contenitore lasciando in vita il resto. */
  root.paint = function paint(contenitore, markup) {
    if (!contenitore) return null;
    contenitore.innerHTML = markup;
    return contenitore;
  };

  /**
   * Un solo ascoltatore per contenitore invece di uno per elemento: una
   * selezione non costa mai una ricostruzione degli eventi.
   */
  root.delegate = function delegate(contenitore, tipo, selettore, azione) {
    if (!contenitore) return;
    const marchio = `__kg_${tipo}_${selettore}`;
    if (contenitore[marchio]) return;
    contenitore[marchio] = true;
    contenitore.addEventListener(tipo, (evento) => {
      const bersaglio = evento.target.closest(selettore);
      if (bersaglio && contenitore.contains(bersaglio)) azione(bersaglio, evento);
    });
  };

  /**
   * Una spiegazione breve accanto a un'etichetta, per le parole che un
   * operatore può non conoscere. Si apre col puntatore, col fuoco e al tocco.
   */
  root.info = function info(id, etichetta, spiegazione) {
    const sicuro = esc(id);
    return `
      <span class="info" tabindex="0" data-info-tip="${sicuro}"
        aria-label="${esc(etichetta)}" aria-describedby="info-${sicuro}">i
        <span class="info-bolla" id="info-${sicuro}" role="tooltip">
          <strong>${esc(etichetta)}</strong>
          <span>${esc(spiegazione)}</span>
        </span>
      </span>`;
  };

  root.etichettaTipo = (tipo) => t(`tipo.${tipo}`);
  root.etichettaTipoPl = (tipo) => t(`tipoPl.${tipo}`);
  root.etichettaRelazione = (tipo) => t(`rel.${tipo}`);
  root.ordineTipi = ["Asset", "Symptom", "ErrorCode", "FailureMode", "Component", "CorrectiveAction"];

  root.etichettaStato = (stato) => t(`stato.${stato}`);
  root.etichettaRuolo = (ruolo) => t(`ruolo.${ruolo}`);

  /** Quale tipo di nodo alimenta un ruolo di colonna: tiene coerenti i colori. */
  root.tipoDaRuolo = {
    observation: "Symptom",
    cause: "FailureMode",
    action: "CorrectiveAction",
    component: "Component",
    error_code: "ErrorCode",
  };

  /* Il motore riporta codici. L'operatore non ne deve leggere nessuno: qui
     diventano un titolo breve, e la frase del motore resta la spiegazione. */
  const LACUNE = new Set([
    "missing_failure_mode", "missing_diagnostic_indicator", "missing_corrective_action",
    "ambiguous_symptom_cause_pairing", "ambiguous_cause_component_pairing",
    "ambiguous_cause_action_pairing", "ambiguous_error_cause_pairing",
  ]);
  const DIFETTI = new Set([
    "extra_property", "missing_required_property", "duplicate_id",
    "relation_domain_range_mismatch", "relation_missing_source", "relation_missing_target",
    "unresolvable_provenance", "missing_provenance_locator", "unresolved_mapping_diagnostics",
  ]);
  root.titoloLacuna = (codice) => (LACUNE.has(codice) ? t(`lacuna.${codice}`) : t("lacuna.generica"));
  root.titoloDifetto = (codice) => (DIFETTI.has(codice) ? t(`difetto.${codice}`) : t("difetto.generico"));

  /**
   * Il locator è la strada di ritorno alla riga originale: qui diventa una
   * frase. I campi grezzi restano nel dettaglio tecnico, per chi li vuole.
   */
  root.descriviLocator = function descriviLocator(locator) {
    const dato = locator || {};
    if (dato.kind === "table_row") {
      const righe = dato.line_end && dato.line_end !== dato.line_start
        ? t("loc.righe", { a: dato.line_start, b: dato.line_end })
        : t("loc.riga", { n: dato.line_start });
      const nome = dato.table_name || dato.table_id || "";
      return [nome, righe, t("loc.record", { n: dato.record })].filter(Boolean).join(" · ");
    }
    if (dato.kind === "xlsx_row") return t("loc.foglio", { s: dato.sheet, n: dato.row });
    if (dato.kind === "json_path") {
      const percorso = t("loc.percorso", { p: dato.json_path });
      return dato.line ? `${percorso} · ${t("loc.riga", { n: dato.line })}` : percorso;
    }
    if (dato.kind === "pdf") {
      const pagina = t("loc.pagina", { n: dato.page });
      const stampata = dato.printed_page ? ` (${t("loc.stampata", { n: dato.printed_page })})` : "";
      return `${pagina}${stampata}${dato.section ? ` · ${dato.section}` : ""}`;
    }
    if (dato.kind === "operator_input") return t("loc.operatore");
    return t("loc.generico");
  };
})();
