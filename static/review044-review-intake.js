"use strict";
// Review intake is imported, UNSIGNED, and never proof of a reviewer identity.
// Read-only File API; no fetch, storage, crypto attestation, or account mutation.
(() => {
  const $ = id => document.getElementById(id);
  const dossier = $("admin-intake-dossier");
  const queue = $("admin-intake-queue");
  const intake = $("admin-intake-file");
  const open = $("admin-intake-view");
  const result = $("admin-intake-status");
  const rows = $("admin-intake-rows");
  const gates = $("admin-intake-gates");
  const summary = $("admin-intake-summary");
  const dashboard = $("admin-dashboard");
  if (![dossier,queue,intake,open,result,rows,gates,summary,dashboard].every(Boolean)) return;
  const requirements = [
    "SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"
  ];
  const kinds = new Set(["DOCUMENT","SCREENSHOT","LOG_EXCERPT","OTHER_UNTRUSTED"]);
  const roles = new Set(["OWNER_CLAIMED","REVIEWER_CLAIMED","SOURCE_CLAIMED"]);
  const actions = new Set(["REVIEW_REQUESTED","EVIDENCE_REQUESTED","BLOCKER_REPORTED"]);
  const fixed = {
    schema:"palaco.pp.recovery-002-review-intake.v0",
    reference:"PP-RECOVERY-002",verification:"NOT_VERIFIED",
    sourceAuthenticity:"NOT_ESTABLISHED",
    reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",subjectBinding:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",palacoOneHandoff:"BLOCKED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const itemFixed = {
    provenance:"UNSIGNED_LOCAL_UNATTESTED_INTAKE",verification:"NOT_VERIFIED",
    gate:"BLOCKED",authorization:"HOLD",accessDecision:"DENY",
    reviewerAuthority:"NOT_ESTABLISHED",sourceAuthenticity:"NOT_ESTABLISHED"
  };
  const fields = [...Object.keys(fixed),"decisionDossierSha256","requestQueueSha256","items"];
  const itemFields = [...Object.keys(itemFixed),
    "sequence","requestSequence","requestEventSha256","requirementId",
    "evidenceSha256","evidenceKind","submitterRoleClaim",
    "previousItemSha256","itemSha256"];
  const exact = (obj,keys) => obj !== null && typeof obj === "object" &&
    !Array.isArray(obj) && Object.keys(obj).length === keys.length &&
    keys.every(key => Object.hasOwn(obj,key));
  const hash = str => typeof str === "string" && /^[0-9a-f]{64}$/.test(str);
  let version=0;
  const clear = (message="Geen review-intake geladen. HOLD / DENY.") => {
    ++version; rows.replaceChildren();gates.replaceChildren();
    summary.replaceChildren();result.textContent=message;
  };
  for(const f of [dossier,queue,intake])
    f.addEventListener("change",() => clear("Bestand gewijzigd; eerdere beoordeling ongeldig. HOLD / DENY."));
  new MutationObserver(() => {
    if(dashboard.hidden){clear();for(const f of [dossier,queue,intake])f.value="";}
  }).observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",() => {
    clear();for(const f of [dossier,queue,intake])f.value="";
  });

  open.addEventListener("click",async() => {
    clear("Bestanden worden alleen lokaal gelezen. HOLD / DENY.");
    const generation=version,files=[dossier.files?.[0],queue.files?.[0],intake.files?.[0]];
    if(dashboard.hidden || files.some((f,i)=>!f||f.size<1||
       f.size>[16384,131072,16384][i])){
      result.textContent="GEWEIGERD / Beslisdossier ≤16 KiB, queue ≤128 KiB, intake ≤16 KiB. HOLD / DENY.";
      return;
    }
    try{
      const buffers=await Promise.all(files.map(f=>f.arrayBuffer()));
      if(version!==generation||dashboard.hidden)return;
      const decode=new TextDecoder("utf-8",{fatal:true});
      const [d,q,t]=buffers.map(b=>JSON.parse(decode.decode(b)));
      if(d?.schema!=="palaco.pp.recovery-002-decision-dossier.v0" ||
        d.reference!=="PP-RECOVERY-002" || d.authorization!=="HOLD" ||
        d.accessDecision!=="DENY" || d.palacoOneHandoff!=="BLOCKED" ||
        d.openRequirementCount!==5 || !Array.isArray(d.requirements) ||
        d.requirements.length!==5)throw Error();
      if(q?.schema!=="palaco.pp.recovery-002-human-review-queue.v0" ||
        q.reference!=="PP-RECOVERY-002" || q.authorization!=="HOLD" ||
        q.accessDecision!=="DENY" || q.palacoOneHandoff!=="BLOCKED" ||
        !Array.isArray(q.events)||q.events.length>128 ||
        !hash(q.decisionDossierSha256))throw Error();
      if(!exact(t,fields)||Object.entries(fixed).some(([k,v])=>t[k]!==v)||
        !hash(t.decisionDossierSha256)||!hash(t.requestQueueSha256)||
        t.decisionDossierSha256!==q.decisionDossierSha256 ||
        !Array.isArray(t.items)||t.items.length>64)throw Error();
      const requests=new Map();
      for(let i=0;i<q.events.length;i++){
        const e=q.events[i];
        if(!e||e.sequence!==i+1||!hash(e.eventSha256)||
          !requirements.includes(e.requirementId)||!actions.has(e.action)||
          e.gate!=="BLOCKED"||e.authorization!=="HOLD"||
          e.accessDecision!=="DENY")throw Error();
        requests.set(e.sequence,e);
      }
      const evidenceRows=document.createDocumentFragment();
      let previous=null;
      const duplicates=new Set();
      for(let i=0;i<t.items.length;i++){
        const item=t.items[i];
        if(!exact(item,itemFields) ||
          Object.entries(itemFixed).some(([k,v])=>item[k]!==v) ||
          item.sequence!==i+1||!Number.isInteger(item.requestSequence)||
          !requests.has(item.requestSequence)||
          item.requestEventSha256!==requests.get(item.requestSequence).eventSha256||
          item.requirementId!==requests.get(item.requestSequence).requirementId||
          !hash(item.evidenceSha256)||!hash(item.itemSha256)||
          !kinds.has(item.evidenceKind)||!roles.has(item.submitterRoleClaim)||
          item.previousItemSha256!==previous)throw Error();
        const duplicate=item.requestSequence+":"+item.evidenceSha256;
        if(duplicates.has(duplicate))throw Error();
        duplicates.add(duplicate);previous=item.itemSha256;
        const tr=document.createElement("tr");
        for(const text of [
          item.sequence,item.requestSequence,item.requirementId,item.evidenceKind,
          item.evidenceSha256.slice(0,16)+"…",item.submitterRoleClaim,"NOT_VERIFIED / BLOCKED"
        ]){
          const td=document.createElement("td");td.textContent=String(text);tr.append(td);
        }
        evidenceRows.append(tr);
      }
      const gateRows=document.createDocumentFragment();
      for(let i=0;i<requirements.length;i++){
        const item=d.requirements[i],name=requirements[i];
        if(!item||item.requirementId!==name||
          item.evidenceStatus!=="NOT_ESTABLISHED"||item.gate!=="BLOCKED")throw Error();
        const tr=document.createElement("tr");
        for(const value of [name,"NOT_ESTABLISHED","BLOCKED"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }gateRows.append(tr);
      }
      const facts=[
        ["Intake-items",t.items.length],
        ["Ingelezen reviewverzoeken",q.events.length],
        ["Dossierbinding","NIET CRYPTOGRAFISCH GEVERIFIEERD IN BROWSER"],
        ["Queue-binding","NIET CRYPTOGRAFISCH GEVERIFIEERD IN BROWSER"],
        ["Revieweridentiteit","NOT_ESTABLISHED"],
        ["Reviewerbevoegdheid","NOT_ESTABLISHED"],
        ["Bronauthenticiteit","NOT_ESTABLISHED"],
        ["PALACO ONE-overdracht","BLOCKED"],
        ["Verificatie / rechten","NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED"]
      ];
      const dl=document.createDocumentFragment();
      for(const [label,value] of facts){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=label;dd.textContent=String(value);dl.append(dt,dd);
      }
      if(version!==generation||dashboard.hidden)return;
      rows.replaceChildren(evidenceRows);gates.replaceChildren(gateRows);
      summary.replaceChildren(dl);
      result.textContent="LOKALE STRUCTUURINDICATIE / Ingelezen intakeclaims herkenbaar, maar Python-ketenvalidatie, revieweridentiteit en bronherkomst NIET vastgesteld. HOLD / DENY.";
    }catch(_){
      if(version!==generation||dashboard.hidden)return;
      clear("INTAKE GEWEIGERD / Onjuiste structuur, koppeling of status. HOLD / DENY.");
    }
  });
})();
