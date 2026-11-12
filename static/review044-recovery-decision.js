"use strict";
// Untrusted local JSON viewer, never an identity or authorization verifier.
(() => {
  const $=id=>document.getElementById(id);
  const input=$("admin-pp-decision-file"),load=$("admin-pp-decision-load");
  const status=$("admin-pp-decision-status"),rows=$("admin-pp-decision-rows");
  const details=$("admin-pp-decision-details"),dashboard=$("admin-dashboard");
  if(![input,load,status,rows,details,dashboard].every(Boolean))return;
  const required=[
    ["SOURCE_ATTESTATION","Independent attestation of input origin"],
    ["CROSS_SOURCE_SUBJECT","Independent common-subject evidence"],
    ["OWNER_AUTHORITY","Authenticated owner authority review"],
    ["RUNTIME_EXECUTION","Independent execution provenance"],
    ["HUMAN_REVIEW","Recorded authorized human review"]
  ];
  const fixed={
    schema:"palaco.pp.recovery-002-decision-dossier.v0",
    reference:"PP-RECOVERY-002",openRequirementCount:5,
    crossSourceSubjectBinding:"NOT_ESTABLISHED",
    ownerAuthority:"NOT_ESTABLISHED",humanReview:"NOT_COMPLETED",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    independentVerification:"NOT_VERIFIED",reviewDecision:"HOLD",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED",
    nextPermittedStep:"MANUAL_SOURCE_AND_IDENTITY_REVIEW_ONLY"
  };
  const keys=[...Object.keys(fixed),"coordinationSha256","handoffSha256",
    "technicalReportSha256","ownerWorksheetSha256","localRegistrationStatus",
    "technicalEvidence","requirements","selfReportedMarkCount"];
  const markSet=new Set(["NOT_REVIEWED","REVIEW_REQUESTED","BLOCKER_REPORTED"]);
  const hash=v=>typeof v==="string"&&/^[a-f0-9]{64}$/.test(v);
  const exact=(o,fields)=>o&&typeof o==="object"&&!Array.isArray(o)
    &&Object.keys(o).length===fields.length&&fields.every(k=>Object.hasOwn(o,k));
  let revision=0;
  function reset(message="Geen beslisdossier geladen. HOLD / DENY."){
    revision++;rows.replaceChildren();details.replaceChildren();status.textContent=message;
  }
  input.addEventListener("change",()=>reset("Bestand gewijzigd; vorige beoordeling gewist. HOLD / DENY."));
  new MutationObserver(()=>{if(dashboard.hidden){reset();input.value="";}})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",()=>{reset();input.value="";});
  load.addEventListener("click",async()=>{
    reset("Beslisdossier wordt lokaal gelezen. HOLD / DENY.");
    const current=revision,file=input.files?.[0];
    if(dashboard.hidden||!file||!file.size||file.size>16384){
      status.textContent="GEWEIGERD / Kies een JSON-bestand van maximaal 16 KiB. HOLD / DENY.";return;
    }
    try{
      const buf=await file.arrayBuffer();
      if(revision!==current||dashboard.hidden)return;
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(buf));
      if(!exact(data,keys)||Object.entries(fixed).some(([k,v])=>data[k]!==v)
         ||![data.coordinationSha256,data.handoffSha256,data.technicalReportSha256,
              data.ownerWorksheetSha256].every(hash)
         ||!["ACTIVE","REVOKED"].includes(data.localRegistrationStatus)
         ||data.technicalEvidence!=="STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED"
         ||!Number.isInteger(data.selfReportedMarkCount)
         ||data.selfReportedMarkCount<0||data.selfReportedMarkCount>5
         ||!Array.isArray(data.requirements)||data.requirements.length!==5)throw Error();
      let marked=0;
      data.requirements.forEach((entry,i)=>{
        const [name,description]=required[i];
        if(!exact(entry,["requirementId","description","evidenceStatus","ownerMark","markProvenance","gate"])
          ||entry.requirementId!==name||entry.description!==description
          ||entry.evidenceStatus!=="NOT_ESTABLISHED"||entry.gate!=="BLOCKED"
          ||!markSet.has(entry.ownerMark)
          ||entry.markProvenance!==(entry.ownerMark==="NOT_REVIEWED"?"NO_OBSERVATION":"SELF_REPORTED")
             &&!(entry.ownerMark==="NOT_REVIEWED"&&entry.markProvenance==="SELF_REPORTED"))
          throw Error();
        if(entry.markProvenance==="SELF_REPORTED")marked++;
      });
      if(marked!==data.selfReportedMarkCount)throw Error();
      const draft=document.createDocumentFragment();
      for(const entry of data.requirements){
        const tr=document.createElement("tr");
        for(const value of [entry.requirementId,entry.evidenceStatus,entry.ownerMark,entry.gate]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }
        draft.append(tr);
      }
      const dl=document.createDocumentFragment();
      for(const [label,value] of [
        ["Hersteloverdracht SHA-256",data.handoffSha256],
        ["Technisch rapport SHA-256",data.technicalReportSha256],
        ["Eigenaarwerkblad SHA-256",data.ownerWorksheetSha256],
        ["Bronkoppeling",data.crossSourceSubjectBinding],
        ["Menselijke review",data.humanReview],
        ["PALACO ONE-overdracht",data.palacoOneHandoff],
        ["Toegang / uitgifte","DENY / NOT_AUTHORIZED"],
        ["Vervolg",data.nextPermittedStep]
      ]){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=label;dd.textContent=value;dl.append(dt,dd);
      }
      if(revision!==current||dashboard.hidden)return;
      rows.replaceChildren(draft);details.replaceChildren(dl);
      status.textContent="BESTANDSSTRUCTUUR HERKEND / Vijf bewijsvereisten blijven BLOCKED. Ingelezen claims zijn niet opnieuw in Python geverifieerd. HOLD / DENY.";
    }catch(_){
      if(revision!==current||dashboard.hidden)return;
      reset("BESLISDOSSIER GEWEIGERD / Ongeldige of tegenstrijdige gegevens. HOLD / DENY.");
    }
  });
})();
