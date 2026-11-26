"use strict";
// Unsigned local v0 compatibility registry viewer. No migration or authority.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-compat-file"),button=$("admin-compat-load"),
    status=$("admin-compat-status"),rows=$("admin-compat-rows"),
    rules=$("admin-compat-rules"),dashboard=$("admin-dashboard");
  if(![file,button,status,rows,rules,dashboard].every(Boolean))return;
  const roles=["DECISION_DOSSIER","REVIEW_QUEUE","REVIEW_INTAKE",
    "VERIFICATION_PLAN","OBSERVATION_REGISTER","HANDOFF_MANIFEST",
    "RECEIPT_PROTOCOL","REVIEWER_AUTH_REQUIREMENTS",
    "REVIEWER_SERVICE_BLUEPRINT","REVIEWER_INTERFACE_CONTRACT",
    "TRUST_TRANSITION_PROTOCOL","REVOCATION_RECOVERY_CONTRACT"];
  const schemas=["decision-dossier","human-review-queue","review-intake",
    "verification-plan","observation-register","human-review-handoff",
    "review-protocol","reviewer-auth-contract","reviewer-service-blueprint",
    "reviewer-interface-contract","trust-transition","revocation-recovery"]
    .map(name=>"palaco.pp.recovery-002-"+name+".v0");
  const restrictions=["UNKNOWN_SCHEMA_REJECT","MIXED_VERSION_REJECT",
    "SILENT_MIGRATION_PROHIBITED","FORWARD_VERSION_UNSUPPORTED",
    "STRICT_REVALIDATION_REQUIRED",
    "EXTERNAL_ATTESTATION_REQUIRED_FOR_AUTHORITY"];
  const gates=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const fixed={schema:"palaco.pp.recovery-002-contract-compatibility.v0",
    reference:"PP-RECOVERY-002",supportedVersion:"v0",
    mixedVersionAcceptance:"DENY",migrationService:"NOT_IMPLEMENTED",
    breakingChangeEvaluation:"REQUIRES_NEW_INDEPENDENT_REVIEW",
    compatibilityScope:"STRICT_INTERNAL_SOURCE_CONSISTENCY_ONLY",
    externallyVerifiedCompatibility:"NOT_VERIFIED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"};
  const keys=[...Object.keys(fixed),"securityAssuranceSha256","contracts",
    "upgradeRules","decisionGates"];
  const exact=(o,k)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===k.length&&k.every(x=>Object.hasOwn(o,x));
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((x,i)=>x===b[i]);
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let revision=0;
  function clear(message="Geen compatibiliteitsregister geladen. HOLD / DENY."){
    revision++;rows.replaceChildren();rules.replaceChildren();status.textContent=message;
  }
  file.addEventListener("change",()=>clear("Bestand gewijzigd; registerweergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal versiecontract lezen. HOLD / DENY.");
    const epoch=revision,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON van maximaal 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(epoch!==revision||dashboard.hidden)return;
      if(!exact(data,keys)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.securityAssuranceSha256)||
        !Array.isArray(data.contracts)||data.contracts.length!==12||
        !same(data.upgradeRules,restrictions)||
        !Array.isArray(data.decisionGates)||data.decisionGates.length!==5)throw Error();
      const body=document.createDocumentFragment();
      for(let i=0;i<12;i++){
        const c=data.contracts[i];
        if(!exact(c,["order","role","schema","majorVersion","sha256",
          "compatibility","externalAttestation","migration"])||
          c.order!==i+1||c.role!==roles[i]||c.schema!==schemas[i]||
          c.majorVersion!==0||!sha(c.sha256)||
          c.compatibility!=="INTERNALLY_MATCHED_V0_ONLY"||
          c.externalAttestation!=="NOT_VERIFIED"||
          c.migration!=="NOT_PERFORMED")throw Error();
        const tr=document.createElement("tr");
        for(const value of [i+1,c.role,"v0",c.sha256.slice(0,18)+"…","NOT_VERIFIED"]){
          const td=document.createElement("td");td.textContent=String(value);tr.append(td);
        }body.append(tr);
      }
      for(let i=0;i<5;i++){
        const g=data.decisionGates[i];
        if(!exact(g,["requirementId","gate","verification"])||
          g.requirementId!==gates[i]||g.gate!=="BLOCKED"||
          g.verification!=="NOT_VERIFIED")throw Error();
      }
      const list=document.createDocumentFragment();
      for(const item of restrictions){
        const li=document.createElement("li");li.textContent=item;list.append(li);
      }
      if(epoch!==revision||dashboard.hidden)return;
      rows.replaceChildren(body);rules.replaceChildren(list);
      status.textContent="V0 STRUCTUUR HERKEND / Geen externe verificatie of automatische migratie; vijf poorten BLOCKED. HOLD / DENY.";
    }catch(_){
      if(epoch!==revision||dashboard.hidden)return;
      clear("COMPATIBILITEITSREGISTER GEWEIGERD / Schema- of statusafwijking. HOLD / DENY.");
    }
  });
})();
