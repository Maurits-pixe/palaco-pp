"use strict";
const DB_NAME = "palaco-pp-offline-v1";
const STORE = "drafts";
const $ = id => document.getElementById(id);
function openDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: "id" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}
async function transaction(mode, operation) {
  const db = await openDb();
  try {
    return await new Promise((resolve, reject) => {
      const tx = db.transaction(STORE, mode);
      let result;
      tx.oncomplete = () => resolve(result);
      tx.onabort = () => reject(tx.error || Error("Transactie afgebroken."));
      tx.onerror = () => reject(tx.error || Error("Transactie mislukt."));
      try {
        const request = operation(tx.objectStore(STORE));
        if (request) request.onsuccess = () => { result = request.result; };
      } catch (error) {
        tx.abort();
        reject(error);
      }
    });
  } finally { db.close(); }
}
const all = () => transaction("readonly", store => store.getAll());
const put = draft => transaction("readwrite", store => store.put(draft));
const drop = id => transaction("readwrite", store => store.delete(id));
const putMany = drafts => transaction("readwrite", store => {
  for (const draft of drafts) store.put(draft);
});
async function sha256Hex(value) {
  if (!crypto.subtle) throw Error("SHA-256 niet beschikbaar in deze browser.");
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, "0")).join("");
}
const status = message => { $("status").textContent = message; };
function updateConnection() {
  $("connection-state").textContent = navigator.onLine
    ? "Netwerksignaal beschikbaar · servertoegang niet bevestigd"
    : "Geen netwerksignaal · lokale concepten blijven beschikbaar";
}
window.addEventListener("online", updateConnection);
window.addEventListener("offline", updateConnection);
updateConnection();
let unsaved = false;
$("draft-form").addEventListener("input", () => { unsaved = true; });
window.addEventListener("beforeunload", event => {
  if (!unsaved) return;
  event.preventDefault();
  event.returnValue = "";
});
async function render() {
  const drafts = (await all()).sort((a,b) => b.updatedAt.localeCompare(a.updatedAt));
  $("count").textContent = String(drafts.length);
  const root = $("drafts"); root.replaceChildren();
  if (!drafts.length) { root.textContent = "Nog geen lokale concepten."; return; }
  for (const d of drafts) {
    const item = document.createElement("article"); item.className = "item";
    const heading = document.createElement("h3"); heading.textContent = d.title;
    const time = document.createElement("small"); time.textContent = d.updatedAt;
    const body = document.createElement("p"); body.textContent = d.body;
    const button = document.createElement("button"); button.type = "button"; button.textContent = "Verwijderen";
    button.addEventListener("click", async () => {
      if (!confirm("Dit lokale concept verwijderen?")) return;
      try { await drop(d.id); await render(); status("Lokaal concept verwijderd."); }
      catch { status("Opslag is niet beschikbaar."); }
    });
    item.append(heading,time,body,button); root.append(item);
  }
}
$("draft-form").addEventListener("submit", async event => {
  event.preventDefault();
  const title = $("title").value.trim(), body = $("body").value.trim();
  if (!title || !body || title.length > 120 || body.length > 2000) return;
  try {
    const existing = await all();
    if (existing.length >= 100) { status("Maximaal 100 concepten; exporteer en verwijder eerst een concept."); return; }
    await put({ id: crypto.randomUUID(), title, body, updatedAt: new Date().toISOString() });
    event.target.reset(); unsaved = false; await render(); status("Concept alleen op dit apparaat opgeslagen.");
  } catch { status("Offline opslag niet beschikbaar. Exporteer je tekst handmatig."); }
});
$("export").addEventListener("click", async () => {
  try {
    const drafts = await all();
    const checksum = await sha256Hex(JSON.stringify(drafts));
    const data = JSON.stringify({
      schema:"palaco.pp.offline-drafts.v2", drafts,
      integrity:{algorithm:"SHA-256",checksum}
    },null,2);
    const url = URL.createObjectURL(new Blob([data],{type:"application/json"}));
    const link = document.createElement("a"); link.href=url; link.download="palaco-pp-offline-drafts.json";
    link.click(); setTimeout(()=>URL.revokeObjectURL(url),1000);
    status("Exportbestand aangemaakt. Bewaar het veilig.");
  } catch { status("Export mislukt."); }
});
$("import").addEventListener("change", async event => {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    if (file.size > 1_000_000) throw Error("Bestand te groot.");
    const parsed = JSON.parse(await file.text());
    if (!Array.isArray(parsed.drafts) || parsed.drafts.length > 100) throw Error("Ongeldige export.");
    if (parsed.schema === "palaco.pp.offline-drafts.v2") {
      if (parsed.integrity?.algorithm !== "SHA-256" || !/^[a-f0-9]{64}$/.test(parsed.integrity?.checksum || "")) throw Error("Integriteitscontrole ontbreekt.");
      const actual = await sha256Hex(JSON.stringify(parsed.drafts));
      if (actual !== parsed.integrity.checksum) throw Error("Integriteitscontrole mislukt: bestand gewijzigd of beschadigd.");
    } else if (parsed.schema === "palaco.pp.offline-drafts.v1") {
      if (!confirm("Oud exportbestand zonder integriteitscontrole. Alleen importeren als je de herkomst vertrouwt. Doorgaan?")) return;
    } else throw Error("Onbekend exportschema.");
    const incoming = parsed.drafts;
    if (!incoming.every(d => d && typeof d.id==="string" && /^[0-9a-f-]{36}$/.test(d.id)
      && typeof d.title==="string" && d.title.length>0 && d.title.length<=120
      && typeof d.body==="string" && d.body.length>0 && d.body.length<=2000
      && typeof d.updatedAt==="string" && !Number.isNaN(Date.parse(d.updatedAt)))) throw Error("Ongeldige concepten.");
    const existing = await all();
    const merged = new Map(existing.map(d=>[d.id,d]));
    for (const d of incoming) merged.set(d.id,d);
    if (merged.size > 100) throw Error("Maximaal 100 concepten.");
    await putMany(incoming.map(d => ({id:d.id,title:d.title,body:d.body,updatedAt:d.updatedAt})));
    await render(); status("Concepten geïmporteerd. Geen cloudregistratie gewijzigd.");
  } catch(e) { status("Import geweigerd: "+e.message); }
  finally { event.target.value=""; }
});
render().then(() => {
  $("storage-state").textContent = "Lokale conceptopslag beschikbaar";
}).catch(() => {
  $("storage-state").textContent = "Lokale opslag NIET beschikbaar";
  status("Offline opslag is niet beschikbaar in deze browser.");
});
