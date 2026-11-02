"use strict";

// Run only on an explicitly approved demo consumer: this revokes its final choice.
async function runPPBrowserAcceptance(page) {
  function check(condition, message) {
    if (!condition) throw new Error(`Browser acceptance failed: ${message}`);
  }

  async function readState() {
    return page.evaluate(async () => {
      const response = await fetch("/api/pp/me");
      if (!response.ok) throw new Error(`State request failed: ${response.status}`);
      return response.json();
    });
  }

  async function readHistory() {
    return page.evaluate(async () => {
      const response = await fetch("/api/pp/history");
      if (!response.ok) throw new Error(`History request failed: ${response.status}`);
      return response.json();
    });
  }

  async function snapshot() {
    return page.locator(".number-option").evaluateAll((labels) =>
      labels.map((label) => ({
        id: label.querySelector("input").value,
        number: label.querySelector(".number-value").textContent.replaceAll(" ", ""),
        color: label.className,
        background: getComputedStyle(label.querySelector(".number-face")).backgroundColor,
      }))
    );
  }

  await page.reload();
  await page.waitForFunction(() =>
    !document.getElementById("selection-panel").hidden
      || !document.getElementById("result-panel").hidden
      || document.getElementById("notice").classList.contains("error"));
  const initial = await readState();
  check(initial.status === "OFFERED", "requires an unselected demo consumer");
  await page.getByTestId("pp-option-10").waitFor({ state: "visible" });
  const before = await snapshot();
  check(before.length === 10, "expected exactly ten options");
  check(new Set(before.map((o) => o.number)).size === 10, "numbers must be unique");
  check(before.every((o) => /^[1-9][0-9]{9}$/.test(o.number)), "invalid number format");
  for (const color of ["blue", "red", "green", "yellow"]) {
    check(before.some((o) => o.color.includes(`color-${color}`)), `missing ${color}`);
  }
  check(new Set(before.map((o) => o.background)).size === 4, "expected four rendered colors");
  const offeredHistory = (await readHistory()).events;
  check(offeredHistory.length === 10
    && offeredHistory.every((event) => event.event === "OPTION_OFFERED"),
  "the engine history must record all ten offers");
  check(offeredHistory.every((event) =>
    before.some((option) => option.id === event.detail.optionId
      && option.number === event.detail.ppNumber
      && event.detail.color === (option.color.match(/(?:^|\\s)color-(blue|red|green|yellow)(?:\\s|$)/) || [])[1])),
  "offer history does not match the displayed batch");
  await page.reload();
  await page.getByTestId("pp-option-10").waitFor({ state: "visible" });
  check(JSON.stringify(before) === JSON.stringify(await snapshot()), "batch changed after reload");

  const chosen = before[2];
  await page.getByTestId("pp-option-3").locator('input[type="radio"]').check();
  check(await page.getByTestId("pp-option-3").getByRole("radio").isChecked(), "radio not selected");
  await page.getByRole("button", { name: "Bevestig je keuze", exact: true }).click();
  await page.getByRole("dialog", { name: "Maak het van jou.", exact: true }).waitFor();
  check((await page.locator("#dialog-number").textContent()).replaceAll(" ", "") === chosen.number,
    "confirmation shows wrong number");
  await page.getByRole("button", { name: "Definitief kiezen", exact: true }).click();
  await page.locator("#result-panel").waitFor({ state: "visible" });
  const active = await readState();
  check(active.status === "ACTIVE" && active.ppNumberId === chosen.id
    && active.ppNumber === chosen.number && active.consumerId === initial.consumerId,
  "selection not registered for the original consumer");
  const selectedHistory = (await readHistory()).events;
  check(selectedHistory.length === 11
    && selectedHistory[10].event === "NUMBER_SELECTED"
    && selectedHistory[10].detail.ppNumber === chosen.number,
  "selection missing from the engine history");

  await page.reload();
  await page.locator("#result-panel").waitFor({ state: "visible" });
  check(JSON.stringify(active) === JSON.stringify(await readState()), "selection changed after reload");
  check((await page.locator("#result-number").textContent()).replaceAll(" ", "") === chosen.number,
    "persisted number not displayed");
  check(await page.locator("#selection-panel").isHidden(), "options still available after selection");

  await page.getByRole("button", { name: "Nummer intrekken", exact: true }).click();
  await page.getByRole("dialog", { name: "Nummer intrekken?", exact: true }).waitFor();
  await page.getByRole("button", { name: "Definitief intrekken", exact: true }).click();
  await page.waitForFunction(() =>
    document.getElementById("result-badge").textContent === "INGETROKKEN"
      && !document.getElementById("confirm-dialog").open);
  const revoked = await readState();
  check(revoked.status === "REVOKED" && revoked.revokedAt
    && revoked.consumerId === initial.consumerId && revoked.ppNumberId === chosen.id,
  "revocation not persisted for original consumer");
  const revokedHistory = (await readHistory()).events;
  check(revokedHistory.length === 12
    && revokedHistory[11].event === "NUMBER_REVOKED"
    && revokedHistory[11].detail.ppNumber === chosen.number,
  "revocation missing from the engine history");
  await page.reload();
  await page.locator("#result-panel").waitFor({ state: "visible" });
  check(JSON.stringify(revoked) === JSON.stringify(await readState()), "revocation changed after reload");
  check(await page.locator("#revoke").isHidden(), "revocation control still visible");
  check(await page.locator("#selection-panel").isHidden(), "selection UI reopened after revocation");

  const rejected = await page.evaluate(async (optionId) => {
    const results = [];
    for (const [path, body] of [
      ["/api/pp/select", { optionId }],
      ["/api/pp/options", {}],
    ]) {
      const response = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      results.push({ path, status: response.status, body: await response.json() });
    }
    return results;
  }, before[3].id);
  check(rejected.every((r) => r.status === 409 && r.body.error === "PP_ALREADY_SELECTED"),
    "second selection or replacement batch was not blocked");
  check(JSON.stringify(revoked) === JSON.stringify(await readState()), "rejected requests changed registration");
  return {
    checkedAt: new Date().toISOString(),
    samePageAndContext: true,
    tenUniqueNumbers: true,
    fourRenderedColors: true,
    batchStableAfterReload: true,
    selectionPersistedAfterReload: true,
    revocationPersistedAfterReload: true,
    reselectionAndNewBatchBlocked: rejected,
    localAcceptance: "GO",
    productionReadiness: "HOLD",
  };
}

if (typeof module !== "undefined") module.exports = { runPPBrowserAcceptance };
