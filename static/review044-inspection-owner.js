"use strict";
// Client-side owner worksheet preview only. Python remains normative.
// No fetch, persistence, runner, identity action or automatic authorization.
(() => {
  const $ = id => document.getElementById(id);
  const fileInput = $("admin-review044-inspection-owner-file");
  const loadButton = $("admin-review044-inspection-owner-load");
  const exportButton = $("admin-review044-inspection-owner-export");
  const status = $("admin-review044-inspection-owner-status");
  const table = $("admin-review044-inspection-owner-rows");
  const dashboard = $("admin-dashboard");
  if (!fileInput || !loadButton || !exportButton || !table || !dashboard) return;

  const scenarios = [["baseline_consistent_untrusted","REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED"],["wrong_sequence","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["boolean_sequence","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_entry_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_technical_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_owner_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_index_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["forged_previous_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["authorization_escalation","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["verification_escalation","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["history_escalation","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["missing_field","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["unexpected_field","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["duplicate_inspection_key","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["truncated_inspection_json","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["oversized_inspection","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["empty_inspection","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["invalid_utf8_inspection","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["broken_registry_entry_hash","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["forged_registry_authorization","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["empty_registry","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["wrong_registry_row_sequence","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["duplicate_registry_key","PP_REVIEW_044_OWNER_INSPECTION_INVALID"],["oversized_registry","PP_REVIEW_044_OWNER_INSPECTION_INVALID"]];
  const allowedResults = new Set(["REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED",
                                  "PP_REVIEW_044_OWNER_INSPECTION_INVALID"]);
  const requiredTop = {
    schema: "palaco.pp.review-044-inspection-technical-report.v0",
    reference: "PP-RECOVERY-002", scope: "SYNTHETIC_OFFLINE_ONLY",
    independentVerification: "NOT_VERIFIED", reviewDecision: "PENDING_OWNER_REVIEW",
    authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED"
  };
  const rowFields = ["scenario_id","expected_result","observed_result","comparison",
                     "evidence_kind","authorization","accessDecision"];
  const exact = (obj, keys) => obj !== null && typeof obj === "object" && !Array.isArray(obj)
    && Object.keys(obj).length === keys.length && keys.every(k => Object.hasOwn(obj,k));
  let epoch = 0;
  let assessment = null;
  let marks = new Map();
  const reset = (message = "Geen technisch rapport geladen. HOLD / DENY.") => {
    epoch += 1;
    assessment = null;
    marks.clear();
    exportButton.disabled = true;
    table.replaceChildren();
    status.textContent = message;
  };
  fileInput.addEventListener("change", () => reset("Bestand gewijzigd; eerdere markeringen ongeldig. HOLD / DENY."));
  // Also invalidate on logout/session loss (even when the original admin code hides the dashboard).
  const observer = new MutationObserver(() => {
    if (dashboard.hidden) {
      reset("Beheerderssessie gesloten; lokaal werkblad gewist. HOLD / DENY.");
      fileInput.value = "";
    }
  });
  observer.observe(dashboard, {attributes: true, attributeFilter: ["hidden"]});
  $("admin-logout").addEventListener("click", () => {
    reset("Afmelden aangevraagd; eigenaarwerkblad lokaal gewist. HOLD / DENY.");
    fileInput.value = "";
  });

  const updateCount = () => {
    if (!assessment) return;
    const marked = [...marks.values()].filter(v => v !== "NOT_REVIEWED").length;
    const diff = [...marks.values()].filter(v => v === "DISCREPANCY_REPORTED").length;
    status.textContent = `24 synthetische scenario's herkenbaar (browserindicatie). ${marked} gemarkeerd; ${diff} afwijkingen door eigenaar geclaimd. Geen Python-uitvoering of onafhankelijke verificatie. HOLD / DENY.`;
  };
  const showRows = report => {
    table.replaceChildren();
    report.observations.forEach((item, index) => {
      const tr = document.createElement("tr");
      const number = document.createElement("td");
      number.textContent = String(index + 1);
      const name = document.createElement("td");
      name.textContent = item.scenario_id;
      const observed = document.createElement("td");
      observed.textContent = item.comparison === "MATCH" ? "MATCH_CLAIMED" : "MISMATCH_CLAIMED";
      const markCell = document.createElement("td");
      const select = document.createElement("select");
      select.setAttribute("aria-label", `Eigen waarneming: ${item.scenario_id}`);
      select.className = "admin-review044-inspection-owner-mark";
      for (const [value,label] of [
        ["", "Niet ingevoerd"],
        ["NOT_REVIEWED", "Expliciet niet beoordeeld"],
        ["OBSERVED_AS_REPORTED", "Zelf waargenomen zoals gerapporteerd"],
        ["DISCREPANCY_REPORTED", "Zelf een afwijking waargenomen"]
      ]) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        select.append(option);
      }
      select.addEventListener("change", () => {
        if (!assessment || dashboard.hidden) return;
        if (select.value === "") marks.delete(item.scenario_id);
        else marks.set(item.scenario_id, select.value);
        updateCount();
      });
      markCell.append(select);
      tr.append(number, name, observed, markCell);
      table.append(tr);
    });
  };

  loadButton.addEventListener("click", async () => {
    reset("Technisch rapport wordt lokaal gelezen. HOLD / DENY.");
    const current = epoch;
    const file = fileInput.files?.[0];
    if (dashboard.hidden || !file || file.size < 1 || file.size > 64 * 1024) {
      status.textContent = "GEWEIGERD / Kies een technisch JSON-rapport van maximaal 64 KiB. HOLD / DENY.";
      return;
    }
    try {
      const bytes = await file.arrayBuffer();
      if (current !== epoch || dashboard.hidden) return;
      const report = JSON.parse(new TextDecoder("utf-8", {fatal:true}).decode(bytes));
      if (!exact(report, [...Object.keys(requiredTop),"observations"]) ||
          Object.entries(requiredTop).some(([k,v]) => report[k] !== v) ||
          !Array.isArray(report.observations) || report.observations.length !== scenarios.length) throw Error();
      report.observations.forEach((row,index) => {
        const [name, expected] = scenarios[index];
        if (!exact(row,rowFields) ||
            row.scenario_id !== name || row.expected_result !== expected ||
            !allowedResults.has(row.observed_result) ||
            row.comparison !== (row.observed_result === expected ? "MATCH" : "MISMATCH") ||
            row.evidence_kind !== "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION" ||
            row.authorization !== "HOLD" || row.accessDecision !== "DENY") throw Error();
      });
      const digest = await crypto.subtle.digest("SHA-256", bytes);
      if (current !== epoch || dashboard.hidden) return;
      const sha = [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2,"0")).join("");
      const mismatches = report.observations.filter(x => x.comparison === "MISMATCH").length;
      assessment = {sha, comparison: mismatches === 0 ? "ALL_MATCH_CLAIMED" : "MISMATCH_CLAIMED"};
      showRows(report);
      exportButton.disabled = false;
      updateCount();
    } catch (_) {
      if (current !== epoch || dashboard.hidden) return;
      reset("Rapportstructuur geweigerd. Browser detecteert geen dubbele JSON-sleutels; gebruik Python voor strikte beoordeling. HOLD / DENY.");
    }
  });
  exportButton.addEventListener("click", () => {
    if (dashboard.hidden || !assessment || exportButton.disabled) return;
    const rows = scenarios.map(([name]) => ({
      scenario_id: name,
      owner_mark: marks.get(name) ?? "NOT_REVIEWED",
      evidence_kind: marks.has(name) ? "SELF_REPORTED" : "NO_OBSERVATION"
    }));
    const worksheet = {
      schema: "palaco.pp.review-044-inspection-owner-worksheet.v0",
      reference: "PP-RECOVERY-002",
      technicalReportSha256: assessment.sha,
      technicalComparison: assessment.comparison,
      executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
      ownerMarks: rows,
      ownerMarkedCount: rows.filter(x => x.owner_mark !== "NOT_REVIEWED").length,
      ownerDiscrepancyCount: rows.filter(x => x.owner_mark === "DISCREPANCY_REPORTED").length,
      ownerEvidence: "UNSIGNED_SELF_REPORTED_OR_NOT_OBSERVED",
      independentVerification: "NOT_VERIFIED",
      reviewDecision: "HOLD", identityBinding: "NOT_ESTABLISHED",
      authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED"
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(worksheet,null,2)+"\n"],{type:"application/json"}));
    const anchor=document.createElement("a");
    anchor.href=url;
    anchor.download="palaco-pp-review-044-inspection-owner-worksheet-hold.json";
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url),1000);
    status.textContent = "Niet-ondertekend werkblad als download aangeboden. Controleer zelf de opslag; Python-validatie blijft noodzakelijk. HOLD / DENY.";
  });
})();
