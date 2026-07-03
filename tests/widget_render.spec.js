const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

function widgetFixtures() {
  const dir = path.join(__dirname, "fixtures", "widgets");
  return fs.readdirSync(dir)
    .filter((name) => name.endsWith(".json"))
    .map((name) => JSON.parse(fs.readFileSync(path.join(dir, name), "utf8")));
}

test("registered widget fixtures render through the frontend registry", async ({ page }) => {
  const consoleErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => consoleErrors.push(error.message));

  await page.goto("/");
  const fixtures = widgetFixtures();

  const rendered = await page.evaluate(async (payloads) => {
    const registry = await import("/widgets/registry.js");
    const sections = await import("/widgets/sections.js");
    const triplet = await import("/widgets/triplet.js");
    const required = await import("/widgets/required_fields.js");
    const nodeCard = await import("/widgets/node_card.js");

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

    const handlers = {
      sections: (payload) => sections.renderSectionsWidget(payload, () => {}),
      ontology_review: (payload) => placeholder("ontology_review", payload),
      triplet: (payload) => triplet.renderTripletWidget(payload, () => {}),
      triplet_review_start: (payload) => placeholder("triplet_review_start", payload),
      required_fields: (payload) => required.renderRequiredFieldsWidget(payload, () => {}),
      node_draft: (payload) => nodeCard.renderNodeCard(
        {
          name: payload.normalized_name || payload.raw_text || "Draft node",
          description: payload.normalized_description || "",
        },
        payload.node_type || "Symptom",
        { isDraft: true, onConfirm: () => {} },
      ),
      extraction_graph: (payload) => placeholder("extraction_graph", payload),
      modify_workspace_sync: (payload) => placeholder("modify_workspace_sync", payload),
      export: (payload) => placeholder("export", payload),
      run_metrics: (payload) => placeholder("run_metrics", payload),
    };

    return payloads.map((payload) => {
      const result = registry.renderRegisteredWidget(payload.widget, payload, handlers);
      if (!result.handled || !result.element) {
        return { widget: payload.widget, handled: result.handled, nonEmpty: false };
      }
      mount.appendChild(result.element);
      return {
        widget: payload.widget,
        handled: result.handled,
        nonEmpty: Boolean(result.element.textContent.trim() || result.element.children.length),
      };
    });
  }, fixtures);

  expect(rendered).toHaveLength(fixtures.length);
  expect(rendered.filter((item) => !item.handled || !item.nonEmpty)).toEqual([]);
  expect(consoleErrors).toEqual([]);
});
