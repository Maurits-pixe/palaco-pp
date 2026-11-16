"use strict";
// Unsigned readiness viewer only. Never validates external evidence or grants.
(() => {
 const $=id=>document.getElementById(id);
 const file=$("admin-audit-matrix-file"),load=$("admin-audit-matrix-load"),
   status=$("admin-audit-matrix-status"),rows=$("admin-audit-matrix-rows"),
   steps=$("admin-audit-matrix-steps"),dashboard=$("admin-dashboard");
 if(![file,load,status,rows,steps,dashboard].every(Boolean))return;
 const items=[
 ["EXACT_DECISION_PROTOCOL_AND_CHANGE_HASHES","INDEPENDENT_AUDIT_VERIFIER","ORIGINAL_POLICY_AND_DECISION_BYTE_ATTESTATION","REBUILD_ORIGINAL_POLICY_AND_CHANGE_CONTROL_BYTES"],
 ["SIGNED_EXTERNAL_EVIDENCE_RECEIPT","INDEPENDENT_EVIDENCE_CUSTODIAN","INDEPENDENT_SIGNED_RECEIPT_AND_ISSUER_AUTHENTICATION","AUTHENTICATE_INDEPENDENT_ISSUER_AND_SIGNER_TRUST_CHAIN"],
 ["REVIEWER_IDENTITY_ROLE_AND_REVOCATION_ATTESTATION","INDEPENDENT_IDENTITY_AUDITOR","EXTERNAL_REVIEWER_IDENTITY_SCOPE_REVOCATION_CHECK","RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION"],
 ["CANONICAL_SIGNED_HUMAN_DECISION","AUTHORIZED_HUMAN_DECISION_AUDITOR","SEPARATE_SIGNED_HUMAN_AUTHORITY_DECISION","RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION"],
 ["TRUSTED_TIME_AND_NONCE_REPLAY_LEDGER_PROOF","INDEPENDENT_REPLAY_AUDITOR","TRUSTED_NONCE_LEDGER_AND_SIGNED_TIME_ANCHOR","VERIFY_REPLAY_NONCE_AND_TRUSTED_CLOCK_WINDOW"],
 ["IMMUTABLE_LOG_INCLUSION_AND_CONSISTENCY_PROOF","INDEPENDENT_AUDIT_VERIFIER","SIGNED_LOG_INCLUSION_AND_CONSISTENCY_WITNESSES","VERIFY_APPEND_ONLY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY"],
 ["KEY_EPOCH_ROTATION_AND_REVOCATION_PROOF","INDEPENDENT_CRYPTO_AUDITOR","PINNED_KEY_EPOCH_AND_SIGNED_REVOCATION_HISTORY","VERIFY_KEY_REVOCATION_AND_SIGNED_ROTATION_HISTORY"],
 ["SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_RECORD","INDEPENDENT_RELEASE_ATTESTOR","INDEPENDENT_RELEASE_OPERATOR_ROLLBACK_ATTESTATION","VERIFY_INDEPENDENT_DEPLOYMENT_AND_ROLLBACK_APPROVAL"]
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
 const sequence=[
 "REQUEST_ORIGINAL_EXTERNAL_EVIDENCE_FROM_INDEPENDENT_CUSTODIAN",
 "AUTHENTICATE_EXTERIOR_SIGNER_AND_ROLE_IN_TRUSTED_SYSTEM",
 "VERIFY_SIGNED_BYTES_AND_EXACT_DECISION_PROTOCOL_BINDING",
 "VERIFY_REPLAY_REVOCATION_AND_TRUSTED_TIMESTAMP",
 "VERIFY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY",
 "RECORD_INDEPENDENT_REVIEW_OUTSIDE_THIS_LOCAL_MODULE",
 "REQUIRE_SEPARATE_HUMAN_AND_DEPLOYMENT_AUTHORIZATION"
 ];
 const failures=["MISSING_EXTERNAL_AUDIT_RECEIPT","UNTRUSTED_LOG_ISSUER_OR_SIGNER",
 "INVALID_DECISION_OR_RECEIPT_SIGNATURE","SOURCE_HASH_OR_SIGNED_PAYLOAD_MISMATCH",
 "NONCE_REPLAY_OR_UNTRUSTED_TIMESTAMP","REVOKED_KEY_OR_REVIEWER_AUTHORITY",
 "AUDIT_LOG_FORK_OR_INCLUSION_FAILURE","MISSING_SEPARATE_HUMAN_OR_DEPLOYMENT_DECISION"];
 const fixed={schema:"palaco.pp.recovery-002-audit-evidence-readiness-matrix.v0",
 reference:"PP-RECOVERY-002",sourceBinding:"STRICT_INTERNAL_RECONSTRUCTION_ONLY",
 matrixProvenance:"UNSIGNED_LOCAL_REQUIREMENTS_NOT_EVIDENCE",
 requiredEvidenceCount:8,externallyVerifiedEvidenceCount:0,blockedEvidenceCount:8,
 auditEvidenceAcceptance:"PROHIBITED",trustedAuditService:"NOT_CONFIGURED",
 reviewerAuthority:"NOT_ESTABLISHED",independentVerification:"NOT_VERIFIED",
 humanDecision:"NOT_COMPLETED",deploymentDecision:"NOT_AUTHORIZED",
 changeApplied:false,trustedIssuerCount:0,keyMaterial:"NOT_PRESENT",
 releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
 palacoOneSession:"NOT_CREATED",authorization:"HOLD",accessDecision:"DENY",
 issuance:"NOT_AUTHORIZED"};
 const exact=(x,keys)=>x!==null&&typeof x==="object"&&!Array.isArray(x)&&
   Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
 const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
 let version=0;
 const clear=(msg="Geen Audit Evidence Readiness Matrix geladen. HOLD / DENY.")=>{
   version++;rows.replaceChildren();steps.replaceChildren();status.textContent=msg;
 };
 file.addEventListener("change",()=>clear("Bestand gewijzigd. HOLD / DENY."));
 const logout=()=>{clear();file.value="";};
 new MutationObserver(()=>{if(dashboard.hidden)logout();})
   .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
 $("admin-logout")?.addEventListener("click",logout);
 load.addEventListener("click",async()=>{
   clear("Ongetekende auditvereisten lokaal lezen. HOLD / DENY.");
   const stamp=version,f=file.files?.[0];
   if(dashboard.hidden||!f||f.size<1||f.size>65536){
     status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
   }
   try{
     const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
     if(stamp!==version||dashboard.hidden)return;
     if(!exact(data,[...Object.keys(fixed),"auditContractSha256",
       "decisionProtocolSha256","evidenceRows","reconstructionReadiness",
       "independentReviewSequence","failurePolicy","allowedAlgorithms"])||
       Object.entries(fixed).some(([k,v])=>data[k]!==v)||
       !sha(data.auditContractSha256)||!sha(data.decisionProtocolSha256)||
       !Array.isArray(data.allowedAlgorithms)||data.allowedAlgorithms.length!==0||
       !Array.isArray(data.evidenceRows)||data.evidenceRows.length!==8||
       !Array.isArray(data.reconstructionReadiness)||data.reconstructionReadiness.length!==8||
       !Array.isArray(data.independentReviewSequence)||data.independentReviewSequence.length!==7||
       !Array.isArray(data.failurePolicy)||data.failurePolicy.length!==8)throw Error();
     const result=document.createDocumentFragment();
     for(let i=0;i<8;i++){
       const x=data.evidenceRows[i],want=items[i];
       if(!exact(x,["rowId","evidenceId","requiredIndependentRole","missingProof",
         "requiredExternalVerificationStep","evidenceStatus","signerAuthentication",
         "independentVerification","blocker","nextPermittedAction","gate","decision"])||
         x.rowId!=="AUD-E"+String(i+1).padStart(2,"0")||
         x.evidenceId!==want[0]||x.requiredIndependentRole!==want[1]||
         x.missingProof!==want[2]||x.requiredExternalVerificationStep!==want[3]||
         x.evidenceStatus!=="NOT_PROVIDED"||x.signerAuthentication!=="NOT_ESTABLISHED"||
         x.independentVerification!=="NOT_PERFORMED"||
         x.blocker!=="MISSING_EXTERNALLY_ATTESTED_EVIDENCE"||
         x.nextPermittedAction!=="REQUEST_EVIDENCE_FOR_EXTERNAL_REVIEW_ONLY"||
         x.gate!=="BLOCKED"||x.decision!=="DENY")throw Error();
       const tr=document.createElement("tr");
       for(const val of [x.rowId,x.evidenceId,x.requiredIndependentRole,x.missingProof,"BLOCKED / DENY"]){
         const td=document.createElement("td");td.textContent=val;tr.append(td);
       }result.append(tr);
     }
     for(let i=0;i<8;i++){
       const x=data.reconstructionReadiness[i];
       if(!exact(x,["stepId","status","gate"])||x.stepId!==reconstruction[i]||
         x.status!=="NOT_PERFORMED"||x.gate!=="BLOCKED")throw Error();
     }
     const plan=document.createDocumentFragment();
     for(let i=0;i<7;i++){
       const x=data.independentReviewSequence[i];
       if(!exact(x,["order","stepId","status"])||x.order!==i+1||
         x.stepId!==sequence[i]||x.status!=="NOT_STARTED")throw Error();
       const li=document.createElement("li");li.textContent=x.stepId+" — NOT_STARTED";plan.append(li);
     }
     for(let i=0;i<8;i++){
       const x=data.failurePolicy[i];
       if(!exact(x,["reason","decision","authorityEffect"])||
         x.reason!==failures[i]||x.decision!=="DENY"||x.authorityEffect!=="NONE")throw Error();
     }
     if(stamp!==version||dashboard.hidden)return;
     rows.replaceChildren(result);steps.replaceChildren(plan);
     status.textContent="MATRIX HERKEND / 0 van 8 extern geverifieerd, 8 blokkades. HOLD / DENY.";
   }catch(_){
     if(stamp!==version||dashboard.hidden)return;
     clear("AUDIT READINESS MATRIX GEWEIGERD / Ongeldig schema of vrijgaveclaim. HOLD / DENY.");
   }
 });
})();
