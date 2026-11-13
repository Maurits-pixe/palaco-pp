"use strict";
// Unsigned Release Evidence Matrix: view-only, no approvals or evidence acceptance.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-evidence-matrix-file"),button=$("admin-evidence-matrix-load"),
    status=$("admin-evidence-matrix-status"),rows=$("admin-evidence-matrix-rows"),
    dashboard=$("admin-dashboard");
  if(![file,button,status,rows,dashboard].every(Boolean))return;
  const gates=["SOURCE_PROVENANCE","VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION","AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION","DEPLOYMENT_APPROVAL"];
  const role=["INDEPENDENT_SOURCE_CUSTODIAN","INDEPENDENT_COMPATIBILITY_REVIEWER",
    "INDEPENDENT_TECHNICAL_VERIFIER","AUTHORIZED_INDEPENDENT_HUMAN_REVIEWER",
    "INDEPENDENT_RELEASE_ATTESTOR","AUTHORIZED_RELEASE_OPERATOR"];
  const evidence=[
    ["ORIGINAL_SOURCE_BYTES_FROM_TRUSTED_CUSTODIAN",
     "INDEPENDENT_PROVENANCE_ATTESTATION","SOURCE_HASH_AND_SIGNER_VALIDATION"],
    ["VERSION_LOCK_AND_DEPENDENCY_RECHECK",
     "INDEPENDENT_BREAKING_CHANGE_ASSESSMENT","SUPPORTED_TARGET_RUNTIME_DECLARATION"],
    ["REPRODUCIBLE_TEST_RESULTS_WITH_PROVENANCE",
     "INDEPENDENT_IDENTITY_AND_SUBJECT_BINDING","NONCE_REVOCATION_AND_CLOCK_CHECK"],
    ["INDEPENDENT_REVIEWER_AUTHENTICATION",
     "SIGNED_ROLE_SCOPE_AND_INDEPENDENCE_ATTESTATION",
     "RECORDED_HUMAN_DECISION_WITH_EXACT_MANIFEST_BINDING"],
    ["REPRODUCIBLE_SBOM_AND_BUILD_PROVENANCE",
     "TRUSTED_SIGNING_KEY_AND_SIGNATURE_VALIDATION",
     "EXTERNALLY_ANCHORED_TIMESTAMP_AND_AUDIT"],
    ["APPROVED_RELEASE_POLICY_AND_ENVIRONMENT",
     "AUTHORIZED_SEPARATE_DEPLOYMENT_DECISION",
     "ROLLBACK_AND_REVOCATION_READINESS"]
  ];
  const fixed={schema:"palaco.pp.recovery-002-release-evidence-matrix.v0",
    reference:"PP-RECOVERY-002",integrityBinding:"STRICT_INTERNAL_SIXTEEN_SOURCE_CONSISTENCY",
    evidenceItemCount:18,unmetReleaseGateCount:6,externalEvidenceIncluded:false,
    independentVerification:"NOT_VERIFIED",reviewerAuthority:"NOT_ESTABLISHED",
    releaseReadiness:"NOT_READY",softwareBundle:"NOT_CREATED",sbom:"NOT_GENERATED",
    signing:"NOT_PERFORMED",deployment:"NOT_EXECUTED",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",accessDecision:"DENY",
    issuance:"NOT_AUTHORIZED"};
  const exact=(x,k)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===k.length&&k.every(v=>Object.hasOwn(x,v));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let revision=0;
  const clear=(m="Geen Release Evidence Matrix geladen. HOLD / DENY.")=>{
    revision++;rows.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; vorige weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal ongetekende bewijsvoorwaarden lezen. HOLD / DENY.");
    const version=revision,chosen=file.files?.[0];
    if(dashboard.hidden||!chosen||chosen.size<1||chosen.size>32768){
      status.textContent="GEWEIGERD / Kies een JSON-matrix tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true})
        .decode(await chosen.arrayBuffer()));
      if(version!==revision||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"releaseIntegrityManifestSha256","evidenceMatrix"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.releaseIntegrityManifestSha256)||
        !Array.isArray(data.evidenceMatrix)||data.evidenceMatrix.length!==6)throw Error();
      const fragment=document.createDocumentFragment();
      for(let i=0;i<6;i++){
        const x=data.evidenceMatrix[i];
        if(!exact(x,["order","releaseGate","requiredEvidence","requiredIndependentRole",
          "reviewerAuthentication","reviewerAuthority","evidenceAcceptance",
          "reviewDecision","gate","decision"])||
          x.order!==i+1||x.releaseGate!==gates[i]||
          x.requiredIndependentRole!==role[i]||
          x.reviewerAuthentication!=="NOT_ESTABLISHED"||
          x.reviewerAuthority!=="NOT_ESTABLISHED"||
          x.evidenceAcceptance!=="NOT_PERFORMED"||
          x.reviewDecision!=="NOT_COMPLETED"||x.gate!=="BLOCKED"||
          x.decision!=="DENY"||!Array.isArray(x.requiredEvidence)||
          x.requiredEvidence.length!==3)throw Error();
        for(let j=0;j<3;j++){
          const e=x.requiredEvidence[j];
          if(!exact(e,["evidenceId","status","independentVerification"])||
            e.evidenceId!==evidence[i][j]||e.status!=="MISSING"||
            e.independentVerification!=="NOT_PERFORMED")throw Error();
        }
        const tr=document.createElement("tr");
        for(const value of [x.order,x.releaseGate,x.requiredIndependentRole,
          x.requiredEvidence.map(e=>e.evidenceId).join(", "),"BLOCKED / DENY"]){
          const td=document.createElement("td");td.textContent=String(value);
          tr.append(td);
        }fragment.append(tr);
      }
      if(version!==revision||dashboard.hidden)return;
      rows.replaceChildren(fragment);
      status.textContent="ONGETEKENDE MATRIX / 6 poorten BLOCKED, 18 bewijsstukken MISSING. Geen reviewer bevoegd, geen externe verificatie, HOLD / DENY.";
    }catch(_){
      if(version!==revision||dashboard.hidden)return;
      clear("RELEASE EVIDENCE MATRIX GEWEIGERD / Ongeldige structuur of statusclaim. HOLD / DENY.");
    }
  });
})();
