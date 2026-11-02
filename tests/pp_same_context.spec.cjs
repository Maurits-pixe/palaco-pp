"use strict";

// Explicitly destructive: irreversibly selects and revokes on a disposable local demo consumer.
const fs = require("node:fs");
const { test, expect } = require("@playwright/test");
const { runPPBrowserAcceptance } = require("../browser_acceptance");

const statePath = process.env.PP_TEST_STORAGE_STATE;
const baseURL = process.env.PP_BASE_URL || "http://127.0.0.1:8765";
const parsed = new URL(baseURL);
if (parsed.protocol !== "http:" || parsed.hostname !== "127.0.0.1" ||
    parsed.username || parsed.password || parsed.pathname !== "/" ||
    parsed.search || parsed.hash) {
  throw new Error("PP acceptance must target local http://127.0.0.1:<port>/ only");
}

test.use({
  // No implicit authenticated context; the test is skipped without explicit opt-in.
  storageState: statePath || { cookies: [], origins: [] },
});

test("P.P. selection, reload, revocation and 409 in one context", async ({ page }) => {
  test.skip(process.env.PP_DESTRUCTIVE_BROWSER_ACCEPTANCE !== "YES",
    "Only run on an explicitly approved disposable consumer");
  test.skip(!statePath || !fs.existsSync(statePath), "Approved storageState file missing");

  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  const response = await page.request.get(new URL("/api/auth/me", baseURL).toString());
  expect(response.ok(), "Local demo account must be logged in").toBeTruthy();
  const account = await response.json();
  expect(account.authenticated, "Only an authenticated demo account may run").toBe(true);

  const result = await runPPBrowserAcceptance(page);
  expect(result.localAcceptance).toBe("GO");
  expect(result.productionReadiness).toBe("HOLD");
  test.info().annotations.push({
    type: "pp-acceptance",
    description: "Same page/context, destructive local test only; production HOLD",
  });
});
