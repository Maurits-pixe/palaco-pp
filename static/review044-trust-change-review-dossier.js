"use strict";
// View-only unsigned trust change review request. Never performs an approval.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-change-dossier-file"),button=$("admin-change-dossier-load"),
    status=$("admin-change-dossier-status"),evidence=$("admin-change-dossier-evidence"),
    gates=$("admin-change-dossier-gates"),dashboard=$("admin-dashboard");
  if(![file,button,status,evidence,gates,dashboard].every(Boolean))return;
  const categories={
    ISSUER_POLICY:["EXTERNALLY_APPROVED_ISSUER_ROOT","ISSUER_ID_AND_RECEIPT_AUDIENCE_BINDING","TRUST_ANCHOR_PROVENANCE_AND_OWNER_AUTHORIZATION","INDEPENDENT_ISSUER_ONBOARDING_REVIEW","ISSUER_REVOCATION_AND_EMERGENCY_DENY"],
    ALGORITHM_POLICY:["EXPLICIT_ALGORITHM_ALLOWLIST_NOT_WILDCARD","NO_ALG_NONE_OR_SYMMETRIC_ASYMMETRIC_CONFUSION","KEY_TYPE_CURVE_AND_USAGE_MATCH","CANONICAL_SIGNED_BYTES_NO_REENCODING","DOWNGRADE_AND_UNSUPPORTED_ALGORITHM_DENY"],
    KEY_ROTATION_POLICY:["ISSUER_SCOPED_KID_UNIQUENESS","PINNED_ROOT_AND_SIGNED_KEYSET_UPDATES","KEY_VALIDITY_WITH_TRUSTED_CLOCK","ROTATION_EPOCH_AND_SIGNED_OVERLAP_POLICY","HISTORICAL_KEY_VERIFICATION_ONLY_UNDER_AUTHORIZED_POLICY","NO_KEY_MATERIAL_IN_LOCAL_REPORTS"],
    REVOCATION_POLICY:["SIGNED_FRESH_ISSUER_REVOCATION_FEED","KEY_AND_REVIEWER_CREDENTIAL_REVOCATION","TRUST_ROOT_REMOVAL_FAIL_CLOSED","REVOCATION_FEED_OUTAGE_FAIL_CLOSED","COMPROMISE_RESPONSE_REQUIRES_INDEPENDENT_REVIEW","NO_OFFLINE_STALE_TRUST_FALLBACK"]
  };
  const changes=["PROPOSE_REQUIREMENT_REVISION","PROPOSE_NEW_TRUST_ROOT",
    "PROPOSE_ALGORITHM_ALLOWLIST","PROPOSE_KEY_ROTATION","PROPOSE_REVOCATION_POLICY"];
  const evidenceList=[
    ["PINNED_TRUST_ROOT_AND_ISSUER_PROVENANCE","INDEPENDENT_SECURITY_REVIEWER"],
    ["SIGNED_CANONICAL_POLICY_DIFF","AUTHORIZED_TRUST_POLICY_OWNER"],
    ["KEY_AND_ALGORITHM_COMPATIBILITY_ASSESSMENT","INDEPENDENT_SECURITY_REVIEWER"],
    ["ROTATION_AND_REVOKE_SIGNED_FEED_EVIDENCE","INDEPENDENT_SECURITY_REVIEWER"],
    ["NONCE_REPLAY_TRUSTED_CLOCK_RECHECK","INDEPENDENT_SECURITY_REVIEWER"],
    ["IMMUTABLE_EXTERNAL_AUDIT_INCLUSION_PROOF","INDEPENDENT_RELEASE_ATTESTOR"],
    ["INDEPENDENT_IDENTITY_SCOPE_SEPARATION_OF_DUTIES","AUTHORIZED_TRUST_POLICY_OWNER"],
    ["REPRODUCIBLE_NEGATIVE_AND_REGRESSION_TEST_PROVENANCE","INDEPENDENT_RELEASE_ATTESTOR"],
    ["SEPARATE_SIGNED_HUMAN_DECISION","AUTHORIZED_TRUST_POLICY_OWNER"]
  ];
  const reassessment=["ORIGINAL_SOURCE_AND_HANDOFF_BINDING",
    "INDEPENDENT_ISSUER_IDENTITY_AND_ROOT_ATTESTATION",
    "CRYPTOGRAPHIC_ALGORITHM_AND_KEY_USAGE","KEY_ROTATION_OVERLAP_AND_ROLLBACK",
    "SIGNED_FRESH_REVOCATION_FEED","NONCE_REPLAY_LEDGER_AND_TRUSTED_CLOCK",
    "EXTERNAL_AUDIT_AND_INCLUSION_PROOF",
    "INDEPENDENT_REVIEWER_ROLE_AND_SEPARATION_OF_DUTIES",
    "SEPARATE_AUTHORIZED_HUMAN_RELEASE_DECISION"];
  const roles=["INDEPENDENT_SECURITY_REVIEWER","AUTHORIZED_TRUST_POLICY_OWNER",
    "INDEPENDENT_RELEASE_ATTESTOR"];
  const checkpoints=["SOURCE_HASHES_REBUILT_AND_ATTESTED",
    "EXTERNAL_EVIDENCE_INDEPENDENTLY_AUTHENTICATED",
    "REVIEWER_IDENTITY_SCOPE_AND_REVOCATION_VERIFIED",
    "SIGNED_POLICY_DIFF_INDEPENDENTLY_APPROVED",
    "SECURITY_AND_REGRESSION_EVIDENCE_REVIEWED",
    "EXTERNAL_AUDIT_AND_TRUSTED_TIME_VERIFIED",
    "SEPARATE_HUMAN_RELEASE_DECISION_CONFIRMED"];
  const fixed={
    schema:"palaco.pp.recovery-002-trust-change-review-dossier.v0",
    reference:"PP-RECOVERY-002",
    sourceBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    dossierProvenance:"UNSIGNED_LOCAL_REVIEW_REQUEST_NOT_SENT",
    handoffDelivery:"NOT_SENT",signedReceipt:"NOT_AVAILABLE",
    externalAudit:"NOT_VERIFIED",independentReview:"NOT_COMPLETED",
    decision:"DENY",issuerPromotion:"PROHIBITED",
    algorithmPromotion:"PROHIBITED",trustedIssuerCount:0,
    keyMaterial:"NOT_PRESENT",changeApplied:false,
    independentVerification:"NOT_VERIFIED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const shape=(x,keys)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let epoch=0;
  const clear=(msg="Geen Trust Change Review Dossier geladen. HOLD / DENY.")=>{
    epoch++;evidence.replaceChildren();gates.replaceChildren();status.textContent=msg;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal ongetekend beoordelingsverzoek lezen. HOLD / DENY.");
    const now=epoch,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(now!==epoch||dashboard.hidden)return;
      if(!shape(data,[...Object.keys(fixed),"changeControlSha256","trustPolicySha256",
        "changeScope","affectedRequirements","externalEvidenceRequirements",
        "requiredReviewers","reassessmentGates","decisionCheckpoints","allowedAlgorithms"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.changeControlSha256)||!sha(data.trustPolicySha256)||
        !Array.isArray(data.allowedAlgorithms)||data.allowedAlgorithms.length!==0||
        !shape(data.changeScope,["category","changeType","changeApplied","reviewStatus"])||
        !Object.hasOwn(categories,data.changeScope.category)||
        !changes.includes(data.changeScope.changeType)||
        data.changeScope.changeApplied!==false||
        data.changeScope.reviewStatus!=="NOT_STARTED"||
        !Array.isArray(data.affectedRequirements)||
        data.affectedRequirements.length!==categories[data.changeScope.category].length||
        !Array.isArray(data.externalEvidenceRequirements)||
        data.externalEvidenceRequirements.length!==9||
        !Array.isArray(data.requiredReviewers)||data.requiredReviewers.length!==3||
        !Array.isArray(data.reassessmentGates)||data.reassessmentGates.length!==9||
        !Array.isArray(data.decisionCheckpoints)||data.decisionCheckpoints.length!==7)throw Error();
      for(let i=0;i<data.affectedRequirements.length;i++){
        const x=data.affectedRequirements[i];
        if(!shape(x,["requirementId","reassessment","verified"])||
          x.requirementId!==categories[data.changeScope.category][i]||
          x.reassessment!=="REQUIRED"||x.verified!==false)throw Error();
      }
      const evidenceNodes=document.createDocumentFragment();
      for(let i=0;i<9;i++){
        const x=data.externalEvidenceRequirements[i];
        if(!shape(x,["order","evidenceId","requiredRole","evidenceReceived","independentVerification"])||
          x.order!==i+1||x.evidenceId!==evidenceList[i][0]||
          x.requiredRole!==evidenceList[i][1]||
          x.evidenceReceived!=="NOT_PROVIDED"||
          x.independentVerification!=="NOT_PERFORMED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [x.order,x.evidenceId,x.requiredRole,"NOT_PROVIDED"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }evidenceNodes.append(tr);
      }
      for(let i=0;i<3;i++){
        const x=data.requiredReviewers[i];
        if(!shape(x,["role","authentication","authority","decision"])||
          x.role!==roles[i]||x.authentication!=="NOT_ESTABLISHED"||
          x.authority!=="NOT_ESTABLISHED"||x.decision!=="NOT_COMPLETED")throw Error();
      }
      const checkpointNodes=document.createDocumentFragment();
      for(let i=0;i<9;i++){
        const x=data.reassessmentGates[i];
        if(!shape(x,["gate","status","verification"])||
          x.gate!==reassessment[i]||x.status!=="BLOCKED"||
          x.verification!=="NOT_PERFORMED")throw Error();
      }
      for(let i=0;i<7;i++){
        const x=data.decisionCheckpoints[i];
        if(!shape(x,["order","checkpointId","status"])||
          x.order!==i+1||x.checkpointId!==checkpoints[i]||
          x.status!=="BLOCKED")throw Error();
        const li=document.createElement("li");
        li.textContent=x.checkpointId+" — BLOCKED";
        checkpointNodes.append(li);
      }
      if(now!==epoch||dashboard.hidden)return;
      evidence.replaceChildren(evidenceNodes);gates.replaceChildren(checkpointNodes);
      status.textContent="ONGESTUURD REVIEWDOSSIER / "+data.changeScope.category+
        ", 9 externe bewijzen NOT_PROVIDED, 7 beslisvoorwaarden BLOCKED. HOLD / DENY.";
    }catch(_){
      if(now!==epoch||dashboard.hidden)return;
      clear("REVIEWDOSSIER GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
