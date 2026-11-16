"use strict";
// Read-only deny-all trust policy. No issuer enrollment, signing or authorization.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-trust-policy-file"),load=$("admin-trust-policy-load"),
    status=$("admin-trust-policy-status"),rows=$("admin-trust-policy-rows"),
    denials=$("admin-trust-policy-denials"),dashboard=$("admin-dashboard");
  if(![file,load,status,rows,denials,dashboard].every(Boolean))return;
  const issuer=["EXTERNALLY_APPROVED_ISSUER_ROOT",
    "ISSUER_ID_AND_RECEIPT_AUDIENCE_BINDING",
    "TRUST_ANCHOR_PROVENANCE_AND_OWNER_AUTHORIZATION",
    "INDEPENDENT_ISSUER_ONBOARDING_REVIEW",
    "ISSUER_REVOCATION_AND_EMERGENCY_DENY"];
  const algorithms=["EXPLICIT_ALGORITHM_ALLOWLIST_NOT_WILDCARD",
    "NO_ALG_NONE_OR_SYMMETRIC_ASYMMETRIC_CONFUSION",
    "KEY_TYPE_CURVE_AND_USAGE_MATCH",
    "CANONICAL_SIGNED_BYTES_NO_REENCODING",
    "DOWNGRADE_AND_UNSUPPORTED_ALGORITHM_DENY"];
  const rotations=["ISSUER_SCOPED_KID_UNIQUENESS",
    "PINNED_ROOT_AND_SIGNED_KEYSET_UPDATES",
    "KEY_VALIDITY_WITH_TRUSTED_CLOCK",
    "ROTATION_EPOCH_AND_SIGNED_OVERLAP_POLICY",
    "HISTORICAL_KEY_VERIFICATION_ONLY_UNDER_AUTHORIZED_POLICY",
    "NO_KEY_MATERIAL_IN_LOCAL_REPORTS"];
  const revocations=["SIGNED_FRESH_ISSUER_REVOCATION_FEED",
    "KEY_AND_REVIEWER_CREDENTIAL_REVOCATION",
    "TRUST_ROOT_REMOVAL_FAIL_CLOSED","REVOCATION_FEED_OUTAGE_FAIL_CLOSED",
    "COMPROMISE_RESPONSE_REQUIRES_INDEPENDENT_REVIEW",
    "NO_OFFLINE_STALE_TRUST_FALLBACK"];
  const failureCodes=["UNKNOWN_ISSUER","UNPINNED_TRUST_ROOT",
    "MISSING_TRUSTED_KEY","UNSUPPORTED_SIGNATURE_ALGORITHM",
    "EXPIRED_SIGNING_KEY","REVOKED_KEY_OR_REVIEWER",
    "STALE_REVOCATION_FEED","TRUSTED_CLOCK_UNAVAILABLE",
    "REPLAY_LEDGER_UNAVAILABLE","INDEPENDENT_REVIEWER_UNAUTHENTICATED",
    "AUDIT_ANCHOR_UNVERIFIABLE","HUMAN_RELEASE_DECISION_MISSING"];
  const fixed={
    schema:"palaco.pp.recovery-002-verifier-trust-policy.v0",
    reference:"PP-RECOVERY-002",
    binding:"STRICT_INTERNAL_SOURCE_CONSISTENCY_ONLY",
    policyMode:"DENY_ALL_UNTIL_EXTERNAL_TRUST_CONFIGURED_AND_VERIFIED",
    trustedIssuerCount:0,trustAnchorImport:"PROHIBITED_IN_THIS_MODULE",
    keyMaterial:"NOT_PRESENT",trustAnchorVerification:"NOT_PERFORMED",
    issuerOnboarding:"NOT_IMPLEMENTED",
    signatureVerification:"NOT_IMPLEMENTED",keyRotation:"NOT_IMPLEMENTED",
    revocationFeed:"NOT_CONFIGURED",independentVerifier:"NOT_DEPLOYED",
    externalAudit:"NOT_VERIFIED",reviewerAuthority:"NOT_ESTABLISHED",
    receiptAcceptance:"NOT_PERFORMED",independentVerification:"NOT_VERIFIED",
    releaseReadiness:"NOT_READY",palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const exact=(x,keys)=>x&&typeof x==="object"&&!Array.isArray(x)&&
    Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
  const sha=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let gen=0;
  const clear=(message="Geen Verifier Trust Policy Register geladen. HOLD / DENY.")=>{
    gen++;rows.replaceChildren();denials.replaceChildren();status.textContent=message;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout")?.addEventListener("click",logout);
  load.addEventListener("click",async()=>{
    clear("Ongetekend deny-all trustregister lokaal lezen. HOLD / DENY.");
    const sequence=gen,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(sequence!==gen||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"verifierBlueprintSha256",
        "receiptProtocolSha256","issuerRegistry","issuerRequirements",
        "algorithmRules","allowedAlgorithms","rotationRules",
        "revocationRules","defaultDenialRules"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !sha(data.verifierBlueprintSha256)||!sha(data.receiptProtocolSha256)||
        !Array.isArray(data.issuerRegistry)||data.issuerRegistry.length!==0||
        !Array.isArray(data.allowedAlgorithms)||data.allowedAlgorithms.length!==0)throw Error();
      const requirements=document.createDocumentFragment();
      for(const [key,labels] of [
        ["issuerRequirements",issuer],["algorithmRules",algorithms],
        ["rotationRules",rotations],["revocationRules",revocations]
      ]){
        const a=data[key];
        if(!Array.isArray(a)||a.length!==labels.length)throw Error();
        for(let i=0;i<a.length;i++){
          const x=a[i];
          if(!exact(x,["requirementId","status","verification"])||
            x.requirementId!==labels[i]||x.status!=="NOT_CONFIGURED"||
            x.verification!=="NOT_PERFORMED")throw Error();
          const tr=document.createElement("tr");
          for(const v of [key,x.requirementId,"NOT_CONFIGURED"]){
            const td=document.createElement("td");td.textContent=v;tr.append(td);
          }requirements.append(tr);
        }
      }
      const failures=document.createDocumentFragment();
      if(!Array.isArray(data.defaultDenialRules)||
        data.defaultDenialRules.length!==failureCodes.length)throw Error();
      for(let i=0;i<failureCodes.length;i++){
        const x=data.defaultDenialRules[i];
        if(!exact(x,["reason","decision","authorityEffect"])||
          x.reason!==failureCodes[i]||x.decision!=="DENY"||
          x.authorityEffect!=="NONE")throw Error();
        const li=document.createElement("li");li.textContent=x.reason+" — DENY";
        failures.append(li);
      }
      if(sequence!==gen||dashboard.hidden)return;
      rows.replaceChildren(requirements);denials.replaceChildren(failures);
      status.textContent="TRUSTREGISTER HERKEND / 0 vertrouwde uitgevers, 0 algoritmen, 22 niet-geconfigureerde eisen. DENY / HOLD.";
    }catch(_){
      if(sequence!==gen||dashboard.hidden)return;
      clear("TRUST POLICY GEWEIGERD / Ongeldige structuur of tegenstrijdige status. HOLD / DENY.");
    }
  });
})();
