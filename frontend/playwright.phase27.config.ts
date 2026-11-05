import { defineConfig, devices } from "@playwright/test";

/**
 * Phase 27 observability dashboard suite (committed on the
 * Phase 26 branch). Deliberately separate from the Phase 23
 * and Phase 25 suites, so no suite can disturb another.
 *
 * Prerequisites before running:
 *   1. Backend API running on http://127.0.0.1:8000 (FastAPI,
 *      migration 20261104_0022 applied, observability seeded).
 *   2. Production frontend build present (`npm run build`).
 * Kill any manually started `next start` on port 3000 first:
 * reuseExistingServer silently reuses a stale server and
 * masks fixes (Phase 23 lesson).
 */
export default defineConfig({
  testDir: "./e2e/phase27",
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
      use: { ...devices["Pixel 5"] },
    },
  ],
});
