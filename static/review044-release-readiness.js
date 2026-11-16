"use strict";
// Untrusted local readiness-gap report. NEVER a release or identity verdict.
(() => {
  const $=id=>document.getElementById(id);
  const input=$("admin-readiness-file"),load=$("admin-readiness-load"),
    status=$("admin-readiness-status"),gates=$("admin-readiness-gates"),
    blockers=$("admin-readiness-blockers"),dashboard=$("admin-dashboard");
  if(![input,load,status,gates,blockers,dashboard].every(Boolean))return;
  const req=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const checks=["ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED",
    "SOURCE_PROVENANCE_NOT_ATTESTED","SUBMITTER_IDENTITY_NOT_AUTHENTICATED",
    "REVIEWER_AUTHORITY_NOT_ESTABLISHED","SUBJECT_BINDING_NOT_ESTABLISHED",
    "INDEPENDENT_REVIEW_NOT_COMPLETED"];
  const prereqs=[[1,2],[1,2,3,5],[3,4,5],[1,2,6],[1,2,3,4,5,6]];
  const next=["OBTAIN_INDEPENDENT_SOURCE_ATTESTATION",
    "ESTABLISH_INDEPENDENT_SUBJECT_BINDING",
    "AUTHENTICATE_OWNER_AND_REVIEWER_SEPARATELY",
    "ATTEST_ORIGINAL_RUNTIME_EXECUTION",
    "COMPLETE_AUTHORIZED_HUMAN_REVIEW_OUTSIDE_THIS_MODULE"];
  const global=[
    "ORIGINAL_SOURCE_ATTESTATION_ABSENT","SUBMITTER_AUTHENTICATION_ABSENT",
    "REVIEWER_IDENTITY_AND_AUTHORITY_ABSENT",
    "CROSS_SOURCE_SUBJECT_BINDING_ABSENT",
    "INDEPENDENT_HUMAN_REVIEW_NOT_COMPLETED",
    "IMMUTABLE_AUDIT_PROVENANCE_ABSENT"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-release-readiness.v0",
    reference:"PP-RECOVERY-002",
    blockedGateCount:5,overallReadiness:"NOT_READY",
    manualDecision:"REQUIRED_OUTSIDE_THIS_MODULE",
    sourceAuthenticity:"NOT_ESTABLISHED",subjectBinding:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",independentVerification:"NOT_VERIFIED",
    humanReview:"NOT_COMPLETED",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const fields=[...Object.keys(fixed),"statusReportCanonicalSha256",
    "sourceFingerprints","reviewRequests","intakeReferences",
    "unsignedObservations","globalBlockers","gateReadiness"];
  const sourceFields=["decisionDossierSha256","reviewQueueSha256",
    "reviewIntakeSha256","verificationPlanSha256","observationRegisterSha256"];
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
  const exact=(x,keys)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const hex=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let generation=0;
  const clear=(message="Geen vrijgavegereedheidsrapport geladen. HOLD / DENY.")=>{
    generation++;gates.replaceChildren();blockers.replaceChildren();status.textContent=message;
  };
  input.addEventListener("change",()=>clear("Rapport gewijzigd; vorige weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();input.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Rapport lokaal lezen. HOLD / DENY.");
    const current=generation,f=input.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>32768){
      status.textContent="GEWEIGERD / Kies een bestaand JSON-rapport tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const bytes=await f.arrayBuffer();
      if(generation!==current||dashboard.hidden)return;
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
      if(!exact(data,fields)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !hex(data.statusReportCanonicalSha256)||
        !exact(data.sourceFingerprints,sourceFields)||
        sourceFields.some(k=>!hex(data.sourceFingerprints[k]))||
        !Number.isInteger(data.reviewRequests)||data.reviewRequests<0||data.reviewRequests>128||
        !Number.isInteger(data.intakeReferences)||data.intakeReferences<0||data.intakeReferences>64||
        !Number.isInteger(data.unsignedObservations)||data.unsignedObservations<0||
        data.unsignedObservations>128||
        !same(data.globalBlockers,global)||
        !Array.isArray(data.gateReadiness)||data.gateReadiness.length!==5)throw Error();
      const b=document.createDocumentFragment(),r=document.createDocumentFragment();
      for(const value of data.globalBlockers){
        const li=document.createElement("li");li.textContent=value;b.append(li);
      }
      for(let i=0;i<5;i++){
        const item=data.gateReadiness[i],deps=prereqs[i];
        if(!exact(item,["requirementId","description","missingChecks","missingCount",
          "nextManualAction","gate","readiness"])||
          item.requirementId!==req[i]||typeof item.description!=="string"||
          item.description.length<1||item.description.length>160||
          item.nextManualAction!==next[i]||item.missingCount!==deps.length||
          item.gate!=="BLOCKED"||item.readiness!=="NOT_READY"||
          !Array.isArray(item.missingChecks)||item.missingChecks.length!==deps.length)throw Error();
        for(let j=0;j<deps.length;j++){
          const c=item.missingChecks[j],order=deps[j];
          if(!exact(c,["checkOrder","checkId","status","verification"])||
            c.checkOrder!==order||c.checkId!==checks[order-1]||
            c.status!=="NOT_STARTED"||c.verification!=="NOT_VERIFIED")throw Error();
        }
        const tr=document.createElement("tr");
        for(const v of [item.requirementId,item.missingCount,
          item.nextManualAction,"NOT_READY / BLOCKED"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }r.append(tr);
      }
      if(generation!==current||dashboard.hidden)return;
      blockers.replaceChildren(b);gates.replaceChildren(r);
      status.textContent="STRUCTUUR HERKEND / Alle vijf poorten NOT_READY; geen onafhankelijke bron- of reviewerverificatie. Browsercontrole is indicatief. HOLD / DENY.";
    }catch(_){
      if(generation!==current||dashboard.hidden)return;
      clear("GEREEDHEIDSRAPPORT GEWEIGERD / Ongeldige inhoud of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
