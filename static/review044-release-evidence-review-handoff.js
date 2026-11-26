"use strict";
// Unsigned handoff preview only. Never claims delivery, receipt or review.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-review-handoff-file"),button=$("admin-review-handoff-load"),
    status=$("admin-review-handoff-status"),rows=$("admin-review-handoff-rows"),
    checks=$("admin-review-handoff-checks"),dashboard=$("admin-dashboard");
  if(![file,button,status,rows,checks,dashboard].every(Boolean))return;
  const gates=["SOURCE_PROVENANCE","VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION","AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION","DEPLOYMENT_APPROVAL"];
  const roles=["INDEPENDENT_SOURCE_CUSTODIAN","INDEPENDENT_COMPATIBILITY_REVIEWER",
    "INDEPENDENT_TECHNICAL_VERIFIER","AUTHORIZED_INDEPENDENT_HUMAN_REVIEWER",
    "INDEPENDENT_RELEASE_ATTESTOR","AUTHORIZED_RELEASE_OPERATOR"];
  const requirements=["EXTERNAL_REVIEWER_IDENTITY_AUTHENTICATION",
    "INDEPENDENT_ROLE_AND_SCOPE_ATTESTATION",
    "REVOCATION_AND_SEPARATION_OF_DUTIES_CHECK",
    "ORIGINAL_EVIDENCE_BYTES_AND_PROVENANCE_VERIFICATION",
    "SIGNED_RECEIPT_BOUND_TO_EXACT_HANDOFF_SHA256",
    "EXTERNAL_AUDIT_ANCHOR_AND_TRUSTED_TIME",
    "AUTHORIZED_HUMAN_REVIEW_DECISION"];
  const evidence=[
    ["ORIGINAL_SOURCE_BYTES_FROM_TRUSTED_CUSTODIAN","INDEPENDENT_PROVENANCE_ATTESTATION","SOURCE_HASH_AND_SIGNER_VALIDATION"],
    ["VERSION_LOCK_AND_DEPENDENCY_RECHECK","INDEPENDENT_BREAKING_CHANGE_ASSESSMENT","SUPPORTED_TARGET_RUNTIME_DECLARATION"],
    ["REPRODUCIBLE_TEST_RESULTS_WITH_PROVENANCE","INDEPENDENT_IDENTITY_AND_SUBJECT_BINDING","NONCE_REVOCATION_AND_CLOCK_CHECK"],
    ["INDEPENDENT_REVIEWER_AUTHENTICATION","SIGNED_ROLE_SCOPE_AND_INDEPENDENCE_ATTESTATION","RECORDED_HUMAN_DECISION_WITH_EXACT_MANIFEST_BINDING"],
    ["REPRODUCIBLE_SBOM_AND_BUILD_PROVENANCE","TRUSTED_SIGNING_KEY_AND_SIGNATURE_VALIDATION","EXTERNALLY_ANCHORED_TIMESTAMP_AND_AUDIT"],
    ["APPROVED_RELEASE_POLICY_AND_ENVIRONMENT","AUTHORIZED_SEPARATE_DEPLOYMENT_DECISION","ROLLBACK_AND_REVOCATION_READINESS"]
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-release-evidence-review-handoff.v0",
    reference:"PP-RECOVERY-002",sourceBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    handoffProvenance:"UNSIGNED_LOCAL_REQUEST_NOT_SENT",delivery:"NOT_SENT",
    recipientAuthentication:"NOT_ESTABLISHED",
    reviewerAuthentication:"NOT_ESTABLISHED",reviewerAuthority:"NOT_ESTABLISHED",
    signedReceipt:"NOT_AVAILABLE",externalAudit:"NOT_VERIFIED",
    humanReview:"NOT_COMPLETED",independentVerification:"NOT_VERIFIED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",accessDecision:"DENY",
    issuance:"NOT_AUTHORIZED"
  };
  const exact=(o,k)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let rev=0;
  const clear=(m="Geen Evidence Review Handoff geladen. HOLD / DENY.")=>{
    rev++;rows.replaceChildren();checks.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Ongetekende overdrachtsaanvraag lokaal lezen. HOLD / DENY.");
    const epoch=rev,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(epoch!==rev||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"executionPlanSha256",
        "observationRegisterSha256","evidenceIntakeSha256",
        "evidenceReferences","evidenceReferenceCount","requiredExternalReview",
        "releaseGateReview"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.executionPlanSha256)||!sha(data.observationRegisterSha256)||
        !sha(data.evidenceIntakeSha256)||!Array.isArray(data.evidenceReferences)||
        data.evidenceReferences.length>64||data.evidenceReferenceCount!==data.evidenceReferences.length||
        !Array.isArray(data.requiredExternalReview)||data.requiredExternalReview.length!==7||
        !Array.isArray(data.releaseGateReview)||data.releaseGateReview.length!==6)throw Error();
      for(let i=0;i<6;i++){
        const g=data.releaseGateReview[i];
        if(!exact(g,["releaseGate","requiredIndependentRole","status",
          "reviewerAuthority","decision"])||g.releaseGate!==gates[i]||
          g.requiredIndependentRole!==roles[i]||g.status!=="BLOCKED"||
          g.reviewerAuthority!=="NOT_ESTABLISHED"||g.decision!=="DENY")throw Error();
      }
      const review=document.createDocumentFragment();
      for(let i=0;i<7;i++){
        const g=data.requiredExternalReview[i];
        if(!exact(g,["order","requirement","status"])||g.order!==i+1||
          g.requirement!==requirements[i]||g.status!=="NOT_STARTED")throw Error();
        const li=document.createElement("li");li.textContent=g.requirement+" — NOT_STARTED";
        review.append(li);
      }
      const records=document.createDocumentFragment();
      for(let i=0;i<data.evidenceReferences.length;i++){
        const x=data.evidenceReferences[i],gateIndex=gates.indexOf(x.releaseGate);
        if(!exact(x,["sequence","checkId","releaseGate","evidenceId",
          "requiredIndependentRole","observationEventSha256","evidenceSha256",
          "evidenceByteCount","evidenceKind","externalAuthenticity",
          "reviewStatus","decision"])||x.sequence!==i+1||
          !/^RG0[1-6]-E0[1-3]$/.test(x.checkId)||gateIndex<0||
          gateIndex!==Number(x.checkId.slice(2,4))-1||
          x.evidenceId!==evidence[gateIndex][Number(x.checkId.slice(6,8))-1]||
          x.requiredIndependentRole!==roles[gateIndex]||
          !sha(x.observationEventSha256)||!sha(x.evidenceSha256)||
          !Number.isInteger(x.evidenceByteCount)||x.evidenceByteCount<1||
          x.evidenceByteCount>65536||
          !["DOCUMENT","SCREENSHOT","LOG_EXCERPT","OTHER_UNTRUSTED"].includes(x.evidenceKind)||
          x.externalAuthenticity!=="NOT_VERIFIED"||x.reviewStatus!=="NOT_STARTED"||
          x.decision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const value of [x.sequence,x.checkId,x.evidenceKind,
          x.evidenceSha256.slice(0,16)+"…","NOT_STARTED / DENY"]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }records.append(tr);
      }
      if(epoch!==rev||dashboard.hidden)return;
      rows.replaceChildren(records);checks.replaceChildren(review);
      status.textContent="ONGEBRUIKTE OVERDRACHTSAANVRAAG / "+data.evidenceReferenceCount+
        " bewijsverwijzingen, niet verstuurd, niet beoordeeld. HOLD / DENY.";
    }catch(_){
      if(epoch!==rev||dashboard.hidden)return;
      clear("EVIDENCE REVIEW HANDOFF GEWEIGERD / Ongeldig schema of status. HOLD / DENY.");
    }
  });
})();
