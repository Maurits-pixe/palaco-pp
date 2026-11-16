"use strict";
// Read-only display of a claimed offline Python result. File metadata is untrusted.
// No network, no filesystem writes, no authority or identity transitions.
(() => {
  const $ = id => document.getElementById(id);
  const input = $("admin-review044-evidence-view-file");
  const check = $("admin-review044-evidence-view-load");
  const output = $("admin-review044-evidence-view-status");
  const details = $("admin-review044-evidence-view-details");
  const dashboard = $("admin-dashboard");
  if (![input, check, output, details, dashboard].every(Boolean)) return;

  const required = {
    schema: "palaco.pp.review-044-inspection-owner-evidence.v0",
    reference: "PP-RECOVERY-002",
    reportedScenarios: 24,
    binding: "STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED",
    evidenceKind: "UNSIGNED_LOCAL_PYTHON_VALIDATION_RESULT",
    executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
    independentVerification: "NOT_VERIFIED",
    reviewDecision: "HOLD",
    identityBinding: "NOT_ESTABLISHED",
    authorization: "HOLD",
    accessDecision: "DENY",
    issuance: "NOT_AUTHORIZED",
    historicalImmutability: "NOT_ESTABLISHED",
    limitations: "Consistent input bytes are not attestation, origin, execution, time, identity or authority proof."
  };
  const fields = [...Object.keys(required), "sourceTechnicalReportSha256",
    "sourceOwnerWorksheetSha256", "claimedTechnicalMismatches",
    "technicalComparison", "ownerMarkedCount", "ownerDiscrepancyCount"];
  const hash = v => typeof v === "string" && /^[a-f0-9]{64}$/.test(v);
  const integer = v => Number.isInteger(v) && v >= 0 && v <= 24;
  let revision = 0;
  const reset = (message = "Nog geen bewijsrapport geïnspecteerd. HOLD / DENY.") => {
    revision++;
    details.replaceChildren();
    details.hidden = true;
    output.textContent = message;
  };
  input.addEventListener("change", () => reset("Bestandskeuze gewijzigd; eerdere indicatie vervallen. HOLD / DENY."));
  new MutationObserver(() => {
    if (dashboard.hidden) {
      reset("Sessie gesloten; lokale bewijsweergave gewist. HOLD / DENY.");
      input.value = "";
    }
  }).observe(dashboard, {attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click", () => {
    reset("Afmelding aangevraagd; bewijsweergave gewist. HOLD / DENY.");
    input.value = "";
  });
  check.addEventListener("click", async () => {
    reset("Bewijsbestand wordt uitsluitend lokaal gelezen. HOLD / DENY.");
    const version = revision;
    const file = input.files?.[0];
    if (dashboard.hidden || !file || !file.size || file.size > 16384) {
      output.textContent = "GEWEIGERD / Kies een niet-leeg JSON-bewijsrapport van maximaal 16 KiB. HOLD / DENY.";
      return;
    }
    try {
      const bytes = await file.arrayBuffer();
      if (version !== revision || dashboard.hidden) return;
      const obj = JSON.parse(new TextDecoder("utf-8", {fatal:true}).decode(bytes));
      if (!obj || typeof obj !== "object" || Array.isArray(obj)
        || Object.keys(obj).length !== fields.length
        || !fields.every(k => Object.hasOwn(obj,k))
        || Object.entries(required).some(([k,v]) => obj[k] !== v)
        || !hash(obj.sourceTechnicalReportSha256)
        || !hash(obj.sourceOwnerWorksheetSha256)
        || !integer(obj.claimedTechnicalMismatches)
        || !integer(obj.ownerMarkedCount) || !integer(obj.ownerDiscrepancyCount)
        || obj.ownerDiscrepancyCount > obj.ownerMarkedCount
        || obj.technicalComparison !== (obj.claimedTechnicalMismatches === 0
          ? "ALL_MATCH_CLAIMED" : "MISMATCH_CLAIMED")) throw Error();

      const sections = [
        ["TECHNISCHE CONSISTENTIE — alleen geclaimd", [
          ["Rapporttype", obj.evidenceKind],
          ["Binding (ingelezen claim)", obj.binding],
          ["Aantal scenario's", obj.reportedScenarios],
          ["Technische mismatchclaims", obj.claimedTechnicalMismatches],
          ["Technische vergelijking", obj.technicalComparison],
          ["Technisch rapport SHA-256", obj.sourceTechnicalReportSha256],
          ["Eigenaarwerkblad SHA-256", obj.sourceOwnerWorksheetSha256]
        ]],
        ["EIGENAARSWAARNEMINGEN — niet ondertekend", [
          ["Gemarkeerd", obj.ownerMarkedCount],
          ["Door eigenaar geclaimde afwijkingen", obj.ownerDiscrepancyCount],
          ["Uitvoeringsherkomst", obj.executionProvenance]
        ]],
        ["ONAFHANKELIJKE VERIFICATIE EN BESLUIT", [
          ["Verificatie", obj.independentVerification],
          ["Identiteitsbinding", obj.identityBinding],
          ["Historische onveranderlijkheid", obj.historicalImmutability],
          ["Beoordeling / autorisatie", obj.reviewDecision + " / " + obj.authorization],
          ["Toegang / uitgifte", obj.accessDecision + " / " + obj.issuance],
          ["Beperkingen", obj.limitations]
        ]]
      ];
      const fragment = document.createDocumentFragment();
      for (const [heading,rows] of sections) {
        const section = document.createElement("section");
        const h = document.createElement("h4");
        h.textContent = heading;
        const dl = document.createElement("dl");
        dl.className = "admin-registry-inspector";
        for (const [name,value] of rows) {
          const dt = document.createElement("dt");
          dt.textContent = name;
          const dd = document.createElement("dd");
          dd.textContent = String(value);
          dl.append(dt,dd);
        }
        section.append(h,dl);
        fragment.append(section);
      }
      if (version !== revision || dashboard.hidden) return;
      details.replaceChildren(fragment);
      details.hidden = false;
      output.textContent = "STRUCTUUR HERKEND / Dit bestand CLAIMT een strikte Python-bewijsbinding; de browser kan de uitvoering of oorspronkelijke bytes niet onafhankelijk bevestigen. NOT_VERIFIED / HOLD / DENY.";
    } catch (_) {
      if (version !== revision || dashboard.hidden) return;
      reset("BEWIJSRAPPORT GEWEIGERD / Structuur, status of interne aantallen ongeldig. HOLD / DENY.");
    }
  });
})();
