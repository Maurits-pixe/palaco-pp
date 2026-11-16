"use strict";
// Local, unsigned, read-only cockpit. This UI cannot verify external evidence.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-release-cockpit-file"),button=$("admin-release-cockpit-load"),
    status=$("admin-release-cockpit-status"),metrics=$("admin-release-cockpit-metrics"),
    rows=$("admin-release-cockpit-rows"),blockers=$("admin-release-cockpit-blockers"),
    dashboard=$("admin-dashboard");
  if(![file,button,status,metrics,rows,blockers,dashboard].every(Boolean))return;
  const gateNames=["SOURCE_PROVENANCE","VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION","AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION","DEPLOYMENT_APPROVAL"];
  const independentRoles=["INDEPENDENT_SOURCE_CUSTODIAN",
    "INDEPENDENT_COMPATIBILITY_REVIEWER","INDEPENDENT_TECHNICAL_VERIFIER",
    "AUTHORIZED_INDEPENDENT_HUMAN_REVIEWER","INDEPENDENT_RELEASE_ATTESTOR",
    "AUTHORIZED_RELEASE_OPERATOR"];
  const evidence=[
    ["ORIGINAL_SOURCE_BYTES_FROM_TRUSTED_CUSTODIAN","INDEPENDENT_PROVENANCE_ATTESTATION","SOURCE_HASH_AND_SIGNER_VALIDATION"],
    ["VERSION_LOCK_AND_DEPENDENCY_RECHECK","INDEPENDENT_BREAKING_CHANGE_ASSESSMENT","SUPPORTED_TARGET_RUNTIME_DECLARATION"],
    ["REPRODUCIBLE_TEST_RESULTS_WITH_PROVENANCE","INDEPENDENT_IDENTITY_AND_SUBJECT_BINDING","NONCE_REVOCATION_AND_CLOCK_CHECK"],
    ["INDEPENDENT_REVIEWER_AUTHENTICATION","SIGNED_ROLE_SCOPE_AND_INDEPENDENCE_ATTESTATION","RECORDED_HUMAN_DECISION_WITH_EXACT_MANIFEST_BINDING"],
    ["REPRODUCIBLE_SBOM_AND_BUILD_PROVENANCE","TRUSTED_SIGNING_KEY_AND_SIGNATURE_VALIDATION","EXTERNALLY_ANCHORED_TIMESTAMP_AND_AUDIT"],
    ["APPROVED_RELEASE_POLICY_AND_ENVIRONMENT","AUTHORIZED_SEPARATE_DEPLOYMENT_DECISION","ROLLBACK_AND_REVOCATION_READINESS"]
  ];
  const blockersList=["INDEPENDENT_EVIDENCE_NOT_VERIFIED","SOURCE_AUTHENTICITY_NOT_ATTESTED",
    "REVIEWER_AUTHORITY_NOT_ESTABLISHED","HUMAN_REVIEW_NOT_COMPLETED",
    "SIGNATURE_AND_RELEASE_PROVENANCE_NOT_ESTABLISHED",
    "COMPATIBILITY_NOT_EXTERNALLY_VERIFIED","TRUST_TRANSITIONS_BLOCKED",
    "REVOCATION_PROCESSING_NOT_IMPLEMENTED","PALACO_ONE_HANDOFF_BLOCKED"];
  const steps=["COLLECT_EXTERNAL_SOURCE_ATTESTATIONS","VERIFY_INDEPENDENT_REVIEWER_CREDENTIALS",
    "COLLECT_REPRODUCIBLE_TEST_AND_SBOM_EVIDENCE","VERIFY_SIGNED_RELEASE_PROVENANCE",
    "COMPLETE_AUTHORIZED_HUMAN_RELEASE_REVIEW"];
  const counts={sourceArtifacts:15,releaseGatesBlocked:6,evidenceMissing:18,
    releaseBlockersOpen:9,originalDecisionGatesBlocked:5,approvedGates:0};
  const fixed={
    schema:"palaco.pp.recovery-002-release-readiness-cockpit.v0",
    reference:"PP-RECOVERY-002",
    snapshotProvenance:"UNSIGNED_LOCAL_RECONSTRUCTION",
    dataRefresh:"MANUAL_OFFLINE_REBUILD_REQUIRED",
    interactiveApproval:"PROHIBITED",
    externalEvidenceVerification:"NOT_PERFORMED",
    runtimeTests:"NOT_EXECUTED",softwareBundle:"NOT_CREATED",
    signing:"NOT_PERFORMED",deployment:"NOT_EXECUTED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(o,k)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
  let revision=0;
  const clear=(m="Geen Release Readiness Cockpit geladen. HOLD / DENY.")=>{
    revision++;metrics.replaceChildren();rows.replaceChildren();
    blockers.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; cockpitweergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal release-cockpitrapport lezen. HOLD / DENY.");
    const index=revision,selected=file.files?.[0];
    if(dashboard.hidden||!selected||selected.size<1||selected.size>32768){
      status.textContent="GEWEIGERD / Kies JSON tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await selected.arrayBuffer()));
      if(index!==revision||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"releaseEvidenceMatrixSha256",
        "releaseIntegrityManifestSha256","counts","releaseGateRows",
        "openReleaseBlockers","handoffChecklist"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.releaseEvidenceMatrixSha256)||!sha(data.releaseIntegrityManifestSha256)||
        !exact(data.counts,Object.keys(counts))||
        Object.entries(counts).some(([k,v])=>data.counts[k]!==v)||
        !Array.isArray(data.releaseGateRows)||data.releaseGateRows.length!==6||
        !Array.isArray(data.openReleaseBlockers)||data.openReleaseBlockers.length!==9||
        !Array.isArray(data.handoffChecklist)||data.handoffChecklist.length!==5)throw Error();
      const gateRows=document.createDocumentFragment();
      for(let i=0;i<6;i++){
        const x=data.releaseGateRows[i];
        if(!exact(x,["order","gateId","requiredIndependentRole",
          "missingEvidenceIds","reviewerAuthority","gate","decision"])||
          x.order!==i+1||x.gateId!==gateNames[i]||
          x.requiredIndependentRole!==independentRoles[i]||
          !same(x.missingEvidenceIds,evidence[i])||
          x.reviewerAuthority!=="NOT_ESTABLISHED"||
          x.gate!=="BLOCKED"||x.decision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const v of [x.order,x.gateId,x.requiredIndependentRole,
          x.missingEvidenceIds.length,"BLOCKED / DENY"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }gateRows.append(tr);
      }
      const blockerRows=document.createDocumentFragment();
      for(let i=0;i<9;i++){
        const x=data.openReleaseBlockers[i];
        if(!exact(x,["blockerId","status"])||
          x.blockerId!==blockersList[i]||x.status!=="OPEN")throw Error();
        const li=document.createElement("li");li.textContent=x.blockerId+" — OPEN";
        blockerRows.append(li);
      }
      for(let i=0;i<5;i++){
        const step=data.handoffChecklist[i];
        if(!exact(step,["step","status","approvalEffect"])||
          step.step!==steps[i]||step.status!=="NOT_STARTED"||
          step.approvalEffect!=="NONE")throw Error();
      }
      const metricNodes=document.createDocumentFragment();
      for(const [label,value] of [["Bronartefacten",15],["Geblokkeerde releasepoorten",6],
        ["Ontbrekende bewijzen",18],["Open releaseblokkades",9],
        ["Herstelbeslispoorten geblokkeerd",5],["Vrijgegeven poorten",0]]){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=label;dd.textContent=String(value);metricNodes.append(dt,dd);
      }
      if(index!==revision||dashboard.hidden)return;
      rows.replaceChildren(gateRows);blockers.replaceChildren(blockerRows);
      metrics.replaceChildren(metricNodes);
      status.textContent="ONGETEKENDE RELEASECOCKPIT / 6 poorten BLOCKED, 18 bewijzen MISSING, 9 blokkades OPEN. Geen externe verificatie of vrijgave. HOLD / DENY.";
    }catch(_){
      if(index!==revision||dashboard.hidden)return;
      clear("RELEASECOCKPIT GEWEIGERD / Ongeldige structuur of tegenstrijdige status. HOLD / DENY.");
    }
  });
})();
