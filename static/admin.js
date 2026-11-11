"use strict";

const $ = (id) => document.getElementById(id);
const errors = {
  PP_ADMIN_REQUIRED: "Meld je opnieuw aan als beheerder.",
  PP_CREDENTIALS_INVALID: "Beheerdersnaam of wachtwoord onjuist.",
  PP_LOGIN_RATE_LIMITED: "Te veel pogingen. Probeer over 15 minuten opnieuw.",
  PP_ADMIN_REASON_INVALID: "Geef een reden van 5 tot 240 tekens.",
  PP_SELECTION_REVOKED: "Dit nummer is al ingetrokken. Vernieuw het overzicht.",
  PP_SELECTION_UNKNOWN: "De registratie kan niet betrouwbaar worden verwerkt.",
  PP_AUDIT_UNKNOWN: "De beheeraudit bevat ongeldige gegevens. Auditweergave geblokkeerd; controleer de database.",
};
let busy = false;
let authenticated = false;
let accountOffset = 0;
let auditOffset = 0;
let target = null;
let search = "";
let statusFilter = "";
let auditSearch = "";
let auditEvent = "";
let auditStatus = "";
let reviewAssessment = null;
let bundleAssessment = null;
let bundleSelectionVersion = 0;
let chainSelectionVersion = 0;
let chainAssessment = null;
const review044Expectations = Object.freeze({
  baseline_untrusted_hold: "FOUR_FILE_HASH_MATCH_UNTRUSTED",
  handoff_changed_without_rebinding: "PP_CHAIN_INVALID",
  report_authority_escalation: "PP_CHAIN_INVALID",
  index_wrong_report_digest: "PP_CHAIN_INVALID",
  observation_wrong_index_digest: "PP_CHAIN_INVALID",
  observation_authority_escalation: "PP_CHAIN_INVALID",
  observation_duplicate_key: "PP_CHAIN_INVALID",
  observation_truncated_json: "PP_CHAIN_INVALID",
  observation_oversized: "PP_CHAIN_INVALID",
});
const review044Observations = new Map();
const review044TechnicalExpectations = Object.freeze({
  baseline_unobserved_hold: "HOLD_DENY_PREVIEW",
  baseline_self_reported_hold: "HOLD_DENY_PREVIEW",
  time_missing_z: "PP_REVIEW_044_PREVIEW_INVALID",
  time_noncanonical_offset: "PP_REVIEW_044_PREVIEW_INVALID",
  time_impossible_date: "PP_REVIEW_044_PREVIEW_INVALID",
  time_missing_milliseconds: "PP_REVIEW_044_PREVIEW_INVALID",
  authority_escalation: "PP_REVIEW_044_PREVIEW_INVALID",
  verification_escalation: "PP_REVIEW_044_PREVIEW_INVALID",
  observation_after_report: "PP_REVIEW_044_PREVIEW_INVALID",
  forged_pass_label: "PP_REVIEW_044_PREVIEW_INVALID",
  missing_provenance: "PP_REVIEW_044_PREVIEW_INVALID",
  duplicate_json_key: "PP_REVIEW_044_PREVIEW_INVALID",
  oversized_report: "PP_REVIEW_044_PREVIEW_INVALID",
});
const review044TechnicalResults = new Set([
  "HOLD_DENY_PREVIEW", "PP_REVIEW_044_PREVIEW_INVALID",
  "UNEXPECTED_AUTHORITY_STATE", "UNEXPECTED_ERROR",
]);
const review044OwnerMarks = new Map();
let review044TechnicalAssessment = null;
let review044TechnicalSelectionVersion = 0;
let review044IndexSelectionVersion = 0;
let review044IndexAssessment = null;
let review044DossierSelectionVersion = 0;
let review044DossierAssessment = null;
let review044RegistryVersion = 0;
let review044RegistryDraft = null;

function exactFields(value, fields) {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    && Object.keys(value).length === fields.length
    && fields.every((field) => Object.hasOwn(value, field));
}

// Browser-only structural indication; JSON.parse does not reject duplicate keys.
// review_044_preview_assessment.py remains the stricter normative parser.
function assessReview044TechnicalBrowserReport(report) {
  const topFields = ["schema", "reference", "scope", "observations", "verification",
    "reviewDecision", "authorization", "accessDecision", "issuance"];
  const requirements = {
    schema: "palaco.pp.review-044-preview-technical-report.v0",
    reference: "PP-RECOVERY-002", scope: "SYNTHETIC_OFFLINE_ONLY",
    verification: "NOT_INDEPENDENTLY_VERIFIED", reviewDecision: "PENDING_OWNER_REVIEW",
    authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
  };
  if (!exactFields(report, topFields)
    || Object.entries(requirements).some(([key, value]) => report[key] !== value)) {
    throw new Error("TECHNICAL_STRUCTURE_INVALID");
  }
  const scenarios = Object.entries(review044TechnicalExpectations);
  if (!Array.isArray(report.observations) || report.observations.length !== scenarios.length) {
    throw new Error("TECHNICAL_SCENARIOS_INVALID");
  }
  let mismatches = 0;
  const rowFields = ["scenario_id", "expected_result", "observed_result", "comparison",
    "evidence_kind", "authorization", "accessDecision"];
  for (let i = 0; i < scenarios.length; i += 1) {
    const [name, expected] = scenarios[i];
    const row = report.observations[i];
    if (!exactFields(row, rowFields) || row.scenario_id !== name
      || row.expected_result !== expected || !review044TechnicalResults.has(row.observed_result)
      || row.evidence_kind !== "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION"
      || row.authorization !== "HOLD" || row.accessDecision !== "DENY"
      || row.comparison !== (row.observed_result === expected ? "MATCH" : "MISMATCH")) {
      throw new Error("TECHNICAL_ROW_INVALID");
    }
    if (row.comparison === "MISMATCH") mismatches += 1;
  }
  return mismatches === 0 ? "ALL_MATCH_CLAIMED" : "MISMATCH_CLAIMED";
}

function downloadReview044OwnerJson(report) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-review-044-owner-worksheet-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function clearReview() {
  reviewAssessment = null;
  bundleAssessment = null;
  bundleSelectionVersion += 1;
  chainSelectionVersion += 1;
  chainAssessment = null;
  $("admin-review-file").value = "";
  $("admin-review-note").value = "";
  $("admin-review-result").textContent = "Nog geen bestand beoordeeld.";
  $("admin-review-download").disabled = true;
  $("admin-bundle-handoff").value = "";
  $("admin-bundle-report").value = "";
  $("admin-bundle-result").textContent = "Nog geen bewijsbinding beoordeeld.";
  $("admin-bundle-export").disabled = true;
  for (const id of ["admin-chain-handoff", "admin-chain-report", "admin-chain-index"]) $(id).value = "";
  $("admin-chain-result").textContent = "Geen ketencontrole uitgevoerd. HOLD / DENY.";
  $("admin-chain-export").disabled = true;
  review044Observations.clear();
  review044TechnicalSelectionVersion += 1;
  review044TechnicalAssessment = null;
  review044OwnerMarks.clear();
  $("admin-review044-tech-file").value = "";
  $("admin-review044-owner-scenario").selectedIndex = 0;
  $("admin-review044-owner-mark").value = "NOT_REVIEWED";
  $("admin-review044-tech-status").textContent = "Geen lokaal technisch rapport geladen. HOLD / DENY.";
  $("admin-review044-owner-record").disabled = true;
  $("admin-review044-owner-export").disabled = true;
  review044IndexSelectionVersion += 1;
  review044IndexAssessment = null;
  $("admin-review044-index-tech").value = "";
  $("admin-review044-index-owner").value = "";
  $("admin-review044-index-result").textContent = "Geen bestandsbinding beoordeeld. HOLD / DENY.";
  $("admin-review044-index-export").disabled = true;
  review044DossierSelectionVersion += 1;
  review044DossierAssessment = null;
  for (const id of ["admin-review044-dossier-tech", "admin-review044-dossier-owner",
    "admin-review044-dossier-index"]) $(id).value = "";
  $("admin-review044-dossier-result").textContent = "Nog geen dossierbeoordeling. HOLD / DENY.";
  $("admin-review044-dossier-export").disabled = true;
  review044RegistryVersion += 1;
  review044RegistryDraft = null;
  $("admin-review044-registry-file").value = "";
  $("admin-review044-registry-add").disabled = true;
  $("admin-review044-registry-export").disabled = true;
  $("admin-review044-registry-result").textContent = "Geen registerversie voorbereid. HOLD / DENY.";
  $("admin-review044-scenario").selectedIndex = 0;
  $("admin-review044-observed").value = "NOT_OBSERVED";
  $("admin-review044-result").textContent = "Nog geen eigen waarnemingen vastgelegd. HOLD / DENY.";
  $("admin-review044-export").disabled = true;
}

function notice(message, error = false) {
  $("admin-notice").textContent = message;
  $("admin-notice").classList.toggle("error", error);
}

function showLogin() {
  clearReview();
  authenticated = false;
  $("admin-dashboard").hidden = true;
  $("admin-dashboard").querySelectorAll("tbody").forEach((body) => body.replaceChildren());
  $("admin-counts").replaceChildren();
  $("admin-login-panel").hidden = false;
  $("admin-logout").hidden = true;
  $("admin-name").textContent = "";
  target = null;
  $("admin-reason").value = "";
  $("admin-confirm-dialog").close();
  $("admin-filters").reset();
  $("audit-filters").reset();
  search = statusFilter = "";
  auditSearch = auditEvent = auditStatus = "";
  accountOffset = auditOffset = 0;
}

async function api(path, body) {
  const response = await fetch(`/api/admin/${path}`, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const result = await response.json();
  if (!response.ok) {
    if (result.error === "PP_ADMIN_REQUIRED") showLogin();
    if (result.error === "PP_AUDIT_UNKNOWN") {
      $("admin-audit").replaceChildren();
      $("audit-page").textContent = "Audit niet beschikbaar";
      $("audit-no-results").hidden = true;
      auditTotal = 0;
    }
    throw new Error(errors[result.error] || `Verzoek mislukt: ${result.error || response.status}`);
  }
  return result;
}

async function action(work) {
  if (busy) return;
  busy = true;
  document.querySelectorAll("button").forEach((button) => {
    button.dataset.disabledBefore = String(button.disabled);
    button.disabled = true;
  });
  try {
    await work();
    return true;
  } catch (error) {
    notice(error.message, true);
    return false;
  } finally {
    busy = false;
    document.querySelectorAll("button").forEach((button) => {
      button.disabled = button.dataset.disabledBefore === "true";
    });
    if (authenticated) updatePagination();
  }
}

let accountTotal = 0;
let auditTotal = 0;
function updatePagination() {
  $("accounts-prev").disabled = accountOffset === 0;
  $("accounts-next").disabled = accountOffset + 50 >= accountTotal;
  $("audit-prev").disabled = auditOffset === 0;
  $("audit-next").disabled = auditOffset + 50 >= auditTotal;
}

function cell(row, text) {
  const td = document.createElement("td");
  td.textContent = text;
  row.append(td);
  return td;
}

async function refresh() {
  const query = new URLSearchParams({ offset: accountOffset, q: search, status: statusFilter });
  const auditQuery = new URLSearchParams({
    offset: auditOffset, q: auditSearch, event: auditEvent, status: auditStatus,
  });
  let [overview, audit] = await Promise.all([
    api(`overview?${query}`), api(`audit?${auditQuery}`),
  ]);
  if (!authenticated) return;
  if (accountOffset > 0 && accountOffset >= overview.total) {
    const lastPage = Math.max(0, Math.ceil(overview.total / 50) - 1) * 50;
    query.set("offset", lastPage);
    overview = await api(`overview?${query}`);
    accountOffset = lastPage;
  }
  if (auditOffset > 0 && auditOffset >= audit.total) {
    const lastPage = Math.max(0, Math.ceil(audit.total / 50) - 1) * 50;
    auditQuery.set("offset", lastPage);
    audit = await api(`audit?${auditQuery}`);
    auditOffset = lastPage;
  }
  accountTotal = overview.total;
  auditTotal = audit.total;
  $("admin-counts").replaceChildren();
  for (const [key, label] of Object.entries({
    consumers: "Consumers", accounts: "Accounts", active: "Actieve nummers", revoked: "Ingetrokken",
  })) {
    const metric = document.createElement("article");
    metric.className = "admin-metric";
    const value = document.createElement("strong");
    value.textContent = overview.counts[key];
    const caption = document.createElement("span");
    caption.textContent = label;
    metric.append(value, caption);
    $("admin-counts").append(metric);
  }
  $("admin-accounts").replaceChildren();
  $("admin-no-results").hidden = overview.total !== 0;
  for (const entry of overview.entries) {
    const row = document.createElement("tr");
    const identity = cell(row, entry.username || "Anonieme demo");
    const reference = document.createElement("small");
    reference.textContent = entry.consumerId;
    identity.append(reference);
    cell(row, entry.ppNumber || "Nog geen keuze");
    cell(row, entry.status);
    const control = cell(row, "");
    if (entry.status === "ACTIVE") {
      const revoke = document.createElement("button");
      revoke.className = "text-button danger";
      revoke.textContent = "Intrekken";
      revoke.addEventListener("click", () => {
        if (busy) return;
        target = entry;
        $("admin-target").textContent = `${entry.username || entry.consumerId} / ${entry.ppNumber}`;
        $("admin-reason").value = "";
        $("admin-confirm-dialog").showModal();
      });
      control.append(revoke);
    }
    $("admin-accounts").append(row);
  }
  $("admin-audit").replaceChildren();
  $("audit-no-results").hidden = audit.total !== 0;
  for (const entry of audit.entries) {
    const row = document.createElement("tr");
    const reference = cell(row, entry.sequence);
    const time = document.createElement("small");
    time.textContent = new Date(entry.createdAt).toLocaleString("nl-NL");
    reference.append(time);
    const event = cell(row, entry.event);
    const status = document.createElement("small");
    status.textContent = entry.status || "Geen PP-status";
    event.append(status);
    const account = cell(row, entry.username || (entry.consumerId ? "Anonieme demo" : "Beheer / systeem"));
    if (entry.consumerId) {
      const consumerId = document.createElement("small");
      consumerId.textContent = entry.consumerId;
      account.append(consumerId);
    }
    const admin = cell(row, entry.adminUsername || (entry.adminId ? "Onbekende beheerder" : "Niet vastgelegd"));
    if (entry.adminId) {
      const adminId = document.createElement("small");
      adminId.textContent = entry.adminId;
      admin.append(adminId);
    }
    const reason = cell(row, entry.reason || "Niet van toepassing");
    reason.className = "audit-reason";
    $("admin-audit").append(row);
  }
  $("accounts-page").textContent = `${overview.entries.length} van ${accountTotal} / pagina ${accountOffset / 50 + 1}`;
  $("audit-page").textContent = `${audit.entries.length} van ${auditTotal} / pagina ${auditOffset / 50 + 1}`;
  updatePagination();
}

async function loadSession() {
  const admin = await api("me");
  authenticated = true;
  $("admin-name").textContent = admin.username;
  $("admin-login-panel").hidden = true;
  $("admin-logout").hidden = false;
  $("admin-dashboard").hidden = false;
  await refresh();
  notice("Beheerderssessie actief. Privé-notities blijven afgeschermd.");
}

$("admin-login").addEventListener("submit", (event) => {
  event.preventDefault();
  action(async () => {
    const password = $("admin-password").value;
    $("admin-password").value = "";
    await api("login", { username: $("admin-username").value, password });
    accountOffset = auditOffset = 0;
    await loadSession();
  });
});
$("admin-logout").addEventListener("click", () => action(async () => {
  await api("logout", {});
  showLogin();
  notice("Je bent afgemeld.");
}));
$("admin-refresh").addEventListener("click", () => action(async () => {
  await refresh();
  notice("Overzicht bijgewerkt.");
}));
async function applyFilters(reset) {
  if (busy) return;
  const previous = { search, statusFilter, accountOffset };
  search = reset ? "" : $("admin-search").value.trim();
  statusFilter = reset ? "" : $("admin-status").value;
  accountOffset = 0;
  const succeeded = await action(async () => {
    await refresh();
    notice("Zoekresultaten bijgewerkt.");
  });
  if (!succeeded && authenticated) {
    ({ search, statusFilter, accountOffset } = previous);
    updatePagination();
  }
  $("admin-search").value = search;
  $("admin-status").value = statusFilter;
}
$("admin-filters").addEventListener("submit", (event) => {
  event.preventDefault();
  applyFilters(false);
});
$("admin-filter-reset").addEventListener("click", () => applyFilters(true));
async function applyAuditFilters(reset) {
  if (busy) return;
  const previous = { auditSearch, auditEvent, auditStatus, auditOffset };
  auditSearch = reset ? "" : $("audit-search").value.trim();
  auditEvent = reset ? "" : $("audit-event").value;
  auditStatus = reset ? "" : $("audit-status").value;
  auditOffset = 0;
  const succeeded = await action(async () => {
    await refresh();
    notice("Auditresultaten bijgewerkt.");
  });
  if (!succeeded && authenticated) {
    ({ auditSearch, auditEvent, auditStatus, auditOffset } = previous);
    updatePagination();
  }
  $("audit-search").value = auditSearch;
  $("audit-event").value = auditEvent;
  $("audit-status").value = auditStatus;
}
$("audit-filters").addEventListener("submit", (event) => {
  event.preventDefault();
  applyAuditFilters(false);
});
$("audit-filter-reset").addEventListener("click", () => applyAuditFilters(true));
for (const [id, change] of [
  ["accounts-prev", () => { accountOffset -= 50; }],
  ["accounts-next", () => { accountOffset += 50; }],
  ["audit-prev", () => { auditOffset -= 50; }],
  ["audit-next", () => { auditOffset += 50; }],
]) {
  $(id).addEventListener("click", () => {
    if (busy) return;
    action(async () => {
      const previous = { accountOffset, auditOffset };
      change();
      try {
        await refresh();
      } catch (error) {
        if (authenticated) ({ accountOffset, auditOffset } = previous);
        throw error;
      }
    });
  });
}
$("admin-cancel").addEventListener("click", () => {
  target = null;
  $("admin-confirm-dialog").close();
});
$("admin-confirm-dialog").addEventListener("cancel", (event) => {
  if (busy) event.preventDefault();
  else target = null;
});
$("admin-revoke").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!target) return;
  action(async () => {
    await api("revoke", {
      consumerId: target.consumerId, reason: $("admin-reason").value, confirm: true,
    });
    target = null;
    $("admin-confirm-dialog").close();
    await refresh();
    notice("Nummer definitief ingetrokken; beheerhandeling geaudit.");
  });
});

$("admin-review-file").addEventListener("change", async () => {
  reviewAssessment = null;
  $("admin-review-download").disabled = true;
  const file = $("admin-review-file").files?.[0];
  const output = $("admin-review-result");
  output.textContent = "Geen bestand geselecteerd.";
  if (!file || !authenticated || busy) return;
  if (file.size === 0 || file.size > 16384) {
    output.textContent = "BESTAND GEWEIGERD / Alleen JSON van 1 t/m 16384 bytes.";
    $("admin-review-file").value = "";
    return;
  }
  const sessionName = $("admin-name").textContent;
  try {
    const raw = await file.arrayBuffer();
    if (!authenticated || $("admin-name").textContent !== sessionName) {
      output.textContent = "SESSIE GEWIJZIGD / Meld opnieuw aan.";
      return;
    }
    const bytes = new Uint8Array(raw);
    const digest = await crypto.subtle.digest("SHA-256", raw);
    if (!authenticated || $("admin-name").textContent !== sessionName) {
      output.textContent = "SESSIE GEWIJZIGD / Meld opnieuw aan.";
      return;
    }
    const sha256 = Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
    const data = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
    const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
    const fields = {
      schema: "palaco.pp.one.review-handoff.v0", reference: "PP-RECOVERY-002",
      source: "LOCAL_PP_PROTOTYPE_USER_EXPORTED", destination: "PALACO_ONE_MANUAL_REVIEW_ONLY",
      provenance: "UNSIGNED_USER_CONTROLLED_FILE", identityVerification: "NOT_VERIFIED",
      reviewDecision: "PENDING_HUMAN_REVIEW", authorization: "HOLD",
      accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
    };
    const expectedKeys = [...Object.keys(fields), "createdAt", "subjectReference", "registration", "constraints"];
    const registrationKeys = ["ppNumberId", "ppNumberLast4", "status", "selectedAt", "revokedAt"];
    const constraints = ["NO_AUTOMATIC_ACCOUNT_LINK", "NO_AUTHENTICATION", "NO_AUTO_ISSUANCE"];
    const exactKeys = (item, keys) => isObject(item) && Object.keys(item).length === keys.length &&
      keys.every((key) => Object.hasOwn(item, key));
    const structureValid = exactKeys(data, expectedKeys) &&
      Object.entries(fields).every(([key, value]) => data[key] === value) &&
      typeof data.createdAt === "string" && !Number.isNaN(Date.parse(data.createdAt)) &&
      exactKeys(data.subjectReference, ["consumerId"]) &&
      typeof data.subjectReference.consumerId === "string" &&
      exactKeys(data.registration, registrationKeys) &&
      typeof data.registration.ppNumberId === "string" &&
      typeof data.registration.ppNumberLast4 === "string" &&
      /^[0-9]{4}$/.test(data.registration.ppNumberLast4) &&
      ["ACTIVE", "REVOKED"].includes(data.registration.status) &&
      typeof data.registration.selectedAt === "string" &&
      Array.isArray(data.constraints) && data.constraints.length === 3 &&
      constraints.every((item) => data.constraints.includes(item));
    reviewAssessment = {
      schema: "palaco.pp.manual-review.v0", evidenceReference: "PP-RECOVERY-002",
      capturedAt: new Date().toISOString(), fileSha256: sha256,
      structuralStatus: structureValid ? "CLIENT_STRUCTURE_RECOGNIZED_UNTRUSTED" : "STRUCTURE_REJECTED",
      sourceEvidence: "UNSIGNED_USER_SUPPLIED_FILE", verification: "NOT_VERIFIED",
      reviewDecision: "HOLD", authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
    };
    output.textContent = structureValid
      ? "STRUCTUUR HERKEND / Inhoud blijft ONVERTROUWD. Geen verificatie van persoon, accountkoppeling of rechten. HOLD / DENY."
      : "STRUCTUUR AFGEWEZEN / Niet conform het conceptcontract. HOLD / DENY.";
    $("admin-review-download").disabled = false;
  } catch (error) {
    output.textContent = "ONGELDIG / Bestand of bestandsvingerafdruk kon niet worden verwerkt. Geen rapport aangemaakt.";
  } finally {
    $("admin-review-file").value = "";
  }
});

$("admin-review-download").addEventListener("click", () => {
  if (!authenticated || busy || !reviewAssessment) return;
  const report = {
    ...reviewAssessment,
    note: $("admin-review-note").value.trim().slice(0, 240),
    noteClass: "LOCAL_ADMIN_NOTE_NOT_INDEPENDENTLY_VERIFIED",
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-review-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("admin-review-result").textContent = "HOLD-rapport aangeboden als download. Geen opslag op de server of automatische goedkeuring.";
});

for (const id of ["admin-bundle-handoff", "admin-bundle-report"]) {
  $(id).addEventListener("change", () => {
    bundleAssessment = null;
    bundleSelectionVersion += 1;
    $("admin-bundle-export").disabled = true;
    $("admin-bundle-result").textContent = "Bestanden geselecteerd; controle nog niet uitgevoerd.";
  });
}

$("admin-bundle-check").addEventListener("click", async () => {
  if (!authenticated || busy) return;
  bundleAssessment = null;
  $("admin-bundle-export").disabled = true;
  const output = $("admin-bundle-result");
  const handoff = $("admin-bundle-handoff").files?.[0];
  const report = $("admin-bundle-report").files?.[0];
  if (!handoff || !report || handoff.size < 1 || report.size < 1 ||
      handoff.size > 16384 || report.size > 16384) {
    output.textContent = "GEWEIGERD / Kies twee niet-lege JSON-bestanden van elk maximaal 16 KB.";
    return;
  }
  const adminName = $("admin-name").textContent;
  const selectedVersion = bundleSelectionVersion;
  try {
    const [handoffBytes, reportBytes] = await Promise.all([handoff.arrayBuffer(), report.arrayBuffer()]);
    const [handoffDigest, reportDigest] = await Promise.all([
      crypto.subtle.digest("SHA-256", handoffBytes), crypto.subtle.digest("SHA-256", reportBytes),
    ]);
    if (!authenticated || $("admin-name").textContent !== adminName ||
        bundleSelectionVersion !== selectedVersion) {
      output.textContent = "SESSIE OF BESTANDSKEUZE GEWIJZIGD / Controleer opnieuw.";
      return;
    }
    const hex = (digest) => Array.from(new Uint8Array(digest),
      (byte) => byte.toString(16).padStart(2, "0")).join("");
    const handoffSha256 = hex(handoffDigest);
    const reportSha256 = hex(reportDigest);
    const decoder = new TextDecoder("utf-8", { fatal: true });
    const transfer = JSON.parse(decoder.decode(handoffBytes));
    const review = JSON.parse(decoder.decode(reportBytes));
    const valid = transfer && typeof transfer === "object" && !Array.isArray(transfer) &&
      transfer.schema === "palaco.pp.one.review-handoff.v0" &&
      transfer.reference === "PP-RECOVERY-002" &&
      transfer.authorization === "HOLD" && transfer.accessDecision === "DENY" &&
      transfer.identityVerification === "NOT_VERIFIED" &&
      transfer.issuance === "NOT_AUTHORIZED" &&
      transfer.provenance === "UNSIGNED_USER_CONTROLLED_FILE" &&
      review && typeof review === "object" && !Array.isArray(review) &&
      review.schema === "palaco.pp.manual-review.v0" &&
      review.evidenceReference === "PP-RECOVERY-002" &&
      review.structuralStatus === "CLIENT_STRUCTURE_RECOGNIZED_UNTRUSTED" &&
      review.fileSha256 === handoffSha256 &&
      review.verification === "NOT_VERIFIED" && review.reviewDecision === "HOLD" &&
      review.authorization === "HOLD" && review.accessDecision === "DENY" &&
      review.issuance === "NOT_AUTHORIZED";
    if (!valid) {
      output.textContent = "BINDING AFGEWEZEN / De vingerafdruk of HOLD-contractvelden komen niet overeen. Geen index aangemaakt.";
      return;
    }
    bundleAssessment = {
      schema: "palaco.pp.evidence-index.v0",
      reference: "PP-RECOVERY-002",
      createdAt: new Date().toISOString(),
      linkage: "HASH_MATCH_UNTRUSTED_CLIENT_OBSERVATION",
      handoffSha256, reportSha256,
      verification: "NOT_VERIFIED", reviewDecision: "HOLD",
      authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
      note: "Geen digitale handtekening, onafhankelijke bronverificatie of accountkoppeling.",
    };
    $("admin-bundle-export").disabled = false;
    output.textContent = "LOKALE HASHBINDING KOMT OVEREEN / Beide bestanden zijn gekoppeld, maar blijven onvertrouwd. HOLD / DENY.";
  } catch (error) {
    output.textContent = "ONGELDIG / Bestanden konden niet veilig worden gelezen. Geen index aangemaakt.";
  }
});

$("admin-bundle-export").addEventListener("click", () => {
  if (!authenticated || busy || !bundleAssessment) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(bundleAssessment, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-evidence-index-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("admin-bundle-result").textContent = "Bewijsindex aangeboden als lokale download. Autorisatie blijft HOLD / DENY.";
});

for (const id of ["admin-chain-handoff", "admin-chain-report", "admin-chain-index"]) {
  $(id).addEventListener("change", () => {
    chainSelectionVersion += 1;
    chainAssessment = null;
    $("admin-chain-export").disabled = true;
    $("admin-chain-result").textContent = "Bestandskeuze gewijzigd; controle nog niet uitgevoerd. HOLD / DENY.";
  });
}

$("admin-chain-check").addEventListener("click", async () => {
  if (!authenticated || busy) return;
  chainAssessment = null;
  $("admin-chain-export").disabled = true;
  const output = $("admin-chain-result");
  const files = ["admin-chain-handoff", "admin-chain-report", "admin-chain-index"]
    .map((id) => $(id).files?.[0]);
  if (files.some((file) => !file || file.size < 1 || file.size > 16384)) {
    output.textContent = "GEWEIGERD / Selecteer drie niet-lege JSON-bestanden van elk maximaal 16 KB. HOLD / DENY.";
    return;
  }
  const selectedVersion = chainSelectionVersion;
  const adminName = $("admin-name").textContent;
  output.textContent = "Lokale bestandsvingerafdrukken worden vergeleken. HOLD / DENY.";
  try {
    const bytes = await Promise.all(files.map((file) => file.arrayBuffer()));
    const digests = await Promise.all(bytes
      .map((data) => crypto.subtle.digest("SHA-256", data)));
    if (!authenticated || busy || chainSelectionVersion !== selectedVersion ||
        $("admin-name").textContent !== adminName) {
      output.textContent = "SESSIE OF BESTANDSKEUZE GEWIJZIGD / Controle opnieuw vereist. HOLD / DENY.";
      return;
    }
    const decoder = new TextDecoder("utf-8", { fatal: true });
    const [handoff, report, index] = bytes.map((data) => JSON.parse(decoder.decode(data)));
    const plain = (value) => value && typeof value === "object" && !Array.isArray(value);
    const hex = (digest) => Array.from(new Uint8Array(digest),
      (byte) => byte.toString(16).padStart(2, "0")).join("");
    const handoffSha256 = hex(digests[0]);
    const reportSha256 = hex(digests[1]);
    const indexSha256 = hex(digests[2]);
    const expectedIndex = {
      schema: "palaco.pp.evidence-index.v0", reference: "PP-RECOVERY-002",
      linkage: "HASH_MATCH_UNTRUSTED_CLIENT_OBSERVATION",
      verification: "NOT_VERIFIED", reviewDecision: "HOLD", authorization: "HOLD",
      accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
      note: "Geen digitale handtekening, onafhankelijke bronverificatie of accountkoppeling.",
    };
    const valid = plain(handoff) && plain(report) && plain(index) &&
      handoff.schema === "palaco.pp.one.review-handoff.v0" &&
      handoff.reference === "PP-RECOVERY-002" &&
      handoff.authorization === "HOLD" && handoff.accessDecision === "DENY" &&
      handoff.identityVerification === "NOT_VERIFIED" &&
      handoff.issuance === "NOT_AUTHORIZED" &&
      handoff.provenance === "UNSIGNED_USER_CONTROLLED_FILE" &&
      report.schema === "palaco.pp.manual-review.v0" &&
      report.evidenceReference === "PP-RECOVERY-002" &&
      report.structuralStatus === "CLIENT_STRUCTURE_RECOGNIZED_UNTRUSTED" &&
      report.fileSha256 === handoffSha256 &&
      report.verification === "NOT_VERIFIED" && report.reviewDecision === "HOLD" &&
      report.authorization === "HOLD" && report.accessDecision === "DENY" &&
      report.issuance === "NOT_AUTHORIZED" &&
      Object.keys(index).length === 12 &&
      Object.entries(expectedIndex).every(([key, value]) => index[key] === value) &&
      typeof index.createdAt === "string" &&
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/.test(index.createdAt) &&
      Number.isFinite(Date.parse(index.createdAt)) &&
      index.handoffSha256 === handoffSha256 && index.reportSha256 === reportSha256;
    if (valid) {
      chainAssessment = {
        schema: "palaco.pp.chain-observation.v0",
        reference: "PP-RECOVERY-002",
        capturedAt: new Date().toISOString(),
        outcome: "CLIENT_THREE_FILE_HASH_MATCH_UNTRUSTED",
        handoffSha256, reportSha256, indexSha256,
        verification: "NOT_VERIFIED", reviewDecision: "HOLD",
        authorization: "HOLD", accessDecision: "DENY",
        issuance: "NOT_AUTHORIZED", provenance: "UNSIGNED_LOCAL_BROWSER_OBSERVATION",
      };
      $("admin-chain-export").disabled = false;
      output.textContent = "DRIE HASHVERWIJZINGEN CONSISTENT / Alleen lokale, onvertrouwde bestandsbinding. Geen identiteitsbewijs. HOLD / DENY.";
    } else {
      output.textContent = "KETEN AFGEWEZEN / Schema, referenties, hashes of HOLD-contractvelden wijken af. HOLD / DENY.";
    }
  } catch (_error) {
    output.textContent = "ONGELDIG / Ketenbestanden konden niet veilig worden verwerkt. HOLD / DENY.";
  }
});
$("admin-chain-export").addEventListener("click", () => {
  if (!authenticated || busy || !chainAssessment) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(chainAssessment, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-chain-observation-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("admin-chain-result").textContent = "Lokaal ketenrapport aangeboden als download; geen onafhankelijke verificatie. HOLD / DENY.";
});

for (const scenario of Object.keys(review044Expectations)) {
  const option = document.createElement("option");
  option.value = scenario;
  option.textContent = scenario.replaceAll("_", " ");
  $("admin-review044-scenario").append(option);
}

$("admin-review044-scenario").addEventListener("change", () => {
  const row = review044Observations.get($("admin-review044-scenario").value);
  $("admin-review044-observed").value = row?.observed_result || "NOT_OBSERVED";
});

$("admin-review044-record").addEventListener("click", () => {
  if (!authenticated || busy) return;
  const scenario = $("admin-review044-scenario").value;
  const result = $("admin-review044-observed").value;
  if (!Object.hasOwn(review044Expectations, scenario) || ![
    "NOT_OBSERVED", "FOUR_FILE_HASH_MATCH_UNTRUSTED", "PP_CHAIN_INVALID", "UNEXPECTED_ERROR",
  ].includes(result)) return;
  // The timestamp is attached to the explicit owner action, never fabricated for missing rows.
  review044Observations.set(scenario, {
    observed_result: result,
    observed_at: new Date().toISOString(),
  });
  $("admin-review044-export").disabled = false;
  $("admin-review044-result").textContent = `${review044Observations.size} van 9 scenario's zelf gerapporteerd. Geen onafhankelijke verificatie. HOLD / DENY.`;
});

$("admin-review044-export").addEventListener("click", () => {
  if (!authenticated || busy || review044Observations.size === 0) return;
  const report = {
    schema: "palaco.pp.review-044-self-report.v0",
    reference: "PP-RECOVERY-002",
    recordedAt: new Date().toISOString(),
    provenance: "UNSIGNED_OWNER_SELF_REPORT_NOT_INDEPENDENTLY_VERIFIED",
    scenarios: Object.entries(review044Expectations).map(([scenario, expected]) => {
      const observation = review044Observations.get(scenario);
      const result = observation?.observed_result || "NOT_OBSERVED";
      return {
        scenario_id: scenario,
        expected_result: expected,
        observed_result: result,
        observed_at: observation?.observed_at || null,
        evidence_kind: observation ? "SELF_REPORTED" : "NO_OBSERVATION",
        comparison: !observation || result === "NOT_OBSERVED"
          ? "NOT_ASSESSED" : result === expected ? "MATCH_CLAIMED" : "MISMATCH_CLAIMED",
      };
    }),
    verification: "NOT_VERIFIED", reviewDecision: "HOLD",
    authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-review-044-self-reported-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("admin-review044-result").textContent = "Zelfrapport aangeboden als lokale download. Controleer of het bestand is opgeslagen; HOLD / DENY.";
});

for (const scenario of Object.keys(review044TechnicalExpectations)) {
  const option = document.createElement("option");
  option.value = scenario;
  option.textContent = scenario.replaceAll("_", " ");
  $("admin-review044-owner-scenario").append(option);
}

$("admin-review044-tech-file").addEventListener("change", async () => {
  const version = ++review044TechnicalSelectionVersion;
  const file = $("admin-review044-tech-file").files?.[0];
  review044TechnicalAssessment = null;
  review044OwnerMarks.clear();
  $("admin-review044-owner-mark").value = "NOT_REVIEWED";
  $("admin-review044-owner-record").disabled = true;
  $("admin-review044-owner-export").disabled = true;
  const output = $("admin-review044-tech-status");
  output.textContent = "Bestand lokaal lezen; geen verificatie. HOLD / DENY.";
  if (!authenticated || !file || file.size === 0 || file.size > 32 * 1024) {
    output.textContent = "Geen geldig bestand gekozen (maximaal 32 KB). HOLD / DENY.";
    return;
  }
  try {
    const bytes = await file.arrayBuffer();
    if (version !== review044TechnicalSelectionVersion || !authenticated) return;
    const decoded = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    const comparison = assessReview044TechnicalBrowserReport(JSON.parse(decoded));
    const hashBytes = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
    if (version !== review044TechnicalSelectionVersion || !authenticated) return;
    const digest = [...hashBytes].map((byte) => byte.toString(16).padStart(2, "0")).join("");
    review044TechnicalAssessment = { digest, comparison };
    $("admin-review044-owner-record").disabled = false;
    $("admin-review044-owner-export").disabled = false;
    output.textContent = `13 scenario's structureel herkenbaar. ${comparison}. Alleen browserindicatie; dubbele JSON-sleutels worden hier niet gecontroleerd. HOLD / DENY.`;
  } catch (_error) {
    if (version !== review044TechnicalSelectionVersion || !authenticated) return;
    output.textContent = "Technisch bestand niet bruikbaar voor dit werkblad. Controleer later met de strengere Python-beoordelaar. HOLD / DENY.";
  }
});

$("admin-review044-owner-scenario").addEventListener("change", () => {
  const mark = review044OwnerMarks.get($("admin-review044-owner-scenario").value);
  $("admin-review044-owner-mark").value = mark || "NOT_REVIEWED";
});

$("admin-review044-owner-record").addEventListener("click", () => {
  if (!authenticated || busy || !review044TechnicalAssessment) return;
  const scenario = $("admin-review044-owner-scenario").value;
  const mark = $("admin-review044-owner-mark").value;
  if (!Object.hasOwn(review044TechnicalExpectations, scenario)
    || !["NOT_REVIEWED", "OBSERVED_AS_REPORTED", "DISCREPANCY_REPORTED"].includes(mark)) return;
  review044OwnerMarks.set(scenario, mark);
  const reviewed = [...review044OwnerMarks.values()].filter((value) => value !== "NOT_REVIEWED").length;
  $("admin-review044-tech-status").textContent = `${reviewed} van 13 scenario's door eigenaar gemarkeerd; uitsluitend SELF_REPORTED. HOLD / DENY.`;
});

$("admin-review044-owner-export").addEventListener("click", () => {
  if (!authenticated || busy || !review044TechnicalAssessment) return;
  const rows = Object.keys(review044TechnicalExpectations).map((name) => ({
    scenario_id: name,
    owner_mark: review044OwnerMarks.get(name) || "NOT_REVIEWED",
    evidence_kind: review044OwnerMarks.has(name) ? "SELF_REPORTED" : "NO_OBSERVATION",
  }));
  const report = {
    schema: "palaco.pp.review-044-owner-worksheet.v0",
    reference: "PP-RECOVERY-002",
    technicalReportSha256: review044TechnicalAssessment.digest,
    sourceTrust: "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
    technicalComparison: review044TechnicalAssessment.comparison,
    executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
    ownerMarks: rows,
    ownerMarkedCount: rows.filter((row) => row.owner_mark !== "NOT_REVIEWED").length,
    ownerDiscrepancyCount: rows.filter((row) => row.owner_mark === "DISCREPANCY_REPORTED").length,
    independentVerification: "NOT_VERIFIED", reviewDecision: "HOLD",
    identityBinding: "NOT_ESTABLISHED", authorization: "HOLD",
    accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
  };
  downloadReview044OwnerJson(report);
  $("admin-review044-tech-status").textContent = "Werkblad als lokale download aangeboden. Controleer zelf of het is opgeslagen. HOLD / DENY.";
});

function readReview044OwnerBrowserWorksheet(owner, technicalDigest, comparison) {
  const fields = ["schema", "reference", "technicalReportSha256", "sourceTrust",
    "technicalComparison", "executionProvenance", "ownerMarks", "ownerMarkedCount",
    "ownerDiscrepancyCount", "independentVerification", "reviewDecision",
    "identityBinding", "authorization", "accessDecision", "issuance"];
  const required = {
    schema: "palaco.pp.review-044-owner-worksheet.v0",
    reference: "PP-RECOVERY-002", technicalReportSha256: technicalDigest,
    sourceTrust: "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
    technicalComparison: comparison, executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
    independentVerification: "NOT_VERIFIED", reviewDecision: "HOLD",
    identityBinding: "NOT_ESTABLISHED", authorization: "HOLD",
    accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
  };
  if (!exactFields(owner, fields)
    || Object.entries(required).some(([key, value]) => owner[key] !== value)
    || !Array.isArray(owner.ownerMarks) || owner.ownerMarks.length !== 13) {
    throw new Error("OWNER_STRUCTURE_INVALID");
  }
  let marked = 0;
  let discrepancies = 0;
  const names = Object.keys(review044TechnicalExpectations);
  for (let i = 0; i < names.length; i += 1) {
    const row = owner.ownerMarks[i];
    if (!exactFields(row, ["scenario_id", "owner_mark", "evidence_kind"])
      || row.scenario_id !== names[i]
      || !["NOT_REVIEWED", "OBSERVED_AS_REPORTED", "DISCREPANCY_REPORTED"].includes(row.owner_mark)
      || !["SELF_REPORTED", "NO_OBSERVATION"].includes(row.evidence_kind)
      || (row.evidence_kind === "NO_OBSERVATION" && row.owner_mark !== "NOT_REVIEWED")) {
      throw new Error("OWNER_MARK_INVALID");
    }
    marked += row.owner_mark !== "NOT_REVIEWED" ? 1 : 0;
    discrepancies += row.owner_mark === "DISCREPANCY_REPORTED" ? 1 : 0;
  }
  if (!Number.isInteger(owner.ownerMarkedCount) || owner.ownerMarkedCount !== marked
    || !Number.isInteger(owner.ownerDiscrepancyCount)
    || owner.ownerDiscrepancyCount !== discrepancies) {
    throw new Error("OWNER_COUNTS_INVALID");
  }
  return { marked, discrepancies };
}

function resetReview044Index(message = "Bestandskeuze gewijzigd; controle opnieuw nodig. HOLD / DENY.") {
  review044IndexSelectionVersion += 1;
  review044IndexAssessment = null;
  $("admin-review044-index-export").disabled = true;
  $("admin-review044-index-result").textContent = message;
}

for (const id of ["admin-review044-index-tech", "admin-review044-index-owner"]) {
  $(id).addEventListener("change", () => resetReview044Index());
}

$("admin-review044-index-check").addEventListener("click", async () => {
  if (!authenticated || busy) return;
  resetReview044Index("Twee lokale bestanden worden beoordeeld. Geen herkomstverificatie. HOLD / DENY.");
  const version = review044IndexSelectionVersion;
  const techFile = $("admin-review044-index-tech").files?.[0];
  const ownerFile = $("admin-review044-index-owner").files?.[0];
  const output = $("admin-review044-index-result");
  if (!techFile || !ownerFile || !techFile.size || !ownerFile.size
    || techFile.size > 32 * 1024 || ownerFile.size > 32 * 1024) {
    output.textContent = "Kies beide JSON-bestanden (elk maximaal 32 KB). HOLD / DENY.";
    return;
  }
  try {
    const [technicalBytes, ownerBytes] = await Promise.all([techFile.arrayBuffer(), ownerFile.arrayBuffer()]);
    if (version !== review044IndexSelectionVersion || !authenticated) return;
    const decoder = new TextDecoder("utf-8", { fatal: true });
    const comparison = assessReview044TechnicalBrowserReport(JSON.parse(decoder.decode(technicalBytes)));
    const digest = async (bytes) => {
      const hash = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
      return [...hash].map((byte) => byte.toString(16).padStart(2, "0")).join("");
    };
    const [technicalDigest, ownerDigest] = await Promise.all([digest(technicalBytes), digest(ownerBytes)]);
    if (version !== review044IndexSelectionVersion || !authenticated) return;
    const counts = readReview044OwnerBrowserWorksheet(
      JSON.parse(decoder.decode(ownerBytes)), technicalDigest, comparison);
    review044IndexAssessment = {
      schema: "palaco.pp.review-044-owner-evidence-index.v0",
      reference: "PP-RECOVERY-002", technicalReportSha256: technicalDigest,
      ownerWorksheetSha256: ownerDigest, binding: "TWO_FILE_HASH_MATCH_UNTRUSTED",
      technicalComparison: comparison, ownerMarkedCount: counts.marked,
      ownerDiscrepancyCount: counts.discrepancies,
      sourceTrust: "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
      independentVerification: "NOT_VERIFIED", reviewDecision: "HOLD",
      identityBinding: "NOT_ESTABLISHED", authorization: "HOLD",
      accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
    };
    $("admin-review044-index-export").disabled = false;
    output.textContent = "Twee bestanden consistent volgens browserindicatie. Dubbele JSON-sleutels niet uitgesloten; Python-controle blijft noodzakelijk. HOLD / DENY.";
  } catch (_error) {
    if (version !== review044IndexSelectionVersion || !authenticated) return;
    output.textContent = "BESTANDSBINDING GEWEIGERD: inhoud, structuur, hashes of HOLD-contract wijken af. HOLD / DENY.";
  }
});

$("admin-review044-index-export").addEventListener("click", () => {
  if (!authenticated || busy || !review044IndexAssessment) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(review044IndexAssessment, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-review-044-owner-evidence-index-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("admin-review044-index-result").textContent = "Bewijsindex als lokale download aangeboden. Bewaren zelf controleren. HOLD / DENY.";
});

function resetReview044Dossier(message = "Bestandskeuze gewijzigd; eerdere beoordeling vervallen. HOLD / DENY.") {
  review044DossierSelectionVersion += 1;
  review044DossierAssessment = null;
  $("admin-review044-dossier-export").disabled = true;
  $("admin-review044-dossier-result").textContent = message;
  resetReview044Registry();
}

for (const id of ["admin-review044-dossier-tech", "admin-review044-dossier-owner",
  "admin-review044-dossier-index"]) {
  $(id).addEventListener("change", () => resetReview044Dossier());
}

$("admin-review044-dossier-check").addEventListener("click", async () => {
  if (!authenticated || busy) return;
  resetReview044Dossier("Drie bestanden worden uitsluitend lokaal gelezen. HOLD / DENY.");
  const version = review044DossierSelectionVersion;
  const files = ["admin-review044-dossier-tech", "admin-review044-dossier-owner",
    "admin-review044-dossier-index"].map((id) => $(id).files?.[0]);
  const output = $("admin-review044-dossier-result");
  if (files.some((file, i) => !file || !file.size || file.size > (i === 2 ? 16 : 32) * 1024)) {
    output.textContent = "Selecteer drie JSON-bestanden binnen de aangegeven groottelimieten. HOLD / DENY.";
    return;
  }
  try {
    const buffers = await Promise.all(files.map((file) => file.arrayBuffer()));
    if (version !== review044DossierSelectionVersion || !authenticated) return;
    const decoder = new TextDecoder("utf-8", { fatal: true });
    const [technical, owner, suppliedIndex] = buffers.map((bytes) => JSON.parse(decoder.decode(bytes)));
    const comparison = assessReview044TechnicalBrowserReport(technical);
    const hashes = await Promise.all(buffers.slice(0, 2).map(async (bytes) => {
      const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
      return [...digest].map((byte) => byte.toString(16).padStart(2, "0")).join("");
    }));
    if (version !== review044DossierSelectionVersion || !authenticated) return;
    const counts = readReview044OwnerBrowserWorksheet(owner, hashes[0], comparison);
    const expectedIndex = {
      schema: "palaco.pp.review-044-owner-evidence-index.v0", reference: "PP-RECOVERY-002",
      technicalReportSha256: hashes[0], ownerWorksheetSha256: hashes[1],
      binding: "TWO_FILE_HASH_MATCH_UNTRUSTED", technicalComparison: comparison,
      ownerMarkedCount: counts.marked, ownerDiscrepancyCount: counts.discrepancies,
      sourceTrust: "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
      independentVerification: "NOT_VERIFIED", reviewDecision: "HOLD",
      identityBinding: "NOT_ESTABLISHED", authorization: "HOLD",
      accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
    };
    if (!exactFields(suppliedIndex, Object.keys(expectedIndex))
      || Object.keys(expectedIndex).some((key) => suppliedIndex[key] !== expectedIndex[key])) {
      throw new Error("DOSSIER_INDEX_INVALID");
    }
    review044DossierAssessment = {
      schema: "palaco.pp.review-044-owner-dossier-assessment.v0",
      reference: "PP-RECOVERY-002", binding: "THREE_FILE_HASH_MATCH_UNTRUSTED",
      technicalReportSha256: hashes[0], ownerWorksheetSha256: hashes[1],
      technicalComparison: comparison, ownerMarkedCount: counts.marked,
      ownerDiscrepancyCount: counts.discrepancies,
      sourceTrust: "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
      executionProvenance: "NOT_INDEPENDENTLY_ESTABLISHED",
      independentVerification: "NOT_VERIFIED", reviewDecision: "HOLD",
      identityBinding: "NOT_ESTABLISHED", authorization: "HOLD",
      accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
    };
    $("admin-review044-dossier-export").disabled = false;
    $("admin-review044-registry-add").disabled = false;
    output.textContent = "Drie bestanden consistent volgens de browserindicatie. Strikte Python-controle nog nodig; HOLD / DENY.";
  } catch (_error) {
    if (version !== review044DossierSelectionVersion || !authenticated) return;
    output.textContent = "DOSSIER GEWEIGERD: ongeldige structuur, inhoud of bestandsbinding. HOLD / DENY.";
  }
});

$("admin-review044-dossier-export").addEventListener("click", () => {
  if (!authenticated || busy || !review044DossierAssessment) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(review044DossierAssessment, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-review-044-owner-dossier-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("admin-review044-dossier-result").textContent = "Dossierbeoordeling als download aangeboden. Opslag zelf bevestigen. HOLD / DENY.";
});

function resetReview044Registry() {
  review044RegistryVersion += 1;
  review044RegistryDraft = null;
  $("admin-review044-registry-export").disabled = true;
  $("admin-review044-registry-add").disabled = !review044DossierAssessment;
  $("admin-review044-registry-result").textContent = "Registerkeuze of dossier gewijzigd. Nieuwe beoordeling nodig. HOLD / DENY.";
}

$("admin-review044-registry-file").addEventListener("change", () => resetReview044Registry());

const review044RegistryRequired = Object.freeze({
  schema: "palaco.pp.review-044-owner-registry.v0", reference: "PP-RECOVERY-002",
  verification: "NOT_VERIFIED", authorization: "HOLD", accessDecision: "DENY",
});
const review044RegistryRowFields = ["sequence", "previousEntrySha256", "entrySha256",
  "technicalReportSha256", "ownerWorksheetSha256", "evidenceIndexSha256",
  "binding", "evidenceKind", "verification", "authorization", "accessDecision", "issuance"];
const review044RegistryRowRequired = Object.freeze({
  binding: "THREE_FILE_HASH_MATCH_UNTRUSTED",
  evidenceKind: "IMPORTED_UNATTESTED_LOCAL_DOSSIER", verification: "NOT_VERIFIED",
  authorization: "HOLD", accessDecision: "DENY", issuance: "NOT_AUTHORIZED",
});
const isSha256Hex = (value) => typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
const review044Canonical = (value) => JSON.stringify(Object.fromEntries(
  Object.keys(value).sort().map((key) => [key, value[key]])));
async function review044Hash(bytes) {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return [...digest].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

$("admin-review044-registry-add").addEventListener("click", async () => {
  if (!authenticated || busy || !review044DossierAssessment) return;
  resetReview044Registry();
  const version = review044RegistryVersion;
  const dossierVersion = review044DossierSelectionVersion;
  const indexFile = $("admin-review044-dossier-index").files?.[0];
  const registryFile = $("admin-review044-registry-file").files?.[0];
  const output = $("admin-review044-registry-result");
  if (!indexFile || (registryFile && (!registryFile.size || registryFile.size > 256 * 1024))) {
    output.textContent = "Registerbestand ongeldig of dossierselectie ontbreekt. HOLD / DENY.";
    return;
  }
  try {
    const [indexBytes, registryBytes] = await Promise.all([
      indexFile.arrayBuffer(), registryFile ? registryFile.arrayBuffer() : Promise.resolve(null),
    ]);
    if (version !== review044RegistryVersion || dossierVersion !== review044DossierSelectionVersion || !authenticated) return;
    const decode = new TextDecoder("utf-8", { fatal: true });
    const snapshot = registryBytes ? JSON.parse(decode.decode(registryBytes)) : {
      ...review044RegistryRequired, entries: [],
    };
    if (!exactFields(snapshot, [...Object.keys(review044RegistryRequired), "entries"])
      || Object.entries(review044RegistryRequired).some(([key, value]) => snapshot[key] !== value)
      || !Array.isArray(snapshot.entries) || snapshot.entries.length >= 256) {
      throw new Error("REGISTRY_HEADER_INVALID");
    }
    let previous = null;
    const identities = new Set();
    for (let i = 0; i < snapshot.entries.length; i += 1) {
      const row = snapshot.entries[i];
      if (!exactFields(row, review044RegistryRowFields)
        || !Number.isInteger(row.sequence) || row.sequence !== i + 1
        || row.previousEntrySha256 !== previous
        || Object.entries(review044RegistryRowRequired).some(([key, value]) => row[key] !== value)
        || ["entrySha256", "technicalReportSha256", "ownerWorksheetSha256",
          "evidenceIndexSha256"].some((field) => !isSha256Hex(row[field]))) {
        throw new Error("REGISTRY_ROW_INVALID");
      }
      const unsigned = Object.fromEntries(Object.entries(row).filter(([key]) => key !== "entrySha256"));
      const actual = await review044Hash(new TextEncoder().encode(review044Canonical(unsigned)));
      if (row.entrySha256 !== actual) throw new Error("REGISTRY_CHAIN_INVALID");
      const identity = [row.technicalReportSha256, row.ownerWorksheetSha256, row.evidenceIndexSha256].join(":");
      if (identities.has(identity)) throw new Error("REGISTRY_DUPLICATE");
      identities.add(identity);
      previous = row.entrySha256;
    }
    const assessment = review044DossierAssessment;
    const indexDigest = await review044Hash(indexBytes);
    if (version !== review044RegistryVersion || dossierVersion !== review044DossierSelectionVersion || !authenticated) return;
    const identity = [assessment.technicalReportSha256, assessment.ownerWorksheetSha256, indexDigest].join(":");
    if (identities.has(identity)) throw new Error("REGISTRY_DUPLICATE");
    const newRow = {
      sequence: snapshot.entries.length + 1, previousEntrySha256: previous,
      technicalReportSha256: assessment.technicalReportSha256,
      ownerWorksheetSha256: assessment.ownerWorksheetSha256,
      evidenceIndexSha256: indexDigest, ...review044RegistryRowRequired,
    };
    newRow.entrySha256 = await review044Hash(new TextEncoder().encode(review044Canonical(newRow)));
    if (version !== review044RegistryVersion || dossierVersion !== review044DossierSelectionVersion || !authenticated) return;
    snapshot.entries.push(newRow);
    const serialized = JSON.stringify(snapshot, null, 2) + "\n";
    if (new TextEncoder().encode(serialized).length > 256 * 1024) throw new Error("REGISTRY_TOO_LARGE");
    review044RegistryDraft = serialized;
    $("admin-review044-registry-export").disabled = false;
    output.textContent = `${snapshot.entries.length} lokale dossierverwijzing(en) voorbereid. Ongetekend en onvertrouwd; download vereist. HOLD / DENY.`;
  } catch (_error) {
    if (version !== review044RegistryVersion || !authenticated) return;
    output.textContent = "REGISTER GEWEIGERD: schema, volgorde, hashketen of dubbele dossierverwijzing ongeldig. HOLD / DENY.";
  }
});

$("admin-review044-registry-export").addEventListener("click", () => {
  if (!authenticated || busy || !review044RegistryDraft) return;
  const url = URL.createObjectURL(new Blob([review044RegistryDraft], { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-pp-review-044-owner-registry-hold.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  $("admin-review044-registry-result").textContent = "Registerversie als download aangeboden. Bevestig zelf de opslag. HOLD / DENY.";
});
action(loadSession);
