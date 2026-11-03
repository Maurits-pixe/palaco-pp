"use strict";
const { test, expect } = require("@playwright/test");
const { randomUUID } = require("node:crypto");
const { runPPBrowserAcceptance } = require("../browser_acceptance");

test("ephemeral local P.P. acceptance: select / reload / revoke / 409", async ({page}) => {
  const url = process.env.PP_BASE_URL || "http://127.0.0.1:8765/";
  const target = new URL(url);
  if (target.protocol !== "http:" || target.hostname !== "127.0.0.1" ||
      target.pathname !== "/" || target.search || target.hash) {
    throw new Error("Ephemeral acceptance refuses a non-local target");
  }
  if (process.env.PP_EPHEMERAL_CI !== "YES") test.skip(true, "Temporary CI-only fixture required");

  await page.goto(url, {waitUntil:"domcontentloaded"});
  // Only an empty, isolated CI database. Don't reuse cookies, profiles or sessions.
  const previous = await page.evaluate(async () => {
    const r = await fetch("/api/auth/me");
    return r.json();
  });
  // The app bootstrap creates an anonymous local consumer on first page load.
  expect(previous.consumerId).toEqual(expect.any(String));
  expect(previous.authenticated).toBe(false);
  const initialState = await page.evaluate(async () => {
    const r = await fetch("/api/pp/me");
    return { status: r.status, body: await r.json() };
  });
  // A fresh database must have no selected identity or existing offers.
  expect(initialState.status).toBe(401);

  const username = "ci_" + randomUUID().replaceAll("-","").slice(0,20);
  const password = randomUUID() + "_Pp-Local-Only!";
  const bootstrap = await page.evaluate(async ({username,password}) => {
    async function post(path, data) {
      const r = await fetch(path,{
        method:"POST",credentials:"same-origin",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify(data),
      });
      return {status:r.status,body:await r.json()};
    }
    const session = await post("/api/session",{});
    if (session.status !== 200) throw new Error("Ephemeral session initialization failed");
    const registration = await post("/api/auth/register",{username,password});
    if (registration.status !== 201) throw new Error("Ephemeral account registration failed");
    const options = await post("/api/pp/options",{});
    if (options.status !== 200) throw new Error("Ephemeral options creation failed");
    return {consumerId: registration.body.consumerId};
  }, {username,password});
  expect(bootstrap.consumerId).toBeTruthy();
  const result = await runPPBrowserAcceptance(page);
  expect(result.localAcceptance).toBe("GO");
  expect(result.productionReadiness).toBe("HOLD");
});
