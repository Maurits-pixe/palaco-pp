"use strict";
const { defineConfig, devices } = require("@playwright/test");

// Deliberately local, opt-in, non-production acceptance.
module.exports = defineConfig({
  testDir: "./tests",
  testMatch: ["**/pp_same_context.spec.cjs", "**/pp_ephemeral_ci.spec.cjs"],
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60000,
  expect: { timeout: 10000 },
  reporter: [["list"], ["html", { outputFolder: "playwright-report", open: "never" }]],
  use: {
    ...devices["Desktop Chrome"],
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
});
