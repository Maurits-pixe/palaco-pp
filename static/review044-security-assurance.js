"use strict";
// Local unsigned Security Assurance Dossier viewer; never an attestation.
(() => {
  const $=id=>document.getElementById(id);
  const file=$("admin-assurance-file"),button=$("admin-assurance-load"),
    status=$("admin-assurance-status"),sources=$("admin-assurance-sources"),
    gaps=$("admin-assurance-gaps"),dashboard=$("admin-dashboard");
  if(![file,button,status,sources,gaps,dashboard].every(Boolean))return;
  const roles=["DECISION_DOSSIER","REVIEW_QUEUE","REVIEW_INTAKE",
    "VERIFICATION_PLAN","OBSERVATION_REGISTER","HANDOFF_MANIFEST",
    "RECEIPT_PROTOCOL","REVIEWER_AUTH_REQUIREMENTS",
    "REVIEWER_SERVICE_BLUEPRINT","REVIEWER_INTERFACE_CONTRACT",
    "TRUST_TRANSITION_PROTOCOL","REVOCATION_RECOVERY_CONTRACT"];
  const controls=["TRUSTED_IDENTITY_PROVIDER","CRYPTOGRAPHIC_CHALLENGE",
    "REVIEWER_ROLE_ATTESTATION","POLICY_SCOPE_MATCH","REPLAY_AND_EXPIRY",
    "SEPARATION_OF_DUTIES","SIGNED_RECEIPT","AUDIT_ANCHOR"];
  const transitions=["AUTHENTICATION_TO_AUTHORIZATION",
    "AUTHORIZATION_TO_AUDIT","AUDIT_TO_MANUAL_REVIEW"];
  const revocations=["CREDENTIAL_REVOKED","ROLE_REVOKED",
    "SIGNING_KEY_REVOKED","AUDIT_ANCHOR_COMPROMISED"];
  const recovery=["INDEPENDENT_REVOCATION_EVENT_ATTESTATION",
    "QUARANTINE_DERIVED_ASSERTIONS_AND_DECISIONS",
    "INVALIDATE_NONCES_AND_EXPIRED_CREDENTIALS",
    "REVERIFY_ISSUER_KEYS_AND_FRESH_CREDENTIAL",
    "RECHECK_ROLE_SCOPE_AND_SEPARATION_OF_DUTIES",
    "VERIFY_NEW_RECEIPT_SIGNATURE_AND_EXTERNAL_AUDIT_ANCHOR",
    "REQUIRE_NEW_INDEPENDENT_HUMAN_REVIEW",
    "KEEP_HOLD_UNTIL_EXTERNAL_AUTHORIZED_DECISION"];
  const gates=["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT",
    "OWNER_AUTHORITY","RUNTIME_EXECUTION","HUMAN_REVIEW"];
  const openGaps=["SOURCE_AUTHENTICITY_NOT_ATTESTED","SUBMITTER_IDENTITY_NOT_VERIFIED",
    "REVIEWER_AUTHENTICATION_NOT_ESTABLISHED","REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "SUBJECT_BINDING_NOT_ESTABLISHED","CRYPTOGRAPHIC_ASSERTIONS_NOT_VALIDATED",
    "SIGNED_RECEIPT_NOT_VERIFIED","EXTERNAL_AUDIT_NOT_VERIFIED",
    "REVOCATION_PROPAGATION_NOT_IMPLEMENTED",
    "INDEPENDENT_HUMAN_REVIEW_NOT_COMPLETED","PALACO_ONE_AUTHORIZATION_NOT_GRANTED"];
  const fixed={schema:"palaco.pp.recovery-002-security-assurance.v0",
    reference:"PP-RECOVERY-002",
    contractBinding:"STRICT_INTERNAL_TWELVE_SOURCE_CONSISTENCY",
    independentVerification:"NOT_VERIFIED",humanReview:"NOT_COMPLETED",
    reviewerAuthority:"NOT_ESTABLISHED",releaseReadiness:"NOT_READY",
    palacoOneHandoff:"BLOCKED",palacoOneSession:"NOT_CREATED",
    authorization:"HOLD",accessDecision:"DENY",issuance:"NOT_AUTHORIZED"};
  const exact=(o,keys)=>o&&typeof o==="object"&&!Array.isArray(o)&&
    Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
  const isHash=x=>typeof x==="string"&&/^[a-f0-9]{64}$/.test(x);
  let generation=0;
  const clear=(m="Geen assurance-dossier geladen. HOLD / DENY.")=>{
    generation++;sources.replaceChildren();gaps.replaceChildren();status.textContent=m;
  };
  file.addEventListener("change",()=>clear("Bestand gewijzigd; weergave gewist. HOLD / DENY."));
  const logout=()=>{clear();file.value="";};
  new MutationObserver(()=>{if(dashboard.hidden)logout();})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",logout);
  button.addEventListener("click",async()=>{
    clear("Lokaal dossier lezen. HOLD / DENY.");
    const current=generation,f=file.files?.[0];
    if(dashboard.hidden||!f||f.size<1||f.size>65536){
      status.textContent="GEWEIGERD / Kies JSON tot 64 KiB. HOLD / DENY.";return;
    }
    try{
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(await f.arrayBuffer()));
      if(current!==generation||dashboard.hidden)return;
      if(!exact(data,[...Object.keys(fixed),"sources","evidenceLimits",
        "reviewerControls","trustTransitions","revocationRequirements",
        "recoveryRequirements","decisionGates","unresolvedAssuranceGaps"])||
        Object.entries(fixed).some(([k,v])=>data[k]!==v)||
        !exact(data.evidenceLimits,["sourceByteDigests","cryptographicSignatures",
          "independentTimestamp","externalRevocationFeed"])||
        data.evidenceLimits.sourceByteDigests!=="LOCAL_SHA256_ONLY"||
        data.evidenceLimits.cryptographicSignatures!=="NOT_VERIFIED"||
        data.evidenceLimits.independentTimestamp!=="ABSENT"||
        data.evidenceLimits.externalRevocationFeed!=="NOT_CONFIGURED")throw Error();
      const arrays=[["sources",12],["reviewerControls",8],["trustTransitions",3],
        ["revocationRequirements",4],["recoveryRequirements",8],
        ["decisionGates",5],["unresolvedAssuranceGaps",11]];
      if(arrays.some(([key,size])=>!Array.isArray(data[key])||
        data[key].length!==size))throw Error();
      const src=document.createDocumentFragment();
      for(let i=0;i<12;i++){
        const s=data.sources[i];
        if(!exact(s,["order","role","sha256","internalContract","externalAuthenticity"])||
          s.order!==i+1||s.role!==roles[i]||!isHash(s.sha256)||
          s.internalContract!=="RECONSTRUCTED"||s.externalAuthenticity!=="NOT_ATTESTED")throw Error();
        const tr=document.createElement("tr");
        for(const v of [s.order,s.role,s.sha256.slice(0,18)+"…","NOT_ATTESTED"]){
          const td=document.createElement("td");td.textContent=String(v);tr.append(td);
        }src.append(tr);
      }
      for(let i=0;i<8;i++){
        const c=data.reviewerControls[i],r=data.recoveryRequirements[i];
        if(!exact(c,["controlId","status"])||c.controlId!==controls[i]||
          c.status!=="NOT_ESTABLISHED"||!exact(r,["control","status"])||
          r.control!==recovery[i]||r.status!=="NOT_STARTED")throw Error();
      }
      for(let i=0;i<3;i++){
        const t=data.trustTransitions[i];
        if(!exact(t,["boundary","status","decision"])||
          t.boundary!==transitions[i]||t.status!=="BLOCKED"||t.decision!=="DENY")throw Error();
      }
      for(let i=0;i<4;i++){
        const r=data.revocationRequirements[i];
        if(!exact(r,["event","ownerService","propagation","decision"])||
          r.event!==revocations[i]||r.propagation!=="NOT_EXECUTED"||
          r.decision!=="DENY")throw Error();
      }
      for(let i=0;i<5;i++){
        const g=data.decisionGates[i];
        if(!exact(g,["requirementId","status","verification"])||
          g.requirementId!==gates[i]||g.status!=="BLOCKED"||
          g.verification!=="NOT_VERIFIED")throw Error();
      }
      const gapList=document.createDocumentFragment();
      for(let i=0;i<11;i++){
        const g=data.unresolvedAssuranceGaps[i];
        if(!exact(g,["gapId","status","resolution"])||g.gapId!==openGaps[i]||
          g.status!=="OPEN"||
          g.resolution!=="INDEPENDENT_EXTERNAL_EVIDENCE_REQUIRED")throw Error();
        const li=document.createElement("li");li.textContent=g.gapId+" — OPEN";gapList.append(li);
      }
      if(current!==generation||dashboard.hidden)return;
      sources.replaceChildren(src);gaps.replaceChildren(gapList);
      status.textContent="ONGETEKEND DOSSIER / 12 interne bronverwijzingen, 11 open gaps, 5 poorten BLOCKED. Geen originele bronnen of externe bewijzen opnieuw gecontroleerd. HOLD / DENY.";
    }catch(_){
      if(current!==generation||dashboard.hidden)return;
      clear("ASSURANCE-DOSSIER GEWEIGERD / Onjuiste structuur of vrijgaveclaim. HOLD / DENY.");
    }
  });
})();
