"""PP-RECOVERY-002 Audit Evidence Collection Plan: preparation only.

Reconstructs and type-exactly binds the eight-row readiness matrix. It
specifies safe external collection, byte integrity, custody and reviewer
handoff for each missing item. Does not collect, upload, verify, or authorize.
"""
import hashlib
from review_044_audit_evidence_readiness_matrix import (
    prepare_audit_evidence_readiness_matrix, PREREQUISITES, REVIEW_SEQUENCE,
)
from review_044_trust_decision_audit_contract import AUDIT_EVIDENCE
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_AUDIT_EVIDENCE_COLLECTION_PLAN_INVALID"
MAX_MATRIX_BYTES = 64 * 1024

COLLECTION_ACTIONS = (
    "REQUEST_SIGNED_SOURCE_BYTE_ATTESTATION_FROM_EXTERNAL_CUSTODIAN",
    "REQUEST_ORIGINAL_SIGNED_RECEIPT_AND_TRUST_ANCHOR",
    "REQUEST_INDEPENDENT_REVIEWER_IDENTITY_SCOPE_AND_REVOCATION",
    "REQUEST_SEPARATE_CANONICAL_SIGNED_HUMAN_DECISION",
    "REQUEST_NONCE_CONSUMPTION_PROOF_AND_TRUSTED_TIMESTAMP",
    "REQUEST_INDEPENDENT_LOG_INCLUSION_AND_CONSISTENCY_PROOFS",
    "REQUEST_SIGNED_KEY_EPOCH_AND_REVOCATION_HISTORY",
    "REQUEST_SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_EVIDENCE",
)
CUSTODY_RULES = (
    "ORIGINAL_BYTES_REMAIN_WITH_AUTHORIZED_EXTERNAL_CUSTODIAN",
    "NO_PRIVATE_KEYS_OR_SECRET_BYTES_IN_LOCAL_SNAPSHOT",
    "EXACT_SOURCE_AND_AUDIT_CONTRACT_HASH_BINDING_REQUIRED",
    "INDEPENDENT_TRUSTED_SIGNATURE_AND_PROVENANCE_CHECK_REQUIRED",
    "AUTHORIZED_REVIEWER_ROLE_AND_REVOCATION_CHECK_REQUIRED",
    "FRESH_NONCE_TRUSTED_TIME_AND_REPLAY_CHECK_REQUIRED",
    "EXTERNAL_SIGNED_AUDIT_INCLUSION_CHECK_REQUIRED",
    "SEPARATE_HUMAN_AND_DEPLOYMENT_DECISIONS_REQUIRED",
)


def prepare_audit_evidence_collection_plan(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes, audit_contract_bytes: bytes,
    readiness_matrix_bytes: bytes,
) -> dict[str, object]:
    """Return a blocked request plan; no evidence enters the trust boundary."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        supplied = _loads(readiness_matrix_bytes, MAX_MATRIX_BYTES)
        expected = prepare_audit_evidence_readiness_matrix(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
            review_dossier_bytes, decision_protocol_bytes, audit_contract_bytes,
        )
        if not _strict_equal(supplied, expected):
            raise ValueError
        if (supplied["requiredEvidenceCount"] != len(AUDIT_EVIDENCE)
                or supplied["externallyVerifiedEvidenceCount"] != 0
                or supplied["blockedEvidenceCount"] != len(AUDIT_EVIDENCE)
                or supplied["auditEvidenceAcceptance"] != "PROHIBITED"
                or supplied["authorization"] != "HOLD"
                or supplied["accessDecision"] != "DENY"
                or supplied["changeApplied"] is not False):
            raise ValueError
        collection_rows = []
        for index, row in enumerate(supplied["evidenceRows"]):
            if (row["rowId"] != "AUD-E%02d" % (index + 1)
                    or row["evidenceId"] != AUDIT_EVIDENCE[index][0]
                    or row["requiredIndependentRole"] != AUDIT_EVIDENCE[index][1]
                    or row["missingProof"] != PREREQUISITES[index][0]
                    or row["gate"] != "BLOCKED"
                    or row["decision"] != "DENY"):
                raise ValueError
            collection_rows.append({
                "rowId": row["rowId"],
                "evidenceId": row["evidenceId"],
                "independentCustodianRole": row["requiredIndependentRole"],
                "requiredMissingProof": row["missingProof"],
                "externalVerificationStep": row["requiredExternalVerificationStep"],
                "collectionRequest": COLLECTION_ACTIONS[index],
                "evidenceBytes": "NOT_COLLECTED",
                "externalEvidenceReceipt": "NOT_AVAILABLE",
                "reviewerAuthentication": "NOT_ESTABLISHED",
                "evidenceProvenance": "NOT_VERIFIED",
                "requestState": "NOT_SENT",
                "nextPermittedAction": "PREPARE_EXTERNAL_REQUEST_ONLY",
                "gate": "BLOCKED",
                "decision": "DENY",
            })
        return {
            "schema": "palaco.pp.recovery-002-audit-evidence-collection-plan.v0",
            "reference": "PP-RECOVERY-002",
            "readinessMatrixSha256": hashlib.sha256(readiness_matrix_bytes).hexdigest(),
            "auditContractSha256": supplied["auditContractSha256"],
            "sourceBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "collectionProvenance": "UNSIGNED_LOCAL_REQUEST_PLAN_ONLY",
            "collectionRows": collection_rows,
            "requiredCollectionCount": len(collection_rows),
            "evidenceCollectedCount": 0,
            "externallyVerifiedEvidenceCount": 0,
            "blockedCollectionCount": len(collection_rows),
            "custodyRules": [
                {"order": i, "ruleId": rule, "status": "NOT_ESTABLISHED"}
                for i, rule in enumerate(CUSTODY_RULES, 1)
            ],
            "externalReviewSequence": [
                {"order": i, "stepId": step, "status": "NOT_STARTED"}
                for i, step in enumerate(REVIEW_SEQUENCE, 1)
            ],
            "evidenceCollection": "NOT_EXECUTED",
            "externalRequestDelivery": "NOT_SENT",
            "evidenceAcceptance": "PROHIBITED",
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
