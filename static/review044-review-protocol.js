"use strict";
// Displays UNSIGNED receipt/reviewer role claims only. Does not authenticate.
(() => {
  const $=id=>document.getElementById(id);
  const manifest=$("admin-review-protocol-manifest");
  const snapshot=$("admin-review-protocol-snapshot");
  const button=$("admin-review-protocol-load");
  const status=$("admin-review-protocol-status");
  const rows=$("admin-review-protocol-rows");
  const details=$("admin-review-protocol-details");
  const dashboard=$("admin-dashboard");
  if (![manifest,snapshot,button,status,rows,details,dashboard].every(Boolean))return;
  const fixed={
    schema:"palaco.pp.recovery-002-review-protocol.v0",
    reference:"PP-RECOVERY-002",
    provenance:"UNSIGNED_LOCAL_ROLE_CLAIMS",
    reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    recipientAuthentication:"NOT_ESTABLISHED",
    receiptVerification:"NOT_VERIFIED",
    humanReview:"NOT_COMPLETED",
    deliveryVerification:"NOT_VERIFIED",
    palacoOneHandoff:"BLOCKED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const itemFixed={
    claimProvenance:"SELF_REPORTED_UNAUTHENTICATED",
    receiptVerification:"NOT_VERIFIED",
    reviewerAuthority:"NOT_ESTABLISHED",
    reviewStatus:"NOT_COMPLETED",
    gate:"BLOCKED",authorization:"HOLD",accessDecision:"DENY"
  };
  const fields=[...Object.keys(fixed),"handoffManifestSha256","events"];
  const itemFields=[...Object.keys(itemFixed),"sequence","mark","roleClaim",
    "requirementId","previousEventSha256","eventSha256"];
  const marks=new Set(["RECEIPT_CLAIMED","REVIEW_REQUESTED",
    "IDENTITY_CHECK_REQUESTED","AUTHORITY_CHECK_REQUESTED",
    "AUTHENTICATION_BLOCKER_REPORTED","EVIDENCE_GAP_REPORTED",
    "RECHECK_REQUESTED"]);
  const roles=new Set(["OWNER_CLAIMED","RECIPIENT_CLAIMED","REVIEWER_CLAIMED"]);
  const requirements=new Set(["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT",
    "OWNER_AUTHORITY","RUNTIME_EXECUTION","HUMAN_REVIEW"]);
  const hex=s=>typeof s==="string"&&/^[0-9a-f]{64}$/.test(s);
  const exact=(x,keys)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  let revision=0;
  const clear=(message="Geen ontvangstprotocol geladen. HOLD / DENY.")=>{
    revision++;rows.replaceChildren();details.replaceChildren();status.textContent=message;
  };
  [manifest,snapshot].forEach(f=>f.addEventListener("change",()=>clear("Bestand gewijzigd; vorige weergave gewist. HOLD / DENY.")));
  const logout=()=>{clear();manifest.value="";snapshot.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Bestanden lokaal lezen. HOLD / DENY.");
    const generation=revision,a=manifest.files?.[0],b=snapshot.files?.[0];
    if(dashboard.hidden||!a||!b||a.size<1||a.size>32768||b.size<1||b.size>65536){
      status.textContent="GEWEIGERD / Handoffmanifest max 32 KiB, protocol max 64 KiB. HOLD / DENY.";return;
    }
    try{
      const bytes=await Promise.all([a.arrayBuffer(),b.arrayBuffer()]);
      if(generation!==revision||dashboard.hidden)return;
      const decoder=new TextDecoder("utf-8",{fatal:true});
      const handoff=JSON.parse(decoder.decode(bytes[0]));
      const record=JSON.parse(decoder.decode(bytes[1]));
      if(handoff?.schema!=="palaco.pp.recovery-002-human-review-handoff.v0" ||
        handoff.reference!=="PP-RECOVERY-002"||
        handoff.deliveryStatus!=="NOT_DELIVERED"||
        handoff.receiptStatus!=="NOT_ACKNOWLEDGED"||
        handoff.recipientAuthentication!=="NOT_ESTABLISHED"||
        handoff.recipientAuthorization!=="NOT_ESTABLISHED"||
        handoff.authorization!=="HOLD"||handoff.accessDecision!=="DENY"||
        !exact(record,fields)||Object.entries(fixed).some(([k,v])=>record[k]!==v)||
        !hex(record.handoffManifestSha256)||!Array.isArray(record.events)||
        record.events.length>64)throw Error();
      const digest=await crypto.subtle.digest("SHA-256",bytes[0]);
      if(generation!==revision||dashboard.hidden)return;
      const actual=Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,"0")).join("");
      if(actual!==record.handoffManifestSha256)throw Error();
      let previous=null;
      const lines=document.createDocumentFragment();
      for(let i=0;i<record.events.length;i++){
        const event=record.events[i];
        if(!exact(event,itemFields)||
          Object.entries(itemFixed).some(([k,v])=>event[k]!==v)||
          !Number.isInteger(event.sequence)||event.sequence!==i+1||
          !marks.has(event.mark)||!roles.has(event.roleClaim)||
          !requirements.has(event.requirementId)||
          event.previousEventSha256!==previous||!hex(event.eventSha256))throw Error();
        previous=event.eventSha256;
        const tr=document.createElement("tr");
        for(const val of [event.sequence,event.mark,event.roleClaim,
          event.requirementId,"NOT_VERIFIED / BLOCKED"]){
          const td=document.createElement("td");td.textContent=String(val);tr.append(td);
        }
        lines.append(tr);
      }
      const facts=document.createDocumentFragment();
      for(const [label,value] of [
        ["Lokale manifestbytehash",actual.slice(0,20)+"…"],
        ["Ongetekende claims",record.events.length],
        ["Ontvangststatus",record.receiptVerification],
        ["Reviewer-authenticatie",record.reviewerAuthentication],
        ["Reviewerbevoegdheid",record.reviewerAuthority],
        ["Onafhankelijke review",record.humanReview],
        ["PALACO ONE",record.palacoOneHandoff],
        ["Autorisatie","HOLD / DENY / NOT_AUTHORIZED"]
      ]){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=label;dd.textContent=String(value);facts.append(dt,dd);
      }
      if(generation!==revision||dashboard.hidden)return;
      rows.replaceChildren(lines);details.replaceChildren(facts);
      status.textContent="ONGETEKENDE CLAIMS GELEZEN / Manifestbytehash komt overeen; werkelijke levering, ontvangst en revieweridentiteit NIET geverifieerd. HOLD / DENY.";
    }catch(_){
      if(generation!==revision||dashboard.hidden)return;
      clear("ONTVANGSTPROTOCOL GEWEIGERD / Ongeldige koppeling of inhoud. HOLD / DENY.");
    }
  });
})();
