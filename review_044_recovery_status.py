"""PP-RECOVERY-002 central HOLD status report, offline and non-authoritative.

The five original JSON sources are strictly revalidated via the existing
cockpit contract. This produces an owner-oriented *action queue*, not
an identity verdict, reviewer signoff, or completed verification.
"""
import hashlib

from review_044_recovery_cockpit import prepare_recovery_cockpit
from review_044_recovery_decision import REQUIREMENTS
from review_044_verification_plan import CHECKS, GATE_PREREQUISITES

ERROR = "PP_RECOVERY_002_STATUS_REPORT_INVALID"
_NEXT = (
    ("PRESERVE_ORIGINALS", "Preserve five original local JSON files and any original evidence bytes."),
    ("RECHECK_EVIDENCE_BYTES", "Independently compare each original evidence file to its recorded SHA-256."),
    ("ATTEST_SOURCE_ORIGIN", "Obtain independent source provenance and execution evidence."),
    ("AUTHENTICATE_SUBMITTER", "Authenticate the source and submitter using an independent channel."),
    ("AUTHENTICATE_REVIEWER", "Verify reviewer identity and authority independently."),
    ("ESTABLISH_SUBJECT_BINDING", "Resolve subject binding between PALACO PHONE and relevant evidence."),
    ("RECORD_HUMAN_REVIEW", "Document authorized human review after preceding controls are satisfied."),
    ("REASSESS_MANUAL_HOLD", "Reassess HOLD only in a separate authorized workflow, never in this report."),
)


def build_recovery_status_report(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes,
) -> dict[str, object]:
    """Aggregate unresolved review work while preserving all five blocked gates."""
    try:
        cockpit = prepare_recovery_cockpit(
            dossier_bytes, queue_bytes, intake_bytes,
            plan_bytes, observations_bytes
        )
        gates = cockpit["decisionGates"]
        if (len(gates) != len(REQUIREMENTS)
                or any(g["requirementId"] != name or g["gate"] != "BLOCKED"
                       or g["verification"] != "NOT_VERIFIED"
                       for g, (name, _) in zip(gates, REQUIREMENTS))):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-status-report.v0",
            "reference": "PP-RECOVERY-002",
            "sourceFingerprints": cockpit["sources"],
            "cockpitCanonicalSha256": hashlib.sha256(
                __import__("json").dumps(
                    cockpit, ensure_ascii=False, sort_keys=True,
                    separators=(",", ":")
                ).encode("utf-8")
            ).hexdigest(),
            "sourceScope": "FIVE_ORIGINAL_LOCAL_FILES_STRICT_INTERNAL_CONSISTENCY",
            "counts": {
                "reviewRequests": cockpit["requestCount"],
                "intakeReferences": cockpit["intakeCount"],
                "plannedChecks": cockpit["plannedCheckCount"],
                "unsignedObservations": cockpit["observationCount"],
                "reportedBlockers": cockpit["observationKinds"]["BLOCKER_REPORTED"],
            },
            "evidenceChecks": [
                {"order": order, "checkId": check_id,
                 "dependsOn": list(deps), "status": "NOT_STARTED",
                 "verification": "NOT_VERIFIED"}
                for order, (check_id, deps, _) in enumerate(CHECKS, 1)
            ],
            "decisionGates": [
                {"requirementId": name, "prerequisiteCheckOrders": list(GATE_PREREQUISITES[name]),
                 "evidenceStatus": "NOT_ESTABLISHED", "gate": "BLOCKED"}
                for name, _ in REQUIREMENTS
            ],
            "nextPermittedActions": [
                {"priority": i, "actionId": key, "description": description,
                 "execution": "MANUAL_FUTURE_ACTION_ONLY", "authorizationEffect": "NONE"}
                for i, (key, description) in enumerate(_NEXT, 1)
            ],
            "independentVerification": "NOT_VERIFIED",
            "sourceAuthenticity": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "subjectBinding": "NOT_ESTABLISHED",
            "historicalImmutability": "NOT_ESTABLISHED",
            "humanReview": "NOT_COMPLETED",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "reviewDecision": "HOLD",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
