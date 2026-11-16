"use strict";
// Strictly read-only static preview. Not an external transfer verifier.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-custody-transfer-file"),
    load=$("admin-custody-transfer-load"),
    status=$("admin-custody-transfer-status"),
    rows=$("admin-custody-transfer-rows"),
    fields=$("admin-custody-transfer-fields"),
    dashboard=$("admin-dashboard");
  if(![file,load,status,rows,fields,dashboard].every(Boolean))return;
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
  const envelope=[
    "CANONICAL_TRANSFER_PROTOCOL_VERSION",
    "EXACT_CUSTODY_CONTRACT_AND_COLLECTION_HASHES",
    "EVIDENCE_ROW_ID_AND_ORIGINAL_BYTES_SHA256",
    "SENDING_CUSTODIAN_TRUSTED_SUBJECT_AND_SCOPE",
    "RECEIVING_CUSTODIAN_TRUSTED_SUBJECT_AND_SCOPE",
    "ISSUER_KEY_ID_AND_APPROVED_SIGNATURE_ALGORITHM",
    "AUDIENCE_PURPOSE_AND_SINGLE_USE_NONCE",
    "TRUSTED_ISSUED_AT_AND_EXPIRES_AT",
    "SIGNER_REVOCATION_AND_KEY_EPOCH_PROOF",
    "ENCRYPTED_TRANSFER_CHANNEL_AND_KEY_CUSTODY_ATTESTATION",
    "DETACHED_SIGNATURE_OVER_CANONICAL_ENVELOPE",
    "INDEPENDENT_APPEND_ONLY_LOG_INCLUSION_PROOF",
    "RECIPIENT_SIGNED_ACK_BOUND_TO_EXACT_ENVELOPE",
    "SEPARATE_AUTHORIZED_HUMAN_ACCEPTANCE_DECISION"
  ];
  const stages=[
    ["PREPARE_TRANSFER_INTENT","NO_EVIDENCE_BYTES_IN_LOCAL_MODULE"],
    ["VERIFY_SENDER_AND_EVIDENCE","INDEPENDENT_EXTERNAL_SOURCE_VERIFIER"],
    ["VERIFY_RECEIVER_AND_CHANNEL","INDEPENDENT_RECIPIENT_AUTHENTICATION"],
    ["VERIFY_SIGNED_TRANSFER_AND_REPLAY","TRUSTED_SIGNATURE_AND_NONCE_LEDGER"],
    ["VERIFY_EXTERNAL_AUDIT_RECEIPT","IMMUTABLE_INDEPENDENT_AUDIT_SERVICE"],
    ["REQUIRE_SEPARATE_ACCEPTANCE","AUTHORIZED_HUMAN_REVIEW_REQUIRED"]
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
  const failures=[
    "CUSTODIAN_IDENTITY_UNVERIFIED","SOURCE_OR_PAYLOAD_HASH_MISMATCH",
    "ENCRYPTION_OR_KEY_CUSTODY_NOT_VERIFIED",
    "ACCESS_SCOPE_OR_SEPARATION_OF_DUTIES_FAILED",
    "CHAIN_OF_CUSTODY_GAP","SIGNED_TRANSFER_RECEIPT_MISSING",
    "REPLAY_REVOCATION_OR_TRUSTED_TIME_FAILURE",
    "UNAPPROVED_RETENTION_OR_DISPOSAL",
    "MISSING_OR_MALFORMED_TRANSFER_ENVELOPE",
    "SENDER_RECEIVER_AUDIENCE_OR_SCOPE_MISMATCH",
    "MISSING_OR_INVALID_RECIPIENT_ACKNOWLEDGEMENT",
    "NONCE_REPLAY_OR_ATOMIC_LEDGER_UNAVAILABLE",
    "UNTRUSTED_ISSUER_KEY_OR_SIGNATURE_ALGORITHM",
    "ABSENT_SEPARATE_EVIDENCE_ACCEPTANCE_DECISION"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-custody-transfer-verification-protocol.v0",
    reference:"PP-RECOVERY-002",
    binding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    protocolScope:"UNSIGNED_FUTURE_EXTERNAL_TRANSFER_REQUIREMENTS_ONLY",
    requiredTransferCount:8,transfersInitiated:0,
    transfersAuthenticated:0,evidenceAccepted:0,
    senderTrust:"NOT_ESTABLISHED",recipientTrust:"NOT_ESTABLISHED",
    canonicalEnvelopeVerifier:"NOT_IMPLEMENTED",
    signatureVerifier:"NOT_CONFIGURED",trustedNonceLedger:"NOT_CONFIGURED",
    auditVerifier:"NOT_CONFIGURED",humanAcceptance:"NOT_COMPLETED",
    evidenceTransfer:"NOT_INITIATED",evidenceStorage:"NONE",
    trustedIssuerCount:0,independentVerification:"NOT_VERIFIED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(x,keys)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let epoch=0;
  const clear=(message="Geen Custody Transfer Verification Protocol geladen. HOLD / DENY.")=>{
    epoch++;rows.replaceChildren();fields.replaceChildren();status.textContent=message;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend overdrachtsprotocol lokaal lezen. HOLD / DENY.");
    const version=epoch,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const d=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(version!==epoch||dashboard.hidden)return;
      if(!exact(d,[...Object.keys(fixed),"custodyContractSha256",
          "collectionPlanSha256","auditContractSha256","transferRecords",
          "requiredEnvelopeFields","verificationStages",
          "externalTransferCheckpoints","failurePolicy","allowedAlgorithms"])||
          Object.entries(fixed).some(([k,v])=>d[k]!==v)||
          !["custodyContractSha256","collectionPlanSha256","auditContractSha256"].every(k=>sha(d[k]))||
          !Array.isArray(d.allowedAlgorithms)||d.allowedAlgorithms.length!==0||
          !Array.isArray(d.transferRecords)||d.transferRecords.length!==8||
          !Array.isArray(d.requiredEnvelopeFields)||d.requiredEnvelopeFields.length!==14||
          !Array.isArray(d.verificationStages)||d.verificationStages.length!==6||
          !Array.isArray(d.externalTransferCheckpoints)||d.externalTransferCheckpoints.length!==8||
          !Array.isArray(d.failurePolicy)||d.failurePolicy.length!==14)throw Error();
      const newRows=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=d.transferRecords[i],e=evidence[i];
        if(!exact(x,["rowId","evidenceId","requiredIndependentCustodianRole",
          "originalEvidenceDigest","senderAuthentication","recipientAuthentication",
          "signedEnvelope","recipientSignedAcknowledgement",
          "nonceAndClockVerification","keyRevocationVerification",
          "externalAuditReceipt","independentEvidenceAcceptance","transfer","gate","decision"])||
          x.rowId!=="AUD-E"+String(i+1).padStart(2,"0")||
          x.evidenceId!==e[0]||x.requiredIndependentCustodianRole!==e[1]||
          x.originalEvidenceDigest!=="NOT_AVAILABLE"||
          x.senderAuthentication!=="NOT_ESTABLISHED"||
          x.recipientAuthentication!=="NOT_ESTABLISHED"||
          x.signedEnvelope!=="NOT_PRESENT"||
          x.recipientSignedAcknowledgement!=="NOT_AVAILABLE"||
          x.nonceAndClockVerification!=="NOT_PERFORMED"||
          x.keyRevocationVerification!=="NOT_PERFORMED"||
          x.externalAuditReceipt!=="NOT_AVAILABLE"||
          x.independentEvidenceAcceptance!=="NOT_PERFORMED"||
          x.transfer!=="NOT_INITIATED"||x.gate!=="BLOCKED"||
          x.decision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const value of [x.rowId,x.evidenceId,x.requiredIndependentCustodianRole,
            "NOT_PRESENT","NOT_INITIATED","DENY"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }newRows.append(tr);
      }
      const newFields=document.createDocumentFragment();
      for(let i=0;i<14;i++){
        const x=d.requiredEnvelopeFields[i];
        if(!exact(x,["order","fieldId","status"])||x.order!==i+1||
          x.fieldId!==envelope[i]||x.status!=="MISSING")throw Error();
        const li=document.createElement("li");li.textContent=x.fieldId+" — MISSING";
        newFields.append(li);
      }
      for(let i=0;i<6;i++){
        const x=d.verificationStages[i];
        if(!exact(x,["order","stageId","requirement","status","gate"])||
          x.order!==i+1||x.stageId!==stages[i][0]||x.requirement!==stages[i][1]||
          x.status!=="NOT_PERFORMED"||x.gate!=="BLOCKED")throw Error();
      }
      for(let i=0;i<8;i++){
        const x=d.externalTransferCheckpoints[i];
        if(!exact(x,["order","checkpointId","status","gate"])||
          x.order!==i+1||x.checkpointId!==checkpoints[i]||
          x.status!=="NOT_PERFORMED"||x.gate!=="BLOCKED")throw Error();
      }
      for(let i=0;i<14;i++){
        const x=d.failurePolicy[i];
        if(!exact(x,["reason","decision","authorityEffect"])||
          x.reason!==failures[i]||x.decision!=="DENY"||
          x.authorityEffect!=="NONE")throw Error();
      }
      if(version!==epoch||dashboard.hidden)return;
      rows.replaceChildren(newRows);fields.replaceChildren(newFields);
      status.textContent="OVERDRACHTSPROTOCOL HERKEND / 0 van 8 gestart, 14 verplichte velden MISSING. HOLD / DENY.";
    }catch(_){
      if(version!==epoch||dashboard.hidden)return;
      clear("OVERDRACHTSPROTOCOL GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
