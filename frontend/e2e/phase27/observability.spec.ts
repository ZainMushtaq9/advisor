/**
 * Phase 27 observability dashboard specs.
 *
 * Prerequisites (same pattern as the Phase 23/25/26 suites):
 *   1. Backend API running on http://127.0.0.1:8000 with the
 *      Phase 27 migration applied and the observability seeded.
 *   2. Production frontend build present (`npm run build`).
 * Kill any manually started `next start` on port 3000 first:
 * the config's reuseExistingServer silently reuses a stale
 * server and masks fixes (Phase 23 lesson, recorded in
 * docs/phase-23/ux_audit.md).
 */
import { expect, test } from "@playwright/test";

test("observability page shows run, SLOs, stale source and incidents", async ({
  page,
}) => {
  await page.goto("/admin/observability");
  await expect(
    page.getByRole("heading", { name: "Observability", exact: true }),
  ).toBeVisible();
  // The seed run id is the Phase 27 run label.
  await expect(
    page.getByText("phase27-observability-2026-11-05").first(),
  ).toBeVisible();
  // SLO counts: 14 total, 10 met, 4 unmet — unmet is a finding, not hidden.
  await expect(page.getByText("SLOs: 14 total").first()).toBeVisible();
  await expect(page.getByText("4 unmet").first()).toBeVisible();
  // The unmet SLOs are named, with reasons.
  await expect(
    page.getByText("price_coverage_latest_day").first(),
  ).toBeVisible();
  await expect(
    page.getByText("previous_close_completeness").first(),
  ).toBeVisible();
  // Only market_prices is stale; the rest are fresh or unknown-free.
  await expect(page.getByText("market_prices").first()).toBeVisible();
  await expect(page.getByText("stale", { exact: true }).first()).toBeVisible();
  // Open exceptions include the HBL pending item and paused jobs.
  await expect(page.getByText("known_hbl_pending").first()).toBeVisible();
  // Historical incidents are resolved, not rewritten as successes.
  await expect(
    page.getByText("incident_vm_replacement_6").first(),
  ).toBeVisible();
  await expect(page.getByText("resolved", { exact: true }).first()).toBeVisible();
});

test("admin page links to observability", async ({ page }) => {
  await page.goto("/admin");
  await expect(
    page.getByText("Observability", { exact: true }).first(),
  ).toBeVisible();
});

test("home navigation includes observability", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("link", { name: "Observability" }).first(),
  ).toBeVisible();
});
