const { test, expect } = require("@playwright/test");

const MOCK_PDF = Buffer.from(
  "JVBERi0xLjcKJcK1wrYKJSBXcml0dGVuIGJ5IE11UERGIDEuMjcuMQoKMSAwIG9iago8PC9UeXBlL0NhdGFsb2cvUGFnZXMgMiAwIFIvSW5mbzw8L1Byb2R1Y2VyKE11UERGIDEuMjcuMSk+Pj4+CmVuZG9iagoKMiAwIG9iago8PC9UeXBlL1BhZ2VzL0NvdW50IDEvS2lkc1s0IDAgUl0+PgplbmRvYmoKCjMgMCBvYmoKPDwvRm9udDw8L2hlbHYgNSAwIFI+Pj4+CmVuZG9iagoKNCAwIG9iago8PC9UeXBlL1BhZ2UvTWVkaWFCb3hbMCAwIDU5NSA4NDJdL1JvdGF0ZSAwL1Jlc291cmNlcyAzIDAgUi9QYXJlbnQgMiAwIFIvQ29udGVudHNbNiAwIFJdPj4KZW5kb2JqCgo1IDAgb2JqCjw8L1R5cGUvRm9udC9TdWJ0eXBlL1R5cGUxL0Jhc2VGb250L0hlbHZldGljYS9FbmNvZGluZy9XaW5BbnNpRW5jb2Rpbmc+PgplbmRvYmoKCjYgMCBvYmoKPDwvTGVuZ3RoIDY0Pj4Kc3RyZWFtCgpxCkJUCjEgMCAwIDEgNzIgNzcwIFRtCi9oZWx2IDExIFRmIFs8NGQ2ZjYzNmIyMDUwNDQ0Nj5dVEoKRVQKUQoKZW5kc3RyZWFtCmVuZG9iagoKeHJlZgowIDcKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDQyIDAwMDAwIG4gCjAwMDAwMDAxMjAgMDAwMDAgbiAKMDAwMDAwMDE3MiAwMDAwMCBuIAowMDAwMDAwMjEzIDAwMDAwIG4gCjAwMDAwMDAzMjAgMDAwMDAgbiAKMDAwMDAwMDQwOSAwMDAwMCBuIAoKdHJhaWxlcgo8PC9TaXplIDcvUm9vdCAxIDAgUi9JRFs8QzI4Q0MyQkRDMjhEMjE1NzM3QzI5NEMzODcyOUMzODA+PDQyOURFQkM1NzgxRUY0QjY0OUFBNEQxNUQ5OUUyNUU3Pl0+PgpzdGFydHhyZWYKNTIyCiUlRU9GCg==",
  "base64"
);

test("chat bootstrap recovers if the chat layout shell is missing from the DOM", async ({ page }) => {
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
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok", pdf_id: "mock-pdf" }),
    });
  });

  await page.route("**/chat/stream/mock-pdf", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: [
        'data: {"type":"chat_delta","text":"Hello from the fallback shell."}',
        "",
        'data: {"type":"done"}',
        "",
      ].join("\n"),
    });
  });

  await page.goto("/");
  await page.evaluate(() => document.getElementById("chat-layout")?.remove());

  await page.selectOption("#manual-select", "mock-manual.pdf");
  await page.click("#upload-btn");

  await expect(page.locator("#upload-screen")).toBeHidden();
  await expect(page.locator("#chat-layout")).toBeVisible();
  await expect(page.locator("#chat-stream")).toContainText("Hello from the fallback shell.");
});
