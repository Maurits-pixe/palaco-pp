"use strict";

// Start the PALACO local server separately. No account credentials are needed.
const { chromium } = require("playwright");
const { runOfflineAtelierAcceptance } = require("./offline_browser_acceptance");

async function main() {
  const base = process.env.PALACO_TEST_ORIGIN || "http://127.0.0.1:8765";
  const url = new URL(base);
  if (url.protocol !== "http:" || url.hostname !== "127.0.0.1") {
    throw Error("Only the local PALACO loopback origin is permitted.");
  }
  const response = await fetch(new URL("/offline.html", url), { signal: AbortSignal.timeout(5000) });
  if (!response.ok) throw Error("Local server not ready: HTTP " + response.status);

  const browser = await chromium.launch({ headless: true });
  try {
    const context = await browser.newContext({ acceptDownloads: true, serviceWorkers: "allow" });
    try {
      const page = await context.newPage();
      await page.goto(url.toString());
      const report = await runOfflineAtelierAcceptance(page);
      console.log(JSON.stringify(report, null, 2));
    } finally {
      await context.close();
    }
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error("OFFLINE_ATELIER_NOT_ACCEPTED:", error.message);
  process.exitCode = 1;
});
