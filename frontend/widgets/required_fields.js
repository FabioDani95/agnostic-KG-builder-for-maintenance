/**
 * Chat widget: required fields form for ontology review.
 */

export function renderRequiredFieldsWidget(payload, onAction) {
    const { human_required_fields = [] } = payload;
    if (!human_required_fields.length) return null;

    const wrap = document.createElement("div");
    wrap.className = "chat-widget chat-widget--required-fields";

    const header = document.createElement("div");
    header.className = "widget-header";
    header.innerHTML = `
        <span class="widget-icon">📝</span>
        <span class="widget-title">Required Information</span>
        <span class="widget-meta">${human_required_fields.length} field(s)</span>
    `;
    wrap.appendChild(header);

    const form = document.createElement("div");
    form.className = "widget-fields-form";

    human_required_fields.slice(0, 5).forEach(field => {
        const row = document.createElement("div");
        row.className = "field-row";

        const label = document.createElement("label");
        label.textContent = field.prompt || field.property_name;
        label.className = "field-label";

        const input = document.createElement("input");
        input.type = "text";
        input.className = "field-input";
        input.placeholder = field.suggested_value || `Enter ${field.property_name}…`;
        input.value = field.suggested_value || "";
        input.dataset.fieldKey = field.field_key;

        if (field.allowed_values && field.allowed_values.length) {
            const select = document.createElement("select");
            select.className = "field-input";
            select.dataset.fieldKey = field.field_key;
            field.allowed_values.forEach(v => {
                const opt = document.createElement("option");
                opt.value = v;
                opt.textContent = v;
                select.appendChild(opt);
            });
            row.appendChild(label);
            row.appendChild(select);
        } else {
            row.appendChild(label);
            row.appendChild(input);
        }

        const submitBtn = document.createElement("button");
        submitBtn.className = "btn-sm btn-secondary";
        submitBtn.textContent = "Set";
        submitBtn.addEventListener("click", () => {
            const el = row.querySelector("[data-field-key]");
            const value = el ? el.value.trim() : "";
            if (!value) return;
            submitBtn.disabled = true;
            submitBtn.textContent = "Saved ✓";
            onAction("fill_required_field", { field_key: field.field_key, value });
        });

        row.appendChild(submitBtn);
        form.appendChild(row);
    });

    if (human_required_fields.length > 5) {
        const more = document.createElement("p");
        more.className = "widget-empty";
        more.textContent = `… and ${human_required_fields.length - 5} more field(s). Fill these first and I'll show the rest.`;
        form.appendChild(more);
    }

    wrap.appendChild(form);
    return wrap;
}
