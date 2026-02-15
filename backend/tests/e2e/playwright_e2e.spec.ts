/**
 * Control Tower – Playwright End-to-End Tests
 *
 * Run: npx playwright test backend/tests/e2e/
 *
 * Requires:
 *   - Backend running on localhost:8000
 *   - Frontend running on localhost:3000
 */

import { test, expect } from "@playwright/test";

const BASE = "http://localhost:3000";

test.describe("Control Tower E2E", () => {
  test("Dashboard loads with all stat cards", async ({ page }) => {
    await page.goto(`${BASE}/dashboard`);
    await expect(page.locator("h1")).toContainText("Control Tower Dashboard");
    // 8 stat cards
    await expect(page.locator('[class*="rounded-xl border bg-white p-6"]').first()).toBeVisible();
    // Compliance frameworks section
    await expect(page.getByText("SR 11-7")).toBeVisible();
    await expect(page.getByText("NIST 600-1")).toBeVisible();
    await expect(page.getByText("OWASP LLM")).toBeVisible();
  });

  test("Models page renders inventory table", async ({ page }) => {
    await page.goto(`${BASE}/models`);
    await expect(page.locator("h1")).toContainText("Model Inventory");
    await expect(page.getByPlaceholder("Search models...")).toBeVisible();
    // Table headers
    await expect(page.getByText("Risk Tier")).toBeVisible();
    await expect(page.getByText("Deployment")).toBeVisible();
  });

  test("Tools page shows attestation stats", async ({ page }) => {
    await page.goto(`${BASE}/tools`);
    await expect(page.locator("h1")).toContainText("Tools & EUC Inventory");
    await expect(page.getByText("Total Tools")).toBeVisible();
    await expect(page.getByText("Attested")).toBeVisible();
    await expect(page.getByText("Overdue")).toBeVisible();
  });

  test("Use Cases page shows pipeline funnel", async ({ page }) => {
    await page.goto(`${BASE}/use-cases`);
    await expect(page.locator("h1")).toContainText("GenAI Use Cases");
    await expect(page.getByText("Certification Pipeline")).toBeVisible();
    // Architecture flags visible on cards
    await expect(page.getByText("RAG").first()).toBeVisible();
  });

  test("Evaluations page shows pass rates", async ({ page }) => {
    await page.goto(`${BASE}/evaluations`);
    await expect(page.locator("h1")).toContainText("Evaluations");
    await expect(page.getByText("Avg Pass Rate")).toBeVisible();
    await expect(page.getByText("Total Failures")).toBeVisible();
  });

  test("Findings page shows severity breakdown", async ({ page }) => {
    await page.goto(`${BASE}/findings`);
    await expect(page.locator("h1")).toContainText("Findings Register");
    await expect(page.getByText("Open Critical")).toBeVisible();
  });

  test("Certifications page shows pack structure", async ({ page }) => {
    await page.goto(`${BASE}/certifications`);
    await expect(page.locator("h1")).toContainText("Certification Packs");
    await expect(page.getByText("NIST AI 600-1")).toBeVisible();
    await expect(page.getByText("OWASP LLM Top 10")).toBeVisible();
    await expect(page.getByText("ISO/IEC 42001")).toBeVisible();
  });

  test("Compliance Matrix page shows all frameworks", async ({ page }) => {
    await page.goto(`${BASE}/compliance`);
    await expect(page.locator("h1")).toContainText("Compliance Control Matrix");
    await expect(page.getByText("OWASP LLM Top 10 (2025)")).toBeVisible();
    await expect(page.getByText("OWASP Agentic Top 10 (2026)")).toBeVisible();
    await expect(page.getByText("NIST AI 600-1 GenAI Profile")).toBeVisible();
    await expect(page.getByText("SR 11-7")).toBeVisible();
    await expect(page.getByText("FINRA GenAI Control Expectations")).toBeVisible();
    // Specific control verification
    await expect(page.getByText("LLM01")).toBeVisible();
    await expect(page.getByText("ASI01")).toBeVisible();
  });

  test("Settings page shows system status", async ({ page }) => {
    await page.goto(`${BASE}/settings`);
    await expect(page.locator("h1")).toContainText("Settings");
    await expect(page.getByText("Policy Engine (OPA)")).toBeVisible();
    await expect(page.getByText("Evidence Store")).toBeVisible();
    await expect(page.getByText("SHA-256")).toBeVisible();
  });

  test("Sidebar navigation works for all pages", async ({ page }) => {
    await page.goto(`${BASE}/dashboard`);
    // Navigate through each sidebar item
    const navItems = [
      { text: "Models", url: "/models" },
      { text: "Tools & EUCs", url: "/tools" },
      { text: "GenAI Use Cases", url: "/use-cases" },
      { text: "Evaluations", url: "/evaluations" },
      { text: "Findings", url: "/findings" },
      { text: "Certifications", url: "/certifications" },
      { text: "Compliance Matrix", url: "/compliance" },
    ];
    for (const nav of navItems) {
      await page.getByRole("link", { name: nav.text }).click();
      await expect(page).toHaveURL(new RegExp(nav.url));
    }
  });
});
