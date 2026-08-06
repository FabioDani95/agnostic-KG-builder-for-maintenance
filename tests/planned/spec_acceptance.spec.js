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
 * after the object of work; the internal development checkpoints must appear
 * neither in the interface nor in the address bar.
 */
async function identifyMachine(page, { name, model, serial, description }) {
  await page.locator('[name="name"]').fill(name);
  await page.locator('[name="brand"]').fill("ExampleWorks");
  await page.locator('[name="model"]').fill(model);
  await page.locator('[name="description"]').fill(description);
  await page.locator('[name="serial"]').fill(serial);
  await page.locator('[name="operator"]').fill("PO");
  await page.getByRole("button", { name: "Salva macchina e continua" }).click();
  await expect(page.locator(".topbar h1")).toHaveText(name);
  await page.getByRole("button", { name: "Continua ai documenti" }).click();
  await expect(page.locator(".topbar h1")).toHaveText("Documenti della macchina");
}

const uploadFiles = (page, files) =>
  page.locator('#source-upload input[type="file"]').setInputFiles(files);

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
  await expect(page.locator(".nav-item[data-fase]")).toHaveCount(4);
  await expect(page.locator(".nav-item[data-fase]")).toHaveText([
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
  await uploadFiles(page, {
    name: "unsupported.txt", mimeType: "text/plain", buffer: Buffer.from("unsupported source"),
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
  await uploadFiles(page, [
    { name: path.basename(fixture), mimeType: "application/pdf", buffer: fs.readFileSync(fixture) },
    { name: path.basename(secondPdfFixture), mimeType: "application/pdf", buffer: fs.readFileSync(secondPdfFixture) },
    {
      name: "hydraulic_press_logs_a.csv", mimeType: "text/csv",
      buffer: Buffer.from("machine_serial,event_timestamp,action_taken\nHP7-000042,2026-07-26T13:44:00+02:00,Backup battery replaced\n"),
    },
    {
      name: "hydraulic_press_logs_b.csv", mimeType: "text/csv",
      buffer: Buffer.from("machine_serial,event_timestamp,action_taken\nHP7-000042,2026-07-27T08:15:00+02:00,Hydraulic seal inspected\n"),
    },
  ]);
  await expect(page.locator("[data-nome-file]")).toHaveText("4 file selezionati");
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".documento")).toHaveCount(4, { timeout: 60000 });
  await expect(page.locator(".nav-item[data-fonte]")).toHaveCount(4);
  await expect(page.locator(".scope-page-card")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Controlla le pagine proposte" })).toHaveCount(0);

  // Repeating an active PDF is blocked before upload and clearly flagged.
  const requestsBeforeDuplicate = sourcePostRequests;
  await uploadFiles(page, fixture);
  await expect(page.getByRole("alert")).toContainText("Documento già caricato");
  await expect(page.getByRole("alert")).toContainText("Non serve caricarlo di nuovo");
  await expect(page.getByRole("button", { name: "Carica documento" })).toBeDisabled();
  expect(sourcePostRequests).toBe(requestsBeforeDuplicate);
  await expect(page.locator(".documento")).toHaveCount(4, { timeout: 60000 });

  // Archiving is explained, reversible and never silent.
  const archiveCsv = page.getByRole("button", { name: "Archivia documento hydraulic_press_logs_a.csv" });
  await expect(archiveCsv).toBeVisible();
  await archiveCsv.click();
  await expect(page.getByRole("dialog")).toContainText("Archiviare “hydraulic_press_logs_a.csv”?");
  await page.getByRole("dialog").getByRole("button", { name: "Annulla" }).click();
  await expect(page.locator(".documento")).toHaveCount(4);
  await archiveCsv.click();
  await expect(page.getByRole("dialog")).toContainText("Le revisioni restano conservate");
  await page.getByRole("dialog").getByRole("button", { name: "Archivia documento" }).click();
  await expect(page.locator(".lista > .documento")).toHaveCount(3);

  await page.getByRole("button", { name: "Documenti archiviati" }).click();
  await expect(page.getByRole("button", { name: "Ripristina" })).toBeVisible();
  await page.getByRole("button", { name: "Ripristina" }).click();
  await expect(page.locator(".documento")).toHaveCount(4);
  await expect(page.getByRole("status")).toContainText("Documento ripristinato");

  // Re-uploading the now-active source is still blocked as a duplicate.
  await uploadFiles(page, {
    name: "hydraulic_press_logs_a.csv", mimeType: "text/csv",
    buffer: Buffer.from("machine_serial,event_timestamp,action_taken\nHP7-000042,2026-07-26T13:44:00+02:00,Backup battery replaced\n"),
  });
  await expect(page.getByRole("alert")).toContainText("Documento già caricato");

  await page.reload();
  await expect(page.locator(".documento")).toHaveCount(4);

  // The machines home summarises each machine and reopens it by its stable id.
  await page.goto("/home.html");
  await expect(page.locator(".topbar .marchio-nome")).toContainText("Nexus");
  await expect(page.locator(".elenco-capo h2")).toContainText("Area di lavoro");
  const rigaPressa = page.getByRole("link", { name: /Hydraulic Press 7/ });
  await expect(rigaPressa).toBeVisible();
  // Every fact has its own column, so two machines can be compared by eye.
  await expect(rigaPressa.locator(".cella").nth(2)).toHaveText("HP-700");
  await expect(rigaPressa.locator(".cella").nth(3)).toHaveText("4");
  await page.getByRole("link", { name: /Hydraulic Press 7/ }).click();
  await expect(page).toHaveURL(/console\.html\?foundation=1&workspace_id=ws_/);
  await expect(page.locator(".brand-text")).toContainText("Hydraulic Press 7");

  // A new machine is genuinely separate and comes back to the home list.
  await page.goto("/home.html");
  await page.getByRole("link", { name: "Nuova macchina" }).first().click();
  await expect(page).toHaveURL(/console\.html\?foundation=1&new=1/);
  await identifyMachine(page, {
    name: "Conveyor 2", model: "CV-200", serial: "CV2-0007",
    description: "Packaging conveyor in production line two.",
  });
  await page.goto("/home.html");
  await expect(page.locator(".riga-macchina")).toHaveCount(2);
  const rigaNastro = page.getByRole("link", { name: /Conveyor 2/ });
  await expect(rigaNastro.locator(".cella").nth(2)).toHaveText("CV-200");
  await expect(rigaNastro.locator(".cella").nth(3)).toHaveText("0");
});

test("AC-UX-011: the interface switches language and theme without losing its place", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "Bilingual Press", model: "BI-100", serial: "BI-0001",
    description: "Workspace for the language and theme test.",
  });

  // A direct link cannot strand the operator inside a locked phase.
  const lockedGraphUrl = new URL(page.url());
  lockedGraphUrl.searchParams.set("fase", "grafo");
  await page.goto(lockedGraphUrl.toString());
  await expect(page).toHaveURL(/fase=documenti/);
  await expect(page.locator(".topbar h1")).toHaveText("Documenti della macchina");

  // The switch shows the language in force and moves to the other one.
  const language = page.locator("[data-lingua]");
  await expect(language).toHaveText("IT");
  await language.click();
  await expect(language).toHaveText("ENG");
  await expect(page.locator(".nav-item[data-fase]")).toHaveText([
    /Machine/, /Documents/, /Structure/, /Graph/,
  ]);
  await expect(page.locator(".topbar h1")).toHaveText("Machine documents");
  await expect(page.getByRole("button", { name: "Upload document" })).toBeVisible();

  // The choice survives a reload, and so does the phase.
  await page.reload();
  await expect(page.locator("[data-lingua]")).toHaveText("ENG");
  await expect(page.locator(".topbar h1")).toHaveText("Machine documents");
  await page.locator("[data-lingua]").click();
  await expect(page.locator(".topbar h1")).toHaveText("Documenti della macchina");

  // The theme is an explicit choice, remembered across reloads.
  const theme = page.locator("[data-tema]");
  const before = await page.evaluate(() => document.documentElement.dataset.theme);
  await theme.click();
  const after = await page.evaluate(() => document.documentElement.dataset.theme);
  expect(after).not.toBe(before);
  await page.reload();
  expect(await page.evaluate(() => document.documentElement.dataset.theme)).toBe(after);
});

test("AC-UX-017: a PDF-only workspace never offers an unavailable graph action", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "PDF Manual Press", model: "PDF-100", serial: "PDF-0001",
    description: "Workspace used to verify honest PDF graph guidance.",
  });

  await uploadFiles(page, fixture);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".documento")).toHaveCount(1, { timeout: 60000 });
  await page.getByRole("button", { name: "Continua alla struttura" }).click();
  await page.getByRole("button", { name: "Vai al grafo" }).click();

  await expect(page.getByText("Grafo PDF non ancora disponibile").first()).toBeVisible();
  await expect(page.locator(".ispettore")).toContainText("Grafo PDF non ancora disponibile");
  await expect(page.locator(".decisione")).toContainText("Nessuna azione richiesta su questo PDF");
  await expect(page.getByRole("button", { name: "Costruisci il grafo" })).toHaveCount(0);
  await expect(page.locator("#app")).not.toContainText("Costruisci il grafo di questa fonte per esplorarlo");
});

test("AC-UX-014: the structure phase is automatic and asks one question at a time", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "G2 Test Press", model: "G2-200", serial: "G2-0001",
    description: "Workspace used for the structure phase product test.",
  });

  await uploadFiles(page, [
    {
      name: "ambiguous-events.csv", mimeType: "text/csv",
      buffer: Buffer.from("event_id,description,action_taken\nE1,abnormal vibration,inspect bearing\nE2,oil leakage,replace seal\n"),
    },
    {
      name: "observations.jsonl", mimeType: "application/x-ndjson",
      buffer: Buffer.from(
        '{"event_id":"J1","symptom_observation":"noise","action_taken":"inspect"}\n'
        + '{"event_id":"BROKEN","symptom_observation":\n'
        + '{"event_id":"J2","symptom_observation":"heat","action_taken":"cool"}\n'
      ),
    },
  ]);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".documento")).toHaveCount(2);
  await page.getByRole("button", { name: "Continua alla struttura" }).click();

  // The phase is addressed by what it is about, not by a checkpoint number.
  await expect(page).toHaveURL(/fase=struttura/);
  await expect(page).not.toHaveURL(/stage=g2/);

  // Exactly one open question, and it is at the top of the work pane.
  await expect(page.locator(".lavoro .card")).toHaveCount(1);
  await expect(page.locator(".decisione")).toContainText("Serve una tua scelta");
  await expect(page.getByText("Dove va usata la colonna “description”?")).toBeVisible();
  await page.locator('.lavoro .card select[name="role"]').selectOption("observation");
  await page.getByRole("button", { name: "Salva e continua" }).click();

  // Answering must not scroll the frame away. The app fills the window and its
  // panes scroll on their own; when the document itself could scroll, bringing
  // a control into view pushed the top bar off screen with no way back.
  const topbar = await page.locator(".topbar").boundingBox();
  expect(topbar.y).toBe(0);
  expect(await page.evaluate(() => window.scrollY)).toBe(0);

  // The question card is a surface of the app, not of the retained console:
  // both call it a card, and the wrong one made it white under the dark theme,
  // where the title is near-white too.
  await page.evaluate(() => { document.documentElement.dataset.theme = "dark"; });
  const contrasto = await page.evaluate(() => {
    const carta = document.querySelector(".lavoro .card") || document.querySelector(".tabella-wrap");
    return getComputedStyle(carta).backgroundColor;
  });
  expect(contrasto).not.toBe("rgb(255, 255, 255)");
  await page.evaluate(() => { document.documentElement.dataset.theme = "light"; });

  // With no question open the pane explains the mapping instead.
  await expect(page.locator(".lavoro .card")).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Che cosa significa ogni colonna" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Significato" })).toBeVisible();
  const ruoloDescription = page.locator('.tabella tbody select[data-colonna="description"]');
  await expect(ruoloDescription).toHaveValue("observation");
  await expect(page.locator("#app")).not.toContainText(/\bGate\b/);

  // The meaning of a column is a control, not a label: it stays correctable,
  // and a role belongs to one column, so handing it over releases the previous
  // holder to plain data instead of gluing the two together.
  await page.locator('.tabella tbody select[data-colonna="action_taken"]').selectOption("observation");
  await expect(page.locator('.tabella tbody select[data-colonna="action_taken"]')).toHaveValue("observation");
  await expect(ruoloDescription).toHaveValue("attribute");

  // Re-reading the file withdraws a confirmation given for the previous reading.
  await expect(page.locator(".decisione")).toContainText("Conferma questo file");
  await page.locator('.tabella tbody select[data-colonna="action_taken"]').selectOption("action");
  await expect(ruoloDescription).toHaveValue("attribute");
  await page.locator('.tabella tbody select[data-colonna="description"]').selectOption("observation");
  await expect(ruoloDescription).toHaveValue("observation");

  // A confirmation applies to one file only.
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await expect(page.locator(".topbar")).toContainText("Confermata");

  await page.locator(".nav-item[data-fonte]").filter({ hasText: "observations.jsonl" }).click();
  await expect(page.locator(".decisione")).toContainText("observations.jsonl");
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await expect(page.locator(".decisione")).toContainText("Struttura confermata");

  await page.reload();
  await expect(page.locator(".decisione")).toContainText("Struttura confermata");
  await expect(page.locator(".lavoro .card")).toHaveCount(0);
});

test("AC-UX-014/AC-TAB-001/AC-LANG-002: CSV variants stay understandable", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "CSV Robustness Press", model: "CSV-300", serial: "CSV-0001",
    description: "Workspace for structured data verification.",
  });

  await uploadFiles(page, [
    {
      name: "eventi-latin1.csv", mimeType: "text/csv",
      buffer: Buffer.from(
        "event_timestamp;component;symptom_observation;action_taken;language\n"
        + "2026-01-01T10:00:00Z;pompa;temperatura è alta;pulita valvola;IT\n", "latin1"),
    },
    {
      name: "languages.csv", mimeType: "text/csv",
      buffer: Buffer.from(
        "language,symptom_observation,action_taken\n"
        + "EN,abnormal noise,inspect bearing\n"
        + "IT,rumore anomalo,ispezionare cuscinetto\n"
        + "DE,ungewoehnliches Geraeusch,Lager pruefen\n"
        + "MIXED,rumore and noise,inspect e controllare\n"),
    },
    {
      name: "righe-irregolari.csv", mimeType: "text/csv",
      buffer: Buffer.from("event_id,symptom_observation,action_taken\nE1,noise,inspect\nE2,leak\nE3,heat,cool,unexpected\n"),
    },
  ]);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".documento")).toHaveCount(3);
  await page.getByRole("button", { name: "Continua alla struttura" }).click();
  await expect(page.locator(".nav-item[data-fonte]")).toHaveCount(3);

  // Languages are reported without translating anything, in plain words.
  await page.locator(".nav-item[data-fonte]").filter({ hasText: "languages.csv" }).click();
  const inspector = page.locator(".ispettore");
  await expect(inspector).toContainText("1 in inglese");
  await expect(inspector).toContainText("1 in italiano");
  await expect(inspector).toContainText("1 in tedesco");
  await expect(inspector).toContainText("1 in più lingue");

  // Malformed rows are isolated, counted and explained — never deleted.
  await page.locator(".nav-item[data-fonte]").filter({ hasText: "righe-irregolari.csv" }).click();
  await expect(inspector).toContainText("righe lette");
  await expect(inspector).toContainText("1 riga preparata");
  await expect(inspector).toContainText("2 righe isolate");
  await page.getByRole("tab", { name: "Avvisi" }).click();
  await expect(page.getByRole("heading", { name: "Righe messe da parte" })).toBeVisible();
  await expect(page.getByText("Alcune righe hanno un numero errato di colonne")).toBeVisible();

  // Every value stays visible exactly as it is in the file.
  await page.getByRole("tab", { name: "Righe" }).click();
  await expect(page.getByRole("heading", { name: "Le righe come sono nel file" })).toBeVisible();
});

test("AC-HITL-002/AC-UX-005: the graph is a navigable 2D map down to its source rows", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "G3 Synthetic Press", model: "G3-300", serial: "G3-0001",
    description: "Workspace for source graph verification.",
  });

  await uploadFiles(page, [
    path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_it.csv"),
    path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_en.csv"),
  ]);
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.locator(".documento")).toHaveCount(2);
  await page.getByRole("button", { name: "Continua alla struttura" }).click();

  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await page.locator(".nav-item[data-fonte]").filter({ hasText: "synthetic_press_events_en.csv" }).click();
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await expect(page.locator(".decisione")).toContainText("Struttura confermata");
  await page.getByRole("button", { name: "Vai al grafo" }).click();

  await expect(page).toHaveURL(/fase=grafo/);
  await expect(page).not.toHaveURL(/stage=g3/);
  await expect(page.locator("#app")).not.toContainText(/\bGate\b/);
  await expect(page.locator(".nav-item[data-fonte]")).toHaveCount(2);
  await expect(page.locator("[data-confronto]")).toContainText("Confronto tra fonti");

  // The graph is built on an explicit human action, never automatically.
  await page.locator(".nav-item[data-fonte]").filter({ hasText: "synthetic_press_events_it.csv" }).click();
  await expect(page.locator(".decisione")).toContainText("Grafo non ancora costruito");
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();

  // A real 2D map: one draggable node per element, one line per link.
  await expect(page.locator(".nodo")).toHaveCount(11);
  await expect(page.locator(".arco")).toHaveCount(12);
  await expect(page.locator(".grafo-svg")).toBeVisible();

  // Selecting a node opens its contextual detail, down to the source rows.
  await page.locator('.nodo[aria-label^="Sintomo: Rumore metallico"]').click();
  const inspector = page.locator(".ispettore");
  await expect(inspector).toContainText("Rumore metallico");
  await expect(inspector).toContainText("Sintomo");
  await expect(inspector).toContainText("Da verificare");
  await expect(inspector).toContainText("Occorrenze consolidate");
  await expect(inspector).toContainText("riga 2");
  await expect(inspector).toContainText("riga 4");
  // The map is highlighted in place, not rebuilt: the selection survives.
  await expect(page.locator(".nodo.scelto")).toHaveCount(1);

  // A relation row navigates to the element at the other end.
  await inspector.locator(".riga-legame").first().click();
  await expect(inspector.locator("h3")).not.toHaveText("Rumore metallico");

  // Filters are live and apply to the tables as well as to the map.
  await page.getByRole("tab", { name: /^Elementi/ }).click();
  await page.getByLabel("Cerca un elemento").fill("pompa");
  await page.getByLabel("Tipo di elemento").selectOption("Component");
  await expect(page.locator(".tabella tbody tr")).toHaveCount(1);
  await expect(page.locator(".tabella tbody tr")).toContainText("Pompa idraulica");
  await page.getByLabel("Cerca un elemento").fill("");
  await page.getByLabel("Tipo di elemento").selectOption("all");

  await page.getByRole("tab", { name: /^Collegamenti/ }).click();
  await expect(page.locator(".tabella tbody tr")).toHaveCount(12);

  // Every row read from the file is reachable, whatever it produced.
  await page.getByRole("tab", { name: /^Righe di origine/ }).click();
  await expect(page.getByRole("heading", { name: "Ogni riga letta da questo file" })).toBeVisible();

  // Diagnostic chains read from the observation to the corrective action.
  await page.getByRole("tab", { name: "Catene" }).click();
  await expect(page.getByRole("heading", { name: "Dal sintomo all'azione" })).toBeVisible();

  // The decision states its own limits before it is taken.
  await expect(page.locator(".decisione")).toContainText("non unisce le fonti e non pubblica niente");
  await page.getByRole("button", { name: "Conferma la verifica" }).click();
  await expect(page.locator(".decisione")).toContainText("Fonte verificata");

  // One verified source is not a comparison: the second is still untouched.
  await expect(page.locator("[data-confronto]")).toContainText("—");
  await page.locator(".nav-item[data-fonte]").filter({ hasText: "synthetic_press_events_en.csv" }).click();
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();
  await page.getByRole("button", { name: "Conferma la verifica" }).click();
  await expect(page.locator(".decisione")).toContainText("Fonte verificata");

  // Cross-source matches are proposals, explicitly not a merge.
  await page.locator("[data-confronto]").click();
  await expect(page.locator(".topbar h1")).toHaveText("Confronto tra fonti");
  const work = page.locator(".lavoro");
  await expect(work).toContainText("Niente viene unito automaticamente");
  await expect(work).toContainText("2 corrispondenze esatte trovate");
  await expect(work).toContainText("E-PUMP-17");
  await expect(work).toContainText("E-VALVE-04");
});

test("AC-UX-016: reopening a workspace guides the next source without losing existing graphs", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "Journey Press", model: "JY-400", serial: "JY-0001",
    description: "Workspace used to verify the complete guided journey.",
  });

  await uploadFiles(page, path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_it.csv"));
  await page.getByRole("button", { name: "Carica documento" }).click();
  await page.getByRole("button", { name: "Continua alla struttura" }).click();
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await page.getByRole("button", { name: "Vai al grafo" }).click();
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();
  await page.getByRole("button", { name: "Conferma la verifica" }).click();
  await expect(page.locator(".journey-next")).toContainText("tutti i grafi disponibili sono aggiornati");

  // The home reopens the stable workspace directly where work last completed.
  await page.goto("/home.html");
  // The row does not spell the next step out, but it still carries it: the link
  // opens the phase the journey points to.
  const rigaJourney = page.getByRole("link", { name: /Journey Press/ });
  await expect(rigaJourney).toHaveAttribute("href", /fase=grafo/);
  await page.getByRole("link", { name: /Journey Press/ }).click();
  await expect(page).toHaveURL(/fase=grafo/);
  await expect(page.locator(".nodo")).toHaveCount(11);

  // A new document becomes the explicit context and the journey points to it.
  await page.locator('.nav-item[data-fase="documents"]').click();
  await uploadFiles(page, {
    name: "journey_new_events.csv", mimeType: "text/csv",
    buffer: Buffer.from(
      "component,symptom_observation,diagnosis,action_taken\n"
      + "cooling fan,high temperature,bearing friction,replace bearing\n"
    ),
  });
  await page.getByRole("button", { name: "Carica documento" }).click();
  await expect(page.getByRole("status")).toContainText("Documento caricato");
  await expect(page.locator(".journey-context")).toContainText("journey_new_events.csv");
  await expect(page.locator(".journey-next")).toContainText("controlla la struttura");
  await expect(page).toHaveURL(/source_id=src_/);

  // Refreshing preserves both the source and the point in the journey.
  await page.reload();
  await expect(page.locator(".journey-context")).toContainText("journey_new_events.csv");
  await page.locator("[data-follow-journey]").click();
  await expect(page).toHaveURL(/fase=struttura/);
  await expect(page.locator(".journey-context")).toContainText("journey_new_events.csv");
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await expect(page.locator(".journey-next")).toContainText("costruisci il grafo");
  await page.locator("[data-follow-journey]").click();
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();
  await expect(page.locator(".nodo")).toHaveCount(5);

  // Archiving hides this source graph but preserves its immutable revision.
  await page.locator('.nav-item[data-fase="documents"]').click();
  await page.getByRole("button", { name: "Archivia documento journey_new_events.csv" }).click();
  await page.getByRole("dialog").getByRole("button", { name: "Archivia documento" }).click();
  await expect(page.getByRole("status")).toContainText("Documento archiviato");
  await page.getByRole("button", { name: "Documenti archiviati" }).click();
  const archived = page.locator(".documento.archiviato").filter({ hasText: "journey_new_events.csv" });
  await expect(archived).toContainText(/grafo conservato/i);
  await archived.getByRole("button", { name: "Ripristina" }).click();
  await expect(page.getByRole("status")).toContainText("Documento ripristinato");
  await page.locator('.nav-item[data-fase="graph"]').click();
  await expect(page.locator(".nodo")).toHaveCount(5);
  await expect(page.locator(".ispettore")).toContainText("1 versione");
});

test("AC-UX-005: the map is operable by keyboard and survives a narrow viewport", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "Keyboard Press", model: "KB-100", serial: "KB-0001",
    description: "Workspace for keyboard and responsive verification.",
  });
  await uploadFiles(page, path.resolve(__dirname, "../fixtures/g3/synthetic_press_events_it.csv"));
  await page.getByRole("button", { name: "Carica documento" }).click();
  await page.getByRole("button", { name: "Continua alla struttura" }).click();
  await page.getByRole("button", { name: "Conferma questo file" }).click();
  await page.getByRole("button", { name: "Vai al grafo" }).click();
  await page.getByRole("button", { name: "Costruisci il grafo" }).click();
  await expect(page.locator(".nodo")).toHaveCount(11);

  // The map takes focus, hands it to a node, and the arrows walk the graph.
  await page.locator(".grafo-svg").focus();
  await expect(page.locator('.nodo[tabindex="0"]')).toHaveCount(1);
  const first = await page.evaluate(() => document.activeElement.getAttribute("aria-label"));
  await page.keyboard.press("ArrowRight");
  const second = await page.evaluate(() => document.activeElement.getAttribute("aria-label"));
  expect(second).not.toBe(first);
  await page.keyboard.press("Enter");
  await expect(page.locator(".nodo.scelto")).toHaveCount(1);
  await expect(page.locator(".ispettore")).toContainText("Occorrenze consolidate");
  await page.keyboard.press("Escape");
  await expect(page.locator(".nodo.scelto")).toHaveCount(0);

  // Narrow viewport: columns are reduced, never the text. The inspector
  // becomes a dismissible overlay instead of squeezing the map.
  await page.setViewportSize({ width: 700, height: 900 });
  await expect(page.locator(".contenuto")).toHaveAttribute("data-ispettore", "chiuso");
  await page.locator(".nodo").first().click();
  await expect(page.locator(".contenuto")).toHaveAttribute("data-ispettore", "aperto");
  await page.getByRole("button", { name: "Chiudi dettaglio" }).click();
  await expect(page.locator(".contenuto")).toHaveAttribute("data-ispettore", "chiuso");
  await expect(page.locator(".nav-item[data-fase]")).toHaveCount(4);
});

test("AC-UX-005: a graph with knowledge gaps cannot be verified, and says why", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto("/console.html?foundation=1&new=1");
  await identifyMachine(page, {
    name: "Gap Press", model: "GAP-100", serial: "GAP-0001",
    description: "Workspace for the blocking-gap product test.",
  });

  await uploadFiles(page, {
    name: "lacune.csv", mimeType: "text/csv",
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
  const decision = page.locator(".decisione");
  await expect(decision).toContainText("Non ancora verificabile");
  await expect(decision).toContainText("È una protezione");
  await expect(decision).toContainText("nessun collegamento è stato inventato");
  await expect(page.getByRole("button", { name: "Conferma la verifica" })).toBeDisabled();

  // A knowledge gap is told apart from a technical defect, in plain Italian,
  // and never as an engine code.
  await decision.getByRole("button", { name: /lacune nei dati/ }).click();
  const work = page.locator(".lavoro");
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
  await page.locator('.decisione textarea[name="note"]').fill("La colonna delle azioni è vuota per la seconda riga.");
  await page.getByRole("button", { name: "Registra la segnalazione" }).click();
  await expect(decision).toContainText("Segnalata da correggere");
  await expect(decision).toContainText("La colonna delle azioni è vuota per la seconda riga.");
});
