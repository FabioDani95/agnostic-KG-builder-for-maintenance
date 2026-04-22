/**
 * Chat widget: triplet card for review.
 * Shows Symptom → FailureMode → CorrectiveAction with Validate/Skip/Edit buttons.
 */

export function renderTripletWidget(payload, onAction) {
    const { triplet, index, total } = payload;
    if (!triplet) return null;

    const { symptom = {}, failure_modes = [], corrective_actions = [] } = triplet;

    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--triplet";

    // Header
    const header = document.createElement("div");
    header.className = "widget-header";
    header.innerHTML = `
        <span class="widget-icon">🔗</span>
        <span class="widget-title">Triplet ${index + 1}${total ? ` / ${total}` : ""}</span>
        <span class="widget-meta">Review required</span>
    `;
    wrap.appendChild(header);

    // Symptom
    const symSection = _section("Symptom", symptom.name, symptom.description, [
        symptom.severity ? `Severity: ${symptom.severity}` : null,
        symptom.evidence_page ? `Evidence: p. ${symptom.evidence_page}` : null,
    ]);
    wrap.appendChild(symSection);

    // Failure Modes
    failure_modes.forEach(fm => {
        const fmSection = _section("Failure Mode", fm.name, fm.description, [
            fm.material_context ? `Context: ${fm.material_context}` : null,
            fm.evidence_page ? `Evidence: p. ${fm.evidence_page}` : null,
        ]);
        wrap.appendChild(fmSection);
    });

    // Corrective Actions
    corrective_actions.forEach(ca => {
        const caSection = _section("Corrective Action", ca.name, ca.description, [
            ca.instruction_text ? `Steps: ${ca.instruction_text}` : null,
            ca.source_page ? `Source: p. ${ca.source_page}` : null,
        ]);
        wrap.appendChild(caSection);
    });

    // Actions
    const actions = document.createElement("div");
    actions.className = "widget-actions";

    const skipBtn = document.createElement("button");
    skipBtn.className = "btn-secondary btn-sm";
    skipBtn.textContent = "Skip";
    skipBtn.addEventListener("click", () => {
        _disableButtons(actions);
        onAction("skip_triplet", { index });
    });

    const validateBtn = document.createElement("button");
    validateBtn.className = "btn-primary btn-sm";
    validateBtn.textContent = "Validate ✓";
    validateBtn.addEventListener("click", () => {
        _disableButtons(actions);
        onAction("approve_triplet", { index });
    });

    actions.appendChild(skipBtn);
    actions.appendChild(validateBtn);
    wrap.appendChild(actions);

    return wrap;
}

function _section(type, name, description, meta = []) {
    const div = document.createElement("div");
    div.className = `triplet-section triplet-section--${type.toLowerCase().replace(" ", "-")}`;
    div.innerHTML = `
        <div class="ts-type">${type}</div>
        <div class="ts-name">${name || "—"}</div>
        ${description ? `<div class="ts-desc">${description}</div>` : ""}
        ${meta.filter(Boolean).map(m => `<div class="ts-meta">${m}</div>`).join("")}
    `;
    return div;
}

function _disableButtons(container) {
    container.querySelectorAll("button").forEach(b => b.disabled = true);
}
