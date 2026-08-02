const path = require("path");
const { test, expect } = require("@playwright/test");

const fixture = path.resolve(__dirname, "../fixtures/manuals/g1_pdf_inventory.pdf");

test("AC-UX-009: G1 actionable errors and accounting drill-down", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 700 });
  await page.goto("/console.html?foundation=1");

  await expect(page.getByText(
    "Inserisci i dati della targhetta e conferma l’identità della macchina. Solo dopo potrai caricare i documenti che la riguardano."
  )).toBeVisible();
  const serialInfo = page.locator('[data-info-tip="numero-seriale"]');
  await serialInfo.focus();
  await expect(serialInfo.getByRole("tooltip")).toBeVisible();
  await expect(serialInfo.getByRole("tooltip")).toContainText("S/N");

  await page.locator('[name="name"]').fill("Hydraulic Press 7");
  await page.locator('[name="brand"]').fill("ExampleWorks");
  await page.locator('[name="model"]').fill("HP-700");
  await page.locator('[name="asset_type"]').fill("hydraulic_press");
  await page.locator('[name="description"]').fill("Hydraulic forming press in maintenance bay seven.");
  await page.locator('[name="serial"]').fill("HP7-000042");
  await page.locator('[name="reason"]').fill("Identity read directly from the machine nameplate.");
  await page.locator('[name="operator"]').fill("FD");
  await page.getByRole("button", { name: "Salva macchina e continua" }).click();
  await expect(page.getByRole("heading", { name: "Hydraulic Press 7" })).toBeVisible();
  await expect(page.getByText("HP7-000042")).toBeVisible();
  await expect(page.getByText("hydraulic_press")).toBeVisible();

  // An isolated source error remains actionable and does not hide the machine.
  await expect(page.getByText("Scegli un file", { exact: true })).toBeVisible();
  const documentTypeInfo = page.locator('[data-info-tip="tipo-documento"]');
  await documentTypeInfo.focus();
  await expect(documentTypeInfo.getByRole("tooltip")).toBeVisible();
  await expect(documentTypeInfo.getByRole("tooltip")).toContainText("Normativa");
  await page.locator('#source-upload input[type="file"]').setInputFiles({
    name: "unsupported.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("unsupported source"),
  });
  await page.getByRole("button", { name: "Carica documento" }).click();
  const error = page.getByRole("alert");
  await expect(error).toContainText("Formato non supportato");
  await expect(error).toContainText("Cosa è rimasto invariato:");
  await expect(error).toContainText("Cosa puoi fare:");
  await expect(error.getByText("Dettaglio tecnico")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Hydraulic Press 7" })).toBeVisible();

  // Structured files keep the user's position and expose the real G1 boundary.
  const main = page.locator(".foundation-main");
  await page.locator('#source-upload select[name="authority"]').selectOption("observational");
  await page.locator('#source-upload input[type="file"]').setInputFiles({
    name: "hydraulic_press_logs.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "machine_serial,event_timestamp,action_taken\n"
      + "HP7-000042,2026-07-26T13:44:00+02:00,Backup battery replaced\n"
    ),
  });
  await main.evaluate((element) => {
    element.scrollTop = element.scrollHeight;
  });
  expect(await main.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".assessment-resolution")).toBeVisible();
  expect(await main.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);

  await page.locator('.assessment-resolution [name="reason"]').fill(
    "Seriale HP7-000042 verificato nel CSV caricato."
  );
  await page.locator('.assessment-resolution [name="operator"]').fill("FD");
  await page.getByRole("button", { name: "Conferma associazione" }).scrollIntoViewIfNeeded();
  const beforeConfirmation = await main.evaluate((element) => element.scrollTop);
  await page.getByRole("button", { name: "Conferma associazione" }).click();
  const structuredReady = page.getByTestId("structured-g1-ready");
  await expect(structuredReady).toContainText("non ci sono pagine da scegliere");
  await expect(structuredReady).toContainText("In questa schermata non devi premere altro");
  await expect(page.locator('[data-flow-step="3"]')).toContainText("File pronto");
  await expect(page.locator('[data-flow-step="4"]')).toContainText("Righe · G2");
  const afterConfirmation = await main.evaluate((element) => element.scrollTop);
  expect(afterConfirmation).toBeGreaterThan(0);
  expect(Math.abs(afterConfirmation - beforeConfirmation)).toBeLessThan(80);

  await page.getByRole("button", { name: "Modifica la decisione" }).scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: "Modifica la decisione" }).click();
  await expect(page.locator(".assessment-resolution")).toBeVisible();
  expect(await main.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await page.locator('.assessment-resolution [name="reason"]').fill(
    "Seriale HP7-000042 ricontrollato nel CSV."
  );
  await page.locator('.assessment-resolution [name="operator"]').fill("FD");
  await page.getByRole("button", { name: "Conferma associazione" }).click();
  await expect(page.getByTestId("structured-g1-ready")).toBeVisible();

  await page.locator('#source-upload input[type="file"]').setInputFiles(fixture);
  await expect(page.locator("[data-source-file-name]")).toHaveText("g1_pdf_inventory.pdf");
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.getByText("g1_pdf_inventory.pdf")).toBeVisible({ timeout: 30000 });
  await page.getByRole("button", { name: "Controlla le pagine proposte" }).click();
  await expect(page.getByRole("button", { name: "Analisi del PDF in corso…" })).toBeDisabled();
  const scopeHeading = page.getByRole("heading", { name: "Controlla le pagine proposte" });
  await expect(scopeHeading).toBeVisible({ timeout: 30000 });
  await expect(scopeHeading).toBeFocused();
  await expect(page.getByText("Proposta automatica pronta")).toBeVisible();
  await expect(page.locator('[data-flow-step="3"]')).toHaveClass(/is-current/);
  await expect(page.locator('[data-flow-step="4"]')).not.toHaveClass(/is-current/);
  await expect(page.locator(".scope-page-card")).toHaveCount(5);
  await expect(page.locator(".scope-page-preview[open]")).toHaveCount(0);
  await expect(page.locator('[data-scope-page="5"]')).toContainText("61 righe tabella");
  const pageCountsInfo = page.locator('[data-info-tip="conteggi-pagina"]');
  await pageCountsInfo.focus();
  await expect(pageCountsInfo.getByRole("tooltip")).toBeVisible();
  await expect(pageCountsInfo.getByRole("tooltip")).toContainText("blocchi di testo");
  const firstExclusionReason = page.locator('[data-scope-page="1"] .scope-exclusion-reason');
  await expect(firstExclusionReason).toBeHidden();
  await page.locator("#scope-page-1").uncheck();
  await expect(firstExclusionReason).toBeVisible();
  await page.locator("#scope-page-1").check();
  await expect(firstExclusionReason).toBeHidden();
  await page.locator('#pdf-scope [name="operator"]').fill("FD");
  await page.getByRole("button", { name: "Approva la proposta e continua" }).click();

  const accounting = page.getByTestId("g1-accounting");
  await expect(accounting).toBeVisible({ timeout: 30000 });
  await expect(accounting).toBeFocused();
  await expect(page.locator('[data-flow-step="3"]')).toHaveClass(/is-done/);
  await expect(page.locator('[data-flow-step="4"]')).toHaveClass(/is-current/);
  await expect(accounting).toContainText("Pronto per il tuo controllo");
  await expect(accounting).toContainText("✓ Controllo superato");
  await expect(accounting).toContainText("5 pagine del PDF");
  await expect(accounting).toContainText("0 senza esito");
  const elementsInfo = accounting.locator('[data-info-tip="elementi-trovati"]');
  await elementsInfo.focus();
  await expect(elementsInfo.getByRole("tooltip")).toBeVisible();
  await expect(elementsInfo.getByRole("tooltip")).toContainText("blocchi di testo");
  await expect(accounting.locator("[data-accounting-page]")).toHaveCount(5);
  await expect(accounting.locator("[data-accounting-page-detail]")).toContainText("Seleziona una pagina");
  await accounting.locator('[data-accounting-page="5"]').click();
  const pageFive = accounting.locator("[data-accounting-page-detail]");
  await expect(pageFive).toContainText("Pagina 5");
  await expect(pageFive).toContainText("61 righe");
  await pageFive.locator("[data-accounting-search]").fill("G1_TABLE_5_ROW_61_MARKER");
  // The marker is preserved both in the native text block and in structured row 61.
  await expect(pageFive).toContainText("2 risultati");
  await expect(pageFive).toContainText("G1_TABLE_5_ROW_61_MARKER");
  await expect(pageFive).toContainText("Pagina 5 · Tabella 5 · Riga 61");

  await page.reload();
  await page.getByRole("button", { name: "Controlla le pagine proposte" }).click();
  await expect(page.getByTestId("g1-accounting")).toContainText("Pronto per il tuo controllo");
});
