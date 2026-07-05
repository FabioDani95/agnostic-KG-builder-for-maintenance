// E2E for the HITL console (frontend/console.html) against the real backend
// in mock-LLM mode: new session advances deterministically to scoping
// (propose_cut_plan), approval reaches the ontology draft, review decisions
// persist across a reload, and export stays locked before the export phase.
const { test, expect } = require("@playwright/test");

test("console: new session flow, decision persistence, export gating", async ({ page }) => {
  test.setTimeout(180000);
  await page.setViewportSize({ width: 1440, height: 900 });

  await page.goto("/console.html");
  await expect(page.getByRole("heading", { name: "Sessioni" })).toBeVisible();

  // New session: fixture manual is preselected as the only entry.
  await page.getByRole("button", { name: "+ Nuova sessione" }).click();
  await expect(page.getByText("e2e_pump_manual.pdf").first()).toBeVisible();
  await page.getByRole("button", { name: "Carica il PDF e avvia" }).click();

  // The console must kick scoping itself (propose_cut_plan): the run may not
  // stay parked in the "loaded" phase.
  const header = page.locator(".c-header");
  await expect(header).toContainText("fase: scoping", { timeout: 60000 });
  const runShort = (await header.innerText()).match(/run_[0-9a-f]+/)[0];

  // Approve the page selection → chained ontology draft.
  await page.getByRole("button", { name: "Scoping" }).click();
  await page.getByRole("button", { name: "Approva selezione e continua" }).click();
  await expect(header).toContainText("fase: ontology_draft", { timeout: 60000 });

  // From the draft phase the console offers the extraction step (run_extraction).
  await page.getByRole("button", { name: "Dashboard" }).click();
  await expect(page.getByRole("button", { name: "Avvia estrazione" })).toBeVisible();

  // Export is locked before the export phase even with a clean queue.
  await page.getByRole("button", { name: "Export", exact: true }).click();
  await expect(page.getByText("Estrazione non completata")).toBeVisible();
  await expect(page.getByRole("button", { name: /Esporta/ })).toBeDisabled();

  // Handle the advisory queue item from the inspector.
  await page.getByRole("button", { name: /Review Center/ }).click();
  await page.locator(".c-main .card button.row-hover").first().click();
  await page.locator(".c-inspector").getByRole("button", { name: "Prendi atto" }).click();
  await expect(header).toContainText("1 di 1 gestiti");

  // The decision must survive a full reload + reopen from the sessions list.
  await page.reload();
  await expect(page.getByRole("heading", { name: "Sessioni" })).toBeVisible();
  const row = page.locator(".c-main .card > div", { hasText: runShort });
  await row.getByRole("button", { name: "Apri" }).click();
  await expect(header).toContainText("1 di 1 gestiti", { timeout: 30000 });
});
