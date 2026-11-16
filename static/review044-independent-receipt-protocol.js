"use strict";
// Read-only independent receipt requirements. Not a signed receipt or verifier.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-independent-receipt-file"),
    button=$("admin-independent-receipt-load"),
    status=$("admin-independent-receipt-status"),
    fields=$("admin-independent-receipt-fields"),
    steps=$("admin-independent-receipt-steps"),
    dashboard=$("admin-dashboard");
  if(![file,button,status,fields,steps,dashboard].every(Boolean))return;
  const requiredFields=[
    "RECEIPT_SCHEMA_AND_PROTOCOL_VERSION","EXACT_HANDOFF_SHA256",
    "INDEPENDENT_ISSUER_ID_AND_AUDIENCE","REVIEWER_SUBJECT_AND_ROLE_SCOPE",
    "INDEPENDENCE_AND_SEPARATION_OF_DUTIES_ATTESTATION",
    "CHALLENGE_NONCE_AND_PURPOSE_BINDING",
    "TRUSTED_ISSUED_AT_AND_EXPIRES_AT",
    "SIGNED_EVIDENCE_REFERENCE_SET_SHA256",
    "EXTERNAL_IMMUTABLE_AUDIT_ANCHOR",
    "AUTHORIZED_REVIEW_DECISION_REFERENCE",
    "SIGNING_KEY_ID_AND_SIGNATURE_ALGORITHM",
    "DETACHED_CRYPTOGRAPHIC_SIGNATURE"
  ];
  const verificationSteps=[
    "VALIDATE_RECEIPT_SCHEMA_AND_CANONICAL_SIGNED_BYTES",
    "MATCH_HANDOFF_HASH_AND_EXACT_EVIDENCE_REFERENCE_SET",
    "VERIFY_TRUSTED_ISSUER_SIGNATURE_AND_KEY_ROTATION",
    "VERIFY_AUDIENCE_PURPOSE_FRESH_NONCE_AND_TRUSTED_TIME",
    "CHECK_REVIEWER_IDENTITY_ROLE_SCOPE_AND_INDEPENDENCE",
    "CHECK_CREDENTIAL_ROLE_AND_SIGNING_KEY_REVOCATION",
    "VERIFY_EXTERNAL_AUDIT_ANCHOR_AND_DECISION_PROVENANCE",
    "REQUIRE_SEPARATE_AUTHORIZED_HUMAN_DECISION"
  ];
  const failureCodes=[
    "RECEIPT_MISSING","UNTRUSTED_ISSUER_OR_KEY",
    "INVALID_OR_UNSUPPORTED_SIGNATURE","HANDOFF_OR_EVIDENCE_HASH_MISMATCH",
    "EXPIRED_OR_REPLAYED_CHALLENGE",
    "UNVERIFIED_REVIEWER_SCOPE_OR_INDEPENDENCE",
    "REVOKED_CREDENTIAL_OR_SIGNING_KEY","EXTERNAL_AUDIT_NOT_VERIFIABLE",
    "TRUSTED_CLOCK_UNAVAILABLE","AUTHORIZED_HUMAN_DECISION_ABSENT"
  ];
  const review=[
    "EXTERNAL_REVIEWER_IDENTITY_AUTHENTICATION",
    "INDEPENDENT_ROLE_AND_SCOPE_ATTESTATION",
    "REVOCATION_AND_SEPARATION_OF_DUTIES_CHECK",
    "ORIGINAL_EVIDENCE_BYTES_AND_PROVENANCE_VERIFICATION",
    "SIGNED_RECEIPT_BOUND_TO_EXACT_HANDOFF_SHA256",
    "EXTERNAL_AUDIT_ANCHOR_AND_TRUSTED_TIME",
    "AUTHORIZED_HUMAN_REVIEW_DECISION"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-independent-review-receipt-protocol.v0",
    reference:"PP-RECOVERY-002",
    sourceBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    evidenceAcceptance:"NOT_PERFORMED",receiptSubmission:"NOT_IMPLEMENTED",
    delivery:"NOT_SENT",independentVerifier:"NOT_CONFIGURED",
    trustedClock:"NOT_CONFIGURED",revocationCheck:"NOT_PERFORMED",
    auditAnchoring:"NOT_IMPLEMENTED",reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",signedReceipt:"NOT_AVAILABLE",
    humanReview:"NOT_COMPLETED",independentVerification:"NOT_VERIFIED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",accessDecision:"DENY",
    issuance:"NOT_AUTHORIZED"
  };
  const profile={
    requiredFormat:"CANONICAL_SIGNED_EXTERNAL_ENVELOPE",
    signatureAlgorithm:"TRUST_POLICY_DEFINED_NOT_CONFIGURED",
    keyTrustSource:"EXTERNAL_AUTHORITY_NOT_CONFIGURED",
    receiptBytes:"NOT_PRESENT",signatureVerification:"NOT_IMPLEMENTED"
  };
  const exact=(x,k)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===k.length&&k.every(y=>Object.hasOwn(x,y));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let generation=0;
  function clear(m="Geen Independent Review Receipt Protocol geladen. HOLD / DENY."){
    generation++;fields.replaceChildren();steps.replaceChildren();status.textContent=m;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Ongetekend ontvangstprotocol lokaal lezen. HOLD / DENY.");
    const current=generation,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(current!==generation||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"reviewHandoffSha256",
        "executionPlanSha256","observationRegisterSha256","evidenceIntakeSha256",
        "receiptProfile","externalVerification","failureBehavior",
        "reviewRequirements","evidenceReferenceCount"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !["reviewHandoffSha256","executionPlanSha256","observationRegisterSha256",
          "evidenceIntakeSha256"].every(k=>sha(data[k]))||
        !Number.isInteger(data.evidenceReferenceCount)||
        data.evidenceReferenceCount<0||data.evidenceReferenceCount>64||
        !exact(data.receiptProfile,[...Object.keys(profile),"requiredFields"])||
        Object.entries(profile).some(([k,v])=>data.receiptProfile[k]!==v)||
        !Array.isArray(data.receiptProfile.requiredFields)||
        data.receiptProfile.requiredFields.length!==12||
        !Array.isArray(data.externalVerification)||data.externalVerification.length!==8||
        !Array.isArray(data.failureBehavior)||data.failureBehavior.length!==10||
        !Array.isArray(data.reviewRequirements)||data.reviewRequirements.length!==7)throw Error();
      const fieldList=document.createDocumentFragment();
      for(let i=0;i<12;i++){
        const x=data.receiptProfile.requiredFields[i];
        if(!exact(x,["fieldId","status"])||x.fieldId!==requiredFields[i]||
          x.status!=="MISSING")throw Error();
        const li=document.createElement("li");li.textContent=x.fieldId+" — MISSING";
        fieldList.append(li);
      }
      const stepList=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=data.externalVerification[i];
        if(!exact(x,["order","check","status","gate"])||
          x.order!==i+1||x.check!==verificationSteps[i]||
          x.status!=="NOT_PERFORMED"||x.gate!=="BLOCKED")throw Error();
        const li=document.createElement("li");li.textContent=x.check+" — NOT_PERFORMED";
        stepList.append(li);
      }
      for(let i=0;i<10;i++){
        const x=data.failureBehavior[i];
        if(!exact(x,["failure","decision","authorityEffect"])||
          x.failure!==failureCodes[i]||x.decision!=="DENY"||
          x.authorityEffect!=="NONE")throw Error();
      }
      for(let i=0;i<7;i++){
        const x=data.reviewRequirements[i];
        if(!exact(x,["requirement","status"])||
          x.requirement!==review[i]||x.status!=="NOT_STARTED")throw Error();
      }
      if(current!==generation||dashboard.hidden)return;
      fields.replaceChildren(fieldList);steps.replaceChildren(stepList);
      status.textContent="ONGETEKEND CONTRACT / 12 ontvangstvelden MISSING, 8 externe checks NOT_PERFORMED. Geen ontvangst of autorisatie. HOLD / DENY.";
    }catch(_){
      if(current!==generation||dashboard.hidden)return;
      clear("ONTVANGSTPROTOCOL GEWEIGERD / Ongeldige structuur of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
