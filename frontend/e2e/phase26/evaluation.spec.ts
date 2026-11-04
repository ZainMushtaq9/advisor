/**
 * Phase 26 evaluation dashboard specs.
 *
 * Prerequisites (same pattern as the Phase 23/25 suites):
 *   1. Backend API running on http://127.0.0.1:8000 with the
 *      Phase 26 migration applied and the evaluation seeded.
 *   2. Production frontend build present (`npm run build`).
 * Kill any manually started `next start` on port 3000 first:
 * the config's reuseExistingServer silently reuses a stale
 * server and masks fixes (Phase 23 lesson, recorded in
 * docs/phase-23/ux_audit.md).
 */
import { expect, test } from "@playwright/test";

test("evaluation page shows run, gates and golden cases", async ({ page }) => {
  await page.goto("/admin/evaluation");
  await expect(
    page.getByRole("heading", { name: "Evaluation", exact: true }),
  ).toBeVisible();
  // The seed run id is the Phase 26 run label.
  await expect(
    page.getByText("phase26-evaluation-2026-11-05").first(),
  ).toBeVisible();
  // No model is promoted and no gate is met: both are honest zeros.
  await expect(page.getByText("Promoted models: 0").first()).toBeVisible();
  await expect(page.getByText("out_of_sample_evidence").first()).toBeVisible();
  await expect(page.getByText("NOT_MET").first()).toBeVisible();
  // Golden suite: the citation case is present and passed.
  await expect(page.getByText("golden_qa_citation_rule").first()).toBeVisible();
  // NOT_EVALUABLE metrics carry no invented value.
  await expect(
    page.getByText("not evaluable — no value").first(),
  ).toBeVisible();
});

test("admin page links to evaluation", async ({ page }) => {
  await page.goto("/admin");
  await expect(
    page.getByText("Evaluation", { exact: true }).first(),
  ).toBeVisible();
});

test("home navigation includes evaluation", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("link", { name: "Evaluation" }).first(),
  ).toBeVisible();
});
