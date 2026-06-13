/** @type {import('@playwright/test').PlaywrightTestConfig} */
const webServerCommand =
  process.platform === "win32"
    ? ".\\.venv\\Scripts\\python.exe -m uvicorn backend.main:app --port 8000"
    : "./.venv/bin/python3 -m uvicorn backend.main:app --port 8000";

module.exports = {
  testDir: "./tests",
  timeout: 120000,
  use: {
    baseURL: "http://127.0.0.1:8000",
    headless: true,
  },
  webServer: {
    command: webServerCommand,
    url: "http://127.0.0.1:8000",
    reuseExistingServer: true,
    timeout: 120000,
    env: {
      // Keep e2e exports away from the real output/ bundles (see ontology_export_store).
      KG_OUTPUT_DIR: "output_e2e",
    },
  },
};
