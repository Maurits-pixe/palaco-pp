"use strict";
// View-only unsigned custody contract; no collection, authentication or transfer.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-audit-custody-file"),load=$("admin-audit-custody-load"),
    status=$("admin-audit-custody-status"),rows=$("admin-audit-custody-rows"),
    controls=$("admin-audit-custody-controls"),dashboard=$("admin-dashboard");
  if(![file,load,status,rows,controls,dashboard].every(Boolean))return;
  const records=[
    ["EXACT_DECISION_PROTOCOL_AND_CHANGE_HASHES","INDEPENDENT_AUDIT_VERIFIER","REQUEST_SIGNED_SOURCE_BYTE_ATTESTATION_FROM_EXTERNAL_CUSTODIAN"],
    ["SIGNED_EXTERNAL_EVIDENCE_RECEIPT","INDEPENDENT_EVIDENCE_CUSTODIAN","REQUEST_ORIGINAL_SIGNED_RECEIPT_AND_TRUST_ANCHOR"],
    ["REVIEWER_IDENTITY_ROLE_AND_REVOCATION_ATTESTATION","INDEPENDENT_IDENTITY_AUDITOR","REQUEST_INDEPENDENT_REVIEWER_IDENTITY_SCOPE_AND_REVOCATION"],
    ["CANONICAL_SIGNED_HUMAN_DECISION","AUTHORIZED_HUMAN_DECISION_AUDITOR","REQUEST_SEPARATE_CANONICAL_SIGNED_HUMAN_DECISION"],
    ["TRUSTED_TIME_AND_NONCE_REPLAY_LEDGER_PROOF","INDEPENDENT_REPLAY_AUDITOR","REQUEST_NONCE_CONSUMPTION_PROOF_AND_TRUSTED_TIMESTAMP"],
    ["IMMUTABLE_LOG_INCLUSION_AND_CONSISTENCY_PROOF","INDEPENDENT_AUDIT_VERIFIER","REQUEST_INDEPENDENT_LOG_INCLUSION_AND_CONSISTENCY_PROOFS"],
    ["KEY_EPOCH_ROTATION_AND_REVOCATION_PROOF","INDEPENDENT_CRYPTO_AUDITOR","REQUEST_SIGNED_KEY_EPOCH_AND_REVOCATION_HISTORY"],
    ["SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_RECORD","INDEPENDENT_RELEASE_ATTESTOR","REQUEST_SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_EVIDENCE"]
  ];
  const security=[
    "INDEPENDENT_CUSTODIAN_IDENTITY_AND_SCOPE_ATTESTATION",
    "ORIGINAL_BYTE_INTEGRITY_AND_SIGNED_HASH_BINDING",
    "ENCRYPTED_IN_TRANSIT_AND_AT_REST_WITH_APPROVED_KEY_CUSTODY",
    "LEAST_PRIVILEGE_ACCESS_AND_SEPARATION_OF_DUTIES",
    "IMMUTABLE_CHAIN_OF_CUSTODY_AND_INDEPENDENT_AUDIT_LOG",
    "SIGNED_TRANSFER_RECEIPT_AND_AUDIENCE_NONCE_BINDING",
    "DOCUMENTED_RETENTION_AND_AUTHORIZED_DISPOSAL",
    "REVOCATION_KEY_COMPROMISE_AND_EMERGENCY_DENY"
  ];
  const checkpoints=[
    "AUTHENTICATE_SENDING_CUSTODIAN_IN_EXTERNAL_TRUST_SYSTEM",
    "VERIFY_ORIGINAL_EVIDENCE_BYTES_AND_SOURCE_PROVENANCE",
    "VALIDATE_EXACT_COLLECTION_PLAN_AND_AUDIT_HASHES",
    "VERIFY_RECEIVER_IDENTITY_ROLE_SCOPE_AND_KEY_REVOCATION",
    "USE_SIGNED_CANONICAL_TRANSFER_ENVELOPE",
    "VERIFY_FRESH_NONCE_TRUSTED_TIME_AND_REPLAY_LEDGER",
    "ANCHOR_SIGNED_RECEIPT_IN_EXTERNAL_APPEND_ONLY_LOG",
    "REQUIRE_SEPARATE_AUTHORIZED_REVIEW_BEFORE_ANY_ACCEPTANCE"
  ];
  const reasons=[
    "CUSTODIAN_IDENTITY_UNVERIFIED","SOURCE_OR_PAYLOAD_HASH_MISMATCH",
    "ENCRYPTION_OR_KEY_CUSTODY_NOT_VERIFIED",
    "ACCESS_SCOPE_OR_SEPARATION_OF_DUTIES_FAILED",
    "CHAIN_OF_CUSTODY_GAP","SIGNED_TRANSFER_RECEIPT_MISSING",
    "REPLAY_REVOCATION_OR_TRUSTED_TIME_FAILURE",
    "UNAPPROVED_RETENTION_OR_DISPOSAL"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-audit-evidence-custody-contract.v0",
    reference:"PP-RECOVERY-002",
    binding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    provenance:"UNSIGNED_LOCAL_CUSTODY_REQUIREMENTS_NOT_EVIDENCE",
    requiredCustodyCount:8,externallyHeldEvidenceCount:0,
    locallyReceivedEvidenceCount:0,transferredEvidenceCount:0,
    verifiedEvidenceCount:0,evidenceCustody:"NOT_ESTABLISHED",
    evidenceTransfer:"NOT_INITIATED",evidenceAcceptance:"PROHIBITED",
    originalEvidenceStorage:"NONE",credentialOrKeyStorage:"NONE",
    externalCustodian:"NOT_AUTHENTICATED",recipientAuthority:"NOT_ESTABLISHED",
    trustedAuditService:"NOT_CONFIGURED",
    independentVerification:"NOT_VERIFIED",humanDecision:"NOT_COMPLETED",
    deploymentDecision:"NOT_AUTHORIZED",changeApplied:false,
    trustedIssuerCount:0,releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(o,keys)=>o!==null&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let generation=0;
  const clear=(m="Geen Audit Evidence Custody Contract geladen. HOLD / DENY.")=>{
    generation++;rows.replaceChildren();controls.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend bewaarkontrakt lokaal lezen. HOLD / DENY.");
    const stamp=generation,selected=file.files?.[0];
    if(dashboard.hidden||!selected||selected.size<1||selected.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await selected.arrayBuffer()));
      if(stamp!==generation||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"collectionPlanSha256",
        "readinessMatrixSha256","auditContractSha256",
        "custodyRecords","securityControls","transferCheckpoints",
        "denialConditions","allowedAlgorithms"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !["collectionPlanSha256","readinessMatrixSha256",
          "auditContractSha256"].every(k=>sha(data[k]))||
        !Array.isArray(data.allowedAlgorithms)||data.allowedAlgorithms.length!==0||
        !Array.isArray(data.custodyRecords)||data.custodyRecords.length!==8||
        !Array.isArray(data.securityControls)||data.securityControls.length!==8||
        !Array.isArray(data.transferCheckpoints)||data.transferCheckpoints.length!==8||
        !Array.isArray(data.denialConditions)||data.denialConditions.length!==8)throw Error();
      const rowNodes=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=data.custodyRecords[i],item=records[i];
        if(!exact(x,["rowId","evidenceId","requiredIndependentCustodianRole",
          "requestedExternalSource","originalBytesLocation","custodianAuthentication",
          "originalByteHash","integrityVerification","accessGrant","custodyChain",
          "signedTransferReceipt","retentionApproval","transferStatus",
          "evidencePossession","gate","decision"])||
          x.rowId!=="AUD-E"+String(i+1).padStart(2,"0")||
          x.evidenceId!==item[0]||x.requiredIndependentCustodianRole!==item[1]||
          x.requestedExternalSource!==item[2]||
          x.originalBytesLocation!=="EXTERNAL_CUSTODIAN_ONLY_NOT_ACCESSED"||
          x.custodianAuthentication!=="NOT_ESTABLISHED"||
          x.originalByteHash!=="NOT_AVAILABLE"||
          x.integrityVerification!=="NOT_PERFORMED"||
          x.accessGrant!=="NONE"||x.custodyChain!=="NOT_ESTABLISHED"||
          x.signedTransferReceipt!=="NOT_AVAILABLE"||
          x.retentionApproval!=="NOT_ESTABLISHED"||
          x.transferStatus!=="NOT_INITIATED"||
          x.evidencePossession!=="NONE"||x.gate!=="BLOCKED"||
          x.decision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const value of [x.rowId,x.evidenceId,x.requiredIndependentCustodianRole,
          "NOT_ESTABLISHED","NOT_INITIATED","DENY"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }rowNodes.append(tr);
      }
      const controlNodes=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=data.securityControls[i];
        if(!exact(x,["order","controlId","status","verification"])||
          x.order!==i+1||x.controlId!==security[i]||
          x.status!=="NOT_ESTABLISHED"||x.verification!=="NOT_PERFORMED")throw Error();
        const li=document.createElement("li");li.textContent=x.controlId+" — NOT_ESTABLISHED";
        controlNodes.append(li);
      }
      for(let i=0;i<8;i++){
        const x=data.transferCheckpoints[i];
        if(!exact(x,["order","checkpointId","status","gate"])||
          x.order!==i+1||x.checkpointId!==checkpoints[i]||
          x.status!=="NOT_STARTED"||x.gate!=="BLOCKED")throw Error();
        const x2=data.denialConditions[i];
        if(!exact(x2,["reason","decision","authorityEffect"])||
          x2.reason!==reasons[i]||x2.decision!=="DENY"||
          x2.authorityEffect!=="NONE")throw Error();
      }
      if(stamp!==generation||dashboard.hidden)return;
      rows.replaceChildren(rowNodes);controls.replaceChildren(controlNodes);
      status.textContent="BEWAARCONTRACT HERKEND / 0/8 ontvangen, 0/8 overgedragen, geen bewaarrechten. HOLD / DENY.";
    }catch(_){
      if(stamp!==generation||dashboard.hidden)return;
      clear("BEWAARCONTRACT GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
