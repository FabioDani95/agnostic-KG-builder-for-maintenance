/**
 * Chat widget: section list for cut-plan approval.
 * Renders an interactive list of sections with checkboxes and an approve button.
 */

export function renderSectionsWidget(payload, onAction) {
    const { sections = [], pages_to_keep = [], total_pages = 0, product_info } = payload;

    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--sections";

    // Header
    const header = document.createElement("div");
    header.className = "widget-header";
    header.innerHTML = `
        <span class="widget-icon">📄</span>
        <span class="widget-title">Section Selection</span>
        <span class="widget-meta">${pages_to_keep.length}/${total_pages} pages selected</span>
    `;
    wrap.appendChild(header);

    const hint = document.createElement("p");
    hint.className = "widget-hint";
    hint.textContent = "Review the detected sections. Scroll inside the panel or drag its lower-right corner to resize it.";
    wrap.appendChild(hint);

    // Product info
    if (product_info && product_info.product_name) {
        const infoDiv = document.createElement("div");
        infoDiv.className = "widget-info-row";
        const assetLabel = document.createElement("span");
        assetLabel.className = "wi-label";
        assetLabel.textContent = "Asset";
        const assetValue = document.createElement("span");
        assetValue.className = "wi-value";
        assetValue.textContent = product_info.product_name;
        infoDiv.appendChild(assetLabel);
        infoDiv.appendChild(assetValue);

        if (product_info.document_type) {
            const typeLabel = document.createElement("span");
            typeLabel.className = "wi-label";
            typeLabel.textContent = "Type";
            const typeValue = document.createElement("span");
            typeValue.className = "wi-value";
            typeValue.textContent = product_info.document_type;
            infoDiv.appendChild(typeLabel);
            infoDiv.appendChild(typeValue);
        }
        wrap.appendChild(infoDiv);
    }

    // Section list
    if (sections.length === 0) {
        const empty = document.createElement("p");
        empty.className = "widget-empty";
        empty.textContent = "No sections detected — the full document will be used.";
        wrap.appendChild(empty);
    } else {
        const list = document.createElement("div");
        list.className = "widget-section-list";
        sections.forEach((sec, idx) => {
            const row = document.createElement("div");
            row.className = "section-row";
            const chk = document.createElement("input");
            chk.type = "checkbox";
            chk.checked = true;
            chk.id = `sec-chk-${idx}`;
            chk.dataset.name = sec.name;
            const label = document.createElement("label");
            label.htmlFor = chk.id;
            label.className = "section-row-info";

            const title = document.createElement("div");
            title.className = "section-row-title";
            title.textContent = sec.name || `Section ${idx + 1}`;

            const pages = document.createElement("div");
            pages.className = "section-row-pages";
            pages.textContent = `pp. ${sec.start}–${sec.end}`;

            label.appendChild(title);
            label.appendChild(pages);
            row.appendChild(chk);
            row.appendChild(label);
            list.appendChild(row);
        });
        wrap.appendChild(list);
    }

    // Actions
    const actions = document.createElement("div");
    actions.className = "widget-actions";

    const approveBtn = document.createElement("button");
    approveBtn.className = "btn-primary btn-sm";
    approveBtn.textContent = "Approve & Continue";
    approveBtn.addEventListener("click", () => {
        approveBtn.disabled = true;
        approveBtn.textContent = "Approving…";
        onAction("approve_cut_plan", {});
    });

    actions.appendChild(approveBtn);
    wrap.appendChild(actions);

    return wrap;
}
