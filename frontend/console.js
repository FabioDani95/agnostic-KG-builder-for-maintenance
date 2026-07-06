/* Console HITL — implementation of "Console HITL.dc.html" wired to the real backend.
 *
 * Screens: Sessioni · Nuova sessione · Dashboard · Scoping · Grafo · Review Center ·
 * Qualità · Campi richiesti · Export, plus the right-hand Inspector.
 *
 * Real endpoints used:
 *   GET  /api/runs, GET /api/runs/{id}, GET|POST /api/runs/{id}/review-decisions,
 *   GET  /api/runs/{id}/export/{file}
 *   GET  /api/manuals, GET|POST /api/config, POST /api/load-manual
 *   POST /chat/start/{pdf_id}, POST /chat/action (propose_cut_plan, fill_required_field,
 *        apply_suggested_relation, approve_cut_plan, run_extraction, export_ontology)
 *   GET  /multi-agent/status/{run_id} (via /api/runs/{id}.status)
 */
(() => {
"use strict";

const ACCENT = "#C96442";
const app = document.getElementById("app");

/* ── colors (design tokens) ── */
const C = {
  ok: "#7A9B7E", okBg: "rgba(122,155,126,0.14)",
  warn: "#9A8352", warnBg: "rgba(194,163,107,0.18)",
  danger: "#B4543E", dangerBg: "rgba(180,84,62,0.10)",
  mute: "#8A867D", muteBg: "rgba(0,0,0,0.05)",
  brown: "#A07A56", brownBg: "rgba(176,135,106,0.14)",
};
const TYPE_COLORS = { Symptom: "#C96442", FailureMode: "#8E4A5B", CorrectiveAction: "#5E7B6A", ErrorCode: "#6E7B8A", Component: "#8C8474", Asset: "#7B6E8A" };
const ID_FIELDS = { Asset: "asset_id", Component: "component_id", Symptom: "symptom_id", FailureMode: "failure_mode_id", CorrectiveAction: "action_id", ErrorCode: "error_code_id" };

/* ── state ── */
const S = {
  view: "runs", lang: "it",
  runsList: [], manuals: [], config: null,
  run: null,            // derived session (see deriveSession)
  decisions: {}, removedCauses: {}, fieldAnswers: {}, answersSent: false, exportDone: false,
  filter: "all", search: "", selected: null,
  graph: { mode: "rete", colorBy: "tipo", showComp: true, zoom: 1, panX: 0, panY: 0, pos: {} },
  setup: { manual: "", scopingModel: "", extractionModel: "", lang: "italiano", operator: "", smallDoc: "40", maxRetries: "2", retrySev: "error" },
  busy: false, toast: null, starting: false, extracting: false,
};
let H = [];                 // per-render handler registry
let layoutCache = {};       // graph layout cache, invalidated per session
let dragInfo = null;
let pollTimer = null;

const L = (it, en) => (S.lang === "it" ? it : en);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const on = (fn) => (H.push(fn) - 1);
const fmtConf = (v) => (v == null ? "—" : Number(v).toFixed(2));

function toast(msg, isError) {
  S.toast = { msg, isError };
  render();
  setTimeout(() => { S.toast = null; render(); }, 3500);
}

/* ── API ── */
async function api(path, opts) {
  const res = await fetch(path, opts && opts.body ? { headers: { "Content-Type": "application/json" }, ...opts, body: JSON.stringify(opts.body) } : opts);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) { /* not json */ }
    throw new Error(detail);
  }
  return res.json();
}
const chatAction = async (pdfId, action, payload) => {
  const res = await api("/chat/action", { method: "POST", body: { pdf_id: pdfId, action, payload: payload || {} } });
  // The gate refuses out-of-phase actions with HTTP 200 + {status: "refused"}.
  if (res && res.status === "refused") throw new Error(res.reason || L("azione rifiutata dal sistema", "action refused by the system"));
  return res;
};

/* ── session derivation from GET /api/runs/{id} ── */
function deriveSession(payload) {
  const state = payload.state || {};
  const pipeline = state.ontology_pipeline || {};
  const ontology = pipeline.ontology || { nodes: {}, relations: [] };
  const report = pipeline.confidence_report || null;

  const confMap = {};
  (report && report.entries || []).forEach((e) => { confMap[e.node_id] = e; });

  const nodes = [];
  const nodeById = {};
  Object.entries(ontology.nodes || {}).forEach(([type, list]) => {
    (list || []).forEach((raw) => {
      const id = String(raw[ID_FIELDS[type] || "id"] || raw.id || "").trim();
      if (!id) return;
      const entry = confMap[id];
      const ev = (raw.evidence || [])[0] || null;
      const node = { id, type, label: String(raw.name || id), conf: entry ? entry.score : null, raw, quote: ev ? ev.quote : "", page: ev ? ev.source_page : "" };
      nodes.push(node);
      nodeById[id] = node;
    });
  });
  const edges = (ontology.relations || []).map((r) => ({
    s: String(r.from_id || r.from || ""), t: String(r.to_id || r.to || ""), rel: String(r.name || r.type || ""),
    quote: ((r.evidence || [])[0] || {}).quote || "", page: ((r.evidence || [])[0] || {}).source_page || "",
  })).filter((e) => e.s && e.t);

  const out = {}, inn = {};
  edges.forEach((e) => {
    (out[e.rel] = out[e.rel] || {})[e.s] = (out[e.rel][e.s] || []).concat(e.t);
    (inn[e.rel] = inn[e.rel] || {})[e.t] = (inn[e.rel][e.t] || []).concat(e.s);
  });

  const suggestions = pipeline.suggested_relations || [];
  const ambigBySymptom = {};
  const queue = (pipeline.review_queue || []).map((item) => {
    const q = { ...item };
    if (q.kind === "ambiguous_multi_cause_symptom") {
      q.causes = (q.candidate_failure_mode_ids || []).map((fid, i) => {
        const n = nodeById[fid];
        return { id: fid, label: (q.candidate_failure_mode_labels || [])[i] || (n ? n.label : fid), page: n ? n.page : "" };
      });
      ambigBySymptom[q.target_id] = true;
    }
    const sugIdx = suggestions.findIndex((sg) => sg.from_id === q.target_id || sg.to_id === q.target_id);
    if (sugIdx >= 0 && (q.severity === "open")) {
      const sg = suggestions[sugIdx];
      q.suggestion = { index: sugIdx, rel: sg.relation_name, from: sg.from_label || sg.from_id, to: sg.to_label || sg.to_id, toId: sg.to_id, conf: sg.confidence, rationale: sg.rationale || "" };
    }
    const n = nodeById[q.target_id];
    if (n && n.quote) { q.quote = n.quote; q.page = n.page; }
    if (n && (!q.label || q.label === q.target_id)) q.label = n.label || q.label;
    return q;
  });

  // Diagnostic chains Symptom → FailureMode → CorrectiveAction
  const triplets = [];
  nodes.filter((n) => n.type === "Symptom").forEach((sym) => {
    const fms = (out.MAY_INDICATE || {})[sym.id] || [];
    if (!fms.length) {
      triplets.push({ id: "t_" + sym.id, symptom: sym.label, fm: L("— nessuna causa collegata", "— no linked cause"), ca: "—", conf: sym.conf, complete: false, quote: sym.quote, page: sym.page, queueRef: "symptom_without_failure_mode|" + sym.id });
      return;
    }
    if (fms.length > 1) {
      const cas = fms.flatMap((f) => (out.RESOLVED_BY || {})[f] || []);
      triplets.push({
        id: "t_" + sym.id, symptom: sym.label,
        fm: fms.length + L(" cause candidate (ambiguità)", " candidate causes (ambiguity)"),
        ca: cas.slice(0, 2).map((c) => (nodeById[c] || {}).label || c).join(" / ") || "—",
        conf: Math.min(...[sym.conf, ...fms.map((f) => (nodeById[f] || {}).conf)].filter((v) => v != null).concat([1])),
        complete: cas.length > 0, ambiguous: true, quote: sym.quote, page: sym.page,
        queueRef: "ambiguous_multi_cause_symptom|" + sym.id,
      });
      return;
    }
    const fm = nodeById[fms[0]];
    const cas = (out.RESOLVED_BY || {})[fms[0]] || [];
    const ca = cas.length ? nodeById[cas[0]] : null;
    const confs = [sym.conf, fm && fm.conf, ca && ca.conf].filter((v) => v != null);
    const conf = confs.length ? Math.min(...confs) : null;
    triplets.push({
      id: "t_" + sym.id, symptom: sym.label, fm: fm ? fm.label : fms[0], ca: ca ? ca.label : L("— nessun rimedio", "— no remedy"),
      conf, complete: !!ca, weak: conf != null && conf < 0.65,
      quote: sym.quote || (fm && fm.quote) || "", page: sym.page || (fm && fm.page) || "",
      queueRef: !ca ? "failure_mode_without_action|" + fms[0] : null,
    });
  });

  const nodeTypes = Object.entries(ontology.nodes || {}).map(([t, l]) => [t, (l || []).length]).filter(([, c]) => c > 0).sort((a, b) => b[1] - a[1]);
  const relCounts = {};
  edges.forEach((e) => { relCounts[e.rel] = (relCounts[e.rel] || 0) + 1; });
  const REL_DESC = {
    MAY_INDICATE: "Symptom → FailureMode", RESOLVED_BY: "FailureMode → CorrectiveAction",
    AFFECTS: "FailureMode → Component", INDICATES: "ErrorCode → FailureMode",
    OBSERVED_ON: "Symptom → Component", HAS_COMPONENT: "Asset → Component",
  };
  const relTypes = Object.entries(relCounts).map(([t, c]) => [t, REL_DESC[t] || "", c]).sort((a, b) => b[2] - a[2]);

  const cut = state.cut_plan || null;
  const sections = cut ? (cut.sections || []).map((s) => ({
    name: s.name,
    pages: s.page_range ? s.page_range.start + "–" + s.page_range.end : "",
    source: s.source || "rule",
    why: s.reasoning || "",
    reasoning: s.reasoning || "",
    keywords: (s.keyword_matches || []).join(", "),
  })) : [];

  const trace = (payload.trace || []).map((t) => {
    const summary = t.output_summary || {};
    const secs = summary.duration_seconds;
    const parts = [];
    if (secs != null) parts.push(secs >= 60 ? Math.floor(secs / 60) + " min " + Math.round(secs % 60) + " s" : Math.round(secs) + " s");
    if (t.tokens) parts.push(Math.round(t.tokens / 1000) + "k tok");
    return {
      agent: t.agent || t.step || "", decision: t.decision || "",
      meta: parts.join(" · "), handoff: !!t.human_handoff, retries: t.retry_count || 0,
    };
  });

  const decisions = {};
  (payload.events || []).forEach((ev) => {
    if (ev.kind !== "review_decision") return;
    const d = ev.decision || {};
    const key = d.kind + "|" + d.target_id;
    if (d.verdict === "reopened") delete decisions[key];
    else decisions[key] = { status: d.verdict, label: d.note || "" };
  });

  return {
    runId: payload.run_id, pdfId: state.pdf_id || (payload.manifest || {}).pdf_id || "",
    manifest: payload.manifest || {}, status: payload.status || {}, state,
    isLive: !!payload.is_live, hasExport: !!payload.has_export, exportFiles: payload.export_files || [],
    pipeline, ontology, report, confMap,
    nodes, nodeById, edges, queue, triplets, nodeTypes, relTypes, sections, trace,
    fields: state.human_required_fields || pipeline.human_required_fields || [],
    suggestions, serverDecisions: decisions,
    cutPlan: cut,
    totalPages: state.total_pages || (payload.manifest || {}).page_count || 0,
  };
}

/* ── data loading ── */
async function loadRuns() {
  try { S.runsList = await api("/api/runs"); } catch (e) { toast(L("Errore nel caricare le sessioni: ", "Could not load sessions: ") + e.message, true); }
  render();
}
async function loadSetupData() {
  try {
    const [m, cfg] = await Promise.all([api("/api/manuals"), api("/api/config")]);
    S.manuals = m.manuals || [];
    // Model entries may be plain ids or {id, label, default} objects.
    const ids = (list) => (list || []).map((x) => (typeof x === "string" ? x : x.id)).filter(Boolean);
    const preferred = (list) => {
      const def = (list || []).find((x) => x && typeof x === "object" && x.default);
      return def ? def.id : ids(list)[0] || "";
    };
    const defScoping = preferred(cfg.scoping_models);
    const defExtraction = preferred(cfg.extraction_models);
    cfg.scoping_models = ids(cfg.scoping_models);
    cfg.extraction_models = ids(cfg.extraction_models);
    S.config = cfg;
    if (!S.setup.manual && S.manuals.length) S.setup.manual = S.manuals[0].filename;
    if (!S.setup.scopingModel) S.setup.scopingModel = defScoping;
    if (!S.setup.extractionModel) S.setup.extractionModel = defExtraction;
    S.setup.smallDoc = String(cfg.small_doc_threshold ?? S.setup.smallDoc);
    S.setup.maxRetries = String((cfg.reflective_loop || {}).max_retries ?? S.setup.maxRetries);
    S.setup.retrySev = (cfg.reflective_loop || {}).retry_on_severity || S.setup.retrySev;
  } catch (e) { toast(e.message, true); }
  render();
}
async function openRun(runId, view) {
  S.busy = true; render();
  try {
    const payload = await api("/api/runs/" + encodeURIComponent(runId));
    S.run = deriveSession(payload);
    S.decisions = { ...S.run.serverDecisions };
    S.removedCauses = {}; S.fieldAnswers = {}; S.answersSent = false; S.exportDone = false;
    S.selected = null; S.filter = "all"; S.search = "";
    S.graph = { mode: "rete", colorBy: "tipo", showComp: true, zoom: 1, panX: 0, panY: 0, pos: {} };
    layoutCache = {};
    S.view = view || "dashboard";
    schedulePoll();
  } catch (e) {
    toast(L("Impossibile aprire la sessione: ", "Could not open the session: ") + e.message, true);
  }
  S.busy = false; render();
}
async function refreshRun(keepUi) {
  if (!S.run) return;
  try {
    const payload = await api("/api/runs/" + encodeURIComponent(S.run.runId));
    const prevDecisions = S.decisions;
    S.run = deriveSession(payload);
    S.decisions = keepUi ? { ...S.run.serverDecisions, ...prevDecisions } : { ...S.run.serverDecisions };
    layoutCache = {};
  } catch (e) { /* transient poll error: keep last state */ }
  render();
}
function schedulePoll() {
  clearTimeout(pollTimer);
  // A single is_live=false read can be a transient race while backend tools
  // swap graph_state: stop only after several consecutive terminal reads.
  let terminalReads = 0;
  const tick = async () => {
    if (!S.run) return;
    const st = (S.run.status || {}).run_status || "";
    const terminal = !S.run.isLive || ["completed", "failed", "exported"].includes(st);
    terminalReads = terminal ? terminalReads + 1 : 0;
    if (terminalReads >= 3) return;
    await refreshRun(true);
    pollTimer = setTimeout(tick, 4000);
  };
  pollTimer = setTimeout(tick, 4000);
}

/* ── decisions ── */
const qKey = (item) => item.kind + "|" + item.target_id;
const getDec = (item) => S.decisions[qKey(item)];
function decide(item, status, label) {
  S.decisions = { ...S.decisions, [qKey(item)]: { status, label } };
  persistDecision(item, status, label);
  render();
}
function reopenDecision(item) {
  const d = { ...S.decisions }; delete d[qKey(item)]; S.decisions = d;
  persistDecision(item, "reopened", "");
  render();
}
function persistDecision(item, verdict, note) {
  if (!S.run) return;
  api("/api/runs/" + encodeURIComponent(S.run.runId) + "/review-decisions", {
    method: "POST",
    body: { kind: item.kind, target_id: item.target_id, target_type: item.target_type || "", verdict, note: note || "", operator: S.run.state.operator || "" },
  }).catch((e) => toast(L("Decisione non salvata sul server: ", "Decision not saved server-side: ") + e.message, true));
}

/* ── meta dictionaries ── */
function sevMeta() {
  return {
    blocking: { label: L("Bloccante", "Blocking"), color: C.danger, bg: C.dangerBg },
    open: { label: L("Lacuna aperta", "Open gap"), color: C.brown, bg: C.brownBg },
    reject: { label: L("Auto-rifiutato", "Auto-rejected"), color: C.danger, bg: C.dangerBg },
    review: { label: L("Revisione", "Review"), color: C.warn, bg: C.warnBg },
    advisory: { label: "Advisory", color: C.mute, bg: C.muteBg },
  };
}
function kindLabels() {
  return {
    required_property_missing: L("Proprietà richiesta mancante", "Required property missing"),
    symptom_without_failure_mode: L("Sintomo senza causa", "Symptom without cause"),
    failure_mode_without_action: L("Guasto senza rimedio", "Failure without remedy"),
    orphan_corrective_action: L("Azione orfana", "Orphan action"),
    error_code_without_failure_mode: L("Codice non collegato", "Unlinked error code"),
    low_confidence: L("Bassa confidenza", "Low confidence"),
    ambiguous_multi_cause_symptom: L("Ambiguità multi-causa", "Multi-cause ambiguity"),
    non_actionable_instruction: L("Istruzione non azionabile", "Non-actionable instruction"),
    duplicate_candidate: L("Possibile duplicato", "Possible duplicate"),
    material_context_not_linked: L("Contesto materiale non collegato", "Material context not linked"),
  };
}
function decMeta() {
  return {
    confirmed: { label: L("Confermato", "Confirmed"), color: C.ok },
    resolved: { label: L("Gestito", "Handled"), color: C.ok },
    accepted: { label: L("Suggerimento accettato", "Suggestion accepted"), color: C.ok },
    rejected: { label: L("Rifiutato", "Rejected"), color: C.danger },
    ignored: { label: L("Ignorato", "Ignored"), color: C.mute },
    acknowledged: { label: L("Preso atto", "Acknowledged"), color: C.mute },
  };
}
const typeLabel = (t) => {
  const it = { Symptom: "Sintomo", FailureMode: "Guasto", CorrectiveAction: "Azione correttiva", ErrorCode: "Codice errore", Component: "Componente", Asset: "Asset" };
  return L(it[t] || t, t);
};

/* ── queue math ── */
function queueStats() {
  const run = S.run;
  const visible = run ? run.queue : [];
  const decided = visible.filter((q) => getDec(q));
  const open = visible.filter((q) => !getDec(q));
  const blocking = open.filter((q) => q.severity === "blocking").length;
  const gaps = open.filter((q) => q.severity === "open").length;
  const answered = run ? run.fields.filter((f) => (S.fieldAnswers[f.field_key] || "").trim()).length : 0;
  const fieldsMissing = run ? run.fields.length - answered : 0;
  return { visible, decided, open, blocking, gaps, review: open.length - blocking - gaps, answered, fieldsMissing };
}

/* ═══ RENDER ═══ */
function render() {
  H = [];
  const run = S.run;
  const st = queueStats();

  let runStatus, statusColor, statusBg;
  if (!run) { runStatus = L("Nessuna sessione aperta", "No session open"); statusColor = C.mute; statusBg = C.muteBg; }
  else if (st.blocking > 0 || st.fieldsMissing > 0) { runStatus = L("Richiede revisione umana", "Needs human review"); statusColor = C.warn; statusBg = C.warnBg; }
  else if (st.open.length > 0) { runStatus = L("Revisione in corso", "Review in progress"); statusColor = C.warn; statusBg = C.warnBg; }
  else if (!["export", "completed"].includes(run.status.current_phase || "")) { runStatus = L("Coda gestita — pipeline da completare", "Queue handled — pipeline to finish"); statusColor = C.mute; statusBg = C.muteBg; }
  else { runStatus = L("Pronto per l'export", "Ready to export"); statusColor = C.ok; statusBg = C.okBg; }
  if (run && !run.pipeline.review_queue) { runStatus = phaseLabel(run.status.current_phase); statusColor = C.mute; statusBg = C.muteBg; }

  const metrics = run ? (run.status.metrics || {}) : {};
  const durTxt = fmtDuration(metrics.duration_seconds);
  const costTxt = metrics.estimated_cost_usd != null ? "$ " + Number(metrics.estimated_cost_usd).toFixed(2) : "—";
  const model = run ? ((run.state.selected_models || {}).extraction || "—") : "—";

  const views = {
    runs: viewRuns, setup: viewSetup, dashboard: viewDashboard, scoping: viewScoping,
    graph: viewGraph, review: viewReview, quality: viewQuality, fields: viewFields, export: viewExport,
  };
  const inspector = buildInspector();

  app.innerHTML = `
  <header class="c-header">
    <div style="display:flex;align-items:baseline;gap:10px;min-width:0;">
      <span class="serif" style="font-size:16px;font-weight:600;white-space:nowrap;">Console estrazione KG</span>
      ${run ? `<span style="font-size:12px;color:#8A867D;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(run.manifest.filename || run.state.filename || "")}</span>` : ""}
    </div>
    <div style="flex:1;"></div>
    <div style="display:flex;gap:2px;background:rgba(0,0,0,0.05);border-radius:99px;padding:2px;">
      ${[["it", "ITA"], ["en", "ENG"]].map(([v, lbl]) => `
        <button data-h="${on(() => { S.lang = v; render(); })}" style="font-size:11px;font-weight:600;padding:4px 10px;border-radius:99px;border:none;background:${S.lang === v ? "#FFFFFF" : "transparent"};color:${S.lang === v ? "#22211D" : "#8A867D"};">${lbl}</button>`).join("")}
    </div>
    <div style="display:flex;align-items:center;gap:7px;padding:5px 12px;border-radius:99px;background:${statusBg};">
      <span style="width:7px;height:7px;border-radius:50%;background:${run ? statusColor : "#B5B1A6"};"></span>
      <span style="font-size:12px;font-weight:600;color:${statusColor};white-space:nowrap;">${esc(runStatus)}</span>
    </div>
    ${run ? `
      <span class="tnum" style="font-size:12px;color:#8A867D;white-space:nowrap;">${st.decided.length}${L(" di ", " of ")}${st.visible.length}${L(" gestiti", " handled")}</span>
      <div style="width:120px;height:4px;border-radius:2px;background:rgba(0,0,0,0.08);overflow:hidden;">
        <div style="height:100%;background:${ACCENT};width:${st.visible.length ? Math.round((st.decided.length / st.visible.length) * 100) : 0}%;transition:width .3s ease;"></div>
      </div>
      <span class="mono" style="font-size:11px;color:#B5B1A6;white-space:nowrap;">${esc(shortRunId(run.runId))} · ${L("fase: ", "phase: ")}${esc(run.status.current_phase || "")}</span>` : ""}
  </header>
  <div class="c-body">
    <nav class="c-nav">
      ${renderNav(st)}
      <div style="flex:1;"></div>
      ${run ? `
      <div style="padding:10px;border-top:1px solid rgba(0,0,0,0.06);font-size:11px;line-height:1.7;color:#918D83;">
        <div style="display:flex;justify-content:space-between;"><span>${L("Modello", "Model")}</span><span class="mono">${esc(model || "—")}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>${L("Costo run", "Run cost")}</span><span class="tnum">${costTxt}</span></div>
        <div style="display:flex;justify-content:space-between;"><span>${L("Durata", "Duration")}</span><span class="tnum">${durTxt}</span></div>
      </div>` : ""}
    </nav>
    <main class="c-main">${(views[S.view] || viewRuns)(st)}</main>
    ${inspector}
  </div>
  ${S.toast ? `<div class="c-toast ${S.toast.isError ? "error" : ""}">${esc(S.toast.msg)}</div>` : ""}`;
}

function shortRunId(id) { return id && id.length > 12 ? id.slice(0, 12) : (id || ""); }
function fmtDuration(secs) {
  if (secs == null || !isFinite(secs)) return "—";
  if (secs < 60) return Math.round(secs) + " s";
  return Math.floor(secs / 60) + " min " + Math.round(secs % 60) + " s";
}
function phaseLabel(phase) {
  const map = {
    loaded: L("Caricato", "Loaded"), scoping: "Scoping", ontology_draft: L("Bozza ontologia", "Ontology draft"),
    extraction: L("Estrazione", "Extraction"), validation: L("Validazione", "Validation"),
    coverage: L("Copertura", "Coverage"), grounding: L("Verifica citazioni", "Citation check"),
    conflict_resolution: L("Duplicati", "Duplicates"), refinement: L("Rifinitura", "Refinement"),
    export: "Export", completed: L("Completato", "Completed"),
  };
  return map[phase] || phase || L("In corso", "Running");
}

/* ── nav ── */
function renderNav(st) {
  const icons = {
    runs: "M12 8v4l3 2.5M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18",
    setup: "M10 8l6 4-6 4V8M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18",
    dashboard: "M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z",
    scoping: "M6 2v14a2 2 0 0 0 2 2h14M2 6h14a2 2 0 0 1 2 2v14",
    graph: "M12 3v5m0 0l-6 5m6-5l6 5M6 13v5m12-5v5",
    review: "M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11",
    quality: "M22 12h-4l-3 9L9 3l-3 9H2",
    fields: "M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z",
    export: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12",
  };
  const defs = [
    ["runs", L("Sessioni", "Sessions"), null],
    ["setup", L("Nuova sessione", "New session"), null],
    ["dashboard", "Dashboard", null],
    ["scoping", "Scoping", null],
    ["graph", L("Grafo", "Graph"), null],
    ["review", "Review Center", st.open.length || null],
    ["quality", L("Qualità", "Quality"), null],
    ["fields", L("Campi richiesti", "Required fields"), st.fieldsMissing || null],
    ["export", "Export", null],
  ];
  const sessionViews = ["dashboard", "scoping", "graph", "review", "quality", "fields", "export"];
  const btns = defs.map(([id, label, count]) => {
    const locked = sessionViews.includes(id) && !S.run;
    const go = on(() => {
      if (locked) { S.view = "runs"; } else { S.view = id; S.selected = null; if (id === "runs") loadRuns(); if (id === "setup") loadSetupData(); }
      render();
    });
    return `
    <button class="nav-btn" data-h="${go}" ${S.view === id ? "data-active" : ""} ${locked ? "data-locked" : ""}
      style="opacity:${locked ? 0.45 : 1};cursor:${locked ? "not-allowed" : "pointer"};color:${locked ? "#A5A196" : S.view === id ? "#22211D" : "#55524B"};">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" style="flex:none;opacity:0.75;"><path d="${icons[id]}"></path></svg>
      <span style="flex:1;font-size:13px;font-weight:${S.view === id ? 600 : 500};">${esc(label)}</span>
      ${!locked && count ? `<span class="tnum" style="font-size:11px;font-weight:600;padding:1px 7px;border-radius:99px;background:${id === "review" && st.blocking > 0 ? C.dangerBg : C.warnBg};color:${id === "review" && st.blocking > 0 ? C.danger : C.warn};">${count}</span>` : ""}
    </button>`;
  }).join("");
  const hint = !S.run ? `<div style="margin:8px 4px 0;padding:10px 12px;border-radius:10px;background:rgba(0,0,0,0.04);font-size:11px;line-height:1.55;color:#8A867D;">${L("Dashboard, grafo e revisione si riferiscono a una sessione: aprine una o avviane una nuova per sbloccarli.", "Dashboard, graph and review refer to a session: open one or start a new one to unlock them.")}</div>` : "";
  return btns + hint;
}

/* ── Sessioni ── */
function viewRuns() {
  const statusMeta = {
    needs_human_review: { label: L("revisione umana", "human review"), color: C.warn, bg: C.warnBg },
    needs_human: { label: L("revisione umana", "human review"), color: C.warn, bg: C.warnBg },
    awaiting_operator: { label: L("attende operatore", "awaiting operator"), color: C.warn, bg: C.warnBg },
    in_progress: { label: L("in corso", "in progress"), color: C.brown, bg: C.brownBg },
    loaded: { label: L("caricato", "loaded"), color: C.mute, bg: C.muteBg },
    exported: { label: L("esportato", "exported"), color: C.ok, bg: C.okBg },
    completed: { label: L("completato", "completed"), color: C.ok, bg: C.okBg },
    failed: { label: L("fallito", "failed"), color: C.danger, bg: C.dangerBg },
  };
  const rows = S.runsList.map((r) => {
    const m = statusMeta[r.run_status] || { label: r.run_status || "—", color: C.mute, bg: C.muteBg };
    const isCurrent = S.run && S.run.runId === r.run_id;
    const dt = r.created_at ? new Date(r.created_at) : null;
    const dateTxt = dt && !isNaN(dt) ? dt.toLocaleDateString(S.lang === "it" ? "it-IT" : "en-GB", { day: "numeric", month: "short", year: "numeric" }) : "";
    const models = [r.selected_scoping_model || "—", r.selected_extraction_model || "—"].join(" / ");
    return `
    <div style="display:grid;grid-template-columns:110px 1fr 140px 180px 116px 70px;gap:12px;align-items:center;padding:12px 20px;border-top:1px solid rgba(0,0,0,0.05);">
      <span class="mono" style="font-size:12px;">${esc(shortRunId(r.run_id))}</span>
      <span style="font-size:13px;font-weight:500;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(r.manual_filename || "—")}
        ${isCurrent ? `<span style="margin-left:8px;font-size:10.5px;font-weight:600;color:${ACCENT};">${L("corrente", "current")}</span>` : ""}
      </span>
      <span style="font-size:12px;color:#8A867D;">${esc([r.operator, dateTxt].filter(Boolean).join(" · ") || "—")}</span>
      <span class="mono" style="font-size:11px;color:#8A867D;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(models)}</span>
      <span class="pill" style="font-size:11px;color:${m.color};background:${m.bg};padding:3px 9px;text-align:center;">${esc(m.label)}</span>
      <button class="btn-ghost" data-h="${on(() => openRun(r.run_id))}">${L("Apri", "Open")}</button>
    </div>`;
  }).join("");
  return `
  <div style="max-width:960px;margin:0 auto;padding:26px 32px 40px;">
    <div style="display:flex;align-items:flex-start;gap:16px;margin:0 0 18px;">
      <div style="flex:1;min-width:0;">
        <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 6px;">${L("Sessioni", "Sessions")}</h1>
        <p style="font-size:13px;color:#55524B;line-height:1.55;margin:0;max-width:620px;">${L("Riprendi una sessione di verifica o avviane una nuova. Ogni sessione resta salvata: puoi chiudere la console e riprendere da dove eri.", "Resume a verification session or start a new one. Every session is saved: you can close the console and pick up where you left off.")}</p>
      </div>
      <button class="btn-primary" style="--accent:${ACCENT};" data-h="${on(() => { S.view = "setup"; loadSetupData(); })}">${L("+ Nuova sessione", "+ New session")}</button>
    </div>
    <div class="card" style="overflow:hidden;">
      <div class="kicker" style="display:grid;grid-template-columns:110px 1fr 140px 180px 116px 70px;gap:12px;padding:10px 20px;">
        <span>Run</span><span>${L("Manuale", "Manual")}</span><span>${L("Operatore · data", "Operator · date")}</span><span>${L("Modelli (scop. / estraz.)", "Models (scop. / extr.)")}</span><span>${L("Stato", "Status")}</span><span></span>
      </div>
      ${rows || `<div style="padding:28px 20px;font-size:13px;color:#8A867D;border-top:1px solid rgba(0,0,0,0.05);">${L("Nessuna sessione salvata — avviane una nuova.", "No saved sessions — start a new one.")}</div>`}
    </div>
  </div>`;
}

/* ── Nuovo run ── */
function viewSetup() {
  const SU = S.setup;
  const seg = (opts, cur, set) => opts.map((o) => `
    <button data-h="${on(() => { set(o); render(); })}" class="mono" style="font-size:12px;font-weight:500;padding:6px 12px;border-radius:8px;border:1px solid rgba(0,0,0,0.10);background:${cur === o ? "#3A3934" : "#FFFFFF"};color:${cur === o ? "#FFFFFF" : "#55524B"};">${esc(o)}</button>`).join("");
  const manuals = S.manuals.map((m) => `
    <button data-h="${on(() => { SU.manual = m.filename; render(); })}" class="row-hover" style="display:flex;align-items:center;gap:12px;width:100%;padding:10px 12px;border:none;border-radius:10px;background:transparent;text-align:left;">
      <span style="width:14px;height:14px;flex:none;border-radius:50%;background:${SU.manual === m.filename ? ACCENT : "#FFFFFF"};box-shadow:${SU.manual === m.filename ? "0 0 0 1px " + ACCENT : "inset 0 0 0 1.5px rgba(0,0,0,0.18)"};"></span>
      <span style="flex:1;min-width:0;">
        <span style="display:block;font-size:13px;font-weight:500;">${esc(m.filename)}</span>
        <span style="display:block;font-size:11px;color:#8A867D;margin-top:1px;">${(m.size_bytes / 1048576).toFixed(1)} MB</span>
      </span>
    </button>`).join("") || `<div style="font-size:12.5px;color:#8A867D;padding:8px 12px;">${L("Nessun PDF nella cartella manuals/.", "No PDFs in the manuals/ folder.")}</div>`;

  const startBtn = on(async () => {
    if (!SU.manual || S.starting) return;
    S.starting = true; render();
    try {
      await api("/api/config", { method: "POST", body: { small_doc_threshold: parseInt(SU.smallDoc, 10) || 40, max_retries: parseInt(SU.maxRetries, 10) || 0, retry_on_severity: SU.retrySev } });
      const up = await api("/api/load-manual", { method: "POST", body: { filename: SU.manual } });
      await api("/chat/start/" + up.pdf_id, { method: "POST", body: {
        selected_scoping_model: SU.scopingModel || null,
        selected_extraction_model: SU.extractionModel || null,
        target_language: SU.lang === "italiano" ? "it" : "en",
        operator: SU.operator || null,
      } });
      // The auto-start LLM turn is not guaranteed to invoke the scoping tool:
      // kick it deterministically (allowed in both loaded and scoping phases).
      try { await chatAction(up.pdf_id, "propose_cut_plan"); } catch (e) { /* scoping already started */ }
      toast(L("Run avviato — il sistema sta leggendo il manuale.", "Run started — the system is reading the manual."));
      await openRun(up.run_id, "dashboard");
    } catch (e) { toast(L("Avvio fallito: ", "Start failed: ") + e.message, true); }
    S.starting = false; render();
  });

  const inp = (val, set, style) => `<input value="${esc(val)}" data-h="${on((e) => set(e.target.value))}" data-evt="change" style="${style}font-size:13px;padding:8px 12px;border-radius:9px;border:1px solid rgba(0,0,0,0.10);background:#FDFCFA;">`;

  return `
  <div style="max-width:700px;margin:0 auto;padding:26px 32px 40px;">
    <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 6px;">${L("Nuova sessione", "New session")}</h1>
    <p style="font-size:13px;color:#55524B;line-height:1.55;margin:0 0 18px;">${L("Due passi: scegli il manuale e i modelli, poi avvia. La selezione delle pagine utili e l'allineamento dei numeri di pagina sono automatici.", "Two steps: pick the manual and the models, then start. Selecting the useful pages and aligning page numbers happen automatically.")}</p>

    <div class="card" style="padding:16px 20px;margin-bottom:12px;">
      <div class="kicker" style="margin-bottom:10px;">${L("Manuale", "Manual")}</div>
      ${manuals}
    </div>

    <div class="card" style="padding:16px 20px;margin-bottom:12px;">
      <div class="kicker" style="margin-bottom:12px;">${L("Modelli", "Models")}</div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap;">
        <span style="font-size:12.5px;color:#55524B;width:92px;flex:none;">Scoping</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">${seg((S.config || {}).scoping_models || [], SU.scopingModel, (v) => SU.scopingModel = v)}</div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <span style="font-size:12.5px;color:#55524B;width:92px;flex:none;">${L("Estrazione", "Extraction")}</span>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">${seg((S.config || {}).extraction_models || [], SU.extractionModel, (v) => SU.extractionModel = v)}</div>
      </div>
    </div>

    <div class="card" style="padding:16px 20px;margin-bottom:12px;">
      <div class="kicker" style="margin-bottom:12px;">${L("Contesto", "Context")}</div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap;">
        <span style="font-size:12.5px;color:#55524B;width:92px;flex:none;">${L("Lingua grafo", "Graph language")}</span>
        <div style="display:flex;gap:6px;">
          ${["italiano", "english"].map((o) => `<button data-h="${on(() => { SU.lang = o; render(); })}" style="font-size:12px;font-weight:500;font-family:inherit;padding:6px 14px;border-radius:8px;border:1px solid rgba(0,0,0,0.10);background:${SU.lang === o ? "#3A3934" : "#FFFFFF"};color:${SU.lang === o ? "#FFFFFF" : "#55524B"};">${o}</button>`).join("")}
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <span style="font-size:12.5px;color:#55524B;width:92px;flex:none;">${L("Operatore", "Operator")}</span>
        ${inp(SU.operator, (v) => SU.operator = v, "width:140px;")}
        <span style="font-size:11.5px;color:#A5A196;">${L("sigla di chi esegue la verifica — data e ora sono registrate da sole", "initials of who runs the verification — date and time are recorded automatically")}</span>
      </div>
    </div>

    <div class="card" style="padding:16px 20px;margin-bottom:16px;">
      <div class="kicker" style="margin-bottom:12px;">${L("Avanzate", "Advanced")}</div>
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap;">
        <span style="font-size:12.5px;color:#55524B;width:170px;flex:none;">${L("Documenti brevi", "Short documents")}</span>
        <input type="number" min="1" value="${esc(SU.smallDoc)}" data-h="${on((e) => SU.smallDoc = e.target.value)}" data-evt="change" class="tnum" style="width:80px;font-size:13px;padding:7px 12px;border-radius:9px;border:1px solid rgba(0,0,0,0.10);background:#FDFCFA;">
        <span style="font-size:11.5px;color:#A5A196;">${L("fino a questo numero di pagine il manuale viene letto per intero, senza selezione", "up to this many pages the manual is read in full, without page selection")}</span>
      </div>
      <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
        <span style="font-size:12.5px;color:#55524B;width:170px;flex:none;">${L("Correzioni automatiche", "Automatic retries")}</span>
        <input type="number" min="0" max="5" value="${esc(SU.maxRetries)}" data-h="${on((e) => SU.maxRetries = e.target.value)}" data-evt="change" class="tnum" style="width:80px;font-size:13px;padding:7px 12px;border-radius:9px;border:1px solid rgba(0,0,0,0.10);background:#FDFCFA;">
        <span style="font-size:12.5px;color:#55524B;margin-left:8px;">${L("riprova quando trova", "retry when it finds")}</span>
        <div style="display:flex;gap:6px;">
          ${[["error", L("solo errori", "errors only")], ["warning", L("anche avvisi", "warnings too")]].map(([o, lbl]) => `<button data-h="${on(() => { SU.retrySev = o; render(); })}" style="font-size:12px;font-weight:500;font-family:inherit;padding:6px 12px;border-radius:8px;border:1px solid rgba(0,0,0,0.10);background:${SU.retrySev === o ? "#3A3934" : "#FFFFFF"};color:${SU.retrySev === o ? "#FFFFFF" : "#55524B"};">${lbl}</button>`).join("")}
        </div>
      </div>
    </div>

    <div style="display:flex;align-items:center;gap:12px;">
      <button class="btn-primary" style="--accent:${ACCENT};padding:11px 22px;" data-h="${startBtn}" ${S.starting ? "disabled" : ""}>${S.starting ? L("Avvio in corso…", "Starting…") : L("Carica il PDF e avvia", "Load the PDF and start")}</button>
      <span style="font-size:11.5px;color:#A5A196;line-height:1.5;max-width:340px;">${L("Il sistema legge il manuale, seleziona da solo le pagine utili e ti avvisa quando serve la tua verifica.", "The system reads the manual, picks the useful pages on its own and alerts you when your verification is needed.")}</span>
    </div>
  </div>`;
}

/* ── Dashboard ── */
function viewDashboard(st) {
  const run = S.run;
  if (!run) return viewRuns();
  const status = run.status || {};
  const phase = status.current_phase || "loaded";
  const phaseOrder = ["loaded", "scoping", "ontology_draft", "extraction", "validation", "coverage", "grounding", "conflict_resolution", "refinement", "export", "completed"];
  const stageDefs = [
    ["Upload", "loaded"], ["Scoping", "scoping"], [L("Bozza ontologia", "Ontology draft"), "ontology_draft"],
    [L("Estrazione", "Extraction"), "extraction"], ["Review", "review"], ["Export", "export"],
  ];
  const idx = phaseOrder.indexOf(phase);
  const reviewActive = run.queue.length > 0 && !["export", "completed"].includes(phase);
  const stageState = (key) => {
    if (key === "review") return reviewActive ? "current" : (["export", "completed"].includes(phase) ? "done" : "pending");
    const kidx = phaseOrder.indexOf(key);
    if (kidx < 0) return "pending";
    if (kidx < idx || phase === "completed") return "done";
    if (kidx === idx && !reviewActive) return "current";
    return kidx <= idx ? "done" : "pending";
  };
  const stages = stageDefs.map(([label, key], i) => {
    const stt = stageState(key);
    return `
    <div style="display:flex;align-items:center;flex:${i < stageDefs.length - 1 ? "1" : "0 0 auto"};min-width:0;">
      <div style="display:flex;flex-direction:column;align-items:center;gap:5px;min-width:76px;">
        <span style="width:22px;height:22px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:600;background:${stt === "done" ? C.okBg : stt === "current" ? ACCENT : "rgba(0,0,0,0.05)"};color:${stt === "done" ? C.ok : stt === "current" ? "#FFFFFF" : "#B5B1A6"};box-shadow:${stt === "current" ? "0 0 0 4px rgba(201,100,66,0.15)" : "none"};">${stt === "done" ? "✓" : stt === "current" ? "●" : "○"}</span>
        <span style="font-size:11px;font-weight:${stt === "current" ? 600 : 500};color:${stt === "pending" ? "#B5B1A6" : "#3A3934"};white-space:nowrap;">${esc(label)}</span>
      </div>
      ${i < stageDefs.length - 1 ? `<div style="flex:1;height:1.5px;background:${stt === "done" ? "rgba(122,155,126,0.4)" : "rgba(0,0,0,0.08)"};margin:0 4px 18px;min-width:20px;"></div>` : ""}
    </div>`;
  }).join("");

  // Operator handoffs: the authoritative signal is run_status/next_step set by
  // the backend at each handoff; the structural checks keep runs persisted
  // before that change (and transient states) covered.
  const runStatusRaw = (run.status || {}).run_status || "";
  const nextStep = (run.status || {}).next_step || "";
  const awaitingScoping = !!run.cutPlan && !run.pipeline.ontology && ["scoping", "loaded"].includes(phase);
  const awaitingExtraction = phase === "ontology_draft";
  const handoff = awaitingScoping || awaitingExtraction ||
    (runStatusRaw === "awaiting_operator" && ["approve_cut_plan", "run_extraction"].includes(nextStep));
  const awaitingOperator = run.isLive && phase !== "completed" && handoff;
  // Mid-flow run whose backend session is gone (e.g. server restart): without
  // this branch the banner used to fall through to "run complete".
  const interrupted = !run.isLive && phase !== "completed" && handoff;
  const running = run.isLive && !awaitingOperator && !run.pipeline.review_queue && phase !== "completed";
  let bannerTitle, bannerDetail, bannerGlyph, bannerBg, bannerColor, bannerCta = "";
  if (interrupted) {
    bannerTitle = L("Sessione non più attiva — run incompleto", "Session no longer active — run incomplete");
    bannerDetail = L("Il run si era fermato in attesa dell'operatore (" , "The run had stopped waiting for the operator (")
      + (awaitingScoping ? L("approvazione della selezione pagine", "page-selection approval") : L("avvio dell'estrazione", "extraction start"))
      + L(") e il processo backend non è più attivo. I dati restano consultabili; per completare l'estrazione avvia una nuova sessione.", ") and the backend process is no longer active. The data is still browsable; start a new session to complete the extraction.");
    bannerGlyph = "!"; bannerBg = C.dangerBg; bannerColor = C.danger;
  } else if (awaitingOperator) {
    bannerGlyph = "!"; bannerBg = C.warnBg; bannerColor = C.warn;
    if (awaitingScoping || nextStep === "approve_cut_plan") {
      bannerTitle = L("Tocca a te: approva la selezione delle pagine", "Your turn: approve the page selection");
      bannerDetail = L("Lo scoping è completato e il run resta in pausa finché non approvi (o correggi) la selezione nella scheda Scoping.", "Scoping is done and the run stays paused until you approve (or fix) the selection in the Scoping tab.");
      bannerCta = `<button class="btn-primary" style="--accent:${ACCENT};padding:9px 18px;" data-h="${on(() => { S.view = "scoping"; S.selected = null; render(); })}">${L("Vai allo Scoping", "Go to Scoping")}</button>`;
    } else {
      bannerTitle = L("Tocca a te: avvia l'estrazione", "Your turn: start the extraction");
      bannerDetail = L("La bozza dell'ontologia è pronta. L'estrazione parte solo quando la avvii tu.", "The ontology draft is ready. Extraction starts only when you launch it.");
    }
  } else if (running) {
    bannerTitle = phase === "loaded" ? L("Avvio in corso…", "Starting…") : phaseLabel(phase) + L(" — in corso…", " — in progress…");
    bannerDetail = L("Il sistema sta lavorando: la pagina si aggiorna da sola.", "The system is working: this page refreshes on its own.");
    bannerGlyph = "●"; bannerBg = C.muteBg; bannerColor = C.mute;
  } else if (st.blocking > 0) {
    bannerTitle = L("Richiede revisione umana", "Needs human review");
    bannerDetail = st.open.length + L(" elementi in coda, di cui ", " items in the queue, of which ") + st.blocking + L(" bloccante. L'export resta bloccato finché la segnalazione non è risolta.", " blocking. Export stays locked until the issue is resolved.");
    bannerGlyph = "!"; bannerBg = C.warnBg; bannerColor = C.warn;
  } else if (st.open.length > 0) {
    bannerTitle = L("Revisione in corso", "Review in progress");
    bannerDetail = st.open.length + L(" elementi ancora da rivedere. L'export è possibile ma dichiarerà le lacune aperte.", " items still to review. Export is possible but will declare the open gaps.");
    bannerGlyph = "●"; bannerBg = C.warnBg; bannerColor = C.warn;
  } else {
    bannerTitle = L("Run completo — pronto per l'export", "Run complete — ready to export");
    bannerDetail = L("Tutti gli elementi della coda sono stati gestiti.", "All queue items have been handled.");
    bannerGlyph = "✓"; bannerBg = C.okBg; bannerColor = C.ok;
  }

  const nodesCount = run.nodes.length;
  const relsCount = run.edges.length;
  const complete = run.triplets.filter((t) => t.complete && !t.ambiguous).length;
  const counts = (run.report && run.report.counts) || {};
  const metrics = run.status.metrics || {};

  const nav = (view) => on(() => { S.view = view; S.selected = null; render(); });
  const kpi = (value, label, color, go) => `
    <button data-h="${go}" style="flex:1;min-width:104px;text-align:left;border:none;background:transparent;padding:0;font-family:inherit;cursor:pointer;">
      <div class="tnum" style="font-size:19px;font-weight:600;letter-spacing:-0.02em;white-space:nowrap;color:${color || "#22211D"};">${value}</div>
      <div style="font-size:11.5px;color:#6E6A61;line-height:1.4;margin-top:2px;">${label}</div>
    </button>`;

  const groups = [
    [L("Estratto dal manuale", "Extracted from the manual"), L("quello che il sistema ha trovato nelle pagine selezionate", "what the system found in the selected pages"), [
      kpi(nodesCount, L("informazioni trovate (nodi)", "pieces of information found (nodes)"), null, nav("graph")),
      kpi(relsCount, L("collegamenti tra loro", "connections between them"), null, nav("graph")),
      kpi(complete + L(" di ", " of ") + run.triplets.length, L("catene sintomo → guasto → rimedio complete", "complete symptom → failure → remedy chains"), null, nav("graph")),
    ]],
    [L("Controllo di affidabilità", "Confidence check"), L("ogni informazione estratta riceve un punteggio automatico", "every extracted item gets an automatic score"), [
      kpi(counts.auto_approve ?? "—", L("approvate in automatico", "approved automatically"), C.ok, nav("quality")),
      kpi(counts.human_review ?? "—", L("da verificare a mano (operatore)", "to verify by hand (operator)"), C.warn, nav("quality")),
      kpi(counts.auto_reject ?? "—", L("scartate in automatico", "discarded automatically"), C.danger, nav("quality")),
    ]],
    [L("Da fare per chiudere", "To do before closing"), L("cosa manca prima di poter esportare il grafo", "what is missing before the graph can be exported"), [
      kpi(st.gaps, L("catene diagnostiche incomplete (lacune)", "incomplete diagnostic chains (gaps)"), st.gaps ? C.brown : C.ok, nav("review")),
      kpi(st.open.length, L("segnalazioni da gestire nel Review Center", "items to handle in the Review Center"), st.open.length ? C.warn : C.ok, nav("review")),
      kpi(st.fieldsMissing, L("campi da compilare a mano", "fields to fill in by hand"), st.fieldsMissing ? C.warn : C.ok, nav("fields")),
    ]],
    [L("Elaborazione automatica", "Automatic processing"), L("tempo e costo del lavoro fatto dal sistema prima del tuo intervento", "time and cost of the work the system did before your input"), [
      kpi(fmtDuration(metrics.duration_seconds), L("durata dell'estrazione automatica", "duration of the automatic extraction"), null, nav("dashboard")),
      kpi(metrics.estimated_cost_usd != null ? "$ " + Number(metrics.estimated_cost_usd).toFixed(2) : "—", L("costo stimato dei modelli", "estimated model cost"), null, nav("dashboard")),
    ]],
  ].map(([title, sub, items]) => `
    <div class="card" style="padding:14px 18px;">
      <div class="kicker">${title}</div>
      <div style="font-size:11.5px;color:#A5A196;margin-top:2px;line-height:1.4;">${sub}</div>
      <div style="display:flex;gap:16px;margin-top:12px;flex-wrap:wrap;">${items.join("")}</div>
    </div>`).join("");

  const agentLabels = {
    scoping_agent: L("Selezione pagine", "Page selection"), ontology_draft_agent: L("Bozza ontologia", "Ontology draft"),
    extraction_agent: L("Estrazione", "Extraction"), validation_agent: L("Validazione", "Validation"),
    coverage_agent: L("Copertura", "Coverage"), grounding_agent: L("Verifica citazioni", "Citation check"),
    conflict_resolution_agent: L("Duplicati", "Duplicates"), refiner_agent: L("Rifinitura", "Refinement"),
    confidence: L("Affidabilità", "Confidence"), review_queue: L("Coda di verifica", "Review queue"),
    Operator: L("Operatore", "Operator"), export: "Export",
  };
  const traceRows = run.trace.slice(-40).map((t) => `
    <div style="display:grid;grid-template-columns:170px 1fr auto;gap:12px;align-items:baseline;padding:9px 20px;border-top:1px solid rgba(0,0,0,0.05);">
      <span class="mono" style="font-size:11.5px;color:#6E6A61;">${esc(agentLabels[t.agent] || t.agent)}</span>
      <span style="font-size:12.5px;color:#3A3934;line-height:1.5;">${esc(t.decision)}
        ${t.handoff ? `<span style="margin-left:8px;font-size:10.5px;font-weight:600;color:#9A8352;background:rgba(194,163,107,0.15);padding:1px 7px;border-radius:99px;">handoff umano</span>` : ""}
        ${t.retries ? `<span style="margin-left:8px;font-size:10.5px;color:#8A867D;">retry ×${t.retries}</span>` : ""}
      </span>
      <span class="tnum" style="font-size:11px;color:#B5B1A6;white-space:nowrap;">${esc(t.meta)}</span>
    </div>`).join("");

  return `
  <div style="max-width:960px;margin:0 auto;padding:26px 32px 40px;">
    <div class="card" style="display:flex;align-items:center;gap:16px;padding:18px 22px;">
      <div style="width:38px;height:38px;flex:none;border-radius:50%;background:${bannerBg};display:flex;align-items:center;justify-content:center;font-size:17px;color:${bannerColor};font-weight:600;">${bannerGlyph}</div>
      <div style="flex:1;min-width:0;">
        <div class="serif" style="font-size:18px;font-weight:600;">${esc(bannerTitle)}</div>
        <div style="font-size:13px;color:#55524B;margin-top:2px;line-height:1.5;">${esc(bannerDetail)}</div>
        ${running ? `<div class="tnum" id="kg-live-tick" style="font-size:11.5px;color:#8A867D;margin-top:4px;"></div>` : ""}
      </div>
      ${bannerCta}
      ${run.isLive && phase === "ontology_draft" ? `<button class="btn-primary" style="--accent:${ACCENT};padding:9px 18px;" data-h="${on(async () => {
        if (S.extracting) return;
        S.extracting = true; render();
        try {
          await chatAction(run.pdfId, "run_extraction");
          toast(L("Estrazione avviata — le fasi successive procedono da sole.", "Extraction started — the next phases run on their own."));
          setTimeout(() => refreshRun(true), 1500);
        } catch (e) { toast(e.message, true); }
        S.extracting = false; render();
      })}" ${S.extracting ? "disabled" : ""}>${S.extracting ? L("Avvio…", "Starting…") : L("Avvia estrazione", "Start extraction")}</button>` : ""}
      ${!running && !awaitingOperator ? `<button class="btn-primary" style="--accent:${ACCENT};padding:9px 18px;" data-h="${nav("review")}">${L("Apri Review Center", "Open Review Center")}</button>` : ""}
    </div>
    <div class="card" style="display:flex;align-items:center;margin-top:22px;padding:16px 20px;overflow-x:auto;">${stages}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:22px;">${groups}</div>
    <div class="card" style="margin-top:22px;overflow:hidden;">
      <div class="kicker" style="padding:14px 20px 10px;">${L("Diario del run", "Run log")}</div>
      ${traceRows || `<div style="padding:16px 20px;font-size:12.5px;color:#8A867D;border-top:1px solid rgba(0,0,0,0.05);">${L("Nessun passo registrato finora.", "No steps recorded yet.")}</div>`}
    </div>
  </div>`;
}

/* ── Scoping ── */
function viewScoping() {
  const run = S.run;
  if (!run) return viewRuns();
  const cut = run.cutPlan;
  if (!cut) {
    return `<div style="max-width:960px;margin:0 auto;padding:26px 32px;">
      <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 8px;">${L("Selezione delle pagine", "Page selection")}</h1>
      <p style="font-size:13px;color:#55524B;">${L("Lo scoping non è ancora stato eseguito per questa sessione.", "Scoping has not run yet for this session.")}</p></div>`;
  }
  const kept = (cut.pages_to_keep || []).length;
  const total = cut.total_pages || run.totalPages || 0;
  const srcMeta = { llm: { c: "#6E7B8A", bg: "rgba(110,123,138,0.12)" }, keyword: { c: C.brown, bg: C.brownBg }, rule: { c: C.mute, bg: C.muteBg }, user: { c: C.ok, bg: C.okBg } };
  const rows = run.sections.map((s, i) => {
    const sm = srcMeta[s.source] || srcMeta.rule;
    return `
    <button class="row-hover" data-h="${on(() => { S.selected = { t: "section", id: i }; render(); })}" style="display:grid;grid-template-columns:1fr 130px 96px 1fr;gap:12px;align-items:baseline;width:100%;padding:12px 20px;border:none;border-top:1px solid rgba(0,0,0,0.05);background:transparent;text-align:left;">
      <span style="font-size:13px;font-weight:500;">${esc(s.name)}</span>
      <span class="tnum" style="font-size:12.5px;color:#55524B;">${esc(s.pages)}</span>
      <span class="pill" style="font-size:11px;color:${sm.c};background:${sm.bg};padding:2px 8px;justify-self:start;">${esc(s.source)}</span>
      <span style="font-size:12px;color:#8A867D;line-height:1.5;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${esc(s.why)}</span>
    </button>`;
  }).join("");
  const approved = !!run.pipeline.ontology;
  const canApprove = run.isLive && !approved;
  const approveBtn = canApprove ? `
    <button class="btn-primary" style="--accent:${ACCENT};" data-h="${on(async () => {
      try { await chatAction(run.pdfId, "approve_cut_plan"); toast(L("Selezione approvata — parte la bozza dell'ontologia.", "Selection approved — ontology draft starting.")); setTimeout(() => refreshRun(true), 1500); }
      catch (e) { toast(e.message, true); }
    })}">${L("Approva selezione e continua", "Approve selection and continue")}</button>` : `
    <button class="btn-ghost" disabled style="color:#B5B1A6;">${L("Modifica selezione", "Edit selection")}</button>
    <span style="font-size:11.5px;color:#A5A196;">${L("la modifica richiede un nuovo run di scoping — la fase è già stata approvata e usata dall'estrazione", "changing it requires a new scoping run — the phase was already approved and used by extraction")}</span>`;

  return `
  <div style="max-width:960px;margin:0 auto;padding:26px 32px 40px;">
    <div style="display:flex;align-items:baseline;gap:12px;">
      <h1 class="serif" style="font-size:22px;font-weight:600;margin:0;">${L("Selezione delle pagine", "Page selection")}</h1>
      <span style="font-size:12.5px;color:#8A867D;">${kept}${L(" di ", " of ")}${total}${L(" pagine conservate", " pages kept")}${total ? " · " + Math.round((kept / total) * 100) + "%" : ""}</span>
      <span style="flex:1;"></span>
      ${approved ? `<span style="font-size:12px;font-weight:600;color:#7A9B7E;">${L("✓ Selezione approvata", "✓ Selection approved")}</span>` : ""}
    </div>
    <p style="font-size:13px;color:#55524B;line-height:1.55;margin:8px 0 20px;max-width:640px;">${L("Il sistema ha individuato da solo le sezioni utili alla diagnostica — dall'indice e dalle parole chiave — e ha allineato i numeri di pagina a quelli stampati sul manuale. Ogni sezione riporta la ragione per cui è stata tenuta.", "The system found the diagnostic sections on its own — from the table of contents and keywords — and aligned page numbers to the ones printed in the manual. Each section shows why it was kept.")}</p>
    <div class="card" style="overflow:hidden;">
      <div class="kicker" style="display:grid;grid-template-columns:1fr 130px 96px 1fr;gap:12px;padding:10px 20px;">
        <span>${L("Sezione", "Section")}</span><span>${L("Pagine PDF", "PDF pages")}</span><span>${L("Fonte", "Source")}</span><span>${L("Perché è stata tenuta", "Why it was kept")}</span>
      </div>
      ${rows || `<div style="padding:16px 20px;font-size:12.5px;color:#8A867D;border-top:1px solid rgba(0,0,0,0.05);">${L("Nessuna sezione (documento breve: letto per intero).", "No sections (short document: read in full).")}</div>`}
    </div>
    <div style="display:flex;align-items:center;gap:10px;margin-top:16px;">${approveBtn}</div>
  </div>`;
}

/* ── Grafo: layout ── */
function graphLayout(mode, run) {
  const key = mode;
  if (layoutCache[key]) return layoutCache[key];
  const nodes = run.nodes, edges = run.edges;
  const pos = {};
  if (mode === "catene") {
    const cols = { ErrorCode: 80, Symptom: 330, FailureMode: 580, CorrectiveAction: 830, Component: 1050, Asset: 1050 };
    const byType = {};
    nodes.forEach((n) => { (byType[n.type] = byType[n.type] || []).push(n); });
    Object.entries(byType).forEach(([type, arr]) => {
      const gap = 540 / (arr.length + 1);
      arr.forEach((n, i) => { pos[n.id] = { x: cols[type] || 550, y: 40 + gap * (i + 1) }; });
    });
    for (let s = 0; s < 4; s++) {
      Object.values(byType).forEach((arr) => {
        arr.forEach((n) => {
          const nb = [];
          edges.forEach((e) => { if (e.s === n.id && pos[e.t]) nb.push(pos[e.t].y); if (e.t === n.id && pos[e.s]) nb.push(pos[e.s].y); });
          pos[n.id].bc = nb.length ? nb.reduce((a, b) => a + b, 0) / nb.length : pos[n.id].y;
        });
        arr.sort((a, b) => pos[a.id].bc - pos[b.id].bc);
        const gap = Math.min(56, 540 / (arr.length + 1));
        const start = 310 - gap * (arr.length - 1) / 2;
        arr.forEach((n, i) => { pos[n.id].y = start + gap * i; });
      });
    }
  } else {
    let seed = 1234;
    const rand = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    const centers = { Symptom: [330, 200], FailureMode: [550, 330], CorrectiveAction: [800, 210], ErrorCode: [290, 470], Component: [810, 480], Asset: [550, 90] };
    nodes.forEach((n) => { const c = centers[n.type] || [550, 310]; pos[n.id] = { x: c[0] + (rand() - 0.5) * 240, y: c[1] + (rand() - 0.5) * 190 }; });
    const ids = nodes.map((n) => n.id);
    for (let it = 0; it < 300; it++) {
      const t = 1 - it / 300;
      for (let i = 0; i < ids.length; i++) {
        for (let j = i + 1; j < ids.length; j++) {
          const a = pos[ids[i]], b = pos[ids[j]];
          let dx = a.x - b.x, dy = a.y - b.y;
          let d2 = dx * dx + dy * dy; if (!d2) { dx = 1; d2 = 1; }
          if (d2 < 64000) {
            const d = Math.sqrt(d2), f = Math.min(10, 2400 * t / d2);
            dx = dx / d * f; dy = dy / d * f;
            a.x += dx; a.y += dy; b.x -= dx; b.y -= dy;
          }
        }
      }
      edges.forEach((e) => {
        const a = pos[e.s], b = pos[e.t];
        if (!a || !b) return;
        const dx = b.x - a.x, dy = b.y - a.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 1;
        const f = (d - 115) * 0.015 * t;
        a.x += dx / d * f; a.y += dy / d * f;
        b.x -= dx / d * f; b.y -= dy / d * f;
      });
      nodes.forEach((n) => {
        const c = centers[n.type] || [550, 310], p = pos[n.id];
        p.x += (c[0] - p.x) * 0.01 * t; p.y += (c[1] - p.y) * 0.01 * t;
        p.x = Math.max(50, Math.min(1050, p.x)); p.y = Math.max(40, Math.min(580, p.y));
      });
    }
  }
  layoutCache[key] = pos;
  return pos;
}

function viewGraph() {
  const run = S.run;
  if (!run) return viewRuns();
  if (!run.nodes.length) {
    return `<div style="max-width:960px;margin:0 auto;padding:26px 32px;">
      <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 8px;">${L("Ontologia estratta", "Extracted ontology")}</h1>
      <p style="font-size:13px;color:#55524B;">${L("Il grafo non è ancora disponibile: l'estrazione non è arrivata alla bozza dell'ontologia.", "The graph is not available yet: extraction has not reached the ontology draft.")}</p></div>`;
  }
  const G = S.graph;
  const layout = graphLayout(G.mode, run);
  const shown = run.nodes.filter((n) => G.showComp || n.type !== "Component");
  const shownIds = new Set(shown.map((n) => n.id));
  const dragPos = (G.pos && G.pos[G.mode]) || {};
  const P = (id) => dragPos[id] || layout[id] || { x: 550, y: 310 };
  const selId = S.selected && S.selected.t === "gnode" ? S.selected.id : null;
  const nbr = new Set();
  if (selId) run.edges.forEach((e) => { if (e.s === selId) nbr.add(e.t); if (e.t === selId) nbr.add(e.s); });
  const deg = {};
  run.edges.forEach((e) => { deg[e.s] = (deg[e.s] || 0) + 1; deg[e.t] = (deg[e.t] || 0) + 1; });
  const queueBy = {};
  run.queue.forEach((it) => { if (!queueBy[it.target_id]) queueBy[it.target_id] = it; });
  const ambigEdges = new Set();
  run.queue.filter((q) => q.kind === "ambiguous_multi_cause_symptom").forEach((q) => (q.causes || []).forEach((cz) => ambigEdges.add(q.target_id + ">" + cz.id)));

  const edgesSvg = run.edges.filter((e) => shownIds.has(e.s) && shownIds.has(e.t)).map((e) => {
    const a = P(e.s), b = P(e.t);
    const touches = selId && (e.s === selId || e.t === selId);
    const ambig = e.rel === "MAY_INDICATE" && ambigEdges.has(e.s + ">" + e.t);
    const d = G.mode === "catene"
      ? `M ${a.x} ${a.y} C ${(a.x + b.x) / 2} ${a.y}, ${(a.x + b.x) / 2} ${b.y}, ${b.x} ${b.y}`
      : `M ${a.x} ${a.y} L ${b.x} ${b.y}`;
    return `<path d="${d}" fill="none" stroke="${touches ? ACCENT : ambig ? "#9A8352" : "#22211D"}" stroke-width="${touches ? 2.2 : 1.3}" stroke-dasharray="${ambig ? "5 4" : "none"}" opacity="${selId ? (touches ? 0.85 : 0.06) : (ambig ? 0.55 : 0.16)}"></path>`;
  }).join("");

  const nodesSvg = shown.map((n) => {
    const p = P(n.id);
    const qi = queueBy[n.id];
    const r = Math.min(17, 8 + (deg[n.id] || 0) * 1.4);
    const isSel = n.id === selId;
    const dim = selId && !isSel && !nbr.has(n.id);
    const conf = n.conf == null ? 0.85 : n.conf;
    const fill = G.colorBy === "conf"
      ? (conf >= 0.8 ? "#7A9B7E" : conf >= 0.45 ? "#C2A36B" : "#B4543E")
      : (TYPE_COLORS[n.type] || "#8C8474");
    let stroke = "#F7F6F2", sw = 1.5, dash = "none";
    if (qi) { stroke = qi.severity === "blocking" || qi.severity === "reject" ? "#B4543E" : "#9A8352"; sw = 2.2; dash = "3 3"; }
    if (isSel) { stroke = "#22211D"; sw = 2.8; dash = "none"; }
    const shortLabel = n.label.length > 24 ? n.label.slice(0, 23) + "…" : n.label;
    const tip = typeLabel(n.type) + L(" · affidabilità ", " · confidence ") + fmtConf(n.conf) + (qi ? L(" · in coda di verifica", " · in review queue") : "");
    return `
    <g transform="translate(${p.x} ${p.y})" opacity="${dim ? 0.22 : 1}" data-gnode="${esc(n.id)}" style="cursor:pointer;">
      <circle r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-dasharray="${dash}"></circle>
      <text y="${r + 13}" text-anchor="middle" style="font-size:11px;font-weight:500;fill:#55524B;paint-order:stroke;stroke:#FBFAF7;stroke-width:3px;pointer-events:none;">${esc(shortLabel)}</text>
      <title>${esc(tip)}</title>
    </g>`;
  }).join("");

  const setG = (patch) => { Object.assign(S.graph, patch); render(); };
  const seg = (defs, cur, key) => defs.map(([val, lbl]) => `
    <button data-h="${on(() => setG({ [key]: val }))}" style="font-size:12px;font-weight:500;padding:5px 12px;border-radius:7px;border:none;font-family:inherit;background:${cur === val ? "#FFFFFF" : "transparent"};color:${cur === val ? "#22211D" : "#6E6A61"};">${lbl}</button>`).join("");

  const legend = (G.colorBy === "conf"
    ? [
        { color: "#7A9B7E", label: L("Affidabilità ≥ 0,80", "Confidence ≥ 0.80"), count: shown.filter((n) => (n.conf ?? 0.85) >= 0.8).length },
        { color: "#C2A36B", label: L("Da rivedere (0,45–0,80)", "To review (0.45–0.80)"), count: shown.filter((n) => (n.conf ?? 0.85) >= 0.45 && (n.conf ?? 0.85) < 0.8).length },
        { color: "#B4543E", label: L("Sotto soglia (< 0,45)", "Below threshold (< 0.45)"), count: shown.filter((n) => (n.conf ?? 0.85) < 0.45).length },
      ]
    : Object.keys(TYPE_COLORS).filter((t) => shown.some((n) => n.type === t))
        .map((t) => ({ color: TYPE_COLORS[t], label: typeLabel(t), count: shown.filter((n) => n.type === t).length }))
  ).map((lg) => `
    <div style="display:flex;align-items:center;gap:8px;padding:2px 0;">
      <span style="width:10px;height:10px;flex:none;border-radius:50%;background:${lg.color};"></span>
      <span style="flex:1;font-size:11.5px;color:#3A3934;">${esc(lg.label)}</span>
      <span class="tnum" style="font-size:11px;color:#B5B1A6;margin-left:8px;">${lg.count}</span>
    </div>`).join("");

  const maxNodes = Math.max(...run.nodeTypes.map(([, c]) => c), 1);
  const nodeTypeRows = run.nodeTypes.map(([type, count]) => `
    <div style="display:flex;align-items:center;gap:10px;padding:5px 0;">
      <span class="mono" style="font-size:12px;color:#3A3934;width:140px;">${esc(type)}</span>
      <span style="flex:1;height:5px;border-radius:3px;background:rgba(0,0,0,0.06);overflow:hidden;"><span style="display:block;height:100%;width:${Math.round((count / maxNodes) * 100)}%;background:#C9C4B4;border-radius:3px;"></span></span>
      <span class="tnum" style="font-size:12.5px;font-weight:600;width:26px;text-align:right;">${count}</span>
    </div>`).join("");
  const relTypeRows = run.relTypes.map(([type, desc, count]) => `
    <div style="display:flex;align-items:baseline;gap:10px;padding:5px 0;">
      <span class="mono" style="font-size:11.5px;color:#3A3934;width:140px;">${esc(type)}</span>
      <span style="flex:1;font-size:11.5px;color:#8A867D;">${esc(desc)}</span>
      <span class="tnum" style="font-size:12.5px;font-weight:600;">${count}</span>
    </div>`).join("");

  const tripletRows = run.triplets.map((t) => {
    const dot = !t.complete ? C.danger : t.ambiguous ? C.warn : t.weak ? C.warn : C.ok;
    const chainLabel = !t.complete ? L("catena interrotta", "broken chain") : t.ambiguous ? L("ambiguità da confermare", "ambiguity to confirm") : t.weak ? L("catena debole", "weak chain") : L("completa", "complete");
    const chainColor = !t.complete ? C.danger : (t.ambiguous || t.weak) ? C.warn : C.ok;
    return `
    <button class="row-hover" data-h="${on(() => { S.selected = { t: "triplet", id: t.id }; render(); })}" style="display:flex;align-items:center;gap:12px;width:100%;padding:12px 20px;border:none;border-top:1px solid rgba(0,0,0,0.05);background:transparent;text-align:left;">
      <span style="width:7px;height:7px;flex:none;border-radius:50%;background:${dot};"></span>
      <span style="flex:1;min-width:0;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;">
        <span style="font-size:13px;font-weight:500;">${esc(t.symptom)}</span>
        <span style="font-size:11px;color:#B5B1A6;">→</span>
        <span style="font-size:12.5px;color:#55524B;">${esc(t.fm)}</span>
        <span style="font-size:11px;color:#B5B1A6;">→</span>
        <span style="font-size:12.5px;color:#55524B;">${esc(t.ca)}</span>
      </span>
      <span style="flex:none;font-size:11px;font-weight:600;color:${chainColor};white-space:nowrap;">${chainLabel}</span>
      <span class="tnum" style="flex:none;font-size:11px;color:#8A867D;width:64px;text-align:right;">conf. ${fmtConf(t.conf)}</span>
    </button>`;
  }).join("");

  const validated = run.triplets.filter((t) => t.complete && !t.ambiguous && !t.weak).length;
  return `
  <div style="max-width:960px;margin:0 auto;padding:26px 32px 40px;">
    <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 16px;">${L("Ontologia estratta", "Extracted ontology")}</h1>
    <div class="card" style="overflow:hidden;margin-bottom:24px;">
      <div style="display:flex;align-items:center;gap:10px;padding:11px 14px;border-bottom:1px solid rgba(0,0,0,0.06);flex-wrap:wrap;">
        <div style="display:flex;gap:2px;background:rgba(0,0,0,0.05);border-radius:9px;padding:2px;">${seg([["rete", L("Rete", "Network")], ["catene", L("Catene per livelli", "Layered chains")]], G.mode, "mode")}</div>
        <div style="display:flex;gap:2px;background:rgba(0,0,0,0.05);border-radius:9px;padding:2px;">${seg([["tipo", L("Per tipo", "By type")], ["conf", L("Per affidabilità", "By confidence")]], G.colorBy, "colorBy")}</div>
        <button data-h="${on(() => setG({ showComp: !G.showComp }))}" style="font-size:12px;font-weight:500;padding:6px 12px;border-radius:99px;border:1px solid rgba(0,0,0,0.10);font-family:inherit;background:${G.showComp ? "#3A3934" : "#FFFFFF"};color:${G.showComp ? "#FFFFFF" : "#55524B"};">${L("Componenti", "Components")}${G.showComp ? " ✓" : ""}</button>
        <span style="flex:1;"></span>
        <div style="display:flex;align-items:center;gap:4px;">
          <button class="btn-ghost" style="width:26px;height:26px;padding:0;font-size:14px;line-height:1;" data-h="${on(() => setG({ zoom: Math.max(0.5, G.zoom / 1.25) }))}">−</button>
          <span class="tnum" style="font-size:11.5px;color:#8A867D;width:42px;text-align:center;">${Math.round(G.zoom * 100)}%</span>
          <button class="btn-ghost" style="width:26px;height:26px;padding:0;font-size:14px;line-height:1;" data-h="${on(() => setG({ zoom: Math.min(2.6, G.zoom * 1.25) }))}">+</button>
          <button class="btn-ghost" style="margin-left:4px;font-size:11.5px;" data-h="${on(() => setG({ zoom: 1, panX: 0, panY: 0, pos: {} }))}">${L("Reimposta", "Reset")}</button>
        </div>
      </div>
      <div style="position:relative;height:560px;background:#FBFAF7;user-select:none;">
        <svg id="gsvg" width="100%" height="100%" viewBox="0 0 1100 620" preserveAspectRatio="xMidYMid meet" style="display:block;cursor:grab;">
          <g transform="translate(${550 - 550 * G.zoom + G.panX} ${310 - 310 * G.zoom + G.panY}) scale(${G.zoom})">
            ${edgesSvg}${nodesSvg}
          </g>
        </svg>
        <div style="position:absolute;left:14px;bottom:14px;padding:11px 14px;border-radius:12px;background:rgba(255,255,255,0.93);box-shadow:0 1px 4px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.05);">
          <div class="kicker" style="font-size:10px;margin-bottom:6px;">${L("Legenda", "Legend")}</div>
          ${legend}
          <div style="margin-top:6px;padding-top:6px;border-top:1px solid rgba(0,0,0,0.06);">
            <div style="display:flex;align-items:center;gap:8px;padding:2px 0;">
              <span style="width:11px;height:11px;flex:none;border-radius:50%;border:2px dashed #9A8352;"></span>
              <span style="font-size:11px;color:#55524B;">${L("in coda di verifica", "in review queue")}</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;padding:2px 0;">
              <svg width="14" height="6" viewBox="0 0 14 6" style="flex:none;"><line x1="0" y1="3" x2="14" y2="3" stroke="#9A8352" stroke-width="1.5" stroke-dasharray="4 3"></line></svg>
              <span style="font-size:11px;color:#55524B;">${L("ambiguità da confermare", "ambiguity to confirm")}</span>
            </div>
          </div>
        </div>
        <div style="position:absolute;right:14px;bottom:14px;font-size:11px;color:#A5A196;background:rgba(255,255,255,0.85);padding:5px 10px;border-radius:8px;">${L("trascina per spostare · clic su un nodo per i dettagli", "drag to pan · click a node for details")}</div>
      </div>
    </div>

    <div style="display:flex;gap:24px;flex-wrap:wrap;">
      <div class="card" style="flex:1;min-width:280px;padding:16px 20px;">
        <div class="kicker" style="margin-bottom:10px;">${L("Nodi per tipo · ", "Nodes by type · ")}${run.nodes.length}</div>
        ${nodeTypeRows}
      </div>
      <div class="card" style="flex:1;min-width:280px;padding:16px 20px;">
        <div class="kicker" style="margin-bottom:10px;">${L("Relazioni per tipo · ", "Relations by type · ")}${run.edges.length}</div>
        ${relTypeRows}
      </div>
    </div>

    <div style="display:flex;align-items:baseline;gap:10px;margin:24px 0 10px;">
      <h2 style="font-size:14px;font-weight:600;margin:0;">${L("Catene diagnostiche · ", "Diagnostic chains · ")}${validated}${L(" validate", " validated")}</h2>
      <span style="font-size:12px;color:#8A867D;">Symptom → MAY_INDICATE → FailureMode → RESOLVED_BY → CorrectiveAction</span>
    </div>
    <div class="card" style="overflow:hidden;">${tripletRows || `<div style="padding:16px 20px;font-size:12.5px;color:#8A867D;">${L("Nessuna catena estratta.", "No chains extracted.")}</div>`}</div>
  </div>`;
}

/* ── Review Center ── */
function viewReview(st) {
  const run = S.run;
  if (!run) return viewRuns();
  const visible = st.visible;
  const filterDefs = [
    ["all", L("Tutti", "All"), visible.length],
    ["blocking", L("Bloccanti", "Blocking"), visible.filter((q) => q.severity === "blocking").length],
    ["open", L("Lacune", "Gaps"), visible.filter((q) => q.severity === "open").length],
    ["ambiguity", L("Ambiguità", "Ambiguities"), visible.filter((q) => q.kind === "ambiguous_multi_cause_symptom").length],
    ["lowconf", L("Bassa conf.", "Low conf."), visible.filter((q) => q.kind === "low_confidence").length],
    ["advisory", "Advisory", visible.filter((q) => q.severity === "advisory").length],
    ["done", L("Gestiti", "Handled"), st.decided.length],
  ];
  const filters = filterDefs.map(([id, lbl, count]) => `
    <button data-h="${on(() => { S.filter = id; render(); })}" style="font-size:11.5px;font-weight:500;padding:5px 11px;border-radius:99px;border:none;font-family:inherit;background:${S.filter === id ? "#3A3934" : "rgba(0,0,0,0.05)"};color:${S.filter === id ? "#FFFFFF" : "#6E6A61"};white-space:nowrap;">${lbl} ${count}</button>`).join("");

  const q = S.search.toLowerCase();
  let filtered = visible.filter((item) => {
    if (S.filter === "blocking") return item.severity === "blocking";
    if (S.filter === "open") return item.severity === "open";
    if (S.filter === "ambiguity") return item.kind === "ambiguous_multi_cause_symptom";
    if (S.filter === "lowconf") return item.kind === "low_confidence";
    if (S.filter === "advisory") return item.severity === "advisory";
    if (S.filter === "done") return !!getDec(item);
    return true;
  });
  if (q) filtered = filtered.filter((item) => (item.label + " " + item.target_id).toLowerCase().includes(q));
  const sevOrder = { blocking: 0, open: 1, reject: 2, review: 3, advisory: 4 };
  filtered = filtered.slice().sort((a, b) => {
    const da = getDec(a) ? 1 : 0, db = getDec(b) ? 1 : 0;
    if (da !== db) return da - db;
    return (sevOrder[a.severity] ?? 9) - (sevOrder[b.severity] ?? 9);
  });

  const selKey = S.selected && S.selected.t === "queue" ? S.selected.id : null;
  const KL = kindLabels(), SM = sevMeta(), DM = decMeta();
  const rows = filtered.map((item) => {
    const dec = getDec(item);
    const sv = SM[item.severity] || SM.advisory;
    const key = qKey(item);
    return `
    <button class="row-hover" data-h="${on(() => { S.selected = { t: "queue", id: key }; render(); })}" style="display:grid;grid-template-columns:104px 1fr 210px 100px;gap:12px;align-items:center;width:100%;padding:11px 20px;border:none;border-top:1px solid rgba(0,0,0,0.05);font-family:inherit;text-align:left;background:${selKey === key ? "#FBF6F2" : "transparent"};opacity:${dec ? 0.55 : 1};">
      <span class="pill" style="font-size:10.5px;color:${sv.color};background:${sv.bg};padding:3px 8px;text-align:center;overflow:hidden;text-overflow:ellipsis;">${sv.label}</span>
      <span style="min-width:0;">
        <span style="display:block;font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(item.label)}</span>
        <span style="display:block;font-size:11px;color:#8A867D;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(KL[item.kind] || item.kind)} · <span class="mono">${esc(item.target_type)} · ${esc(item.target_id)}</span></span>
      </span>
      <span style="font-size:11.5px;color:#8A867D;line-height:1.45;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${esc(item.reason)}</span>
      <span style="text-align:right;">
        ${item.score != null ? `<span class="tnum" style="display:block;font-size:11.5px;color:#6E6A61;">score ${Number(item.score).toFixed(2)}</span>` : ""}
        ${dec ? `<span style="display:block;font-size:11px;font-weight:600;color:${(DM[dec.status] || DM.ignored).color};">${(DM[dec.status] || DM.ignored).label}</span>` : ""}
      </span>
    </button>`;
  }).join("");

  return `
  <div style="max-width:960px;margin:0 auto;padding:26px 32px 40px;">
    <div style="display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;">
      <h1 class="serif" style="font-size:22px;font-weight:600;margin:0;">Review Center</h1>
      <span style="font-size:12.5px;color:#8A867D;">${L("coda prioritaria: bloccanti → lacune → auto-rifiutati → revisione → advisory", "priority queue: blocking → gaps → auto-rejected → review → advisory")}</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin:16px 0 14px;flex-wrap:wrap;">
      ${filters}
      <span style="flex:1;"></span>
      <input value="${esc(S.search)}" data-h="${on((e) => { S.search = e.target.value; render(); })}" data-evt="change" placeholder="${L("Cerca per id o nome…", "Search by id or name…")}" style="font-size:12.5px;padding:6px 12px;border-radius:9px;border:1px solid rgba(0,0,0,0.10);background:#FFFFFF;width:200px;">
    </div>
    ${rows ? `<div class="card" style="overflow:hidden;">${rows}</div>` : `
      <div style="padding:36px 20px;text-align:center;border-radius:14px;background:#FFFFFF;box-shadow:0 0 0 1px rgba(0,0,0,0.04);">
        <div style="font-size:14px;font-weight:500;color:#55524B;">${q ? L("Nessun elemento corrisponde a «" + esc(S.search) + "».", "Nothing matches “" + esc(S.search) + "”.") : S.filter === "done" ? L("Nessun elemento gestito finora.", "Nothing handled yet.") : L("Nessun elemento in questa vista — la coda è pulita.", "Nothing in this view — the queue is clean.")}</div>
      </div>`}
  </div>`;
}

/* ── Qualità ── */
function viewQuality() {
  const run = S.run;
  if (!run) return viewRuns();
  const report = run.report;
  const counts = (report && report.counts) || {};
  const thetaHigh = report ? report.theta_high : 0.8;
  const thetaLow = report ? report.theta_low : 0.45;
  const cells = [
    { glyph: "✓", bg: C.okBg, color: C.ok, count: counts.auto_approve ?? 0, label: L("Auto-approvati", "Auto-approved"), sub: L("score ≥ " + thetaHigh + " — nessuna azione", "score ≥ " + thetaHigh + " — no action needed") },
    { glyph: "!", bg: C.warnBg, color: C.warn, count: counts.human_review ?? 0, label: L("Revisione umana", "Human review"), sub: thetaLow + " ≤ score < " + thetaHigh },
    { glyph: "×", bg: C.dangerBg, color: C.danger, count: counts.auto_reject ?? 0, label: L("Auto-rifiutati", "Auto-rejected"), sub: L("score < " + thetaLow + " — esclusi dall'export", "score < " + thetaLow + " — excluded from export") },
  ].map((cc) => `
    <div style="background:#FFFFFF;padding:16px 20px;">
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="width:20px;height:20px;border-radius:50%;background:${cc.bg};color:${cc.color};display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;">${cc.glyph}</span>
        <span class="tnum" style="font-size:22px;font-weight:600;letter-spacing:-0.02em;">${cc.count}</span>
      </div>
      <div style="font-size:12px;font-weight:500;color:#3A3934;margin-top:6px;">${cc.label}</div>
      <div style="font-size:11px;color:#8A867D;margin-top:1px;">${cc.sub}</div>
    </div>`).join("");

  const attention = (report && report.entries || []).filter((e) => e.classification !== "auto_approve");
  const classMeta = {
    auto_approve: { label: L("auto-approvato", "auto-approved"), color: C.ok, bg: C.okBg },
    human_review: { label: L("revisione umana", "human review"), color: C.warn, bg: C.warnBg },
    auto_reject: { label: L("auto-rifiutato", "auto-rejected"), color: C.danger, bg: C.dangerBg },
  };
  const rows = attention.map((e) => {
    const cm = classMeta[e.classification] || classMeta.human_review;
    const queueItem = run.queue.find((it) => it.target_id === e.node_id && it.kind === "low_confidence");
    const open = on(() => { S.selected = queueItem ? { t: "queue", id: qKey(queueItem) } : { t: "conf", id: e.node_id }; render(); });
    return `
    <button class="row-hover" data-h="${open}" style="display:grid;grid-template-columns:150px 1fr 120px 130px;gap:12px;align-items:center;width:100%;padding:11px 20px;border:none;border-top:1px solid rgba(0,0,0,0.05);background:transparent;font-family:inherit;text-align:left;">
      <span style="min-width:0;">
        <span class="mono" style="display:block;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(e.node_id)}</span>
        <span style="display:block;font-size:11px;color:#8A867D;">${esc(e.node_type)}</span>
      </span>
      <span style="font-size:11.5px;color:#8A867D;line-height:1.45;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;">${esc((e.reasons || []).join("; "))}</span>
      <span style="display:flex;align-items:center;gap:8px;">
        <span style="flex:1;height:4px;border-radius:2px;background:rgba(0,0,0,0.07);overflow:hidden;"><span style="display:block;height:100%;width:${Math.round(e.score * 100)}%;background:${e.score >= 0.8 ? C.ok : e.score >= 0.45 ? "#C2A36B" : C.danger};border-radius:2px;"></span></span>
        <span class="tnum" style="font-size:11.5px;color:#55524B;">${Number(e.score).toFixed(2)}</span>
      </span>
      <span class="pill" style="font-size:11px;color:${cm.color};background:${cm.bg};padding:3px 9px;text-align:center;">${cm.label}</span>
    </button>`;
  }).join("");

  return `
  <div style="max-width:960px;margin:0 auto;padding:26px 32px 40px;">
    <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 6px;">${L("Confidenza e qualità", "Confidence & quality")}</h1>
    <p style="font-size:13px;color:#55524B;line-height:1.55;margin:0 0 18px;max-width:680px;">${L("Ogni elemento estratto riceve un punteggio di affidabilità: sopra " + thetaHigh + " è approvato automaticamente, sotto " + thetaLow + " è scartato, nella fascia intermedia decide l'operatore.", "Every extracted element gets a confidence score: above " + thetaHigh + " it is approved automatically, below " + thetaLow + " it is discarded, in between the operator decides.")}</p>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;border-radius:14px;overflow:hidden;background:rgba(0,0,0,0.05);box-shadow:0 1px 2px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.04);">${cells}</div>
    <div style="display:flex;align-items:baseline;gap:10px;margin:24px 0 10px;">
      <h2 style="font-size:14px;font-weight:600;margin:0;">${L("Nodi che richiedono attenzione · ", "Nodes needing attention · ")}${attention.length}</h2>
      <span style="font-size:12px;color:#8A867D;">${L("i " + (counts.auto_approve ?? 0) + " auto-approvati non richiedono azione", "the " + (counts.auto_approve ?? 0) + " auto-approved need no action")}</span>
    </div>
    <div class="card" style="overflow:hidden;">${rows || `<div style="padding:16px 20px;font-size:12.5px;color:#8A867D;">${L("Nessun nodo sotto soglia.", "No nodes below threshold.")}</div>`}</div>
  </div>`;
}

/* ── Campi richiesti ── */
function viewFields(st) {
  const run = S.run;
  if (!run) return viewRuns();
  const rows = run.fields.map((f) => {
    const val = S.fieldAnswers[f.field_key] ?? "";
    const setVal = (v) => { S.fieldAnswers = { ...S.fieldAnswers, [f.field_key]: v }; render(); };
    const isEnum = (f.allowed_values || []).length > 0;
    return `
    <div class="card" style="padding:18px 22px;margin-bottom:12px;">
      <div style="display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;">
        <span style="font-size:14px;font-weight:600;">${esc(f.prompt)}</span>
        <span style="flex:1;"></span>
        <span class="mono" style="font-size:11px;color:#918D83;">${esc(f.target_type)}.${esc(f.target_id)} → ${esc(f.property_name)}</span>
      </div>
      <div style="font-size:12px;color:#8A867D;margin-top:3px;line-height:1.5;">${esc(f.reason)}</div>
      ${isEnum ? `
        <div style="display:flex;gap:6px;margin-top:12px;flex-wrap:wrap;">
          ${f.allowed_values.map((opt) => `<button data-h="${on(() => setVal(opt))}" style="font-size:12.5px;font-weight:500;padding:7px 16px;border-radius:9px;border:1px solid rgba(0,0,0,0.10);font-family:inherit;background:${val === opt ? "#3A3934" : "#FFFFFF"};color:${val === opt ? "#FFFFFF" : "#55524B"};">${esc(opt)}</button>`).join("")}
        </div>` : `
        <div style="display:flex;gap:8px;margin-top:12px;align-items:center;">
          <input value="${esc(val)}" data-h="${on((e) => setVal(e.target.value))}" data-evt="change" placeholder="${f.expected_type === "int" ? L("es. 30", "e.g. 30") : L("Scrivi la risposta…", "Type your answer…")}" style="flex:1;font-size:13px;padding:9px 12px;border-radius:9px;border:1px solid rgba(0,0,0,0.10);background:#FDFCFA;min-width:0;">
          ${f.suggested_value ? `<button class="btn-ghost" style="white-space:nowrap;padding:8px 13px;color:#55524B;" data-h="${on(() => setVal(f.suggested_value))}">${L("Usa suggerito", "Use suggested")}</button>` : ""}
        </div>
        ${f.suggested_value ? `<div style="font-size:11.5px;color:#A5A196;margin-top:6px;line-height:1.5;">${L("Suggerito:", "Suggested:")} <i>${esc(f.suggested_value)}</i></div>` : ""}`}
      ${val.trim() ? `<div style="font-size:11.5px;font-weight:600;color:#7A9B7E;margin-top:8px;">${L("✓ Risposta pronta", "✓ Answer ready")}</div>` : ""}
    </div>`;
  }).join("");

  const canSubmit = st.answered > 0 && !S.answersSent && run.isLive;
  const submit = on(async () => {
    if (!canSubmit) return;
    S.answersSent = true; render();
    try {
      for (const f of run.fields) {
        const v = (S.fieldAnswers[f.field_key] || "").trim();
        if (v) await chatAction(run.pdfId, "fill_required_field", { field_key: f.field_key, value: v });
      }
      toast(L("Risposte inviate — la validazione riparte e aggiorna la coda.", "Answers sent — validation restarts and updates the queue."));
      setTimeout(() => { S.fieldAnswers = {}; S.answersSent = false; refreshRun(true); }, 1200);
    } catch (e) { S.answersSent = false; toast(e.message, true); render(); }
  });

  return `
  <div style="max-width:760px;margin:0 auto;padding:26px 32px 40px;">
    <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 6px;">${L("Campi richiesti all'umano", "Fields required from you")}</h1>
    <p style="font-size:13px;color:#55524B;line-height:1.55;margin:0 0 18px;">${L("L'estrazione non ha potuto compilare questi campi obbligatori. Rispondi qui: le risposte completano il grafo e sbloccano l'export.", "Extraction could not fill these required fields. Answer here: your answers complete the graph and unlock the export.")}</p>
    ${rows || `<div class="card" style="padding:24px;font-size:13px;color:#55524B;">${L("Nessun campo richiesto — lo schema è completo.", "No fields required — the schema is complete.")}</div>`}
    ${run.fields.length ? `
    <div style="display:flex;align-items:center;gap:12px;margin-top:6px;">
      <button data-h="${submit}" ${canSubmit ? "" : "disabled"} style="font-size:13px;font-weight:600;padding:10px 20px;border-radius:10px;border:none;background:${canSubmit ? ACCENT : "rgba(0,0,0,0.08)"};color:${canSubmit ? "#FFFFFF" : "#A5A196"};">${L("Invia " + st.answered + " risposte", "Send " + st.answered + " answers")}</button>
      <span style="font-size:11.5px;color:#A5A196;line-height:1.5;">${!run.isLive ? L("Sessione in archivio: riavvia il backend con questa run per modificarla.", "Archived session: the backend must hold this run live to modify it.") : S.answersSent ? L("Risposte inviate — la validazione riparte da sola e aggiorna la coda.", "Answers sent — validation restarts on its own and updates the queue.") : L("Le risposte completano i campi mancanti e fanno ripartire la validazione.", "Your answers fill the missing fields and restart validation.")}</span>
    </div>` : ""}
  </div>`;
}

/* ── Export ── */
function viewExport(st) {
  const run = S.run;
  if (!run) return viewRuns();
  const phase = run.status.current_phase || "";
  const phaseReady = ["export", "completed"].includes(phase);
  let status, title, detail, glyph, iconBg, iconColor;
  if (!phaseReady) {
    status = "phase"; title = L("Estrazione non completata", "Extraction not finished");
    detail = L("La sessione è in fase «", "The session is in the “") + phaseLabel(phase) + L("»: l'export si abilita quando estrazione e validazione sono completate.", "” phase: export becomes available once extraction and validation are complete.");
    glyph = "!"; iconBg = C.warnBg; iconColor = C.warn;
  } else if (st.blocking > 0 || st.fieldsMissing > 0) {
    status = "blocked"; title = L("Export bloccato", "Export blocked");
    const parts = [];
    if (st.blocking) parts.push(st.blocking + L(" segnalazioni bloccanti", " blocking issues"));
    if (st.fieldsMissing) parts.push(st.fieldsMissing + L(" campi richiesti senza risposta", " required fields unanswered"));
    detail = L("Da risolvere prima: ", "To resolve first: ") + parts.join(L(" e ", " and ")) + L(". Il grafo non è ancora completo.", ". The graph is not complete yet.");
    glyph = "×"; iconBg = C.dangerBg; iconColor = C.danger;
  } else if (st.gaps > 0 || st.review > 0) {
    status = "warning"; title = L("Export possibile, con avvertenze", "Export possible, with warnings");
    detail = (st.gaps ? st.gaps + L(" lacune aperte", " open gaps") : "") + (st.gaps && st.review ? L(" e ", " and ") : "") + (st.review ? st.review + L(" elementi non ancora rivisti", " items not yet reviewed") : "") + L(" — saranno dichiarati nel file esportato, così chi lo usa a valle ne è consapevole.", " — they will be declared in the exported file, so downstream users are aware.");
    glyph = "!"; iconBg = C.warnBg; iconColor = C.warn;
  } else {
    status = "ok"; title = L("Pronto per l'export", "Ready to export");
    detail = L("Tutti i controlli superati: schema completo, nessuna lacuna aperta, coda di review vuota.", "All checks passed: schema complete, no open gaps, empty review queue.");
    glyph = "✓"; iconBg = C.okBg; iconColor = C.ok;
  }

  const grounding = run.status.grounding_summary || {};
  const weakG = grounding.weak_grounding_entities || 0;
  const nav = (view) => on(() => { S.view = view; S.selected = null; render(); });
  const mkCheck = (ok, warn, label, det, view) => `
    <button class="row-hover" data-h="${nav(view)}" style="display:flex;align-items:center;gap:12px;width:100%;padding:13px 20px;border:none;border-top:1px solid rgba(0,0,0,0.05);background:transparent;font-family:inherit;text-align:left;">
      <span style="width:20px;height:20px;flex:none;border-radius:50%;background:${ok ? C.okBg : warn ? C.warnBg : C.dangerBg};color:${ok ? C.ok : warn ? C.warn : C.danger};display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;">${ok ? "✓" : warn ? "!" : "×"}</span>
      <span style="flex:1;min-width:0;">
        <span style="display:block;font-size:13px;font-weight:500;">${label}</span>
        <span style="display:block;font-size:11.5px;color:#8A867D;margin-top:1px;line-height:1.45;">${det}</span>
      </span>
      <span style="font-size:11px;color:#B5B1A6;">${L("apri →", "open →")}</span>
    </button>`;
  const checks = [
    mkCheck(st.blocking === 0, false, L("Completezza dello schema", "Schema completeness"), st.blocking ? st.blocking + L(" segnalazioni bloccanti da schema", " blocking schema issues") : L("Nessuna segnalazione bloccante", "No blocking issues"), "review"),
    mkCheck(st.fieldsMissing === 0, false, L("Campi richiesti all'umano", "Fields required from you"), st.fieldsMissing ? st.fieldsMissing + L(" di ", " of ") + run.fields.length + L(" campi senza risposta", " fields unanswered") : L("Tutti i campi compilati", "All fields filled"), "fields"),
    mkCheck(st.gaps === 0, st.gaps > 0, L("Lacune strutturali", "Structural gaps"), st.gaps ? st.gaps + L(" catene diagnostiche non chiuse (dichiarate nel file esportato)", " diagnostic chains not closed (declared in the exported file)") : L("Tutte le catene diagnostiche sono chiuse", "All diagnostic chains are closed"), "review"),
    mkCheck(st.review === 0, st.review > 0, L("Coda di review", "Review queue"), st.review ? st.review + L(" elementi in attesa (bassa confidenza, ambiguità, advisory)", " items waiting (low confidence, ambiguities, advisory)") : L("Coda vuota", "Queue empty"), "review"),
    mkCheck(weakG === 0, weakG > 0, L("Verifica delle citazioni", "Citation check"), weakG ? weakG + L(" evidenze deboli o non trovate sulla pagina citata — penalità applicata", " weak or unlocated quotes on the cited page — penalty applied") : L("Tutte le citazioni verificate", "All quotes verified"), "quality"),
  ].join("");

  const blocked = status === "blocked" || status === "phase" || !run.isLive;
  const doExport = on(async () => {
    if (blocked || S.exportDone) return;
    S.exportDone = true; render();
    try {
      await chatAction(run.pdfId, "export_ontology");
      toast(L("Export avviato — i file compaiono qui sotto a fine scrittura.", "Export started — files appear below once written."));
      setTimeout(() => refreshRun(true), 2500);
    } catch (e) { S.exportDone = false; toast(e.message, true); render(); }
  });
  const exportLinks = run.exportFiles.map((f) => `
    <a href="/api/runs/${encodeURIComponent(run.runId)}/export/${encodeURIComponent(f)}" download style="display:inline-block;margin:6px 8px 0 0;font-size:12px;font-weight:500;padding:6px 12px;border-radius:8px;border:1px solid rgba(0,0,0,0.10);background:#FFFFFF;color:#22211D;text-decoration:none;">↓ ${esc(f)}</a>`).join("");

  return `
  <div style="max-width:760px;margin:0 auto;padding:26px 32px 40px;">
    <h1 class="serif" style="font-size:22px;font-weight:600;margin:0 0 16px;">${L("Pronto per l'export?", "Ready to export?")}</h1>
    <div class="card" style="display:flex;align-items:center;gap:14px;padding:18px 22px;">
      <div style="width:38px;height:38px;flex:none;border-radius:50%;background:${iconBg};color:${iconColor};display:flex;align-items:center;justify-content:center;font-size:17px;font-weight:600;">${glyph}</div>
      <div style="flex:1;">
        <div style="font-size:16px;font-weight:600;">${title}</div>
        <div style="font-size:12.5px;color:#55524B;margin-top:2px;line-height:1.5;">${detail}</div>
      </div>
    </div>
    <div class="card" style="margin-top:18px;overflow:hidden;">${checks}</div>
    <div style="display:flex;align-items:center;gap:12px;margin-top:18px;">
      <button data-h="${doExport}" ${blocked || S.exportDone ? "disabled" : ""} style="font-size:13px;font-weight:600;padding:11px 22px;border-radius:10px;border:${status === "warning" && !blocked && !S.exportDone ? "1px solid rgba(0,0,0,0.10)" : "none"};background:${blocked || S.exportDone ? "rgba(0,0,0,0.08)" : status === "warning" ? "#FFFFFF" : ACCENT};color:${blocked || S.exportDone ? "#A5A196" : status === "warning" ? C.warn : "#FFFFFF"};">${status === "warning" ? L("Esporta con avvertenze", "Export with warnings") : L("Esporta grafo", "Export graph")}</button>
      <span style="font-size:11.5px;color:#A5A196;line-height:1.5;max-width:380px;">${!run.isLive
        ? L("Sessione in archivio: l'export si esegue solo su una run attiva. I file già esportati restano scaricabili qui sotto.", "Archived session: exporting requires a live run. Previously exported files stay downloadable below.")
        : status === "phase"
        ? L("Il pulsante si abilita quando la pipeline raggiunge la fase di export.", "The button enables once the pipeline reaches the export phase.")
        : blocked
        ? L("Il pulsante si abilita quando le segnalazioni bloccanti e i campi richiesti sono risolti.", "The button enables once blocking issues and required fields are resolved.")
        : status === "warning"
          ? L("Le lacune aperte vengono dichiarate nel file esportato — l'export non nasconde ciò che è incompleto.", "Open gaps are declared in the exported file — the export never hides what is incomplete.")
          : L("Il grafo verificato viene scaricato come file, pronto per l'uso.", "The verified graph is downloaded as a file, ready to use.")}</span>
    </div>
    ${run.exportFiles.length ? `
      <div style="margin-top:16px;">
        <div class="kicker" style="margin-bottom:4px;">${L("File esportati", "Exported files")}</div>
        ${exportLinks}
      </div>` : ""}
    ${S.exportDone ? `<div style="margin-top:12px;font-size:12.5px;color:#7A9B7E;font-weight:500;">${L("✓ Export richiesto — le lacune rimaste aperte sono dichiarate nel file, così chi lo usa a valle ne è consapevole.", "✓ Export requested — remaining open gaps are declared in the file, so downstream users are aware.")}</div>` : ""}
  </div>`;
}

/* ── Inspector ── */
function confBlock(nodeId) {
  const run = S.run;
  const e = run && run.confMap[nodeId];
  if (!e) return "";
  const sigLabels = {
    evidence_present: L("Evidenza presente", "Evidence present"), corroboration: L("Corroborazione", "Corroboration"),
    required_props_complete: L("Proprietà richieste", "Required properties"), chain_participation: L("Catena nello schema", "Chain participation"),
    clean_extraction: L("Estrazione pulita", "Clean extraction"),
  };
  const penLabels = { ungrounded_evidence: L("citazione non trovata sulla pagina", "quote not found on the page"), human_binding_required: L("richiesta compilazione umana", "human input required"), per_retry: L("retry di correzione automatica", "automatic retry") };
  const signals = Object.entries(e.signals || {}).map(([k, v]) => `
    <div style="display:flex;align-items:center;gap:10px;padding:3.5px 0;">
      <span style="font-size:11.5px;color:#55524B;width:150px;flex:none;">${esc(sigLabels[k] || k)}</span>
      <span style="flex:1;height:4px;border-radius:2px;background:rgba(0,0,0,0.07);overflow:hidden;"><span style="display:block;height:100%;width:${Math.round(v * 100)}%;background:${v >= 0.8 ? C.ok : v >= 0.45 ? "#C2A36B" : C.danger};border-radius:2px;"></span></span>
      <span class="tnum" style="font-size:11px;color:#8A867D;width:32px;text-align:right;">${Number(v).toFixed(2)}</span>
    </div>`).join("");
  const pens = Object.entries(e.penalties || {}).map(([k, v]) => `
    <div style="display:flex;align-items:baseline;gap:8px;padding:3.5px 0;">
      <span style="font-size:11.5px;color:#B4543E;flex:1;">− ${esc(penLabels[k] || k)}</span>
      <span class="tnum" style="font-size:11px;color:#B4543E;">−${Number(v).toFixed(2)}</span>
    </div>`).join("");
  return `
  <div style="margin-top:18px;padding-top:14px;border-top:1px solid rgba(0,0,0,0.07);">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
      <span class="kicker">${L("Segnali di confidenza", "Confidence signals")}</span>
      <span style="flex:1;"></span>
      <span class="tnum" style="font-size:12px;font-weight:600;color:#3A3934;">${Number(e.score).toFixed(2)} · ${e.classification === "auto_reject" ? L("auto-rifiutato", "auto-rejected") : L("revisione umana", "human review")}</span>
    </div>
    ${signals}${pens}
  </div>`;
}

function actionBtn(label, kind, fn) {
  const styles = {
    primary: `background:${ACCENT};color:#FFFFFF;border:none;font-weight:600;`,
    ghost: `background:#FFFFFF;color:#22211D;border:1px solid rgba(0,0,0,0.10);font-weight:500;`,
    danger: `background:#FFFFFF;color:${C.danger};border:1px solid rgba(180,84,62,0.30);font-weight:500;`,
  };
  return `<button data-h="${on(fn)}" style="font-size:12.5px;padding:9px 16px;border-radius:10px;font-family:inherit;text-align:center;${styles[kind]}">${label}</button>`;
}

function buildInspector() {
  const sel = S.selected;
  const run = S.run;
  if (!sel || !run) return "";
  const KL = kindLabels(), SM = sevMeta(), DM = decMeta();
  let head = "", body = "";

  const close = on(() => { S.selected = null; render(); });
  const shell = (sevLabel, sevColor, sevBg, title, targetRef, inner) => `
  <aside class="c-inspector">
    <div style="display:flex;align-items:center;gap:10px;">
      <span class="pill" style="font-size:10.5px;color:${sevColor};background:${sevBg};padding:3px 9px;">${sevLabel}</span>
      <span style="flex:1;"></span>
      <button data-h="${close}" style="width:26px;height:26px;border-radius:8px;border:none;background:rgba(0,0,0,0.05);color:#6E6A61;font-size:13px;">✕</button>
    </div>
    <h2 class="serif" style="font-size:18px;font-weight:600;line-height:1.3;margin:12px 0 4px;">${title}</h2>
    <div class="mono" style="font-size:11px;color:#918D83;">${targetRef}</div>
    ${inner}
  </aside>`;
  const whyBlock = (reason) => `
    <div style="margin-top:16px;">
      <div class="kicker" style="margin-bottom:5px;">${L("Perché è segnalato", "Why it is flagged")}</div>
      <p style="font-size:13px;line-height:1.6;color:#3A3934;margin:0;">${esc(reason)}</p>
    </div>`;
  const fixBlock = (fix, label) => fix ? `
    <div style="margin-top:14px;padding:12px 14px;border-radius:10px;background:#F7F3EE;">
      <div class="kicker" style="color:#A08B77;margin-bottom:4px;">${label || L("Intervento suggerito", "Suggested action")}</div>
      <div style="font-size:12.5px;line-height:1.55;color:#55524B;">${esc(fix)}</div>
    </div>` : "";
  const quoteBlock = (quote, page) => quote ? `
    <div style="margin-top:16px;">
      <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:5px;">
        <span class="kicker">${L("Evidenza", "Evidence")}</span>
        ${page ? `<span class="mono" style="font-size:10.5px;color:#B5B1A6;">p. ${esc(page)}</span>` : ""}
      </div>
      <blockquote class="serif" style="margin:0;padding:0 0 0 12px;border-left:2px solid rgba(0,0,0,0.10);font-size:12.5px;line-height:1.65;color:#55524B;font-style:italic;">“${esc(quote)}”</blockquote>
    </div>` : "";
  const noQuoteBlock = () => `<div style="margin-top:16px;font-size:12px;color:#A5A196;line-height:1.55;">${L("Nessuna evidenza testuale collegata — è parte del motivo della segnalazione.", "No textual evidence attached — that is part of why it was flagged.")}</div>`;
  const actionsBlock = (btns, note) => btns.length || note ? `
    <div style="margin-top:20px;display:flex;flex-direction:column;gap:8px;">
      ${btns.join("")}
      ${note ? `<div style="font-size:11px;color:#A5A196;line-height:1.55;">${note}</div>` : ""}
    </div>` : "";

  if (sel.t === "queue") {
    const item = run.queue.find((it) => qKey(it) === sel.id);
    if (!item) return "";
    const sv = SM[item.severity] || SM.advisory;
    const dec = getDec(item);
    const key = qKey(item);
    const removed = S.removedCauses[key] || [];
    let inner = "";
    if (dec) {
      inner += `
      <div style="display:flex;align-items:center;gap:10px;margin-top:14px;padding:9px 14px;border-radius:10px;background:#ECEAE2;">
        <span style="flex:1;font-size:12.5px;font-weight:500;color:#55524B;">${(DM[dec.status] || DM.ignored).label}${dec.label ? " — " + esc(dec.label) : ""}</span>
        <button class="btn-ghost" style="font-size:11.5px;padding:4px 11px;" data-h="${on(() => reopenDecision(item))}">${L("Riapri", "Reopen")}</button>
      </div>`;
    }
    inner += whyBlock(item.reason);
    inner += fixBlock(item.suggested_fix);

    if (item.kind === "ambiguous_multi_cause_symptom") {
      inner += `
      <div style="margin-top:16px;">
        <div class="kicker" style="margin-bottom:8px;">${L("Cause candidate · MAY_INDICATE", "Candidate causes · MAY_INDICATE")}</div>
        ${(item.causes || []).map((cz) => {
          const isRemoved = removed.includes(cz.id);
          return `
          <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:10px;background:#FFFFFF;box-shadow:0 0 0 1px rgba(0,0,0,0.05);margin-bottom:6px;opacity:${isRemoved ? 0.5 : 1};">
            <span style="flex:1;min-width:0;">
              <span style="display:block;font-size:12.5px;font-weight:500;text-decoration:${isRemoved ? "line-through" : "none"};">${esc(cz.label)}</span>
              <span class="mono" style="display:block;font-size:10.5px;color:#B5B1A6;margin-top:1px;">${esc(cz.id)}${cz.page ? " · p. " + esc(cz.page) : ""}</span>
            </span>
            ${isRemoved ? `<span style="font-size:11px;font-weight:600;color:${C.danger};">${L("rimossa", "removed")}</span>`
              : (!dec ? `<button data-h="${on(() => { S.removedCauses = { ...S.removedCauses, [key]: [...removed, cz.id] }; render(); })}" style="flex:none;font-size:11.5px;font-weight:500;padding:4px 11px;border-radius:8px;border:1px solid rgba(180,84,62,0.30);background:#FFFFFF;color:${C.danger};">${L("Rimuovi", "Remove")}</button>` : "")}
          </div>`;
        }).join("")}
      </div>`;
    }
    if (item.suggestion) {
      inner += `
      <div style="margin-top:16px;padding:12px 14px;border-radius:10px;background:#FFFFFF;box-shadow:0 0 0 1px rgba(0,0,0,0.05);">
        <div class="kicker" style="margin-bottom:6px;">${L("Relazione suggerita · conf.", "Suggested relation · conf.")} ${fmtConf(item.suggestion.conf)}</div>
        <div style="font-size:12.5px;line-height:1.5;"><span style="font-weight:500;">${esc(item.suggestion.from)}</span> <span class="mono" style="font-size:10.5px;color:#A5A196;">${esc(item.suggestion.rel)}</span> <span style="font-weight:500;">${esc(item.suggestion.to)}</span></div>
        ${item.suggestion.rationale ? `<div style="font-size:11.5px;color:#8A867D;line-height:1.5;margin-top:4px;">${esc(item.suggestion.rationale)}</div>` : ""}
      </div>`;
    }
    inner += item.quote ? quoteBlock(item.quote, item.page) : ((item.severity === "open" || item.kind === "low_confidence") ? noQuoteBlock() : "");
    inner += confBlock(item.target_id);

    if (!dec) {
      const btns = [];
      let note = "";
      const live = run.isLive;
      if (item.kind === "ambiguous_multi_cause_symptom") {
        const remaining = (item.causes || []).length - removed.length;
        btns.push(actionBtn(L("Conferma le " + remaining + " cause rimanenti come valide", "Confirm the remaining " + remaining + " causes as valid"), "primary",
          () => decide(item, "confirmed", L(remaining + " cause parallele valide", remaining + " valid parallel causes") + (removed.length ? L(", " + removed.length + " rimosse", ", " + removed.length + " removed") : ""))));
        note = L("Rimuovere una causa elimina quel collegamento dal grafo. La conferma resta registrata nel diario della sessione.", "Removing a cause deletes that link from the graph. The confirmation is recorded in the session log.");
      } else if (item.severity === "blocking") {
        btns.push(actionBtn(L("Compila il campo richiesto", "Fill in the required field"), "primary", () => { S.view = "fields"; S.selected = null; render(); }));
        btns.push(actionBtn(L("Ignora (sconsigliato: blocca l'export)", "Ignore (not advised: blocks export)"), "ghost", () => decide(item, "ignored")));
        note = L("La risposta compilata completa il grafo e sblocca la validazione.", "Your answer completes the graph and unlocks validation.");
      } else if (item.severity === "open") {
        if (item.suggestion && live) {
          btns.push(actionBtn(L("Accetta la relazione suggerita", "Accept the suggested relation"), "primary", async () => {
            try {
              await chatAction(run.pdfId, "apply_suggested_relation", { indices: [item.suggestion.index] });
              decide(item, "accepted", item.suggestion.rel + " → " + item.suggestion.toId);
              setTimeout(() => refreshRun(true), 1200);
            } catch (e) { toast(e.message, true); }
          }));
          note = L("Accettando, la relazione suggerita viene aggiunta al grafo.", "Accepting adds the suggested relation to the graph.");
        } else {
          btns.push(actionBtn(L("Segna come gestita", "Mark as handled"), "primary", () => decide(item, "resolved")));
          note = L("Per collegare i nodi a mano usa l'editor del grafo. La decisione resta nel diario della sessione.", "To link nodes by hand use the graph editor. The decision is recorded in the session log.");
        }
        btns.push(actionBtn(L("Lascia aperta (dichiarata nell'export)", "Leave open (declared in the export)"), "ghost", () => decide(item, "ignored")));
      } else if (item.kind === "low_confidence") {
        btns.push(actionBtn(L("Conferma il nodo", "Confirm the node"), "primary", () => decide(item, "confirmed")));
        btns.push(actionBtn(L("Rifiuta il nodo", "Reject the node"), "danger", () => decide(item, "rejected")));
        note = item.severity === "reject"
          ? L("Nodo sotto la soglia minima di affidabilità: resta fuori dall'export salvo tua conferma esplicita.", "Node below the minimum confidence threshold: it stays out of the export unless you explicitly confirm it.")
          : L("Il rifiuto esclude il nodo dal grafo. La decisione resta nel diario della sessione.", "Rejecting removes the node from the graph. The decision is recorded in the session log.");
      } else {
        btns.push(actionBtn(L("Prendi atto", "Acknowledge"), "ghost", () => decide(item, "acknowledged")));
        note = L("Segnalazione informativa: non blocca l'export. L'eventuale correzione si fa nell'editor del grafo.", "Informational note: it does not block the export. Any fix is done in the graph editor.");
      }
      inner += actionsBlock(btns, note);
    }
    return shell(sv.label + " · " + (KL[item.kind] || item.kind), sv.color, sv.bg, esc(item.label), esc(item.target_type) + " · " + esc(item.target_id), inner);
  }

  if (sel.t === "triplet") {
    const t = run.triplets.find((x) => x.id === sel.id);
    if (!t) return "";
    const sevLabel = !t.complete ? L("Catena interrotta", "Broken chain") : t.ambiguous ? L("Ambiguità da confermare", "Ambiguity to confirm") : t.weak ? L("Catena debole", "Weak chain") : L("Catena completa", "Complete chain");
    const sevColor = !t.complete ? C.danger : (t.ambiguous || t.weak) ? C.warn : C.ok;
    const sevBg = !t.complete ? C.dangerBg : (t.ambiguous || t.weak) ? C.warnBg : C.okBg;
    let inner = whyBlock("Symptom → " + t.fm + " → " + t.ca) + quoteBlock(t.quote, t.page);
    if (t.queueRef) {
      const target = run.queue.find((it) => qKey(it) === t.queueRef);
      if (target) {
        inner += actionsBlock([actionBtn(L("Apri nel Review Center", "Open in Review Center"), "primary", () => { S.view = "review"; S.selected = { t: "queue", id: t.queueRef }; render(); })],
          L("Questa catena ha un elemento corrispondente nella coda di review.", "This chain has a matching item in the review queue."));
      }
    }
    return shell(sevLabel, sevColor, sevBg, esc(t.symptom), esc(t.id) + L(" · conf. min ", " · min conf. ") + fmtConf(t.conf), inner);
  }

  if (sel.t === "section") {
    const s = run.sections[sel.id];
    if (!s) return "";
    let inner = whyBlock(s.reasoning || s.why);
    if (s.keywords) inner += fixBlock(L("Parole chiave trovate: ", "Keywords found: ") + s.keywords, L("Parole chiave", "Keywords"));
    return shell(L("Sezione · ", "Section · ") + esc(s.source), "#6E7B8A", "rgba(110,123,138,0.12)", esc(s.name), L("pagine PDF ", "PDF pages ") + esc(s.pages), inner);
  }

  if (sel.t === "gnode") {
    const n = run.nodeById[sel.id];
    if (!n) return "";
    const q = run.queue.find((it) => it.target_id === n.id);
    const rels = run.edges.filter((e) => e.s === n.id || e.t === n.id);
    const names = rels.map((e) => {
      const otherId = e.s === n.id ? e.t : e.s;
      const other = run.nodeById[otherId];
      return (e.s === n.id ? e.rel + " → " : "← " + e.rel + " · ") + (other ? other.label : otherId);
    });
    const reason = rels.length
      ? rels.length + L(" collegamenti nel grafo: ", " links in the graph: ") + names.slice(0, 4).join(" · ") + (names.length > 4 ? " · …" : "")
      : L("Nessun collegamento — nodo isolato nel grafo.", "No links — isolated node in the graph.");
    let inner = whyBlock(reason);
    if (q) inner += fixBlock(q.reason, L("Segnalazione in coda", "Flagged in queue"));
    inner += quoteBlock(n.quote, n.page);
    inner += confBlock(n.id);
    if (q) inner += actionsBlock([actionBtn(L("Apri nel Review Center", "Open in Review Center"), "primary", () => { S.view = "review"; S.selected = { t: "queue", id: qKey(q) }; render(); })],
      L("Questo nodo ha una segnalazione nella coda di verifica.", "This node has an item in the review queue."));
    return shell(typeLabel(n.type), TYPE_COLORS[n.type] || "#8C8474", "rgba(0,0,0,0.05)", esc(n.label), esc(n.id) + L(" · affidabilità ", " · confidence ") + fmtConf(n.conf), inner);
  }

  if (sel.t === "conf") {
    const e = run.confMap[sel.id];
    if (!e) return "";
    const isRej = e.classification === "auto_reject";
    let inner = whyBlock((e.reasons || []).join("; ")) + noQuoteBlock() + confBlock(e.node_id);
    return shell(isRej ? L("Auto-rifiutato", "Auto-rejected") : L("Revisione umana", "Human review"), isRej ? C.danger : C.warn, isRej ? C.dangerBg : C.warnBg, esc(e.node_id), esc(e.node_type), inner);
  }
  return "";
}

/* ── events ── */
app.addEventListener("click", (e) => {
  const g = e.target.closest("[data-gnode]");
  if (g && dragInfo && dragInfo.moved) return;
  const el = e.target.closest("[data-h]");
  if (el && !el.dataset.evt) {
    const fn = H[+el.dataset.h];
    if (fn) fn(e);
  }
});
app.addEventListener("change", (e) => {
  const el = e.target.closest("[data-h][data-evt='change']");
  if (el) {
    const fn = H[+el.dataset.h];
    if (fn) fn(e);
  }
});

/* graph drag/pan */
app.addEventListener("mousedown", (e) => {
  const svg = e.target.closest("#gsvg");
  if (!svg) return;
  const gnode = e.target.closest("[data-gnode]");
  dragInfo = gnode
    ? { type: "node", id: gnode.dataset.gnode, x: e.clientX, y: e.clientY, moved: false }
    : { type: "pan", x: e.clientX, y: e.clientY, moved: false };
  e.preventDefault();
});
window.addEventListener("mousemove", (e) => {
  const d = dragInfo;
  if (!d || !S.run) return;
  const svg = document.getElementById("gsvg");
  if (!svg) { dragInfo = null; return; }
  const rect = svg.getBoundingClientRect();
  const s = Math.min(rect.width / 1100, rect.height / 620) || 1;
  const dx = e.clientX - d.x, dy = e.clientY - d.y;
  if (Math.abs(dx) + Math.abs(dy) > 3) d.moved = true;
  if (!d.moved) return;
  d.x = e.clientX; d.y = e.clientY;
  const G = S.graph;
  if (d.type === "pan") {
    G.panX += dx / s; G.panY += dy / s;
  } else if (G.mode === "rete") {
    const layout = graphLayout("rete", S.run);
    const cur = (G.pos.rete && G.pos.rete[d.id]) || layout[d.id];
    if (!cur) return;
    G.pos.rete = { ...(G.pos.rete || {}), [d.id]: { x: cur.x + dx / (s * G.zoom), y: cur.y + dy / (s * G.zoom) } };
  }
  render();
});
window.addEventListener("mouseup", () => {
  const d = dragInfo;
  dragInfo = null;
  if (d && d.type === "node" && !d.moved) { S.selected = { t: "gnode", id: d.id }; render(); }
});

/* ── boot ── */
// Liveness ticker: while a phase is running the banner shows how long ago the
// backend last persisted progress, updated every second without re-rendering.
// A frozen cumulative-duration KPI used to read as "the run is stuck".
setInterval(() => {
  const el = document.getElementById("kg-live-tick");
  if (!el) return;
  const ts = S.run && (S.run.status || {}).updated_at;
  if (!ts) { el.textContent = ""; return; }
  const secs = Math.max(0, Math.round((Date.now() - new Date(ts).getTime()) / 1000));
  const span = secs < 60 ? secs + " s" : Math.floor(secs / 60) + " min " + (secs % 60) + " s";
  el.textContent = L("ultimo avanzamento registrato ", "last recorded progress ") + span + L(" fa", " ago");
}, 1000);
render();
loadRuns();
})();
