"""Custody Transfer Verification Protocol: unsigned requirements, no transfer.

Reconstructs the 18-source PP-RECOVERY-002 chain and the exact preceding
custody contract before specifying external signatures, integrity, nonce,
recipient authorization, and audit receipt requirements. This module is
not a verifier, receiver, sender, or authority service.
"""
import hashlib

from review_044_audit_evidence_custody_contract import (
    prepare_audit_evidence_custody_contract, CUSTODY_CONTROLS,
    TRANSFER_CHECKPOINTS, FAIL_CLOSED,
)
from review_044_trust_decision_audit_contract import AUDIT_EVIDENCE
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_CUSTODY_TRANSFER_VERIFICATION_INVALID"
MAX_CUSTODY_CONTRACT_BYTES = 64 * 1024

ENVELOPE_FIELDS = (
    "CANONICAL_TRANSFER_PROTOCOL_VERSION",
    "EXACT_CUSTODY_CONTRACT_AND_COLLECTION_HASHES",
    "EVIDENCE_ROW_ID_AND_ORIGINAL_BYTES_SHA256",
    "SENDING_CUSTODIAN_TRUSTED_SUBJECT_AND_SCOPE",
    "RECEIVING_CUSTODIAN_TRUSTED_SUBJECT_AND_SCOPE",
    "ISSUER_KEY_ID_AND_APPROVED_SIGNATURE_ALGORITHM",
    "AUDIENCE_PURPOSE_AND_SINGLE_USE_NONCE",
    "TRUSTED_ISSUED_AT_AND_EXPIRES_AT",
    "SIGNER_REVOCATION_AND_KEY_EPOCH_PROOF",
    "ENCRYPTED_TRANSFER_CHANNEL_AND_KEY_CUSTODY_ATTESTATION",
    "DETACHED_SIGNATURE_OVER_CANONICAL_ENVELOPE",
    "INDEPENDENT_APPEND_ONLY_LOG_INCLUSION_PROOF",
    "RECIPIENT_SIGNED_ACK_BOUND_TO_EXACT_ENVELOPE",
    "SEPARATE_AUTHORIZED_HUMAN_ACCEPTANCE_DECISION",
)
TRANSFER_STAGES = (
    ("PREPARE_TRANSFER_INTENT", "NO_EVIDENCE_BYTES_IN_LOCAL_MODULE"),
    ("VERIFY_SENDER_AND_EVIDENCE", "INDEPENDENT_EXTERNAL_SOURCE_VERIFIER"),
    ("VERIFY_RECEIVER_AND_CHANNEL", "INDEPENDENT_RECIPIENT_AUTHENTICATION"),
    ("VERIFY_SIGNED_TRANSFER_AND_REPLAY", "TRUSTED_SIGNATURE_AND_NONCE_LEDGER"),
    ("VERIFY_EXTERNAL_AUDIT_RECEIPT", "IMMUTABLE_INDEPENDENT_AUDIT_SERVICE"),
    ("REQUIRE_SEPARATE_ACCEPTANCE", "AUTHORIZED_HUMAN_REVIEW_REQUIRED"),
)
ADDITIONAL_FAILURES = (
    "MISSING_OR_MALFORMED_TRANSFER_ENVELOPE",
    "SENDER_RECEIVER_AUDIENCE_OR_SCOPE_MISMATCH",
    "MISSING_OR_INVALID_RECIPIENT_ACKNOWLEDGEMENT",
    "NONCE_REPLAY_OR_ATOMIC_LEDGER_UNAVAILABLE",
    "UNTRUSTED_ISSUER_KEY_OR_SIGNATURE_ALGORITHM",
    "ABSENT_SEPARATE_EVIDENCE_ACCEPTANCE_DECISION",
)


def prepare_custody_transfer_verification_protocol(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes, audit_contract_bytes: bytes,
    readiness_matrix_bytes: bytes, collection_plan_bytes: bytes,
    custody_contract_bytes: bytes,
) -> dict[str, object]:
    """Produce a fail-closed specification with zero receipts or trusted transfers."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        supplied = _loads(custody_contract_bytes, MAX_CUSTODY_CONTRACT_BYTES)
        expected = prepare_audit_evidence_custody_contract(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
            review_dossier_bytes, decision_protocol_bytes, audit_contract_bytes,
            readiness_matrix_bytes, collection_plan_bytes,
        )
        if not _strict_equal(supplied, expected):
            raise ValueError
        if (supplied["locallyReceivedEvidenceCount"] != 0
                or supplied["transferredEvidenceCount"] != 0
                or supplied["verifiedEvidenceCount"] != 0
                or supplied["evidenceTransfer"] != "NOT_INITIATED"
                or supplied["evidenceAcceptance"] != "PROHIBITED"
                or supplied["authorization"] != "HOLD"
                or supplied["accessDecision"] != "DENY"
                or len(supplied["custodyRecords"]) != len(AUDIT_EVIDENCE)
                or len(supplied["securityControls"]) != len(CUSTODY_CONTROLS)
                or len(supplied["transferCheckpoints"]) != len(TRANSFER_CHECKPOINTS)):
            raise ValueError
        records = []
        for i, row in enumerate(supplied["custodyRecords"], 1):
            evidence_id, role = AUDIT_EVIDENCE[i - 1]
            if (row["rowId"] != "AUD-E%02d" % i
                    or row["evidenceId"] != evidence_id
                    or row["requiredIndependentCustodianRole"] != role
                    or row["originalByteHash"] != "NOT_AVAILABLE"
                    or row["signedTransferReceipt"] != "NOT_AVAILABLE"
                    or row["evidencePossession"] != "NONE"
                    or row["gate"] != "BLOCKED"
                    or row["decision"] != "DENY"):
                raise ValueError
            records.append({
                "rowId": row["rowId"],
                "evidenceId": evidence_id,
                "requiredIndependentCustodianRole": role,
                "originalEvidenceDigest": "NOT_AVAILABLE",
                "senderAuthentication": "NOT_ESTABLISHED",
                "recipientAuthentication": "NOT_ESTABLISHED",
                "signedEnvelope": "NOT_PRESENT",
                "recipientSignedAcknowledgement": "NOT_AVAILABLE",
                "nonceAndClockVerification": "NOT_PERFORMED",
                "keyRevocationVerification": "NOT_PERFORMED",
                "externalAuditReceipt": "NOT_AVAILABLE",
                "independentEvidenceAcceptance": "NOT_PERFORMED",
                "transfer": "NOT_INITIATED",
                "gate": "BLOCKED",
                "decision": "DENY",
            })
        return {
            "schema": "palaco.pp.recovery-002-custody-transfer-verification-protocol.v0",
            "reference": "PP-RECOVERY-002",
            "custodyContractSha256": hashlib.sha256(custody_contract_bytes).hexdigest(),
            "collectionPlanSha256": supplied["collectionPlanSha256"],
            "auditContractSha256": supplied["auditContractSha256"],
            "binding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "protocolScope": "UNSIGNED_FUTURE_EXTERNAL_TRANSFER_REQUIREMENTS_ONLY",
            "transferRecords": records,
            "requiredTransferCount": len(records),
            "transfersInitiated": 0,
            "transfersAuthenticated": 0,
            "evidenceAccepted": 0,
            "requiredEnvelopeFields": [
                {"order": i, "fieldId": item, "status": "MISSING"}
                for i, item in enumerate(ENVELOPE_FIELDS, 1)
            ],
            "verificationStages": [
                {"order": i, "stageId": stage, "requirement": requirement,
                 "status": "NOT_PERFORMED", "gate": "BLOCKED"}
                for i, (stage, requirement) in enumerate(TRANSFER_STAGES, 1)
            ],
            "externalTransferCheckpoints": [
                {"order": i, "checkpointId": item,
                 "status": "NOT_PERFORMED", "gate": "BLOCKED"}
                for i, item in enumerate(TRANSFER_CHECKPOINTS, 1)
            ],
            "failurePolicy": [
                {"reason": reason, "decision": "DENY", "authorityEffect": "NONE"}
                for reason in FAIL_CLOSED + ADDITIONAL_FAILURES
            ],
            "senderTrust": "NOT_ESTABLISHED",
            "recipientTrust": "NOT_ESTABLISHED",
            "canonicalEnvelopeVerifier": "NOT_IMPLEMENTED",
            "signatureVerifier": "NOT_CONFIGURED",
            "trustedNonceLedger": "NOT_CONFIGURED",
            "auditVerifier": "NOT_CONFIGURED",
            "humanAcceptance": "NOT_COMPLETED",
            "evidenceTransfer": "NOT_INITIATED",
            "evidenceStorage": "NONE",
            "trustedIssuerCount": 0,
            "allowedAlgorithms": [],
            "independentVerification": "NOT_VERIFIED",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
