"""Unsigned transfer receipt reconciliation *requirements*, not a receipt.

Strictly rebuilds the prior 18-source custody-transfer protocol. No sender
or recipient receipts are processed: all comparisons are required externally,
and all outcomes are blocked. No authority is ever granted by this module.
"""
import hashlib

from review_044_custody_transfer_verification_protocol import (
    prepare_custody_transfer_verification_protocol, ENVELOPE_FIELDS,
    TRANSFER_STAGES, ADDITIONAL_FAILURES,
)
from review_044_audit_evidence_custody_contract import FAIL_CLOSED
from review_044_trust_decision_audit_contract import AUDIT_EVIDENCE
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_TRANSFER_RECEIPT_RECONCILIATION_INVALID"
MAX_TRANSFER_PROTOCOL_BYTES = 64 * 1024

MATCH_REQUIREMENTS = (
    "SENDER_RECEIPT_CANONICAL_BYTES_AND_SIGNATURE",
    "RECIPIENT_ACK_CANONICAL_BYTES_AND_SIGNATURE",
    "EXACT_TRANSFER_ENVELOPE_SHA256_MATCH",
    "EXACT_EVIDENCE_ID_AND_ORIGINAL_BYTE_HASH_MATCH",
    "SENDER_AND_RECIPIENT_IDENTITIES_AND_ROLE_SCOPE",
    "AUDIENCE_PURPOSE_FRESH_NONCE_AND_TRUSTED_TIME",
    "SIGNER_KEY_EPOCH_AND_REVOCATION_CHECK",
    "INDEPENDENT_AUDIT_INCLUSION_AND_CONSISTENCY",
    "EXPLICIT_NON_ACCEPTANCE_UNTIL_SEPARATE_HUMAN_DECISION",
)
EXTERNAL_GATES = (
    "RECEIVE_ORIGINAL_SIGNED_SENDER_RECEIPT_OUTSIDE_LOCAL_MODULE",
    "RECEIVE_ORIGINAL_SIGNED_RECIPIENT_ACK_OUTSIDE_LOCAL_MODULE",
    "VERIFY_BOTH_SIGNATURES_WITH_TRUSTED_EXTERNAL_KEYS",
    "COMPARE_CANONICAL_ENVELOPE_AND_EVIDENCE_DIGESTS",
    "CHECK_BOTH_SUBJECTS_ROLE_SCOPES_AND_REVOCATIONS",
    "VERIFY_ATOMIC_NONCE_REPLAY_AND_TRUSTED_TIME",
    "VERIFY_IMMUTABLE_AUDIT_INCLUSION_PROOF",
    "REQUIRE_SEPARATE_HUMAN_EVIDENCE_ACCEPTANCE",
)
CONFLICTS = (
    "SENDER_RECEIPT_ABSENT_OR_UNTRUSTED",
    "RECIPIENT_ACK_ABSENT_OR_UNTRUSTED",
    "ENVELOPE_OR_EVIDENCE_DIGEST_MISMATCH",
    "SENDER_RECIPIENT_IDENTITY_OR_SCOPE_MISMATCH",
    "AUDIENCE_PURPOSE_NONCE_OR_TIME_MISMATCH",
    "REVOKED_OR_UNTRUSTED_SIGNING_KEY",
    "UNVERIFIABLE_EXTERNAL_AUDIT_PROOF",
    "SEPARATE_HUMAN_ACCEPTANCE_ABSENT",
)


def prepare_transfer_receipt_reconciliation_contract(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes, audit_contract_bytes: bytes,
    readiness_matrix_bytes: bytes, collection_plan_bytes: bytes,
    custody_contract_bytes: bytes, transfer_protocol_bytes: bytes,
) -> dict[str, object]:
    """Define external reconciliation requirements; reconcile no real receipts."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        actual = _loads(transfer_protocol_bytes, MAX_TRANSFER_PROTOCOL_BYTES)
        expected = prepare_custody_transfer_verification_protocol(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
            review_dossier_bytes, decision_protocol_bytes, audit_contract_bytes,
            readiness_matrix_bytes, collection_plan_bytes, custody_contract_bytes,
        )
        if not _strict_equal(actual, expected):
            raise ValueError
        if (actual["transfersInitiated"] != 0
                or actual["transfersAuthenticated"] != 0
                or actual["evidenceAccepted"] != 0
                or actual["evidenceTransfer"] != "NOT_INITIATED"
                or actual["trustedIssuerCount"] != 0
                or actual["allowedAlgorithms"] != []
                or actual["authorization"] != "HOLD"
                or actual["accessDecision"] != "DENY"
                or len(actual["requiredEnvelopeFields"]) != len(ENVELOPE_FIELDS)
                or len(actual["verificationStages"]) != len(TRANSFER_STAGES)
                or len(actual["failurePolicy"]) != len(FAIL_CLOSED + ADDITIONAL_FAILURES)
                or len(actual["transferRecords"]) != len(AUDIT_EVIDENCE)):
            raise ValueError
        rows = []
        for i, record in enumerate(actual["transferRecords"], 1):
            evidence_id, role = AUDIT_EVIDENCE[i - 1]
            if (record["rowId"] != "AUD-E%02d" % i
                    or record["evidenceId"] != evidence_id
                    or record["requiredIndependentCustodianRole"] != role
                    or record["signedEnvelope"] != "NOT_PRESENT"
                    or record["recipientSignedAcknowledgement"] != "NOT_AVAILABLE"
                    or record["transfer"] != "NOT_INITIATED"
                    or record["gate"] != "BLOCKED"
                    or record["decision"] != "DENY"):
                raise ValueError
            rows.append({
                "rowId": record["rowId"],
                "evidenceId": evidence_id,
                "requiredIndependentCustodianRole": role,
                "senderSignedReceipt": "NOT_AVAILABLE",
                "recipientSignedAcknowledgement": "NOT_AVAILABLE",
                "senderSignatureVerification": "NOT_PERFORMED",
                "recipientSignatureVerification": "NOT_PERFORMED",
                "exactEnvelopeDigestMatch": "NOT_PERFORMED",
                "exactEvidenceDigestMatch": "NOT_PERFORMED",
                "identityScopeAndRevocation": "NOT_VERIFIED",
                "trustedNonceAndTime": "NOT_VERIFIED",
                "externalAuditProof": "NOT_AVAILABLE",
                "reconciliation": "NOT_PERFORMED",
                "transfer": "NOT_INITIATED",
                "gate": "BLOCKED",
                "decision": "DENY",
            })
        return {
            "schema": "palaco.pp.recovery-002-transfer-receipt-reconciliation.v0",
            "reference": "PP-RECOVERY-002",
            "transferProtocolSha256": hashlib.sha256(transfer_protocol_bytes).hexdigest(),
            "custodyContractSha256": actual["custodyContractSha256"],
            "auditContractSha256": actual["auditContractSha256"],
            "binding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "scope": "UNSIGNED_RECONCILIATION_REQUIREMENTS_NOT_RECEIPTS",
            "receiptRows": rows,
            "requiredReceiptPairs": len(rows),
            "senderReceiptsReceived": 0,
            "recipientAcknowledgementsReceived": 0,
            "reconciledReceiptPairs": 0,
            "requiredMatchChecks": [
                {"order": i, "checkId": rule, "status": "NOT_PERFORMED",
                 "gate": "BLOCKED"}
                for i, rule in enumerate(MATCH_REQUIREMENTS, 1)
            ],
            "externalReviewGates": [
                {"order": i, "gateId": gate, "status": "NOT_STARTED",
                 "decision": "DENY"}
                for i, gate in enumerate(EXTERNAL_GATES, 1)
            ],
            "conflictPolicy": [
                {"reason": issue, "outcome": "DENY", "authorityEffect": "NONE"}
                for issue in CONFLICTS
            ],
            "senderAuthority": "NOT_ESTABLISHED",
            "recipientAuthority": "NOT_ESTABLISHED",
            "signatureVerification": "NOT_CONFIGURED",
            "trustedReplayLedger": "NOT_CONFIGURED",
            "auditAnchoring": "NOT_CONFIGURED",
            "independentReconciliation": "NOT_VERIFIED",
            "humanAcceptance": "NOT_COMPLETED",
            "evidenceTransfer": "NOT_INITIATED",
            "evidenceAcceptance": "PROHIBITED",
            "evidenceStorage": "NONE",
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
