/** @type {import('@playwright/test').PlaywrightTestConfig} */
const port = process.env.PORT || "8000";
const baseURL = `http://127.0.0.1:${port}`;

module.exports = {
  testDir: "./tests",
  timeout: 120000,
  use: {
    baseURL,
    headless: true,
  },
  webServer: {
    command: "node scripts/dev_server.mjs",
    url: `${baseURL}/api/health`,
    reuseExistingServer: false,
    timeout: 120000,
    env: {
      // Keep e2e exports away from the real output/ bundles (see ontology_export_store)
      // and run persistence away from data/runs (see backend/runstore).
      KG_OUTPUT_DIR: "output_e2e",
      KG_RUNS_DIR: "runs_e2e",
      // No tokens in e2e: the LLM gateway serves deterministic mock replies.
      KG_LLM_MODE: "mock",
      // The real-backend spec loads this small committed fixture manual.
      KG_MANUALS_DIR: "tests/fixtures/manuals",
      KG_RELOAD: "0",
      PORT: port,
    },
  },
};
