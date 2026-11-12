"use strict";
// Read-only display of an untrusted, already exported offline verification plan.
// No checks are executed; no evidence or identity is verified in the browser.
(() => {
  const $ = id => document.getElementById(id);
  const input = $("admin-verification-plan-file");
  const load = $("admin-verification-plan-load");
  const status = $("admin-verification-plan-status");
  const overview = $("admin-verification-plan-summary");
  const work = $("admin-verification-plan-rows");
  const gates = $("admin-verification-plan-gates");
  const dashboard = $("admin-dashboard");
  if (![input,load,status,overview,work,gates,dashboard].every(Boolean)) return;

  const checks = [
    ["ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED",[],"Compare original bytes with the intake SHA-256 reference."],
    ["SOURCE_PROVENANCE_NOT_ATTESTED",[1],"Obtain independently verifiable source provenance."],
    ["SUBMITTER_IDENTITY_NOT_AUTHENTICATED",[],"Authenticate the claimed submitter through an independent channel."],
    ["REVIEWER_AUTHORITY_NOT_ESTABLISHED",[],"Authenticate and independently authorize a human reviewer."],
    ["SUBJECT_BINDING_NOT_ESTABLISHED",[2,3],"Establish common-subject binding with independently sourced evidence."],
    ["INDEPENDENT_REVIEW_NOT_COMPLETED",[1,2,3,4,5],"Conduct documented review only after prerequisites are independently satisfied."]
  ];
  const gateChecks = [
    ["SOURCE_ATTESTATION",[1,2]],
    ["CROSS_SOURCE_SUBJECT",[1,2,3,5]],
    ["OWNER_AUTHORITY",[3,4,5]],
    ["RUNTIME_EXECUTION",[1,2,6]],
    ["HUMAN_REVIEW",[1,2,3,4,5,6]]
  ];
  const fixed = {
    schema:"palaco.pp.recovery-002-verification-plan.v0",
    reference:"PP-RECOVERY-002",
    workflowStatus:"PREPARED_NOT_EXECUTED",
    sourceAuthenticity:"NOT_ESTABLISHED",
    submitterAuthentication:"NOT_ESTABLISHED",
    reviewerAuthority:"NOT_ESTABLISHED",
    crossSourceSubjectBinding:"NOT_ESTABLISHED",
    humanReview:"NOT_COMPLETED",
    palacoOneHandoff:"BLOCKED",
    palacoOneSession:"NOT_CREATED",
    independentVerification:"NOT_VERIFIED",
    reviewDecision:"HOLD",
    authorization:"HOLD",
    accessDecision:"DENY",
    issuance:"NOT_AUTHORIZED"
  };
  const topFields = [...Object.keys(fixed),
    "decisionDossierSha256","requestQueueSha256","intakeSnapshotSha256",
    "assessmentSha256","intakeCount","checkCount","workItems","decisionGates"];
  const workFields = ["intakeSequence","requestSequence","requirementId",
    "evidenceSha256","checks","gate"];
  const checkFields = ["checkOrder","checkId","prerequisites","instruction",
    "status","verification","reviewerAuthority"];
  const gateFields = ["requirementId","prerequisiteCheckOrders","status","gate"];
  const allowedReq = new Set(gateChecks.map(x => x[0]));
  const sha = v => typeof v === "string" && /^[0-9a-f]{64}$/.test(v);
  const exact = (v,keys) => v && typeof v === "object" && !Array.isArray(v) &&
    Object.keys(v).length === keys.length && keys.every(k => Object.hasOwn(v,k));
  const same = (a,b) => Array.isArray(a) && a.length===b.length &&
    a.every((v,i) => v===b[i]);
  let revision=0;
  function clear(message="Geen verificatieplan geladen. HOLD / DENY.") {
    revision++;
    overview.replaceChildren();work.replaceChildren();gates.replaceChildren();
    status.textContent=message;
  }
  input.addEventListener("change",() => clear("Bestand gewijzigd; eerdere planweergave gewist. HOLD / DENY."));
  new MutationObserver(() => {
    if (dashboard.hidden) { clear(); input.value=""; }
  }).observe(dashboard,{attributes:true,attributeFilter:["hidden"]});
  $("admin-logout").addEventListener("click", () => { clear(); input.value=""; });

  load.addEventListener("click",async() => {
    clear("Verificatieplan wordt uitsluitend lokaal gelezen. HOLD / DENY.");
    const generation=revision;
    const file=input.files?.[0];
    if (dashboard.hidden || !file || file.size<1 || file.size>128*1024) {
      status.textContent="GEWEIGERD / Kies een bestaand JSON-verificatieplan van maximaal 128 KiB. HOLD / DENY.";
      return;
    }
    try {
      const bytes=await file.arrayBuffer();
      if (generation!==revision || dashboard.hidden) return;
      const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
      if (!exact(data,topFields) ||
          Object.entries(fixed).some(([key,value]) => data[key]!==value) ||
          ![data.decisionDossierSha256,data.requestQueueSha256,
            data.intakeSnapshotSha256,data.assessmentSha256].every(sha) ||
          !Number.isInteger(data.intakeCount) || data.intakeCount<0 || data.intakeCount>64 ||
          data.checkCount!==data.intakeCount*6 ||
          !Array.isArray(data.workItems) || data.workItems.length!==data.intakeCount ||
          !Array.isArray(data.decisionGates) || data.decisionGates.length!==5) throw Error();

      const lines=document.createDocumentFragment();
      for (let i=0;i<data.workItems.length;i++) {
        const item=data.workItems[i];
        if (!exact(item,workFields) || item.intakeSequence!==i+1 ||
            !Number.isInteger(item.requestSequence) || item.requestSequence<1 ||
            !allowedReq.has(item.requirementId) || !sha(item.evidenceSha256) ||
            item.gate!=="BLOCKED" ||
            !Array.isArray(item.checks) || item.checks.length!==6) throw Error();
        for (let j=0;j<checks.length;j++) {
          const c=item.checks[j],expected=checks[j];
          if (!exact(c,checkFields) || c.checkOrder!==j+1 ||
              c.checkId!==expected[0] || !same(c.prerequisites,expected[1]) ||
              c.instruction!==expected[2] || c.status!=="NOT_STARTED" ||
              c.verification!=="NOT_VERIFIED" ||
              c.reviewerAuthority!=="NOT_ESTABLISHED") throw Error();
          const tr=document.createElement("tr");
          for (const value of [item.intakeSequence,item.requirementId,
            c.checkOrder,c.checkId,c.prerequisites.length ?
              c.prerequisites.join(", ") : "Geen","NOT_STARTED / BLOCKED"]) {
            const td=document.createElement("td");td.textContent=String(value);tr.append(td);
          }
          lines.append(tr);
        }
      }
      const gateRows=document.createDocumentFragment();
      for (let i=0;i<gateChecks.length;i++) {
        const gate=data.decisionGates[i],expected=gateChecks[i];
        if (!exact(gate,gateFields) || gate.requirementId!==expected[0] ||
            !same(gate.prerequisiteCheckOrders,expected[1]) ||
            gate.status!=="NOT_ESTABLISHED" || gate.gate!=="BLOCKED") throw Error();
        const tr=document.createElement("tr");
        for (const value of [gate.requirementId,gate.prerequisiteCheckOrders.join(", "),
          "NOT_ESTABLISHED","BLOCKED"]) {
          const td=document.createElement("td");td.textContent=value;tr.append(td);
        }gateRows.append(tr);
      }
      const info=document.createDocumentFragment();
      for (const [name,value] of [
        ["Intake-items",data.intakeCount],
        ["Geplande controles",data.checkCount],
        ["Planstatus",data.workflowStatus],
        ["Technische bronbinding","INGELEZEN CLAIM; NIET ONAFHANKELIJK GECONTROLEERD"],
        ["Reviewerbevoegdheid",data.reviewerAuthority],
        ["PALACO ONE-overdracht",data.palacoOneHandoff],
        ["Autorisatie / toegang / uitgifte","HOLD / DENY / NOT_AUTHORIZED"]
      ]) {
        const dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=name;dd.textContent=String(value);info.append(dt,dd);
      }
      if (generation!==revision || dashboard.hidden) return;
      overview.replaceChildren(info);work.replaceChildren(lines);
      gates.replaceChildren(gateRows);
      status.textContent="STRUCTUUR HERKEND / Alle zes stappen per item staan op NOT_STARTED; vijf poorten BLOCKED. Dit is een browserindicatie van ongetekende JSON, geen Python-hercontrole. HOLD / DENY.";
    } catch (_) {
      if (generation!==revision || dashboard.hidden) return;
      clear("VERIFICATIEPLAN GEWEIGERD / Ongeldige structuur, afhankelijkheden of status. HOLD / DENY.");
    }
  });
})();
