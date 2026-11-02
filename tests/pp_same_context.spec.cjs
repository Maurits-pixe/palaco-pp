"use strict";

// Run ONLY with a specifically approved, disposable OFFERED test consumer.
// This test permanently selects and revokes its P.P. number.
const { test, expect } = require("@playwright/test");
const { runPPBrowserAcceptance } = require("../browser_acceptance");

test("P.P. same-context selection, reload, revoke, reselection denial", async ({ page }) => {
  test.skip(process.env.PP_DESTRUCTIVE_BROWSER_ACCEPTANCE !== "YES", "Explicit opt-in required");
  test.skip(!process.env.PP_TEST_STORAGE_STATE, "Approved test account storage state required");
  const baseURL = process.env.PP_BASE_URL || "http://127.0.0.1:8765";
  const url = new URL(baseURL);
  expect(url.hostname, "Only the local demo is permitted").toBe("127.0.0.1");
  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  const result = await runPPBrowserAcceptance(page);
  expect(result.localAcceptance).toBe("GO");
  expect(result.productionReadiness).toBe("HOLD");
  test.info().annotations.push({ type: "pp-acceptance", description: "same browser page/context; local demo only" });
});
