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

function clearReview() {
  reviewAssessment = null;
  bundleAssessment = null;
  bundleSelectionVersion += 1;
  chainSelectionVersion += 1;
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
    $("admin-chain-result").textContent = "Bestandskeuze gewijzigd; controle nog niet uitgevoerd. HOLD / DENY.";
  });
}

$("admin-chain-check").addEventListener("click", async () => {
  if (!authenticated || busy) return;
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
    const digests = await Promise.all(bytes.slice(0, 2)
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
    output.textContent = valid
      ? "DRIE HASHVERWIJZINGEN CONSISTENT / Alleen lokale, onvertrouwde bestandsbinding. Geen identiteitsbewijs. HOLD / DENY."
      : "KETEN AFGEWEZEN / Schema, referenties, hashes of HOLD-contractvelden wijken af. HOLD / DENY.";
  } catch (_error) {
    output.textContent = "ONGELDIG / Ketenbestanden konden niet veilig worden verwerkt. HOLD / DENY.";
  }
});
action(loadSession);
