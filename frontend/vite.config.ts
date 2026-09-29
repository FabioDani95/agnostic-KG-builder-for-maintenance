/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The API runs on 8765 (scripts/ui.py); in dev mode Vite forwards /api to it.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://127.0.0.1:8765" } },
  build: { chunkSizeWarningLimit: 1500 },
  test: { environment: "jsdom", include: ["tests/**/*.test.{ts,tsx}"] },
});
