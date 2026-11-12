"use strict";
// View only a local unsigned human review request queue.
// Browser cannot establish history, actor identity, execution or authorization.
(() => {
  const $=id=>document.getElementById(id);
  const dossier=$("admin-reviewqueue-dossier"),queue=$("admin-reviewqueue-file");
  const button=$("admin-reviewqueue-view"),status=$("admin-reviewqueue-status");
  const body=$("admin-reviewqueue-rows"),dashboard=$("admin-dashboard");
  if(![dossier,queue,button,status,body,dashboard].every(Boolean))return;
  const names=new Set(["SOURCE_ATTESTATION","CROSS_SOURCE_SUBJECT",
                       "OWNER_AUTHORITY","RUNTIME_EXECUTION","HUMAN_REVIEW"]);
  const actions=new Set(["REVIEW_REQUESTED","EVIDENCE_REQUESTED","BLOCKER_REPORTED"]);
  const fixed={
    schema:"palaco.pp.recovery-002-human-review-queue.v0",
    reference:"PP-RECOVERY-002",
    evidenceVerification:"NOT_VERIFIED",
    crossSourceSubjectBinding:"NOT_ESTABLISHED",
    ownerAuthority:"NOT_ESTABLISHED",humanReview:"NOT_COMPLETED",
    palacoOneHandoff:"BLOCKED",authorization:"HOLD",
    accessDecision:"DENY",issuance:"NOT_AUTHORIZED"
  };
  const fields=[...Object.keys(fixed),"decisionDossierSha256","events"];
  const ef=["sequence","requirementId","action","previousEventSha256",
            "provenance","verification","gate","authorization","accessDecision","eventSha256"];
  const hash=x=>typeof x==="string"&&/^[0-9a-f]{64}$/.test(x);
  const exact=(o,k)=>o&&typeof o==="object"&&!Array.isArray(o)
    &&Object.keys(o).length===k.length&&k.every(v=>Object.hasOwn(o,v));
  let version=0;
  const clear=(s="Geen queue geladen. HOLD / DENY.")=>{
    version++;body.replaceChildren();status.textContent=s;
  };
  for(const file of [dossier,queue])file.addEventListener("change",()=>clear("Bestand gewijzigd; eerdere weergave vervallen. HOLD / DENY."));
  new MutationObserver(()=>{if(dashboard.hidden){clear();dossier.value="";queue.value="";}})
    .observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click",()=>{clear();dossier.value="";queue.value="";});
  button.addEventListener("click",async()=>{
    clear("Queue wordt lokaal ingelezen. HOLD / DENY.");
    const current=version,a=dossier.files?.[0],b=queue.files?.[0];
    if(dashboard.hidden||!a||!b||a.size<1||b.size<1||a.size>16384||b.size>131072){
      status.textContent="GEWEIGERD / Beslisdossier max. 16 KiB; queue max. 128 KiB. HOLD / DENY.";return;
    }
    try{
      const [ar,br]=await Promise.all([a.arrayBuffer(),b.arrayBuffer()]);
      if(current!==version||dashboard.hidden)return;
      const decoder=new TextDecoder("utf-8",{fatal:true});
      const decision=JSON.parse(decoder.decode(ar));
      const snapshot=JSON.parse(decoder.decode(br));
      if(!decision||decision.schema!=="palaco.pp.recovery-002-decision-dossier.v0"
        ||decision.reference!=="PP-RECOVERY-002"
        ||decision.authorization!=="HOLD"||decision.accessDecision!=="DENY"
        ||decision.palacoOneHandoff!=="BLOCKED"||decision.openRequirementCount!==5
        ||!exact(snapshot,fields)||Object.entries(fixed).some(([k,v])=>snapshot[k]!==v)
        ||!hash(snapshot.decisionDossierSha256)
        ||!Array.isArray(snapshot.events)||snapshot.events.length>128)throw Error();
      // A browser import is only a preview. It does not reconstruct Python's
      // canonical dossier digest or verify the full SHA-256 chain.
      const fragment=document.createDocumentFragment();
      let previous=null;
      for(const [i,event] of snapshot.events.entries()){
        if(!exact(event,ef)||event.sequence!==i+1||!names.has(event.requirementId)
          ||!actions.has(event.action)||event.previousEventSha256!==previous
          ||!hash(event.eventSha256)||event.provenance!=="UNSIGNED_LOCAL_REVIEW_REQUEST"
          ||event.verification!=="NOT_VERIFIED"||event.gate!=="BLOCKED"
          ||event.authorization!=="HOLD"||event.accessDecision!=="DENY")throw Error();
        const tr=document.createElement("tr");
        for(const value of [String(event.sequence),event.requirementId,event.action,
          event.eventSha256.slice(0,12)+"…","BLOCKED / HOLD"]){
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }
        fragment.append(tr);
        previous=event.eventSha256;
      }
      if(current!==version||dashboard.hidden)return;
      body.replaceChildren(fragment);
      status.textContent=`BROWSERINDICATIE / ${snapshot.events.length} ongetekende reviewverzoeken. Dossierhash en keten zijn NIET strikt geverifieerd. Alle vijf poorten BLOCKED; HOLD / DENY.`;
    }catch(_){
      if(current!==version||dashboard.hidden)return;
      clear("QUEUE GEWEIGERD / Ongeldige structuur of volgorde. HOLD / DENY.");
    }
  });
})();
