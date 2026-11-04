/**
 * Phase 25 operations dashboard specs.
 *
 * Prerequisites (same pattern as the Phase 23 suite):
 *   1. Backend API running on http://127.0.0.1:8000 with the
 *      Phase 25 migration applied and the registry seeded.
 *   2. Production frontend build present (`npm run build`).
 * Kill any manually started `next start` on port 3000 first:
 * the config's reuseExistingServer silently reuses a stale
 * server and masks fixes (Phase 23 lesson, recorded in
 * docs/phase-23/ux_audit.md).
 */
import { expect, test } from "@playwright/test";

test("jobs page shows definitions and paused collection jobs", async ({ page }) => {
  await page.goto("/admin/jobs");
  await expect(
    page.getByRole("heading", { name: "Jobs" })
  ).toBeVisible();
  // The registry seeds 8 definitions, 3 of them paused.
  await expect(page.getByText("market_post_close").first()).toBeVisible();
  await expect(page.getByText("system_health").first()).toBeVisible();
  await expect(
    page.getByText(/Terms evidence pending/)
  ).toBeVisible();
  // Runs table: the live seed run produced succeeded runs.
  await expect(page.getByText("succeeded").first()).toBeVisible();
});

test("admin page links to jobs", async ({ page }) => {
  await page.goto("/admin");
  await expect(page.getByText("Jobs / automation")).toBeVisible();
});

test("home navigation includes jobs", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("link", { name: "Jobs" }).first()).toBeVisible();
});
