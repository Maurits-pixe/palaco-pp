"""Manual Release Verification Execution Plan for PP-RECOVERY-002.

Constructs a request-only checklist from eighteen byte-bound artifacts.
This plan is NOT verification evidence; no checklist item can become PASS
through this module. No I/O, test execution, authority or session creation.
"""
import hashlib

from review_044_release_readiness_cockpit import prepare_release_readiness_cockpit
from review_044_release_evidence_matrix import REQUIREMENTS
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_RELEASE_EXECUTION_PLAN_INVALID"
MAX_COCKPIT_BYTES = 32 * 1024

PROCEDURE = (
    "RECORD_ORIGINAL_ARTIFACT_FINGERPRINTS",
    "REQUEST_EVIDENCE_FROM_INDEPENDENT_CUSTODIAN",
    "CONFIRM_REVIEWER_IDENTITY_IN_EXTERNAL_TRUSTED_SYSTEM",
    "CHECK_SCOPE_REVOCATION_AND_SEPARATION_OF_DUTIES",
    "VERIFY_EVIDENCE_WITH_INDEPENDENT_TOOLS",
    "RECORD_UNSIGNED_LOCAL_OBSERVATIONS_SEPARATELY",
    "ESCALATE_TO_AUTHORIZED_HUMAN_REVIEW_OUTSIDE_THIS_TOOL",
)


def prepare_release_verification_execution_plan(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes, revocation_bytes: bytes,
    assurance_bytes: bytes, compatibility_bytes: bytes, impact_bytes: bytes,
    release_manifest_bytes: bytes, matrix_bytes: bytes, cockpit_bytes: bytes,
) -> dict[str, object]:
    """Regenerate and strictly bind the cockpit; emit only NOT_STARTED tasks."""
    try:
        sources = (
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes, interface_bytes,
            transition_bytes, revocation_bytes, assurance_bytes,
            compatibility_bytes, impact_bytes, release_manifest_bytes,
            matrix_bytes,
        )
        supplied = _loads(cockpit_bytes, MAX_COCKPIT_BYTES)
        expected = prepare_release_readiness_cockpit(*sources)
        if not _strict_equal(supplied, expected):
            raise ValueError
        if (supplied["releaseReadiness"] != "NOT_READY"
                or supplied["authorization"] != "HOLD"
                or supplied["accessDecision"] != "DENY"
                or supplied["counts"]["approvedGates"] != 0):
            raise ValueError
        if [row["gateId"] for row in supplied["releaseGateRows"]] != [
                gate for gate, _, _ in REQUIREMENTS]:
            raise ValueError
        checks = []
        for gate_order, (gate, evidence_ids, role) in enumerate(REQUIREMENTS, 1):
            for evidence_order, evidence_id in enumerate(evidence_ids, 1):
                checks.append({
                    "checkId": "RG%02d-E%02d" % (gate_order, evidence_order),
                    "releaseGate": gate,
                    "evidenceId": evidence_id,
                    "requiredIndependentRole": role,
                    "step": "COLLECT_THEN_VERIFY_EXTERNALLY",
                    "execution": "NOT_STARTED",
                    "evidenceCapture": "NOT_PROVIDED",
                    "independentVerification": "NOT_PERFORMED",
                    "reviewerAuthentication": "NOT_ESTABLISHED",
                    "reviewerAuthority": "NOT_ESTABLISHED",
                    "gate": "BLOCKED",
                    "decision": "DENY",
                })
        return {
            "schema": "palaco.pp.recovery-002-release-execution-plan.v0",
            "reference": "PP-RECOVERY-002",
            "readinessCockpitSha256": hashlib.sha256(cockpit_bytes).hexdigest(),
            "releaseEvidenceMatrixSha256": supplied["releaseEvidenceMatrixSha256"],
            "planProvenance": "UNSIGNED_LOCAL_REQUIREMENTS_ONLY",
            "executionProcedure": [
                {"order": i, "step": step, "status": "NOT_STARTED"}
                for i, step in enumerate(PROCEDURE, 1)
            ],
            "verificationChecks": checks,
            "checkCount": len(checks),
            "gateSummary": [
                {"releaseGate": gate, "requiredIndependentRole": role,
                 "checkCount": len(evidence_ids), "gate": "BLOCKED",
                 "reviewStatus": "NOT_COMPLETED"}
                for gate, evidence_ids, role in REQUIREMENTS
            ],
            "futureObservationContract": {
                "recordType": "SELF_REPORTED_LOCAL_OBSERVATION_ONLY",
                "evidenceHash": "REQUIRED_IF_LATER_RECORDED",
                "externalSignature": "NOT_VERIFIED",
                "roleClaims": "UNAUTHENTICATED",
                "allowedEffect": "NONE",
                "export": "SEPARATE_CREATE_ONLY_SNAPSHOT",
            },
            "independentVerification": "NOT_VERIFIED",
            "humanReview": "NOT_COMPLETED",
            "releaseReadiness": "NOT_READY",
            "runtimeTests": "NOT_EXECUTED",
            "softwareBundle": "NOT_CREATED",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
