"use strict";
// Only displays an unsigned, DENY-only decision protocol. No review actions.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-trust-decision-file"),load=$("admin-trust-decision-load"),
    status=$("admin-trust-decision-status"),stages=$("admin-trust-decision-stages"),
    guards=$("admin-trust-decision-guards"),dashboard=$("admin-dashboard");
  if(![file,load,status,stages,guards,dashboard].every(Boolean))return;
  const phase=[
    ["LOCAL_CLAIM_INTAKE","UNAUTHENTICATED_REQUEST_ONLY"],
    ["EXTERNAL_EVIDENCE_VERIFICATION","INDEPENDENT_TRUSTED_VERIFIER_REQUIRED"],
    ["AUTHORIZED_HUMAN_DECISION","SEPARATE_AUTHORITY_AND_SIGNED_DECISION_REQUIRED"]
  ];
  const borders=[
    ["LOCAL_CLAIM_INTAKE","EXTERNAL_EVIDENCE_VERIFICATION","LOCAL_CLAIM_CANNOT_ATTEST_EVIDENCE"],
    ["EXTERNAL_EVIDENCE_VERIFICATION","AUTHORIZED_HUMAN_DECISION","TECHNICAL_VERIFICATION_CANNOT_APPROVE_POLICY"],
    ["AUTHORIZED_HUMAN_DECISION","TRUST_POLICY_ACTIVATION","HUMAN_DECISION_ALONE_CANNOT_DEPLOY"]
  ];
  const proof=[
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
  const reviewers=["INDEPENDENT_SECURITY_REVIEWER","AUTHORIZED_TRUST_POLICY_OWNER",
    "INDEPENDENT_RELEASE_ATTESTOR"];
  const checkpoints=["SOURCE_HASHES_REBUILT_AND_ATTESTED",
    "EXTERNAL_EVIDENCE_INDEPENDENTLY_AUTHENTICATED",
    "REVIEWER_IDENTITY_SCOPE_AND_REVOCATION_VERIFIED",
    "SIGNED_POLICY_DIFF_INDEPENDENTLY_APPROVED",
    "SECURITY_AND_REGRESSION_EVIDENCE_REVIEWED",
    "EXTERNAL_AUDIT_AND_TRUSTED_TIME_VERIFIED",
    "SEPARATE_HUMAN_RELEASE_DECISION_CONFIRMED"];
  const controls=["EXACT_REVIEW_DOSSIER_AND_POLICY_HASH_BINDING",
    "INDEPENDENT_TRUST_ANCHOR_AND_RECEIPT_SIGNATURE",
    "ORIGINAL_EVIDENCE_PROVENANCE_AND_REVOCATION",
    "REVIEWER_AUTHENTICATION_ROLE_SCOPE_AND_INDEPENDENCE",
    "SIGNED_CANONICAL_POLICY_DIFF_AND_REPLAY_PROTECTION",
    "EXTERNAL_AUDIT_ANCHOR_AND_TRUSTED_TIME",
    "SEPARATE_AUTHORIZED_HUMAN_DECISION",
    "INDEPENDENT_DEPLOYMENT_APPROVAL_AND_ROLLBACK"];
  const fixed={
    schema:"palaco.pp.recovery-002-trust-change-decision-protocol.v0",
    reference:"PP-RECOVERY-002",
    sourceBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    decisionPolicy:"DENY_ALL_UNTIL_SEPARATE_VERIFIED_AUTHORITIES",
    localClaimAuthority:"NONE",externalVerificationService:"NOT_CONFIGURED",
    humanDecisionService:"NOT_CONFIGURED",signedDecision:"NOT_AVAILABLE",
    decisionReceipt:"NOT_AVAILABLE",reviewDossierDelivery:"NOT_SENT",
    policyChangeExecution:"PROHIBITED",issuerPromotion:"PROHIBITED",
    algorithmPromotion:"PROHIBITED",trustedIssuerCount:0,
    keyMaterial:"NOT_PRESENT",changeApplied:false,
    independentVerification:"NOT_VERIFIED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const shape=(o,keys)=>o!==null&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let revision=0;
  const clear=(m="Geen Trust Change Decision Protocol geladen. HOLD / DENY.")=>{
    revision++;stages.replaceChildren();guards.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend beslisprotocol lokaal lezen. HOLD / DENY.");
    const epoch=revision,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(epoch!==revision||dashboard.hidden)return;
      if(!shape(data,[...Object.keys(fixed),"reviewDossierSha256",
        "changeControlSha256","trustPolicySha256","decisionStages",
        "trustBoundaryRules","evidenceChecks","reviewerGates",
        "decisionCheckpoints","nonBypassableControls","allowedAlgorithms"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.reviewDossierSha256)||!sha(data.changeControlSha256)||
        !sha(data.trustPolicySha256)||!Array.isArray(data.allowedAlgorithms)||
        data.allowedAlgorithms.length!==0)throw Error();
      const phaseNodes=document.createDocumentFragment();
      if(!Array.isArray(data.decisionStages)||data.decisionStages.length!==3)throw Error();
      for(let i=0;i<3;i++){
        const x=data.decisionStages[i];
        if(!shape(x,["order","stageId","requirement","status","verification","decision"])||
          x.order!==i+1||x.stageId!==phase[i][0]||x.requirement!==phase[i][1]||
          x.status!=="BLOCKED"||x.verification!=="NOT_PERFORMED"||
          x.decision!=="DENY")throw Error();
        const li=document.createElement("li");
        li.textContent=x.stageId+" — BLOCKED / DENY";phaseNodes.append(li);
      }
      if(!Array.isArray(data.trustBoundaryRules)||data.trustBoundaryRules.length!==3)throw Error();
      for(let i=0;i<3;i++){
        const x=data.trustBoundaryRules[i];
        if(!shape(x,["fromStage","toStage","ruleId","crossing","authorityEffect"])||
          x.fromStage!==borders[i][0]||x.toStage!==borders[i][1]||
          x.ruleId!==borders[i][2]||x.crossing!=="PROHIBITED"||
          x.authorityEffect!=="NONE")throw Error();
      }
      if(!Array.isArray(data.evidenceChecks)||data.evidenceChecks.length!==9)throw Error();
      for(let i=0;i<9;i++){
        const x=data.evidenceChecks[i];
        if(!shape(x,["evidenceId","requiredRole","externalAuthenticity",
          "independentAssessment","maySatisfyDecision"])||
          x.evidenceId!==proof[i][0]||x.requiredRole!==proof[i][1]||
          x.externalAuthenticity!=="NOT_VERIFIED"||
          x.independentAssessment!=="NOT_PERFORMED"||
          x.maySatisfyDecision!==false)throw Error();
      }
      if(!Array.isArray(data.reviewerGates)||data.reviewerGates.length!==3)throw Error();
      for(let i=0;i<3;i++){
        const x=data.reviewerGates[i];
        if(!shape(x,["role","authentication","authority","independence","decision"])||
          x.role!==reviewers[i]||x.authentication!=="NOT_ESTABLISHED"||
          x.authority!=="NOT_ESTABLISHED"||x.independence!=="NOT_VERIFIED"||
          x.decision!=="NOT_COMPLETED")throw Error();
      }
      if(!Array.isArray(data.decisionCheckpoints)||data.decisionCheckpoints.length!==7)throw Error();
      for(let i=0;i<7;i++){
        const x=data.decisionCheckpoints[i];
        if(!shape(x,["checkpointId","status","independentVerification"])||
          x.checkpointId!==checkpoints[i]||x.status!=="BLOCKED"||
          x.independentVerification!=="NOT_PERFORMED")throw Error();
      }
      const controlNodes=document.createDocumentFragment();
      if(!Array.isArray(data.nonBypassableControls)||data.nonBypassableControls.length!==8)throw Error();
      for(let i=0;i<8;i++){
        const x=data.nonBypassableControls[i];
        if(!shape(x,["controlId","status","approvalEffect"])||
          x.controlId!==controls[i]||x.status!=="NOT_SATISFIED"||
          x.approvalEffect!=="NONE")throw Error();
        const li=document.createElement("li");li.textContent=x.controlId+" — NOT_SATISFIED";
        controlNodes.append(li);
      }
      if(epoch!==revision||dashboard.hidden)return;
      stages.replaceChildren(phaseNodes);guards.replaceChildren(controlNodes);
      status.textContent="BESLISPROTOCOL HERKEND / 3 gescheiden fasen BLOCKED, 8 controles NOT_SATISFIED. Geen goedkeuring. HOLD / DENY.";
    }catch(_){
      if(epoch!==revision||dashboard.hidden)return;
      clear("BESLISPROTOCOL GEWEIGERD / Ongeldige structuur of statusclaim. HOLD / DENY.");
    }
  });
})();
