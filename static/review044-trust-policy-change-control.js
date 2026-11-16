"use strict";
// Read-only hypothetical trust policy changes; no policy updates or approval.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-trust-change-file"),load=$("admin-trust-change-load"),
    status=$("admin-trust-change-status"),rows=$("admin-trust-change-rows"),
    reviewers=$("admin-trust-change-reviewers"),dashboard=$("admin-dashboard");
  if(![file,load,status,rows,reviewers,dashboard].every(Boolean))return;
  const categories={
    ISSUER_POLICY:["EXTERNALLY_APPROVED_ISSUER_ROOT","ISSUER_ID_AND_RECEIPT_AUDIENCE_BINDING","TRUST_ANCHOR_PROVENANCE_AND_OWNER_AUTHORIZATION","INDEPENDENT_ISSUER_ONBOARDING_REVIEW","ISSUER_REVOCATION_AND_EMERGENCY_DENY"],
    ALGORITHM_POLICY:["EXPLICIT_ALGORITHM_ALLOWLIST_NOT_WILDCARD","NO_ALG_NONE_OR_SYMMETRIC_ASYMMETRIC_CONFUSION","KEY_TYPE_CURVE_AND_USAGE_MATCH","CANONICAL_SIGNED_BYTES_NO_REENCODING","DOWNGRADE_AND_UNSUPPORTED_ALGORITHM_DENY"],
    KEY_ROTATION_POLICY:["ISSUER_SCOPED_KID_UNIQUENESS","PINNED_ROOT_AND_SIGNED_KEYSET_UPDATES","KEY_VALIDITY_WITH_TRUSTED_CLOCK","ROTATION_EPOCH_AND_SIGNED_OVERLAP_POLICY","HISTORICAL_KEY_VERIFICATION_ONLY_UNDER_AUTHORIZED_POLICY","NO_KEY_MATERIAL_IN_LOCAL_REPORTS"],
    REVOCATION_POLICY:["SIGNED_FRESH_ISSUER_REVOCATION_FEED","KEY_AND_REVIEWER_CREDENTIAL_REVOCATION","TRUST_ROOT_REMOVAL_FAIL_CLOSED","REVOCATION_FEED_OUTAGE_FAIL_CLOSED","COMPROMISE_RESPONSE_REQUIRES_INDEPENDENT_REVIEW","NO_OFFLINE_STALE_TRUST_FALLBACK"]
  };
  const changeTypes=["PROPOSE_REQUIREMENT_REVISION","PROPOSE_NEW_TRUST_ROOT","PROPOSE_ALGORITHM_ALLOWLIST","PROPOSE_KEY_ROTATION","PROPOSE_REVOCATION_POLICY"];
  const reassessment=["ORIGINAL_SOURCE_AND_HANDOFF_BINDING","INDEPENDENT_ISSUER_IDENTITY_AND_ROOT_ATTESTATION","CRYPTOGRAPHIC_ALGORITHM_AND_KEY_USAGE","KEY_ROTATION_OVERLAP_AND_ROLLBACK","SIGNED_FRESH_REVOCATION_FEED","NONCE_REPLAY_LEDGER_AND_TRUSTED_CLOCK","EXTERNAL_AUDIT_AND_INCLUSION_PROOF","INDEPENDENT_REVIEWER_ROLE_AND_SEPARATION_OF_DUTIES","SEPARATE_AUTHORIZED_HUMAN_RELEASE_DECISION"];
  const roles=["INDEPENDENT_SECURITY_REVIEWER","AUTHORIZED_TRUST_POLICY_OWNER","INDEPENDENT_RELEASE_ATTESTOR"];
  const denies=["UNKNOWN_ISSUER","UNPINNED_TRUST_ROOT","MISSING_TRUSTED_KEY","UNSUPPORTED_SIGNATURE_ALGORITHM","EXPIRED_SIGNING_KEY","REVOKED_KEY_OR_REVIEWER","STALE_REVOCATION_FEED","TRUSTED_CLOCK_UNAVAILABLE","REPLAY_LEDGER_UNAVAILABLE","INDEPENDENT_REVIEWER_UNAUTHENTICATED","AUDIT_ANCHOR_UNVERIFIABLE","HUMAN_RELEASE_DECISION_MISSING"];
  const fixed={schema:"palaco.pp.recovery-002-trust-policy-change-control.v0",
    reference:"PP-RECOVERY-002",scope:"UNSIGNED_HYPOTHETICAL_POLICY_PROPOSAL_ONLY",
    changeAuthorization:"DENY",deploymentAuthorization:"DENY",
    issuerPromotion:"PROHIBITED",algorithmPromotion:"PROHIBITED",
    keyMaterial:"NOT_PRESENT",trustedIssuerCount:0,
    independentVerification:"NOT_VERIFIED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"};
  const shape=(o,k)=>o&&typeof o==="object"&&!Array.isArray(o)&&Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let generation=0;
  function clear(msg="Geen Trust Policy Change Control geladen. HOLD / DENY."){
    generation++;rows.replaceChildren();reviewers.replaceChildren();status.textContent=msg;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();}).observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Hypothetische beleidswijziging lokaal lezen. HOLD / DENY.");
    const ticket=generation,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(ticket!==generation||dashboard.hidden)return;
      if(!shape(data,[...Object.keys(fixed),"trustPolicySha256","verifierBlueprintSha256",
        "changeRequest","affectedPolicyRequirements","transitiveImpact",
        "releaseReassessment","requiredIndependentReviewers",
        "defaultDenialReasons","allowedAlgorithms"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.trustPolicySha256)||!sha(data.verifierBlueprintSha256)||
        !Array.isArray(data.allowedAlgorithms)||data.allowedAlgorithms.length!==0||
        !shape(data.changeRequest,["category","changeType","proposedTrustMaterial",
          "proposedPolicyBytes","changeApplied","externalReview"])||
        !Object.hasOwn(categories,data.changeRequest.category)||
        !changeTypes.includes(data.changeRequest.changeType)||
        data.changeRequest.proposedTrustMaterial!=="NOT_PROVIDED"||
        data.changeRequest.proposedPolicyBytes!=="NOT_PROVIDED"||
        data.changeRequest.changeApplied!==false||
        data.changeRequest.externalReview!=="NOT_STARTED")throw Error();
      const requirements=categories[data.changeRequest.category];
      if(!Array.isArray(data.affectedPolicyRequirements)||
        data.affectedPolicyRequirements.length!==requirements.length||
        !Array.isArray(data.transitiveImpact)||data.transitiveImpact.length!==4||
        !Array.isArray(data.releaseReassessment)||data.releaseReassessment.length!==9||
        !Array.isArray(data.requiredIndependentReviewers)||
        data.requiredIndependentReviewers.length!==3||
        !Array.isArray(data.defaultDenialReasons)||
        data.defaultDenialReasons.length!==12)throw Error();
      const display=document.createDocumentFragment();
      for(let i=0;i<requirements.length;i++){
        const x=data.affectedPolicyRequirements[i];
        if(!shape(x,["order","requirementId","assessment","verification"])||
          x.order!==i+1||x.requirementId!==requirements[i]||
          x.assessment!=="REASSESSMENT_REQUIRED"||
          x.verification!=="NOT_PERFORMED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [x.order,x.requirementId,x.assessment]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }display.append(tr);
      }
      for(const [i,category] of Object.keys(categories).entries()){
        const x=data.transitiveImpact[i];
        if(!shape(x,["category","status","verification"])||x.category!==category||
          x.status!=="REVALIDATION_REQUIRED"||x.verification!=="NOT_PERFORMED")throw Error();
      }
      for(let i=0;i<9;i++){
        const x=data.releaseReassessment[i];
        if(!shape(x,["order","gate","status","independentVerification"])||
          x.order!==i+1||x.gate!==reassessment[i]||x.status!=="BLOCKED"||
          x.independentVerification!=="NOT_PERFORMED")throw Error();
      }
      const list=document.createDocumentFragment();
      for(let i=0;i<3;i++){
        const x=data.requiredIndependentReviewers[i];
        if(!shape(x,["role","authentication","authority","decision"])||
          x.role!==roles[i]||x.authentication!=="NOT_ESTABLISHED"||
          x.authority!=="NOT_ESTABLISHED"||x.decision!=="NOT_COMPLETED")throw Error();
        const li=document.createElement("li");li.textContent=x.role+" — NOT_ESTABLISHED";
        list.append(li);
      }
      for(let i=0;i<12;i++){
        const x=data.defaultDenialReasons[i];
        if(!shape(x,["reason","decision"])||x.reason!==denies[i]||
          x.decision!=="DENY")throw Error();
      }
      if(ticket!==generation||dashboard.hidden)return;
      rows.replaceChildren(display);reviewers.replaceChildren(list);
      status.textContent="VOORSTEL HERKEND / "+data.changeRequest.category+
        " — NIET TOEGEPAST. 9 herbeoordelingen BLOCKED. HOLD / DENY.";
    }catch(_){
      if(ticket!==generation||dashboard.hidden)return;
      clear("CHANGE CONTROL GEWEIGERD / Ongeldig contract of tegenstrijdige status. HOLD / DENY.");
    }
  });
})();
