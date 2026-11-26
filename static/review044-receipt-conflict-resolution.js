"use strict";
// Unsigned local contract viewer; cannot process disputed receipts or grant.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-conflict-resolution-file"),load=$("admin-conflict-resolution-load"),
    status=$("admin-conflict-resolution-status"),
    rows=$("admin-conflict-resolution-rows"),
    steps=$("admin-conflict-resolution-steps"),
    dashboard=$("admin-dashboard");
  if(![file,load,status,rows,steps,dashboard].every(Boolean))return;
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
  const process=[
    "PRESERVE_DISPUTED_ORIGINALS_WITH_INDEPENDENT_CUSTODIAN",
    "FREEZE_ACCEPTANCE_AND_FLAG_CONFLICT_FOR_HUMAN_REVIEW",
    "AUTHENTICATE_INDEPENDENT_SENDER_AND_RECIPIENT",
    "COMPARE_CANONICAL_SIGNED_BYTES_AND_EXACT_DIGESTS",
    "VERIFY_NONCE_REPLAY_TRUSTED_TIME_AND_KEY_REVOCATION",
    "VERIFY_INDEPENDENT_AUDIT_INCLUSION_AND_LOG_CONSISTENCY",
    "OBTAIN_SEPARATE_AUTHORIZED_CONFLICT_REVIEW_DECISION",
    "REQUIRE_INDEPENDENT_POST_REVIEW_RELEASE_AUTHORIZATION"
  ];
  const roles=[
    "INDEPENDENT_EVIDENCE_CUSTODIAN",
    "INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER",
    "AUTHORIZED_INDEPENDENT_CONFLICT_REVIEWER",
    "SEPARATE_RELEASE_AUTHORITY"
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
    schema:"palaco.pp.recovery-002-receipt-conflict-resolution.v0",
    reference:"PP-RECOVERY-002",binding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
    scope:"UNSIGNED_CONFLICT_RESOLUTION_REQUIREMENTS_NOT_ADJUDICATION",
    requiredReceiptPairs:8,externallyAdjudicatedConflicts:0,acceptedReceiptPairs:0,
    conflictIntake:"NOT_IMPLEMENTED",signedReceiptVerification:"NOT_CONFIGURED",
    trustedReplayLedger:"NOT_CONFIGURED",externalAudit:"NOT_CONFIGURED",
    independentConflictReview:"NOT_COMPLETED",humanDecision:"NOT_COMPLETED",
    evidenceAcceptance:"PROHIBITED",evidenceTransfer:"NOT_INITIATED",
    evidenceStorage:"NONE",trustedIssuerCount:0,releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(x,keys)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let revision=0;
  const clear=(m="Geen Receipt Conflict Resolution Protocol geladen. HOLD / DENY.")=>{
    revision++;rows.replaceChildren();steps.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekende conflictregels lokaal lezen. HOLD / DENY.");
    const stamp=revision,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const d=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(stamp!==revision||dashboard.hidden)return;
      if(!exact(d,[...Object.keys(fixed),"reconciliationSha256",
         "transferProtocolSha256","custodyContractSha256","conflictCases",
         "disputeConditions","independentResolutionSteps","escalationRoles",
         "nonBypassRules","allowedAlgorithms"])||
         Object.entries(fixed).some(([k,v])=>d[k]!==v)||
         !["reconciliationSha256","transferProtocolSha256",
           "custodyContractSha256"].every(k=>sha(d[k]))||
         !Array.isArray(d.allowedAlgorithms)||d.allowedAlgorithms.length!==0||
         !Array.isArray(d.conflictCases)||d.conflictCases.length!==8||
         !Array.isArray(d.disputeConditions)||d.disputeConditions.length!==8||
         !Array.isArray(d.independentResolutionSteps)||
           d.independentResolutionSteps.length!==8||
         !Array.isArray(d.escalationRoles)||d.escalationRoles.length!==4||
         !Array.isArray(d.nonBypassRules)||d.nonBypassRules.length!==6)throw Error();
      const table=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=d.conflictCases[i],e=evidence[i],condition=d.disputeConditions[i];
        if(!exact(x,["rowId","evidenceId","custodianRoleRequired","senderReceipt",
           "recipientAck","conflictDetermination","externalCaseCreation",
           "evidencePreservation","independentAdjudication","disposition",
           "transfer","gate","accessDecision"])||
           x.rowId!=="AUD-E"+String(i+1).padStart(2,"0")||
           x.evidenceId!==e[0]||x.custodianRoleRequired!==e[1]||
           x.senderReceipt!=="NOT_RECEIVED"||x.recipientAck!=="NOT_RECEIVED"||
           x.conflictDetermination!=="NOT_PERFORMED"||
           x.externalCaseCreation!=="NOT_STARTED"||
           x.evidencePreservation!=="REQUIRED_NOT_EXECUTED"||
           x.independentAdjudication!=="NOT_COMPLETED"||
           x.disposition!=="UNRESOLVED_DENY"||x.transfer!=="NOT_INITIATED"||
           x.gate!=="BLOCKED"||x.accessDecision!=="DENY"||
           !exact(condition,["order","reasonId","classification","disposition"])||
           condition.order!==i+1||condition.reasonId!==conflicts[i]||
           condition.classification!=="POTENTIAL_CONFLICT_NOT_OBSERVED"||
           condition.disposition!=="DENY_PENDING_INDEPENDENT_REVIEW")throw Error();
        const tr=document.createElement("tr");
        for(const val of [x.rowId,x.evidenceId,x.custodianRoleRequired,
          "NOT_RECEIVED","NOT_PERFORMED","UNRESOLVED_DENY"]){
          const td=document.createElement("td");td.textContent=val;tr.append(td);
        }table.append(tr);
      }
      const list=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const x=d.independentResolutionSteps[i];
        if(!exact(x,["order","stepId","status","gate"])||
           x.order!==i+1||x.stepId!==process[i]||
           x.status!=="NOT_STARTED"||x.gate!=="BLOCKED")throw Error();
        const li=document.createElement("li");li.textContent=x.stepId+" — NOT_STARTED";
        list.append(li);
      }
      for(let i=0;i<4;i++){
        const x=d.escalationRoles[i];
        if(!exact(x,["role","authentication","authority"])||
           x.role!==roles[i]||x.authentication!=="NOT_ESTABLISHED"||
           x.authority!=="NOT_ESTABLISHED")throw Error();
      }
      for(let i=0;i<6;i++){
        const x=d.nonBypassRules[i];
        if(!exact(x,["ruleId","status","authorityEffect"])||
           x.ruleId!==rules[i]||x.status!=="ENFORCE_DENY_ONLY"||
           x.authorityEffect!=="NONE")throw Error();
      }
      if(stamp!==revision||dashboard.hidden)return;
      rows.replaceChildren(table);steps.replaceChildren(list);
      status.textContent="CONFLICTPROTOCOL HERKEND / 0 echte conflictsituaties onderzocht; 8 mogelijke situaties beschreven. HOLD / DENY.";
    }catch(_){
      if(stamp!==revision||dashboard.hidden)return;
      clear("CONFLICTPROTOCOL GEWEIGERD / Ongeldig schema of autorisatieclaim. HOLD / DENY.");
    }
  });
})();
