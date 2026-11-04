import { defineConfig, devices } from "@playwright/test";

/**
 * Phase 23 product test suite (committed on the Phase 23 branch).
 * This is deliberately separate from the Phase 2 smoke config
 * (playwright.config.ts, untracked): different file, different spec dir,
 * so neither suite can disturb the other.
 *
 * Prerequisites before running:
 *   1. Backend API running on http://127.0.0.1:8000 (FastAPI).
 *   2. Production frontend build present (`npm run build`).
 * The webServer entry reuses an already-running `next start` on port 3000
 * when one exists, otherwise it starts one.
 */
export default defineConfig({
  testDir: "./e2e/phase23",
  timeout: 60_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run start -- --port 3000",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: true,
    timeout: 60_000,
  },
  projects: [
    {
      name: "desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile",
      use: { ...devices["Pixel 7"] },
    },
  ],
});
