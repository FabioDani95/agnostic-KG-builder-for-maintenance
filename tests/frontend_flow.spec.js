const { test, expect } = require("@playwright/test");

const MOCK_PDF = Buffer.from(
  "JVBERi0xLjcKJcK1wrYKJSBXcml0dGVuIGJ5IE11UERGIDEuMjcuMQoKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFIvSW5mbzw8L1Byb2R1Y2VyKE11UERGIDEuMjcuMSk+Pj4+CmVuZG9iagoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0NvdW50IDEvS2lkc1s0IDAgUl0+PgplbmRvYmoKCjMgMCBvYmoKPDwvRm9udDw8L2hlbHYgNSAwIFI+Pj4+CmVuZG9iagoKNCAwIG9iago8PC9UeXBlL1BhZ2UvTWVkaWFCb3hbMCAwIDU5NSA4NDJdL1JvdGF0ZSAwL1Jlc291cmNlcyAzIDAgUi9QYXJlbnQgMiAwIFIvQ29udGVudHNbNiAwIFJdPj4KZW5kb2JqCgo1IDAgb2JqCjw8L1R5cGUvRm9udC9TdWJ0eXBlL1R5cGUxL0Jhc2VGb250L0hlbHZldGljYS9FbmNvZGluZy9XaW5BbnNpRW5jb2Rpbmc+PgplbmRvYmoKCjYgMCBvYmoKPDwvTGVuZ3RoIDY0Pj4Kc3RyZWFtCgpxCkJUCjEgMCAwIDEgNzIgNzcwIFRtCi9oZWx2IDExIFRmIFs8NGQ2ZjYzNmIyMDUwNDQ0Nj5dVEoKRVQKUQoKZW5kc3RyZWFtCmVuZG9iagoKeHJlZgowIDcKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDQyIDAwMDAwIG4gCjAwMDAwMDAxMjAgMDAwMDAgbiAKMDAwMDAwMDE3MiAwMDAwMCBuIAowMDAwMDAwMjEzIDAwMDAwIG4gCjAwMDAwMDAzMjAgMDAwMDAgbiAKMDAwMDAwMDQwOSAwMDAwMCBuIAoKdHJhaWxlcgo8PC9TaXplIDcvUm9vdCAxIDAgUi9JRFs8QzI4Q0MyQkRDMjhEMjE1NzM3QzI5NEMzODcyOUMzODA+PDQyOURFQkM1NzgxRUY0QjY0OUFBNEQxNUQ5OUUyNUU3Pl0+PgpzdGFydHhyZWYKNTIyCiUlRU9GCg==",
  "base64",
);

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
  await expect.poll(async () => page.evaluate(() => window.__mockEventSources?.length || 0)).toBeGreaterThan(0);
  await page.evaluate((evt) => window.__emitMockSse(evt), event);
}

async function stubStartupRoutes(page, onChatAction) {
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
        page_count: 2,
        run_id: "run-mock",
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
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok", pdf_id: "mock-pdf" }),
    });
  });

  await page.route("**/chat/action", async (route) => {
    onChatAction(route.request().postDataJSON());
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });
}

test("chat-first frontend flow opens section review and approves cut plan", async ({ page }) => {
  await page.setViewportSize({ width: 1500, height: 960 });
  await installMockEventSource(page);
  let chatActionBody = null;
  await stubStartupRoutes(page, (body) => {
    chatActionBody = body;
  });

  await page.goto("/");

  await expect(page.getByText("Diagnostic Knowledge Graph Extraction")).toBeVisible();
  await expect(page.locator("#pipeline-mode")).toHaveCount(0);
  await page.locator("#manual-select").selectOption("mock-manual.pdf");
  await page.locator("#upload-form").evaluate((form) =>
    form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })),
  );

  await expect(page.locator("#chat-layout")).toBeVisible();
  await expect(page.locator("#chat-doc-title")).toContainText("mock-manual.pdf");

  await emitSse(page, {
    type: "widget",
    widget: "sections",
    payload: {
      sections: [{ name: "Troubleshooting", start: 1, end: 2, source: "rule" }],
      pages_to_keep: [1, 2],
      total_pages: 2,
      product_info: { product_name: "Mock Robot", document_type: "Service manual" },
    },
  });

  await expect(page.getByRole("heading", { name: "Section Selection" })).toBeVisible();
  await expect(page.getByText("Troubleshooting")).toBeVisible();
  await page.getByRole("button", { name: "Approve & Continue" }).click();

  await expect.poll(() => chatActionBody?.action).toBe("approve_cut_plan");
  expect(chatActionBody.pdf_id).toBe("mock-pdf");
  expect(chatActionBody.client_action_id).toMatch(/^action-/);
});
