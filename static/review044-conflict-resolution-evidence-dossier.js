"use strict";
// Read-only local conflict evidence requirements, not an evidence intake.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-conflict-dossier-file"),button=$("admin-conflict-dossier-load"),
    status=$("admin-conflict-dossier-status"),cases=$("admin-conflict-dossier-cases"),
    checks=$("admin-conflict-dossier-checks"),dashboard=$("admin-dashboard");
  if(![file,button,status,cases,checks,dashboard].every(Boolean))return;
  const conflicts=[
    "SENDER_RECEIPT_ABSENT_OR_UNTRUSTED","RECIPIENT_ACK_ABSENT_OR_UNTRUSTED",
    "ENVELOPE_OR_EVIDENCE_DIGEST_MISMATCH",
    "SENDER_RECIPIENT_IDENTITY_OR_SCOPE_MISMATCH",
    "AUDIENCE_PURPOSE_NONCE_OR_TIME_MISMATCH",
    "REVOKED_OR_UNTRUSTED_SIGNING_KEY","UNVERIFIABLE_EXTERNAL_AUDIT_PROOF",
    "SEPARATE_HUMAN_ACCEPTANCE_ABSENT"
  ];
  const evidence=[
    ["ORIGINAL_SIGNED_SENDER_RECEIPT_AND_ISSUER_CHAIN","INDEPENDENT_EVIDENCE_CUSTODIAN"],
    ["ORIGINAL_SIGNED_RECIPIENT_ACK_AND_RECEIVER_SCOPE","INDEPENDENT_EVIDENCE_CUSTODIAN"],
    ["CANONICAL_ENVELOPE_AND_ORIGINAL_EVIDENCE_DIGESTS","INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"],
    ["SENDER_RECEIVER_IDENTITY_AND_ROLE_SCOPE_ATTESTATIONS","INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"],
    ["SIGNED_NONCE_REPLAY_LEDGER_AND_TRUSTED_TIME_PROOF","INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"],
    ["SIGNER_KEY_EPOCH_AND_FRESH_REVOCATION_ATTESTATION","INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"],
    ["EXTERNAL_APPEND_ONLY_LOG_INCLUSION_AND_CONSISTENCY","INDEPENDENT_EVIDENCE_CUSTODIAN"],
    ["SEPARATE_SIGNED_HUMAN_ACCEPTANCE_OR_DENIAL_DECISION","AUTHORIZED_INDEPENDENT_CONFLICT_REVIEWER"]
  ];
  const checkpoints=[
    "EXACT_CONFLICT_PROTOCOL_AND_RECONCILIATION_HASHES",
    "TRUSTED_EXTERNAL_EVIDENCE_PROVENANCE_AND_ORIGINAL_BYTES",
    "INDEPENDENT_REVIEWER_IDENTITY_ROLE_SCOPE_AND_REVOCATION",
    "CANONICAL_SIGNATURE_DIGEST_AND_KEY_EPOCH_VALIDATION",
    "NONCE_REPLAY_TRUSTED_TIME_AND_AUDIENCE_VALIDATION",
    "IMMUTABLE_EXTERNAL_LOG_PROOF",
    "SEPARATE_AUTHORIZED_HUMAN_CONFLICT_DECISION",
    "SEPARATE_DEPLOYMENT_RELEASE_AUTHORIZATION"
  ];
  const roles=[
    "INDEPENDENT_EVIDENCE_CUSTODIAN",
    "INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER",
    "AUTHORIZED_INDEPENDENT_CONFLICT_REVIEWER",
    "SEPARATE_RELEASE_AUTHORITY"
  ];
  const sequence=[
    "PRESERVE_DISPUTED_ORIGINALS_WITH_INDEPENDENT_CUSTODIAN",
    "FREEZE_ACCEPTANCE_AND_FLAG_CONFLICT_FOR_HUMAN_REVIEW",
    "AUTHENTICATE_INDEPENDENT_SENDER_AND_RECIPIENT",
    "COMPARE_CANONICAL_SIGNED_BYTES_AND_EXACT_DIGESTS",
    "VERIFY_NONCE_REPLAY_TRUSTED_TIME_AND_KEY_REVOCATION",
    "VERIFY_INDEPENDENT_AUDIT_INCLUSION_AND_LOG_CONSISTENCY",
    "OBTAIN_SEPARATE_AUTHORIZED_CONFLICT_REVIEW_DECISION",
    "REQUIRE_INDEPENDENT_POST_REVIEW_RELEASE_AUTHORIZATION"
  ];
  const rules=[
    "NO_AUTOMATIC_ACCEPTANCE_FROM_LOCAL_RECEIPT_CLAIM",
    "NO_AUTO_RETRY_OR_REPLAY_OF_DISPUTED_TRANSFER",
    "NO_MUTATION_OF_ORIGINAL_SIGNED_EVIDENCE",
    "NO_TRUST_ON_FIRST_USE_OR_UNVERIFIED_KEYS",
    "NO_ESCALATION_FROM_SELF_ASSERTED_REVIEWER_ROLE",
    "NO_DEPLOYMENT_FROM_RESOLUTION_OUTCOME_ALONE"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-conflict-resolution-evidence-dossier.v0",
    reference:"PP-RECOVERY-002",sourceBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    dossierProvenance:"UNSIGNED_LOCAL_REQUIREMENTS_NOT_A_CONFLICT_CASE",
    potentialConflictCount:8,observedConflictCount:0,externalEvidenceReceivedCount:0,
    independentlyReviewedCount:0,externalRequestDelivery:"NOT_SENT",
    evidenceIntake:"NOT_IMPLEMENTED",conflictAdjudication:"NOT_PERFORMED",
    independentConflictDecision:"NOT_AVAILABLE",trustedAuditService:"NOT_CONFIGURED",
    independentVerification:"NOT_VERIFIED",humanDecision:"NOT_COMPLETED",
    evidenceAcceptance:"PROHIBITED",evidenceTransfer:"NOT_INITIATED",
    evidenceStorage:"NONE",trustedIssuerCount:0,releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(x,k)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===k.length&&k.every(v=>Object.hasOwn(x,v));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let generation=0;
  const clear=(msg="Geen Conflict Resolution Evidence Dossier geladen. HOLD / DENY.")=>{
    generation++;cases.replaceChildren();checks.replaceChildren();status.textContent=msg;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Ongetekend bewijsvereistendossier lokaal lezen. HOLD / DENY.");
    const token=generation,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const d=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(token!==generation||dashboard.hidden)return;
      if(!exact(d,[...Object.keys(fixed),"conflictProtocolSha256",
          "reconciliationSha256","transferProtocolSha256","potentialConflictCases",
          "reviewCheckpoints","requiredReviewers","independentResolutionSequence",
          "nonBypassRules","allowedAlgorithms"])||
          Object.entries(fixed).some(([k,v])=>d[k]!==v)||
          !["conflictProtocolSha256","reconciliationSha256","transferProtocolSha256"].every(k=>sha(d[k]))||
          !Array.isArray(d.allowedAlgorithms)||d.allowedAlgorithms.length!==0||
          !Array.isArray(d.potentialConflictCases)||d.potentialConflictCases.length!==8||
          !Array.isArray(d.reviewCheckpoints)||d.reviewCheckpoints.length!==8||
          !Array.isArray(d.requiredReviewers)||d.requiredReviewers.length!==4||
          !Array.isArray(d.independentResolutionSequence)||d.independentResolutionSequence.length!==8||
          !Array.isArray(d.nonBypassRules)||d.nonBypassRules.length!==6)throw Error();
      const cells=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=d.potentialConflictCases[i];
        if(!exact(x,["caseId","potentialConflict","classification",
            "requiredExternalEvidenceId","requiredIndependentRole",
            "originalEvidence","sourceAuthenticity","independentReviewerAuthority",
            "externalAuditProof","review","decision","nextPermittedAction"])||
            x.caseId!=="CR-E"+String(i+1).padStart(2,"0")||
            x.potentialConflict!==conflicts[i]||
            x.classification!=="POTENTIAL_CONFLICT_NOT_OBSERVED"||
            x.requiredExternalEvidenceId!==evidence[i][0]||
            x.requiredIndependentRole!==evidence[i][1]||
            x.originalEvidence!=="NOT_RECEIVED"||
            x.sourceAuthenticity!=="NOT_VERIFIED"||
            x.independentReviewerAuthority!=="NOT_ESTABLISHED"||
            x.externalAuditProof!=="NOT_AVAILABLE"||
            x.review!=="NOT_STARTED"||x.decision!=="DENY"||
            x.nextPermittedAction!=="PREPARE_REQUEST_FOR_EXTERNAL_REVIEW_ONLY")throw Error();
        const tr=document.createElement("tr");
        for(const value of [x.caseId,x.potentialConflict,x.requiredExternalEvidenceId,
          x.requiredIndependentRole,"NOT_RECEIVED / DENY"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }cells.append(tr);
      }
      const list=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=d.reviewCheckpoints[i],y=d.independentResolutionSequence[i];
        if(!exact(x,["order","checkpointId","status","gate"])||
           x.order!==i+1||x.checkpointId!==checkpoints[i]||
           x.status!=="NOT_PERFORMED"||x.gate!=="BLOCKED"||
           !exact(y,["order","stepId","status","gate"])||
           y.order!==i+1||y.stepId!==sequence[i]||
           y.status!=="NOT_STARTED"||y.gate!=="BLOCKED")throw Error();
        const li=document.createElement("li");
        li.textContent=x.checkpointId+" — BLOCKED";list.append(li);
      }
      for(let i=0;i<4;i++){
        const x=d.requiredReviewers[i];
        if(!exact(x,["role","authentication","scope","decision"])||
           x.role!==roles[i]||x.authentication!=="NOT_ESTABLISHED"||
           x.scope!=="NOT_ATTESTED"||x.decision!=="NOT_COMPLETED")throw Error();
      }
      for(let i=0;i<6;i++){
        const x=d.nonBypassRules[i];
        if(!exact(x,["ruleId","status","authorityEffect"])||
           x.ruleId!==rules[i]||x.status!=="DENY_ONLY"||
           x.authorityEffect!=="NONE")throw Error();
      }
      if(token!==generation||dashboard.hidden)return;
      cases.replaceChildren(cells);checks.replaceChildren(list);
      status.textContent="CONFLICT-EVIDENCE DOSSIER HERKEND / 8 mogelijke gevallen, 0 waargenomen. Geen externe bewijzen ontvangen. HOLD / DENY.";
    }catch(_){
      if(token!==generation||dashboard.hidden)return;
      clear("EVIDENCEDOSSIER GEWEIGERD / Ongeldig contract of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
