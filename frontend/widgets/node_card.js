/**
 * Chat widget: ontology node card (for review and manual add-node draft).
 */

export function renderNodeCard(node, nodeType, { isDraft = false, onConfirm, onEdit } = {}) {
    const wrap = document.createElement("div");
    wrap.className = `chat-widget chat-widget--node-card${isDraft ? " chat-widget--draft" : ""}`;

    const typeColor = {
        Asset: "#5b8dee",
        Component: "#48bb78",
        Symptom: "#ed8936",
        FailureMode: "#e53e3e",
        CorrectiveAction: "#38b2ac",
        ErrorCode: "#805ad5",
    }[nodeType] || "#a0aec0";

    const header = document.createElement("div");
    header.className = "widget-header";
    header.innerHTML = `
        <span class="widget-type-badge" style="background:${typeColor}">${nodeType}</span>
        <span class="widget-title">${node.name || "—"}</span>
        ${isDraft ? "<span class=\"widget-meta draft-badge\">DRAFT — pending confirmation</span>" : ""}
    `;
    wrap.appendChild(header);

    if (node.description) {
        const desc = document.createElement("p");
        desc.className = "node-description";
        desc.textContent = node.description;
        wrap.appendChild(desc);
    }

    // Extra fields
    const extras = [];
    if (node.brand) extras.push(`Brand: ${node.brand}`);
    if (node.model) extras.push(`Model: ${node.model}`);
    if (node.material_context) extras.push(`Material context: ${node.material_context}`);
    if (node.instruction_text) extras.push(`Steps: ${node.instruction_text}`);
    if (extras.length) {
        const extrasDiv = document.createElement("div");
        extrasDiv.className = "node-extras";
        extrasDiv.innerHTML = extras.map(e => `<span class="node-meta">${e}</span>`).join("");
        wrap.appendChild(extrasDiv);
    }

    if (isDraft && onConfirm) {
        const actions = document.createElement("div");
        actions.className = "widget-actions";

        const confirmBtn = document.createElement("button");
        confirmBtn.className = "btn-primary btn-sm";
        confirmBtn.textContent = "Confirm & Add";
        confirmBtn.addEventListener("click", () => {
            confirmBtn.disabled = true;
            onConfirm(node, nodeType);
        });

        actions.appendChild(confirmBtn);
        wrap.appendChild(actions);
    }

    return wrap;
}
