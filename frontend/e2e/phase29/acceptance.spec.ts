/**
 * Phase 29 acceptance dashboard specs.
 *
 * Prerequisites (same pattern as the Phase 23/25–27 suites):
 *   1. Backend API running on http://127.0.0.1:8000 with the
 *      Phase 29 migration applied and the acceptance run committed.
 *   2. Production frontend build present (`npm run build`).
 * Kill any manually started `next start` on port 3000 first:
 * the config's reuseExistingServer silently reuses a stale
 * server and masks fixes (Phase 23 lesson, recorded in
 * docs/phase-23/ux_audit.md).
 */
import { expect, test } from "@playwright/test";

test("acceptance page shows run, verdict and counts", async ({ page }) => {
  await page.goto("/admin/acceptance");
  await expect(
    page.getByRole("heading", { name: "Acceptance", exact: true }),
  ).toBeVisible();
  // The committed run id is the Phase 29 run label.
  await expect(
    page.getByText("phase29-acceptance-2026-11-05").first(),
  ).toBeVisible();
  // Verdict is PARTIALLY COMPLETE: human sign-off is pending —
  // shown, not hidden. (The HBL chain is no longer blocked: the
  // batch flipped G1 to MET and the blocker run resolved D-05.)
  await expect(page.getByText("PARTIALLY COMPLETE").first()).toBeVisible();
  // Scenario counts (blocker run): 14 total, 12 pass, 0 fail,
  // 0 blocked, 2 not evaluable.
  await expect(page.getByText("12 pass").first()).toBeVisible();
  await expect(page.getByText("0 fail").first()).toBeVisible();
  // Recomputation counts (blocker run): 15 matched, 0 mismatched.
  // The former 14/1 split (expected HBL drift vs the Phase 24
  // baseline) was resolved 2026-11-05 by the D-05/drift baseline
  // updates — a mismatched count now means a real regression.
  await expect(page.getByText("15 matched").first()).toBeVisible();
  await expect(page.getByText("0 mismatched").first()).toBeVisible();
});

test("scenario table shows HBL full chain passing and no failures", async ({
  page,
}) => {
  await page.goto("/admin/acceptance");
  await expect(
    page.getByRole("heading", { name: "Acceptance", exact: true }),
  ).toBeVisible();
  // The HBL chain is a full passing chain since the batch (G1 MET);
  // the retired chain_hbl_partial key must not reappear.
  await expect(page.getByText("chain_hbl_full").first()).toBeVisible();
  await expect(page.getByText("0 blocked").first()).toBeVisible();
  // The three other full chains pass.
  await expect(page.getByText("chain_hubc_full").first()).toBeVisible();
  await expect(page.getByText("chain_ogdc_full").first()).toBeVisible();
  await expect(page.getByText("chain_nml_full").first()).toBeVisible();
});

test("defect register shows no critical/high defects", async ({ page }) => {
  await page.goto("/admin/acceptance");
  await expect(
    page.getByRole("heading", { name: "Acceptance", exact: true }),
  ).toBeVisible();
  // Defect counts: 0 critical, 0 high — the gate's G2 item.
  await expect(page.getByText("0 critical").first()).toBeVisible();
  await expect(page.getByText("0 high").first()).toBeVisible();
  // D-05 was resolved by the clean recovery #7 re-derivation.
  await expect(page.getByText("D-05").first()).toBeVisible();
});
