"""Offline release-readiness *gap analysis* for PP-RECOVERY-002.

This is NOT a release decision. Strictly checks five original files via
the existing status-report contract. Evidence and reviewer claims never
satisfy gates. Always HOLD/DENY/NOT_AUTHORIZED.
"""
import hashlib
import json

from review_044_recovery_status import build_recovery_status_report
from review_044_verification_plan import CHECKS, GATE_PREREQUISITES
from review_044_recovery_decision import REQUIREMENTS

ERROR = "PP_RECOVERY_002_READINESS_INVALID"
GLOBAL_BLOCKERS = (
    "ORIGINAL_SOURCE_ATTESTATION_ABSENT",
    "SUBMITTER_AUTHENTICATION_ABSENT",
    "REVIEWER_IDENTITY_AND_AUTHORITY_ABSENT",
    "CROSS_SOURCE_SUBJECT_BINDING_ABSENT",
    "INDEPENDENT_HUMAN_REVIEW_NOT_COMPLETED",
    "IMMUTABLE_AUDIT_PROVENANCE_ABSENT",
)
_NEXT_ACTIONS = {
    "SOURCE_ATTESTATION": "OBTAIN_INDEPENDENT_SOURCE_ATTESTATION",
    "CROSS_SOURCE_SUBJECT": "ESTABLISH_INDEPENDENT_SUBJECT_BINDING",
    "OWNER_AUTHORITY": "AUTHENTICATE_OWNER_AND_REVIEWER_SEPARATELY",
    "RUNTIME_EXECUTION": "ATTEST_ORIGINAL_RUNTIME_EXECUTION",
    "HUMAN_REVIEW": "COMPLETE_AUTHORIZED_HUMAN_REVIEW_OUTSIDE_THIS_MODULE",
}


def analyze_release_readiness(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes,
) -> dict[str, object]:
    """Return incomplete prerequisites, not readiness or authorization."""
    try:
        status = build_recovery_status_report(
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes, observations_bytes
        )
        gates = status["decisionGates"]
        if (len(gates) != len(REQUIREMENTS)
                or len(status["evidenceChecks"]) != len(CHECKS)
                or status["reviewDecision"] != "HOLD"
                or status["accessDecision"] != "DENY"):
            raise ValueError
        details = []
        for gate, (name, description) in zip(gates, REQUIREMENTS):
            required = tuple(GATE_PREREQUISITES[name])
            if (gate["requirementId"] != name
                    or gate["prerequisiteCheckOrders"] != list(required)
                    or gate["evidenceStatus"] != "NOT_ESTABLISHED"
                    or gate["gate"] != "BLOCKED"):
                raise ValueError
            missing = []
            for order in required:
                check = status["evidenceChecks"][order - 1]
                if (check["order"] != order
                        or check["checkId"] != CHECKS[order - 1][0]
                        or check["status"] != "NOT_STARTED"
                        or check["verification"] != "NOT_VERIFIED"):
                    raise ValueError
                missing.append({
                    "checkOrder": order,
                    "checkId": check["checkId"],
                    "status": "NOT_STARTED",
                    "verification": "NOT_VERIFIED",
                })
            details.append({
                "requirementId": name,
                "description": description,
                "missingChecks": missing,
                "missingCount": len(missing),
                "nextManualAction": _NEXT_ACTIONS[name],
                "gate": "BLOCKED",
                "readiness": "NOT_READY",
            })
        return {
            "schema": "palaco.pp.recovery-002-release-readiness.v0",
            "reference": "PP-RECOVERY-002",
            "statusReportCanonicalSha256": hashlib.sha256(json.dumps(
                status, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")).hexdigest(),
            "sourceFingerprints": status["sourceFingerprints"],
            "reviewRequests": status["counts"]["reviewRequests"],
            "intakeReferences": status["counts"]["intakeReferences"],
            "unsignedObservations": status["counts"]["unsignedObservations"],
            "globalBlockers": list(GLOBAL_BLOCKERS),
            "gateReadiness": details,
            "blockedGateCount": len(details),
            "overallReadiness": "NOT_READY",
            "manualDecision": "REQUIRED_OUTSIDE_THIS_MODULE",
            "sourceAuthenticity": "NOT_ESTABLISHED",
            "subjectBinding": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "independentVerification": "NOT_VERIFIED",
            "humanReview": "NOT_COMPLETED",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
