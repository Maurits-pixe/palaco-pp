"use strict";
// Display an untrusted PP-RECOVERY-002 coordination draft; never verify identity.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-pp-recovery002-file"),button=$("admin-pp-recovery002-view");
  const status=$("admin-pp-recovery002-status"),details=$("admin-pp-recovery002-details");
  const dashboard=$("admin-dashboard");
  if(!file||!button||!status||!details||!dashboard)return;
  const fixed={
    schema:"palaco.pp.recovery-002-coordination.v0",
    reference:"PP-RECOVERY-002",
    handoffStructure:"STRUCTURE_ACCEPTED_UNTRUSTED",
    review044Evidence:"STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED",
    reportedScenarios:24,
    crossSourceSubjectBinding:"NOT_ESTABLISHED",
    ownerAuthority:"NOT_ESTABLISHED",
    palacoOneSession:"NOT_CREATED",
    externalAttestation:"ABSENT",
    sourceTrust:"UNSIGNED_UNATTESTED_LOCAL_INPUTS",
    independentVerification:"NOT_VERIFIED",
    reviewDecision:"HOLD",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED",
    nextPermittedStep:"MANUAL_SOURCE_AND_IDENTITY_REVIEW_ONLY"
  };
  const additional=["handoffSha256","technicalReportSha256",
    "ownerWorksheetSha256","localRegistrationStatus","claimedTechnicalMismatches",
    "ownerMarkedCount","ownerDiscrepancyCount"];
  const hash=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  const count=x=>Number.isInteger(x)&&x>=0&&x<=24;
  let generation=0;
  function clear(message="Geen hersteloverzicht geladen. HOLD / DENY."){
    generation++;details.replaceChildren();details.hidden=true;status.textContent=message;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd; hersteloverzicht gewist. HOLD / DENY."));
  new MutationObserver(()=>{if(dashboard.hidden){clear();file.value="";}})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",()=>{clear();file.value="";});
  button.addEventListener("click",async()=>{
    clear("Lokaal hersteloverzicht lezen. HOLD / DENY.");
    const revision=generation,selected=file.files?.[0];
    if(dashboard.hidden||!selected||!selected.size||selected.size>16384){
      status.textContent="GEWEIGERD / Kies JSON van maximaal 16 KiB. HOLD / DENY.";return;
    }
    try{
      const bytes=await selected.arrayBuffer();
      if(revision!==generation||dashboard.hidden)return;
      const obj=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
      const fields=[...Object.keys(fixed),...additional];
      if(!obj||typeof obj!=="object"||Array.isArray(obj)
        ||Object.keys(obj).length!==fields.length
        ||!fields.every(k=>Object.hasOwn(obj,k))
        ||Object.entries(fixed).some(([k,v])=>obj[k]!==v)
        ||!hash(obj.handoffSha256)||!hash(obj.technicalReportSha256)
        ||!hash(obj.ownerWorksheetSha256)
        ||!["ACTIVE","REVOKED"].includes(obj.localRegistrationStatus)
        ||!count(obj.claimedTechnicalMismatches)||!count(obj.ownerMarkedCount)
        ||!count(obj.ownerDiscrepancyCount)
        ||obj.ownerDiscrepancyCount>obj.ownerMarkedCount)throw Error();
      const groups=[
        ["P.P. REGISTRATIE — ONVERTROUWD",[
          ["Lokale registratiestatus",obj.localRegistrationStatus],
          ["Overdrachtsbestand SHA-256",obj.handoffSha256],
          ["Handoffstructuur",obj.handoffStructure]]],
        ["REVIEW 044 — TECHNISCHE CLAIM",[
          ["Scenario's",obj.reportedScenarios],["Technische afwijkingen",obj.claimedTechnicalMismatches],
          ["Eigenaarsmarkeringen",obj.ownerMarkedCount],["Gemelde eigenaarsafwijkingen",obj.ownerDiscrepancyCount],
          ["Technisch rapport SHA-256",obj.technicalReportSha256],
          ["Werkblad SHA-256",obj.ownerWorksheetSha256]]],
        ["IDENTITEIT, BRON EN RECHTEN — GEBLOKKEERD",[
          ["Koppeling tussen bronnen",obj.crossSourceSubjectBinding],
          ["Eigenaarsbevoegdheid",obj.ownerAuthority],
          ["PALACO ONE-sessie",obj.palacoOneSession],
          ["Externe attestatie",obj.externalAttestation],
          ["Onafhankelijke verificatie",obj.independentVerification],
          ["Autorisatie / toegang / uitgifte","HOLD / DENY / NOT_AUTHORIZED"],
          ["Enige toegestane vervolg",obj.nextPermittedStep]]]
      ];
      const fragment=document.createDocumentFragment();
      for(const [heading,rows] of groups){
        const section=document.createElement("section"),h=document.createElement("h4");
        h.textContent=heading;
        const dl=document.createElement("dl");dl.className="admin-registry-inspector";
        for(const [name,value] of rows){
          const dt=document.createElement("dt"),dd=document.createElement("dd");
          dt.textContent=name;dd.textContent=String(value);dl.append(dt,dd);
        }
        section.append(h,dl);fragment.append(section);
      }
      if(revision!==generation||dashboard.hidden)return;
      details.replaceChildren(fragment);details.hidden=false;
      status.textContent="STRUCTUUR HERKEND / Geselecteerd herstelrapport blijft onvertrouwd. Geen identiteitsbinding of PALACO ONE-toegang. HOLD / DENY.";
    }catch(_){
      if(revision!==generation||dashboard.hidden)return;
      clear("HERSTELRAPPORT GEWEIGERD / Ongeldige of tegenstrijdige gegevens. HOLD / DENY.");
    }
  });
})();
