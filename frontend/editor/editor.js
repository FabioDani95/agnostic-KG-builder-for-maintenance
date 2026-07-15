const apiUrl = (path) => `${API_BASE}${path}`;
const COLOR_PALETTE = [
  "#6b8cba", "#7aab82", "#c47e5a", "#9b79b8",
  "#5fa8a0", "#b87a7a", "#a0a052", "#6b9eb8",
  "#b8906b", "#7a8fb8", "#88a87a"
];

let network = null;
let nodesDataSet = null;
let edgesDataSet = null;
let nodesView = null;
let edgesView = null;
let allNodes = [];
let allEdges = [];
let activeNodeTypes = new Set();
let activeEdgeTypes = new Set();
let colorByType = {};
let editMode = false;
let hasUnsavedChanges = false;
let selectedNodeId = null;
let schemaData = null;
let allNodesList = [];
let currentPanelMode = "edit";
let coCreateMode = "write";
let coCreateDraft = null;
let acceptedSuggestions = [];
let speechRecognition = null;
let voiceStartedAt = null;
let voiceTimer = null;

function pickColor(idx) {
  return COLOR_PALETTE[idx % COLOR_PALETTE.length];
}

function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 2500);
}

function updateStatusPill() {
  const nCount = nodesView ? nodesView.get().length : 0;
  const eCount = edgesView ? edgesView.get().length : 0;
  document.getElementById("status-pill").textContent = `${nCount} nodes · ${eCount} edges`;
}

function markUnsaved() {
  hasUnsavedChanges = true;
  document.getElementById("unsaved-dot").classList.add("visible");
}

function setEditorPanelOpen(open) {
  editMode = Boolean(open);
  document.getElementById("layout").classList.toggle("edit-mode", editMode);
  document.getElementById("edit-mode-toggle").classList.toggle("active", editMode);
  if (!editMode && typeof stopActiveRecognition === "function") stopActiveRecognition();
  if (network) {
    setTimeout(() => { network.redraw(); }, 260);
  }
}

function setPanelMode(mode) {
  const next = mode === "create" ? "create" : "edit";
  if (next !== "create" && typeof stopActiveRecognition === "function") stopActiveRecognition();
  currentPanelMode = next;
  document.getElementById("ep-tab-edit")?.classList.toggle("active", currentPanelMode === "edit");
  document.getElementById("ep-tab-create")?.classList.toggle("active", currentPanelMode === "create");
}

function buildNodeChips(nodeTypes) {
  const container = document.getElementById("node-types");
  container.innerHTML = "";
  nodeTypes.forEach((val, idx) => {
    const color = pickColor(idx);
    const chip = document.createElement("div");
    chip.className = `chip ${activeNodeTypes.has(val) ? "active" : ""}`;
    chip.dataset.value = val;
    chip.innerHTML = `<span class="dot" style="background:${color}"></span>${val}`;
    chip.addEventListener("click", () => {
      const isActive = chip.classList.toggle("active");
      if (isActive) activeNodeTypes.add(val); else activeNodeTypes.delete(val);
      applyFilters();
    });
    container.appendChild(chip);
  });
}

function buildEdgeChips(edgeTypes) {
  const container = document.getElementById("edge-types");
  container.innerHTML = "";
  edgeTypes.forEach((val) => {
    const chip = document.createElement("div");
    chip.className = `chip ${activeEdgeTypes.has(val) ? "active" : ""}`;
    chip.dataset.value = val;
    chip.textContent = val;
    chip.addEventListener("click", () => {
      const isActive = chip.classList.toggle("active");
      if (isActive) activeEdgeTypes.add(val); else activeEdgeTypes.delete(val);
      applyFilters();
    });
    container.appendChild(chip);
  });
}

function applyFilters() {
  if (!nodesView || !edgesView) return;
  nodesView.refresh();
  edgesView.refresh();
  updateStatusPill();
}

function showError(msg) {
  const box = document.getElementById("error-box");
  box.textContent = msg;
  box.style.display = "block";
  document.getElementById("status-pill").textContent = "Error";
}

function enrichNode(n) {
  const c = colorByType[n.group] || "#4b5563";
  return {
    ...n,
    color: {
      border: c, background: c,
      highlight: { border: "#e5e7eb", background: c },
      hover: { border: "#e5e7eb", background: c },
    },
    font: { color: "#f9fafb", size: 12, face: "system-ui" },
    shape: "dot",
    size: 13,
  };
}

// ---- Edit panel ----
async function loadNodeEdit(nodeId) {
  selectedNodeId = nodeId;
  document.getElementById("ep-title").textContent = "Edit Node";
  const body = document.getElementById("ep-body");
  body.innerHTML = '<div class="ep-placeholder">Loading…</div>';

  let data;
  try {
    const res = await fetch(apiUrl(`/node/${encodeURIComponent(nodeId)}`));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
  } catch (err) {
    body.innerHTML = `<div class="ep-placeholder" style="color:#f87171">${err.message}</div>`;
    return;
  }

  // Highlight selected node
  if (nodesDataSet) {
    // Reset all
    nodesDataSet.forEach(n => {
      nodesDataSet.update({ id: n.id, borderWidth: 1 });
    });
    nodesDataSet.update({ id: nodeId, borderWidth: 3 });
  }

  renderEditPanel(data);
}

function renderEditPanel(data) {
  setPanelMode("edit");
  const body = document.getElementById("ep-body");
  const color = colorByType[data.type] || "#4b5563";
  const idKey = nodeIdKeyForType(data.type, data.attributes);

  let html = `<div class="ep-section">
    <div class="ep-badge"><span class="dot" style="background:${color}"></span>${data.type}</div>
    <div class="ep-id">${data.id}</div>
  </div>`;

  html += `<div class="ep-section">
    <div class="ep-section-title">Attributes</div>
    ${buildAttributeTable(data.type, data.attributes, { readonlyKeys: new Set([idKey]), scope: "edit" })}
    <div class="ep-attr-actions">
      <span class="ep-muted">Edit values directly in the table, then save this node.</span>
      <button class="ep-btn ep-btn-primary" id="apply-attrs-btn">Save Attributes</button>
    </div>
  </div>`;

  // Outgoing relationships
  html += `<div class="ep-section"><div class="ep-section-title">Outgoing Relationships (${data.relationships_out.length})</div>`;
  if (data.relationships_out.length === 0) {
    html += `<div style="font-size:11px;color:#6b7280">None</div>`;
  }
  for (const r of data.relationships_out) {
    html += `<div class="ep-rel-row">
      <span class="rel-type">${escHtml(r.type)}</span>
      <span class="rel-node" data-nav-node="${escHtml(r.to_id)}" title="${escHtml(r.to_id)}">${escHtml(r.to_label)}</span>
      <button class="rel-del" data-rel-idx="${r.index}" title="Delete">&times;</button>
    </div>`;
  }
  html += `</div>`;

  // Incoming relationships
  html += `<div class="ep-section"><div class="ep-section-title">Incoming Relationships (${data.relationships_in.length})</div>`;
  if (data.relationships_in.length === 0) {
    html += `<div style="font-size:11px;color:#6b7280">None</div>`;
  }
  for (const r of data.relationships_in) {
    html += `<div class="ep-rel-row">
      <span class="rel-node" data-nav-node="${escHtml(r.from_id)}" title="${escHtml(r.from_id)}">${escHtml(r.from_label)}</span>
      <span class="rel-type">${escHtml(r.type)}</span>
      <button class="rel-del" data-rel-idx="${r.index}" title="Delete">&times;</button>
    </div>`;
  }
  html += `</div>`;

  // Add relationship
  html += `<details class="ep-add-rel"><summary>+ Add Relationship</summary>
    <div class="ep-add-rel-form">
      <div class="ep-field">
        <label>Direction</label>
        <select id="add-rel-dir">
          <option value="out">Outgoing from this node</option>
          <option value="in">Incoming to this node</option>
        </select>
      </div>
      <div class="ep-field">
        <label>Relationship Type</label>
        <select id="add-rel-type">
          ${buildRelTypeOptions()}
        </select>
      </div>
      <div class="ep-field">
        <label>Target Node</label>
        <input type="text" id="add-rel-node-search" placeholder="Search nodes…" autocomplete="off" />
        <select id="add-rel-node" size="4" style="margin-top:4px;max-height:120px"></select>
      </div>
      <button class="ep-btn" id="add-rel-btn">Add</button>
    </div>
  </details>`;

  // Delete node
  html += `<div class="ep-section" style="margin-top:20px;padding-top:14px;border-top:1px solid #374151">
    <div class="ep-section-title" style="color:#f87171">Danger Zone</div>
    <button class="ep-btn ep-btn-danger" id="delete-node-btn" style="width:100%">Delete this node</button>
  </div>`;

  body.innerHTML = html;

  // Wire up events
  document.getElementById("apply-attrs-btn").addEventListener("click", () => applyAttrs(data.id));
  body.querySelectorAll(".field-polish").forEach(btn => {
    btn.addEventListener("click", () => polishFields(data.type, [btn.dataset.field], "#ep-body"));
  });

  body.querySelectorAll(".rel-del").forEach(btn => {
    btn.addEventListener("click", () => deleteRelationship(parseInt(btn.dataset.relIdx)));
  });

  body.querySelectorAll(".rel-node[data-nav-node]").forEach(el => {
    el.addEventListener("click", () => {
      const targetId = el.dataset.navNode;
      if (targetId && nodesDataSet.get(targetId)) {
        network.selectNodes([targetId]);
        network.focus(targetId, { scale: 1.2, animation: { duration: 400 } });
        loadNodeEdit(targetId);
      }
    });
  });

  // Node search for add-rel
  const searchInput = document.getElementById("add-rel-node-search");
  const nodeSelect = document.getElementById("add-rel-node");
  populateNodeSelect(nodeSelect, data.id, "");
  searchInput.addEventListener("input", () => {
    populateNodeSelect(nodeSelect, data.id, searchInput.value.trim().toLowerCase());
  });
  document.getElementById("add-rel-dir").addEventListener("change", () => {
    populateNodeSelect(nodeSelect, data.id, searchInput.value.trim().toLowerCase());
  });
  document.getElementById("add-rel-type").addEventListener("change", () => {
    populateNodeSelect(nodeSelect, data.id, searchInput.value.trim().toLowerCase());
  });

  document.getElementById("add-rel-btn").addEventListener("click", () => addRelationship(data.id));

  document.getElementById("delete-node-btn").addEventListener("click", () => {
    if (!confirm(`Delete node "${data.attributes.name || data.id}"?
All its relationships will also be removed.`)) return;
    deleteNode(data.id);
  });
}

function schemaPropsFor(nodeType) {
  return schemaData?.node_types?.[nodeType] || [];
}

function propByName(nodeType, key) {
  return schemaPropsFor(nodeType).find(prop => prop.name === key) || null;
}

function nodeIdKeyForType(nodeType, attrs = {}) {
  const schemaIdKey = schemaPropsFor(nodeType).find(prop => String(prop.name || "").endsWith("_id"))?.name;
  return schemaIdKey || Object.keys(attrs).find(k => k.endsWith("_id")) || `${String(nodeType || "node").toLowerCase()}_id`;
}

function valueToEditorString(value) {
  if (Array.isArray(value)) return value.join("\n");
  return value == null ? "" : String(value);
}

function shouldUseTextarea(key, value, prop) {
  const text = valueToEditorString(value);
  return prop?.type === "array" || text.length > 64 || /description|instruction|context|reference/i.test(key);
}

function buildFieldControl(nodeType, key, value, { readonly = false, scope = "edit" } = {}) {
  const prop = propByName(nodeType, key);
  const required = prop?.required ? `<span class="ep-required">Required</span>` : "";
  const type = prop?.type || "string";
  const readonlyAttr = readonly ? "readonly" : "";
  const dataAttrs = readonly
    ? ""
    : `data-attr-key="${escHtml(key)}" data-attr-type="${escHtml(type)}" data-attr-scope="${escHtml(scope)}"`;
  const valueText = valueToEditorString(value);
  const control = shouldUseTextarea(key, value, prop)
    ? `<textarea ${dataAttrs} ${readonlyAttr} rows="${type === "array" ? 3 : 4}">${escHtml(valueText)}</textarea>`
    : `<input type="text" ${dataAttrs} ${readonlyAttr} value="${escHtml(valueText)}" />`;
  const polishButton = !readonly && !key.endsWith("_id") && !["code", "severity"].includes(key)
    ? `<button class="ep-btn field-polish" type="button" data-field="${escHtml(key)}">Polish</button>`
    : "";
  const note = type === "array" ? `<div class="ep-field-note">One item per line or comma-separated.</div>` : "";
  return `
    <div class="ep-field-row">
      <div>
        ${control}
        ${note}
      </div>
      ${polishButton}
    </div>
    ${required}`;
}

function buildAttributeTable(nodeType, attrs, { readonlyKeys = new Set(), scope = "edit" } = {}) {
  const keys = [];
  for (const prop of schemaPropsFor(nodeType)) {
    if (prop.name && !keys.includes(prop.name)) keys.push(prop.name);
  }
  for (const key of Object.keys(attrs || {})) {
    if (!keys.includes(key)) keys.push(key);
  }
  if (keys.length === 0) {
    return `<div class="ep-muted">No attributes are defined for this node type.</div>`;
  }
  const rows = keys.map(key => {
    const value = attrs?.[key] ?? "";
    return `<tr>
      <th>${escHtml(key)}</th>
      <td>${buildFieldControl(nodeType, key, value, {
        readonly: readonlyKeys.has(key),
        scope,
      })}</td>
    </tr>`;
  }).join("");
  return `<table class="ep-attr-table"><tbody>${rows}</tbody></table>`;
}

function collectAttributes(rootSelector) {
  const attrs = {};
  document.querySelectorAll(`${rootSelector} [data-attr-key]`).forEach(input => {
    const key = input.dataset.attrKey;
    if (!key) return;
    const raw = input.value;
    attrs[key] = input.dataset.attrType === "array"
      ? raw.split(/[\n,]+/).map(v => v.trim()).filter(Boolean)
      : raw;
  });
  return attrs;
}

function setAttributeControls(rootSelector, attrs) {
  document.querySelectorAll(`${rootSelector} [data-attr-key]`).forEach(input => {
    const key = input.dataset.attrKey;
    if (!key || !(key in attrs)) return;
    input.value = valueToEditorString(attrs[key]);
  });
}

async function polishFields(nodeType, fields, rootSelector) {
  const attrs = collectAttributes(rootSelector);
  try {
    const res = await fetch(apiUrl("/node/polish"), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ node_type: nodeType, attributes: attrs, fields }),
    });
    const result = await parseApiResponse(res);
    if (result.ok && result.attributes) {
      setAttributeControls(rootSelector, result.attributes);
      if (currentPanelMode === "create") {
        updateCreatePreview(nodeType);
        updateCreateSummary(nodeType);
      }
      toast(fields?.length ? "Field polished" : "Text fields polished");
    }
  } catch (err) {
    toast("Polish error: " + err.message);
  }
}

function buildRelTypeOptions() {
  const types = new Set();
  if (schemaData && schemaData.relation_constraints) {
    Object.keys(schemaData.relation_constraints).forEach(t => types.add(t));
  }
  // Also from current edges
  if (edgesDataSet) {
    edgesDataSet.forEach(e => types.add(e.label));
  }
  return Array.from(types).sort().map(t => `<option value="${escHtml(t)}">${escHtml(t)}</option>`).join("");
}

function compatibleTargetTypes(currentNodeId) {
  const relationType = document.getElementById("add-rel-type")?.value || "";
  const direction = document.getElementById("add-rel-dir")?.value || "out";
  const currentNode = allNodesList.find(n => n.id === currentNodeId);
  if (!currentNode) return null;
  return compatibleTargetTypesFor(currentNode.type, relationType, direction);
}

function compatibleTargetTypesFor(nodeType, relationType, direction) {
  const constraints = schemaData?.relation_constraints?.[relationType];
  if (!constraints) return null;
  const domain = constraints.domain || [];
  const range = constraints.range || [];
  if (direction === "out") {
    if (domain.length && !domain.includes(nodeType)) return [];
    return range.length ? range : null;
  }
  if (range.length && !range.includes(nodeType)) return [];
  return domain.length ? domain : null;
}

function populateNodeSelect(sel, currentNodeId, filter) {
  sel.innerHTML = "";
  const allowedTypes = compatibleTargetTypes(currentNodeId);
  const items = allNodesList.filter(n =>
    n.id !== currentNodeId &&
    (!allowedTypes || allowedTypes.includes(n.type)) &&
    (!filter || n.label.toLowerCase().includes(filter) || n.id.toLowerCase().includes(filter))
  ).slice(0, 50);
  for (const n of items) {
    const opt = document.createElement("option");
    opt.value = n.id;
    opt.textContent = `[${n.type}] ${n.label}`;
    sel.appendChild(opt);
  }
}

function nodeTypePrefix(nodeType) {
  const known = {
    Asset: "ASSET",
    Component: "CMP",
    Symptom: "SYM",
    FailureMode: "FM",
    CorrectiveAction: "CA",
    ErrorCode: "ERR",
  };
  if (known[nodeType]) return known[nodeType];
  const parts = String(nodeType || "node").match(/[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)/g) || [];
  return (parts.map(part => part[0]).join("") || String(nodeType || "node").slice(0, 3)).toUpperCase();
}

function suggestNextNodeId(nodeType) {
  const prefix = nodeTypePrefix(nodeType);
  let maxSeen = 0;
  const pattern = new RegExp(`^${prefix}-(\\d+)$`, "i");
  for (const item of allNodesList) {
    const match = String(item.id || "").match(pattern);
    if (match) maxSeen = Math.max(maxSeen, Number(match[1]));
  }
  let idx = maxSeen + 1;
  while (allNodesList.some(item => item.id === `${prefix}-${String(idx).padStart(3, "0")}`)) {
    idx += 1;
  }
  return `${prefix}-${String(idx).padStart(3, "0")}`;
}

function allSchemaNodeTypes() {
  const fromSchema = Object.keys(schemaData?.node_types || {});
  const fromGraph = Array.from(new Set(allNodesList.map(n => n.type).filter(Boolean)));
  return Array.from(new Set([...fromSchema, ...fromGraph])).sort();
}

function initialCreateAttrs(nodeType) {
  const attrs = {};
  for (const prop of schemaPropsFor(nodeType)) {
    attrs[prop.name] = prop.name === nodeIdKeyForType(nodeType) ? suggestNextNodeId(nodeType) : "";
  }
  return attrs;
}

function relationTypesForNodeType(nodeType) {
  const entries = Object.entries(schemaData?.relation_constraints || {});
  const compatible = entries.filter(([, constraint]) => {
    const domain = constraint.domain || [];
    const range = constraint.range || [];
    return !domain.length || domain.includes(nodeType) || !range.length || range.includes(nodeType);
  });
  return compatible.map(([name]) => name).sort();
}

function directionOptionsFor(nodeType, relationType) {
  const constraints = schemaData?.relation_constraints?.[relationType];
  if (!constraints) return ["out", "in"];
  const domain = constraints.domain || [];
  const range = constraints.range || [];
  const options = [];
  if (!domain.length || domain.includes(nodeType)) options.push("out");
  if (!range.length || range.includes(nodeType)) options.push("in");
  return options.length ? options : ["out"];
}

function createInputText() {
  const byMode = {
    write: "cocreate-text",
    voice: "cocreate-voice-text",
    guide: "cocreate-guide-text",
  };
  const active = document.getElementById(byMode[coCreateMode] || "cocreate-text")?.value?.trim();
  return active
    || document.getElementById("cocreate-text")?.value?.trim()
    || document.getElementById("cocreate-voice-text")?.value?.trim()
    || document.getElementById("cocreate-guide-text")?.value?.trim()
    || "";
}

function buildCoCreateInputStep(selectedType) {
  const typeOptions = allSchemaNodeTypes()
    .map(t => `<option value="${escHtml(t)}" ${coCreateDraft?.node_type === t ? "selected" : ""}>${escHtml(t)}</option>`)
    .join("");
  return `
    <div class="create-step">
      <div class="create-step-head">
        <h3 class="create-step-title">Co-create intake</h3>
        <span class="create-step-index">Step 1</span>
      </div>
      <div class="cocreate-mode-row">
        <button class="cocreate-mode-btn ${coCreateMode === "write" ? "active" : ""}" data-cocreate-mode="write" type="button">Write</button>
        <button class="cocreate-mode-btn ${coCreateMode === "voice" ? "active" : ""}" data-cocreate-mode="voice" type="button">Voice</button>
        <button class="cocreate-mode-btn ${coCreateMode === "guide" ? "active" : ""}" data-cocreate-mode="guide" type="button">Guide</button>
      </div>
      <div class="cocreate-input-panel" id="cocreate-panel-write" ${coCreateMode === "write" ? "" : "hidden"}>
        <textarea id="cocreate-text" class="cocreate-textarea" placeholder="Describe the node to add, with any useful context. Example: low hydraulic pressure appears during pump startup and may indicate pump wear.">${escHtml(coCreateDraft?.source_text || "")}</textarea>
      </div>
      <div class="cocreate-input-panel" id="cocreate-panel-voice" ${coCreateMode === "voice" ? "" : "hidden"}>
        <textarea id="cocreate-voice-text" class="cocreate-textarea" placeholder="Voice transcript will appear here. You can edit it before generating the draft.">${escHtml(coCreateDraft?.source_text || "")}</textarea>
        <div class="cocreate-action-row">
          <div>
            <button class="ep-btn" id="voice-start-btn" type="button">Record</button>
            <button class="ep-btn" id="voice-stop-btn" type="button" disabled>Stop</button>
          </div>
          <span class="cocreate-status" id="voice-status">Voice input uses browser speech recognition when available.</span>
        </div>
      </div>
      <div class="cocreate-input-panel" id="cocreate-panel-guide" ${coCreateMode === "guide" ? "" : "hidden"}>
        <textarea id="cocreate-guide-text" class="cocreate-textarea" placeholder="Answer the graph co-creator: what is this thing, what problem does it describe, and what should it connect to?">${escHtml(coCreateDraft?.source_text || "")}</textarea>
        <div class="cocreate-agent-note">
          The co-creator will classify the note, fill a structured node draft, flag missing fields, and suggest schema-compatible links. You stay in control of the final create action.
        </div>
      </div>
      <div class="cocreate-action-row">
        <div class="ep-field" style="margin:0;min-width:150px;flex:1">
          <label>Preferred type</label>
          <select id="cocreate-preferred-type">
            <option value="">Auto-detect</option>
            ${typeOptions}
          </select>
        </div>
        <button class="ep-btn ep-btn-primary" id="generate-draft-btn" type="button">Generate Draft</button>
      </div>
      <div class="cocreate-status" id="cocreate-status">${coCreateDraft?.rationale ? escHtml(coCreateDraft.rationale) : "Describe a node, then let the co-creator prepare the draft and possible links."}</div>
    </div>
  `;
}

function draftAttributesFor(selectedType) {
  if (coCreateDraft?.node_type === selectedType && coCreateDraft?.attributes) {
    return { ...initialCreateAttrs(selectedType), ...coCreateDraft.attributes };
  }
  return initialCreateAttrs(selectedType);
}

function renderCreateWizard(nodeType = "", options = {}) {
  if (options.draft) {
    coCreateDraft = options.draft;
    acceptedSuggestions = [];
  } else if (options.resetDraft) {
    coCreateDraft = null;
    acceptedSuggestions = [];
  }
  setEditorPanelOpen(true);
  setPanelMode("create");
  selectedNodeId = null;
  document.getElementById("ep-title").textContent = "Co-create Node";
  if (nodesDataSet) {
    nodesDataSet.forEach(n => nodesDataSet.update({ id: n.id, borderWidth: 1 }));
  }

  const types = allSchemaNodeTypes();
  const selectedType = types.includes(nodeType)
    ? nodeType
    : (types.includes(coCreateDraft?.node_type) ? coCreateDraft.node_type : (types[0] || ""));
  const attrs = draftAttributesFor(selectedType);
  const relationTypes = relationTypesForNodeType(selectedType);
  const firstRelType = relationTypes[0] || "";
  const directions = directionOptionsFor(selectedType, firstRelType);
  const missingFields = coCreateDraft?.node_type === selectedType ? (coCreateDraft.missing_fields || []) : [];
  const duplicateCandidates = coCreateDraft?.node_type === selectedType ? (coCreateDraft.duplicate_candidates || []) : [];

  const body = document.getElementById("ep-body");
  body.innerHTML = `
    ${buildCoCreateInputStep(selectedType)}
    <div class="create-step">
      <div class="create-step-head">
        <h3 class="create-step-title">Node type</h3>
        <span class="create-step-index">Step 2</span>
      </div>
      <div class="ep-field">
        <label>Type</label>
        <select id="create-node-type">
          ${types.map(t => `<option value="${escHtml(t)}" ${t === selectedType ? "selected" : ""}>${escHtml(t)}</option>`).join("")}
        </select>
        <div class="ep-field-note">The form below follows the ontology schema for the selected type.</div>
      </div>
      ${missingFields.length ? `<div class="cocreate-agent-note">Missing required fields: ${missingFields.map(escHtml).join(", ")}.</div>` : ""}
      ${duplicateCandidates.length ? `<div class="cocreate-agent-note">Possible duplicates: ${duplicateCandidates.map(c => `${escHtml(c.label)} (${Math.round(Number(c.score || 0) * 100)}%)`).join(", ")}.</div>` : ""}
    </div>

    <div class="create-step">
      <div class="create-step-head">
        <h3 class="create-step-title">Attributes</h3>
        <span class="create-step-index">Step 3</span>
      </div>
      ${buildAttributeTable(selectedType, attrs, { scope: "create" })}
      <div class="ep-attr-actions">
        <span class="ep-muted">IDs are suggested automatically and can be edited before creation.</span>
        <button class="ep-btn" id="create-polish-all" type="button">Polish Text</button>
      </div>
    </div>

    <div class="create-step">
      <div class="create-step-head">
        <h3 class="create-step-title">Connect to KG</h3>
        <span class="create-step-index">Step 4</span>
      </div>
      <div class="suggestion-list" id="relationship-suggestions"></div>
      <div class="cocreate-action-row">
        <span class="ep-muted">Accept suggested links or choose one manually below.</span>
        <button class="ep-btn" id="suggest-links-btn" type="button">Suggest Links</button>
      </div>
      <div class="create-grid">
        <div class="ep-field">
          <label>Relationship</label>
          <select id="create-rel-type">
            ${relationTypes.map(t => `<option value="${escHtml(t)}" ${t === firstRelType ? "selected" : ""}>${escHtml(t)}</option>`).join("")}
          </select>
        </div>
        <div class="ep-field">
          <label>Direction</label>
          <select id="create-rel-dir">
            ${directions.map(d => `<option value="${d}">${d === "out" ? "New node -> existing" : "Existing -> new node"}</option>`).join("")}
          </select>
        </div>
      </div>
      <div class="ep-field">
        <label>Existing node</label>
        <input type="text" id="create-rel-node-search" placeholder="Search nodes..." autocomplete="off" />
        <select id="create-rel-node" size="5" style="margin-top:4px;max-height:150px"></select>
      </div>
      <label class="ep-inline-check">
        <input type="checkbox" id="create-skip-rel" />
        <span>Create as orphan for now</span>
      </label>
      <div class="create-preview" id="create-link-preview">Select a target node to preview the new link.</div>
    </div>

      <div class="create-step">
      <div class="create-step-head">
        <h3 class="create-step-title">Review</h3>
        <span class="create-step-index">Step 5</span>
      </div>
      <div class="create-summary" id="create-summary"></div>
      <div class="ep-attr-actions">
        <span class="ep-muted" id="create-validation-hint">A connected node is recommended for co-editing the KG.</span>
        <button class="ep-btn ep-btn-primary" id="create-node-btn" type="button">Create Node</button>
      </div>
    </div>
  `;

  wireCreateWizard(selectedType);
}

async function generateDraftFromCoCreate() {
  const text = createInputText();
  const preferredType = document.getElementById("cocreate-preferred-type")?.value || "";
  if (!text) {
    toast("Describe the node first");
    return;
  }
  const status = document.getElementById("cocreate-status");
  if (status) status.textContent = "Co-creator is drafting the node...";
  try {
    const res = await fetch(apiUrl("/node/draft-from-text"), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ text, preferred_type: preferredType || null }),
    });
    const draft = await parseApiResponse(res);
    draft.source_text = text;
    renderCreateWizard(draft.node_type, { draft });
    setTimeout(() => suggestLinksForDraft(draft.node_type), 0);
    toast("Draft generated");
  } catch (err) {
    if (status) status.textContent = err.message;
    toast("Draft error: " + err.message);
  }
}

async function suggestLinksForDraft(nodeType) {
  const attrs = collectAttributes("#ep-body");
  const box = document.getElementById("relationship-suggestions");
  if (box) box.innerHTML = '<div class="ep-muted">Co-creator is ranking compatible links...</div>';
  try {
    const res = await fetch(apiUrl("/relationship/suggest"), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ node_type: nodeType, attributes: attrs, limit: 6 }),
    });
    const result = await parseApiResponse(res);
    renderRelationshipSuggestions(result.suggestions || [], nodeType);
    updateCreateSummary(nodeType);
  } catch (err) {
    if (box) box.innerHTML = `<div class="ep-muted" style="color:#f87171">${escHtml(err.message)}</div>`;
    toast("Suggestion error: " + err.message);
  }
}

function suggestionKey(suggestion) {
  return [
    suggestion.relation_type,
    suggestion.direction,
    suggestion.target_id,
  ].join("|");
}

function renderRelationshipSuggestions(suggestions, nodeType) {
  const box = document.getElementById("relationship-suggestions");
  if (!box) return;
  if (!suggestions.length) {
    box.innerHTML = '<div class="ep-muted">No strong link suggestions yet. Use manual linking below or create as orphan.</div>';
    return;
  }
  box.innerHTML = suggestions.map((s, idx) => {
    const key = suggestionKey(s);
    const accepted = acceptedSuggestions.some(item => suggestionKey(item) === key);
    const attrs = collectAttributes("#ep-body");
    const newLabel = attrs.name || attrs[nodeIdKeyForType(nodeType)] || "new node";
    const flow = s.direction === "out"
      ? `${escHtml(newLabel)} -> ${escHtml(s.relation_type)} -> ${escHtml(s.target_label)}`
      : `${escHtml(s.target_label)} -> ${escHtml(s.relation_type)} -> ${escHtml(newLabel)}`;
    return `<div class="suggestion-card ${accepted ? "accepted" : ""}" data-suggestion-index="${idx}">
      <div class="suggestion-top">
        <div class="suggestion-flow">${flow}</div>
        <span class="suggestion-confidence">${Math.round(Number(s.confidence || 0) * 100)}%</span>
      </div>
      <div class="suggestion-reason">${escHtml(s.reason || "")}</div>
      <div class="suggestion-actions">
        <button class="ep-btn ${accepted ? "" : "ep-btn-primary"} suggestion-accept" type="button" data-suggestion-index="${idx}">${accepted ? "Accepted" : "Accept"}</button>
        <button class="ep-btn suggestion-focus" type="button" data-target-id="${escHtml(s.target_id)}">Show target</button>
      </div>
    </div>`;
  }).join("");
  box.querySelectorAll(".suggestion-accept").forEach(btn => {
    btn.addEventListener("click", () => {
      const suggestion = suggestions[Number(btn.dataset.suggestionIndex)];
      const key = suggestionKey(suggestion);
      if (acceptedSuggestions.some(item => suggestionKey(item) === key)) {
        acceptedSuggestions = acceptedSuggestions.filter(item => suggestionKey(item) !== key);
      } else {
        acceptedSuggestions.push(suggestion);
      }
      renderRelationshipSuggestions(suggestions, nodeType);
      updateCreatePreview(nodeType);
      updateCreateSummary(nodeType);
    });
  });
  box.querySelectorAll(".suggestion-focus").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.targetId;
      if (!targetId || !nodesDataSet.get(targetId)) return;
      network.selectNodes([targetId]);
      network.focus(targetId, { scale: 1.15, animation: { duration: 350 } });
    });
  });
}

function stopActiveRecognition() {
  if (speechRecognition) {
    try { speechRecognition.onresult = null; } catch {}
    try { speechRecognition.onend = null; } catch {}
    try { speechRecognition.onerror = null; } catch {}
    try { speechRecognition.stop(); } catch {}
    try { speechRecognition.abort(); } catch {}
  }
  speechRecognition = null;
  if (voiceTimer) {
    clearInterval(voiceTimer);
    voiceTimer = null;
  }
}

function detectVoiceLang() {
  const fromTextarea = document.getElementById("cocreate-voice-text");
  if (fromTextarea?.lang) return fromTextarea.lang;
  return navigator.language || "en-US";
}

function setupVoiceInput() {
  const startBtn = document.getElementById("voice-start-btn");
  const stopBtn = document.getElementById("voice-stop-btn");
  const status = document.getElementById("voice-status");
  if (!startBtn || !stopBtn) return;
  // Recognition started in a previous wizard render must not outlive its DOM.
  stopActiveRecognition();
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    startBtn.disabled = true;
    if (status) status.textContent = "Voice recognition is not available in this browser.";
    return;
  }
  const restoreIdle = (message) => {
    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (voiceTimer) { clearInterval(voiceTimer); voiceTimer = null; }
    if (status && message) status.textContent = message;
  };
  startBtn.addEventListener("click", () => {
    stopActiveRecognition();
    const transcriptEl = document.getElementById("cocreate-voice-text");
    // Track only the recognizer's own committed output; user edits stay untouched.
    let recognizedFinal = "";
    let lastWrittenValue = transcriptEl?.value || "";
    try {
      speechRecognition = new Recognition();
      speechRecognition.lang = detectVoiceLang();
      speechRecognition.interimResults = true;
      speechRecognition.continuous = true;
      voiceStartedAt = Date.now();
      speechRecognition.onresult = (event) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          const chunk = event.results[i][0]?.transcript || "";
          if (event.results[i].isFinal) recognizedFinal += `${chunk} `;
          else interim += chunk;
        }
        if (!transcriptEl) return;
        // Preserve any manual edits the user made between recognition events:
        // only rewrite the textarea if it still matches what we last set.
        if (transcriptEl.value !== lastWrittenValue) {
          lastWrittenValue = transcriptEl.value;
          recognizedFinal = lastWrittenValue.endsWith(" ") || !lastWrittenValue
            ? lastWrittenValue
            : `${lastWrittenValue} `;
          return;
        }
        const next = `${recognizedFinal}${interim}`.replace(/\s+$/g, "");
        transcriptEl.value = next;
        lastWrittenValue = next;
      };
      speechRecognition.onerror = (event) => {
        const code = event?.error || "unknown";
        const message = code === "not-allowed" || code === "service-not-allowed"
          ? "Microphone access was blocked. Allow it in the browser to dictate."
          : code === "no-speech"
            ? "No speech detected. Try again closer to the microphone."
            : code === "audio-capture"
              ? "No microphone found."
              : `Voice input error: ${code}.`;
        restoreIdle(message);
      };
      speechRecognition.onend = () => {
        restoreIdle("Recording stopped. Review the transcript and generate the draft.");
      };
      speechRecognition.start();
      startBtn.disabled = true;
      stopBtn.disabled = false;
      if (status) status.innerHTML = '<span class="voice-meter"><span class="voice-dot"></span>Listening 0:00</span>';
      voiceTimer = setInterval(() => {
        const elapsed = Math.floor((Date.now() - voiceStartedAt) / 1000);
        const min = Math.floor(elapsed / 60);
        const sec = String(elapsed % 60).padStart(2, "0");
        if (status) status.innerHTML = `<span class="voice-meter"><span class="voice-dot"></span>Listening ${min}:${sec}</span>`;
      }, 500);
    } catch (err) {
      restoreIdle(err.message || "Could not start voice input.");
    }
  });
  stopBtn.addEventListener("click", () => {
    if (speechRecognition) {
      try { speechRecognition.stop(); } catch { stopActiveRecognition(); }
    }
  });
}

function wireCreateWizard(nodeType) {
  const body = document.getElementById("ep-body");
  body.querySelectorAll("[data-cocreate-mode]").forEach(btn => {
    btn.addEventListener("click", () => {
      const next = btn.dataset.cocreateMode || "write";
      if (next !== "voice") stopActiveRecognition();
      coCreateMode = next;
      body.querySelectorAll("[data-cocreate-mode]").forEach(el => el.classList.toggle("active", el === btn));
      body.querySelectorAll(".cocreate-input-panel").forEach(panel => {
        panel.hidden = panel.id !== `cocreate-panel-${coCreateMode}`;
      });
    });
  });
  body.querySelector("#generate-draft-btn")?.addEventListener("click", generateDraftFromCoCreate);
  setupVoiceInput();
  body.querySelector("#create-node-type")?.addEventListener("change", (e) => {
    acceptedSuggestions = [];
    coCreateDraft = null;
    renderCreateWizard(e.target.value);
  });
  body.querySelector("#create-polish-all")?.addEventListener("click", () => polishFields(nodeType, null, "#ep-body"));
  body.querySelectorAll(".field-polish").forEach(btn => {
    btn.addEventListener("click", () => polishFields(nodeType, [btn.dataset.field], "#ep-body"));
  });

  const relType = body.querySelector("#create-rel-type");
  const relDir = body.querySelector("#create-rel-dir");
  const search = body.querySelector("#create-rel-node-search");
  const skip = body.querySelector("#create-skip-rel");

  const refreshDirectionOptions = () => {
    const selected = relDir.value;
    const directions = directionOptionsFor(nodeType, relType.value);
    relDir.innerHTML = directions.map(d => `<option value="${d}">${d === "out" ? "New node -> existing" : "Existing -> new node"}</option>`).join("");
    if (directions.includes(selected)) relDir.value = selected;
  };
  const refreshAll = () => {
    refreshDirectionOptions();
    populateCreateTargetSelect(nodeType);
    updateCreatePreview(nodeType);
    updateCreateSummary(nodeType);
  };

  relType?.addEventListener("change", refreshAll);
  relDir?.addEventListener("change", refreshAll);
  body.querySelector("#suggest-links-btn")?.addEventListener("click", () => suggestLinksForDraft(nodeType));
  search?.addEventListener("input", () => {
    populateCreateTargetSelect(nodeType);
    updateCreatePreview(nodeType);
  });
  skip?.addEventListener("change", () => {
    updateCreatePreview(nodeType);
    updateCreateSummary(nodeType);
  });
  body.querySelector("#create-rel-node")?.addEventListener("change", () => {
    updateCreatePreview(nodeType);
    updateCreateSummary(nodeType);
  });
  body.querySelectorAll("[data-attr-key]").forEach(input => {
    input.addEventListener("input", () => {
      updateCreatePreview(nodeType);
      updateCreateSummary(nodeType);
    });
  });
  body.querySelector("#create-node-btn")?.addEventListener("click", () => createNodeFromWizard(nodeType));

  refreshAll();
}

function populateCreateTargetSelect(nodeType) {
  const sel = document.getElementById("create-rel-node");
  if (!sel) return;
  const relType = document.getElementById("create-rel-type")?.value || "";
  const direction = document.getElementById("create-rel-dir")?.value || "out";
  const filter = (document.getElementById("create-rel-node-search")?.value || "").trim().toLowerCase();
  const allowedTypes = compatibleTargetTypesFor(nodeType, relType, direction);
  sel.innerHTML = "";
  const items = allNodesList.filter(n =>
    (!allowedTypes || allowedTypes.includes(n.type)) &&
    (!filter || n.label.toLowerCase().includes(filter) || n.id.toLowerCase().includes(filter) || n.type.toLowerCase().includes(filter))
  ).slice(0, 80);
  for (const n of items) {
    const opt = document.createElement("option");
    opt.value = n.id;
    opt.textContent = `[${n.type}] ${n.label}`;
    sel.appendChild(opt);
  }
}

function requiredMissingFromControls(nodeType, attrs) {
  return schemaPropsFor(nodeType)
    .filter(prop => prop.required)
    .filter(prop => {
      const value = attrs[prop.name];
      if (prop.type === "array") return !Array.isArray(value) || value.length === 0;
      return !String(value || "").trim();
    })
    .map(prop => prop.name);
}

function manualRelationshipDraft(nodeType, nodeId) {
  const relType = document.getElementById("create-rel-type")?.value || "";
  const direction = document.getElementById("create-rel-dir")?.value || "out";
  const targetId = document.getElementById("create-rel-node")?.value || "";
  const skip = document.getElementById("create-skip-rel")?.checked || false;
  if (skip || !relType || !targetId || !nodeId) return null;
  return {
    type: relType,
    from_id: direction === "out" ? nodeId : targetId,
    to_id: direction === "out" ? targetId : nodeId,
  };
}

function acceptedRelationshipDrafts(nodeId) {
  return acceptedSuggestions.map(s => ({
    type: s.relation_type,
    from_id: s.from_id === "__NEW_NODE__" ? nodeId : s.from_id,
    to_id: s.to_id === "__NEW_NODE__" ? nodeId : s.to_id,
  }));
}

function updateCreatePreview(nodeType) {
  const preview = document.getElementById("create-link-preview");
  const targetId = document.getElementById("create-rel-node")?.value || "";
  const relType = document.getElementById("create-rel-type")?.value || "";
  const direction = document.getElementById("create-rel-dir")?.value || "out";
  const skip = document.getElementById("create-skip-rel")?.checked || false;
  const attrs = collectAttributes("#ep-body");
  const newLabel = attrs.name || attrs[nodeIdKeyForType(nodeType)] || "new node";
  const target = allNodesList.find(n => n.id === targetId);
  if (!preview) return;
  if (acceptedSuggestions.length) {
    preview.innerHTML = `${acceptedSuggestions.length} accepted link${acceptedSuggestions.length === 1 ? "" : "s"} will be created with <strong>${escHtml(newLabel)}</strong>.`;
    return;
  }
  if (skip) {
    preview.innerHTML = `The node <strong>${escHtml(newLabel)}</strong> will be created without a relationship.`;
    return;
  }
  if (!target || !relType) {
    preview.textContent = "Select a compatible relationship and existing node to connect the new node.";
    return;
  }
  preview.innerHTML = direction === "out"
    ? `<strong>${escHtml(newLabel)}</strong> ${escHtml(relType)} <strong>${escHtml(target.label)}</strong>`
    : `<strong>${escHtml(target.label)}</strong> ${escHtml(relType)} <strong>${escHtml(newLabel)}</strong>`;
}

function updateCreateSummary(nodeType) {
  const summary = document.getElementById("create-summary");
  const createBtn = document.getElementById("create-node-btn");
  const hint = document.getElementById("create-validation-hint");
  const attrs = collectAttributes("#ep-body");
  const idKey = nodeIdKeyForType(nodeType);
  const nodeId = String(attrs[idKey] || "").trim();
  const skip = document.getElementById("create-skip-rel")?.checked || false;
  const targetId = document.getElementById("create-rel-node")?.value || "";
  const relType = document.getElementById("create-rel-type")?.value || "";
  const target = allNodesList.find(n => n.id === targetId);
  const missing = requiredMissingFromControls(nodeType, attrs);
  const manualRel = manualRelationshipDraft(nodeType, nodeId);
  const linkLabel = acceptedSuggestions.length
    ? `${acceptedSuggestions.length} accepted suggestion${acceptedSuggestions.length === 1 ? "" : "s"}`
    : (skip ? "orphan" : (relType && target ? `${relType} ${target.label}` : "missing"));
  if (summary) {
    summary.innerHTML = `
      <div class="create-summary-row"><span>Type</span><strong>${escHtml(nodeType)}</strong></div>
      <div class="create-summary-row"><span>ID</span><strong>${escHtml(nodeId || "missing")}</strong></div>
      <div class="create-summary-row"><span>Name</span><strong>${escHtml(attrs.name || "missing")}</strong></div>
      <div class="create-summary-row"><span>Required</span><strong>${missing.length ? escHtml(missing.join(", ")) : "complete"}</strong></div>
      <div class="create-summary-row"><span>Link</span><strong>${escHtml(linkLabel)}</strong></div>
    `;
  }
  const canCreate = Boolean(nodeId) && missing.length === 0 && (acceptedSuggestions.length > 0 || skip || Boolean(manualRel));
  if (createBtn) createBtn.disabled = !canCreate;
  if (hint) hint.textContent = canCreate
    ? "Ready to create. Save Version persists the edited graph to disk."
    : "Fill required fields and accept a link, choose one manually, or explicitly create it as orphan.";
}

async function createNodeFromWizard(nodeType) {
  const attrs = collectAttributes("#ep-body");
  const idKey = nodeIdKeyForType(nodeType);
  const nodeId = String(attrs[idKey] || "").trim();
  const missing = requiredMissingFromControls(nodeType, attrs);
  if (missing.length) {
    toast(`Missing required fields: ${missing.join(", ")}`);
    return;
  }
  const manualRel = manualRelationshipDraft(nodeType, nodeId);
  const relationships = [
    ...acceptedRelationshipDrafts(nodeId),
    ...(acceptedSuggestions.length === 0 && manualRel ? [manualRel] : []),
  ];

  try {
    const res = await fetch(apiUrl("/node/create"), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ node_type: nodeType, attributes: attrs, relationships }),
    });
    const result = await parseApiResponse(res);
    if (result.ok && result.vis_node) {
      ensureNodeTypeVisible(nodeType);
      const enriched = enrichNode(result.vis_node);
      enriched.borderWidth = 3;
      nodesDataSet.add(enriched);
      allNodes.push(enriched);
      allNodesList.push(result.all_node || { id: result.node_id, label: result.vis_node.label, type: nodeType });
      if (Array.isArray(result.edges) && result.edges.length) {
        edgesDataSet.add(result.edges);
        allEdges.push(...result.edges);
        refreshEdgeTypeChips();
      }
      markUnsaved();
      updateStatusPill();
      network.selectNodes([result.node_id]);
      network.focus(result.node_id, { scale: 1.2, animation: { duration: 400 } });
      toast("Node created and linked");
      loadNodeEdit(result.node_id);
    }
  } catch (err) {
    toast("Create error: " + err.message);
  }
}

function ensureNodeTypeVisible(nodeType) {
  if (!colorByType[nodeType]) {
    colorByType[nodeType] = pickColor(Object.keys(colorByType).length);
  }
  if (!activeNodeTypes.has(nodeType)) {
    activeNodeTypes.add(nodeType);
    buildNodeChips(allSchemaNodeTypes());
  }
}

function refreshEdgeTypeChips() {
  const edgeTypes = Array.from(new Set([
    ...allEdges.map(e => e.label).filter(Boolean),
    ...Object.keys(schemaData?.relation_constraints || {}),
  ])).sort();
  edgeTypes.forEach(t => activeEdgeTypes.add(t));
  buildEdgeChips(edgeTypes);
}

function escHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

async function parseApiResponse(res) {
  let payload = null;
  try {
    payload = await res.json();
  } catch {}
  if (!res.ok) {
    const detail = payload && payload.detail ? payload.detail : `HTTP ${res.status}`;
    throw new Error(detail);
  }
  return payload || {};
}

async function applyAttrs(nodeId) {
  const attrs = collectAttributes("#ep-body");

  try {
    const res = await fetch(apiUrl(`/node/${encodeURIComponent(nodeId)}/update`), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ attributes: attrs }),
    });
    const result = await parseApiResponse(res);
    if (result.ok && result.vis_node) {
      const enriched = enrichNode(result.vis_node);
      enriched.borderWidth = 3; // keep selected highlight
      nodesDataSet.update(enriched);
      // Update allNodes reference
      const idx = allNodes.findIndex(n => n.id === nodeId);
      if (idx >= 0) Object.assign(allNodes[idx], enriched);
      // Update allNodesList
      const nIdx = allNodesList.findIndex(n => n.id === nodeId);
      if (nIdx >= 0) allNodesList[nIdx].label = result.vis_node.label;
      markUnsaved();
      toast("Attributes updated");
    }
  } catch (err) {
    toast("Error: " + err.message);
  }
}

async function deleteRelationship(relIndex) {
  try {
    const res = await fetch(apiUrl(`/relationship/${relIndex}/delete`), {
      method: "POST",
    });
    const result = await parseApiResponse(res);
    if (result.ok) {
      // Rebuild edges from server
      await reloadEdges();
      markUnsaved();
      toast("Relationship deleted");
      // Re-fetch current node
      if (selectedNodeId) loadNodeEdit(selectedNodeId);
    }
  } catch (err) {
    toast("Error: " + err.message);
  }
}

async function addRelationship(currentNodeId) {
  const dir = document.getElementById("add-rel-dir").value;
  const rtype = document.getElementById("add-rel-type").value;
  const targetSel = document.getElementById("add-rel-node");
  const targetId = targetSel.value;
  if (!rtype || !targetId) {
    toast("Select relationship type and target node");
    return;
  }

  const from_id = dir === "out" ? currentNodeId : targetId;
  const to_id = dir === "out" ? targetId : currentNodeId;

  try {
    const res = await fetch(apiUrl("/relationship/add"), {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ type: rtype, from_id, to_id }),
    });
    const result = await parseApiResponse(res);
    if (result.ok && result.edge) {
      edgesDataSet.add(result.edge);
      allEdges.push(result.edge);
      // Rebuild edge type chips if new type
      if (!activeEdgeTypes.has(rtype)) {
        activeEdgeTypes.add(rtype);
        const allET = new Set();
        edgesDataSet.forEach(e => allET.add(e.label));
        buildEdgeChips(Array.from(allET).sort());
      }
      markUnsaved();
      toast("Relationship added");
      if (selectedNodeId) loadNodeEdit(selectedNodeId);
      updateStatusPill();
    }
  } catch (err) {
    toast("Error: " + err.message);
  }
}

async function deleteNode(nodeId) {
  try {
    const res = await fetch(apiUrl(`/node/${encodeURIComponent(nodeId)}/delete`), { method: "POST" });
    const result = await parseApiResponse(res);
    if (result.ok) {
      // Remove from DataSet and local arrays
      nodesDataSet.remove(nodeId);
      allNodes = allNodes.filter(n => n.id !== nodeId);
      allNodesList = allNodesList.filter(n => n.id !== nodeId);
      // Reload edges (some were removed server-side)
      await reloadEdges();
      selectedNodeId = null;
      markUnsaved();
      // Reset edit panel
      document.getElementById("ep-body").innerHTML =
        '<div class="ep-placeholder">Node deleted. Click another node to edit.</div>';
      toast(`Node deleted (${result.removed_relationships} relationships removed)`);
      updateStatusPill();
    }
  } catch (err) {
    toast("Error: " + err.message);
  }
}

async function reloadEdges() {
  try {
    const res = await fetch(apiUrl("/data"));
    const payload = await parseApiResponse(res);
    allEdges = payload.edges || [];
    edgesDataSet.clear();
    edgesDataSet.add(allEdges);
    // Refresh edge type chips
    const edgeTypes = Array.from(new Set([
      ...(payload.edge_types || []),
      ...Object.keys(schemaData?.relation_constraints || {}),
    ])).sort();
    activeEdgeTypes.clear();
    edgeTypes.forEach(t => activeEdgeTypes.add(t));
    buildEdgeChips(edgeTypes);
    applyFilters();
  } catch (err) {
    console.error("reloadEdges error:", err);
  }
}

// ---- Save ----
async function saveVersion() {
  try {
    const res = await fetch(apiUrl("/save"), { method: "POST" });
    const result = await parseApiResponse(res);
    if (result.ok) {
      hasUnsavedChanges = false;
      document.getElementById("unsaved-dot").classList.remove("visible");
      document.getElementById("version-label").textContent = `v${result.version}`;
      toast(`Saved as ${result.saved_as}`);
    }
  } catch (err) {
    toast("Save error: " + err.message);
  }
}

// ---- Init ----
async function init() {
  // Load schema & all nodes in parallel
  const [payloadRes, schemaRes, nodesListRes] = await Promise.all([
    fetch(apiUrl("/data")), fetch(apiUrl("/schema")), fetch(apiUrl("/all_nodes"))
  ]);

  let payload;
  try {
    payload = await parseApiResponse(payloadRes);
    schemaData = await parseApiResponse(schemaRes);
    allNodesList = await parseApiResponse(nodesListRes);
  } catch (err) {
    showError(`Failed to load data: ${err.message}`);
    return;
  }

  allNodes = payload.nodes || [];
  allEdges = payload.edges || [];
  const nodeTypes = Array.from(new Set([
    ...(payload.node_types || []),
    ...Object.keys(schemaData?.node_types || {}),
  ])).sort();
  const edgeTypes = Array.from(new Set([
    ...(payload.edge_types || []),
    ...Object.keys(schemaData?.relation_constraints || {}),
  ])).sort();

  if (allNodes.length === 0) {
    showError("No nodes found in the current ontology.");
    return;
  }

  nodeTypes.forEach((t, idx) => { colorByType[t] = pickColor(idx); });

  allNodes = allNodes.map(n => enrichNode(n));

  nodeTypes.forEach(t => activeNodeTypes.add(t));
  edgeTypes.forEach(t => activeEdgeTypes.add(t));

  // Persistent DataSet + DataView
  nodesDataSet = new vis.DataSet(allNodes);
  edgesDataSet = new vis.DataSet(allEdges);

  nodesView = new vis.DataView(nodesDataSet, {
    filter: n => activeNodeTypes.has(n.group)
  });
  edgesView = new vis.DataView(edgesDataSet, {
    filter: e => {
      if (!activeEdgeTypes.has(e.label)) return false;
      const fromNode = nodesDataSet.get(e.from);
      const toNode = nodesDataSet.get(e.to);
      if (!fromNode || !toNode) return false;
      return activeNodeTypes.has(fromNode.group) && activeNodeTypes.has(toNode.group);
    }
  });

  const container = document.getElementById("network");
  const options = {
    autoResize: true,
    physics: {
      enabled: true,
      stabilization: { iterations: 300, fit: true },
      barnesHut: {
        gravitationalConstant: -3000,
        springLength: 130,
        springConstant: 0.04,
        damping: 0.15,
      },
    },
    interaction: {
      hover: true,
      tooltipDelay: 80,
      hideEdgesOnDrag: true,
      navigationButtons: false,
      keyboard: true,
    },
    edges: {
      smooth: { enabled: true, type: "continuous", roundness: 0.2 },
      font: { size: 9, color: "#6b7280", background: "transparent", strokeWidth: 0 },
      color: { color: "#374151", highlight: "#9ca3af", hover: "#9ca3af" },
      arrows: { to: { enabled: true, scaleFactor: 0.6 } },
      width: 1,
    },
  };

  try {
    network = new vis.Network(
      container,
      { nodes: nodesView, edges: edgesView },
      options
    );
  } catch (err) {
    showError(`Failed to render graph: ${err.message}`);
    return;
  }

  buildNodeChips(nodeTypes);
  buildEdgeChips(edgeTypes);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      network.redraw();
      network.fit({ animation: false });
    });
  });

  network.once("stabilizationIterationsDone", () => {
    network.fit({ animation: { duration: 600, easingFunction: "easeInOutQuad" } });
    updateStatusPill();
  });

  setTimeout(() => {
    const pill = document.getElementById("status-pill");
    if (pill.textContent === "Loading…") {
      network.redraw();
      network.fit();
      updateStatusPill();
    }
  }, 8000);

  document.getElementById("physics-toggle").addEventListener("change", e => {
    network.setOptions({ physics: { enabled: e.target.checked } });
  });
  document.getElementById("smooth-toggle").addEventListener("change", e => {
    network.setOptions({ edges: { smooth: { enabled: e.target.checked } } });
  });
  document.getElementById("fit-btn").addEventListener("click", () => {
    network.fit({ animation: { duration: 400, easingFunction: "easeInOutQuad" } });
  });

  // Edit mode toggle
  document.getElementById("edit-mode-toggle").addEventListener("click", () => {
    setEditorPanelOpen(!editMode);
  });
  document.getElementById("create-node-open").addEventListener("click", () => renderCreateWizard("", { resetDraft: true }));
  document.getElementById("ep-new-node-btn").addEventListener("click", () => renderCreateWizard("", { resetDraft: true }));
  document.getElementById("ep-tab-create").addEventListener("click", () => renderCreateWizard());
  document.getElementById("ep-tab-edit").addEventListener("click", () => {
    setPanelMode("edit");
    if (selectedNodeId) {
      loadNodeEdit(selectedNodeId);
    } else {
      document.getElementById("ep-title").textContent = "Graph Editor";
      document.getElementById("ep-body").innerHTML =
        '<div class="ep-placeholder">Click a node in the graph to edit it.</div>';
    }
  });

  // Node click opens the editor directly.
  network.on("click", params => {
    if (params.nodes.length === 0) return;
    setEditorPanelOpen(true);
    loadNodeEdit(params.nodes[0]);
  });

  // Save button
  document.getElementById("save-btn").addEventListener("click", saveVersion);

  // Load current version
  try {
    const statusRes = await fetch(apiUrl("/status"));
    const status = await statusRes.json();
    document.getElementById("version-label").textContent = `v${status.version}`;
  } catch {}

  // Unsaved changes warning
  window.addEventListener("beforeunload", e => {
    if (hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = "";
    }
  });
}

window.addEventListener("load", init);
