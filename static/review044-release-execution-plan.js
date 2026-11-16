"use strict";
// Read-only verification plan for OWNER'S LATER TEST SESSION; no PASS controls.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-execution-plan-file"),load=$("admin-execution-plan-load"),
    status=$("admin-execution-plan-status"),rows=$("admin-execution-plan-rows"),
    procedure=$("admin-execution-plan-procedure"),dashboard=$("admin-dashboard");
  if(![file,load,status,rows,procedure,dashboard].every(Boolean))return;
  const gates=["SOURCE_PROVENANCE","VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION","AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION","DEPLOYMENT_APPROVAL"];
  const roles=["INDEPENDENT_SOURCE_CUSTODIAN","INDEPENDENT_COMPATIBILITY_REVIEWER",
    "INDEPENDENT_TECHNICAL_VERIFIER","AUTHORIZED_INDEPENDENT_HUMAN_REVIEWER",
    "INDEPENDENT_RELEASE_ATTESTOR","AUTHORIZED_RELEASE_OPERATOR"];
  const evidence=[
    ["ORIGINAL_SOURCE_BYTES_FROM_TRUSTED_CUSTODIAN","INDEPENDENT_PROVENANCE_ATTESTATION","SOURCE_HASH_AND_SIGNER_VALIDATION"],
    ["VERSION_LOCK_AND_DEPENDENCY_RECHECK","INDEPENDENT_BREAKING_CHANGE_ASSESSMENT","SUPPORTED_TARGET_RUNTIME_DECLARATION"],
    ["REPRODUCIBLE_TEST_RESULTS_WITH_PROVENANCE","INDEPENDENT_IDENTITY_AND_SUBJECT_BINDING","NONCE_REVOCATION_AND_CLOCK_CHECK"],
    ["INDEPENDENT_REVIEWER_AUTHENTICATION","SIGNED_ROLE_SCOPE_AND_INDEPENDENCE_ATTESTATION","RECORDED_HUMAN_DECISION_WITH_EXACT_MANIFEST_BINDING"],
    ["REPRODUCIBLE_SBOM_AND_BUILD_PROVENANCE","TRUSTED_SIGNING_KEY_AND_SIGNATURE_VALIDATION","EXTERNALLY_ANCHORED_TIMESTAMP_AND_AUDIT"],
    ["APPROVED_RELEASE_POLICY_AND_ENVIRONMENT","AUTHORIZED_SEPARATE_DEPLOYMENT_DECISION","ROLLBACK_AND_REVOCATION_READINESS"]
  ];
  const steps=["RECORD_ORIGINAL_ARTIFACT_FINGERPRINTS",
    "REQUEST_EVIDENCE_FROM_INDEPENDENT_CUSTODIAN",
    "CONFIRM_REVIEWER_IDENTITY_IN_EXTERNAL_TRUSTED_SYSTEM",
    "CHECK_SCOPE_REVOCATION_AND_SEPARATION_OF_DUTIES",
    "VERIFY_EVIDENCE_WITH_INDEPENDENT_TOOLS",
    "RECORD_UNSIGNED_LOCAL_OBSERVATIONS_SEPARATELY",
    "ESCALATE_TO_AUTHORIZED_HUMAN_REVIEW_OUTSIDE_THIS_TOOL"];
  const fixed={
    schema:"palaco.pp.recovery-002-release-execution-plan.v0",
    reference:"PP-RECOVERY-002",planProvenance:"UNSIGNED_LOCAL_REQUIREMENTS_ONLY",
    checkCount:18,independentVerification:"NOT_VERIFIED",
    humanReview:"NOT_COMPLETED",releaseReadiness:"NOT_READY",
    runtimeTests:"NOT_EXECUTED",softwareBundle:"NOT_CREATED",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const observation={
    recordType:"SELF_REPORTED_LOCAL_OBSERVATION_ONLY",
    evidenceHash:"REQUIRED_IF_LATER_RECORDED",externalSignature:"NOT_VERIFIED",
    roleClaims:"UNAUTHENTICATED",allowedEffect:"NONE",
    export:"SEPARATE_CREATE_ONLY_SNAPSHOT"
  };
  const exact=(x,k)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===k.length&&k.every(y=>Object.hasOwn(x,y));
  const sha=s=>typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);
  let version=0;
  const clear=(m="Geen Verification Execution Plan geladen. HOLD / DENY.")=>{
    version++;rows.replaceChildren();procedure.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; vorige planweergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend verificatieplan lokaal lezen. HOLD / DENY.");
    const tick=version,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>32768){
      status.textContent="GEWEIGERD / Kies JSON tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true})
        .decode(await f.arrayBuffer()));
      if(tick!==version||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"readinessCockpitSha256",
        "releaseEvidenceMatrixSha256","executionProcedure","verificationChecks",
        "gateSummary","futureObservationContract"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.readinessCockpitSha256)||!sha(data.releaseEvidenceMatrixSha256)||
        !Array.isArray(data.executionProcedure)||data.executionProcedure.length!==7||
        !Array.isArray(data.verificationChecks)||data.verificationChecks.length!==18||
        !Array.isArray(data.gateSummary)||data.gateSummary.length!==6||
        !exact(data.futureObservationContract,Object.keys(observation))||
        Object.entries(observation).some(([k,v])=>data.futureObservationContract[k]!==v))throw Error();
      const stages=document.createDocumentFragment();
      for(let i=0;i<7;i++){
        const x=data.executionProcedure[i];
        if(!exact(x,["order","step","status"])||x.order!==i+1||
          x.step!==steps[i]||x.status!=="NOT_STARTED")throw Error();
        const li=document.createElement("li");li.textContent=x.step+" — NOT_STARTED";
        stages.append(li);
      }
      const checkRows=document.createDocumentFragment();
      for(let i=0;i<6;i++){
        const summary=data.gateSummary[i];
        if(!exact(summary,["releaseGate","requiredIndependentRole","checkCount",
          "gate","reviewStatus"])||summary.releaseGate!==gates[i]||
          summary.requiredIndependentRole!==roles[i]||summary.checkCount!==3||
          summary.gate!=="BLOCKED"||summary.reviewStatus!=="NOT_COMPLETED")throw Error();
        for(let j=0;j<3;j++){
          const x=data.verificationChecks[i*3+j];
          if(!exact(x,["checkId","releaseGate","evidenceId",
            "requiredIndependentRole","step","execution","evidenceCapture",
            "independentVerification","reviewerAuthentication","reviewerAuthority",
            "gate","decision"])||
            x.checkId!=="RG"+String(i+1).padStart(2,"0")+"-E"+String(j+1).padStart(2,"0")||
            x.releaseGate!==gates[i]||x.evidenceId!==evidence[i][j]||
            x.requiredIndependentRole!==roles[i]||
            x.step!=="COLLECT_THEN_VERIFY_EXTERNALLY"||
            x.execution!=="NOT_STARTED"||x.evidenceCapture!=="NOT_PROVIDED"||
            x.independentVerification!=="NOT_PERFORMED"||
            x.reviewerAuthentication!=="NOT_ESTABLISHED"||
            x.reviewerAuthority!=="NOT_ESTABLISHED"||
            x.gate!=="BLOCKED"||x.decision!=="DENY")throw Error();
          const tr=document.createElement("tr");
          for(const value of [x.checkId,x.releaseGate,x.evidenceId,"NOT_STARTED","BLOCKED"]){
            const td=document.createElement("td");td.textContent=value;tr.append(td);
          }checkRows.append(tr);
        }
      }
      if(tick!==version||dashboard.hidden)return;
      rows.replaceChildren(checkRows);procedure.replaceChildren(stages);
      status.textContent="PLAN HERKEND / 18 controles en 7 procedurestappen NOT_STARTED. Geen verificatie uitgevoerd. HOLD / DENY.";
    }catch(_){
      if(tick!==version||dashboard.hidden)return;
      clear("VERIFICATIEPLAN GEWEIGERD / Ongeldig schema of tegenstrijdige status. HOLD / DENY.");
    }
  });
})();
