"use strict";
// Read-only UNSIGNED revocation architecture, NOT revocation evidence or engine.
(() => {
  const $=id=>document.getElementById(id);
  const input=$("admin-revocation-file"),load=$("admin-revocation-load"),
    status=$("admin-revocation-status"),scenarios=$("admin-revocation-scenarios"),
    recovery=$("admin-revocation-recovery"),dashboard=$("admin-dashboard");
  if(![input,load,status,scenarios,recovery,dashboard].every(Boolean))return;
  const events=["CREDENTIAL_REVOKED","ROLE_REVOKED",
    "SIGNING_KEY_REVOKED","AUDIT_ANCHOR_COMPROMISED"];
  const owners=["AUTHENTICATION","AUTHORIZATION","AUDIT","AUDIT"];
  const invalidates=[
    ["IDENTITY_ASSERTION","REVIEWER_SCOPE_DECISION","SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE"],
    ["REVIEWER_SCOPE_DECISION","SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE"],
    ["SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE"],
    ["SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE"]
  ];
  const steps=["INDEPENDENT_REVOCATION_EVENT_ATTESTATION",
    "QUARANTINE_DERIVED_ASSERTIONS_AND_DECISIONS",
    "INVALIDATE_NONCES_AND_EXPIRED_CREDENTIALS",
    "REVERIFY_ISSUER_KEYS_AND_FRESH_CREDENTIAL",
    "RECHECK_ROLE_SCOPE_AND_SEPARATION_OF_DUTIES",
    "VERIFY_NEW_RECEIPT_SIGNATURE_AND_EXTERNAL_AUDIT_ANCHOR",
    "REQUIRE_NEW_INDEPENDENT_HUMAN_REVIEW",
    "KEEP_HOLD_UNTIL_EXTERNAL_AUTHORIZED_DECISION"];
  const boundaries=["AUTHENTICATION_TO_AUTHORIZATION",
    "AUTHORIZATION_TO_AUDIT","AUDIT_TO_MANUAL_REVIEW"];
  const fixed={
    schema:"palaco.pp.recovery-002-revocation-recovery.v0",
    reference:"PP-RECOVERY-002",
    revocationFeed:"NOT_CONFIGURED",trustedClock:"NOT_CONFIGURED",
    credentialAndRoleValidation:"NOT_PERFORMED",
    auditAnchoring:"NOT_IMPLEMENTED",
    revocationProcessing:"NOT_IMPLEMENTED",
    reinstatement:"NOT_AUTHORIZED",reviewerAuthority:"NOT_ESTABLISHED",
    independentVerification:"NOT_VERIFIED",humanReview:"NOT_COMPLETED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const fields=[...Object.keys(fixed),"trustTransitionSha256",
    "handoffManifestSha256","revocationScenarios","recoveryChecklist",
    "trustTransitionOutcomes"];
  const exact=(o,k)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===k.length&&k.every(v=>Object.hasOwn(o,v));
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
  const digest=s=>typeof s==="string"&&/^[0-9a-f]{64}$/.test(s);
  let revision=0;
  const clear=(message="Geen intrekkingscontract geladen. HOLD / DENY.")=>{
    revision++;scenarios.replaceChildren();recovery.replaceChildren();
    status.textContent=message;
  };
  input.addEventListener("change",()=>clear("Bestand gewijzigd; tijdelijke weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();input.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend intrekkingscontract lokaal lezen. HOLD / DENY.");
    const generation=revision,file=input.files?.[0];
    if(dashboard.hidden||!file||file.size<1||file.size>32768){
      status.textContent="GEWEIGERD / Selecteer JSON tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const bytes=await file.arrayBuffer();
      if(generation!==revision||dashboard.hidden)return;
      const report=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
      if(!exact(report,fields)||
        Object.entries(fixed).some(([k,v])=>report[k]!==v)||
        !digest(report.trustTransitionSha256)||
        !digest(report.handoffManifestSha256)||
        !Array.isArray(report.revocationScenarios)||
        report.revocationScenarios.length!==4||
        !Array.isArray(report.recoveryChecklist)||
        report.recoveryChecklist.length!==8||
        !Array.isArray(report.trustTransitionOutcomes)||
        report.trustTransitionOutcomes.length!==3)throw Error();
      const scenarioRows=document.createDocumentFragment();
      for(let i=0;i<4;i++){
        const event=report.revocationScenarios[i];
        if(!exact(event,["event","ownerService","invalidates","propagation",
          "detection","invalidationExecution","effectiveDecision","restorePermission"])||
          event.event!==events[i]||event.ownerService!==owners[i]||
          !same(event.invalidates,invalidates[i])||
          event.propagation!=="REQUIRED_ACROSS_DEPENDENT_SERVICES"||
          event.detection!=="NOT_IMPLEMENTED"||
          event.invalidationExecution!=="NOT_EXECUTED"||
          event.effectiveDecision!=="DENY"||event.restorePermission!=="NONE")throw Error();
        const tr=document.createElement("tr");
        for(const v of [event.event,event.ownerService,
          event.invalidates.length,"NOT_EXECUTED / DENY"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }scenarioRows.append(tr);
      }
      const checklistRows=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const step=report.recoveryChecklist[i];
        if(!exact(step,["order","control","status","independentVerification",
          "authorityEffect"])||step.order!==i+1||step.control!==steps[i]||
          step.status!=="NOT_STARTED"||
          step.independentVerification!=="REQUIRED_EXTERNALLY"||
          step.authorityEffect!=="NONE")throw Error();
        const tr=document.createElement("tr");
        for(const v of [step.order,step.control,"NOT_STARTED"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }checklistRows.append(tr);
      }
      for(let i=0;i<3;i++){
        const t=report.trustTransitionOutcomes[i];
        if(!exact(t,["boundary","status","decision"])||
          t.boundary!==boundaries[i]||t.status!=="BLOCKED"||
          t.decision!=="DENY")throw Error();
      }
      if(generation!==revision||dashboard.hidden)return;
      scenarios.replaceChildren(scenarioRows);recovery.replaceChildren(checklistRows);
      status.textContent="CONTRACT HERKEND / Vier intrekkingsscenario's, acht herstelcontroles; geen intrekking of herstel uitgevoerd. HOLD / DENY.";
    }catch(_){
      if(generation!==revision||dashboard.hidden)return;
      clear("INTREKKINGSCONTRACT GEWEIGERD / Ongeldige inhoud of rechtenclaim. HOLD / DENY.");
    }
  });
})();
