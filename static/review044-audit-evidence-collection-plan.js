"use strict";
// View-only unsigned evidence collection requirements; never transmits or accepts.
(() => {
  const $ = id => document.getElementById(id);
  const file=$("admin-audit-collection-file"),load=$("admin-audit-collection-load"),
    status=$("admin-audit-collection-status"),rows=$("admin-audit-collection-rows"),
    rules=$("admin-audit-collection-rules"),dashboard=$("admin-dashboard");
  if(![file,load,status,rows,rules,dashboard].every(Boolean))return;
  const evidence=[
    ["EXACT_DECISION_PROTOCOL_AND_CHANGE_HASHES","INDEPENDENT_AUDIT_VERIFIER","ORIGINAL_POLICY_AND_DECISION_BYTE_ATTESTATION","REBUILD_ORIGINAL_POLICY_AND_CHANGE_CONTROL_BYTES","REQUEST_SIGNED_SOURCE_BYTE_ATTESTATION_FROM_EXTERNAL_CUSTODIAN"],
    ["SIGNED_EXTERNAL_EVIDENCE_RECEIPT","INDEPENDENT_EVIDENCE_CUSTODIAN","INDEPENDENT_SIGNED_RECEIPT_AND_ISSUER_AUTHENTICATION","AUTHENTICATE_INDEPENDENT_ISSUER_AND_SIGNER_TRUST_CHAIN","REQUEST_ORIGINAL_SIGNED_RECEIPT_AND_TRUST_ANCHOR"],
    ["REVIEWER_IDENTITY_ROLE_AND_REVOCATION_ATTESTATION","INDEPENDENT_IDENTITY_AUDITOR","EXTERNAL_REVIEWER_IDENTITY_SCOPE_REVOCATION_CHECK","RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION","REQUEST_INDEPENDENT_REVIEWER_IDENTITY_SCOPE_AND_REVOCATION"],
    ["CANONICAL_SIGNED_HUMAN_DECISION","AUTHORIZED_HUMAN_DECISION_AUDITOR","SEPARATE_SIGNED_HUMAN_AUTHORITY_DECISION","RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION","REQUEST_SEPARATE_CANONICAL_SIGNED_HUMAN_DECISION"],
    ["TRUSTED_TIME_AND_NONCE_REPLAY_LEDGER_PROOF","INDEPENDENT_REPLAY_AUDITOR","TRUSTED_NONCE_LEDGER_AND_SIGNED_TIME_ANCHOR","VERIFY_REPLAY_NONCE_AND_TRUSTED_CLOCK_WINDOW","REQUEST_NONCE_CONSUMPTION_PROOF_AND_TRUSTED_TIMESTAMP"],
    ["IMMUTABLE_LOG_INCLUSION_AND_CONSISTENCY_PROOF","INDEPENDENT_AUDIT_VERIFIER","SIGNED_LOG_INCLUSION_AND_CONSISTENCY_WITNESSES","VERIFY_APPEND_ONLY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY","REQUEST_INDEPENDENT_LOG_INCLUSION_AND_CONSISTENCY_PROOFS"],
    ["KEY_EPOCH_ROTATION_AND_REVOCATION_PROOF","INDEPENDENT_CRYPTO_AUDITOR","PINNED_KEY_EPOCH_AND_SIGNED_REVOCATION_HISTORY","VERIFY_KEY_REVOCATION_AND_SIGNED_ROTATION_HISTORY","REQUEST_SIGNED_KEY_EPOCH_AND_REVOCATION_HISTORY"],
    ["SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_RECORD","INDEPENDENT_RELEASE_ATTESTOR","INDEPENDENT_RELEASE_OPERATOR_ROLLBACK_ATTESTATION","VERIFY_INDEPENDENT_DEPLOYMENT_AND_ROLLBACK_APPROVAL","REQUEST_SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_EVIDENCE"]
  ];
  const custody=[
    "ORIGINAL_BYTES_REMAIN_WITH_AUTHORIZED_EXTERNAL_CUSTODIAN",
    "NO_PRIVATE_KEYS_OR_SECRET_BYTES_IN_LOCAL_SNAPSHOT",
    "EXACT_SOURCE_AND_AUDIT_CONTRACT_HASH_BINDING_REQUIRED",
    "INDEPENDENT_TRUSTED_SIGNATURE_AND_PROVENANCE_CHECK_REQUIRED",
    "AUTHORIZED_REVIEWER_ROLE_AND_REVOCATION_CHECK_REQUIRED",
    "FRESH_NONCE_TRUSTED_TIME_AND_REPLAY_CHECK_REQUIRED",
    "EXTERNAL_SIGNED_AUDIT_INCLUSION_CHECK_REQUIRED",
    "SEPARATE_HUMAN_AND_DEPLOYMENT_DECISIONS_REQUIRED"
  ];
  const sequence=[
    "REQUEST_ORIGINAL_EXTERNAL_EVIDENCE_FROM_INDEPENDENT_CUSTODIAN",
    "AUTHENTICATE_EXTERIOR_SIGNER_AND_ROLE_IN_TRUSTED_SYSTEM",
    "VERIFY_SIGNED_BYTES_AND_EXACT_DECISION_PROTOCOL_BINDING",
    "VERIFY_REPLAY_REVOCATION_AND_TRUSTED_TIMESTAMP",
    "VERIFY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY",
    "RECORD_INDEPENDENT_REVIEW_OUTSIDE_THIS_LOCAL_MODULE",
    "REQUIRE_SEPARATE_HUMAN_AND_DEPLOYMENT_AUTHORIZATION"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-audit-evidence-collection-plan.v0",
    reference:"PP-RECOVERY-002",
    sourceBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    collectionProvenance:"UNSIGNED_LOCAL_REQUEST_PLAN_ONLY",
    requiredCollectionCount:8,evidenceCollectedCount:0,
    externallyVerifiedEvidenceCount:0,blockedCollectionCount:8,
    evidenceCollection:"NOT_EXECUTED",externalRequestDelivery:"NOT_SENT",
    evidenceAcceptance:"PROHIBITED",trustedAuditService:"NOT_CONFIGURED",
    reviewerAuthority:"NOT_ESTABLISHED",
    independentVerification:"NOT_VERIFIED",humanDecision:"NOT_COMPLETED",
    deploymentDecision:"NOT_AUTHORIZED",changeApplied:false,
    trustedIssuerCount:0,keyMaterial:"NOT_PRESENT",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const shape=(o,keys)=>o!==null&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let epoch=0;
  function clear(message="Geen Audit Evidence Collection Plan geladen. HOLD / DENY."){
    epoch++;rows.replaceChildren();rules.replaceChildren();status.textContent=message;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend verzamelplan lokaal lezen. HOLD / DENY.");
    const current=epoch,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try {
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(current!==epoch||dashboard.hidden)return;
      if(!shape(data,[...Object.keys(fixed),"readinessMatrixSha256",
        "auditContractSha256","collectionRows","custodyRules",
        "externalReviewSequence","allowedAlgorithms"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.readinessMatrixSha256)||!sha(data.auditContractSha256)||
        !Array.isArray(data.allowedAlgorithms)||data.allowedAlgorithms.length!==0||
        !Array.isArray(data.collectionRows)||data.collectionRows.length!==8||
        !Array.isArray(data.custodyRules)||data.custodyRules.length!==8||
        !Array.isArray(data.externalReviewSequence)||data.externalReviewSequence.length!==7)throw Error();
      const rowNodes=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=data.collectionRows[i],want=evidence[i];
        if(!shape(x,["rowId","evidenceId","independentCustodianRole",
          "requiredMissingProof","externalVerificationStep","collectionRequest",
          "evidenceBytes","externalEvidenceReceipt","reviewerAuthentication",
          "evidenceProvenance","requestState","nextPermittedAction","gate","decision"])||
          x.rowId!=="AUD-E"+String(i+1).padStart(2,"0")||
          x.evidenceId!==want[0]||x.independentCustodianRole!==want[1]||
          x.requiredMissingProof!==want[2]||x.externalVerificationStep!==want[3]||
          x.collectionRequest!==want[4]||
          x.evidenceBytes!=="NOT_COLLECTED"||
          x.externalEvidenceReceipt!=="NOT_AVAILABLE"||
          x.reviewerAuthentication!=="NOT_ESTABLISHED"||
          x.evidenceProvenance!=="NOT_VERIFIED"||
          x.requestState!=="NOT_SENT"||
          x.nextPermittedAction!=="PREPARE_EXTERNAL_REQUEST_ONLY"||
          x.gate!=="BLOCKED"||x.decision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const v of [x.rowId,x.evidenceId,x.independentCustodianRole,
          x.collectionRequest,"NOT_SENT / DENY"]){
          const td=document.createElement("td");td.textContent=v;tr.append(td);
        }rowNodes.append(tr);
      }
      const ruleNodes=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=data.custodyRules[i];
        if(!shape(x,["order","ruleId","status"])||x.order!==i+1||
          x.ruleId!==custody[i]||x.status!=="NOT_ESTABLISHED")throw Error();
        const li=document.createElement("li");li.textContent=x.ruleId+" — NOT_ESTABLISHED";
        ruleNodes.append(li);
      }
      for(let i=0;i<7;i++){
        const x=data.externalReviewSequence[i];
        if(!shape(x,["order","stepId","status"])||x.order!==i+1||
          x.stepId!==sequence[i]||x.status!=="NOT_STARTED")throw Error();
      }
      if(current!==epoch||dashboard.hidden)return;
      rows.replaceChildren(rowNodes);rules.replaceChildren(ruleNodes);
      status.textContent="VERZAMELPLAN HERKEND / 0 van 8 verzameld, niets verzonden. HOLD / DENY.";
    }catch(_){
      if(current!==epoch||dashboard.hidden)return;
      clear("VERZAMELPLAN GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
