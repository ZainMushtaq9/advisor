import { test, expect } from "@playwright/test";

/**
 * Phase 23 acceptance suite. Every assertion checks a real API-backed value
 * or an honest empty/error state — never a placeholder. The backend must be
 * running on :8000 with the recorded Phase 22 state (470 companies, 444
 * prices on 2026-11-03, 89 alerts, 22 DRAFT reports).
 */

test("home shows live registry figures and full navigation", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "PSX Intelligence AI" })).toBeVisible();
  // Real registry figures from /registry/statistics.
  await expect(page.getByText("470", { exact: true }).first()).toBeVisible();
  // No foundation-shell banner may remain on a product page.
  await expect(page.getByText("Foundation shell")).toHaveCount(0);
  // Primary navigation covers the Phase 23 IA.
  for (const label of ["Dashboard", "Companies", "Market", "Securities", "News", "Fundamentals", "Valuation", "Macro", "Technical", "Forecasts", "Risk", "Portfolio", "Screener", "Alerts", "Reports", "Research", "Admin"]) {
    // exact name match: later phases added /admin/evaluation to the
    // nav, and a substring match for "Valuation" resolves to both
    // /valuation and /admin/evaluation (strict-mode violation).
    await expect(page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: label, exact: true })).toBeVisible();
  }
  // Skip link exists for keyboard users.
  await expect(page.getByRole("link", { name: "Skip to main content" })).toBeAttached();
});

test("companies search finds HUBC and detail fundamentals assess", async ({ page }) => {
  await page.goto("/companies");
  await page.getByLabel("Search companies by legal name").fill("Hub Power");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByRole("link", { name: "The Hub Power Company Limited" })).toBeVisible();
  await page.getByRole("link", { name: "The Hub Power Company Limited" }).click();
  await expect(page.getByRole("tab", { name: "Overview" })).toBeVisible();
  // Detail links use the registry id (759 for HUBC); the ticker resolves inside.
  await expect(page).toHaveURL(/\/companies\/759$/);
  await page.getByRole("tab", { name: "Fundamentals" }).click();
  // Assessed live: gross margin row with the Phase 8 value prefix.
  await expect(page.getByRole("cell", { name: "gross_margin", exact: true })).toBeVisible();
  await expect(page.getByText("0.4174", { exact: false }).first()).toBeVisible();
});

test("HBL detail shows computed bank-adapted fundamentals", async ({ page }) => {
  // HBL re-run batch: HBL fundamentals are no longer pending (36
  // bank-adapted metric rows, 20 computed). Gross margin stays
  // insufficient for a bank (no cost-of-goods analogue) while the
  // bank operating margin computes; the old "pending" premise
  // retired with the batch.
  await page.goto("/companies/HBL");
  await page.getByRole("tab", { name: "Fundamentals" }).click();
  await expect(page.getByRole("cell", { name: "operating_margin", exact: true })).toBeVisible();
  // fmtNum renders the stored decimal verbatim (0.4353668…), so the
  // assertion uses the substring prefix, as the HUBC test does.
  await expect(page.getByText("0.4353", { exact: false }).first()).toBeVisible();
});

test("market prices render and ticker search narrows to one row", async ({ page }) => {
  await page.goto("/market");
  await expect(page.getByRole("table", { name: "Daily prices for 2026-11-03" })).toBeVisible();
  await page.getByLabel("Search prices by ticker").fill("HUBC");
  await page.getByRole("button", { name: "Search" }).click();
  await expect(page.getByRole("link", { name: "HUBC", exact: true })).toBeVisible();
  await expect(page.getByText("197.24")).toBeVisible();
});

test("screener shows liquid_leaders matches and the honesty disclaimer", async ({ page }) => {
  await page.goto("/screener");
  await expect(page.getByText(/filter results, not investment opportunities/)).toBeVisible();
  await expect(page.getByText("194", { exact: true }).first()).toBeVisible();
});

test("alerts list renders with in-app-only disclaimer", async ({ page }) => {
  await page.goto("/alerts");
  await expect(page.getByText(/in-app only/)).toBeVisible();
  await expect(page.getByRole("table").first()).toBeVisible();
});

test("reports list renders DRAFT reports and detail shows sections", async ({ page }) => {
  await page.goto("/reports");
  await expect(page.getByText("DRAFT", { exact: true }).first()).toBeVisible();
  await page.getByRole("link", { name: /The Hub Power Company Limited/ }).first().click();
  await expect(page.getByRole("heading", { name: "Executive summary" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Stored alerts" })).toBeVisible();
});

test("unknown ticker shows an honest error, not a guessed company", async ({ page }) => {
  await page.goto("/companies/ZZZZ");
  await expect(
    page.getByText(
      "This company could not be resolved in the registry. Check the ticker or registry id; nothing is shown rather than a guessed company.",
    ),
  ).toBeVisible();
  // No tab panels render for an unresolvable company — nothing to guess from.
  await expect(page.getByRole("tab")).toHaveCount(0);
});

test("keyboard navigation reaches search and tabs", async ({ page }) => {
  await page.goto("/companies");
  await page.keyboard.press("Tab");
  // Focus must land on a real control (skip link, nav link, or search).
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
  await page.getByLabel("Search companies by legal name").focus();
  await expect(page.getByLabel("Search companies by legal name")).toBeFocused();
  await page.goto("/companies/HUBC");
  await page.getByRole("tab", { name: "Valuation" }).focus();
  await expect(page.getByRole("tab", { name: "Valuation" })).toBeFocused();
});

test("forecasts page states abstention, never a forecast number", async ({ page }) => {
  await page.goto("/forecasts");
  await expect(page.getByText(/insufficient_inputs/)).toBeVisible();
  await expect(page.getByText(/No forecast figure appears/)).toBeVisible();
});

test("portfolio page is labelled SIMULATED and reconciles", async ({ page }) => {
  await page.goto("/portfolio");
  await expect(page.getByText(/SIMULATED/)).toBeVisible();
  await expect(page.getByText("ew_statements_3_balanced")).toBeVisible();
  await page.getByRole("button", { name: "ew_statements_3_balanced" }).click();
  await expect(page.getByText("999473.03", { exact: false }).first()).toBeVisible();
});
