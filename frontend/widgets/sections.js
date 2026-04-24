/**
 * Chat widget: section list for cut-plan approval.
 *
 * The operator can:
 *   - Uncheck sections they want to exclude from the selection.
 *   - Add a new custom section (by name + page range).
 *   - Apply those edits, then approve.
 *
 * Page-level editing is not exposed here because the extraction pipeline
 * operates on sections, not individual pages. The operator's page-level
 * lever is the section's [start, end] range, or asking the chatbot to
 * re-extract a specific range after extraction.
 */

export function renderSectionsWidget(payload, onAction) {
    const {
        sections = [],
        pages_to_keep = [],
        total_pages = 0,
        product_info,
        keyword_fallback_sections = 0,
    } = payload || {};

    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--sections";

    const safeTotal = Number(total_pages) > 0
        ? Number(total_pages)
        : (pages_to_keep.length || "?");
    const header = document.createElement("div");
    header.className = "widget-header";
    header.innerHTML = `
        <span class="widget-icon">📄</span>
        <span class="widget-title">Section Selection</span>
        <span class="widget-meta">${pages_to_keep.length}/${safeTotal} pages selected</span>
    `;
    wrap.appendChild(header);

    const hint = document.createElement("p");
    hint.className = "widget-hint";
    hint.innerHTML = (
        "Uncheck sections you want to exclude, or add a custom one below. " +
        "Editing works at the <strong>section</strong> level — page-level tweaks " +
        "happen during extraction (you can ask me to re-extract a range later). " +
        "Drag the bottom-right corner to resize the panel vertically or horizontally."
    );
    wrap.appendChild(hint);

    if (keyword_fallback_sections > 0) {
        const note = document.createElement("p");
        note.className = "widget-hint widget-hint--warn";
        note.textContent = (
            `Note: ${keyword_fallback_sections} additional keyword-fallback ` +
            "range(s) are not shown here, but their pages are still included " +
            "in the selection for extraction recall."
        );
        wrap.appendChild(note);
    }

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

    const checkboxes = [];
    const originalNames = new Set();

    if (sections.length === 0) {
        const empty = document.createElement("p");
        empty.className = "widget-empty";
        empty.textContent = "No named sections detected — the full document will be used.";
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
            checkboxes.push(chk);
            originalNames.add(String(sec.name || ""));

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

    // ── Add-section form ─────────────────────────────────────────────
    const addWrap = document.createElement("details");
    addWrap.className = "widget-section-add";
    const summary = document.createElement("summary");
    summary.textContent = "+ Add a custom section";
    addWrap.appendChild(summary);

    const form = document.createElement("div");
    form.className = "widget-section-add-form";
    form.innerHTML = `
        <input type="text" class="widget-input wsa-name" placeholder="Section name (e.g. Fault codes)" />
        <input type="number" class="widget-input wsa-start" placeholder="Start" min="1" />
        <input type="number" class="widget-input wsa-end" placeholder="End" min="1" />
        <button type="button" class="btn-secondary btn-sm wsa-add">Add</button>
    `;
    addWrap.appendChild(form);
    wrap.appendChild(addWrap);

    const pendingAdds = [];
    const pendingAddsBox = document.createElement("div");
    pendingAddsBox.className = "widget-section-pending";
    wrap.appendChild(pendingAddsBox);

    const renderPendingAdds = () => {
        pendingAddsBox.innerHTML = "";
        if (!pendingAdds.length) return;
        const h = document.createElement("div");
        h.className = "widget-section-pending-title";
        h.textContent = "Pending additions (will be applied on Apply/Approve):";
        pendingAddsBox.appendChild(h);
        pendingAdds.forEach((pa, idx) => {
            const row = document.createElement("div");
            row.className = "widget-section-pending-row";
            row.textContent = `${pa.name} (pp. ${pa.start_page}–${pa.end_page})`;
            const rm = document.createElement("button");
            rm.type = "button";
            rm.className = "btn-secondary btn-xs";
            rm.textContent = "Remove";
            rm.addEventListener("click", () => {
                pendingAdds.splice(idx, 1);
                renderPendingAdds();
            });
            row.appendChild(rm);
            pendingAddsBox.appendChild(row);
        });
    };

    form.querySelector(".wsa-add").addEventListener("click", () => {
        const name = String(form.querySelector(".wsa-name").value || "").trim();
        const start = parseInt(form.querySelector(".wsa-start").value, 10);
        const end = parseInt(form.querySelector(".wsa-end").value, 10);
        if (!name || !Number.isFinite(start) || !Number.isFinite(end) || end < start) {
            return;
        }
        pendingAdds.push({ name, start_page: start, end_page: end });
        form.querySelector(".wsa-name").value = "";
        form.querySelector(".wsa-start").value = "";
        form.querySelector(".wsa-end").value = "";
        renderPendingAdds();
    });

    // ── Actions ──────────────────────────────────────────────────────
    const collectEdits = () => {
        const remove_section_names = checkboxes
            .filter((chk) => !chk.checked)
            .map((chk) => chk.dataset.name);
        return {
            remove_section_names,
            add_sections: pendingAdds.slice(),
        };
    };

    const hasPendingEdits = () => {
        const edits = collectEdits();
        return edits.remove_section_names.length > 0 || edits.add_sections.length > 0;
    };

    const actions = document.createElement("div");
    actions.className = "widget-actions";

    const applyBtn = document.createElement("button");
    applyBtn.className = "btn-secondary btn-sm";
    applyBtn.textContent = "Apply edits";
    applyBtn.disabled = true;
    applyBtn.addEventListener("click", () => {
        if (!hasPendingEdits()) return;
        const edits = collectEdits();
        applyBtn.disabled = true;
        applyBtn.textContent = "Applying…";
        onAction("edit_cut_plan", edits);
    });

    const refreshApplyBtn = () => {
        applyBtn.disabled = !hasPendingEdits();
    };
    checkboxes.forEach((chk) => chk.addEventListener("change", refreshApplyBtn));
    form.querySelector(".wsa-add").addEventListener("click", refreshApplyBtn);

    const approveBtn = document.createElement("button");
    approveBtn.className = "btn-primary btn-sm";
    approveBtn.textContent = "Approve & Continue";
    approveBtn.addEventListener("click", () => {
        approveBtn.disabled = true;
        applyBtn.disabled = true;
        approveBtn.textContent = "Approving…";
        if (hasPendingEdits()) {
            // Apply edits first; backend re-renders the widget with updated
            // state. The operator then clicks Approve on the refreshed widget.
            const edits = collectEdits();
            onAction("edit_cut_plan", edits);
            return;
        }
        onAction("approve_cut_plan", {});
    });

    actions.appendChild(applyBtn);
    actions.appendChild(approveBtn);
    wrap.appendChild(actions);

    return wrap;
}
