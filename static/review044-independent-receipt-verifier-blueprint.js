"use strict";
// Offline read-only verifier blueprint view: no signature verification or access.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-receipt-verifier-file"),load=$("admin-receipt-verifier-load"),
    status=$("admin-receipt-verifier-status"),components=$("admin-receipt-verifier-components"),
    controls=$("admin-receipt-verifier-controls"),dashboard=$("admin-dashboard");
  if(![file,load,status,components,controls,dashboard].every(Boolean))return;
  const parts=[
    ["RECEIPT_FORMAT_GATE","CANONICAL_SCHEMA_AND_BYTE_LIMIT_ENFORCEMENT"],
    ["HANDOFF_BINDING_GATE","EXACT_HANDOFF_AND_EVIDENCE_SET_DIGEST_BINDING"],
    ["TRUST_ANCHOR_RESOLVER","PINNED_EXTERNAL_ISSUER_AND_KEY_TRUST_POLICY"],
    ["SIGNATURE_VALIDATOR","ALGORITHM_ALLOWLIST_AND_KEY_USAGE_VERIFICATION"],
    ["KEY_LIFECYCLE_GATE","KEY_ROTATION_EPOCH_AND_REVOCATION_VALIDATION"],
    ["FRESHNESS_AND_REPLAY_GATE","AUDIENCE_PURPOSE_NONCE_EXPIRY_AND_ATOMIC_REPLAY_LEDGER"],
    ["INDEPENDENT_REVIEWER_GATE","IDENTITY_SCOPE_SEPARATION_OF_DUTIES_CHECKS"],
    ["AUDIT_ANCHOR_GATE","EXTERNAL_IMMUTABLE_LOG_PROOF_AND_TRUSTED_TIME"],
    ["HUMAN_DECISION_GATE","SEPARATE_AUTHORIZED_DECISION_BOUND_TO_RECEIPT"]
  ];
  const keyRules=["TRUSTED_ISSUER_ROOT_PINNING","KID_ISSUER_AND_AUDIENCE_SCOPING",
    "ALGORITHM_ALLOWLIST_NO_DOWNGRADE","ROTATION_EPOCH_AND_OVERLAP_POLICY",
    "KEY_NOT_BEFORE_AND_NOT_AFTER_VALIDATION",
    "SIGNED_KEY_REVOCATION_FEED_AND_FRESHNESS",
    "COMPROMISED_KEY_DENY_AND_FORENSIC_ESCALATION"];
  const replayRules=["CRYPTOSAFE_SINGLE_USE_CHALLENGE_NONCE",
    "NONCE_BOUND_TO_EXACT_HANDOFF_AND_PURPOSE",
    "TRUSTED_CLOCK_WITH_MAX_SKEW",
    "ATOMIC_CONSUME_ONCE_EXTERNAL_NONCE_STORE",
    "REPLAY_STORE_OUTAGE_FAIL_CLOSED",
    "EXPIRED_MISMATCHED_OR_REUSED_NONCE_DENY"];
  const auditRules=["SIGNED_HASH_CHAINED_EXTERNAL_AUDIT_LOG",
    "INDEPENDENT_INCLUSION_AND_CONSISTENCY_PROOFS",
    "TRUSTED_TIMESTAMP_ANCHOR",
    "AUDIT_UNAVAILABILITY_FAIL_CLOSED","LEAST_PRIVILEGE_AUDIT_READER",
    "NO_PII_OR_RAW_SECRET_IN_LOG"];
  const boundaries=[
    ["UNTRUSTED_LOCAL_HANDOFF","EXTERNAL_INDEPENDENT_VERIFIER"],
    ["EXTERNAL_VERIFIER","TRUSTED_ISSUER_KEY_REGISTRY"],
    ["EXTERNAL_VERIFIER","ATOMIC_REPLAY_PROTECTION_STORE"],
    ["EXTERNAL_VERIFIER","IMMUTABLE_AUDIT_SERVICE"],
    ["VERIFIED_TECHNICAL_RECEIPT","SEPARATE_HUMAN_RELEASE_AUTHORITY"]
  ];
  const pipeline=[
    "VALIDATE_RECEIPT_SCHEMA_AND_CANONICAL_SIGNED_BYTES",
    "MATCH_HANDOFF_HASH_AND_EXACT_EVIDENCE_REFERENCE_SET",
    "VERIFY_TRUSTED_ISSUER_SIGNATURE_AND_KEY_ROTATION",
    "VERIFY_AUDIENCE_PURPOSE_FRESH_NONCE_AND_TRUSTED_TIME",
    "CHECK_REVIEWER_IDENTITY_ROLE_SCOPE_AND_INDEPENDENCE",
    "CHECK_CREDENTIAL_ROLE_AND_SIGNING_KEY_REVOCATION",
    "VERIFY_EXTERNAL_AUDIT_ANCHOR_AND_DECISION_PROVENANCE",
    "REQUIRE_SEPARATE_AUTHORIZED_HUMAN_DECISION"
  ];
  const failures=["RECEIPT_MISSING","UNTRUSTED_ISSUER_OR_KEY",
    "INVALID_OR_UNSUPPORTED_SIGNATURE","HANDOFF_OR_EVIDENCE_HASH_MISMATCH",
    "EXPIRED_OR_REPLAYED_CHALLENGE",
    "UNVERIFIED_REVIEWER_SCOPE_OR_INDEPENDENCE",
    "REVOKED_CREDENTIAL_OR_SIGNING_KEY",
    "EXTERNAL_AUDIT_NOT_VERIFIABLE","TRUSTED_CLOCK_UNAVAILABLE",
    "AUTHORIZED_HUMAN_DECISION_ABSENT"];
  const fixed={
    schema:"palaco.pp.recovery-002-independent-receipt-verifier-blueprint.v0",
    reference:"PP-RECOVERY-002",
    contractBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    signingKeyMaterial:"NOT_PRESENT",trustedIssuers:"NOT_CONFIGURED",
    signatureValidation:"NOT_IMPLEMENTED",nonceLedger:"NOT_CONFIGURED",
    trustedClock:"NOT_CONFIGURED",auditService:"NOT_CONFIGURED",
    independentVerifier:"NOT_DEPLOYED",humanReview:"NOT_COMPLETED",
    receiptAcceptance:"NOT_PERFORMED",receiptDelivery:"NOT_SENT",
    reviewerAuthority:"NOT_ESTABLISHED",
    independentVerification:"NOT_VERIFIED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(x,keys)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let revision=0;
  const clear=(msg="Geen Receipt Verifier Blueprint geladen. HOLD / DENY.")=>{
    revision++;components.replaceChildren();controls.replaceChildren();
    status.textContent=msg;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Lokaal onuitgevoerd verificatieontwerp lezen. HOLD / DENY.");
    const active=revision,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(active!==revision||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"receiptProtocolSha256",
        "reviewHandoffSha256","serviceComponents","keyLifecycleControls",
        "replayProtectionControls","auditControls","trustBoundaries",
        "verificationPipeline","failurePolicy"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.receiptProtocolSha256)||!sha(data.reviewHandoffSha256))throw Error();
      const list=document.createDocumentFragment();
      if(!Array.isArray(data.serviceComponents)||data.serviceComponents.length!==9)throw Error();
      for(let i=0;i<parts.length;i++){
        const x=data.serviceComponents[i];
        if(!exact(x,["componentId","responsibility","implementation","runtimeState"])||
          x.componentId!==parts[i][0]||x.responsibility!==parts[i][1]||
          x.implementation!=="NOT_IMPLEMENTED"||x.runtimeState!=="BLOCKED")throw Error();
        const li=document.createElement("li");
        li.textContent=x.componentId+" — NOT_IMPLEMENTED / BLOCKED";list.append(li);
      }
      const entries=document.createDocumentFragment();
      for(const [field,expected] of [["keyLifecycleControls",keyRules],
        ["replayProtectionControls",replayRules],["auditControls",auditRules]]){
        const items=data[field];
        if(!Array.isArray(items)||items.length!==expected.length)throw Error();
        for(let i=0;i<items.length;i++){
          const x=items[i];
          if(!exact(x,["requirementId","implementation","verification"])||
            x.requirementId!==expected[i]||x.implementation!=="NOT_CONFIGURED"||
            x.verification!=="NOT_PERFORMED")throw Error();
          const li=document.createElement("li");
          li.textContent=x.requirementId+" — NOT_CONFIGURED";entries.append(li);
        }
      }
      if(!Array.isArray(data.trustBoundaries)||
        data.trustBoundaries.length!==boundaries.length||
        !Array.isArray(data.verificationPipeline)||
        data.verificationPipeline.length!==pipeline.length||
        !Array.isArray(data.failurePolicy)||
        data.failurePolicy.length!==failures.length)throw Error();
      for(let i=0;i<boundaries.length;i++){
        const x=data.trustBoundaries[i];
        if(!exact(x,["from","to","authentication","accessDecision"])||
          x.from!==boundaries[i][0]||x.to!==boundaries[i][1]||
          x.authentication!=="NOT_ESTABLISHED"||
          x.accessDecision!=="DENY")throw Error();
      }
      for(let i=0;i<pipeline.length;i++){
        const x=data.verificationPipeline[i];
        if(!exact(x,["order","step","execution","gate"])||
          x.order!==i+1||x.step!==pipeline[i]||
          x.execution!=="NOT_PERFORMED"||x.gate!=="BLOCKED")throw Error();
      }
      for(let i=0;i<failures.length;i++){
        const x=data.failurePolicy[i];
        if(!exact(x,["failure","decision","authorityEffect"])||
          x.failure!==failures[i]||x.decision!=="DENY"||
          x.authorityEffect!=="NONE")throw Error();
      }
      if(active!==revision||dashboard.hidden)return;
      components.replaceChildren(list);controls.replaceChildren(entries);
      status.textContent="BLAUWDRUK HERKEND / 9 componenten geblokkeerd, 19 controles niet geconfigureerd. Geen echte ontvangstverificatie. HOLD / DENY.";
    }catch(_){
      if(active!==revision||dashboard.hidden)return;
      clear("RECEIPT VERIFIER BLUEPRINT GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
