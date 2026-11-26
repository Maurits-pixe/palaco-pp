"use strict";
// Display-only, unsigned local evidence references. No proof verification.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-release-intake-file"),button=$("admin-release-intake-load"),
    status=$("admin-release-intake-status"),rows=$("admin-release-intake-rows"),
    dashboard=$("admin-dashboard");
  if(![file,button,status,rows,dashboard].every(Boolean))return;
  const gates=["SOURCE_PROVENANCE","VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION","AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION","DEPLOYMENT_APPROVAL"];
  const kinds=["DOCUMENT","SCREENSHOT","LOG_EXCERPT","OTHER_UNTRUSTED"];
  const fixed={
    schema:"palaco.pp.recovery-002-release-evidence-intake.v0",
    reference:"PP-RECOVERY-002",
    provenance:"UNSIGNED_LOCAL_EVIDENCE_CLAIMS",
    independentVerification:"NOT_VERIFIED",
    sourceAuthenticity:"NOT_ESTABLISHED",
    reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",
    releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const itemFixed={
    provenance:"UNSIGNED_LOCAL_UNTRUSTED",
    evidenceVerification:"NOT_VERIFIED",
    signatureVerification:"NOT_PERFORMED",
    submitterAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    gate:"BLOCKED",decision:"DENY"
  };
  const exact=(o,fields)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===fields.length&&fields.every(x=>Object.hasOwn(o,x));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let generation=0;
  const clear=(message="Geen Verification Evidence Intake geladen. HOLD / DENY.")=>{
    generation++;rows.replaceChildren();status.textContent=message;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Ongetekend bewijsregister lezen. HOLD / DENY.");
    const current=generation,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(current!==generation||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"executionPlanSha256",
        "observationRegisterSha256","records"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.executionPlanSha256)||!sha(data.observationRegisterSha256)||
        !Array.isArray(data.records)||data.records.length>64)throw Error();
      const fragment=document.createDocumentFragment();
      let previous=null;const seen=new Set();
      for(let i=0;i<data.records.length;i++){
        const x=data.records[i];
        if(!exact(x,[...Object.keys(itemFixed),"sequence","observationSequence",
          "observationEventSha256","checkId","gateId","evidenceKind",
          "evidenceSha256","evidenceByteCount","previousRecordSha256",
          "recordSha256"])||
          Object.entries(itemFixed).some(([k,v])=>x[k]!==v)||
          x.sequence!==i+1||!Number.isInteger(x.observationSequence)||
          x.observationSequence<1||x.observationSequence>128||
          seen.has(x.observationSequence)||
          !sha(x.observationEventSha256)||
          typeof x.checkId!=="string"||
          !/^RG0[1-6]-E0[1-3]$/.test(x.checkId)||
          x.gateId!==gates[Number(x.checkId.slice(2,4))-1]||
          !kinds.includes(x.evidenceKind)||!sha(x.evidenceSha256)||
          !Number.isInteger(x.evidenceByteCount)||
          x.evidenceByteCount<1||x.evidenceByteCount>65536||
          x.previousRecordSha256!==previous||!sha(x.recordSha256))throw Error();
        seen.add(x.observationSequence);previous=x.recordSha256;
        const tr=document.createElement("tr");
        for(const v of [x.sequence,x.checkId,x.observationSequence,x.evidenceKind,
          x.evidenceSha256.slice(0,18)+"…","NOT_VERIFIED / DENY"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }
        fragment.append(tr);
      }
      if(current!==generation||dashboard.hidden)return;
      rows.replaceChildren(fragment);
      status.textContent="ONGETEKENDE INTAKE HERKEND / "+data.records.length+
        " lokale bewijsverwijzingen. Hashketen en originele bytes NIET in browser geverifieerd. HOLD / DENY.";
    }catch(_){
      if(current!==generation||dashboard.hidden)return;
      clear("EVIDENCE INTAKE GEWEIGERD / Ongeldige structuur of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
