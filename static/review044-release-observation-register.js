"use strict";
// View-only unsigned local PP release observations. No PASS or approval actions.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-release-observation-file"),load=$("admin-release-observation-load"),
    status=$("admin-release-observation-status"),rows=$("admin-release-observation-rows"),
    dashboard=$("admin-dashboard");
  if(![file,load,status,rows,dashboard].every(Boolean))return;
  const gateNames=["SOURCE_PROVENANCE","VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION","AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION","DEPLOYMENT_APPROVAL"];
  const marks=["OBSERVATION_REPORTED","BLOCKER_REPORTED","RECHECK_REQUESTED"];
  const roles=["OWNER_CLAIMED","REVIEWER_CLAIMED","SOURCE_CLAIMED"];
  const fixed={
    schema:"palaco.pp.recovery-002-release-observation-register.v0",
    reference:"PP-RECOVERY-002",provenance:"UNSIGNED_LOCAL_SELF_REPORT",
    independentVerification:"NOT_VERIFIED",reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",humanReview:"NOT_COMPLETED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const efixed={
    observationProvenance:"SELF_REPORTED_UNAUTHENTICATED",
    evidenceVerification:"NOT_VERIFIED",executionEvidence:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",releaseGate:"BLOCKED",
    authorization:"HOLD",accessDecision:"DENY"
  };
  const shape=(x,fields)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===fields.length&&fields.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let version=0;
  function clear(message="Geen lokaal release-observatieregister geladen. HOLD / DENY."){
    version++;rows.replaceChildren();status.textContent=message;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd; vorige weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekende lokale waarnemingen lezen. HOLD / DENY.");
    const epoch=version,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>131072){
      status.textContent="GEWEIGERD / Kies JSON tot 128 KiB. HOLD / DENY.";return;
    }
    try{
      const record=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(epoch!==version||dashboard.hidden)return;
      if(!shape(record,[...Object.keys(fixed),"executionPlanSha256","events"])||
        Object.entries(fixed).some(([k,v])=>record[k]!==v)||
        !sha(record.executionPlanSha256)||!Array.isArray(record.events)||
        record.events.length>128)throw Error();
      const output=document.createDocumentFragment();
      let previous=null;
      for(let i=0;i<record.events.length;i++){
        const item=record.events[i];
        if(!shape(item,[...Object.keys(efixed),"sequence","checkId","gateId",
          "mark","roleClaim","note","evidenceSha256","previousEventSha256",
          "eventSha256"])||
          Object.entries(efixed).some(([k,v])=>item[k]!==v)||
          item.sequence!==i+1||
          typeof item.checkId!=="string"||
          !/^RG0[1-6]-E0[1-3]$/.test(item.checkId)||
          item.gateId!==gateNames[Number(item.checkId.slice(2,4))-1]||
          !marks.includes(item.mark)||!roles.includes(item.roleClaim)||
          typeof item.note!=="string"||item.note.length>500||
          (item.evidenceSha256!==null&&!sha(item.evidenceSha256))||
          item.previousEventSha256!==previous||!sha(item.eventSha256))throw Error();
        previous=item.eventSha256;
        const tr=document.createElement("tr");
        for(const value of [item.sequence,item.checkId,item.mark,
          item.roleClaim,item.evidenceSha256?"SHA-256 opgegeven":"Geen hash",
          "NOT_VERIFIED / BLOCKED"]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }
        output.append(tr);
      }
      if(epoch!==version||dashboard.hidden)return;
      rows.replaceChildren(output);
      status.textContent="LOKAAL REGISTER HERKEND / "+record.events.length+
        " onbevestigde claims, geen cryptografische ketenverificatie in browser. HOLD / DENY.";
    }catch(_){
      if(epoch!==version||dashboard.hidden)return;
      clear("OBSERVATIEREGISTER GEWEIGERD / Onjuiste structuur of vrijgaveclaims. HOLD / DENY.");
    }
  });
})();
