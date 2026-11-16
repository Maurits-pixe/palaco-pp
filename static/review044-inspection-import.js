"use strict";
// Review 044: browser-only preview. Strict verdict requires offline Python CLI.
// No API calls, no storage, no authorization actions.
(() => {
  const $ = (id) => document.getElementById(id);
  const registry = $("admin-review044-inspection-import-registry");
  const inspection = $("admin-review044-inspection-import-report");
  const button = $("admin-review044-inspection-import-check");
  const output = $("admin-review044-inspection-import-result");
  if (!registry || !inspection || !button || !output) return;
  let generation = 0;
  const reset = () => {
    generation += 1;
    output.textContent = "NOT EXECUTED / Nog geen indicatieve browservergelijking. HOLD / DENY.";
  };
  registry.addEventListener("change", reset);
  inspection.addEventListener("change", reset);
  button.addEventListener("click", async () => {
    const current = ++generation;
    const reg = registry.files?.[0];
    const rep = inspection.files?.[0];
    output.textContent = "Lokale bestandsindicatie wordt voorbereid. HOLD / DENY.";
    if (!reg || !rep || reg.size < 1 || reg.size > 262144 || rep.size < 1 || rep.size > 16384) {
      output.textContent = "GEWEIGERD / Kies een register (max. 256 KiB) en inspectierapport (max. 16 KiB). HOLD / DENY.";
      return;
    }
    try {
      const [regBytes, repBytes] = await Promise.all([reg.arrayBuffer(), rep.arrayBuffer()]);
      if (generation !== current || $("admin-dashboard").hidden) return;
      const decoder = new TextDecoder("utf-8", {fatal: true});
      const snapshot = JSON.parse(decoder.decode(regBytes));
      const report = JSON.parse(decoder.decode(repBytes));
      const fixed = {
        schema: "palaco.pp.review-044-registry-row-inspection.v0",
        reference: "PP-RECOVERY-002",
        sourceRegistrySchema: "palaco.pp.review-044-owner-registry.v0",
        internalConsistency: "BROWSER_INDICATED_CHAIN_CONSISTENT",
        evidenceKind: "IMPORTED_UNATTESTED_LOCAL_DOSSIER",
        independentVerification: "NOT_VERIFIED",
        historicalImmutability: "NOT_ESTABLISHED",
        identityBinding: "NOT_ESTABLISHED",
        executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
        authorization: "HOLD",
        accessDecision: "DENY",
        issuance: "NOT_AUTHORIZED",
        limitations: "No external attestation, source authenticity, historical integrity, clock or identity proof; Python validation required.",
      };
      const binding = ["sequence","technicalReportSha256","ownerWorksheetSha256","evidenceIndexSha256","entrySha256","previousEntrySha256"];
      const exact = (obj, keys) => obj && typeof obj === "object" && !Array.isArray(obj)
        && Object.keys(obj).length === keys.length && keys.every(k => Object.hasOwn(obj,k));
      const header = {
        schema: "palaco.pp.review-044-owner-registry.v0",
        reference: "PP-RECOVERY-002",
        verification: "NOT_VERIFIED",
        authorization: "HOLD",
        accessDecision: "DENY",
      };
      if (!exact(snapshot,[...Object.keys(header),"entries"])
        || Object.entries(header).some(([k,v]) => snapshot[k] !== v)
        || !Array.isArray(snapshot.entries) || snapshot.entries.length > 256
        || !exact(report,[...Object.keys(fixed),...binding])
        || Object.entries(fixed).some(([k,v]) => report[k] !== v)
        || !Number.isInteger(report.sequence) || report.sequence < 1
        || report.sequence > snapshot.entries.length) throw Error();
      const row = snapshot.entries[report.sequence-1];
      if (!row || binding.some(k => row[k] !== report[k])) throw Error();
      // This intentionally does not validate the full chain or duplicate JSON keys.
      if (generation !== current || $("admin-dashboard").hidden) return;
      output.textContent = "BROWSERINDICATIE: geselecteerde regelvelden komen overeen. GEEN strikte ketenvalidatie, geen controle op dubbele JSON-sleutels. Gebruik review_044_inspection_cli.py met --run voor Python-controle. NOT_VERIFIED / HOLD / DENY.";
    } catch (_) {
      if (generation !== current || $("admin-dashboard").hidden) return;
      output.textContent = "BROWSERINDICATIE GEWEIGERD / Bestanden of velden wijken af. Gebruik later de strikte Python-validator. HOLD / DENY.";
    }
  });
})();
