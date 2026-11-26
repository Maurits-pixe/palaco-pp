"""Audit Evidence Readiness Matrix for PP-RECOVERY-002.

Strictly rebuilds the preceding audit contract from the original source
bytes. Maps each missing external proof to its responsible independent
role, prerequisite checks, blocking reason and next permitted request.
It never accepts evidence, performs independent verification or grants.
"""
import hashlib

from review_044_trust_decision_audit_contract import (
    prepare_trust_decision_audit_contract, AUDIT_EVIDENCE,
    RECONSTRUCTION, FAIL_CLOSED,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_AUDIT_EVIDENCE_READINESS_INVALID"
MAX_AUDIT_CONTRACT_BYTES = 64 * 1024

PREREQUISITES = (
    ("ORIGINAL_POLICY_AND_DECISION_BYTE_ATTESTATION",
     "REBUILD_ORIGINAL_POLICY_AND_CHANGE_CONTROL_BYTES"),
    ("INDEPENDENT_SIGNED_RECEIPT_AND_ISSUER_AUTHENTICATION",
     "AUTHENTICATE_INDEPENDENT_ISSUER_AND_SIGNER_TRUST_CHAIN"),
    ("EXTERNAL_REVIEWER_IDENTITY_SCOPE_REVOCATION_CHECK",
     "RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION"),
    ("SEPARATE_SIGNED_HUMAN_AUTHORITY_DECISION",
     "RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION"),
    ("TRUSTED_NONCE_LEDGER_AND_SIGNED_TIME_ANCHOR",
     "VERIFY_REPLAY_NONCE_AND_TRUSTED_CLOCK_WINDOW"),
    ("SIGNED_LOG_INCLUSION_AND_CONSISTENCY_WITNESSES",
     "VERIFY_APPEND_ONLY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY"),
    ("PINNED_KEY_EPOCH_AND_SIGNED_REVOCATION_HISTORY",
     "VERIFY_KEY_REVOCATION_AND_SIGNED_ROTATION_HISTORY"),
    ("INDEPENDENT_RELEASE_OPERATOR_ROLLBACK_ATTESTATION",
     "VERIFY_INDEPENDENT_DEPLOYMENT_AND_ROLLBACK_APPROVAL"),
)
REVIEW_SEQUENCE = (
    "REQUEST_ORIGINAL_EXTERNAL_EVIDENCE_FROM_INDEPENDENT_CUSTODIAN",
    "AUTHENTICATE_EXTERIOR_SIGNER_AND_ROLE_IN_TRUSTED_SYSTEM",
    "VERIFY_SIGNED_BYTES_AND_EXACT_DECISION_PROTOCOL_BINDING",
    "VERIFY_REPLAY_REVOCATION_AND_TRUSTED_TIMESTAMP",
    "VERIFY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY",
    "RECORD_INDEPENDENT_REVIEW_OUTSIDE_THIS_LOCAL_MODULE",
    "REQUIRE_SEPARATE_HUMAN_AND_DEPLOYMENT_AUTHORIZATION",
)


def prepare_audit_evidence_readiness_matrix(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes, audit_contract_bytes: bytes,
) -> dict[str, object]:
    """Create unsigned readiness requirements; all eight remain blocked."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        actual = _loads(audit_contract_bytes, MAX_AUDIT_CONTRACT_BYTES)
        expected = prepare_trust_decision_audit_contract(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
            review_dossier_bytes, decision_protocol_bytes,
        )
        if not _strict_equal(actual, expected):
            raise ValueError
        if (actual["auditVerification"] != "NOT_PERFORMED"
                or actual["signedAuditReceipt"] != "NOT_AVAILABLE"
                or actual["changeApplied"] is not False
                or actual["trustedIssuerCount"] != 0
                or actual["allowedAlgorithms"] != []
                or actual["authorization"] != "HOLD"
                or actual["accessDecision"] != "DENY"
                or len(actual["requiredExternalEvidence"]) != len(AUDIT_EVIDENCE)
                or len(actual["reconstructionSteps"]) != len(RECONSTRUCTION)
                or len(actual["failureRules"]) != len(FAIL_CLOSED)):
            raise ValueError
        rows = []
        for i, (evidence, role) in enumerate(AUDIT_EVIDENCE, 1):
            prerequisite, verification_step = PREREQUISITES[i - 1]
            rows.append({
                "rowId": "AUD-E%02d" % i,
                "evidenceId": evidence,
                "requiredIndependentRole": role,
                "missingProof": prerequisite,
                "requiredExternalVerificationStep": verification_step,
                "evidenceStatus": "NOT_PROVIDED",
                "signerAuthentication": "NOT_ESTABLISHED",
                "independentVerification": "NOT_PERFORMED",
                "blocker": "MISSING_EXTERNALLY_ATTESTED_EVIDENCE",
                "nextPermittedAction": "REQUEST_EVIDENCE_FOR_EXTERNAL_REVIEW_ONLY",
                "gate": "BLOCKED",
                "decision": "DENY",
            })
        return {
            "schema": "palaco.pp.recovery-002-audit-evidence-readiness-matrix.v0",
            "reference": "PP-RECOVERY-002",
            "auditContractSha256": hashlib.sha256(audit_contract_bytes).hexdigest(),
            "decisionProtocolSha256": actual["decisionProtocolSha256"],
            "sourceBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "matrixProvenance": "UNSIGNED_LOCAL_REQUIREMENTS_NOT_EVIDENCE",
            "evidenceRows": rows,
            "requiredEvidenceCount": len(rows),
            "externallyVerifiedEvidenceCount": 0,
            "blockedEvidenceCount": len(rows),
            "reconstructionReadiness": [
                {"stepId": step, "status": "NOT_PERFORMED", "gate": "BLOCKED"}
                for step in RECONSTRUCTION
            ],
            "independentReviewSequence": [
                {"order": i, "stepId": step, "status": "NOT_STARTED"}
                for i, step in enumerate(REVIEW_SEQUENCE, 1)
            ],
            "failurePolicy": [
                {"reason": failure, "decision": "DENY", "authorityEffect": "NONE"}
                for failure in FAIL_CLOSED
            ],
            "auditEvidenceAcceptance": "PROHIBITED",
            "trustedAuditService": "NOT_CONFIGURED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "independentVerification": "NOT_VERIFIED",
            "humanDecision": "NOT_COMPLETED",
            "deploymentDecision": "NOT_AUTHORIZED",
            "changeApplied": False,
            "trustedIssuerCount": 0,
            "allowedAlgorithms": [],
            "keyMaterial": "NOT_PRESENT",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
