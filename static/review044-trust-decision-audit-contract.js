"use strict";
// Static read-only audit requirements, never actual receipt validation.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-trust-audit-file"),load=$("admin-trust-audit-load"),
    status=$("admin-trust-audit-status"),proof=$("admin-trust-audit-evidence"),
    steps=$("admin-trust-audit-steps"),dashboard=$("admin-dashboard");
  if(![file,load,status,proof,steps,dashboard].every(Boolean))return;
  const evidence=[
    ["EXACT_DECISION_PROTOCOL_AND_CHANGE_HASHES","INDEPENDENT_AUDIT_VERIFIER"],
    ["SIGNED_EXTERNAL_EVIDENCE_RECEIPT","INDEPENDENT_EVIDENCE_CUSTODIAN"],
    ["REVIEWER_IDENTITY_ROLE_AND_REVOCATION_ATTESTATION","INDEPENDENT_IDENTITY_AUDITOR"],
    ["CANONICAL_SIGNED_HUMAN_DECISION","AUTHORIZED_HUMAN_DECISION_AUDITOR"],
    ["TRUSTED_TIME_AND_NONCE_REPLAY_LEDGER_PROOF","INDEPENDENT_REPLAY_AUDITOR"],
    ["IMMUTABLE_LOG_INCLUSION_AND_CONSISTENCY_PROOF","INDEPENDENT_AUDIT_VERIFIER"],
    ["KEY_EPOCH_ROTATION_AND_REVOCATION_PROOF","INDEPENDENT_CRYPTO_AUDITOR"],
    ["SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_RECORD","INDEPENDENT_RELEASE_ATTESTOR"]
  ];
  const reconstruction=[
    "REBUILD_ORIGINAL_POLICY_AND_CHANGE_CONTROL_BYTES",
    "VERIFY_EXACT_DECISION_PROTOCOL_AND_EVIDENCE_SET_DIGESTS",
    "AUTHENTICATE_INDEPENDENT_ISSUER_AND_SIGNER_TRUST_CHAIN",
    "VERIFY_KEY_REVOCATION_AND_SIGNED_ROTATION_HISTORY",
    "VERIFY_REPLAY_NONCE_AND_TRUSTED_CLOCK_WINDOW",
    "VERIFY_APPEND_ONLY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY",
    "RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION",
    "VERIFY_INDEPENDENT_DEPLOYMENT_AND_ROLLBACK_APPROVAL"
  ];
  const boundary=[
    ["LOCAL_CLAIM_INTAKE","EXTERNAL_EVIDENCE_VERIFICATION","LOCAL_CLAIM_CANNOT_ATTEST_EVIDENCE"],
    ["EXTERNAL_EVIDENCE_VERIFICATION","AUTHORIZED_HUMAN_DECISION","TECHNICAL_VERIFICATION_CANNOT_APPROVE_POLICY"],
    ["AUTHORIZED_HUMAN_DECISION","TRUST_POLICY_ACTIVATION","HUMAN_DECISION_ALONE_CANNOT_DEPLOY"]
  ];
  const denials=[
    "MISSING_EXTERNAL_AUDIT_RECEIPT","UNTRUSTED_LOG_ISSUER_OR_SIGNER",
    "INVALID_DECISION_OR_RECEIPT_SIGNATURE","SOURCE_HASH_OR_SIGNED_PAYLOAD_MISMATCH",
    "NONCE_REPLAY_OR_UNTRUSTED_TIMESTAMP","REVOKED_KEY_OR_REVIEWER_AUTHORITY",
    "AUDIT_LOG_FORK_OR_INCLUSION_FAILURE",
    "MISSING_SEPARATE_HUMAN_OR_DEPLOYMENT_DECISION"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-trust-decision-audit-contract.v0",
    reference:"PP-RECOVERY-002",
    binding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    auditScope:"FUTURE_EXTERNAL_AUDIT_REQUIREMENTS_NOT_EVIDENCE",
    sourceAuthenticity:"NOT_ATTESTED",signedAuditReceipt:"NOT_AVAILABLE",
    externalAuditLog:"NOT_CONFIGURED",trustedClock:"NOT_CONFIGURED",
    auditVerification:"NOT_PERFORMED",independentReviewerAuthority:"NOT_ESTABLISHED",
    humanDecision:"NOT_COMPLETED",deploymentDecision:"NOT_AUTHORIZED",
    changeApplied:false,issuerPromotion:"PROHIBITED",algorithmPromotion:"PROHIBITED",
    trustedIssuerCount:0,keyMaterial:"NOT_PRESENT",
    independentVerification:"NOT_VERIFIED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(x,keys)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let revision=0;
  const clear=(message="Geen Trust Decision Audit Contract geladen. HOLD / DENY.")=>{
    revision++;proof.replaceChildren();steps.replaceChildren();status.textContent=message;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();}).observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend auditcontract lokaal lezen. HOLD / DENY.");
    const current=revision,selection=file.files?.[0];
    if(dashboard.hidden||!selection||selection.size<1||selection.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await selection.arrayBuffer()));
      if(current!==revision||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"decisionProtocolSha256","reviewDossierSha256",
        "changeControlSha256","trustPolicySha256","requiredExternalEvidence",
        "reconstructionSteps","decisionBoundaryAudit","failureRules","allowedAlgorithms"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !["decisionProtocolSha256","reviewDossierSha256",
          "changeControlSha256","trustPolicySha256"].every(k=>sha(data[k]))||
        !Array.isArray(data.allowedAlgorithms)||data.allowedAlgorithms.length!==0||
        !Array.isArray(data.requiredExternalEvidence)||data.requiredExternalEvidence.length!==8||
        !Array.isArray(data.reconstructionSteps)||data.reconstructionSteps.length!==8||
        !Array.isArray(data.decisionBoundaryAudit)||data.decisionBoundaryAudit.length!==3||
        !Array.isArray(data.failureRules)||data.failureRules.length!==8)throw Error();
      const evidenceNodes=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=data.requiredExternalEvidence[i];
        if(!exact(x,["order","evidenceId","requiredIndependentRole","evidenceStatus","signatureVerification"])||
          x.order!==i+1||x.evidenceId!==evidence[i][0]||
          x.requiredIndependentRole!==evidence[i][1]||
          x.evidenceStatus!=="NOT_PROVIDED"||x.signatureVerification!=="NOT_PERFORMED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [x.order,x.evidenceId,x.requiredIndependentRole,"NOT_PROVIDED"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }evidenceNodes.append(tr);
      }
      const reconstructionNodes=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=data.reconstructionSteps[i];
        if(!exact(x,["order","stepId","status","gate"])||
          x.order!==i+1||x.stepId!==reconstruction[i]||
          x.status!=="NOT_PERFORMED"||x.gate!=="BLOCKED")throw Error();
        const li=document.createElement("li");
        li.textContent=x.stepId+" — BLOCKED";reconstructionNodes.append(li);
      }
      for(let i=0;i<3;i++){
        const x=data.decisionBoundaryAudit[i];
        if(!exact(x,["fromStage","toStage","ruleId","externalProof","crossing"])||
          x.fromStage!==boundary[i][0]||x.toStage!==boundary[i][1]||
          x.ruleId!==boundary[i][2]||x.externalProof!=="NOT_AVAILABLE"||
          x.crossing!=="PROHIBITED")throw Error();
      }
      for(let i=0;i<8;i++){
        const x=data.failureRules[i];
        if(!exact(x,["reason","decision","authorityEffect"])||
          x.reason!==denials[i]||x.decision!=="DENY"||
          x.authorityEffect!=="NONE")throw Error();
      }
      if(current!==revision||dashboard.hidden)return;
      proof.replaceChildren(evidenceNodes);steps.replaceChildren(reconstructionNodes);
      status.textContent="AUDITCONTRACT HERKEND / 8 bewijzen NOT_PROVIDED, 8 reconstructiestappen BLOCKED. Geen externe audit. HOLD / DENY.";
    }catch(_){
      if(current!==revision||dashboard.hidden)return;
      clear("AUDITCONTRACT GEWEIGERD / Ongeldig schema of ongeoorloofde status. HOLD / DENY.");
    }
  });
})();
