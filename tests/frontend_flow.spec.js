const fs = require("fs");
const path = require("path");
const { test, expect } = require("playwright/test");

function firstLocalPdf() {
  const manualsDir = path.join(__dirname, "..", "manuals");
  const pdf = fs.readdirSync(manualsDir).find((name) => name.toLowerCase().endsWith(".pdf"));
  if (!pdf) {
    throw new Error("No PDF found in manuals/ for frontend test");
  }
  return path.join(manualsDir, pdf);
}

for (const pipelineMode of ["classic", "multi_agent"]) {
test(`frontend flow reaches final JSON download without rerun (${pipelineMode})`, async ({ page }) => {
  const pdfPath = firstLocalPdf();

  await page.route("**/api/config", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        scoping_models: [
          { id: "gpt-5.4", label: "GPT-5.4", default: true },
          { id: "gpt-5.4-mini", label: "GPT-5.4 Mini", default: false },
        ],
        extraction_models: [
          { id: "gpt-5.4", label: "GPT-5.4", default: true },
          { id: "gpt-5.4-mini", label: "GPT-5.4 Mini", default: false },
        ],
        pipeline: {
          mode: pipelineMode,
        },
        small_doc_threshold: 15,
        reflective_loop: {
          max_retries: 0,
          retry_on_severity: "error",
        },
      }),
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
      }),
    });
  });

  await page.route("**/cut-plan", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        pdf_id: "mock-pdf",
        total_pages: 2,
        sections: [
          {
            name: "Troubleshooting",
            page_range: { start: 1, end: 2 },
            manual_page_range: { start: 1, end: 2 },
            source: "rule",
            keyword_matches: ["error"],
            reasoning: "Relevant diagnostic section",
          },
        ],
        pages_to_keep: [1, 2],
        page_offset: 0,
        toc: null,
        skipped: false,
        product_info: {
          product_name: "Mock Robot",
          document_type: "Service manual",
          language: "en",
          page_count: 2,
        },
      }),
    });
  });

  await page.route("**/pdf/mock-pdf", async (route) => {
    await route.fulfill({
      path: pdfPath,
      contentType: "application/pdf",
    });
  });

  await page.route("**/cut-plan/approve", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({ status: "ok" }),
    });
  });

  await page.route("**/ontology/draft", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        status: "blocked",
        ontology: {
          ontology_name: "Core_Ontology",
          version: "2.0",
          language: "en",
          source_type: "Service manual",
          source_title: "Mock Robot",
          nodes: {
            Asset: [
              {
                asset_id: "ASSET-001",
                name: "Mock Robot",
                description: "Robot asset",
                brand: "",
                model: "M-100",
                asset_type: "robot",
              },
            ],
            Component: [],
            Symptom: [],
            FailureMode: [],
            CorrectiveAction: [],
            ErrorCode: [],
          },
          relations: [],
        },
        semantic_issues: [],
        schema_issues: [
          {
            severity: "error",
            code: "empty_draft_content",
            message: "Ontology draft contains only the Asset node and no extracted diagnostic content.",
            target_type: "ontology",
            target_id: "",
            property_name: "",
            fix_hint: "Triplet review can still continue.",
          },
        ],
        human_required_fields: [
          {
            field_key: "Asset::ASSET-001::brand",
            prompt: "Provide the brand for Asset Mock Robot.",
            target_type: "Asset",
            target_id: "ASSET-001",
            property_name: "brand",
            reason: "Required by ontology schema but missing from the draft.",
            expected_type: "string",
            suggested_value: "ABB",
            allowed_values: [],
          },
        ],
        is_schema_compliant: false,
        is_ready_for_human_review: false,
        retry_count: 0,
        graph_issues: [],
        suggested_relations: [
          {
            relation_name: "HAS_COMPONENT",
            from_type: "Asset",
            from_id: "ASSET-001",
            from_label: "Mock Robot",
            to_type: "Component",
            to_id: "CMP-001",
            to_label: "Power board",
            confidence: 0.92,
            rationale: "Mentioned repeatedly in troubleshooting notes.",
          },
          {
            relation_name: "GENERATES_ERROR",
            from_type: "Asset",
            from_id: "ASSET-001",
            from_label: "Mock Robot",
            to_type: "ErrorCode",
            to_id: "ERR-001",
            to_label: "E100",
            confidence: 0.64,
            rationale: "Weak match.",
          },
        ],
      }),
    });
  });

  await page.route("**/ontology/apply-suggestions", async (route) => {
    const request = route.request().postDataJSON();
    expect(request.accepted_suggestions).toHaveLength(1);
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        status: "blocked",
        ontology: {
          ontology_name: "Core_Ontology",
          version: "2.0",
          language: "en",
          source_type: "Service manual",
          source_title: "Mock Robot",
          nodes: {
            Asset: [
              {
                asset_id: "ASSET-001",
                name: "Mock Robot",
                description: "Robot asset",
                brand: "",
                model: "M-100",
                asset_type: "robot",
              },
            ],
            Component: [
              {
                component_id: "CMP-001",
                name: "Power board",
                description: "Main power board",
                category: "electrical",
              },
            ],
            Symptom: [],
            FailureMode: [],
            CorrectiveAction: [],
            ErrorCode: [],
          },
          relations: [
            {
              name: "HAS_COMPONENT",
              from_type: "Asset",
              from_id: "ASSET-001",
              to_type: "Component",
              to_id: "CMP-001",
              evidence: [],
            },
          ],
        },
        semantic_issues: [],
        schema_issues: [
          {
            severity: "error",
            code: "empty_draft_content",
            message: "Ontology draft contains only the Asset node and no extracted diagnostic content.",
            target_type: "ontology",
            target_id: "",
            property_name: "",
            fix_hint: "Triplet review can still continue.",
          },
        ],
        human_required_fields: [
          {
            field_key: "Asset::ASSET-001::brand",
            prompt: "Provide the brand for Asset Mock Robot.",
            target_type: "Asset",
            target_id: "ASSET-001",
            property_name: "brand",
            reason: "Required by ontology schema but missing from the draft.",
            expected_type: "string",
            suggested_value: "ABB",
            allowed_values: [],
          },
        ],
        is_schema_compliant: false,
        is_ready_for_human_review: false,
        retry_count: 0,
        graph_issues: [],
        suggested_relations: [],
      }),
    });
  });

  await page.route("**/ontology/review", async (route) => {
    const request = route.request().postDataJSON();
    expect(request.answers).toEqual([
      {
        field_key: "Asset::ASSET-001::brand",
        value: "ABB",
      },
    ]);
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        status: "blocked",
        ontology: {
          ontology_name: "Core_Ontology",
          version: "2.0",
          language: "en",
          source_type: "Service manual",
          source_title: "Mock Robot",
          nodes: {
            Asset: [
              {
                asset_id: "ASSET-001",
                name: "Mock Robot",
                description: "Robot asset",
                brand: "ABB",
                model: "M-100",
                asset_type: "robot",
              },
            ],
            Component: [
              {
                component_id: "CMP-001",
                name: "Power board",
                description: "Main power board",
                category: "electrical",
              },
            ],
            Symptom: [],
            FailureMode: [],
            CorrectiveAction: [],
            ErrorCode: [],
          },
          relations: [
            {
              name: "HAS_COMPONENT",
              from_type: "Asset",
              from_id: "ASSET-001",
              to_type: "Component",
              to_id: "CMP-001",
              evidence: [],
            },
          ],
        },
        semantic_issues: [],
        schema_issues: [
          {
            severity: "error",
            code: "empty_draft_content",
            message: "Ontology draft contains only the Asset node and no extracted diagnostic content.",
            target_type: "ontology",
            target_id: "",
            property_name: "",
            fix_hint: "Triplet review can still continue.",
          },
        ],
        human_required_fields: [],
        is_schema_compliant: false,
        is_ready_for_human_review: false,
        retry_count: 0,
        graph_issues: [],
        suggested_relations: [],
      }),
    });
  });

  await page.route("**/extract-tables", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        triplets: [
          {
            symptom: {
              symptom_id: "SYM-001",
              name: "Robot does not start",
              description: "Startup failure",
              severity: "High",
            },
            failure_modes: [
              {
                failure_mode_id: "FM-001",
                name: "Power board fault",
                description: "Board failure",
                material_context: "Power board",
                linked_symptom_id: "SYM-001",
              },
            ],
            corrective_actions: [
              {
                action_id: "ACT-001",
                name: "Replace power board",
                description: "Replace faulty board",
                instruction_text: "Install a new board and reboot.",
                source_type: "Service manual",
                source_title: "Mock Robot",
                source_page: 1,
                linked_failure_mode_id: "FM-001",
              },
            ],
          },
        ],
        raw_symptom_table: "",
        raw_failure_mode_table: "",
        raw_corrective_action_table: "",
      }),
    });
  });

  await page.route("**/generate-json", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: {
        "Content-Disposition": 'attachment; filename="mock_export.json"',
      },
      body: JSON.stringify({
        metadata: {
          version: "V0",
        },
        nodes: {},
        relationships: [],
      }),
    });
  });

  await page.route("**/run-metrics/**", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        document: {
          filename: "mock-manual.pdf",
          total_pages: 2,
          selected_pages: 2,
        },
        pricing_basis: {
          label: "Estimated using configured model pricing",
        },
        stages: {
          scoping: {
            stage: "scoping",
            duration_seconds: 3.2,
            llm_calls: 2,
            prompt_tokens: 1000,
            cached_prompt_tokens: 0,
            non_cached_prompt_tokens: 1000,
            completion_tokens: 300,
            total_tokens: 1300,
            estimated_cost_usd: 0.007,
            models: ["gpt-5.4"],
            operations: ["scoping"],
            by_model: {
              "gpt-5.4": {
                label: "GPT-5.4",
                llm_calls: 2,
                prompt_tokens: 1000,
                cached_prompt_tokens: 0,
                non_cached_prompt_tokens: 1000,
                completion_tokens: 300,
                total_tokens: 1300,
                estimated_cost_usd: 0.007,
              },
            },
            details: { total_pages: 2, selected_pages: 2, selected_sections: 1, skipped: false },
          },
          ontology: {
            stage: "ontology",
            duration_seconds: 5.4,
            llm_calls: 3,
            prompt_tokens: 2000,
            cached_prompt_tokens: 0,
            non_cached_prompt_tokens: 2000,
            completion_tokens: 800,
            total_tokens: 2800,
            estimated_cost_usd: 0.017,
            models: ["gpt-5.4"],
            operations: ["ontology_draft", "ontology_validation"],
            by_model: {
              "gpt-5.4": {
                label: "GPT-5.4",
                llm_calls: 3,
                prompt_tokens: 2000,
                cached_prompt_tokens: 0,
                non_cached_prompt_tokens: 2000,
                completion_tokens: 800,
                total_tokens: 2800,
                estimated_cost_usd: 0.017,
              },
            },
            details: { selected_pages: 2, selected_sections: 1, chunk_count: 1, retry_count: 0, status: "blocked" },
          },
          extraction: {
            stage: "extraction",
            duration_seconds: 4.1,
            llm_calls: 1,
            prompt_tokens: 900,
            cached_prompt_tokens: 0,
            non_cached_prompt_tokens: 900,
            completion_tokens: 350,
            total_tokens: 1250,
            estimated_cost_usd: 0.0075,
            models: ["gpt-5.4"],
            operations: ["extraction"],
            by_model: {
              "gpt-5.4": {
                label: "GPT-5.4",
                llm_calls: 1,
                prompt_tokens: 900,
                cached_prompt_tokens: 0,
                non_cached_prompt_tokens: 900,
                completion_tokens: 350,
                total_tokens: 1250,
                estimated_cost_usd: 0.0075,
              },
            },
            details: { selected_pages: 2, triplet_count: 1 },
          },
          export: {
            stage: "export",
            duration_seconds: 0.2,
            llm_calls: 0,
            prompt_tokens: 0,
            cached_prompt_tokens: 0,
            non_cached_prompt_tokens: 0,
            completion_tokens: 0,
            total_tokens: 0,
            estimated_cost_usd: 0,
            models: [],
            operations: [],
            by_model: {},
            details: { validated_triplets: 1, filename: "mock_export.json", export_base: "minimal_fallback" },
          },
        },
        totals: {
          duration_seconds: 12.9,
          llm_calls: 6,
          prompt_tokens: 3900,
          cached_prompt_tokens: 0,
          non_cached_prompt_tokens: 3900,
          completion_tokens: 1450,
          total_tokens: 5350,
          estimated_cost_usd: 0.0315,
          by_model: {
            "gpt-5.4": {
              label: "GPT-5.4",
              llm_calls: 6,
              prompt_tokens: 3900,
              cached_prompt_tokens: 0,
              non_cached_prompt_tokens: 3900,
              completion_tokens: 1450,
              total_tokens: 5350,
              estimated_cost_usd: 0.0315,
            },
          },
        },
        derived_kpis: {
          pages_kept_ratio: 1,
          seconds_per_selected_page: 6.45,
          cost_per_selected_page_usd: 0.01575,
          cost_per_extracted_triplet_usd: 0.0315,
        },
      }),
    });
  });

  await page.goto("/");

  await expect(page.getByText("Diagnostic Knowledge Graph Extraction")).toBeVisible();
  await page.locator("#manual-select").selectOption("mock-manual.pdf");
  await page.locator("#upload-form").evaluate((form) => form.dispatchEvent(new Event("submit", { bubbles: true, cancelable: true })));

  await expect(page.locator("#cp-approve-btn")).toBeVisible();
  await page.getByRole("button", { name: /Approve & Extract/i }).click();

  await expect(page.locator("#ontology-screen")).toBeVisible();
  await expect(page.locator("#ontology-guidance")).toContainText("Fill in the 1 required field");
  await expect(page.locator("#ontology-fields")).toContainText("brand");

  await page.getByRole("button", { name: "Accept" }).first().click();
  await page.getByRole("button", { name: "Reject" }).nth(1).click();
  await page.getByRole("button", { name: /Apply Accepted Suggestions/i }).click();
  await expect(page.locator("#ontology-status")).toContainText("relation(s) applied");

  await page.locator('[data-ontology-field="Asset::ASSET-001::brand"]').fill("ABB");
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: /Apply & Continue/i }).click();

  await expect(page.locator("#main-layout")).toBeVisible();
  await expect(page.locator("#save-btn")).toBeVisible();
  await page.getByRole("button", { name: /Save & Next/i }).click();

  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("mock_export.json");

  await expect(page.locator("#summary")).toBeVisible();
  await expect(page.locator("#summary-text")).toContainText("1 triplet(s) validated");
  await expect(page.locator("#summary-kpis")).toContainText("Estimated Cost");
  await expect(page.locator("#summary-kpis")).toContainText("Model Cost Breakdown");
});
}
