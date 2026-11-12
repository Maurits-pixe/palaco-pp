"""PP-RECOVERY-002 offline human-review handoff manifest.

Produces references and unresolved checklist only. An unsigned manifest is
neither delivery, receipt, source attestation, reviewer authentication,
identity verification nor permission. No I/O or side effects.
"""
import hashlib
import json

from review_044_release_readiness import analyze_release_readiness
from review_044_recovery_status import build_recovery_status_report

ERROR = "PP_RECOVERY_002_HANDOFF_PACKAGE_INVALID"
_SOURCE_NAMES = (
    "decisionDossierSha256", "reviewQueueSha256", "reviewIntakeSha256",
    "verificationPlanSha256", "observationRegisterSha256",
)


def prepare_human_review_handoff(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes,
) -> dict[str, object]:
    """Strictly validate originals, emit a de-identified HOLD manifest."""
    try:
        readiness = analyze_release_readiness(
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes, observations_bytes
        )
        status = build_recovery_status_report(
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes, observations_bytes
        )
        if (readiness["overallReadiness"] != "NOT_READY"
                or readiness["blockedGateCount"] != 5
                or readiness["sourceFingerprints"] != status["sourceFingerprints"]
                or readiness["authorization"] != "HOLD"
                or readiness["accessDecision"] != "DENY"):
            raise ValueError
        files = [
            {"role": name, "sha256": readiness["sourceFingerprints"][name],
             "deliveryStatus": "NOT_DELIVERED", "sourceVerification": "NOT_VERIFIED"}
            for name in _SOURCE_NAMES
        ]
        requirements = [
            {
                "requirementId": item["requirementId"],
                "missingCheckIds": [x["checkId"] for x in item["missingChecks"]],
                "gate": "BLOCKED",
                "reviewStatus": "NOT_STARTED",
            }
            for item in readiness["gateReadiness"]
        ]
        return {
            "schema": "palaco.pp.recovery-002-human-review-handoff.v0",
            "reference": "PP-RECOVERY-002",
            "readinessCanonicalSha256": hashlib.sha256(json.dumps(
                readiness, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")).hexdigest(),
            "statusCanonicalSha256": hashlib.sha256(json.dumps(
                status, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")).hexdigest(),
            "files": files,
            "originalEvidenceIncluded": False,
            "originalEvidenceRetention": "REQUIRED_SEPARATELY",
            "globalBlockers": readiness["globalBlockers"],
            "requirements": requirements,
            "intendedRecipient": "INDEPENDENT_AUTHORIZED_HUMAN_REVIEWER_UNASSIGNED",
            "recipientAuthentication": "NOT_ESTABLISHED",
            "recipientAuthorization": "NOT_ESTABLISHED",
            "deliveryStatus": "NOT_DELIVERED",
            "receiptStatus": "NOT_ACKNOWLEDGED",
            "manifestProvenance": "UNSIGNED_LOCAL_DRAFT",
            "independentVerification": "NOT_VERIFIED",
            "subjectBinding": "NOT_ESTABLISHED",
            "humanReview": "NOT_COMPLETED",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, IndexError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
