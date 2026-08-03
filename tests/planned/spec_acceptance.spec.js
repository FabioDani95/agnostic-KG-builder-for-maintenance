const path = require("path");
const fs = require("fs");
const { test, expect } = require("@playwright/test");

const fixture = path.resolve(__dirname, "../fixtures/manuals/g1_pdf_inventory.pdf");
const secondPdfFixture = path.resolve(
  __dirname,
  "../golden/workspaces/ds003/raw/maintenance_manual.pdf"
);

test("AC-UX-002/003/009: G1 multi-upload and automatic PDF preparation", async ({ page }) => {
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
  await expect(page.getByText("Scegli file", { exact: true })).toBeVisible();
  const documentTypeInfo = page.locator('[data-info-tip="tipo-documento"]');
  await documentTypeInfo.focus();
  await expect(documentTypeInfo.getByRole("tooltip")).toBeVisible();
  await expect(documentTypeInfo.getByRole("tooltip")).toContainText("Normativa");
  let sourcePostRequests = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && /\/api\/workspaces\/[^/]+\/sources$/.test(request.url())) {
      sourcePostRequests += 1;
    }
  });
  await page.locator('#source-upload input[type="file"]').setInputFiles({
    name: "unsupported.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("unsupported source"),
  });
  const error = page.getByRole("alert");
  await expect(error).toContainText("Formato non supportato");
  await expect(error).toContainText("Cosa è rimasto invariato:");
  await expect(error).toContainText("Cosa puoi fare:");
  await expect(error.getByText("Dettaglio tecnico")).toBeVisible();
  await expect(page.getByRole("button", { name: "Carica documento" })).toBeDisabled();
  expect(sourcePostRequests).toBe(0);
  await expect(page.getByRole("heading", { name: "Hydraulic Press 7" })).toBeVisible();

  // Multiple PDF and CSV files are accepted in one operation. PDF preparation
  // includes every page automatically and exposes no page-by-page gate.
  const main = page.locator(".foundation-main");
  await page.locator('#source-upload select[name="authority"]').selectOption("observational");
  await page.locator('#source-upload input[type="file"]').setInputFiles([
    {
      name: path.basename(fixture),
      mimeType: "application/pdf",
      buffer: fs.readFileSync(fixture),
    },
    {
      name: path.basename(secondPdfFixture),
      mimeType: "application/pdf",
      buffer: fs.readFileSync(secondPdfFixture),
    },
    {
      name: "hydraulic_press_logs_a.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(
        "machine_serial,event_timestamp,action_taken\n"
        + "HP7-000042,2026-07-26T13:44:00+02:00,Backup battery replaced\n"
      ),
    },
    {
      name: "hydraulic_press_logs_b.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(
        "machine_serial,event_timestamp,action_taken\n"
        + "HP7-000042,2026-07-27T08:15:00+02:00,Hydraulic seal inspected\n"
      ),
    },
  ]);
  await expect(page.locator("[data-source-file-name]")).toHaveText("4 file selezionati");
  await main.evaluate((element) => {
    element.scrollTop = element.scrollHeight;
  });
  expect(await main.evaluate((element) => element.scrollTop)).toBeGreaterThan(0);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".foundation-source")).toHaveCount(4, { timeout: 60000 });
  await expect(page.locator(".assessment-resolution")).toHaveCount(0);
  await expect(page.getByTestId("g1-ready")).toHaveCount(0);
  await expect(page.locator(".source-ready")).toHaveCount(4);
  await expect(page.locator(".source-ready")).toHaveText([
    "Caricato", "Caricato", "Caricato", "Caricato",
  ]);
  await expect(page.locator('[data-flow-step="3"]')).toContainText("Controllo file");
  await expect(page.locator('[data-flow-step="3"]')).toHaveClass(/is-done/);
  await expect(page.locator('[data-flow-step="4"]')).toContainText("Struttura dati");
  await expect(page.getByRole("button", { name: "Controlla le pagine proposte" })).toHaveCount(0);
  await expect(page.locator(".scope-page-card")).toHaveCount(0);

  // Repeating an active PDF is blocked before upload and clearly flagged.
  const requestsBeforeDuplicate = sourcePostRequests;
  await page.locator('#source-upload input[type="file"]').setInputFiles(fixture);
  await expect(page.getByRole("alert")).toContainText("Documento già caricato");
  await expect(page.getByRole("alert")).toContainText("Non serve caricarlo di nuovo");
  await expect(page.getByRole("button", { name: "Carica documento" })).toBeDisabled();
  expect(sourcePostRequests).toBe(requestsBeforeDuplicate);
  await expect(page.locator(".foundation-source")).toHaveCount(4, { timeout: 60000 });

  const removeCsv = page.getByRole("button", { name: "Rimuovi file hydraulic_press_logs_a.csv" });
  await expect(removeCsv).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Rimuovere “hydraulic_press_logs_a.csv”?");
    await dialog.dismiss();
  });
  await removeCsv.click();
  await expect(page.getByText("hydraulic_press_logs_a.csv")).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Potrai ricaricarlo in seguito");
    await dialog.accept();
  });
  await removeCsv.click();
  await expect(page.getByText("hydraulic_press_logs_a.csv")).toHaveCount(0);
  await expect(page.getByText("hydraulic_press_logs_b.csv")).toBeVisible();
  await expect(page.locator(".foundation-source")).toHaveCount(3);

  await page.locator('#source-upload input[type="file"]').setInputFiles({
    name: "hydraulic_press_logs_a.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "machine_serial,event_timestamp,action_taken\n"
      + "HP7-000042,2026-07-26T13:44:00+02:00,Backup battery replaced\n"
    ),
  });
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.getByText("hydraulic_press_logs_a.csv")).toBeVisible();
  await expect(page.locator(".foundation-source")).toHaveCount(4);

  const removePdf = page.getByRole("button", { name: "Rimuovi file g1_pdf_inventory.pdf" });
  page.once("dialog", (dialog) => dialog.accept());
  await removePdf.click();
  await expect(page.getByText("g1_pdf_inventory.pdf")).toHaveCount(0);
  await page.locator('#source-upload input[type="file"]').setInputFiles(fixture);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.getByText("g1_pdf_inventory.pdf")).toBeVisible({ timeout: 60000 });
  await expect(page.getByRole("alert")).toHaveCount(0);
  await expect(page.locator(".foundation-source")).toHaveCount(4);

  await page.reload();
  await expect(page.locator(".foundation-source")).toHaveCount(4);
  await expect(page.getByTestId("g1-ready")).toHaveCount(0);
  await expect(page.locator('[data-flow-step="4"]')).toContainText("Struttura dati");
  await expect(page.getByRole("button", { name: "Controlla le pagine proposte" })).toHaveCount(0);

  // The lightweight home summarizes the current workspace and reopens it by ID.
  await page.getByRole("link", { name: "Workspace" }).click();
  await expect(page).toHaveURL(/\/home\.html$/);
  await expect(page.getByRole("heading", { name: "I tuoi workspace" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Hydraulic Press 7" })).toBeVisible();
  await expect(page.getByText("4 documenti caricati")).toBeVisible();
  await expect(page.getByText("In revisione", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Apri workspace" }).click();
  await expect(page).toHaveURL(/console\.html\?foundation=1&workspace_id=ws_/);
  await expect(page.locator(".foundation-source")).toHaveCount(4);
  await expect(page.getByRole("heading", { name: "Hydraulic Press 7" })).toBeVisible();

  // The plus action creates a genuinely separate workspace and returns it to the home.
  await page.getByRole("link", { name: "Workspace" }).click();
  await page.getByRole("link", { name: "+ Nuovo workspace" }).click();
  await expect(page).toHaveURL(/console\.html\?foundation=1&new=1/);
  await page.locator('[name="name"]').fill("Conveyor 2");
  await page.locator('[name="brand"]').fill("ExampleWorks");
  await page.locator('[name="model"]').fill("CV-200");
  await page.locator('[name="description"]').fill("Packaging conveyor in production line two.");
  await page.locator('[name="serial"]').fill("CV2-0007");
  await page.locator('[name="reason"]').fill("Identity read directly from the conveyor nameplate.");
  await page.locator('[name="operator"]').fill("FD");
  await page.getByRole("button", { name: "Salva macchina e continua" }).click();
  await expect(page).toHaveURL(/console\.html\?foundation=1&workspace_id=ws_/);
  await expect(page.getByRole("heading", { name: "Conveyor 2" })).toBeVisible();
  await page.getByRole("link", { name: "Workspace" }).click();
  await expect(page.locator(".workspace-home-card")).toHaveCount(2);
  await expect(page.getByRole("heading", { name: "Conveyor 2" })).toBeVisible();
  await expect(page.getByText("0 documenti caricati")).toBeVisible();
});

test("AC-UX-014: G2 is automatic and presents one exception at a time", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/console.html?foundation=1&new=1");
  await page.locator('[name="name"]').fill("G2 Test Press");
  await page.locator('[name="brand"]').fill("ExampleWorks");
  await page.locator('[name="model"]').fill("G2-200");
  await page.locator('[name="description"]').fill("Workspace used for the Gate 2 product test.");
  await page.locator('[name="serial"]').fill("G2-0001");
  await page.locator('[name="reason"]').fill("Identity read from the dedicated test machine nameplate.");
  await page.locator('[name="operator"]').fill("PO");
  await page.getByRole("button", { name: "Salva macchina e continua" }).click();

  await page.locator('#source-upload input[type="file"]').setInputFiles([
    {
      name: "ambiguous-events.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(
        "event_id,description,action_taken\n"
        + "E1,abnormal vibration,inspect bearing\n"
        + "E2,oil leakage,replace seal\n"
      ),
    },
    {
      name: "observations.jsonl",
      mimeType: "application/x-ndjson",
      buffer: Buffer.from(
        '{"event_id":"J1","symptom_observation":"noise","action_taken":"inspect"}\n'
        + '{"event_id":"BROKEN","symptom_observation":\n'
        + '{"event_id":"J2","symptom_observation":"heat","action_taken":"cool"}\n'
      ),
    },
  ]);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".foundation-source")).toHaveCount(2);
  await page.getByRole("link", { name: "Continua alla struttura dati" }).click();

  await expect(page).toHaveURL(/stage=g2/);
  await expect(page.getByRole("heading", { name: "Completa la struttura dei dati" })).toBeVisible();
  await expect(page.locator(".g2-decision")).toHaveCount(1);
  await expect(page.getByText("Serve una sola scelta")).toBeVisible();
  await expect(page.getByText("Dove va usata la colonna “description”?")) .toBeVisible();
  await page.locator('.g2-decision select[name="role"]').selectOption("observation");
  await page.getByRole("button", { name: "Salva e continua" }).click();

  await expect(page.getByRole("heading", { name: "Controlla come verranno usati i dati" })).toBeVisible();
  await expect(page.locator(".g2-source-card.is-ready")).toHaveCount(2);
  await expect(page.locator(".g2-data-table")).toHaveCount(2);
  await expect(page.locator(".g2-graph-mapping")).toHaveCount(2);
  await expect(page.getByText("Grafo nel prossimo passo")).toHaveCount(2);
  await expect(page.getByText("1 avviso gestito")).toBeVisible();
  await expect(page.locator(".g2-decision")).toHaveCount(0);
  await expect(page.getByText("Gate 2", { exact: false })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Conferma fonte/ })).toHaveCount(2);
  await page.getByRole("button", { name: "Conferma fonte ambiguous-events.csv" }).click();
  await expect(page.getByText("Confermata", { exact: true })).toHaveCount(1);
  await expect(page.getByRole("button", { name: /Conferma fonte/ })).toHaveCount(1);
  await page.getByRole("button", { name: "Conferma fonte observations.jsonl" }).click();
  await expect(page.getByRole("heading", { name: "Struttura dati confermata" })).toBeVisible();
  await expect(page.getByText("Confermata", { exact: true })).toHaveCount(2);
  await expect(page.getByRole("button", { name: /Conferma fonte/ })).toHaveCount(0);

  await page.reload();
  await expect(page.getByRole("heading", { name: "Struttura dati confermata" })).toBeVisible();
  await expect(page.locator(".g2-decision")).toHaveCount(0);
});

test("AC-UX-014/AC-TAB-001/AC-LANG-002: CSV variants remain understandable", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto("/console.html?foundation=1&new=1");
  await page.locator('[name="name"]').fill("CSV Robustness Press");
  await page.locator('[name="brand"]').fill("ExampleWorks");
  await page.locator('[name="model"]').fill("CSV-300");
  await page.locator('[name="description"]').fill("Workspace for structured data verification.");
  await page.locator('[name="serial"]').fill("CSV-0001");
  await page.locator('[name="reason"]').fill("Dedicated acceptance fixture.");
  await page.locator('[name="operator"]').fill("PO");
  await page.getByRole("button", { name: "Salva macchina e continua" }).click();

  await page.locator('#source-upload input[type="file"]').setInputFiles([
    {
      name: "eventi-latin1.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(
        "event_timestamp;component;symptom_observation;action_taken;language\n"
        + "2026-01-01T10:00:00Z;pompa;temperatura è alta;pulita valvola;IT\n",
        "latin1"
      ),
    },
    {
      name: "languages.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(
        "language,symptom_observation,action_taken\n"
        + "EN,abnormal noise,inspect bearing\n"
        + "IT,rumore anomalo,ispezionare cuscinetto\n"
        + "DE,ungewoehnliches Geraeusch,Lager pruefen\n"
        + "MIXED,rumore and noise,inspect e controllare\n"
      ),
    },
    {
      name: "righe-irregolari.csv",
      mimeType: "text/csv",
      buffer: Buffer.from(
        "event_id,symptom_observation,action_taken\n"
        + "E1,noise,inspect\n"
        + "E2,leak\n"
        + "E3,heat,cool,unexpected\n"
      ),
    },
  ]);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".foundation-source")).toHaveCount(3);
  await page.getByRole("link", { name: "Continua alla struttura dati" }).click();

  await expect(page.getByRole("heading", { name: "Controlla come verranno usati i dati" })).toBeVisible();
  await expect(page.locator(".g2-data-table")).toHaveCount(3);
  await expect(page.locator(".g2-language-summary").filter({ hasText: "1 IT conservata" }).first()).toBeVisible();
  await expect(page.locator(".g2-language-summary").filter({ hasText: "1 EN pronta" }).first()).toBeVisible();
  await expect(page.locator(".g2-language-summary").filter({ hasText: "1 DE conservata" }).first()).toBeVisible();
  await expect(page.locator(".g2-language-summary").filter({ hasText: "1 lingua mista conservata" }).first()).toBeVisible();
  await expect(page.locator(".g2-isolation-note").filter({ hasText: "Alcune righe hanno un numero errato di colonne" })).toBeVisible();
  await expect(page.getByText("3 record letti · 1 preparati · 2 isolati")).toBeVisible();
  await expect(page.getByRole("button", { name: /Conferma fonte/ })).toHaveCount(3);
});

test("AC-HITL-002/AC-UX-005: each CSV graph is navigable and approved before comparison", async ({ page }) => {
  await page.setViewportSize({ width: 1360, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await page.locator('[name="name"]').fill("G3 Synthetic Press");
  await page.locator('[name="brand"]').fill("ExampleWorks");
  await page.locator('[name="model"]').fill("G3-300");
  await page.locator('[name="description"]').fill("Workspace for source graph verification.");
  await page.locator('[name="serial"]').fill("G3-0001");
  await page.locator('[name="reason"]').fill("Dedicated acceptance fixture.");
  await page.locator('[name="operator"]').fill("PO");
  await page.getByRole("button", { name: "Salva macchina e continua" }).click();

  await page.locator('#source-upload input[type="file"]').setInputFiles([
    path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_it.csv"),
    path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_en.csv"),
  ]);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".foundation-source")).toHaveCount(2);
  await page.getByRole("link", { name: "Continua alla struttura dati" }).click();

  await expect(page.getByRole("button", { name: /Conferma fonte/ })).toHaveCount(2);
  await page.getByRole("button", { name: "Conferma fonte synthetic_press_events_it.csv" }).click();
  await page.getByRole("button", { name: "Conferma fonte synthetic_press_events_en.csv" }).click();
  await expect(page.getByRole("heading", { name: "Struttura dati confermata" })).toBeVisible();
  await page.getByRole("link", { name: "Continua all’elaborazione" }).click();

  await expect(page).toHaveURL(/stage=g3/);
  await expect(page.getByRole("heading", { name: "Controlla un grafo alla volta" })).toBeVisible();
  await expect(page.getByText("Gate 3", { exact: false })).toHaveCount(0);
  await expect(page.locator('[data-flow-step="5"]')).toContainText("Elaborazione");
  await expect(page.locator(".g3-source-card")).toHaveCount(2);
  await expect(page.getByText("Confronto tra fonti non ancora disponibile")).toBeVisible();

  const italianCard = page.locator('[data-g3-source]').filter({ hasText: "synthetic_press_events_it.csv" });
  await italianCard.getByRole("button", { name: "Genera sottografo" }).click();
  await expect(italianCard.getByRole("button", { name: "Approva sottografo" })).toBeVisible();
  await expect(italianCard.locator(".g3-svg-node")).toHaveCount(11);
  await expect(italianCard.locator(".g3-edge")).toHaveCount(12);
  await italianCard.locator('.g3-svg-node[aria-label="Sintomi: Rumore metallico"]').click();
  await expect(italianCard.locator(".g3-node-detail")).toContainText("Rumore metallico");
  await expect(italianCard.locator(".g3-node-detail")).toContainText("Riga 2");
  await expect(italianCard.locator(".g3-node-detail")).toContainText("Riga 4");

  await italianCard.getByRole("button", { name: "Nodi (11)" }).click();
  await italianCard.getByLabel("Cerca nodo").fill("pompa");
  await italianCard.getByLabel("Tipo").selectOption("Component");
  await italianCard.getByRole("button", { name: "Filtra" }).click();
  await expect(italianCard.locator(".g3-table tbody tr")).toHaveCount(1);
  await expect(italianCard.locator(".g3-table tbody tr")).toContainText("Pompa idraulica");
  await italianCard.getByRole("button", { name: "Relazioni (12)" }).click();
  await expect(italianCard.locator(".g3-table thead")).toContainText("Relazione");
  await expect(italianCard.locator(".g3-table tbody tr")).toHaveCount(12);
  await italianCard.getByRole("button", { name: "Approva sottografo" }).click();
  await expect(italianCard.getByText("Sottografo approvato per questa fonte")).toBeVisible();
  await expect(page.getByText("Confronto tra fonti non ancora disponibile")).toBeVisible();

  const englishCard = page.locator('[data-g3-source]').filter({ hasText: "synthetic_press_events_en.csv" });
  await englishCard.getByRole("button", { name: "Genera sottografo" }).click();
  await expect(englishCard.getByRole("button", { name: "Approva sottografo" })).toBeVisible();
  await englishCard.getByRole("button", { name: "Approva sottografo" }).click();
  await expect(page.getByText("Fonti pronte per il confronto")).toBeVisible();
  await expect(page.getByText("2 corrispondenze esatte")).toBeVisible();
  await page.getByText("Vedi le corrispondenze esatte").click();
  await expect(page.locator(".g3-barrier")).toContainText("E-PUMP-17");
  await expect(page.locator(".g3-barrier")).toContainText("E-VALVE-04");
});
