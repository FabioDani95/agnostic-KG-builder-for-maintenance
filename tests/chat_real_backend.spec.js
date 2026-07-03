// True end-to-end coverage: no page.route interception. The browser drives the
// real FastAPI backend (KG_LLM_MODE=mock, see playwright.config.js), so the SSE
// stream, widget payloads and human actions cross the real HTTP boundary.
const fs = require("fs");
const path = require("path");
const { test, expect } = require("@playwright/test");

const RUNS_DIR = path.join(__dirname, "..", "runs_e2e");

test("real backend chat flow: load manual, propose sections, approve, draft ontology", async ({ page }) => {
  test.setTimeout(180000);
  await page.setViewportSize({ width: 1500, height: 960 });

  await page.goto("/");
  await expect(page.getByText("Diagnostic Knowledge Graph Extraction")).toBeVisible();

  // The manual list comes from the real /api/manuals (KG_MANUALS_DIR fixture dir).
  await page.locator("#manual-select").selectOption("e2e_pump_manual.pdf");
  await page.locator("#upload-form").evaluate((form) =>
    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })),
  );

  // Real /api/load-manual + /chat/start + SSE greeting.
  await expect(page.locator("#chat-layout")).toBeVisible();
  await expect(page.locator("#chat-doc-title")).toContainText("e2e_pump_manual.pdf");

  // "continue" routes deterministically to propose_cut_plan on the backend.
  await page.locator("#chat-input").fill("continue");
  await page.locator("#chat-input-form").evaluate((form) =>
    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })),
  );

  await expect(page.getByRole("heading", { name: "Section Selection" })).toBeVisible({ timeout: 60000 });

  // Approving runs the real gate + approve_cut_plan → chained draft_ontology.
  await page.getByRole("button", { name: "Approve & Continue" }).click();
  await expect(page.getByRole("dialog", { name: "Ontology Draft Ready" })).toBeVisible({ timeout: 60000 });

  // The run must be persisted under the isolated runs dir with real events.
  const runDirs = fs.readdirSync(RUNS_DIR).filter((name) =>
    fs.existsSync(path.join(RUNS_DIR, name, "manifest.json")),
  );
  expect(runDirs.length).toBeGreaterThan(0);
  const latest = runDirs
    .map((name) => ({ name, mtime: fs.statSync(path.join(RUNS_DIR, name)).mtimeMs }))
    .sort((a, b) => b.mtime - a.mtime)[0].name;
  const runDir = path.join(RUNS_DIR, latest);

  const manifest = JSON.parse(fs.readFileSync(path.join(runDir, "manifest.json"), "utf8"));
  expect(manifest.filename).toBe("e2e_pump_manual.pdf");
  expect(manifest.page_count).toBe(3);

  const events = fs.readFileSync(path.join(runDir, "events.jsonl"), "utf8")
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
  const kinds = new Set(events.map((event) => event.kind));
  expect(kinds.has("chat_event")).toBe(true);
  expect(kinds.has("human_action")).toBe(true);
  const widgets = events
    .filter((event) => event.kind === "chat_event" && event.event?.type === "widget")
    .map((event) => event.event.widget);
  expect(widgets).toContain("sections");
  expect(widgets).toContain("ontology_review");
});
