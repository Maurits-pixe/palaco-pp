"""Deterministic, non-authorizing verification plan for PP-RECOVERY-002.

Plans six manual checks per intake item. This never performs those checks,
confirms a reviewer, changes a gate, or executes an automated test.
"""
import hashlib
import json

from review_044_intake_assessment import assess_review_intake, MISSING_CONTROLS
from review_044_recovery_decision import REQUIREMENTS

ERROR = "PP_RECOVERY_002_VERIFICATION_PLAN_INVALID"

# Ordering expresses procedural prerequisites, NOT completed verification.
CHECKS = (
    ("ORIGINAL_EVIDENCE_BYTES_NOT_RECHECKED", (), "Compare original bytes with the intake SHA-256 reference."),
    ("SOURCE_PROVENANCE_NOT_ATTESTED", (1,), "Obtain independently verifiable source provenance."),
    ("SUBMITTER_IDENTITY_NOT_AUTHENTICATED", (), "Authenticate the claimed submitter through an independent channel."),
    ("REVIEWER_AUTHORITY_NOT_ESTABLISHED", (), "Authenticate and independently authorize a human reviewer."),
    ("SUBJECT_BINDING_NOT_ESTABLISHED", (2, 3), "Establish common-subject binding with independently sourced evidence."),
    ("INDEPENDENT_REVIEW_NOT_COMPLETED", (1, 2, 3, 4, 5), "Conduct documented review only after prerequisites are independently satisfied."),
)

GATE_PREREQUISITES = {
    "SOURCE_ATTESTATION": (1, 2),
    "CROSS_SOURCE_SUBJECT": (1, 2, 3, 5),
    "OWNER_AUTHORITY": (3, 4, 5),
    "RUNTIME_EXECUTION": (1, 2, 6),
    "HUMAN_REVIEW": (1, 2, 3, 4, 5, 6),
}


def prepare_verification_plan(
    decision_dossier_bytes: bytes,
    review_queue_bytes: bytes,
    intake_bytes: bytes,
) -> dict[str, object]:
    """Validate three original inputs; return all-gates-blocked workflow metadata."""
    try:
        assessment = assess_review_intake(
            decision_dossier_bytes, review_queue_bytes, intake_bytes
        )
        if (tuple(x[0] for x in CHECKS) != MISSING_CONTROLS
                or tuple(GATE_PREREQUISITES) != tuple(name for name, _ in REQUIREMENTS)):
            raise ValueError
        work_items = []
        for item in assessment["assessedItems"]:
            work_items.append({
                "intakeSequence": item["sequence"],
                "requestSequence": item["requestSequence"],
                "requirementId": item["requirementId"],
                "evidenceSha256": item["evidenceSha256"],
                "checks": [
                    {
                        "checkOrder": i,
                        "checkId": check_id,
                        "prerequisites": list(deps),
                        "instruction": description,
                        "status": "NOT_STARTED",
                        "verification": "NOT_VERIFIED",
                        "reviewerAuthority": "NOT_ESTABLISHED",
                    }
                    for i, (check_id, deps, description) in enumerate(CHECKS, 1)
                ],
                "gate": "BLOCKED",
            })
        gates = [
            {
                "requirementId": name,
                "prerequisiteCheckOrders": list(GATE_PREREQUISITES[name]),
                "status": "NOT_ESTABLISHED",
                "gate": "BLOCKED",
            }
            for name, _ in REQUIREMENTS
        ]
        return {
            "schema": "palaco.pp.recovery-002-verification-plan.v0",
            "reference": "PP-RECOVERY-002",
            "decisionDossierSha256": assessment["decisionDossierSha256"],
            "requestQueueSha256": assessment["requestQueueSha256"],
            "intakeSnapshotSha256": assessment["intakeSnapshotSha256"],
            "assessmentSha256": hashlib.sha256(json.dumps(
                assessment, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")).hexdigest(),
            "intakeCount": assessment["intakeCount"],
            "checkCount": len(work_items) * len(CHECKS),
            "workItems": work_items,
            "decisionGates": gates,
            "workflowStatus": "PREPARED_NOT_EXECUTED",
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
