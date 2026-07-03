export const WIDGET_RENDERERS = Object.freeze({
    sections: "sections",
    ontology_review: "ontology_review",
    triplet: "triplet",
    triplet_review_start: "triplet_review_start",
    required_fields: "required_fields",
    node_draft: "node_draft",
    extraction_graph: "extraction_graph",
    modify_workspace_sync: "modify_workspace_sync",
    export: "export",
    run_metrics: "run_metrics",
});

export const NON_SHEET_WIDGET_TYPES = new Set([
    "extraction_graph",
    "modify_workspace_sync",
    "export",
    "run_metrics",
]);

export function registeredWidgetTypes() {
    return Object.keys(WIDGET_RENDERERS);
}

export function renderRegisteredWidget(widgetType, payload, handlers) {
    const handlerName = WIDGET_RENDERERS[widgetType];
    if (!handlerName || !handlers || typeof handlers[handlerName] !== "function") {
        return { handled: false, element: null };
    }
    return {
        handled: true,
        element: handlers[handlerName](payload) || null,
    };
}
