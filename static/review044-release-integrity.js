"use strict";
// Unsigned local-only release integrity inventory; not a release decision.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-integrity-file"),button=$("admin-integrity-load"),
    status=$("admin-integrity-status"),artifacts=$("admin-integrity-artifacts"),
    blockers=$("admin-integrity-blockers"),dashboard=$("admin-dashboard");
  if(![file,button,status,artifacts,blockers,dashboard].every(Boolean))return;
  const roles=["DECISION_DOSSIER","REVIEW_QUEUE","REVIEW_INTAKE",
    "VERIFICATION_PLAN","OBSERVATION_REGISTER","HANDOFF_MANIFEST",
    "RECEIPT_PROTOCOL","REVIEWER_AUTH_REQUIREMENTS",
    "REVIEWER_SERVICE_BLUEPRINT","REVIEWER_INTERFACE_CONTRACT",
    "TRUST_TRANSITION_PROTOCOL","REVOCATION_RECOVERY_CONTRACT",
    "SECURITY_ASSURANCE_DOSSIER","CONTRACT_COMPATIBILITY_REGISTER",
    "CHANGE_IMPACT_REGISTER"];
  const names=["decision-dossier","human-review-queue","review-intake",
    "verification-plan","observation-register","human-review-handoff",
    "review-protocol","reviewer-auth-contract","reviewer-service-blueprint",
    "reviewer-interface-contract","trust-transition","revocation-recovery",
    "security-assurance","contract-compatibility","change-impact"];
  const max=[16384,131072,16384,131072,131072,32768,65536,32768,
    32768,32768,32768,32768,65536,65536,65536];
  const problems=["INDEPENDENT_EVIDENCE_NOT_VERIFIED",
    "SOURCE_AUTHENTICITY_NOT_ATTESTED","REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "HUMAN_REVIEW_NOT_COMPLETED",
    "SIGNATURE_AND_RELEASE_PROVENANCE_NOT_ESTABLISHED",
    "COMPATIBILITY_NOT_EXTERNALLY_VERIFIED","TRUST_TRANSITIONS_BLOCKED",
    "REVOCATION_PROCESSING_NOT_IMPLEMENTED","PALACO_ONE_HANDOFF_BLOCKED"];
  const releaseGates=["SOURCE_PROVENANCE","VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION","AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION","DEPLOYMENT_APPROVAL"];
  const gates=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT",
    "OWNER_AUTHORITY","RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const fixed={
    schema:"palaco.pp.recovery-002-release-integrity.v0",
    reference:"PP-RECOVERY-002",artifactCount:15,
    integrityScope:"LOCAL_BYTES_AND_STRICT_INTERNAL_CHAIN_ONLY",
    rebuildPolicy:"ALL_DOWNSTREAM_ARTIFACTS_REQUIRE_REGENERATION",
    supportedSchemaVersion:"v0",mixedVersions:"DENY",
    softwareBundle:"NOT_CREATED",sbom:"NOT_GENERATED",
    provenanceAttestation:"NOT_ESTABLISHED",signing:"NOT_PERFORMED",
    runtimeTests:"NOT_EXECUTED",deployment:"NOT_EXECUTED",
    independentVerification:"NOT_VERIFIED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(o,fields)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===fields.length&&fields.every(k=>Object.hasOwn(o,k));
  const hash=s=>typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);
  let epoch=0;
  const clear=(message="Geen release-integriteitsmanifest geladen. HOLD / DENY.")=>{
    epoch++;artifacts.replaceChildren();blockers.replaceChildren();
    status.textContent=message;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Ongetekend release-integriteitsmanifest lokaal lezen. HOLD / DENY.");
    const generation=epoch,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try {
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(generation!==epoch||dashboard.hidden)return;
      const fields=[...Object.keys(fixed),"artifacts","dependencyEdges",
        "impactScope","releaseBlockers","releaseGates","originalDecisionGates"];
      if(!exact(data,fields)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !Array.isArray(data.artifacts)||data.artifacts.length!==15||
        !Array.isArray(data.dependencyEdges)||data.dependencyEdges.length!==14||
        !Array.isArray(data.releaseBlockers)||data.releaseBlockers.length!==9||
        !Array.isArray(data.releaseGates)||data.releaseGates.length!==6||
        !Array.isArray(data.originalDecisionGates)||
        data.originalDecisionGates.length!==5||
        !exact(data.impactScope,["changedRole","changeType","changeApplied","reassessment"])||
        !roles.includes(data.impactScope.changedRole)||
        !["SCHEMA_CHANGE","VERSION_CHANGE","CONTENT_CHANGE","POLICY_CHANGE"]
          .includes(data.impactScope.changeType)||
        data.impactScope.changeApplied!==false||
        data.impactScope.reassessment!=="REQUIRED")throw Error();
      const lines=document.createDocumentFragment();
      for(let i=0;i<15;i++){
        const a=data.artifacts[i],schema="palaco.pp.recovery-002-"+names[i]+".v0";
        if(!exact(a,["order","role","schema","version","sha256","maxBytes",
          "externalAuthenticity","signature"])||a.order!==i+1||
          a.role!==roles[i]||a.schema!==schema||a.version!=="v0"||
          !hash(a.sha256)||a.maxBytes!==max[i]||
          a.externalAuthenticity!=="NOT_ATTESTED"||
          a.signature!=="NOT_VERIFIED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [i+1,a.role,a.version,a.sha256.slice(0,18)+"…","NOT_VERIFIED"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }lines.append(tr);
        if(i>0){
          const edge=data.dependencyEdges[i-1];
          if(!exact(edge,["fromRole","toRole","relationship"])||
            edge.fromRole!==roles[i-1]||edge.toRole!==roles[i]||
            edge.relationship!=="REQUIRES_UPSTREAM_STRICT_REVALIDATION")throw Error();
        }
      }
      const blockersList=document.createDocumentFragment();
      for(let i=0;i<9;i++){
        const x=data.releaseBlockers[i];
        if(!exact(x,["blocker","status"])||x.blocker!==problems[i]||
          x.status!=="OPEN")throw Error();
        const li=document.createElement("li");li.textContent=x.blocker+" — OPEN";
        blockersList.append(li);
      }
      for(let i=0;i<6;i++){
        const g=data.releaseGates[i];
        if(!exact(g,["gate","status","verification"])||
          g.gate!==releaseGates[i]||g.status!=="BLOCKED"||
          g.verification!=="NOT_VERIFIED")throw Error();
      }
      for(let i=0;i<5;i++){
        const g=data.originalDecisionGates[i];
        if(!exact(g,["requirementId","gate","verification"])||
          g.requirementId!==gates[i]||g.gate!=="BLOCKED"||
          g.verification!=="NOT_VERIFIED")throw Error();
      }
      if(generation!==epoch||dashboard.hidden)return;
      artifacts.replaceChildren(lines);blockers.replaceChildren(blockersList);
      status.textContent="ONGETEKEND MANIFEST / 15 bronartefacten, 14 afhankelijkheden, 9 blokkades, 6 releasepoorten geblokkeerd. Geen softwarepakket of vrijgave. HOLD / DENY.";
    }catch(_){
      if(generation!==epoch||dashboard.hidden)return;
      clear("RELEASE-INTEGRITEITSMANIFEST GEWEIGERD / Ongeldige claims. HOLD / DENY.");
    }
  });
})();
