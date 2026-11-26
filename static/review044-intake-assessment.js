"use strict";
// Read-only preview of an untrusted exported Python intake assessment.
// No server calls, no filesystem writes, no evidence or actor attestation.
(() => {
  const $ = id => document.getElementById(id);
  const input = $("admin-intake-assessment-file");
  const button = $("admin-intake-assessment-load");
  const status = $("admin-intake-assessment-status");
  const entries = $("admin-intake-assessment-rows");
  const blockers = $("admin-intake-assessment-gates");
  const dashboard = $("admin-dashboard");
  if (![input,button,status,entries,blockers,dashboard].every(Boolean)) return;
  const names = ["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const checks = [
    "ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED","SOURCE_PROVENANCE_NOT_ATTESTED",
    "SUBMITTER_IDENTITY_NOT_AUTHENTICATED","REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "SUBJECT_BINDING_NOT_ESTABLISHED","INDEPENDENT_REVIEW_NOT_COMPLETED"
  ];
  const kinds = new Set(["DOCUMENT","SCREENSHOT","LOG_EXCERPT","OTHER_UNTRUSTED"]);
  const roles = new Set(["OWNER_CLAIMED","REVIEWER_CLAIMED","SOURCE_CLAIMED"]);
  const fixed = {
    schema:"palaco.pp.recovery-002-intake-assessment.v0",
    reference:"PP-RECOVERY-002",
    validationScope:"STRICT_INTERNAL_STRUCTURE_AND_HASH_LINKS_ONLY",
    originalEvidenceVerification:"NOT_PERFORMED",
    sourceAuthenticity:"NOT_ESTABLISHED",
    submitterAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    crossSourceSubjectBinding:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    independentVerification:"NOT_VERIFIED",reviewDecision:"HOLD",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const keys = [...Object.keys(fixed),"decisionDossierSha256","requestQueueSha256",
    "intakeSnapshotSha256","intakeCount","assessedItems","requirements"];
  const itemKeys = ["sequence","requestSequence","requirementId","evidenceSha256",
    "evidenceKind","submitterRoleClaim","missingControls","assessment","gate"];
  const gateKeys = ["requirementId","linkedIntakeCount","evidenceStatus","gate"];
  const sha = x => typeof x === "string" && /^[a-f0-9]{64}$/.test(x);
  const exact = (obj,keys) => obj && typeof obj === "object" &&
    !Array.isArray(obj) && Object.keys(obj).length === keys.length &&
    keys.every(key => Object.hasOwn(obj,key));
  let version = 0;
  const clear = (message="Geen intakebeoordeling geladen. HOLD / DENY.") => {
    version++;entries.replaceChildren();blockers.replaceChildren();status.textContent=message;
  };
  input.addEventListener("change",() => clear("Bestand gewijzigd; vorige beoordeling vervallen. HOLD / DENY."));
  new MutationObserver(() => {if(dashboard.hidden){clear();input.value="";}})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",() => {clear();input.value="";});
  button.addEventListener("click",async() => {
    clear("Lokaal bewijsrapport wordt gelezen. HOLD / DENY.");
    const generation=version, file=input.files?.[0];
    if(dashboard.hidden||!file||file.size<1||file.size>65536){
      status.textContent="GEWEIGERD / Kies een JSON-beoordeling van maximaal 64 KiB. HOLD / DENY.";return;
    }
    try{
      const bytes=await file.arrayBuffer();
      if(generation!==version||dashboard.hidden)return;
      const obj=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
      if(!exact(obj,keys) || Object.entries(fixed).some(([k,v])=>obj[k]!==v) ||
        ![obj.decisionDossierSha256,obj.requestQueueSha256,obj.intakeSnapshotSha256].every(sha) ||
        !Number.isInteger(obj.intakeCount)||obj.intakeCount<0||obj.intakeCount>64 ||
        !Array.isArray(obj.assessedItems)||obj.assessedItems.length!==obj.intakeCount||
        !Array.isArray(obj.requirements)||obj.requirements.length!==5)throw Error();
      const counts=new Map(names.map(n=>[n,0]));
      const itemRows=document.createDocumentFragment();
      for(let i=0;i<obj.assessedItems.length;i++){
        const item=obj.assessedItems[i];
        if(!exact(item,itemKeys)||item.sequence!==i+1||
          !Number.isInteger(item.requestSequence)||item.requestSequence<1||
          !names.includes(item.requirementId)||!sha(item.evidenceSha256)||
          !kinds.has(item.evidenceKind)||!roles.has(item.submitterRoleClaim)||
          !Array.isArray(item.missingControls)||
          item.missingControls.length!==checks.length||
          item.missingControls.some((x,j)=>x!==checks[j])||
          item.assessment!=="UNVERIFIED_INTAKE_REFERENCE_ONLY"||item.gate!=="BLOCKED")throw Error();
        counts.set(item.requirementId,counts.get(item.requirementId)+1);
        const tr=document.createElement("tr");
        for(const value of [item.sequence,item.requirementId,item.evidenceKind,
          item.submitterRoleClaim,checks.length,"BLOCKED"]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }
        itemRows.append(tr);
      }
      const gateRows=document.createDocumentFragment();
      for(let i=0;i<5;i++){
        const gate=obj.requirements[i];
        if(!exact(gate,gateKeys)||gate.requirementId!==names[i]||
          gate.linkedIntakeCount!==counts.get(names[i])||
          gate.evidenceStatus!=="NOT_ESTABLISHED"||gate.gate!=="BLOCKED")throw Error();
        const tr=document.createElement("tr");
        for(const value of [gate.requirementId,gate.linkedIntakeCount,"NOT_ESTABLISHED","BLOCKED"]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }gateRows.append(tr);
      }
      if(generation!==version||dashboard.hidden)return;
      entries.replaceChildren(itemRows);blockers.replaceChildren(gateRows);
      status.textContent=`RAPPORTSTRUCTUUR HERKEND / ${obj.intakeCount} onbevestigde intake-items; per item zes open controles. Ingelezen Python-claim NIET onafhankelijk geverifieerd. HOLD / DENY.`;
    }catch(_){
      if(generation!==version||dashboard.hidden)return;
      clear("INTAKEBEOORDELING GEWEIGERD / Ongeldige structuur of inconsistenties. HOLD / DENY.");
    }
  });
})();
