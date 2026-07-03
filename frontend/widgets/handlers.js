/**
 * Widget handler wiring shared by the chat UI and the contract tests.
 *
 * `buildWidgetHandlers` returns the widget_type → renderer map consumed by
 * `renderRegisteredWidget`. The host app injects its integrations through
 * `ctx` (chat.js in production, stubs in tests/widget_render.spec.js), so the
 * per-widget wiring below has a single implementation exercised by both.
 *
 * ctx contract:
 *   onAction(action, payload)          — post a chat action to the backend
 *   sendMessage(text)                  — send a chat message to the backend
 *   showExtractionGraph(graph, opts)   — render the KG panel (side effect)
 *   refreshModifyWorkspace(payload)    — sync the modify workspace (side effect)
 *   syncQuickActions(context)          — refresh quick-action chips
 *   showTripletGraphFocus(payload)     — focus the graph on a triplet
 *   navigateToTripletSource(triplet)   — scroll the PDF to the evidence page
 *   renderOntologyReview(payload, onAction) → HTMLElement
 *   renderExport(payload)              → HTMLElement | null
 *   renderRunMetrics(metrics)          → HTMLElement | null
 */

import { renderSectionsWidget } from "./sections.js?v=20260424a";
import { renderTripletWidget } from "./triplet.js?v=20260501a";
import { renderRequiredFieldsWidget } from "./required_fields.js?v=20260422d";
import { renderNodeCard } from "./node_card.js?v=20260422d";

export function buildWidgetHandlers(payload, ctx) {
    return {
        extraction_graph: () => {
            ctx.showExtractionGraph(payload?.graph || payload, { mode: "all" });
            ctx.syncQuickActions({ widget: "extraction_graph", payload });
            return null;
        },
        modify_workspace_sync: () => {
            ctx.refreshModifyWorkspace(payload);
            ctx.syncQuickActions({ widget: "modify_workspace_sync", payload });
            return null;
        },
        sections: () => renderSectionsWidget(payload, ctx.onAction),
        ontology_review: () => ctx.renderOntologyReview(payload, ctx.onAction),
        triplet_review_start: () => {
            // Request the first triplet from the backend via message
            ctx.sendMessage("[system: begin triplet review]");
            return null;
        },
        triplet: () => {
            const el = renderTripletWidget(payload, ctx.onAction);
            ctx.showTripletGraphFocus(payload);
            ctx.navigateToTripletSource(payload?.triplet);
            return el;
        },
        required_fields: () => renderRequiredFieldsWidget(payload, ctx.onAction),
        node_draft: () => {
            if (!payload.node_type) return null;
            const draftNode = {
                name: payload.normalized_name || payload.raw_text || "",
                description: payload.normalized_description || "",
            };
            return renderNodeCard(draftNode, payload.node_type, {
                isDraft: true,
                onConfirm: (node, type) => ctx.onAction("confirm_node_manual", { node_type: type, node }),
            });
        },
        export: () => ctx.renderExport(payload),
        run_metrics: () => ctx.renderRunMetrics(payload?.metrics || payload),
    };
}
