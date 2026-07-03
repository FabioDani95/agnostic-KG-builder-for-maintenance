const { test, expect } = require("@playwright/test");

const MOCK_PDF = Buffer.from(
  "JVBERi0xLjcKJcK1wrYKJSBXcml0dGVuIGJ5IE11UERGIDEuMjcuMQoKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFIvSW5mbzw8L1Byb2R1Y2VyKE11UERGIDEuMjcuMSk+Pj4+CmVuZG9iagoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0NvdW50IDEvS2lkc1s0IDAgUl0+PgplbmRvYmoKCjMgMCBvYmoKPDwvRm9udDw8L2hlbHYgNSAwIFI+Pj4+CmVuZG9iagoKNCAwIG9iago8PC9UeXBlL1BhZ2UvTWVkaWFCb3hbMCAwIDU5NSA4NDJdL1JvdGF0ZSAwL1Jlc291cmNlcyAzIDAgUi9QYXJlbnQgMiAwIFIvQ29udGVudHNbNiAwIFJdPj4KZW5kb2JqCgo1IDAgb2JqCjw8L1R5cGUvRm9udC9TdWJ0eXBlL1R5cGUxL0Jhc2VGb250L0hlbHZldGljYS9FbmNvZGluZy9XaW5BbnNpRW5jb2Rpbmc+PgplbmRvYmoKCjYgMCBvYmoKPDwvTGVuZ3RoIDY0Pj4Kc3RyZWFtCgpxCkJUCjEgMCAwIDEgNzIgNzcwIFRtCi9oZWx2IDExIFRmIFs8NGQ2ZjYzNmIyMDUwNDQ0Nj5dVEoKRVQKUQoKZW5kc3RyZWFtCmVuZG9iagoKeHJlZgowIDcKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDQyIDAwMDAwIG4gCjAwMDAwMDAxMjAgMDAwMDAgbiAKMDAwMDAwMDE3MiAwMDAwMCBuIAowMDAwMDAwMjEzIDAwMDAwIG4gCjAwMDAwMDAzMjAgMDAwMDAgbiAKMDAwMDAwMDQwOSAwMDAwMCBuIAoKdHJhaWxlcgo8PC9TaXplIDcvUm9vdCAxIDAgUi9JRFs8QzI4Q0MyQkRDMjhEMjE1NzM3QzI5NEMzODcyOUMzODA+PDQyOURFQkM1NzgxRUY0QjY0OUFBNEQxNUQ5OUUyNUU3Pl0+PgpzdGFydHhyZWYKNTIyCiUlRU9GCg==",
  "base64"
);

async function stubBaseRoutes(page, streamBody, options = {}) {
  await page.route("**/api/config", async (route) => {
    const req = route.request();
    if (req.method() === "GET") {
      await route.fulfill({
        contentType: "application/json",
        body: JSON.stringify({
          scoping_models: [{ id: "gpt-5.4", label: "GPT-5.4", default: true }],
          extraction_models: [{ id: "gpt-5.4", label: "GPT-5.4", default: true }],
          pipeline: { mode: "multi_agent" },
          small_doc_threshold: 15,
          reflective_loop: { max_retries: 0, retry_on_severity: "error" },
        }),
      });
      return;
    }

    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.route("**/api/manuals", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        manuals: [{ filename: "mock-manual.pdf", size_bytes: 12345 }],
      }),
    });
  });

  await page.route("**/api/load-manual", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        pdf_id: "mock-pdf",
        filename: "mock-manual.pdf",
      }),
    });
  });

  await page.route("**/pdf/mock-pdf", async (route) => {
    await route.fulfill({
      contentType: "application/pdf",
      body: MOCK_PDF,
    });
  });

  await page.route("**/chat/start/mock-pdf", async (route) => {
    if (options.onChatStart) {
      options.onChatStart(route.request().postDataJSON());
    }
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok", pdf_id: "mock-pdf" }),
    });
  });

  await page.route("**/chat/stream/mock-pdf", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: streamBody,
    });
  });
}

async function openChat(page) {
  await page.goto("/");
  await page.selectOption("#manual-select", "mock-manual.pdf");
  await page.click("#upload-btn");
}

async function installMockEventSource(page) {
  await page.addInitScript(() => {
    window.__mockEventSources = [];
    window.__emitMockSse = (event) => {
      const source = window.__mockEventSources[window.__mockEventSources.length - 1];
      if (source?.onmessage) {
        source.onmessage({ data: JSON.stringify(event) });
      }
    };

    class MockEventSource {
      constructor(url) {
        this.url = url;
        this.readyState = 1;
        window.__mockEventSources.push(this);
        setTimeout(() => this.onopen?.({ type: "open" }), 0);
      }

      close() {
        this.readyState = 2;
      }
    }

    window.EventSource = MockEventSource;
  });
}

async function emitSse(page, event) {
  await page.evaluate((evt) => window.__emitMockSse(evt), event);
}

function sampleGraph(index = 0, total = 2) {
  const suffix = String(index + 1).padStart(3, "0");
  return {
    nodes: [
      { id: `SYM-${suffix}`, label: `Symptom ${index + 1}`, group: "Symptom" },
      { id: `FM-${suffix}`, label: `Failure ${index + 1}`, group: "FailureMode" },
      { id: `CA-${suffix}`, label: `Action ${index + 1}`, group: "CorrectiveAction" },
    ],
    edges: [
      { id: `e${index}-0`, from: `SYM-${suffix}`, to: `FM-${suffix}`, label: "MAY_INDICATE" },
      { id: `e${index}-1`, from: `FM-${suffix}`, to: `CA-${suffix}`, label: "HAS_CORRECTIVE_ACTION" },
    ],
    focus_index: index,
    focus_node_ids: [`SYM-${suffix}`, `FM-${suffix}`, `CA-${suffix}`],
    focus_edge_ids: [`e${index}-0`, `e${index}-1`],
    review_graph: true,
    approved_triplet_count: index,
    total_triplets: total,
    current_triplet_index: index,
    current_is_preview: true,
  };
}

function sampleTripletPayload(index = 0, total = 2) {
  const suffix = String(index + 1).padStart(3, "0");
  return {
    index,
    total,
    graph: sampleGraph(index, total),
    triplet: {
      symptom: {
        symptom_id: `SYM-${suffix}`,
        name: `Symptom ${index + 1}`,
        description: `Symptom ${index + 1} description.`,
        severity: "Medium",
        evidence_page: 1,
      },
      failure_modes: [
        {
          failure_mode_id: `FM-${suffix}`,
          name: `Failure ${index + 1}`,
          description: `Failure ${index + 1} description.`,
          material_context: "Drive",
          linked_symptom_id: `SYM-${suffix}`,
          evidence_page: 1,
        },
      ],
      corrective_actions: [
        {
          action_id: `CA-${suffix}`,
          name: `Action ${index + 1}`,
          description: `Action ${index + 1} description.`,
          instruction_text: "Inspect, adjust, and verify.",
          source_page: 1,
          linked_failure_mode_id: `FM-${suffix}`,
        },
      ],
    },
  };
}

test("startup sends zero page offset when manual page 1 is PDF page 1", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  let chatStartBody = null;
  await stubBaseRoutes(
    page,
    'data: {"type":"done"}\n\n',
    {
      onChatStart(body) {
        chatStartBody = body;
      },
    },
  );

  await page.goto("/");
  await page.fill("#startup-page-offset", "1");
  await page.selectOption("#manual-select", "mock-manual.pdf");
  await page.click("#upload-btn");

  await expect.poll(() => chatStartBody?.page_offset).toBe(0);
});

test("thinking indicator disappears as soon as progress arrives", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  await stubBaseRoutes(
    page,
    [
      'data: {"type":"chat_delta","text":"Hello from the assistant."}',
      "",
      'data: {"type":"thinking"}',
      "",
      'data: {"type":"progress","phase":"scoping","message":"Finding the relevant sections."}',
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  await expect(page.locator(".chat-bubble--progress")).toContainText("Finding the relevant sections.");
  await expect(page.locator(".chat-bubble--thinking")).toHaveCount(0);

  const classes = await page.locator("#chat-stream > *").evaluateAll((nodes) =>
    nodes.map((node) => node.className)
  );
  expect(classes).toHaveLength(2);
  expect(classes[0]).toBe("chat-bubble chat-bubble--assistant");
  expect(classes[1]).toContain("chat-bubble--progress");
});

test("assistant messages render progressively word by word", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  await page.emulateMedia({ reducedMotion: "no-preference" });
  const text = Array.from({ length: 80 }, (_, index) => `word${index + 1}`).join(" ");
  await stubBaseRoutes(
    page,
    [
      `data: ${JSON.stringify({ type: "chat_delta", text })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  const bubble = page.locator(".chat-bubble--assistant").first();
  await expect(bubble).toBeVisible();
  await expect.poll(async () => (await bubble.textContent()) || "").not.toBe(text);
  await expect(bubble).toContainText(text, { timeout: 10000 });
});

test("turn indicator makes it clear when the system is still working", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  await stubBaseRoutes(
    page,
    [
      'data: {"type":"chat_delta","text":"Hello from the assistant."}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  await expect(page.locator("#chat-turn-indicator")).toHaveAttribute("data-mode", "working");
  await expect(page.locator("#chat-turn-badge")).toHaveText("System is working");
  await expect(page.locator("#chat-turn-text")).toContainText("Scoping");
  await expect(page.locator("#chat-turn-text")).toContainText("Starting the extraction workflow");
});

test("assistant messages hide raw widget update json", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  const widgetPayload = {
    status: "ok",
    sections: [{ name: "Alarms", start: 32, end: 32 }],
    pages_to_keep: [32],
    total_pages: 114,
  };
  await stubBaseRoutes(
    page,
    [
      `data: ${JSON.stringify({
        type: "widget",
        widget: "sections",
        payload: widgetPayload,
      })}`,
      "",
      `data: ${JSON.stringify({
        type: "chat_delta",
        text: `${JSON.stringify({ widget: "sections", event: "update", payload: widgetPayload })}\nScoping is complete. Review the Section Selection widget.`,
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  await expect(page.getByRole("dialog", { name: "Section Selection" })).toBeVisible();
  await expect(page.locator(".chat-bubble--assistant")).toContainText("Scoping is complete");
  await expect(page.locator("#chat-stream")).not.toContainText('{"widget":"sections"');
});

test("manual and chatbot columns can be resized horizontally", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 960 });
  await stubBaseRoutes(
    page,
    [
      'data: {"type":"chat_delta","text":"Ready."}',
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  const left = page.locator(".chat-pdf-section");
  const right = page.locator(".chat-section");
  const handle = page.locator("#chat-column-resizer");
  await expect(handle).toBeVisible();
  await handle.scrollIntoViewIfNeeded();

  const beforeLeft = await left.boundingBox();
  const beforeRight = await right.boundingBox();
  const handleBox = await handle.boundingBox();
  expect(beforeLeft).not.toBeNull();
  expect(beforeRight).not.toBeNull();
  expect(handleBox).not.toBeNull();
  expect(handleBox.width).toBeGreaterThan(0);
  expect(handleBox.height).toBeGreaterThan(0);
  await expect(handle).toHaveAttribute("data-bound", "true");
  const hitId = await page.evaluate(({ x, y }) => {
    const el = document.elementFromPoint(x, y);
    return el ? `${el.tagName}#${el.id}.${el.className}` : "";
  }, { x: handleBox.x + handleBox.width / 2, y: handleBox.y + handleBox.height / 2 });
  expect(String(hitId)).toContain("chat-column-resizer");

  await page.mouse.move(handleBox.x + handleBox.width / 2, handleBox.y + handleBox.height / 2);
  await page.mouse.down();
  await page.mouse.move(handleBox.x + handleBox.width / 2 + 180, handleBox.y + handleBox.height / 2, { steps: 8 });
  await page.mouse.up();

  const afterLeft = await left.boundingBox();
  const afterRight = await right.boundingBox();
  expect(afterLeft.width).toBeGreaterThan(beforeLeft.width + 120);
  expect(afterRight.width).toBeLessThan(beforeRight.width - 120);
  await expect(right).toBeVisible();
});

test("section widget opens in sheet with scrollable body", async ({ page }) => {
  await page.setViewportSize({ width: 1800, height: 1000 });
  await page.addInitScript(() => {
    window.localStorage.removeItem("kg_chat_left_column_width");
  });
  await stubBaseRoutes(
    page,
    [
      'data: {"type":"chat_delta","text":"Section review ready."}',
      "",
      `data: ${JSON.stringify({
        type: "widget",
        widget: "sections",
        payload: {
          sections: Array.from({ length: 18 }, (_, index) => ({
            name: `Section ${index + 1}`,
            start: index * 6 + 1,
            end: index * 6 + 6,
          })),
          pages_to_keep: Array.from({ length: 108 }, (_, index) => index + 1),
          total_pages: 114,
          product_info: {
            product_name: "Mock Robot",
            document_type: "Maintenance Manual",
          },
        },
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await page.goto("/");
  await page.evaluate(() => {
    window.localStorage.removeItem("kg_chat_left_column_width");
  });
  await page.selectOption("#manual-select", "mock-manual.pdf");
  await page.click("#upload-btn");

  const widget = page.getByRole("dialog", { name: "Section Selection" });
  await expect(widget).toBeVisible();

  const initialBox = await widget.boundingBox();
  expect(initialBox).not.toBeNull();
  expect(initialBox.height).toBeGreaterThan(900);

  const bodyScroll = await widget.locator(".widget-sheet-body").evaluate((body) => {
    const before = body.scrollTop;
    body.scrollTop = before + 320;
    return {
      before,
      after: body.scrollTop,
      scrollHeight: body.scrollHeight,
      clientHeight: body.clientHeight,
    };
  });
  expect(bodyScroll.scrollHeight).toBeGreaterThan(bodyScroll.clientHeight);
  expect(bodyScroll.after).toBeGreaterThan(bodyScroll.before);
});

test("chat pdf panel is scrollable and supports text search", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 760 });
  await stubBaseRoutes(
    page,
    [
      'data: {"type":"chat_delta","text":"Hello from the assistant."}',
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  await expect(page.locator("#chat-pdf-container .chat-pdf-page")).toHaveCount(1);

  const scrollInfo = await page.locator("#chat-pdf-container").evaluate((el) => {
    return {
      scrollHeight: el.scrollHeight,
      clientHeight: el.clientHeight,
    };
  });
  expect(scrollInfo.scrollHeight).toBeGreaterThan(scrollInfo.clientHeight);

  await page.fill("#chat-pdf-search", "Mock PDF");
  await page.click("#chat-pdf-search-btn");

  await expect(page.locator("#chat-pdf-search-meta")).toContainText("Match 1 of 1");
  await expect(page.locator(".chat-pdf-page--active-match")).toHaveCount(1);
});

test("ontology review shows required fields before enabling extraction", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  await stubBaseRoutes(
    page,
    [
      `data: ${JSON.stringify({
        type: "widget",
        widget: "ontology_review",
        payload: {
          status: "needs_human",
          node_count: 1,
          node_type_counts: { Asset: 1 },
          selected_pages_count: 12,
          selected_sections_count: 3,
          graph_issues_count: 0,
          schema_issues_count: 0,
          human_fields_count: 1,
          suggested_relations_count: 4,
          preview_relations: [],
          confidence_counts: {},
          human_required_fields: [
            {
              field_key: "Asset::ASSET-001::brand",
              prompt: "Provide the brand for Asset VB Series.",
              property_name: "brand",
              suggested_value: "Fryer",
              allowed_values: [],
            },
          ],
        },
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  const widget = page.getByRole("dialog", { name: "Ontology Draft Ready" });
  await expect(widget).toContainText("Provide the brand");
  await expect(widget.locator("[data-field-key='Asset::ASSET-001::brand']")).toHaveValue("Fryer");
  await expect(page.getByRole("button", { name: "Complete Required Items" })).toBeDisabled();
});

test("ontology review widget shows draft stats and graph issue candidates", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 960 });
  await stubBaseRoutes(
    page,
    [
      'data: {"type":"chat_delta","text":"Ontology draft ready."}',
      "",
      `data: ${JSON.stringify({
        type: "critique",
        message: "Graph issue: Symptom 'Axis backlash' is not connected to any Asset in the graph.",
        entity_id: "SYM-001",
        issue_type: "orphan",
        candidates: [
          {
            index: 0,
            relation_name: "MAY_INDICATE",
            from_id: "SYM-001",
            from_label: "Axis backlash",
            to_id: "FM-001",
            to_label: "Backlash compensation mismatch",
            confidence: 0.81,
            rationale: "Token overlap 0.81.",
          },
        ],
      })}`,
      "",
      `data: ${JSON.stringify({
        type: "widget",
        widget: "ontology_review",
        payload: {
          status: "needs_human_review",
          node_count: 19,
          node_type_counts: {
            Asset: 1,
            Symptom: 6,
            FailureMode: 5,
            CorrectiveAction: 7,
          },
          selected_pages_count: 82,
          selected_sections_count: 42,
          graph_issues_count: 6,
          graph_issue_types: { orphan: 6 },
          resolution_completion: {
            target_count: 3,
            attempted: 3,
            completed: 2,
            attempts: [
              { target_id: "FM-001", status: "completed", pages: [12, 13] },
              { target_id: "ERR-504", status: "not_found", pages: [44] },
            ],
          },
          top_graph_issues: [
            {
              issue_type: "orphan",
              description: "Symptom 'Axis backlash' is not connected to any Asset in the graph.",
              affected_nodes: ["SYM-001"],
            },
          ],
          human_fields_count: 0,
          schema_issues_count: 0,
          suggested_relations_count: 30,
          preview_relations: [
            {
              relation_name: "MAY_INDICATE",
              from_label: "Axis backlash",
              to_label: "Backlash compensation mismatch",
              confidence: 0.81,
              rationale: "Token overlap 0.81.",
            },
          ],
          confidence_counts: {
            auto_approve: 96,
            human_review: 1,
            auto_reject: 0,
          },
          human_required_fields: [],
        },
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  await expect(page.locator(".critique-candidate-row")).toHaveCount(1);
  await expect(page.locator(".critique-candidate-path")).toContainText("Axis backlash");
  await expect(page.locator(".critique-candidate-path")).toContainText("Backlash compensation mismatch");
  await expect(page.locator(".critique-candidate-row button")).toHaveText("Apply candidate");

  const widget = page.getByRole("dialog", { name: "Ontology Draft Ready" });
  await expect(widget).toContainText("Scoped Pages");
  await expect(widget).toContainText("82");
  await expect(widget).toContainText("Sections");
  await expect(widget).toContainText("42");
  await expect(widget).toContainText("Graph Issues");
  await expect(widget).toContainText("6");
  await expect(widget).toContainText("Resolved Gaps");
  await expect(widget).toContainText("2/3");
  await expect(widget).toContainText("Suggested links");
  await expect(widget).toContainText("MAY_INDICATE");
  await expect(page.getByRole("button", { name: "Continue to Extraction" })).toBeEnabled();
});

test("extraction graph panel focuses current triplet and keeps PDF on action page", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 960 });
  const graph = {
    nodes: [
      { id: "SYM-001", label: "Axis backlash", group: "Symptom" },
      { id: "FM-001", label: "Compensation mismatch", group: "FailureMode" },
      { id: "CA-001", label: "Adjust compensation", group: "CorrectiveAction" },
      { id: "SYM-002", label: "Spindle alarm", group: "Symptom" },
    ],
    edges: [
      { id: "e0", from: "SYM-001", to: "FM-001", label: "MAY_INDICATE" },
      { id: "e1", from: "FM-001", to: "CA-001", label: "HAS_CORRECTIVE_ACTION" },
    ],
    node_types: ["CorrectiveAction", "FailureMode", "Symptom"],
    edge_types: ["HAS_CORRECTIVE_ACTION", "MAY_INDICATE"],
    triplet_count: 2,
    focus_index: 0,
    focus_node_ids: ["SYM-001", "FM-001", "CA-001"],
    focus_edge_ids: ["e0", "e1"],
  };
  await stubBaseRoutes(
    page,
    [
      `data: ${JSON.stringify({
        type: "widget",
        widget: "extraction_graph",
        payload: { graph: { ...graph, focus_node_ids: [], focus_edge_ids: [], focus_index: null } },
      })}`,
      "",
      `data: ${JSON.stringify({
        type: "widget",
        widget: "triplet",
        payload: {
          index: 0,
          total: 2,
          graph,
          triplet: {
            symptom: {
              symptom_id: "SYM-001",
              name: "Axis backlash",
              description: "Axis backlash detected.",
              severity: "Medium",
              evidence_page: 1,
            },
            failure_modes: [
              {
                failure_mode_id: "FM-001",
                name: "Compensation mismatch",
                description: "Compensation is incorrect.",
                material_context: "Axis",
                linked_symptom_id: "SYM-001",
                evidence_page: 1,
              },
            ],
            corrective_actions: [
              {
                action_id: "CA-001",
                name: "Adjust compensation",
                description: "Adjust backlash compensation.",
                instruction_text: "1. Measure. 2. Adjust.",
                source_type: "manual",
                source_title: "Mock",
                source_page: 1,
                linked_failure_mode_id: "FM-001",
              },
            ],
          },
        },
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await openChat(page);

  await expect(page.locator("#chat-graph-panel")).toBeVisible();
  await expect(page.locator("#chat-graph-meta")).toContainText("focusing triplet 1");
  await expect(page.locator("#chat-graph-focus")).toHaveClass(/is-active/);
  await expect(page.locator("#chat-graph-canvas")).toContainText("Axis backlash");
  await expect(page.locator("#chat-graph-canvas")).toContainText("Adjust compensation");
  await expect(page.locator("#chat-graph-canvas")).not.toContainText("Spindle alarm");
  await expect(page.locator("#chat-page-indicator")).toContainText("Page 1 / 1");

  await page.click("#chat-graph-all");
  await expect(page.locator("#chat-graph-canvas")).toContainText("Spindle alarm");
});

test("triplet review card saves editable field patches on approval", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  const actions = [];
  await stubBaseRoutes(
    page,
    [
      `data: ${JSON.stringify({
        type: "widget",
        widget: "triplet",
        payload: {
          index: 0,
          total: 1,
          logic_assessment: [
            "Logic: Axis backlash forms a clear symptom-to-failure chain.",
            "Sense check: page 24 has concrete adjustment instructions.",
          ],
          triplet: {
            symptom: {
              symptom_id: "SYM-001",
              name: "Axis backlash",
              description: "Backlash detected.",
              severity: "Medium",
              evidence_page: 20,
            },
            failure_modes: [
              {
                failure_mode_id: "FM-001",
                name: "Compensation mismatch",
                description: "Backlash compensation is incorrect.",
                linked_symptom_id: "SYM-001",
                evidence_page: 23,
              },
            ],
            corrective_actions: [
              {
                action_id: "CA-001",
                name: "Adjust compensation",
                description: "Adjust backlash compensation.",
                instruction_text: "Measure backlash and adjust compensation.",
                source_page: 24,
                linked_failure_mode_id: "FM-001",
              },
            ],
          },
          graph: {
            nodes: [
              { id: "SYM-001", label: "Axis backlash", group: "Symptom" },
              { id: "FM-001", label: "Compensation mismatch", group: "FailureMode" },
              { id: "CA-001", label: "Adjust compensation", group: "CorrectiveAction" },
            ],
            edges: [
              { id: "e0", from: "SYM-001", to: "FM-001", label: "MAY_INDICATE" },
              { id: "e1", from: "FM-001", to: "CA-001", label: "HAS_CORRECTIVE_ACTION" },
            ],
            focus_index: 0,
            focus_node_ids: ["SYM-001", "FM-001", "CA-001"],
            focus_edge_ids: ["e0", "e1"],
            review_graph: true,
            approved_triplet_count: 0,
            total_triplets: 1,
            current_triplet_index: 0,
            current_is_preview: true,
          },
        },
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );
  await page.route("**/chat/action", async (route) => {
    actions.push(route.request().postDataJSON());
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await openChat(page);

  const tripletWidget = page.getByRole("dialog", { name: "Triplet 1 / 1" });
  await expect(tripletWidget.locator(".triplet-logic")).toContainText("Logic: Axis backlash");
  await tripletWidget.locator('[data-field-path="symptom.name"]').evaluate((field, value) => {
    field.textContent = value;
    field.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
  }, "Axis backlash after warmup");
  await expect(tripletWidget.getByRole("button", { name: "Save Edits" })).toBeEnabled();
  await tripletWidget.getByRole("button", { name: "Approve" }).click();

  await expect.poll(() => actions.length).toBe(1);
  expect(actions[0].action).toBe("approve_triplet");
  expect(actions[0].payload.patch).toEqual({
    "symptom.name": "Axis backlash after warmup",
  });
});

test("stale done event does not reset the turn indicator after starting extraction from widget", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  await installMockEventSource(page);
  const actions = [];
  await stubBaseRoutes(page, "");
  await page.route("**/chat/action", async (route) => {
    actions.push(route.request().postDataJSON());
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await openChat(page);
  await expect(page.locator("#chat-layout")).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.__mockEventSources?.length || 0)).toBeGreaterThan(0);

  await emitSse(page, {
    type: "widget",
    widget: "ontology_review",
    payload: {
      status: "ready",
      node_count: 3,
      node_type_counts: { Asset: 1, Symptom: 1, CorrectiveAction: 1 },
      selected_pages_count: 8,
      selected_sections_count: 2,
      graph_issues_count: 0,
      schema_issues_count: 0,
      human_fields_count: 0,
      suggested_relations_count: 0,
      preview_relations: [],
      confidence_counts: {},
      human_required_fields: [],
    },
  });

  const widget = page.getByRole("dialog", { name: "Ontology Draft Ready" });
  await expect(widget).toBeVisible();
  await widget.getByRole("button", { name: "Continue to Extraction" }).click();

  await expect.poll(() => actions.length).toBe(1);
  expect(actions[0].action).toBe("run_extraction");
  expect(actions[0].client_action_id).toMatch(/^action-/);

  await emitSse(page, { type: "done" });

  await expect(page.locator("#chat-turn-badge")).toHaveText("System is working");
  await expect(page.locator("#chat-turn-text")).toContainText("Extraction");
});

test("next triplet sheet remains visible when it arrives during the previous close animation", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  await installMockEventSource(page);
  const actions = [];
  await stubBaseRoutes(page, "");
  await page.route("**/chat/action", async (route) => {
    actions.push(route.request().postDataJSON());
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await openChat(page);
  await expect(page.locator("#chat-layout")).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.__mockEventSources?.length || 0)).toBeGreaterThan(0);

  await emitSse(page, {
    type: "widget",
    widget: "triplet",
    payload: sampleTripletPayload(0, 2),
  });

  const firstTriplet = page.getByRole("dialog", { name: "Triplet 1 / 2" });
  await expect(firstTriplet).toBeVisible();
  await firstTriplet.getByRole("button", { name: "Approve" }).click();
  await expect.poll(() => actions.length).toBe(1);

  await emitSse(page, {
    type: "widget",
    widget: "extraction_graph",
    payload: { graph: sampleGraph(0, 2) },
  });
  await emitSse(page, {
    type: "widget",
    widget: "triplet",
    payload: sampleTripletPayload(1, 2),
  });

  await page.waitForTimeout(420);

  await expect(page.getByRole("dialog", { name: "Triplet 2 / 2" })).toBeVisible();
  await expect(page.locator("#widget-sheet")).toHaveClass(/is-open/);
  await expect(page.locator("#widget-sheet")).not.toHaveAttribute("hidden", "");
});

test("export-ready widget automatically starts ontology export", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  const actions = [];
  await stubBaseRoutes(
    page,
    [
      `data: ${JSON.stringify({
        type: "widget",
        widget: "export",
        payload: {
          status: "done",
          total: 2,
          validated: 2,
          exported: false,
          message: "All triplets reviewed.",
        },
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );
  await page.route("**/chat/action", async (route) => {
    actions.push(route.request().postDataJSON());
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await openChat(page);

  await expect(page.locator(".chat-widget--export")).toContainText("Export will run automatically");
  await expect.poll(() => actions.map((item) => item.action)).toContain("export_ontology");
});

test("export widget exposes the modify workspace inside the chat layout", async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 960 });
  await stubBaseRoutes(
    page,
    [
      `data: ${JSON.stringify({
        type: "widget",
        widget: "export",
        payload: {
          status: "ok",
          exported: true,
          editor_url: "/modify/mock-pdf",
          metrics: {
            document: { total_pages: 12, selected_pages: 4 },
            pricing_basis: { label: "Estimated using configured model pricing" },
            stages: {
              scoping: {
                duration_seconds: 3.2,
                llm_calls: 1,
                prompt_tokens: 400,
                completion_tokens: 80,
                total_tokens: 480,
                estimated_cost_usd: 0.0012,
                details: { selected_pages: 4, total_pages: 12 },
              },
              extraction: {
                duration_seconds: 5.8,
                llm_calls: 2,
                prompt_tokens: 1200,
                completion_tokens: 200,
                total_tokens: 1400,
                estimated_cost_usd: 0.0048,
                details: { triplet_count: 3, selected_pages: 4 },
              },
              export: {
                duration_seconds: 0.6,
                llm_calls: 0,
                prompt_tokens: 0,
                completion_tokens: 0,
                total_tokens: 0,
                estimated_cost_usd: 0,
                details: {},
              },
            },
            totals: {
              duration_seconds: 9.6,
              llm_calls: 3,
              prompt_tokens: 1600,
              completion_tokens: 280,
              total_tokens: 1880,
              estimated_cost_usd: 0.006,
              by_model: {
                "gpt-5.4": {
                  label: "GPT-5.4",
                  llm_calls: 3,
                  total_tokens: 1880,
                  estimated_cost_usd: 0.006,
                },
              },
            },
            review: {
              validated_triplets: 2,
              discarded_triplets: 1,
              extracted_triplets: 3,
            },
            derived_kpis: {
              pages_kept_ratio: 0.3333,
              seconds_per_selected_page: 2.4,
              cost_per_selected_page_usd: 0.0015,
              cost_per_extracted_triplet_usd: 0.002,
            },
            nodes_by_type: {
              Component: 4,
              FailureMode: 3,
              CorrectiveAction: 2,
            },
          },
          message: "Export complete.",
        },
      })}`,
      "",
      'data: {"type":"done"}',
      "",
    ].join("\n"),
  );

  await page.route("**/modify/mock-pdf**", async (route) => {
    await route.fulfill({
      contentType: "text/html",
      body: "<!doctype html><html><body>Mock modify workspace</body></html>",
    });
  });

  await openChat(page);

  await expect(page.locator(".chat-widget--export")).toContainText("inspect and modify the graph");
  await expect(page.locator(".chat-widget--export")).toContainText("Estimated Cost");
  await expect(page.locator(".chat-widget--export")).toContainText("Model Cost Breakdown");
  await expect(page.locator(".chat-widget--export")).toContainText("Node Count by Type");
  await expect(page.locator("#chat-modify-btn")).toBeVisible();
  await page.click(".chat-widget--export >> text=Inspect / Modify Graph");

  await expect(page.locator(".chat-pdf-section")).toHaveClass(/chat-pdf-section--modify/);
  await expect(page.locator("#chat-modify-btn")).toHaveText("Manual");
  await expect(page.locator("#chat-modify-panel")).toBeVisible();
  await expect(page.frameLocator("#chat-modify-frame").locator("body")).toContainText("Mock modify workspace");
});
