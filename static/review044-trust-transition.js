"use strict";
// View-only, unsigned LOCAL transition specification. No authority, runtime or network.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-trust-transition-file"),button=$("admin-trust-transition-load"),
    status=$("admin-trust-transition-status"),
    rows=$("admin-trust-transition-rows"),failures=$("admin-trust-transition-errors"),
    dashboard=$("admin-dashboard");
  if(![file,button,status,rows,failures,dashboard].every(Boolean))return;
  const boundaries=["AUTHENTICATION_TO_AUTHORIZATION",
    "AUTHORIZATION_TO_AUDIT","AUDIT_TO_MANUAL_REVIEW"];
  const inputs=["IDENTITY_ASSERTION","REVIEWER_SCOPE_DECISION",
    "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE"];
  const outputs=["REVIEWER_SCOPE_DECISION",
    "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE",
    "EXTERNAL_AUTHORIZED_HUMAN_REVIEW"];
  const conditions=[
    ["EXTERNAL_IDENTITY_ASSERTION_SIGNATURE_VERIFIED",
     "ISSUER_AUDIENCE_PURPOSE_AND_NONCE_VERIFIED",
     "TRUSTED_TIME_AND_CREDENTIAL_REVOCATION_VERIFIED",
     "INDEPENDENT_REVIEWER_ROLE_ATTESTATION_REQUIRED"],
    ["POLICY_SCOPE_AND_LEAST_PRIVILEGE_VERIFIED",
     "SEPARATION_OF_DUTIES_AND_ROLE_REVOCATION_VERIFIED",
     "EXACT_HANDOFF_MANIFEST_SHA256_BOUND",
     "INDEPENDENT_SIGNING_AND_EXTERNAL_AUDIT_REQUIRED"],
    ["RECEIPT_SIGNATURE_INDEPENDENTLY_VERIFIED",
     "EXTERNAL_AUDIT_ANCHOR_VERIFIED",
     "TRUSTED_TIMESTAMP_AND_REVOCATION_VERIFIED",
     "SEPARATE_HUMAN_REVIEW_DECISION_REQUIRED"]
  ];
  const errorCodes=["UNKNOWN_OR_MALFORMED_PROOF","ISSUER_OR_AUDIENCE_MISMATCH",
    "EXPIRED_OR_REPLAYED_CHALLENGE","CREDENTIAL_OR_ROLE_REVOKED",
    "INVALID_OR_MISSING_SIGNATURE","SCOPE_OR_INDEPENDENCE_VIOLATION",
    "AUDIT_UNAVAILABLE_OR_UNVERIFIABLE","TRUSTED_CLOCK_UNAVAILABLE",
    "DEPENDENCY_UNAVAILABLE"];
  const fixed={
    schema:"palaco.pp.recovery-002-trust-transition.v0",
    reference:"PP-RECOVERY-002",
    replayState:"NOT_CONFIGURED",
    revocationValidation:"NOT_PERFORMED",
    independentEvidenceVerification:"NOT_PERFORMED",
    crossBoundaryRule:"NO_CLAIM_ALONE_CAN_ADVANCE_ANY_TRANSITION",
    implementation:"NOT_IMPLEMENTED",
    reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    externalHumanReview:"NOT_COMPLETED",
    releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const keys=[...Object.keys(fixed),"interfaceContractSha256",
    "handoffManifestSha256","transitions","failureBehavior"];
  const exact=(x,k)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===k.length&&k.every(y=>Object.hasOwn(x,y));
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
  const hex=s=>typeof s==="string"&&/^[0-9a-f]{64}$/.test(s);
  let generation=0;
  function clear(message="Geen overgangscontract geladen. HOLD / DENY."){
    generation++;rows.replaceChildren();failures.replaceChildren();
    status.textContent=message;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal overgangscontract lezen. HOLD / DENY.");
    const current=generation,chosen=file.files?.[0];
    if(dashboard.hidden||!chosen||chosen.size<1||chosen.size>32768){
      status.textContent="GEWEIGERD / Kies JSON tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const raw=await chosen.arrayBuffer();
      if(current!==generation||dashboard.hidden)return;
      const record=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(raw));
      if(!exact(record,keys)||Object.entries(fixed).some(([k,v])=>record[k]!==v)||
        !hex(record.interfaceContractSha256)||!hex(record.handoffManifestSha256)||
        !Array.isArray(record.transitions)||record.transitions.length!==3||
        !Array.isArray(record.failureBehavior)||record.failureBehavior.length!==9)throw Error();
      const trRows=document.createDocumentFragment();
      for(let i=0;i<3;i++){
        const t=record.transitions[i];
        if(!exact(t,["sequence","boundary","requiredInput","futureOutput",
            "independentPreconditions","proofAcceptance","status","decision"])||
          t.sequence!==i+1||t.boundary!==boundaries[i]||
          t.requiredInput!==inputs[i]||t.futureOutput!==outputs[i]||
          !same(t.independentPreconditions,conditions[i])||
          t.proofAcceptance!=="NOT_IMPLEMENTED"||t.status!=="BLOCKED"||
          t.decision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const value of [t.sequence,t.boundary,t.independentPreconditions.length,
          "BLOCKED / DENY"]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }
        trRows.append(tr);
      }
      const errorRows=document.createDocumentFragment();
      for(let i=0;i<9;i++){
        const e=record.failureBehavior[i];
        if(!exact(e,["failure","effect","releaseEffect"])||
          e.failure!==errorCodes[i]||e.effect!=="DENY"||
          e.releaseEffect!=="NONE")throw Error();
        const li=document.createElement("li");
        li.textContent=e.failure+" — DENY";
        errorRows.append(li);
      }
      if(current!==generation||dashboard.hidden)return;
      rows.replaceChildren(trRows);failures.replaceChildren(errorRows);
      status.textContent="OVERGANGSCONTRACT HERKEND / Drie overgangen geblokkeerd, negen foutcategorieën DENY. Geen identiteitscontrole of vrijgave uitgevoerd. HOLD / DENY.";
    }catch(_){
      if(current!==generation||dashboard.hidden)return;
      clear("OVERGANGSCONTRACT GEWEIGERD / Tegenstrijdige of ongeldige claims. HOLD / DENY.");
    }
  });
})();
