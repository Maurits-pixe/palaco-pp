"use strict";

const $ = (id) => document.getElementById(id);
const colorLabels = { blue: "Blauw", red: "Rood", green: "Groen", yellow: "Geel" };
const messages = {
  PP_ALREADY_SELECTED: "Je hebt al definitief gekozen. Een tweede keuze is niet toegestaan.",
  PP_OPTION_INVALID: "Deze optie is niet beschikbaar voor jouw consumer-ID.",
  PP_SELECTION_REVOKED: "Dit nummer is al ingetrokken. Je kunt niet opnieuw kiezen.",
  PP_SELECTION_UNKNOWN: "De status kan niet betrouwbaar worden vastgesteld. Er wordt niets geactiveerd. Probeer opnieuw te laden.",
  PP_NUMBER_CONFLICT: "Er konden geen tien unieke opties worden aangemaakt. Probeer het opnieuw.",
  PP_SESSION_REQUIRED: "Je demosessie is niet geldig. Gebruik de oorspronkelijke browser en database. Wis geen cookies om een bestaande keuze te herstellen.",
  PP_ORIGIN_DENIED: "Dit verzoek komt niet van de lokale prototypepagina.",
  PP_REQUEST_INVALID: "Het verzoek is ongeldig. Laad de pagina opnieuw.",
  PP_AUTH_REQUIRED: "Meld je aan om je P.P.-registratie te bekijken.",
  PP_USERNAME_INVALID: "Kies een gebruikersnaam van 3–32 tekens: letters, cijfers, punt, koppelteken of underscore.",
  PP_USERNAME_TAKEN: "Deze gebruikersnaam is al in gebruik.",
  PP_PASSWORD_INVALID: "Gebruik een wachtwoord van 12–128 tekens.",
  PP_CREDENTIALS_INVALID: "Gebruikersnaam of wachtwoord is onjuist.",
  PP_LOGIN_RATE_LIMITED: "Te veel mislukte aanmeldpogingen. Probeer het over 15 minuten opnieuw.",
  PP_ACCOUNT_EXISTS: "Er is al een account aan deze registratie gekoppeld. Meld je aan.",
  PP_MEMORY_INVALID: "Controleer de titel, notitie en tags. Titel maximaal 120 tekens, notitie maximaal 5000 en maximaal 8 tags van 24 tekens.",
  PP_MEMORY_LIMIT: "Je geheugenbank bevat het maximum van 100 notities. Verwijder eerst een notitie.",
  PP_MEMORY_UNKNOWN: "Deze notitie bestaat niet meer of de opgeslagen gegevens kunnen niet veilig worden gelezen.",
};
let selected = null;
let current = null;
let mode = "select";
let authMode = "login";
let sessionState = null;
let historyEvents = [];
let memoryEntries = [];
let memoryToDelete = null;
let busy = false;
let mailAvailable = false;
messages.PP_EMAIL_INVALID = "Vul een geldig e-mailadres in (zonder internationale tekens), of laat het veld leeg.";
messages.PP_EMAIL_UNAVAILABLE = "E-mail is niet geconfigureerd. Kies opnieuw zonder e-mailadres, of laat de beheerder SMTP instellen.";

function format(number) {
  return `${number.slice(0, 3)} ${number.slice(3, 6)} ${number.slice(6)}`;
}

function notice(text, error = false) {
  $("notice").textContent = text;
  $("notice").classList.toggle("error", error);
}

async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(messages[data.error] || `Verzoek geweigerd (${data.error || response.status}).`);
  return data;
}

function setBusy(value) {
  busy = value;
  $("number-fieldset").disabled = value;
  $("review").disabled = value || !selected;
  $("confirm").disabled = value;
  $("cancel").disabled = value;
  $("revoke").disabled = value;
  $("retry").disabled = value;
  $("auth-submit").disabled = value;
  $("auth-switch").disabled = value;
  $("logout").disabled = value;
  $("memory-save").disabled = value
    || (memoryEntries.length >= 100 && !$("memory-id").value);
  $("memory-reset").disabled = value;
}

function showError(error) {
  console.error(error);
  notice(error instanceof TypeError
    ? "Geen verbinding met de lokale server. Een keuze kan al verwerkt zijn: laad de status opnieuw voordat je verdergaat."
    : error.message, true);
  $("retry").hidden = false;
}

function renderOptions(options) {
  $("numbers").replaceChildren();
  options.forEach((option, index) => {
    const label = document.createElement("label");
    label.className = `number-option color-${option.color}`;
    label.dataset.testid = `pp-option-${index + 1}`;
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "pp-number";
    radio.value = option.id;
    radio.setAttribute("aria-label", `P.P.-nummer ${format(option.number)}, ${colorLabels[option.color]}`);
    const face = document.createElement("span");
    face.className = "number-face";
    const top = document.createElement("span");
    top.className = "option-top";
    top.textContent = `${String(index + 1).padStart(2, "0")} / ${colorLabels[option.color].toUpperCase()}`;
    const mark = document.createElement("span");
    mark.className = "radio-mark";
    mark.setAttribute("aria-hidden", "true");
    top.append(mark);
    const number = document.createElement("span");
    number.className = "number-value";
    number.textContent = format(option.number);
    face.append(top, number);
    label.append(radio, face);
    radio.addEventListener("change", () => {
      selected = option;
      $("preview-number").textContent = format(option.number);
      $("preview-label").textContent = "JOUW VOORKEUR / NOG NIET DEFINITIEF";
      $("review").disabled = false;
      $("step-two").classList.add("current");
    });
    $("numbers").append(label);
  });
}

function renderResult(state) {
  const revoked = state.status === "REVOKED";
  $("selection-panel").hidden = true;
  $("result-panel").hidden = false;
  $("preview-number").textContent = format(state.ppNumber);
  $("preview-label").textContent = revoked ? "INGETROKKEN / GEEN NIEUWE KEUZE" : "GEREGISTREERD / JOUW IDENTITEIT";
  $("result-badge").textContent = revoked ? "INGETROKKEN" : "GEREGISTREERD";
  $("result-title").textContent = revoked ? "Dit nummer is ingetrokken." : "Dit is jouw P.P.-nummer.";
  $("result-number").textContent = format(state.ppNumber);
  $("result-description").textContent = revoked
    ? "De registratie blijft bewaard. Dit nummer wordt niet hergebruikt en je kunt niet opnieuw kiezen."
    : "Je keuze is definitief opgeslagen. De overige negen opties zijn vervallen.";
  $("consumer-reference").textContent = `LOKALE CONSUMER-ID / ${state.consumerId}`;
  $("revoke").hidden = revoked;
  $("copy").hidden = revoked;
  $("step-three").classList.add("current");
  notice(revoked ? "P.P.-nummer ingetrokken. De historie blijft bewaard." : "Je P.P.-nummer is actief als lokale identificatie. Geen bel- of SMS-dienst.");
}

function renderHistory(events) {
  historyEvents = events;
  const list = $("history-events");
  list.replaceChildren();
  $("history-count").textContent = `${events.length} ${events.length === 1 ? "gebeurtenis" : "gebeurtenissen"}`;
  $("history-panel").hidden = events.length === 0;
  const labels = {
    OPTION_OFFERED: "Nummer aangeboden",
    NUMBER_SELECTED: "Nummer gekozen",
    NUMBER_REVOKED: "Nummer ingetrokken",
  };
  events.forEach((event) => {
    const item = document.createElement("li");
    item.className = `history-event history-${event.event.toLowerCase()}`;
    const marker = document.createElement("span");
    marker.className = "history-marker";
    marker.setAttribute("aria-hidden", "true");
    const content = document.createElement("div");
    content.className = "history-content";
    const heading = document.createElement("strong");
    heading.textContent = labels[event.event] || "Enginegebeurtenis";
    const detail = document.createElement("p");
    const number = event.detail.ppNumber;
    const color = colorLabels[event.detail.color];
    detail.textContent = [number ? format(number) : "", color || ""].filter(Boolean).join(" / ");
    const time = document.createElement("time");
    time.dateTime = event.createdAt;
    time.textContent = new Date(event.createdAt).toLocaleString("nl-NL");
    content.append(heading, detail, time);
    item.append(marker, content);
    list.append(item);
  });
}

function clearMemoryForm() {
  $("memory-form").reset();
  $("memory-id").value = "";
  $("memory-save").textContent = "Notitie opslaan";
  $("memory-save").disabled = memoryEntries.length >= 100;
  updateMemoryCharCount();
}

function updateMemoryCharCount() {
  $("memory-char-count").textContent = `${$("memory-content").value.length} / 5000`;
}

function renderMemory(data) {
  memoryEntries = data.entries;
  const list = $("memory-list");
  list.replaceChildren();
  $("memory-count").textContent = `${memoryEntries.length} / ${data.limit}`;
  $("memory-empty").hidden = memoryEntries.length > 0;
  $("memory-save").disabled = busy || (memoryEntries.length >= data.limit && !$("memory-id").value);
  $("memory-panel").hidden = false;
  memoryEntries.forEach((entry) => {
    const card = document.createElement("article");
    card.className = "memory-card";
    const top = document.createElement("div");
    top.className = "memory-card-top";
    const headingGroup = document.createElement("div");
    const heading = document.createElement("h4");
    heading.textContent = entry.title;
    const updated = document.createElement("time");
    updated.className = "memory-date";
    updated.dateTime = entry.updatedAt;
    updated.textContent = `Bijgewerkt ${new Date(entry.updatedAt).toLocaleString("nl-NL")}`;
    headingGroup.append(heading, updated);
    top.append(headingGroup);
    const content = document.createElement("p");
    content.className = "memory-card-content";
    content.textContent = entry.content;
    card.append(top, content);
    if (entry.tags.length) {
      const tags = document.createElement("div");
      tags.className = "memory-tags";
      entry.tags.forEach((tag) => {
        const chip = document.createElement("span");
        chip.className = "memory-tag";
        chip.textContent = tag;
        tags.append(chip);
      });
      card.append(tags);
    }
    const actions = document.createElement("div");
    actions.className = "memory-card-actions";
    const edit = document.createElement("button");
    edit.type = "button";
    edit.className = "text-button";
    edit.textContent = "Bewerken";
    edit.setAttribute("aria-label", `Notitie ${entry.title} bewerken`);
    edit.addEventListener("click", () => {
      $("memory-id").value = entry.id;
      $("memory-save").disabled = false;
      $("memory-title-input").value = entry.title;
      $("memory-content").value = entry.content;
      $("memory-tags").value = entry.tags.join(", ");
      $("memory-save").textContent = "Wijzigingen opslaan";
      updateMemoryCharCount();
      $("memory-title-input").focus();
      $("memory-form").scrollIntoView({ behavior: "smooth", block: "center" });
    });
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "text-button danger";
    remove.textContent = "Verwijderen";
    remove.setAttribute("aria-label", `Notitie ${entry.title} verwijderen`);
    remove.addEventListener("click", () => {
      if (busy) return;
      memoryToDelete = entry.id;
      mode = "delete-memory";
      $("confirmation-email-group").hidden = true;
      $("confirmation-email").disabled = true;
      $("dialog-eyebrow").textContent = "GEHEUGENBANK";
      $("dialog-title").textContent = "Notitie verwijderen?";
      $("dialog-number").textContent = entry.title;
      $("dialog-description").textContent = "Deze notitie wordt direct uit je geheugenbank verwijderd. De audit bewaart alleen dat er een notitie is verwijderd, niet de inhoud. Dit kan niet ongedaan worden gemaakt.";
      $("confirm").textContent = "Definitief verwijderen";
      $("confirm-dialog").showModal();
      $("cancel").focus();
    });
    actions.append(edit, remove);
    card.append(actions);
    list.append(card);
  });
}

async function loadMemory() {
  renderMemory(await api("/api/memory"));
}

function renderAuth() {
  $("confirmation-email").value = "";
  $("confirmation-email").disabled = true;
  $("confirmation-email-group").hidden = true;
  $("mail-status").textContent = "";
  mailAvailable = false;
  $("auth-panel").hidden = false;
  $("selection-panel").hidden = true;
  $("result-panel").hidden = true;
  $("recovery-panel").hidden = true;
  $("history-panel").hidden = true;
  $("memory-panel").hidden = true;
  $("account-label").hidden = true;
  $("logout").hidden = true;
  $("auth-title").textContent = authMode === "login"
    ? "Welkom bij PALACO Phone."
    : "Maak jouw account aan.";
  $("auth-description").textContent = authMode === "login"
    ? "Meld je aan om je P.P.-keuze te bekijken of te maken."
    : "Je account wordt gekoppeld aan deze browserregistratie.";
  $("auth-submit").textContent = authMode === "login" ? "Aanmelden" : "Account aanmaken";
  $("auth-switch-copy").textContent = authMode === "login" ? "Nog geen account?" : "Heb je al een account?";
  $("auth-switch").textContent = authMode === "login" ? "Account aanmaken" : "Terug naar aanmelden";
  $("account-link-note").hidden = authMode === "login";
  $("password").autocomplete = authMode === "login" ? "current-password" : "new-password";
  notice(authMode === "login"
    ? "Meld je aan of maak een account om verder te gaan."
    : "Na registratie blijven je bestaande opties en eventuele keuze behouden.");
}

async function load() {
  setBusy(true);
  selected = null;
  $("retry").hidden = true;
  $("auth-panel").hidden = true;
  $("selection-panel").hidden = true;
  $("result-panel").hidden = true;
  notice("Je registratie wordt gecontroleerd...");
  try {
    sessionState = await api("/api/session", {});
    if (!sessionState.authenticated) {
      authMode = "login";
      renderAuth();
      return;
    }
    $("account-label").textContent = sessionState.username;
    $("account-label").hidden = false;
    $("logout").hidden = false;
    current = await api("/api/pp/me");
    renderRecovery();
    await loadMailStatus();
    if (current.status === "ACTIVE" || current.status === "REVOKED") {
      renderResult(current);
    } else if (current.status === "NEW" || current.status === "OFFERED") {
      const batch = await api("/api/pp/options", {});
      if (batch.options.length !== 10
        || new Set(batch.options.map((o) => o.number)).size !== 10
        || batch.options.some((o) => !Object.hasOwn(colorLabels, o.color))) {
        throw new Error(messages.PP_SELECTION_UNKNOWN);
      }
      renderOptions(batch.options);
      $("preview-number").textContent = "Jouw keuze begint hier";
      $("preview-label").textContent = "10 CIJFERS / 1 IDENTITEIT";
      $("step-two").classList.remove("current");
      $("step-three").classList.remove("current");
      $("selection-panel").hidden = false;
      notice("Tien unieke opties staan voor je klaar. Je keuze is pas definitief na bevestiging.");
    } else {
      throw new Error(messages.PP_SELECTION_UNKNOWN);
    }
    renderHistory((await api("/api/pp/history")).events);
    await loadMemory();
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
  }
}

$("auth-switch").addEventListener("click", () => {
  if (busy) return;
  authMode = authMode === "login" ? "register" : "login";
  $("password").value = "";
  renderAuth();
  $("username").focus();
});

$("auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const username = $("username").value;
  const password = $("password").value;
  setBusy(true);
  try {
    if (authMode === "register" && (!sessionState || !sessionState.consumerId)) {
      sessionState = await api("/api/session", {});
    }
    const result = await api(
      authMode === "register" ? "/api/auth/register" : "/api/auth/login",
      { username, password },
    );
    sessionState = result;
    $("password").value = "";
    await load();
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
  }
});

$("logout").addEventListener("click", async () => {
  if (busy) return;
  setBusy(true);
  try {
    await api("/api/auth/logout", {});
    await load();
    notice("Je bent afgemeld. Meld je aan om je registratie terug te zien.");
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
  }
});

$("memory-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  setBusy(true);
  try {
    const tags = $("memory-tags").value.split(",").map((tag) => tag.trim()).filter(Boolean);
    const entry = await api("/api/memory/save", {
      id: $("memory-id").value || null,
      title: $("memory-title-input").value,
      content: $("memory-content").value,
      tags,
    });
    clearMemoryForm();
    await loadMemory();
    notice(`Notitie "${entry.title}" is privé opgeslagen op dit apparaat.`);
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
  }
});

$("memory-reset").addEventListener("click", () => {
  if (!busy) clearMemoryForm();
});
$("memory-content").addEventListener("input", updateMemoryCharCount);

$("review").addEventListener("click", () => {
  if (!selected || busy) return;
  mode = "select";
  $("confirmation-email").disabled = !mailAvailable;
  $("confirmation-email-group").hidden = false;
  $("dialog-eyebrow").textContent = "DE LAATSTE STAP";
  $("dialog-title").textContent = "Maak het van jou.";
  $("dialog-number").textContent = format(selected.number);
  $("dialog-description").textContent = "Dit wordt je definitieve P.P.-nummer. De andere negen opties vervallen. Je kunt daarna niet opnieuw kiezen, ook niet na intrekking.";
  $("confirm").textContent = "Definitief kiezen";
  $("confirm-dialog").showModal();
  $("cancel").focus();
});

$("revoke").addEventListener("click", () => {
  if (busy || !current) return;
  mode = "revoke";
  $("confirmation-email-group").hidden = true;
  $("confirmation-email").disabled = true;
  $("dialog-eyebrow").textContent = "ONOMKEERBARE ACTIE";
  $("dialog-title").textContent = "Nummer intrekken?";
  $("dialog-number").textContent = format(current.ppNumber);
  $("dialog-description").textContent = "Je nummer wordt inactief. De registratie blijft bewaard en je krijgt geen nieuwe set opties. Deze actie kan niet ongedaan worden gemaakt.";
  $("confirm").textContent = "Definitief intrekken";
  $("confirm-dialog").showModal();
  $("cancel").focus();
});

$("cancel").addEventListener("click", () => $("confirm-dialog").close());
$("confirm-dialog").addEventListener("cancel", (event) => { if (busy) event.preventDefault(); });
$("confirm-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || (mode === "select" && !selected)
    || (mode === "delete-memory" && !memoryToDelete)) return;
  setBusy(true);
  try {
    if (mode === "delete-memory") {
      await api("/api/memory/delete", { id: memoryToDelete });
      memoryToDelete = null;
      $("confirm-dialog").close();
      await loadMemory();
      clearMemoryForm();
      notice("De notitie is verwijderd. Alleen het verwijder-event blijft in de audit.");
      return;
    }
    await api(mode === "select" ? "/api/pp/select" : "/api/pp/revoke",
      mode === "select" ? { optionId: selected.id, email: mailAvailable ? $("confirmation-email").value : "" } : {});
    current = await api("/api/pp/me");
    if (current.status !== (mode === "select" ? "ACTIVE" : "REVOKED")) {
      throw new Error(messages.PP_SELECTION_UNKNOWN);
    }
    renderHistory((await api("/api/pp/history")).events);
    $("confirm-dialog").close();
    $("retry").hidden = true;
    renderResult(current);
    renderRecovery();
    await loadMailStatus();
    $("confirmation-email").value = "";
    $("result-title").setAttribute("tabindex", "-1");
    $("result-title").focus();
  } catch (error) {
    $("confirm-dialog").close();
    if (mode !== "delete-memory") {
      $("selection-panel").hidden = true;
      $("result-panel").hidden = true;
    }
    showError(error);
  } finally {
    memoryToDelete = null;
    setBusy(false);
  }
});

$("copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(current.ppNumber);
    notice("Je P.P.-nummer is gekopieerd.");
  } catch (error) {
    console.error(error);
    notice("Kopieren is niet gelukt. Je kunt het nummer hierboven handmatig selecteren.", true);
  }
});
function renderRecovery() {
  if (!sessionState?.authenticated || !current) return;
  $("recovery-account").textContent = sessionState.username;
  $("recovery-status").textContent = {
    NEW: "NEW / nog geen nummeropties",
    OFFERED: "OFFERED / nog geen nummer gekozen",
    ACTIVE: "ACTIVE / lokaal gekozen, niet officieel geverifieerd",
    REVOKED: "REVOKED / lokaal ingetrokken",
  }[current.status] || "UNKNOWN / controle vereist";
  $("recovery-panel").hidden = false;
}

$("recovery-export").addEventListener("click", () => {
  if (busy || !sessionState?.authenticated || !current ||
      !["NEW", "OFFERED", "ACTIVE", "REVOKED"].includes(current.status)) return;
  const dossier = {
    schema: "palaco.phone.recovery.v1",
    reference: "PP-RECOVERY-002",
    generatedAt: new Date().toISOString(),
    source: "LOCAL_PP_PROTOTYPE",
    evidenceClass: "LOCAL_RECORD_SELF_EXPORTED_NOT_INDEPENDENTLY_VERIFIED",
    account: { username: sessionState.username, consumerId: current.consumerId },
    registration: {
      status: current.status,
      ppNumberId: current.ppNumberId || null,
      ppNumber: current.ppNumber || null,
      selectedAt: current.selectedAt || null,
      revokedAt: current.revokedAt || null,
    },
    identityVerification: "NOT_VERIFIED",
    authorization: "HOLD",
    accessDecision: "DENY",
    issuance: "NOT_AUTHORIZED",
    note: "Geen bewijs van persoon, telecomactivatie of PALACO ONE-toegang.",
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(dossier, null, 2) + "\n"],
    { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "palaco-phone-hersteloverzicht.json";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  notice("Hersteloverzicht aangeboden als download. Autorisatie blijft HOLD.");
});
$("retry").addEventListener("click", load);
async function loadMailStatus() {
  const mail = await api("/api/pp/mail");
  mailAvailable = mail.available;
  $("confirmation-email").disabled = !mail.available;
  $("confirmation-email-help").textContent = mail.available
    ? "Optioneel: alleen een keuzebevestiging, geen marketing of wachtwoordherstel. Het adres staat lokaal onversleuteld in de mailwachtrij en wordt via de ingestelde mailserver verwerkt."
    : "E-mail is nog niet beschikbaar: de beheerder moet eerst SMTP configureren. Je kunt wel zonder e-mail een nummer kiezen.";
  const labels = {
    NOT_REQUESTED: "Geen e-mailbevestiging aangevraagd.",
    QUEUED: "Bevestiging staat in de e-mailwachtrij; nog niet door de mailserver aangenomen.",
    SENDING: "E-mail wordt aangeboden aan de mailserver.",
    SENT: "Bevestiging aangenomen door de mailserver. Bezorging in je inbox is niet gegarandeerd.",
    FAILED: "E-mail kon niet worden verstuurd. De beheerder moet de mailinstellingen of toestemming controleren. Je PP-keuze blijft geldig.",
    UNKNOWN: "E-mailuitkomst onbekend. Geen automatische herverzending om duplicaten te voorkomen; je PP-keuze blijft geldig.",
  };
  if (!Object.hasOwn(labels, mail.status)) throw new Error(messages.PP_SELECTION_UNKNOWN);
  $("mail-status").textContent = labels[mail.status];
  $("mail-refresh").hidden = mail.status === "NOT_REQUESTED";
}
$("mail-refresh").addEventListener("click", async () => {
  if (busy) return;
  setBusy(true);
  try { await loadMailStatus(); } catch (error) { showError(error); } finally { setBusy(false); }
});
load();
