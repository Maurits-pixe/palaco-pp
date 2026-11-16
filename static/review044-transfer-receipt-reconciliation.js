"use strict";
// Local unsigned reconciliation REQUIREMENTS viewer. Never verifies real receipts.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-receipt-reconcile-file"),load=$("admin-receipt-reconcile-load"),
    status=$("admin-receipt-reconcile-status"),rows=$("admin-receipt-reconcile-rows"),
    checks=$("admin-receipt-reconcile-checks"),dashboard=$("admin-dashboard");
  if(![file,load,status,rows,checks,dashboard].every(Boolean))return;
  const pairs=[
    ["EXACT_DECISION_PROTOCOL_AND_CHANGE_HASHES","INDEPENDENT_AUDIT_VERIFIER"],
    ["SIGNED_EXTERNAL_EVIDENCE_RECEIPT","INDEPENDENT_EVIDENCE_CUSTODIAN"],
    ["REVIEWER_IDENTITY_ROLE_AND_REVOCATION_ATTESTATION","INDEPENDENT_IDENTITY_AUDITOR"],
    ["CANONICAL_SIGNED_HUMAN_DECISION","AUTHORIZED_HUMAN_DECISION_AUDITOR"],
    ["TRUSTED_TIME_AND_NONCE_REPLAY_LEDGER_PROOF","INDEPENDENT_REPLAY_AUDITOR"],
    ["IMMUTABLE_LOG_INCLUSION_AND_CONSISTENCY_PROOF","INDEPENDENT_AUDIT_VERIFIER"],
    ["KEY_EPOCH_ROTATION_AND_REVOCATION_PROOF","INDEPENDENT_CRYPTO_AUDITOR"],
    ["SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_RECORD","INDEPENDENT_RELEASE_ATTESTOR"]
  ];
  const match=[
    "SENDER_RECEIPT_CANONICAL_BYTES_AND_SIGNATURE",
    "RECIPIENT_ACK_CANONICAL_BYTES_AND_SIGNATURE",
    "EXACT_TRANSFER_ENVELOPE_SHA256_MATCH",
    "EXACT_EVIDENCE_ID_AND_ORIGINAL_BYTE_HASH_MATCH",
    "SENDER_AND_RECIPIENT_IDENTITIES_AND_ROLE_SCOPE",
    "AUDIENCE_PURPOSE_FRESH_NONCE_AND_TRUSTED_TIME",
    "SIGNER_KEY_EPOCH_AND_REVOCATION_CHECK",
    "INDEPENDENT_AUDIT_INCLUSION_AND_CONSISTENCY",
    "EXPLICIT_NON_ACCEPTANCE_UNTIL_SEPARATE_HUMAN_DECISION"
  ];
  const gates=[
    "RECEIVE_ORIGINAL_SIGNED_SENDER_RECEIPT_OUTSIDE_LOCAL_MODULE",
    "RECEIVE_ORIGINAL_SIGNED_RECIPIENT_ACK_OUTSIDE_LOCAL_MODULE",
    "VERIFY_BOTH_SIGNATURES_WITH_TRUSTED_EXTERNAL_KEYS",
    "COMPARE_CANONICAL_ENVELOPE_AND_EVIDENCE_DIGESTS",
    "CHECK_BOTH_SUBJECTS_ROLE_SCOPES_AND_REVOCATIONS",
    "VERIFY_ATOMIC_NONCE_REPLAY_AND_TRUSTED_TIME",
    "VERIFY_IMMUTABLE_AUDIT_INCLUSION_PROOF",
    "REQUIRE_SEPARATE_HUMAN_EVIDENCE_ACCEPTANCE"
  ];
  const conflicts=[
    "SENDER_RECEIPT_ABSENT_OR_UNTRUSTED",
    "RECIPIENT_ACK_ABSENT_OR_UNTRUSTED",
    "ENVELOPE_OR_EVIDENCE_DIGEST_MISMATCH",
    "SENDER_RECIPIENT_IDENTITY_OR_SCOPE_MISMATCH",
    "AUDIENCE_PURPOSE_NONCE_OR_TIME_MISMATCH",
    "REVOKED_OR_UNTRUSTED_SIGNING_KEY",
    "UNVERIFIABLE_EXTERNAL_AUDIT_PROOF",
    "SEPARATE_HUMAN_ACCEPTANCE_ABSENT"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-transfer-receipt-reconciliation.v0",
    reference:"PP-RECOVERY-002",binding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    scope:"UNSIGNED_RECONCILIATION_REQUIREMENTS_NOT_RECEIPTS",
    requiredReceiptPairs:8,senderReceiptsReceived:0,
    recipientAcknowledgementsReceived:0,reconciledReceiptPairs:0,
    senderAuthority:"NOT_ESTABLISHED",recipientAuthority:"NOT_ESTABLISHED",
    signatureVerification:"NOT_CONFIGURED",trustedReplayLedger:"NOT_CONFIGURED",
    auditAnchoring:"NOT_CONFIGURED",independentReconciliation:"NOT_VERIFIED",
    humanAcceptance:"NOT_COMPLETED",evidenceTransfer:"NOT_INITIATED",
    evidenceAcceptance:"PROHIBITED",evidenceStorage:"NONE",
    trustedIssuerCount:0,releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(x,k)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===k.length&&k.every(v=>Object.hasOwn(x,v));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let generation=0;
  function clear(m="Geen Transfer Receipt Reconciliation Contract geladen. HOLD / DENY."){
    generation++;rows.replaceChildren();checks.replaceChildren();status.textContent=m;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend reconciliation-contract lokaal lezen. HOLD / DENY.");
    const rev=generation,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const d=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(rev!==generation||dashboard.hidden)return;
      if(!exact(d,[...Object.keys(fixed),"transferProtocolSha256",
        "custodyContractSha256","auditContractSha256","receiptRows",
        "requiredMatchChecks","externalReviewGates","conflictPolicy","allowedAlgorithms"])||
        Object.entries(fixed).some(([k,v])=>d[k]!==v)||
        !["transferProtocolSha256","custodyContractSha256",
          "auditContractSha256"].every(k=>sha(d[k]))||
        !Array.isArray(d.allowedAlgorithms)||d.allowedAlgorithms.length!==0||
        !Array.isArray(d.receiptRows)||d.receiptRows.length!==8||
        !Array.isArray(d.requiredMatchChecks)||d.requiredMatchChecks.length!==9||
        !Array.isArray(d.externalReviewGates)||d.externalReviewGates.length!==8||
        !Array.isArray(d.conflictPolicy)||d.conflictPolicy.length!==8)throw Error();
      const rowsOut=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=d.receiptRows[i],e=pairs[i];
        if(!exact(x,["rowId","evidenceId","requiredIndependentCustodianRole",
          "senderSignedReceipt","recipientSignedAcknowledgement",
          "senderSignatureVerification","recipientSignatureVerification",
          "exactEnvelopeDigestMatch","exactEvidenceDigestMatch",
          "identityScopeAndRevocation","trustedNonceAndTime","externalAuditProof",
          "reconciliation","transfer","gate","decision"])||
          x.rowId!=="AUD-E"+String(i+1).padStart(2,"0")||
          x.evidenceId!==e[0]||x.requiredIndependentCustodianRole!==e[1]||
          x.senderSignedReceipt!=="NOT_AVAILABLE"||
          x.recipientSignedAcknowledgement!=="NOT_AVAILABLE"||
          x.senderSignatureVerification!=="NOT_PERFORMED"||
          x.recipientSignatureVerification!=="NOT_PERFORMED"||
          x.exactEnvelopeDigestMatch!=="NOT_PERFORMED"||
          x.exactEvidenceDigestMatch!=="NOT_PERFORMED"||
          x.identityScopeAndRevocation!=="NOT_VERIFIED"||
          x.trustedNonceAndTime!=="NOT_VERIFIED"||
          x.externalAuditProof!=="NOT_AVAILABLE"||
          x.reconciliation!=="NOT_PERFORMED"||
          x.transfer!=="NOT_INITIATED"||x.gate!=="BLOCKED"||x.decision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const value of [x.rowId,x.evidenceId,x.requiredIndependentCustodianRole,
          "NOT_AVAILABLE","NOT_AVAILABLE","BLOCKED / DENY"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }rowsOut.append(tr);
      }
      const checkOut=document.createDocumentFragment();
      for(let i=0;i<9;i++){
        const x=d.requiredMatchChecks[i];
        if(!exact(x,["order","checkId","status","gate"])||
          x.order!==i+1||x.checkId!==match[i]||
          x.status!=="NOT_PERFORMED"||x.gate!=="BLOCKED")throw Error();
        const li=document.createElement("li");
        li.textContent=x.checkId+" — NOT_PERFORMED";checkOut.append(li);
      }
      for(let i=0;i<8;i++){
        const g=d.externalReviewGates[i],c=d.conflictPolicy[i];
        if(!exact(g,["order","gateId","status","decision"])||
          g.order!==i+1||g.gateId!==gates[i]||
          g.status!=="NOT_STARTED"||g.decision!=="DENY"||
          !exact(c,["reason","outcome","authorityEffect"])||
          c.reason!==conflicts[i]||c.outcome!=="DENY"||
          c.authorityEffect!=="NONE")throw Error();
      }
      if(rev!==generation||dashboard.hidden)return;
      rows.replaceChildren(rowsOut);checks.replaceChildren(checkOut);
      status.textContent="RECONCILIATION-CONTRACT HERKEND / 0 van 8 receiptparen vergeleken. Geen bewijs ontvangen. HOLD / DENY.";
    }catch(_){
      if(rev!==generation||dashboard.hidden)return;
      clear("RECONCILIATION GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
