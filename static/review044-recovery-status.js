"use strict";
// Read-only presentation of an untrusted local status-report JSON.
// It cannot verify Python execution, independent evidence, or reviewer authority.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-status-report-file");
  const button=$("admin-status-report-load");
  const status=$("admin-status-report-status");
  const summary=$("admin-status-report-summary");
  const gates=$("admin-status-report-gates");
  const checks=$("admin-status-report-checks");
  const next=$("admin-status-report-next");
  const dashboard=$("admin-dashboard");
  if (![file,button,status,summary,gates,checks,next,dashboard].every(Boolean))return;
  const req=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const checkIDs=["ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED","SOURCE_PROVENANCE_NOT_ATTESTED",
    "SUBMITTER_IDENTITY_NOT_AUTHENTICATED","REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "SUBJECT_BINDING_NOT_ESTABLISHED","INDEPENDENT_REVIEW_NOT_COMPLETED"];
  const dependencies=[[],[1],[],[],[2,3],[1,2,3,4,5]];
  const gateDeps=[[1,2],[1,2,3,5],[3,4,5],[1,2,6],[1,2,3,4,5,6]];
  const actionIDs=["PRESERVE_ORIGINALS","RECHECK_EVIDENCE_BYTES",
    "ATTEST_SOURCE_ORIGIN","AUTHENTICATE_SUBMITTER","AUTHENTICATE_REVIEWER",
    "ESTABLISH_SUBJECT_BINDING","RECORD_HUMAN_REVIEW","REASSESS_MANUAL_HOLD"];
  const fixed={
    schema:"palaco.pp.recovery-002-status-report.v0",
    reference:"PP-RECOVERY-002",
    sourceScope:"FIVE_ORIGINAL_LOCAL_FILES_STRICT_INTERNAL_CONSISTENCY",
    independentVerification:"NOT_VERIFIED",sourceAuthenticity:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",subjectBinding:"NOT_ESTABLISHED",
    historicalImmutability:"NOT_ESTABLISHED",humanReview:"NOT_COMPLETED",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    reviewDecision:"HOLD",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const top=[...Object.keys(fixed),"sourceFingerprints","cockpitCanonicalSha256",
    "counts","evidenceChecks","decisionGates","nextPermittedActions"];
  const sourceFields=["decisionDossierSha256","reviewQueueSha256",
    "reviewIntakeSha256","verificationPlanSha256","observationRegisterSha256"];
  const countFields=["reviewRequests","intakeReferences","plannedChecks",
    "unsignedObservations","reportedBlockers"];
  const valid=(v,fields)=>v&&typeof v==="object"&&!Array.isArray(v)&&
    Object.keys(v).length===fields.length&&fields.every(k=>Object.hasOwn(v,k));
  const sha=s=>typeof s==="string"&&/^[0-9a-f]{64}$/.test(s);
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
  let generation=0;
  function clear(message="Geen herstelstatusrapport geladen. HOLD / DENY."){
    generation++;summary.replaceChildren();gates.replaceChildren();
    checks.replaceChildren();next.replaceChildren();status.textContent=message;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd; rapportweergave gewist. HOLD / DENY."));
  new MutationObserver(()=>{if(dashboard.hidden){clear();file.value="";}})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",()=>{clear();file.value="";});
  button.addEventListener("click",async()=>{
    clear("Lokaal statusrapport lezen. HOLD / DENY.");
    const current=generation,selected=file.files?.[0];
    if(dashboard.hidden||!selected||selected.size<1||selected.size>32768){
      status.textContent="GEWEIGERD / Selecteer JSON van maximaal 32 KiB. HOLD / DENY.";return;
    }
    try{
      const bytes=await selected.arrayBuffer();
      if(current!==generation||dashboard.hidden)return;
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
      if(!valid(data,top)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
         !valid(data.sourceFingerprints,sourceFields)||
         !sourceFields.every(k=>sha(data.sourceFingerprints[k]))||
         !sha(data.cockpitCanonicalSha256)||
         !valid(data.counts,countFields)||countFields.some(k=>!Number.isInteger(data.counts[k])||data.counts[k]<0)||
         data.counts.reviewRequests>128||data.counts.intakeReferences>64||
         data.counts.plannedChecks!==data.counts.intakeReferences*6||
         data.counts.unsignedObservations>128||
         data.counts.reportedBlockers>data.counts.unsignedObservations||
         !Array.isArray(data.evidenceChecks)||data.evidenceChecks.length!==6||
         !Array.isArray(data.decisionGates)||data.decisionGates.length!==5||
         !Array.isArray(data.nextPermittedActions)||data.nextPermittedActions.length!==8)throw Error();
      const cr=document.createDocumentFragment();
      for(let i=0;i<6;i++){
        const c=data.evidenceChecks[i];
        if(!valid(c,["order","checkId","dependsOn","status","verification"])||
          c.order!==i+1||c.checkId!==checkIDs[i]||!same(c.dependsOn,dependencies[i])||
          c.status!=="NOT_STARTED"||c.verification!=="NOT_VERIFIED")throw Error();
        const tr=document.createElement("tr");
        for(const value of [c.order,c.checkId,c.dependsOn.length?c.dependsOn.join(", "):"Geen","NOT_STARTED"]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }cr.append(tr);
      }
      const gr=document.createDocumentFragment();
      for(let i=0;i<5;i++){
        const g=data.decisionGates[i];
        if(!valid(g,["requirementId","prerequisiteCheckOrders","evidenceStatus","gate"])||
          g.requirementId!==req[i]||!same(g.prerequisiteCheckOrders,gateDeps[i])||
          g.evidenceStatus!=="NOT_ESTABLISHED"||g.gate!=="BLOCKED")throw Error();
        const tr=document.createElement("tr");
        for(const value of [g.requirementId,g.prerequisiteCheckOrders.join(", "),"BLOCKED"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }gr.append(tr);
      }
      const nr=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const a=data.nextPermittedActions[i];
        if(!valid(a,["priority","actionId","description","execution","authorizationEffect"])||
          a.priority!==i+1||a.actionId!==actionIDs[i]||
          typeof a.description!=="string"||!a.description.trim()||
          a.description.length>300||
          a.execution!=="MANUAL_FUTURE_ACTION_ONLY"||a.authorizationEffect!=="NONE")throw Error();
        const tr=document.createElement("tr");
        for(const value of [a.priority,a.actionId,a.description]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }nr.append(tr);
      }
      const info=document.createDocumentFragment();
      for(const [name,value] of [
        ["Reviewverzoeken (geclaimd)",data.counts.reviewRequests],
        ["Bewijs-intakes (geclaimd)",data.counts.intakeReferences],
        ["Geplande controles (geclaimd)",data.counts.plannedChecks],
        ["Ongetekende observaties (geclaimd)",data.counts.unsignedObservations],
        ["Gemelde blokkades (geclaimd)",data.counts.reportedBlockers],
        ["Onafhankelijke verificatie",data.independentVerification],
        ["Reviewerbevoegdheid",data.reviewerAuthority],
        ["PALACO ONE-overdracht",data.palacoOneHandoff],
        ["Besluit / toegang / uitgifte","HOLD / DENY / NOT_AUTHORIZED"]]){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=name;dd.textContent=String(value);info.append(dt,dd);
      }
      if(current!==generation||dashboard.hidden)return;
      summary.replaceChildren(info);gates.replaceChildren(gr);
      checks.replaceChildren(cr);next.replaceChildren(nr);
      status.textContent="STATUSSTRUCTUUR HERKEND / Ongetekend rapport: geen Python-hercontrole of onafhankelijke identiteitstoets. Vijf poorten BLOCKED; HOLD / DENY.";
    }catch(_){
      if(current!==generation||dashboard.hidden)return;
      clear("STATUSRAPPORT GEWEIGERD / Ongeldige velden of tegenstrijdige statussen. HOLD / DENY.");
    }
  });
})();
