"use strict";
// Imported reviewer-auth contract is an unsigned local claim, not a credential.
(() => {
  const $=id=>document.getElementById(id);
  const input=$("admin-reviewer-auth-file"),button=$("admin-reviewer-auth-load"),
    status=$("admin-reviewer-auth-status"),rows=$("admin-reviewer-auth-rows"),
    gates=$("admin-reviewer-auth-gates"),dashboard=$("admin-dashboard");
  if(![input,button,status,rows,gates,dashboard].every(Boolean))return;
  const controlIds=["TRUSTED_IDENTITY_PROVIDER","CRYPTOGRAPHIC_CHALLENGE",
    "REVIEWER_ROLE_ATTESTATION","POLICY_SCOPE_MATCH","REPLAY_AND_EXPIRY",
    "SEPARATION_OF_DUTIES","SIGNED_RECEIPT","AUDIT_ANCHOR"];
  const gateIds=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT","OWNER_AUTHORITY",
    "RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const fixed={
    schema:"palaco.pp.recovery-002-reviewer-auth-contract.v0",
    reference:"PP-RECOVERY-002",
    trustBoundary:"NO_TRUST_TRANSITION_FROM_UNSIGNED_CLAIMS",
    identityProviderIntegration:"NOT_CONFIGURED",
    credentialValidation:"NOT_PERFORMED",
    recipientAuthentication:"NOT_ESTABLISHED",
    reviewerAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    reviewerIndependence:"NOT_ESTABLISHED",
    receiptVerification:"NOT_VERIFIED",humanReview:"NOT_COMPLETED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const top=[...Object.keys(fixed),"handoffManifestSha256",
    "reviewProtocolSha256","unsignedClaimCount","requiredControls","decisionGates"];
  const exact=(x,fields)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===fields.length&&fields.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let revision=0;
  const clear=(message="Geen reviewerbeveiligingscontract geladen. HOLD / DENY.")=>{
    revision++;rows.replaceChildren();gates.replaceChildren();status.textContent=message;
  };
  input.addEventListener("change",()=>clear("Bestand gewijzigd; vorige weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();input.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Ongetekend beveiligingscontract lokaal lezen. HOLD / DENY.");
    const generation=revision,source=input.files?.[0];
    if(dashboard.hidden||!source||source.size<1||source.size>32768){
      status.textContent="GEWEIGERD / Kies een lokaal JSON-contract tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const buffer=await source.arrayBuffer();
      if(generation!==revision||dashboard.hidden)return;
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(buffer));
      if(!exact(data,top)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.handoffManifestSha256)||!sha(data.reviewProtocolSha256)||
        !Number.isInteger(data.unsignedClaimCount)||data.unsignedClaimCount<0||
        data.unsignedClaimCount>64||!Array.isArray(data.requiredControls)||
        data.requiredControls.length!==8||!Array.isArray(data.decisionGates)||
        data.decisionGates.length!==5)throw Error();
      const checks=document.createDocumentFragment();
      for(let i=0;i<8;i++){
        const c=data.requiredControls[i];
        if(!exact(c,["order","controlId","requirement","status","validationMode"])||
          c.order!==i+1||c.controlId!==controlIds[i]||
          typeof c.requirement!=="string"||c.requirement.length<1||
          c.requirement.length>240||c.status!=="NOT_ESTABLISHED"||
          c.validationMode!=="EXTERNAL_AUTHENTICATED_VERIFICATION_REQUIRED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [c.order,c.controlId,c.requirement,c.status]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }checks.append(tr);
      }
      const gateRows=document.createDocumentFragment();
      for(let i=0;i<5;i++){
        const g=data.decisionGates[i];
        if(!exact(g,["requirementId","gate","verification"])||
          g.requirementId!==gateIds[i]||g.gate!=="BLOCKED"||
          g.verification!=="NOT_VERIFIED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [g.requirementId,g.verification,g.gate]){
          const td=document.createElement("td");td.textContent=v;tr.append(td);
        }gateRows.append(tr);
      }
      if(generation!==revision||dashboard.hidden)return;
      rows.replaceChildren(checks);gates.replaceChildren(gateRows);
      status.textContent="ALLE ACHT AUTHENTICATIECONTROLES ONVERVULD / Geen identity provider aangesloten, geen bevoegdheid aangetoond, geen review uitgevoerd. NOT_READY / HOLD / DENY.";
    }catch(_){
      if(generation!==revision||dashboard.hidden)return;
      clear("CONTRACT GEWEIGERD / Ongeldige claims of tegenstrijdige statussen. HOLD / DENY.");
    }
  });
})();
