"use strict";
// Read-only unsigned handoff manifest. Display ≠ delivery or authorization.
(() => {
  const $=id=>document.getElementById(id);
  const input=$("admin-handoff-manifest-file"),button=$("admin-handoff-manifest-load"),
        status=$("admin-handoff-manifest-status"),
        sources=$("admin-handoff-manifest-sources"),
        blockers=$("admin-handoff-manifest-blockers"),
        gates=$("admin-handoff-manifest-gates"),
        dashboard=$("admin-dashboard");
  if(![input,button,status,sources,blockers,gates,dashboard].every(Boolean))return;
  const sourceNames=["decisionDossierSha256","reviewQueueSha256","reviewIntakeSha256",
    "verificationPlanSha256","observationRegisterSha256"];
  const ids=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const checks=["ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED","SOURCE_PROVENANCE_NOT_ATTESTED",
    "SUBMITTER_IDENTITY_NOT_AUTHENTICATED","REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "SUBJECT_BINDING_NOT_ESTABLISHED","INDEPENDENT_REVIEW_NOT_COMPLETED"];
  const gateOrders=[[1,2],[1,2,3,5],[3,4,5],[1,2,6],[1,2,3,4,5,6]];
  const global=["ORIGINAL_SOURCE_ATTESTATION_ABSENT","SUBMITTER_AUTHENTICATION_ABSENT",
    "REVIEWER_IDENTITY_AND_AUTHORITY_ABSENT","CROSS_SOURCE_SUBJECT_BINDING_ABSENT",
    "INDEPENDENT_HUMAN_REVIEW_NOT_COMPLETED","IMMUTABLE_AUDIT_PROVENANCE_ABSENT"];
  const fixed={
    schema:"palaco.pp.recovery-002-human-review-handoff.v0",reference:"PP-RECOVERY-002",
    originalEvidenceIncluded:false,originalEvidenceRetention:"REQUIRED_SEPARATELY",
    intendedRecipient:"INDEPENDENT_AUTHORIZED_HUMAN_REVIEWER_UNASSIGNED",
    recipientAuthentication:"NOT_ESTABLISHED",
    recipientAuthorization:"NOT_ESTABLISHED",
    deliveryStatus:"NOT_DELIVERED",receiptStatus:"NOT_ACKNOWLEDGED",
    manifestProvenance:"UNSIGNED_LOCAL_DRAFT",
    independentVerification:"NOT_VERIFIED",subjectBinding:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const fields=[...Object.keys(fixed),"readinessCanonicalSha256","statusCanonicalSha256",
    "files","globalBlockers","requirements"];
  const isObject=(obj,keys)=>obj&&typeof obj==="object"&&!Array.isArray(obj)
    &&Object.keys(obj).length===keys.length&&keys.every(k=>Object.hasOwn(obj,k));
  const hash=s=>typeof s==="string"&&/^[0-9a-f]{64}$/.test(s);
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((x,i)=>x===b[i]);
  let epoch=0;
  const clear=(message="Geen handoffmanifest geladen. HOLD / DENY.")=>{
    ++epoch;status.textContent=message;sources.replaceChildren();
    blockers.replaceChildren();gates.replaceChildren();
  };
  input.addEventListener("change",()=>clear("Bestand gewijzigd; vorige weergave vervallen. HOLD / DENY."));
  const logout=()=>{clear();input.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal ongetekend manifest lezen. HOLD / DENY.");
    const current=epoch,file=input.files?.[0];
    if(dashboard.hidden||!file||file.size<1||file.size>32768){
      status.textContent="GEWEIGERD / Manifest maximaal 32 KiB. HOLD / DENY.";return;
    }
    try{
      const raw=await file.arrayBuffer();
      if(current!==epoch||dashboard.hidden)return;
      const obj=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(raw));
      if(!isObject(obj,fields)||Object.entries(fixed).some(([k,v])=>obj[k]!==v)
        ||!hash(obj.readinessCanonicalSha256)||!hash(obj.statusCanonicalSha256)
        ||!Array.isArray(obj.files)||obj.files.length!==5
        ||!same(obj.globalBlockers,global)
        ||!Array.isArray(obj.requirements)||obj.requirements.length!==5)throw Error();
      const src=document.createDocumentFragment();
      for(let i=0;i<5;i++){
        const item=obj.files[i];
        if(!isObject(item,["role","sha256","deliveryStatus","sourceVerification"])
          ||item.role!==sourceNames[i]||!hash(item.sha256)
          ||item.deliveryStatus!=="NOT_DELIVERED"
          ||item.sourceVerification!=="NOT_VERIFIED")throw Error();
        const tr=document.createElement("tr");
        for(const value of [item.role,item.sha256.slice(0,18)+"…",item.deliveryStatus]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }src.append(tr);
      }
      const bl=document.createDocumentFragment();
      for(const b of obj.globalBlockers){
        const li=document.createElement("li");li.textContent=b;bl.append(li);
      }
      const gr=document.createDocumentFragment();
      for(let i=0;i<5;i++){
        const g=obj.requirements[i],expect=gateOrders[i].map(j=>checks[j-1]);
        if(!isObject(g,["requirementId","missingCheckIds","gate","reviewStatus"])
          ||g.requirementId!==ids[i]||!same(g.missingCheckIds,expect)
          ||g.gate!=="BLOCKED"||g.reviewStatus!=="NOT_STARTED")throw Error();
        const tr=document.createElement("tr");
        for(const value of [g.requirementId,String(g.missingCheckIds.length),
          "NOT_STARTED / BLOCKED"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }gr.append(tr);
      }
      if(current!==epoch||dashboard.hidden)return;
      sources.replaceChildren(src);blockers.replaceChildren(bl);gates.replaceChildren(gr);
      status.textContent="ONGETEKEND HANDOFFMANIFEST / Geen reviewer toegewezen of geauthenticeerd, niets verzonden of ontvangen. Alle poorten BLOCKED / HOLD / DENY.";
    }catch(_){
      if(current!==epoch||dashboard.hidden)return;
      clear("HANDOFFMANIFEST GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
