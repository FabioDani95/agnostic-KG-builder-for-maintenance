/** @type {import('@playwright/test').PlaywrightTestConfig} */
module.exports = {
  testDir: "./tests",
  timeout: 120000,
  use: {
    baseURL: "http://127.0.0.1:8000",
    headless: true,
  },
  webServer: {
    command: "bash -lc 'source .venv/bin/activate && uvicorn backend.main:app --port 8000'",
    url: "http://127.0.0.1:8000",
    reuseExistingServer: true,
    timeout: 120000,
  },
};
