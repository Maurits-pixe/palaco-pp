"use strict";
// Browser indication only: this is NOT the normative strict Python validation.
// Never upload files, run tests, persist owner marks, or grant access.
(() => {
  const $ = id => document.getElementById(id);
  const technical = $("admin-review044-inspection-binding-technical");
  const worksheet = $("admin-review044-inspection-binding-owner");
  const check = $("admin-review044-inspection-binding-check");
  const exportButton = $("admin-review044-inspection-binding-export");
  const status = $("admin-review044-inspection-binding-status");
  const detail = $("admin-review044-inspection-binding-detail");
  const dashboard = $("admin-dashboard");
  if (![technical, worksheet, check, exportButton, status, detail, dashboard].every(Boolean)) return;

  const scenarios = [["baseline_consistent_untrusted","REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED"],["wrong_sequence","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["boolean_sequence","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_entry_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_technical_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_owner_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_index_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["forged_previous_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["authorization_escalation","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["verification_escalation","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["history_escalation","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["missing_field","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["unexpected_field","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["duplicate_inspection_key","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["truncated_inspection_json","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["oversized_inspection","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["empty_inspection","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["invalid_utf8_inspection","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["broken_registry_entry_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["forged_registry_authorization","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["empty_registry","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_registry_row_sequence","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["duplicate_registry_key","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["oversized_registry","PP_REVIEW_044_OWNER_INSPECTION_INVALID"]];
  const allowedResults = new Set([
    "REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED",
    "PP_REVIEW_044_OWNER_INSPECTION_INVALID"
  ]);
  const ownerMarks = new Set([
    "NOT_REVIEWED", "OBSERVED_AS_REPORTED", "DISCREPANCY_REPORTED"
  ]);
  const exact = (value, fields) => value !== null && typeof value === "object"
    && !Array.isArray(value) && Object.keys(value).length === fields.length
    && fields.every(key => Object.hasOwn(value, key));
  const fixedTechnical = {
    schema: "palaco.pp.review-044-inspection-technical-report.v0",
    reference: "PP-RECOVERY-002", scope: "SYNTHETIC_OFFLINE_ONLY",
    independentVerification: "NOT_VERIFIED", reviewDecision: "PENDING_OWNER_REVIEW",
    authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED"
  };
  const technicalRowFields = [
    "scenario_id","expected_result","observed_result","comparison",
    "evidence_kind","authorization","accessDecision"
  ];
  const ownerFields = [
    "schema","reference","technicalReportSha256","technicalComparison",
    "executionProvenance","ownerMarks","ownerMarkedCount","ownerDiscrepancyCount",
    "ownerEvidence","independentVerification","reviewDecision","identityBinding",
    "authorization","accessDecision","issuance"
  ];
  const ownerRowFields = ["scenario_id","owner_mark","evidence_kind"];
  let version = 0;
  let assessment = null;

  function reset(message = "Bestandskeuze gewijzigd; beoordeling vervallen. HOLD / DENY.") {
    version += 1;
    assessment = null;
    exportButton.disabled = true;
    detail.replaceChildren();
    status.textContent = message;
  }
  technical.addEventListener("change", () => reset());
  worksheet.addEventListener("change", () => reset());
  // Hide sensitive local review state when the dashboard session ends.
  new MutationObserver(() => {
    if (dashboard.hidden) {
      reset("Sessie gesloten; lokale beoordeling gewist. HOLD / DENY.");
      technical.value = "";
      worksheet.value = "";
    }
  }).observe(dashboard, {attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click", () => {
    reset("Afmelden aangevraagd; eerdere vergelijking gewist. HOLD / DENY.");
    technical.value = "";
    worksheet.value = "";
  });
  const digestHex = async bytes => {
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
    return [...digest].map(byte => byte.toString(16).padStart(2,"0")).join("");
  };
  check.addEventListener("click", async () => {
    reset("De originele bestanden worden lokaal vergeleken. HOLD / DENY.");
    const current = version;
    const tech = technical.files?.[0];
    const owner = worksheet.files?.[0];
    if (dashboard.hidden || !tech || !owner || tech.size < 1 || owner.size < 1
        || tech.size > 65536 || owner.size > 49152) {
      status.textContent = "GEWEIGERD / Technisch rapport max. 64 KiB; werkblad max. 48 KiB. HOLD / DENY.";
      return;
    }
    try {
      const [techBytes, ownerBytes] = await Promise.all([tech.arrayBuffer(), owner.arrayBuffer()]);
      if (current !== version || dashboard.hidden) return;
      const decoder = new TextDecoder("utf-8",{fatal:true});
      const report = JSON.parse(decoder.decode(techBytes));
      const saved = JSON.parse(decoder.decode(ownerBytes));
      if (!exact(report,[...Object.keys(fixedTechnical),"observations"])
          || Object.entries(fixedTechnical).some(([key,value]) => report[key] !== value)
          || !Array.isArray(report.observations) || report.observations.length !== scenarios.length) throw Error();
      let technicalMismatches = 0;
      report.observations.forEach((item,i) => {
        const [name,expected] = scenarios[i];
        if (!exact(item,technicalRowFields) || item.scenario_id !== name
            || item.expected_result !== expected || !allowedResults.has(item.observed_result)
            || item.evidence_kind !== "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION"
            || item.authorization !== "HOLD" || item.accessDecision !== "DENY"
            || item.comparison !== (item.observed_result === expected ? "MATCH" : "MISMATCH")) throw Error();
        if (item.comparison === "MISMATCH") technicalMismatches++;
      });
      const [techSha,ownerSha] = await Promise.all([digestHex(techBytes),digestHex(ownerBytes)]);
      if (current !== version || dashboard.hidden) return;
      const technicalComparison = technicalMismatches === 0 ? "ALL_MATCH_CLAIMED" : "MISMATCH_CLAIMED";
      if (!exact(saved,ownerFields) || !Array.isArray(saved.ownerMarks)
          || saved.ownerMarks.length !== scenarios.length) throw Error();
      let marked = 0, discrepancies = 0;
      for (let i = 0; i < scenarios.length; i++) {
        const row = saved.ownerMarks[i];
        if (!exact(row,ownerRowFields) || row.scenario_id !== scenarios[i][0]
            || !ownerMarks.has(row.owner_mark)
            || (row.evidence_kind !== "SELF_REPORTED" && row.evidence_kind !== "NO_OBSERVATION")
            || (row.evidence_kind === "NO_OBSERVATION" && row.owner_mark !== "NOT_REVIEWED")) throw Error();
        if (row.owner_mark !== "NOT_REVIEWED") marked++;
        if (row.owner_mark === "DISCREPANCY_REPORTED") discrepancies++;
      }
      const fixedOwner = {
        schema: "palaco.pp.review-044-inspection-owner-worksheet.v0",
        reference: "PP-RECOVERY-002", technicalReportSha256: techSha,
        technicalComparison, executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
        ownerMarkedCount: marked, ownerDiscrepancyCount: discrepancies,
        ownerEvidence: "UNSIGNED_SELF_REPORTED_OR_NOT_OBSERVED",
        independentVerification: "NOT_VERIFIED", reviewDecision: "HOLD",
        identityBinding: "NOT_ESTABLISHED", authorization: "HOLD",
        accessDecision: "DENY", issuance: "NOT_AUTHORIZED"
      };
      if (Object.entries(fixedOwner).some(([key,value]) => saved[key] !== value
          || typeof saved[key] !== typeof value)) throw Error();
      assessment = {
        schema: "palaco.pp.review-044-inspection-owner-browser-binding.v0",
        reference: "PP-RECOVERY-002",
        technicalReportSha256: techSha,
        ownerWorksheetSha256: ownerSha,
        binding: "CLIENT_TWO_FILE_HASH_MATCH_UNTRUSTED",
        technicalComparison,
        ownerMarkedCount: marked,
        ownerDiscrepancyCount: discrepancies,
        parserLimitation: "JSON_PARSE_CANNOT_DETECT_DUPLICATE_KEYS",
        executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
        independentVerification: "NOT_VERIFIED",
        reviewDecision: "HOLD", identityBinding: "NOT_ESTABLISHED",
        authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED"
      };
      // Never imply that a client-only comparison is a Python result.
      detail.replaceChildren();
      for (const [label,value] of [
        ["Technisch rapport SHA-256",techSha],["Eigenaarwerkblad SHA-256",ownerSha],
        ["Technische vergelijking",technicalComparison],
        ["Eigenaarsmarkeringen",String(marked)],
        ["Door eigenaar gemelde afwijkingen",String(discrepancies)],
        ["Onafhankelijke verificatie","NOT_VERIFIED"],
        ["Autorisatie","HOLD / DENY / NOT_AUTHORIZED"]
      ]) {
        const dt=document.createElement("dt");dt.textContent=label;
        const dd=document.createElement("dd");dd.textContent=value;
        detail.append(dt,dd);
      }
      exportButton.disabled = false;
      status.textContent = "LOKALE BROWSERINDICATIE / Twee-bestandenbinding consistent volgens deze parser. Strikte Python-validator nog noodzakelijk. HOLD / DENY.";
    } catch (_) {
      if (current !== version || dashboard.hidden) return;
      reset("BINDING AFGEWEZEN / Ongeldige structuur, markeringen of bestandsvingerafdruk. HOLD / DENY.");
    }
  });
  exportButton.addEventListener("click", () => {
    if (dashboard.hidden || !assessment || exportButton.disabled) return;
    const url=URL.createObjectURL(new Blob([JSON.stringify(assessment,null,2)+"\n"],{type:"application/json"}));
    const a=document.createElement("a");
    a.href=url;a.download="palaco-pp-review-044-inspection-owner-browser-binding-hold.json";
    document.body.append(a);a.click();a.remove();
    setTimeout(() => URL.revokeObjectURL(url),1000);
    status.textContent = "Niet-ondertekende browserindicatie als download aangeboden. Opslag zelf bevestigen; Python-controle blijft vereist. HOLD / DENY.";
  });
})();
