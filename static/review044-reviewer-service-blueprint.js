"use strict";
// Static local renderer for an UNIMPLEMENTED reviewer identity service blueprint.
// Never authenticates, authorizes or audits a user.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-reviewer-service-file"),button=$("admin-reviewer-service-load"),
    status=$("admin-reviewer-service-status"),services=$("admin-reviewer-service-services"),
    checks=$("admin-reviewer-service-requirements"),dashboard=$("admin-dashboard");
  if(![file,button,status,services,checks,dashboard].every(Boolean))return;
  const boundaries=["AUTHENTICATION","AUTHORIZATION","AUDIT"];
  const outputNames=["IDENTITY_ASSERTION","REVIEWER_SCOPE_DECISION",
    "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE"];
  const capabilities=[
    ["PINNED_TRUSTED_ISSUER","AUDIENCE_AND_PURPOSE_BOUND_CHALLENGE",
      "SIGNATURE_AND_ALGORITHM_ALLOWLIST","TRUSTED_CLOCK_EXPIRY",
      "NONCE_REPLAY_PREVENTION","ISSUER_KEY_REVOCATION"],
    ["INDEPENDENT_ROLE_ATTESTATION","EXPLICIT_PP_RECOVERY_002_SCOPE",
      "LEAST_PRIVILEGE_AND_SEPARATION","REVOCATION_AND_CONFLICT_CHECK",
      "DENY_BY_DEFAULT","NO_PALACO_ONE_SESSION_DELEGATION"],
    ["MANIFEST_BYTE_DIGEST_BOUND_RECEIPT","REVIEWER_SIGNED_RECEIPT",
      "EXTERNALLY_ANCHORED_EVENT","TRUSTED_TIMESTAMP",
      "INDEPENDENT_RECEIPT_VERIFICATION","NO_LOCAL_CHAIN_AS_ATTESTATION"]
  ];
  const controls=["TRUSTED_IDENTITY_PROVIDER","CRYPTOGRAPHIC_CHALLENGE",
    "REVIEWER_ROLE_ATTESTATION","POLICY_SCOPE_MATCH","REPLAY_AND_EXPIRY",
    "SEPARATION_OF_DUTIES","SIGNED_RECEIPT","AUDIT_ANCHOR"];
  const gates=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const fixed={
    schema:"palaco.pp.recovery-002-reviewer-service-blueprint.v0",
    reference:"PP-RECOVERY-002",
    crossBoundaryRule:"NO_SELF_REPORTED_CLAIM_CAN_GRANT_AUTHORITY",
    identityProviderIntegration:"NOT_CONFIGURED",
    credentialValidation:"NOT_PERFORMED",
    authorizationService:"NOT_IMPLEMENTED",
    auditService:"NOT_IMPLEMENTED",
    reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    independentAudit:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",
    releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const fields=[...Object.keys(fixed),"reviewerAuthContractSha256",
    "handoffManifestSha256","reviewProtocolSha256","services",
    "requirements","decisionGates"];
  const exact=(x,keys)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const sha=v=>typeof v==="string"&&/^[0-9a-f]{64}$/.test(v);
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
  let revision=0;
  const reset=(message="Geen identiteitsarchitectuur geladen. HOLD / DENY.")=>{
    revision++;services.replaceChildren();checks.replaceChildren();status.textContent=message;
  };
  file.addEventListener("change",()=>reset("Bestand gewijzigd; vorige weergave gewist. HOLD / DENY."));
  const logout=()=>{reset();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    reset("Architectuur lokaal lezen. HOLD / DENY.");
    const at=revision,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>32768){
      status.textContent="GEWEIGERD / Kies een lokaal architectuurrapport van maximaal 32 KiB. HOLD / DENY.";return;
    }
    try{
      const raw=await f.arrayBuffer();
      if(at!==revision||dashboard.hidden)return;
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(raw));
      if(!exact(data,fields)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        ![data.reviewerAuthContractSha256,data.handoffManifestSha256,
          data.reviewProtocolSha256].every(sha)||
        !Array.isArray(data.services)||data.services.length!==3||
        !Array.isArray(data.requirements)||data.requirements.length!==8||
        !Array.isArray(data.decisionGates)||data.decisionGates.length!==5)throw Error();
      const serviceRows=document.createDocumentFragment();
      for(let i=0;i<3;i++){
        const s=data.services[i];
        if(!exact(s,["boundary","futureOutput","requiredCapabilities",
          "implementation","trustEvaluation","outboundAuthority"])||
          s.boundary!==boundaries[i]||s.futureOutput!==outputNames[i]||
          !same(s.requiredCapabilities,capabilities[i])||
          s.implementation!=="NOT_IMPLEMENTED"||
          s.trustEvaluation!=="NOT_PERFORMED"||s.outboundAuthority!=="NONE")throw Error();
        const tr=document.createElement("tr");
        for(const v of [s.boundary,s.futureOutput,s.requiredCapabilities.length,s.implementation]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }serviceRows.append(tr);
      }
      const requirements=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const r=data.requirements[i];
        if(!exact(r,["controlId","status"])||
          r.controlId!==controls[i]||r.status!=="NOT_ESTABLISHED")throw Error();
        const li=document.createElement("li");
        li.textContent=r.controlId+" — "+r.status;
        requirements.append(li);
      }
      for(let i=0;i<5;i++){
        const g=data.decisionGates[i];
        if(!exact(g,["requirementId","gate"])||g.requirementId!==gates[i]||
          g.gate!=="BLOCKED")throw Error();
      }
      if(at!==revision||dashboard.hidden)return;
      services.replaceChildren(serviceRows);checks.replaceChildren(requirements);
      status.textContent="ARCHITECTUUR HERKEND / Authenticatie, autorisatie en audit zijn NIET geïmplementeerd. Geen vertrouwde identity provider of reviewerbevoegdheid. HOLD / DENY.";
    }catch(_){
      if(at!==revision||dashboard.hidden)return;
      reset("ARCHITECTUUR GEWEIGERD / Ongeldige bronclaim of afwijkende blokkadestatus. HOLD / DENY.");
    }
  });
})();
