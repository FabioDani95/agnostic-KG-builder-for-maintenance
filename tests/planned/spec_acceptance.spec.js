const path = require("path");
const fs = require("fs");
const { test, expect } = require("@playwright/test");

const fixture = path.resolve(__dirname, "../fixtures/manuals/g1_pdf_inventory.pdf");
const secondPdfFixture = path.resolve(
  __dirname,
  "../golden/workspaces/ds003/raw/maintenance_manual.pdf"
);

/**
 * Identify a machine and land on the documents phase. The four phases are named
 * after the object of work; the internal development checkpoints must not
 * appear in the interface or in the address bar.
 */
async function identifyMachine(page, { name, model, serial, description }) {
  await page.locator('[name="name"]').fill(name);
  await page.locator('[name="brand"]').fill("ExampleWorks");
  await page.locator('[name="model"]').fill(model);
  await page.locator('[name="description"]').fill(description);
  await page.locator('[name="serial"]').fill(serial);
  await page.locator('[name="reason"]').fill("Dati letti direttamente dalla targhetta della macchina.");
  await page.locator('[name="operator"]').fill("PO");
  await page.getByRole("button", { name: "Salva macchina e continua" }).click();
  await expect(page.getByRole("heading", { name })).toBeVisible();
  await page.getByRole("button", { name: "Continua ai documenti" }).click();
  await expect(page.getByRole("heading", { name: "Documenti della macchina" })).toBeVisible();
}

test("AC-UX-002/003/009: multi-upload and automatic PDF preparation", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1");

  await expect(page.getByText(
    "Inserisci i dati della targhetta e conferma l'identità. Solo dopo potrai caricare i documenti che la riguardano."
  )).toBeVisible();
  const serialInfo = page.locator('[data-info-tip="numero-seriale"]');
  await serialInfo.focus();
  await expect(serialInfo.getByRole("tooltip")).toBeVisible();
  await expect(serialInfo.getByRole("tooltip")).toContainText("S/N");

  await page.locator('[name="asset_type"]').fill("hydraulic_press");
  await identifyMachine(page, {
    name: "Hydraulic Press 7",
    model: "HP-700",
    serial: "HP7-000042",
    description: "Hydraulic forming press in maintenance bay seven.",
  });

  // No development-checkpoint vocabulary anywhere in the product.
  const shell = page.locator("#app");
  await expect(shell).not.toContainText(/\bGate\b/);
  await expect(shell).not.toContainText(/sottografo/i);
  await expect(page).not.toHaveURL(/stage=g[123]/);
  await expect(page.locator(".kg-phase")).toHaveCount(4);
  await expect(page.locator(".kg-phase")).toHaveText([
    /Macchina/, /Documenti/, /Struttura/, /Grafo/,
  ]);

  // An isolated source error stays actionable and hides nothing else.
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

  // Several PDF and CSV files in one operation; PDF preparation keeps every
  // page automatically and exposes no page-by-page gate.
  await page.locator('#source-upload select[name="authority"]').selectOption("observational");
  await page.locator('#source-upload input[type="file"]').setInputFiles([
    { name: path.basename(fixture), mimeType: "application/pdf", buffer: fs.readFileSync(fixture) },
    { name: path.basename(secondPdfFixture), mimeType: "application/pdf", buffer: fs.readFileSync(secondPdfFixture) },
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
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".kg-doc")).toHaveCount(4, { timeout: 60000 });
  await expect(page.locator(".kg-rail .kg-source")).toHaveCount(4);
  await expect(page.locator(".kg-rail .kg-badge")).toHaveText([
    /Caricato/, /Caricato/, /Caricato/, /Caricato/,
  ]);
  await expect(page.locator(".scope-page-card")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Controlla le pagine proposte" })).toHaveCount(0);

  // Repeating an active PDF is blocked before upload and clearly flagged.
  const requestsBeforeDuplicate = sourcePostRequests;
  await page.locator('#source-upload input[type="file"]').setInputFiles(fixture);
  await expect(page.getByRole("alert")).toContainText("Documento già caricato");
  await expect(page.getByRole("alert")).toContainText("Non serve caricarlo di nuovo");
  await expect(page.getByRole("button", { name: "Carica documento" })).toBeDisabled();
  expect(sourcePostRequests).toBe(requestsBeforeDuplicate);
  await expect(page.locator(".kg-doc")).toHaveCount(4, { timeout: 60000 });

  // Removal is confirmed, reversible and never silent.
  const removeCsv = page.getByRole("button", { name: "Rimuovi file hydraulic_press_logs_a.csv" });
  await expect(removeCsv).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Rimuovere “hydraulic_press_logs_a.csv”?");
    await dialog.dismiss();
  });
  await removeCsv.click();
  await expect(page.getByText("hydraulic_press_logs_a.csv").first()).toBeVisible();
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toContain("Potrai ricaricarlo in seguito");
    await dialog.accept();
  });
  await removeCsv.click();
  await expect(page.locator(".kg-doc")).toHaveCount(3);
  await expect(page.getByText("hydraulic_press_logs_a.csv")).toHaveCount(0);

  await page.locator('#source-upload input[type="file"]').setInputFiles({
    name: "hydraulic_press_logs_a.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "machine_serial,event_timestamp,action_taken\n"
      + "HP7-000042,2026-07-26T13:44:00+02:00,Backup battery replaced\n"
    ),
  });
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".kg-doc")).toHaveCount(4);

  await page.reload();
  await expect(page.locator(".kg-doc")).toHaveCount(4);

  // The machines home summarises each machine and reopens it by its stable id.
  await page.getByRole("link", { name: "Macchine" }).click();
  await expect(page).toHaveURL(/\/home\.html$/);
  await expect(page.getByRole("heading", { name: "Macchine" })).toBeVisible();
  await expect(page.getByRole("link", { name: /Hydraulic Press 7/ })).toBeVisible();
  await expect(page.getByText(/HP-700 · 4 documenti/)).toBeVisible();
  await page.getByRole("link", { name: /Hydraulic Press 7/ }).click();
  await expect(page).toHaveURL(/console\.html\?foundation=1&workspace_id=ws_/);
  await expect(page.getByRole("heading", { name: "Hydraulic Press 7" })).toBeVisible();

  // A new machine is genuinely separate and comes back to the home list.
  await page.getByRole("link", { name: "Macchine" }).click();
  await page.getByRole("link", { name: "Nuova macchina" }).click();
  await expect(page).toHaveURL(/console\.html\?foundation=1&new=1/);
  await identifyMachine(page, {
    name: "Conveyor 2",
    model: "CV-200",
    serial: "CV2-0007",
    description: "Packaging conveyor in production line two.",
  });
  await expect(page).toHaveURL(/workspace_id=ws_/);
  await page.getByRole("link", { name: "Macchine" }).click();
  await expect(page.locator(".kg-home-card")).toHaveCount(2);
  await expect(page.getByText(/CV-200 · 0 documenti/)).toBeVisible();
});

test("AC-UX-014: the structure phase is automatic and asks one question at a time", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "G2 Test Press",
    model: "G2-200",
    serial: "G2-0001",
    description: "Workspace used for the structure phase product test.",
  });

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
  await expect(page.locator(".kg-doc")).toHaveCount(2);
  await page.getByRole("button", { name: "Continua alla struttura" }).click();

  // The phase is addressed by what it is about, not by a checkpoint number.
  await expect(page).toHaveURL(/fase=struttura/);
  await expect(page).not.toHaveURL(/stage=g2/);

  // Exactly one open question, and it is at the top of the work pane.
  await expect(page.locator(".kg-decision-card")).toHaveCount(1);
  await expect(page.locator(".kg-decision")).toContainText("Serve una tua scelta");
  await expect(page.getByText("Dove va usata la colonna “description”?")).toBeVisible();
  await page.locator('.kg-decision-card select[name="role"]').selectOption("observation");
  await page.getByRole("button", { name: "Salva e continua" }).click();

  // With no question open the pane explains the mapping instead.
  await expect(page.locator(".kg-decision-card")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Che cosa significa ogni colonna" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Significato" })).toBeVisible();
  await expect(page.locator(".kg-table tbody").getByText("Sintomo o osservazione").first()).toBeVisible();
  await expect(page.locator("#app")).not.toContainText(/\bGate\b/);

  // A confirmation applies to one file only.
  const confirm = page.getByRole("button", { name: "Conferma questo file" });
  await expect(confirm).toBeVisible();
  await confirm.click();
  await expect(page.locator(".kg-rail").getByText("Confermata")).toHaveCount(1);

  await page.locator(".kg-source").filter({ hasText: "observations.jsonl" }).click();
  await expect(page.locator(".kg-decision")).toContainText("observations.jsonl");
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await expect(page.locator(".kg-decision")).toContainText("Struttura confermata");
  await expect(page.locator(".kg-rail").getByText("Confermata")).toHaveCount(2);

  await page.reload();
  await expect(page.locator(".kg-decision")).toContainText("Struttura confermata");
  await expect(page.locator(".kg-decision-card")).toHaveCount(0);
});

test("AC-UX-014/AC-TAB-001/AC-LANG-002: CSV variants stay understandable", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "CSV Robustness Press",
    model: "CSV-300",
    serial: "CSV-0001",
    description: "Workspace for structured data verification.",
  });

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
  await expect(page.locator(".kg-doc")).toHaveCount(3);
  await page.getByRole("button", { name: "Continua alla struttura" }).click();
  await expect(page.locator(".kg-rail .kg-source")).toHaveCount(3);

  // Languages are reported without translating anything, in plain words.
  await page.locator(".kg-source").filter({ hasText: "languages.csv" }).click();
  const inspector = page.locator(".kg-inspector");
  await expect(inspector).toContainText("1 in inglese");
  await expect(inspector).toContainText("1 in italiano");
  await expect(inspector).toContainText("1 in tedesco");
  await expect(inspector).toContainText("1 in più lingue");

  // Malformed rows are isolated, counted and explained — never deleted.
  await page.locator(".kg-source").filter({ hasText: "righe-irregolari.csv" }).click();
  await expect(inspector).toContainText("3 righe lette");
  await expect(inspector).toContainText("1 riga preparata");
  await expect(inspector).toContainText("2 righe isolate");
  await page.getByRole("tab", { name: "Avvisi" }).click();
  await expect(page.getByRole("heading", { name: "Righe messe da parte" })).toBeVisible();
  await expect(page.getByText("Alcune righe hanno un numero errato di colonne")).toBeVisible();

  // Every value stays visible exactly as it is in the file.
  await page.getByRole("tab", { name: "Righe" }).click();
  await expect(page.getByRole("heading", { name: "Le righe come sono nel file" })).toBeVisible();
});

test("AC-HITL-002/AC-UX-005: each graph is navigable to its rows and verified per source", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "G3 Synthetic Press",
    model: "G3-300",
    serial: "G3-0001",
    description: "Workspace for source graph verification.",
  });

  await page.locator('#source-upload input[type="file"]').setInputFiles([
    path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_it.csv"),
    path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_en.csv"),
  ]);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".kg-doc")).toHaveCount(2);
  await page.getByRole("button", { name: "Continua alla struttura" }).click();

  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await page.locator(".kg-source").filter({ hasText: "synthetic_press_events_en.csv" }).click();
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await expect(page.locator(".kg-decision")).toContainText("Struttura confermata");
  await page.getByRole("button", { name: "Vai al grafo" }).click();

  await expect(page).toHaveURL(/fase=grafo/);
  await expect(page).not.toHaveURL(/stage=g3/);
  await expect(page.locator("#app")).not.toContainText(/\bGate\b/);
  await expect(page.locator(".kg-rail .kg-source")).toHaveCount(3); // two files + the comparison entry
  await expect(page.locator(".kg-rail")).toContainText("Confronto tra fonti");
  await expect(page.locator(".kg-rail")).toContainText("Non ancora disponibile");

  // The graph is built on an explicit human action, never automatically.
  await page.locator(".kg-source").filter({ hasText: "synthetic_press_events_it.csv" }).click();
  await expect(page.locator(".kg-decision")).toContainText("Grafo non ancora costruito");
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();

  // The explorer is the page: a canvas with every element and link on it.
  await expect(page.locator(".kg-node")).toHaveCount(11);
  await expect(page.locator(".kg-edge")).toHaveCount(12);

  // Selecting a node opens its contextual detail, down to the source rows.
  await page.locator('.kg-node[aria-label^="Sintomo: Rumore metallico"]').click();
  const inspector = page.locator(".kg-inspector");
  await expect(inspector).toContainText("Rumore metallico");
  await expect(inspector).toContainText("Sintomo");
  await expect(inspector).toContainText("Da verificare");
  await expect(inspector).toContainText("Occorrenze consolidate");
  await expect(inspector).toContainText("riga 2");
  await expect(inspector).toContainText("riga 4");

  // A relation row navigates to the element at the other end.
  await inspector.locator(".kg-relation").first().click();
  await expect(inspector.locator("h2")).not.toHaveText("Rumore metallico");

  // Filters are live and apply to the tables as well as to the canvas.
  await page.getByRole("tab", { name: /^Elementi/ }).click();
  await page.getByLabel("Cerca un elemento").fill("pompa");
  await page.getByLabel("Tipo di elemento").selectOption("Component");
  await expect(page.locator(".kg-table tbody tr")).toHaveCount(1);
  await expect(page.locator(".kg-table tbody tr")).toContainText("Pompa idraulica");
  await page.getByLabel("Cerca un elemento").fill("");
  await page.getByLabel("Tipo di elemento").selectOption("all");

  await page.getByRole("tab", { name: /^Collegamenti/ }).click();
  await expect(page.locator(".kg-table tbody tr")).toHaveCount(12);

  // Every row read from the file is reachable, whatever it produced.
  await page.getByRole("tab", { name: /^Righe di origine/ }).click();
  await expect(page.getByRole("heading", { name: "Ogni riga letta da questo file" })).toBeVisible();

  // Diagnostic chains read from the observation to the corrective action.
  await page.getByRole("tab", { name: "Catene diagnostiche" }).click();
  await expect(page.getByRole("heading", { name: "Dal sintomo all'azione" })).toBeVisible();

  // The decision states its own limits before it is taken.
  await expect(page.locator(".kg-decision")).toContainText("non unisce le fonti e non pubblica niente");
  await page.getByRole("button", { name: "Conferma la verifica" }).click();
  await expect(page.locator(".kg-decision")).toContainText("Fonte verificata");

  // One verified source is not a comparison: the second is still untouched.
  await expect(page.locator(".kg-rail")).toContainText("Non ancora disponibile");
  await page.locator(".kg-source").filter({ hasText: "synthetic_press_events_en.csv" }).click();
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();
  await page.getByRole("button", { name: "Conferma la verifica" }).click();
  await expect(page.locator(".kg-decision")).toContainText("Fonte verificata");

  // Cross-source matches are proposals, explicitly not a merge.
  await page.locator(".kg-source").filter({ hasText: "Confronto tra fonti" }).click();
  await expect(page.locator(".kg-work-head h1")).toHaveText("Confronto tra fonti");
  const comparison = page.locator(".kg-work");
  await expect(comparison).toContainText("Niente viene unito automaticamente");
  await expect(comparison).toContainText("2 corrispondenze esatte trovate");
  await expect(comparison).toContainText("E-PUMP-17");
  await expect(comparison).toContainText("E-VALVE-04");
});

test("AC-UX-005: the explorer is operable by keyboard and survives a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "Keyboard Press",
    model: "KB-100",
    serial: "KB-0001",
    description: "Workspace for keyboard and responsive verification.",
  });
  await page.locator('#source-upload input[type="file"]').setInputFiles(
    path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_it.csv")
  );
  await page.getByRole("button", { name: "Carica documento" }).click();
  await page.getByRole("button", { name: "Continua alla struttura" }).click();
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await page.getByRole("button", { name: "Vai al grafo" }).click();
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();
  await expect(page.locator(".kg-node")).toHaveCount(11);

  // Exactly one node is in the tab order; the arrows move the roving focus and
  // Enter selects, so the canvas is usable without a pointer.
  await expect(page.locator('.kg-node[tabindex="0"]')).toHaveCount(1);
  await page.locator('.kg-node[tabindex="0"]').focus();
  const firstFocused = await page.evaluate(() => document.activeElement.getAttribute("aria-label"));
  await page.keyboard.press("ArrowRight");
  const secondFocused = await page.evaluate(() => document.activeElement.getAttribute("aria-label"));
  expect(secondFocused).not.toBe(firstFocused);
  await page.keyboard.press("Enter");
  await expect(page.locator(".kg-node-selected")).toHaveCount(1);
  await expect(page.locator(".kg-inspector")).toContainText("Occorrenze consolidate");
  await page.keyboard.press("Escape");
  await expect(page.locator(".kg-node-selected")).toHaveCount(0);

  // Narrow viewport: columns are reduced, never the text. The inspector
  // becomes a dismissible overlay instead of squeezing the graph.
  await page.setViewportSize({ width: 700, height: 900 });
  await expect(page.locator(".kg-body")).toHaveAttribute("data-inspector", "hidden");
  await page.locator('.kg-node[tabindex="0"]').click();
  await expect(page.locator(".kg-body")).toHaveAttribute("data-inspector", "visible");
  await page.getByRole("button", { name: "Chiudi dettaglio" }).click();
  await expect(page.locator(".kg-body")).toHaveAttribute("data-inspector", "hidden");
  await expect(page.locator(".kg-phase")).toHaveCount(4);
});

test("AC-UX-005: a graph with knowledge gaps cannot be verified, and says why", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "Gap Press",
    model: "GAP-100",
    serial: "GAP-0001",
    description: "Workspace for the blocking-gap product test.",
  });

  await page.locator('#source-upload input[type="file"]').setInputFiles({
    name: "lacune.csv",
    mimeType: "text/csv",
    buffer: Buffer.from(
      "event_id,component,symptom_observation,cause,action_taken,error_code\n"
      + "E1,Pompa idraulica,Rumore metallico,,,\n"
      + "E2,Valvola,Perdita di olio,Guarnizione danneggiata,,E-VALVE-04\n"
      + "E3,Pompa idraulica,Surriscaldamento,Usura cuscinetto,Sostituzione cuscinetto,E-PUMP-17\n"
    ),
  });
  await page.getByRole("button", { name: "Carica documento" }).click();
  await page.getByRole("button", { name: "Continua alla struttura" }).click();
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await page.getByRole("button", { name: "Vai al grafo" }).click();
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();

  // Not verifiable is a protection, stated as such, with the action disabled
  // rather than hidden.
  const decision = page.locator(".kg-decision");
  await expect(decision).toContainText("Non ancora verificabile");
  await expect(decision).toContainText("È una protezione");
  await expect(decision).toContainText("nessun collegamento è stato inventato");
  await expect(page.getByRole("button", { name: "Conferma la verifica" })).toBeDisabled();

  // A knowledge gap is told apart from a technical defect, in plain Italian,
  // and never as an engine code.
  await decision.getByRole("button", { name: /lacune nei dati/ }).click();
  const work = page.locator(".kg-work");
  await expect(work.getByRole("heading", { name: /^Lacune nei dati/ })).toBeVisible();
  await expect(work).toContainText("I dati letti sono validi, ma non dichiarano queste informazioni");
  await expect(work).toContainText("Causa non dichiarata nella riga");
  await expect(work).toContainText("Azione correttiva non dichiarata");
  await expect(work).not.toContainText("missing_failure_mode");
  await expect(work).not.toContainText("missing_corrective_action");
  // A gap points back to the exact row it comes from.
  await expect(work).toContainText("riga 2");

  // Reporting a correction is an inline, explained decision — not a prompt.
  await page.getByRole("button", { name: "Segnala da correggere" }).click();
  await expect(page.getByText("Che cosa deve essere corretto in questa fonte?")).toBeVisible();
  await page.locator('.kg-decision textarea[name="note"]').fill("La colonna delle azioni è vuota per la seconda riga.");
  await page.getByRole("button", { name: "Registra la segnalazione" }).click();
  await expect(decision).toContainText("Segnalata da correggere");
  await expect(decision).toContainText("La colonna delle azioni è vuota per la seconda riga.");
});
