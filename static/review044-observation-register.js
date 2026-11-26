"use strict";
// Local read-only rendering of untrusted self-reported observations.
// Python revalidation of original source files remains mandatory.
// This browser does not certify a hash chain, timestamps, people or authority.
(() => {
  const $ = id => document.getElementById(id);
  const planInput = $("admin-observations-plan-file");
  const registerInput = $("admin-observations-register-file");
  const open = $("admin-observations-load");
  const status = $("admin-observations-status");
  const summary = $("admin-observations-summary");
  const rows = $("admin-observations-rows");
  const dashboard = $("admin-dashboard");
  if (![planInput,registerInput,open,status,summary,rows,dashboard].every(Boolean)) return;

  const marks = new Set([
    "OBSERVATION_REPORTED","BLOCKER_REPORTED","RECHECK_REQUESTED"
  ]);
  const checks = [
    "ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED",
    "SOURCE_PROVENANCE_NOT_ATTESTED",
    "SUBMITTER_IDENTITY_NOT_AUTHENTICATED",
    "REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "SUBJECT_BINDING_NOT_ESTABLISHED",
    "INDEPENDENT_REVIEW_NOT_COMPLETED"
  ];
  const topFixed = {
    schema:"palaco.pp.recovery-002-observation-register.v0",
    reference:"PP-RECOVERY-002",
    provenance:"UNSIGNED_OWNER_SELF_REPORT",
    independentVerification:"NOT_VERIFIED",
    reviewerAuthority:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",
    palacoOneHandoff:"BLOCKED",
    authorization:"HOLD",
    accessDecision:"DENY",
    issuance:"NOT_AUTHORIZED"
  };
  const eventFixed = {
    evidenceKind:"SELF_REPORTED_NOT_INDEPENDENTLY_VERIFIED",
    checkStatus:"NOT_STARTED",verification:"NOT_VERIFIED",
    gate:"BLOCKED",authorization:"HOLD",accessDecision:"DENY"
  };
  const topFields = [...Object.keys(topFixed),"verificationPlanSha256","events"];
  const eventFields = [...Object.keys(eventFixed),
    "sequence","intakeSequence","checkOrder","checkId","mark",
    "previousEventSha256","eventSha256"];
  const hex = s => typeof s==="string" && /^[0-9a-f]{64}$/.test(s);
  const exact = (v,fields) => v && typeof v==="object" &&
    !Array.isArray(v) && Object.keys(v).length===fields.length &&
    fields.every(key => Object.hasOwn(v,key));
  let epoch=0;
  const reset = (message="Geen voortgangsregister geladen. HOLD / DENY.") => {
    epoch++;rows.replaceChildren();summary.replaceChildren();status.textContent=message;
  };
  for (const input of [planInput,registerInput])
    input.addEventListener("change",()=>reset("Bestand gewijzigd; eerdere weergave ongeldig. HOLD / DENY."));
  new MutationObserver(() => {
    if(dashboard.hidden){
      reset("Beheerderssessie gesloten; lokale weergave gewist. HOLD / DENY.");
      planInput.value="";registerInput.value="";
    }
  }).observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",()=>{
    reset("Afmelding aangevraagd; lokale weergave gewist. HOLD / DENY.");
    planInput.value="";registerInput.value="";
  });
  open.addEventListener("click",async()=>{
    reset("Verificatieplan en observaties worden lokaal gelezen. HOLD / DENY.");
    const current=epoch, planFile=planInput.files?.[0], regFile=registerInput.files?.[0];
    if (dashboard.hidden || !planFile || !regFile ||
        planFile.size<1 || regFile.size<1 ||
        planFile.size>131072 || regFile.size>131072) {
      status.textContent="GEWEIGERD / Beide bestanden moeten 1–128 KiB zijn. HOLD / DENY.";
      return;
    }
    try {
      const [planBytes,registerBytes]=await Promise.all([planFile.arrayBuffer(),regFile.arrayBuffer()]);
      if(current!==epoch || dashboard.hidden)return;
      const decoder=new TextDecoder("utf-8",{fatal:true});
      const plan=JSON.parse(decoder.decode(planBytes));
      const register=JSON.parse(decoder.decode(registerBytes));
      if(plan?.schema!=="palaco.pp.recovery-002-verification-plan.v0" ||
         plan.reference!=="PP-RECOVERY-002" ||
         plan.workflowStatus!=="PREPARED_NOT_EXECUTED" ||
         plan.authorization!=="HOLD" || plan.accessDecision!=="DENY" ||
         plan.palacoOneHandoff!=="BLOCKED" ||
         !Number.isInteger(plan.intakeCount) || plan.intakeCount<0 ||
         plan.intakeCount>64 || !Array.isArray(plan.workItems) ||
         plan.workItems.length!==plan.intakeCount ||
         plan.checkCount!==plan.intakeCount*6 ||
         !Array.isArray(plan.decisionGates) || plan.decisionGates.length!==5)throw Error();
      const work=new Map();
      for(let i=0;i<plan.workItems.length;i++){
        const item=plan.workItems[i];
        if(!item || item.intakeSequence!==i+1 ||
           !Array.isArray(item.checks) || item.checks.length!==6 ||
           item.gate!=="BLOCKED")throw Error();
        for(let j=0;j<6;j++){
          const check=item.checks[j];
          if(!check || check.checkOrder!==j+1 ||
             check.checkId!==checks[j] || check.status!=="NOT_STARTED" ||
             check.verification!=="NOT_VERIFIED" ||
             check.reviewerAuthority!=="NOT_ESTABLISHED")throw Error();
        }
        work.set(item.intakeSequence,item);
      }
      const bytesDigest=new Uint8Array(await crypto.subtle.digest("SHA-256",planBytes));
      if(current!==epoch || dashboard.hidden)return;
      const planSha=[...bytesDigest].map(b=>b.toString(16).padStart(2,"0")).join("");
      if(!exact(register,topFields) ||
         Object.entries(topFixed).some(([key,value])=>register[key]!==value) ||
         !hex(register.verificationPlanSha256) ||
         register.verificationPlanSha256!==planSha ||
         !Array.isArray(register.events) || register.events.length>128)throw Error();
      const fragment=document.createDocumentFragment();
      let previous=null;
      let obs=0,blocked=0,rechecks=0;
      for(let i=0;i<register.events.length;i++){
        const entry=register.events[i];
        if(!exact(entry,eventFields) ||
           Object.entries(eventFixed).some(([key,value])=>entry[key]!==value) ||
           !Number.isInteger(entry.sequence) || entry.sequence!==i+1 ||
           !Number.isInteger(entry.intakeSequence) ||
           !work.has(entry.intakeSequence) ||
           !Number.isInteger(entry.checkOrder) || entry.checkOrder<1 || entry.checkOrder>6 ||
           entry.checkId!==work.get(entry.intakeSequence).checks[entry.checkOrder-1].checkId ||
           !marks.has(entry.mark) || !hex(entry.eventSha256) ||
           entry.previousEventSha256!==previous)throw Error();
        previous=entry.eventSha256;
        if(entry.mark==="OBSERVATION_REPORTED")obs++;
        if(entry.mark==="BLOCKER_REPORTED")blocked++;
        if(entry.mark==="RECHECK_REQUESTED")rechecks++;
        const tr=document.createElement("tr");
        for(const value of [
          entry.sequence,entry.intakeSequence,entry.checkOrder,entry.checkId,
          entry.mark,entry.eventSha256.slice(0,12)+"…","NOT_STARTED / BLOCKED"
        ]){
          const cell=document.createElement("td");
          cell.textContent=String(value);tr.append(cell);
        }
        fragment.append(tr);
      }
      const info=document.createDocumentFragment();
      for(const [label,value] of [
        ["Verificatieplan SHA-256 (lokale bytevergelijking)",planSha],
        ["Aantal waarnemingsclaims",register.events.length],
        ["Waarnemingen gemeld",obs],["Blokkades gemeld",blocked],
        ["Hercontroles gevraagd",rechecks],
        ["Volledige gebeurtenisketen","NIET ONAFHANKELIJK GEVALIDEERD IN BROWSER"],
        ["Reviewerbevoegdheid","NOT_ESTABLISHED"],
        ["PALACO ONE-overdracht","BLOCKED"],
        ["Autorisatie / toegang","HOLD / DENY"]
      ]){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=label;dd.textContent=String(value);
        info.append(dt,dd);
      }
      if(current!==epoch || dashboard.hidden)return;
      rows.replaceChildren(fragment);summary.replaceChildren(info);
      status.textContent="LOKALE INDICATIE / Register gekoppeld aan exacte planbytes. Eventhashes, identiteit en onafhankelijke verificatie zijn niet bevestigd. NOT_STARTED / HOLD / DENY.";
    }catch(_){
      if(current!==epoch || dashboard.hidden)return;
      reset("OBSERVATIEREGISTER GEWEIGERD / Ongeldige structuur, plandigest of verwijzing. HOLD / DENY.");
    }
  });
})();
