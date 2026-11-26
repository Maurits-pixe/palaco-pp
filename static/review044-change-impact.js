"use strict";
// Display-only, unsigned hypothetical change impact; never executes changes.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-impact-file"),button=$("admin-impact-load"),
    status=$("admin-impact-status"),rows=$("admin-impact-rows"),
    summary=$("admin-impact-summary"),dashboard=$("admin-dashboard");
  if(![file,button,status,rows,summary,dashboard].every(Boolean))return;
  const roles=["DECISION_DOSSIER","REVIEW_QUEUE","REVIEW_INTAKE",
    "VERIFICATION_PLAN","OBSERVATION_REGISTER","HANDOFF_MANIFEST",
    "RECEIPT_PROTOCOL","REVIEWER_AUTH_REQUIREMENTS",
    "REVIEWER_SERVICE_BLUEPRINT","REVIEWER_INTERFACE_CONTRACT",
    "TRUST_TRANSITION_PROTOCOL","REVOCATION_RECOVERY_CONTRACT"];
  const changeTypes=["SCHEMA_CHANGE","VERSION_CHANGE","CONTENT_CHANGE","POLICY_CHANGE"];
  const gates=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const aggregates=["SECURITY_ASSURANCE_DOSSIER","CONTRACT_COMPATIBILITY_REGISTER"];
  const fixed={schema:"palaco.pp.recovery-002-change-impact.v0",
    reference:"PP-RECOVERY-002",changeApplied:false,
    independentVerification:"NOT_VERIFIED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"};
  const exact=(o,keys)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
  const isHash=s=>typeof s==="string"&&/^[a-f0-9]{64}$/.test(s);
  let seq=0;
  const clear=(msg="Geen change-impactrapport geladen. HOLD / DENY.")=>{
    seq++;rows.replaceChildren();summary.replaceChildren();status.textContent=msg;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; impactweergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Hypothetisch impactrapport lokaal lezen. HOLD / DENY.");
    const generation=seq,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(generation!==seq||dashboard.hidden)return;
      const fields=[...Object.keys(fixed),"compatibilityRegisterSha256",
        "changeRequest","impactAnalysis","affectedAggregateArtifacts",
        "impactCount","gateReassessment","changePolicy"];
      if(!exact(data,fields)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !isHash(data.compatibilityRegisterSha256)||
        !exact(data.changeRequest,["changedRole","changeType","scope",
          "proposedBytes","changeVerification"]))throw Error();
      const req=data.changeRequest,start=roles.indexOf(req.changedRole);
      if(start<0||!changeTypes.includes(req.changeType)||
        req.scope!=="HYPOTHETICAL_NOT_APPLIED"||
        req.proposedBytes!=="NOT_PROVIDED"||
        req.changeVerification!=="NOT_PERFORMED"||
        !Array.isArray(data.impactAnalysis)||data.impactAnalysis.length!==12-start||
        data.impactCount!==12-start||
        !Array.isArray(data.affectedAggregateArtifacts)||
        data.affectedAggregateArtifacts.length!==2||
        !Array.isArray(data.gateReassessment)||data.gateReassessment.length!==5)throw Error();
      const list=document.createDocumentFragment();
      for(let j=0;j<data.impactAnalysis.length;j++){
        const x=data.impactAnalysis[j],index=start+j;
        if(!exact(x,["order","role","impact","requiredAction",
          "verification","migration"])||x.order!==index+1||
          x.role!==roles[index]||
          x.impact!==(j===0?"CHANGED_SOURCE":"TRANSITIVE_DEPENDENCY")||
          x.requiredAction!=="REBUILD_AND_STRICTLY_REVALIDATE"||
          x.verification!=="NOT_PERFORMED"||
          x.migration!=="NOT_AUTHORIZED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [x.order,x.role,x.impact,"NOT_PERFORMED"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }list.append(tr);
      }
      for(let i=0;i<2;i++){
        const x=data.affectedAggregateArtifacts[i];
        if(!exact(x,["artifact","action","status"])||
          x.artifact!==aggregates[i]||
          x.action!=="REGENERATE_FROM_VALIDATED_SOURCES"||
          x.status!=="NOT_STARTED")throw Error();
      }
      for(let i=0;i<5;i++){
        const x=data.gateReassessment[i];
        if(!exact(x,["requirementId","reassessment","gate","verification"])||
          x.requirementId!==gates[i]||x.reassessment!=="REQUIRED"||
          x.gate!=="BLOCKED"||x.verification!=="NOT_VERIFIED")throw Error();
      }
      const p=data.changePolicy;
      if(!exact(p,["unknownSchema","mixedVersions","breakingChange",
        "automaticMigration","unreviewedChange","releaseWithoutExternalEvidence"])||
        p.unknownSchema!=="DENY"||p.mixedVersions!=="DENY"||
        p.breakingChange!=="INDEPENDENT_REVIEW_REQUIRED"||
        p.automaticMigration!=="PROHIBITED"||p.unreviewedChange!=="DENY"||
        p.releaseWithoutExternalEvidence!=="DENY")throw Error();
      const info=document.createDocumentFragment();
      for(const [k,v] of [["Wijziging",req.changeType],["Bronrol",req.changedRole],
        ["Afhankelijke broncontracten",data.impactCount],
        ["Herbouw van aggregaten",2],["Beslispoorten",5],
        ["Werkelijke wijziging","NIET UITGEVOERD"]]){
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=k;dd.textContent=String(v);info.append(dt,dd);
      }
      if(generation!==seq||dashboard.hidden)return;
      rows.replaceChildren(list);summary.replaceChildren(info);
      status.textContent="HYPOTHETISCHE IMPACT / Niets gewijzigd, geen controles uitgevoerd, vijf poorten BLOCKED. HOLD / DENY.";
    }catch(_){
      if(generation!==seq||dashboard.hidden)return;
      clear("CHANGE-IMPACTRAPPORT GEWEIGERD / Ongeldige claims of incompatibiliteit. HOLD / DENY.");
    }
  });
})();
