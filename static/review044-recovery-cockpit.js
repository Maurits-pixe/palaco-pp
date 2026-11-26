"use strict";
// Read-only PP recovery cockpit. Six local files, no upload or authorization.
// Matching bytes to an imported, unsigned Python report is not attestation.
(() => {
  const $=id=>document.getElementById(id);
  const dashboard=$("admin-dashboard"),load=$("admin-recovery-cockpit-load");
  const status=$("admin-recovery-cockpit-status");
  const overview=$("admin-recovery-cockpit-overview");
  const sourcesBody=$("admin-recovery-cockpit-sources");
  const gatesBody=$("admin-recovery-cockpit-gates");
  const files=[
    ["dossier","Beslisdossier",16384,"decisionDossierSha256"],
    ["queue","Review-queue",131072,"reviewQueueSha256"],
    ["intake","Bewijs-intake",16384,"reviewIntakeSha256"],
    ["plan","Verificatieplan",131072,"verificationPlanSha256"],
    ["observations","Observaties",131072,"observationRegisterSha256"],
    ["report","Cockpitrapport",16384,null]
  ].map(([id,label,limit,hashField])=>({
    input:$("admin-recovery-cockpit-"+id),label,limit,hashField
  }));
  if(![dashboard,load,status,overview,sourcesBody,gatesBody].every(Boolean) ||
     files.some(f=>!f.input))return;
  const expectedGates=[
    "SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-cockpit.v0",
    reference:"PP-RECOVERY-002",
    contractBinding:"STRICT_INTERNAL_FIVE_FILE_CONSISTENCY_ONLY",
    independentSourceAttestation:"ABSENT",
    reviewerAuthority:"NOT_ESTABLISHED",subjectBinding:"NOT_ESTABLISHED",
    historicalImmutability:"NOT_ESTABLISHED",humanReview:"NOT_COMPLETED",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    independentVerification:"NOT_VERIFIED",reviewDecision:"HOLD",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const keys=[...Object.keys(fixed),"sources","requestCount","intakeCount",
    "plannedCheckCount","observationCount","observationKinds","decisionGates"];
  const exact=(obj,fields)=>obj&&typeof obj==="object"&&!Array.isArray(obj)
    &&Object.keys(obj).length===fields.length
    &&fields.every(key=>Object.hasOwn(obj,key));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  const int=(x,limit)=>Number.isInteger(x)&&x>=0&&x<=limit;
  let generation=0;
  function clear(message="Geen herstelcockpit geladen. HOLD / DENY."){
    generation++;overview.replaceChildren();sourcesBody.replaceChildren();
    gatesBody.replaceChildren();status.textContent=message;
  }
  for(const file of files)
    file.input.addEventListener("change",()=>clear("Bestanden gewijzigd; overzicht gewist. HOLD / DENY."));
  function logout(){
    clear("Beheerweergave gewist. HOLD / DENY.");
    for(const file of files)file.input.value="";
  }
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);

  load.addEventListener("click",async()=>{
    clear("Bronbestanden worden uitsluitend lokaal vergeleken. HOLD / DENY.");
    const current=generation;
    if(dashboard.hidden||files.some(f=>{
      const file=f.input.files?.[0];
      return !file||file.size<1||file.size>f.limit;
    })){
      status.textContent="GEWEIGERD / Selecteer alle zes bestanden binnen hun opgegeven maximum. HOLD / DENY.";
      return;
    }
    try{
      const bytes=await Promise.all(files.map(f=>f.input.files[0].arrayBuffer()));
      if(current!==generation||dashboard.hidden)return;
      const decoder=new TextDecoder("utf-8",{fatal:true});
      const doc=JSON.parse(decoder.decode(bytes[5]));
      if(!exact(doc,keys)||Object.entries(fixed).some(([k,v])=>doc[k]!==v)||
         !exact(doc.sources,files.slice(0,5).map(f=>f.hashField))||
         files.slice(0,5).some(f=>!sha(doc.sources[f.hashField]))||
         !int(doc.requestCount,128)||!int(doc.intakeCount,64)||
         !int(doc.plannedCheckCount,384)||doc.plannedCheckCount!==doc.intakeCount*6||
         !int(doc.observationCount,128)||
         !exact(doc.observationKinds,["OBSERVATION_REPORTED","BLOCKER_REPORTED","RECHECK_REQUESTED"])||
         Object.values(doc.observationKinds).some(v=>!int(v,128))||
         Object.values(doc.observationKinds).reduce((a,b)=>a+b,0)!==doc.observationCount||
         !Array.isArray(doc.decisionGates)||doc.decisionGates.length!==5)throw Error();
      doc.decisionGates.forEach((g,i)=>{
        if(!exact(g,["requirementId","gate","verification"])||
           g.requirementId!==expectedGates[i]||g.gate!=="BLOCKED"||
           g.verification!=="NOT_VERIFIED")throw Error();
      });
      const digests=await Promise.all(bytes.slice(0,5).map(b=>crypto.subtle.digest("SHA-256",b)));
      if(current!==generation||dashboard.hidden)return;
      const bytesToHex=b=>Array.from(new Uint8Array(b),v=>v.toString(16).padStart(2,"0")).join("");
      const hashes=digests.map(bytesToHex);
      if(files.slice(0,5).some((f,i)=>hashes[i]!==doc.sources[f.hashField]))throw Error();
      // The imported report's counts are claims; compare basic visible shape
      // without suggesting that browser JSON parsing validates the Python contracts.
      const shape=[
        ["palaco.pp.recovery-002-decision-dossier.v0","decision"],
        ["palaco.pp.recovery-002-human-review-queue.v0","queue"],
        ["palaco.pp.recovery-002-review-intake.v0","intake"],
        ["palaco.pp.recovery-002-verification-plan.v0","plan"],
        ["palaco.pp.recovery-002-observation-register.v0","observations"]
      ];
      const originals=bytes.slice(0,5).map(b=>JSON.parse(decoder.decode(b)));
      if(originals.some((v,i)=>v?.schema!==shape[i][0]||v.reference!=="PP-RECOVERY-002"))throw Error();
      const [d,q,t,p,o]=originals;
      if(d.authorization!=="HOLD"||d.accessDecision!=="DENY"||
         q.authorization!=="HOLD"||q.accessDecision!=="DENY"||
         t.authorization!=="HOLD"||t.accessDecision!=="DENY"||
         p.authorization!=="HOLD"||p.palacoOneHandoff!=="BLOCKED"||
         o.authorization!=="HOLD"||o.accessDecision!=="DENY"||
         !Array.isArray(q.events)||q.events.length!==doc.requestCount||
         !Array.isArray(t.items)||t.items.length!==doc.intakeCount||
         p.intakeCount!==doc.intakeCount||p.checkCount!==doc.plannedCheckCount||
         !Array.isArray(o.events)||o.events.length!==doc.observationCount)throw Error();
      const sourceRows=document.createDocumentFragment();
      files.slice(0,5).forEach((f,i)=>{
        const tr=document.createElement("tr");
        for(const val of [f.label,hashes[i].slice(0,20)+"…","LOKALE BYTE-HASH MATCH / INHOUD ONVERTROUWD"]){
          const td=document.createElement("td");td.textContent=val;tr.append(td);
        }sourceRows.append(tr);
      });
      const gates=document.createDocumentFragment();
      for(const g of doc.decisionGates){
        const tr=document.createElement("tr");
        for(const v of [g.requirementId,g.verification,g.gate]){
          const td=document.createElement("td");td.textContent=v;tr.append(td);
        }gates.append(tr);
      }
      const overviewContent=document.createDocumentFragment();
      for(const [label,value] of [
        ["Reviewverzoeken (geclaimd)",doc.requestCount],
        ["Intake-items (geclaimd)",doc.intakeCount],
        ["Geplande controles (geclaimd)",doc.plannedCheckCount],
        ["Zelfrapportages (geclaimd)",doc.observationCount],
        ["Blokkades gemeld (geclaimd)",doc.observationKinds.BLOCKER_REPORTED],
        ["Bronauthenticiteit",doc.independentSourceAttestation],
        ["Reviewerbevoegdheid",doc.reviewerAuthority],
        ["PALACO ONE-overdracht",doc.palacoOneHandoff],
        ["Definitieve status","NOT_VERIFIED / HOLD / DENY / NOT_AUTHORIZED"]
      ]){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=label;dd.textContent=String(value);
        overviewContent.append(dt,dd);
      }
      if(current!==generation||dashboard.hidden)return;
      overview.replaceChildren(overviewContent);sourcesBody.replaceChildren(sourceRows);
      gatesBody.replaceChildren(gates);
      status.textContent="LOKAAL / Vijf bronhashes komen overeen met het ongetekende cockpitrapport. Python-contracten, herkomst, identiteit en gebeurtenisketens NIET onafhankelijk herbeoordeeld. HOLD / DENY.";
    }catch(_){
      if(current!==generation||dashboard.hidden)return;
      clear("HERSTELCOCKPIT GEWEIGERD / Bestanden, hashes, aantallen of statussen komen niet overeen. HOLD / DENY.");
    }
  });
})();
