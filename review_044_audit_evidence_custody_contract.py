"""Audit Evidence Custody Contract: requirements only, never possession.

Strictly reconstructs the exact prior collection plan from original source
bytes and returns unsigned custody, integrity, access, transfer and retention
requirements. It does NOT collect, store, transmit, authenticate, or approve
any original evidence or credentials.
"""
import hashlib

from review_044_audit_evidence_collection_plan import (
    prepare_audit_evidence_collection_plan, COLLECTION_ACTIONS, CUSTODY_RULES,
)
from review_044_trust_decision_audit_contract import AUDIT_EVIDENCE
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_AUDIT_EVIDENCE_CUSTODY_CONTRACT_INVALID"
MAX_COLLECTION_PLAN_BYTES = 64 * 1024

CUSTODY_CONTROLS = (
    "INDEPENDENT_CUSTODIAN_IDENTITY_AND_SCOPE_ATTESTATION",
    "ORIGINAL_BYTE_INTEGRITY_AND_SIGNED_HASH_BINDING",
    "ENCRYPTED_IN_TRANSIT_AND_AT_REST_WITH_APPROVED_KEY_CUSTODY",
    "LEAST_PRIVILEGE_ACCESS_AND_SEPARATION_OF_DUTIES",
    "IMMUTABLE_CHAIN_OF_CUSTODY_AND_INDEPENDENT_AUDIT_LOG",
    "SIGNED_TRANSFER_RECEIPT_AND_AUDIENCE_NONCE_BINDING",
    "DOCUMENTED_RETENTION_AND_AUTHORIZED_DISPOSAL",
    "REVOCATION_KEY_COMPROMISE_AND_EMERGENCY_DENY",
)
TRANSFER_CHECKPOINTS = (
    "AUTHENTICATE_SENDING_CUSTODIAN_IN_EXTERNAL_TRUST_SYSTEM",
    "VERIFY_ORIGINAL_EVIDENCE_BYTES_AND_SOURCE_PROVENANCE",
    "VALIDATE_EXACT_COLLECTION_PLAN_AND_AUDIT_HASHES",
    "VERIFY_RECEIVER_IDENTITY_ROLE_SCOPE_AND_KEY_REVOCATION",
    "USE_SIGNED_CANONICAL_TRANSFER_ENVELOPE",
    "VERIFY_FRESH_NONCE_TRUSTED_TIME_AND_REPLAY_LEDGER",
    "ANCHOR_SIGNED_RECEIPT_IN_EXTERNAL_APPEND_ONLY_LOG",
    "REQUIRE_SEPARATE_AUTHORIZED_REVIEW_BEFORE_ANY_ACCEPTANCE",
)
FAIL_CLOSED = (
    "CUSTODIAN_IDENTITY_UNVERIFIED",
    "SOURCE_OR_PAYLOAD_HASH_MISMATCH",
    "ENCRYPTION_OR_KEY_CUSTODY_NOT_VERIFIED",
    "ACCESS_SCOPE_OR_SEPARATION_OF_DUTIES_FAILED",
    "CHAIN_OF_CUSTODY_GAP",
    "SIGNED_TRANSFER_RECEIPT_MISSING",
    "REPLAY_REVOCATION_OR_TRUSTED_TIME_FAILURE",
    "UNAPPROVED_RETENTION_OR_DISPOSAL",
)


def prepare_audit_evidence_custody_contract(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes, audit_contract_bytes: bytes,
    readiness_matrix_bytes: bytes, collection_plan_bytes: bytes,
) -> dict[str, object]:
    """Return zero-possession, zero-authorization custody requirements."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        supplied = _loads(collection_plan_bytes, MAX_COLLECTION_PLAN_BYTES)
        expected = prepare_audit_evidence_collection_plan(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
            review_dossier_bytes, decision_protocol_bytes, audit_contract_bytes,
            readiness_matrix_bytes,
        )
        if not _strict_equal(supplied, expected):
            raise ValueError
        if (supplied["evidenceCollectedCount"] != 0
                or supplied["externallyVerifiedEvidenceCount"] != 0
                or supplied["requiredCollectionCount"] != len(AUDIT_EVIDENCE)
                or supplied["externalRequestDelivery"] != "NOT_SENT"
                or supplied["evidenceAcceptance"] != "PROHIBITED"
                or supplied["authorization"] != "HOLD"
                or supplied["accessDecision"] != "DENY"
                or supplied["changeApplied"] is not False
                or len(supplied["custodyRules"]) != len(CUSTODY_RULES)):
            raise ValueError
        records = []
        for position, row in enumerate(supplied["collectionRows"], 1):
            if (row["rowId"] != "AUD-E%02d" % position
                    or row["evidenceId"] != AUDIT_EVIDENCE[position - 1][0]
                    or row["independentCustodianRole"] != AUDIT_EVIDENCE[position - 1][1]
                    or row["collectionRequest"] != COLLECTION_ACTIONS[position - 1]
                    or row["evidenceBytes"] != "NOT_COLLECTED"
                    or row["requestState"] != "NOT_SENT"
                    or row["gate"] != "BLOCKED"
                    or row["decision"] != "DENY"):
                raise ValueError
            records.append({
                "rowId": row["rowId"],
                "evidenceId": row["evidenceId"],
                "requiredIndependentCustodianRole": row["independentCustodianRole"],
                "requestedExternalSource": row["collectionRequest"],
                "originalBytesLocation": "EXTERNAL_CUSTODIAN_ONLY_NOT_ACCESSED",
                "custodianAuthentication": "NOT_ESTABLISHED",
                "originalByteHash": "NOT_AVAILABLE",
                "integrityVerification": "NOT_PERFORMED",
                "accessGrant": "NONE",
                "custodyChain": "NOT_ESTABLISHED",
                "signedTransferReceipt": "NOT_AVAILABLE",
                "retentionApproval": "NOT_ESTABLISHED",
                "transferStatus": "NOT_INITIATED",
                "evidencePossession": "NONE",
                "gate": "BLOCKED",
                "decision": "DENY",
            })
        return {
            "schema": "palaco.pp.recovery-002-audit-evidence-custody-contract.v0",
            "reference": "PP-RECOVERY-002",
            "collectionPlanSha256": hashlib.sha256(collection_plan_bytes).hexdigest(),
            "readinessMatrixSha256": supplied["readinessMatrixSha256"],
            "auditContractSha256": supplied["auditContractSha256"],
            "binding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "provenance": "UNSIGNED_LOCAL_CUSTODY_REQUIREMENTS_NOT_EVIDENCE",
            "custodyRecords": records,
            "requiredCustodyCount": len(records),
            "externallyHeldEvidenceCount": 0,
            "locallyReceivedEvidenceCount": 0,
            "transferredEvidenceCount": 0,
            "verifiedEvidenceCount": 0,
            "securityControls": [
                {"order": i, "controlId": name,
                 "status": "NOT_ESTABLISHED", "verification": "NOT_PERFORMED"}
                for i, name in enumerate(CUSTODY_CONTROLS, 1)
            ],
            "transferCheckpoints": [
                {"order": i, "checkpointId": name, "status": "NOT_STARTED",
                 "gate": "BLOCKED"}
                for i, name in enumerate(TRANSFER_CHECKPOINTS, 1)
            ],
            "denialConditions": [
                {"reason": reason, "decision": "DENY", "authorityEffect": "NONE"}
                for reason in FAIL_CLOSED
            ],
            "evidenceCustody": "NOT_ESTABLISHED",
            "evidenceTransfer": "NOT_INITIATED",
            "evidenceAcceptance": "PROHIBITED",
            "originalEvidenceStorage": "NONE",
            "credentialOrKeyStorage": "NONE",
            "externalCustodian": "NOT_AUTHENTICATED",
            "recipientAuthority": "NOT_ESTABLISHED",
            "trustedAuditService": "NOT_CONFIGURED",
            "independentVerification": "NOT_VERIFIED",
            "humanDecision": "NOT_COMPLETED",
            "deploymentDecision": "NOT_AUTHORIZED",
            "changeApplied": False,
            "trustedIssuerCount": 0,
            "allowedAlgorithms": [],
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
