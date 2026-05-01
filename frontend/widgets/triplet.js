/**
 * Chat widget: editable triplet card for review.
 * Lets the operator correct the extracted fields before approving.
 */

export function renderTripletWidget(payload, onAction) {
    const { triplet, index, total } = payload;
    if (!triplet) return null;

    const { symptom = {}, failure_modes = [], corrective_actions = [] } = triplet;

    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--triplet";
    wrap.dataset.tripletIndex = String(index);

    const header = document.createElement("div");
    header.className = "widget-header";
    header.innerHTML = `
        <span class="widget-icon">Triplet</span>
        <span class="widget-title">Triplet ${Number(index) + 1}${total ? ` / ${total}` : ""}</span>
        <span class="widget-meta">Review, edit, then approve or skip</span>
    `;
    wrap.appendChild(header);

    wrap.appendChild(_logicAssessment(payload.logic_assessment, triplet));

    wrap.appendChild(_entitySection({
        type: "Symptom",
        tone: "symptom",
        id: symptom.symptom_id,
        meta: [
            symptom.evidence_page ? `Evidence p. ${symptom.evidence_page}` : null,
        ],
        fields: [
            ["Name", "symptom.name", symptom.name],
            ["Description", "symptom.description", symptom.description, true],
            ["Severity", "symptom.severity", symptom.severity],
        ],
    }));

    wrap.appendChild(_connector());

    const fmBlock = document.createElement("div");
    fmBlock.className = "triplet-group triplet-group--failure";
    fmBlock.appendChild(_groupTitle("Failure Modes", failure_modes.length));
    if (failure_modes.length === 0) {
        fmBlock.appendChild(_empty("No failure modes extracted."));
    } else {
        failure_modes.forEach((fm, fmIndex) => {
            fmBlock.appendChild(_entitySection({
                type: "Failure Mode",
                tone: "failure-mode",
                id: fm.failure_mode_id,
                meta: [
                    fm.evidence_page ? `Evidence p. ${fm.evidence_page}` : null,
                    fm.linked_symptom_id ? `Linked symptom ${fm.linked_symptom_id}` : null,
                ],
                fields: [
                    ["Name", `failure_modes.${fmIndex}.name`, fm.name],
                    ["Description", `failure_modes.${fmIndex}.description`, fm.description, true],
                    ["Material context", `failure_modes.${fmIndex}.material_context`, fm.material_context],
                ],
            }));
        });
    }
    wrap.appendChild(fmBlock);

    wrap.appendChild(_connector());

    const caBlock = document.createElement("div");
    caBlock.className = "triplet-group triplet-group--action";
    caBlock.appendChild(_groupTitle("Corrective Actions", corrective_actions.length));
    if (corrective_actions.length === 0) {
        caBlock.appendChild(_empty("No corrective actions extracted."));
    } else {
        corrective_actions.forEach((ca, caIndex) => {
            caBlock.appendChild(_entitySection({
                type: "Corrective Action",
                tone: "corrective-action",
                id: ca.action_id,
                meta: [
                    ca.source_page ? `Source p. ${ca.source_page}` : null,
                    ca.linked_failure_mode_id ? `Linked failure ${ca.linked_failure_mode_id}` : null,
                ],
                fields: [
                    ["Name", `corrective_actions.${caIndex}.name`, ca.name],
                    ["Description", `corrective_actions.${caIndex}.description`, ca.description, true],
                    ["Instruction", `corrective_actions.${caIndex}.instruction_text`, ca.instruction_text, true],
                ],
            }));
        });
    }
    wrap.appendChild(caBlock);

    const actions = document.createElement("div");
    actions.className = "widget-actions";

    const saveBtn = document.createElement("button");
    saveBtn.className = "btn-secondary btn-sm";
    saveBtn.textContent = "Save Edits";
    saveBtn.disabled = true;
    saveBtn.addEventListener("click", async () => {
        const patch = _collectPatch(_activeTripletScope(wrap, saveBtn));
        if (Object.keys(patch).length === 0) return;
        _disableButtons(_actionButtonScope(actions, saveBtn));
        saveBtn.textContent = "Saving...";
        await onAction("edit_triplet", { index, patch });
    });

    const skipBtn = document.createElement("button");
    skipBtn.className = "btn-secondary btn-sm";
    skipBtn.textContent = "Skip";
    skipBtn.addEventListener("click", async () => {
        _disableButtons(_actionButtonScope(actions, skipBtn));
        await onAction("skip_triplet", { index });
    });

    const approveBtn = document.createElement("button");
    approveBtn.className = "btn-primary btn-sm";
    approveBtn.textContent = "Approve";
    approveBtn.addEventListener("click", async () => {
        _disableButtons(_actionButtonScope(actions, approveBtn));
        const patch = _collectPatch(_activeTripletScope(wrap, approveBtn));
        await onAction("approve_triplet", { index, patch });
    });

    actions.appendChild(saveBtn);
    actions.appendChild(skipBtn);
    actions.appendChild(approveBtn);
    wrap.appendChild(actions);

    _bindDirtyTracking(wrap, saveBtn);

    return wrap;
}

function _logicAssessment(provided, triplet) {
    const lines = Array.isArray(provided) && provided.length
        ? provided.slice(0, 2)
        : _buildLocalAssessment(triplet);

    const box = document.createElement("div");
    box.className = "triplet-logic";
    const title = document.createElement("div");
    title.className = "triplet-logic-title";
    title.textContent = "Logic check";
    box.appendChild(title);
    lines.slice(0, 2).forEach((line) => {
        const row = document.createElement("div");
        row.className = "triplet-logic-line";
        row.textContent = line;
        box.appendChild(row);
    });
    return box;
}

function _buildLocalAssessment(triplet) {
    const symptom = triplet?.symptom || {};
    const failureModes = Array.isArray(triplet?.failure_modes) ? triplet.failure_modes : [];
    const correctiveActions = Array.isArray(triplet?.corrective_actions) ? triplet.corrective_actions : [];
    const linkedActions = correctiveActions.filter((action) => action.linked_failure_mode_id).length;
    const chainState = failureModes.length && correctiveActions.length && linkedActions
        ? "complete enough to review"
        : "incomplete and needs attention";
    const pages = [
        symptom.evidence_page ? `symptom p. ${symptom.evidence_page}` : null,
        ...failureModes.map((fm) => fm.evidence_page ? `failure p. ${fm.evidence_page}` : null),
        ...correctiveActions.map((ca) => ca.source_page ? `action p. ${ca.source_page}` : null),
    ].filter(Boolean);
    return [
        `Chain: ${failureModes.length} failure mode(s) and ${correctiveActions.length} corrective action(s); ${chainState}.`,
        pages.length ? `Evidence: ${pages.slice(0, 4).join(", ")}.` : "Evidence: no source page is attached to this triplet.",
    ];
}

function _entitySection({ type, tone, id, meta = [], fields = [] }) {
    const section = document.createElement("section");
    section.className = `triplet-section triplet-section--${tone}`;

    const head = document.createElement("div");
    head.className = "triplet-section-head";
    const badge = document.createElement("span");
    badge.className = `triplet-type-badge triplet-type-badge--${tone}`;
    badge.textContent = type;
    head.appendChild(badge);
    if (id) {
        const idEl = document.createElement("span");
        idEl.className = "triplet-id";
        idEl.textContent = id;
        head.appendChild(idEl);
    }
    meta.filter(Boolean).forEach((item) => {
        const metaEl = document.createElement("span");
        metaEl.className = "triplet-meta";
        metaEl.textContent = item;
        head.appendChild(metaEl);
    });
    section.appendChild(head);

    const grid = document.createElement("div");
    grid.className = "triplet-edit-grid";
    fields.forEach(([label, path, value, wide]) => {
        grid.appendChild(_editableField(label, path, value, Boolean(wide)));
    });
    section.appendChild(grid);
    return section;
}

function _editableField(label, path, value, wide = false) {
    const row = document.createElement("label");
    row.className = wide ? "triplet-edit-field triplet-edit-field--wide" : "triplet-edit-field";

    const labelEl = document.createElement("span");
    labelEl.className = "triplet-edit-label";
    labelEl.textContent = label;
    row.appendChild(labelEl);

    const input = document.createElement("span");
    input.className = "triplet-edit-value";
    input.contentEditable = "true";
    input.spellcheck = false;
    input.dataset.fieldPath = path;
    input.dataset.initialValue = _normaliseEditableValue(value);
    input.textContent = _normaliseEditableValue(value);
    input.setAttribute("role", "textbox");
    input.setAttribute("aria-label", label);
    row.appendChild(input);

    return row;
}

function _groupTitle(label, count) {
    const title = document.createElement("div");
    title.className = "triplet-group-title";
    title.innerHTML = `<span>${_escapeHtml(label)}</span><span>${Number(count) || 0}</span>`;
    return title;
}

function _connector() {
    const div = document.createElement("div");
    div.className = "triplet-connector";
    div.textContent = "v";
    return div;
}

function _empty(text) {
    const el = document.createElement("p");
    el.className = "triplet-empty";
    el.textContent = text;
    return el;
}

function _bindDirtyTracking(wrap, saveBtn) {
    wrap.querySelectorAll("[data-field-path]").forEach((field) => {
        field.addEventListener("input", () => {
            const scope = _activeTripletScope(wrap, field);
            const hasChanges = Object.keys(_collectPatch(scope)).length > 0;
            saveBtn.disabled = !hasChanges;
            wrap.classList.toggle("triplet-has-edits", hasChanges);
            field.classList.toggle("is-edited", _fieldValue(field) !== (field.dataset.initialValue || ""));
        });
        field.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                _focusNextField(wrap, field);
            }
        });
    });
}

function _activeTripletScope(wrap, node) {
    return node?.closest?.(".widget-sheet") || node?.closest?.(".chat-widget--triplet") || wrap;
}

function _actionButtonScope(actions, button) {
    return button?.closest?.(".widget-sheet-footer") || actions;
}

function _focusNextField(wrap, current) {
    const fields = [...wrap.querySelectorAll("[data-field-path]")];
    const idx = fields.indexOf(current);
    const next = fields[idx + 1];
    if (!next) return;
    next.focus();
    const range = document.createRange();
    range.selectNodeContents(next);
    range.collapse(false);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
}

function _collectPatch(wrap) {
    const patch = {};
    wrap.querySelectorAll("[data-field-path]").forEach((field) => {
        const next = _fieldValue(field);
        const initial = field.dataset.initialValue || "";
        if (next !== initial) {
            patch[field.dataset.fieldPath] = next;
        }
    });
    return patch;
}

function _fieldValue(field) {
    return _normaliseEditableValue(field.textContent || "");
}

function _normaliseEditableValue(value) {
    return String(value ?? "").replace(/\u00a0/g, " ").replace(/\s+/g, " ").trim();
}

function _disableButtons(container) {
    container.querySelectorAll("button").forEach((button) => { button.disabled = true; });
}

function _escapeHtml(text) {
    return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
