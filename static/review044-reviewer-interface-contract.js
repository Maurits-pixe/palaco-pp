"use strict";
// Read-only display of UNIMPLEMENTED reviewer service interfaces.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-reviewer-interface-file"),button=$("admin-reviewer-interface-load"),
    status=$("admin-reviewer-interface-status"),rows=$("admin-reviewer-interface-rows"),
    errors=$("admin-reviewer-interface-errors"),dashboard=$("admin-dashboard");
  if (![file,button,status,rows,errors,dashboard].every(Boolean))return;
  const services=["AUTHENTICATION","AUTHORIZATION","AUDIT"];
  const paths=["/internal/reviewer-auth/assert","/internal/reviewer-auth/scope",
    "/internal/reviewer-auth/receipt"];
  const outputs=["IDENTITY_ASSERTION","REVIEWER_SCOPE_DECISION",
    "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE"];
  const failures=["MALFORMED_REQUEST","UNSUPPORTED_VERSION","UNTRUSTED_ISSUER",
    "INVALID_SIGNATURE","AUDIENCE_MISMATCH","PURPOSE_MISMATCH","CHALLENGE_EXPIRED",
    "REPLAY_DETECTED","CREDENTIAL_REVOKED","ROLE_ATTESTATION_MISSING",
    "SCOPE_DENIED","CONFLICT_OF_INTEREST","AUDIT_UNAVAILABLE",
    "ANCHOR_NOT_VERIFIED","TRUSTED_TIME_UNAVAILABLE","DEPENDENCY_UNAVAILABLE"];
  const revoked=["CREDENTIAL_REVOKED","ROLE_REVOKED","SIGNING_KEY_REVOKED",
    "AUDIT_ANCHOR_COMPROMISED"];
  const owners=["AUTHENTICATION","AUTHORIZATION","AUDIT","AUDIT"];
  const fixed={schema:"palaco.pp.recovery-002-reviewer-interface-contract.v0",
    reference:"PP-RECOVERY-002",integrationState:"NOT_IMPLEMENTED",
    independentVerification:"NOT_VERIFIED",reviewerAuthority:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",authorization:"HOLD",accessDecision:"DENY",
    issuance:"NOT_AUTHORIZED"};
  const shape=(x,k)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===k.length&&k.every(t=>Object.hasOwn(x,t));
  const same=(a,b)=>Array.isArray(a)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
  const hex=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  let rev=0;
  const clear=(msg="Geen interfacecontract geladen. HOLD / DENY.")=>{
    rev++;rows.replaceChildren();errors.replaceChildren();status.textContent=msg;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal interfacecontract lezen. HOLD / DENY.");
    const generation=rev,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>32768){
      status.textContent="GEWEIGERD / Kies een JSON-contract tot 32 KiB. HOLD / DENY.";return;
    }
    try{
      const raw=await f.arrayBuffer();
      if(generation!==rev||dashboard.hidden)return;
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(raw));
      const keys=[...Object.keys(fixed),"blueprintSha256","handoffManifestSha256",
        "interfaces","errorPolicy","revocationPolicy","separation"];
      if(!shape(data,keys)||Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !hex(data.blueprintSha256)||!hex(data.handoffManifestSha256)||
        !Array.isArray(data.interfaces)||data.interfaces.length!==3||
        !Array.isArray(data.revocationPolicy)||data.revocationPolicy.length!==4||
        !shape(data.errorPolicy,["knownFailureCodes","unknownError",
          "onSignatureFailure","onClockOrNonceFailure","onRevocationLookupFailure",
          "onAuditUnavailable","onPolicyMismatch","errorDetails"])||
        !same(data.errorPolicy.knownFailureCodes,failures)||
        data.errorPolicy.unknownError!=="DENY_UNKNOWN_FAILURE"||
        ["onSignatureFailure","onClockOrNonceFailure","onRevocationLookupFailure",
          "onAuditUnavailable","onPolicyMismatch"].some(k=>data.errorPolicy[k]!=="DENY")||
        data.errorPolicy.errorDetails!=="NO_CREDENTIALS_OR_PRIVATE_KEYS_IN_LOGS")throw Error();
      const rendered=document.createDocumentFragment();
      for(let i=0;i<3;i++){
        const item=data.interfaces[i];
        if(!shape(item,["service","method","proposedPath","requestFields",
          "futureSuccessFields","futureOutput","implementation","endpointEnabled",
          "acceptsSelfReportedRoleClaims","responseToday"])||
          item.service!==services[i]||item.method!=="POST"||
          item.proposedPath!==paths[i]||item.futureOutput!==outputs[i]||
          !Array.isArray(item.requestFields)||!Array.isArray(item.futureSuccessFields)||
          item.requestFields.some(s=>typeof s!=="string")||
          item.futureSuccessFields.some(s=>typeof s!=="string")||
          item.implementation!=="NOT_IMPLEMENTED"||item.endpointEnabled!==false||
          item.acceptsSelfReportedRoleClaims!==false||
          item.responseToday!=="DENY_UNIMPLEMENTED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [item.service,item.proposedPath,"UITGESCHAKELD","DENY_UNIMPLEMENTED"]){
          const td=document.createElement("td");td.textContent=v;tr.append(td);
        }rendered.append(tr);
      }
      for(let i=0;i<4;i++){
        const item=data.revocationPolicy[i];
        if(!shape(item,["event","ownerService","effect",
          "requiresFreshIndependentVerification"])||
          item.event!==revoked[i]||item.ownerService!==owners[i]||
          item.effect!=="DENY"||item.requiresFreshIndependentVerification!==true)throw Error();
      }
      const sep=data.separation;
      if(!shape(sep,["authenticationCannotAuthorize","authorizationCannotAuthenticate",
        "auditCannotGrant","untrustedLocalClaimsNeverElevate",
        "singleServiceCannotReleaseHold","palacoOneSessionCreation"])||
        Object.entries(sep).some(([k,v])=>k==="palacoOneSessionCreation"?
          v!=="PROHIBITED":v!==true))throw Error();
      const errList=document.createDocumentFragment();
      for(const failure of failures){
        const li=document.createElement("li");li.textContent=failure+" — DENY";errList.append(li);
      }
      if(generation!==rev||dashboard.hidden)return;
      rows.replaceChildren(rendered);errors.replaceChildren(errList);
      status.textContent="INTERFACECONTRACT HERKEND / Alle drie endpoints UITGESCHAKELD; vier intrekkingen DENY. Geen identity provider of reviewerautorisatie. HOLD / DENY.";
    }catch(_){
      if(generation!==rev||dashboard.hidden)return;
      clear("INTERFACECONTRACT GEWEIGERD / Onjuiste structuur of statusclaim. HOLD / DENY.");
    }
  });
})();
