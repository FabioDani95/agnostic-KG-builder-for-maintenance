const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

function widgetFixtures() {
  const dir = path.join(__dirname, "fixtures", "widgets");
  return fs.readdirSync(dir)
    .filter((name) => name.endsWith(".json"))
    .map((name) => JSON.parse(fs.readFileSync(path.join(dir, name), "utf8")));
}

// Widgets whose real handler renders an element into the chat stream.
const ELEMENT_WIDGETS = new Set([
  "sections",
  "ontology_review",
  "triplet",
  "required_fields",
  "node_draft",
  "export",
  "run_metrics",
]);

// Widgets whose real handler performs a host-app side effect instead.
const SIDE_EFFECT_WIDGETS = {
  extraction_graph: "showExtractionGraph",
  modify_workspace_sync: "refreshModifyWorkspace",
  triplet_review_start: "sendMessage",
};

test("registered widget fixtures render through the real chat handlers", async ({ page }) => {
  const consoleErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));

  await page.goto("/");
  const fixtures = widgetFixtures();

  const rendered = await page.evaluate(async (payloads) => {
    const registry = await import("/widgets/registry.js");
    const { buildWidgetHandlers } = await import("/widgets/handlers.js");

    const mount = document.createElement("main");
    mount.id = "widget-contract-mount";
    document.body.replaceChildren(mount);

    const placeholder = (widget, payload) => {
      const el = document.createElement("section");
      el.className = `chat-widget chat-widget--${widget.replaceAll("_", "-")}`;
      el.dataset.widget = widget;
      el.innerHTML = `
        <div class="widget-header">
          <span class="widget-title">${widget}</span>
        </div>
        <div class="chat-widget-body"><pre></pre></div>
      `;
      el.querySelector("pre").textContent = JSON.stringify(payload, null, 2);
      return el;
    };

    return payloads.map((payload) => {
      // The chat-specific integrations (SSE, PDF panel, KG canvas) are
      // stubbed; the per-widget wiring in buildWidgetHandlers is the real
      // production code path.
      const ctxCalls = [];
      const ctx = {
        onAction: () => {},
        sendMessage: () => ctxCalls.push("sendMessage"),
        showExtractionGraph: () => ctxCalls.push("showExtractionGraph"),
        refreshModifyWorkspace: () => ctxCalls.push("refreshModifyWorkspace"),
        syncQuickActions: () => {},
        showTripletGraphFocus: () => {},
        navigateToTripletSource: () => {},
        renderOntologyReview: (p) => placeholder("ontology_review", p),
        renderExport: (p) => placeholder("export", p),
        renderRunMetrics: (p) => placeholder("run_metrics", p),
      };
      const handlers = buildWidgetHandlers(payload, ctx);
      const result = registry.renderRegisteredWidget(payload.widget, payload, handlers);
      if (result.element) mount.appendChild(result.element);
      return {
        widget: payload.widget,
        handled: result.handled,
        nonEmpty: Boolean(
          result.element
          && (result.element.textContent.trim() || result.element.children.length),
        ),
        ctxCalls,
      };
    });
  }, fixtures);

  expect(rendered).toHaveLength(fixtures.length);
  for (const item of rendered) {
    expect(item.handled, `${item.widget} not handled by registry`).toBe(true);
    if (ELEMENT_WIDGETS.has(item.widget)) {
      expect(item.nonEmpty, `${item.widget} rendered an empty element`).toBe(true);
    } else {
      const expectedCall = SIDE_EFFECT_WIDGETS[item.widget];
      expect(expectedCall, `${item.widget} has no expected behavior defined`).toBeTruthy();
      expect(item.ctxCalls, `${item.widget} did not trigger ${expectedCall}`).toContain(expectedCall);
    }
  }
  expect(consoleErrors).toEqual([]);
});
