"use strict";

// Non-destructive to P.P. registrations. Mutates only browser-local draft notes.
// Run on an explicitly approved test profile, with a running local PALACO server.
// Pass an existing Playwright Page to avoid changing browser storage affinity.
async function runOfflineAtelierAcceptance(page) {
  const results = [];
  const check = (value, label) => {
    if (!value) throw new Error("OFFLINE_ATELIER_FAIL: " + label);
    results.push(label);
  };
  const context = page.context();
  const tag = "qa-" + Date.now();
  const title = "Hersteltest " + tag;
  const body = "Lokaal concept; geen P.P.-nummer of identiteit.";
  const url = new URL("/offline.html", page.url()).toString();
  let switchedOffline = false;
  try {
    await page.goto(url);
    await page.locator("#storage-state").getByText("Lokale conceptopslag beschikbaar").waitFor();
    check(await page.locator("#connection-state").isVisible(), "status indicators visible");
    await page.locator("#title").fill(title);
    await page.locator("#body").fill(body);
    await page.getByRole("button", { name: "Bewaar op dit apparaat" }).click();
    await page.getByText(title, { exact: true }).waitFor();
    check(await page.getByText(body, { exact: true }).isVisible(), "draft committed");

    await page.reload();
    await page.getByText(title, { exact: true }).waitFor();
    check(true, "draft survives reload");

    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Exporteren als JSON" }).click();
    const download = await downloadPromise;
    const buffer = await require("node:fs/promises").readFile(await download.path());
    const exported = JSON.parse(buffer.toString("utf8"));
    check(exported.schema === "palaco.pp.offline-drafts.v2"
      && exported.integrity?.algorithm === "SHA-256", "v2 integrity-bearing export");
    const record = exported.drafts.find(d => d.title === title);
    check(Boolean(record) && record.body === body, "export includes draft");

    // Invalid checksum must fail closed; no draft may be added.
    const tampered = structuredClone(exported);
    tampered.drafts.push({
      id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      title: "INJECTED-" + tag, body: "not trusted",
      updatedAt: new Date().toISOString(),
    });
    await page.locator("#import").setInputFiles({
      name: "tampered.json", mimeType: "application/json",
      buffer: Buffer.from(JSON.stringify(tampered)),
    });
    await page.getByText(/Integriteitscontrole mislukt/).waitFor();
    check(await page.getByText("INJECTED-" + tag, { exact: true }).count() === 0,
      "tampered import rejected");

    // Full network isolation after shell cache warm-up.
    await context.setOffline(true);
    switchedOffline = true;
    await page.reload();
    await page.getByText(title, { exact: true }).waitFor();
    check((await page.locator("#connection-state").innerText()).includes("Geen netwerksignaal"),
      "offline signal visible");
    check(await page.getByText(body, { exact: true }).isVisible(),
      "draft survives offline reload");
    await page.locator("#title").fill("Offline " + tag);
    await page.locator("#body").fill("Tweede concept zonder netwerk.");
    await page.getByRole("button", { name: "Bewaar op dit apparaat" }).click();
    await page.getByText("Offline " + tag, { exact: true }).waitFor();
    check(true, "offline draft commit");

    return {
      checkedAt: new Date().toISOString(),
      tests: results,
      outcome: "LOCAL_BROWSER_ACCEPTANCE_GO",
      production: "HOLD",
      note: "Test data remains in this browser profile. No official P.P. actions executed.",
    };
  } finally {
    if (switchedOffline) await context.setOffline(false);
  }
}
module.exports = { runOfflineAtelierAcceptance };
