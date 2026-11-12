"""Strict, non-authoritative PP-RECOVERY-002 intake assessment.

Pure, offline parsing of the original dossier, request queue, and intake bytes.
Produces a *missing-controls* report; never certifies evidence, its submitter,
a reviewer or a PALACO ONE identity. No filesystem, network or execution.
"""
import hashlib
import json

from review_044_human_review_queue import _dossier, _queue, _digest
from review_044_review_intake import _check_intake, _read_json, MAX_INTAKE_BYTES
from review_044_recovery_decision import REQUIREMENTS

ERROR = "PP_RECOVERY_002_INTAKE_ASSESSMENT_INVALID"
MISSING_CONTROLS = (
    "ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED",
    "SOURCE_PROVENANCE_NOT_ATTESTED",
    "SUBMITTER_IDENTITY_NOT_AUTHENTICATED",
    "REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "SUBJECT_BINDING_NOT_ESTABLISHED",
    "INDEPENDENT_REVIEW_NOT_COMPLETED",
)


def assess_review_intake(
    decision_dossier_bytes: bytes,
    review_queue_bytes: bytes,
    intake_bytes: bytes,
) -> dict[str, object]:
    """Validate exact input contracts and list unresolved checks for each intake.

    No evidence bytes are provided, so evidence digests are only reported
    references. Even a correct internal hash chain is not externally anchored.
    """
    try:
        dossier = _dossier(decision_dossier_bytes)
        dossier_hash = _digest(dossier)
        queue = _queue(review_queue_bytes, dossier_hash)
        queue_hash = _digest(queue)
        requests = {entry["sequence"]: entry for entry in queue["events"]}
        intake = _check_intake(intake_bytes, dossier_hash, queue_hash, requests)
        # Reject repeated references that the intake appender would never create.
        observed = set()
        summaries = []
        for item in intake["items"]:
            pair = (item["requestSequence"], item["evidenceSha256"])
            if pair in observed:
                raise ValueError
            observed.add(pair)
            summaries.append({
                "sequence": item["sequence"],
                "requestSequence": item["requestSequence"],
                "requirementId": item["requirementId"],
                "evidenceSha256": item["evidenceSha256"],
                "evidenceKind": item["evidenceKind"],
                "submitterRoleClaim": item["submitterRoleClaim"],
                "missingControls": list(MISSING_CONTROLS),
                "assessment": "UNVERIFIED_INTAKE_REFERENCE_ONLY",
                "gate": "BLOCKED",
            })
        requirements = [
            {
                "requirementId": identifier,
                "linkedIntakeCount": sum(x["requirementId"] == identifier for x in summaries),
                "evidenceStatus": "NOT_ESTABLISHED",
                "gate": "BLOCKED",
            }
            for identifier, _ in REQUIREMENTS
        ]
        return {
            "schema": "palaco.pp.recovery-002-intake-assessment.v0",
            "reference": "PP-RECOVERY-002",
            "decisionDossierSha256": dossier_hash,
            "requestQueueSha256": queue_hash,
            "intakeSnapshotSha256": hashlib.sha256(intake_bytes).hexdigest(),
            "intakeCount": len(summaries),
            "assessedItems": summaries,
            "requirements": requirements,
            "validationScope": "STRICT_INTERNAL_STRUCTURE_AND_HASH_LINKS_ONLY",
            "originalEvidenceVerification": "NOT_PERFORMED",
            "sourceAuthenticity": "NOT_ESTABLISHED",
            "submitterAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "crossSourceSubjectBinding": "NOT_ESTABLISHED",
            "humanReview": "NOT_COMPLETED",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
