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

function notice(message, error = false) {
  $("admin-notice").textContent = message;
  $("admin-notice").classList.toggle("error", error);
}

function showLogin() {
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
action(loadSession);
