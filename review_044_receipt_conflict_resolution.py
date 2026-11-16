"""Receipt Conflict Resolution Protocol: unsigned, fail-closed requirements only.

Reconstructs all prior PP-RECOVERY-002 contracts and the exact transfer
receipt reconciliation report. No disputed receipt is submitted, accepted,
resolved, trusted or used to authorize any operation in this local module.
"""
import hashlib

from review_044_transfer_receipt_reconciliation import (
    prepare_transfer_receipt_reconciliation_contract, CONFLICTS,
    MATCH_REQUIREMENTS, EXTERNAL_GATES,
)
from review_044_trust_decision_audit_contract import AUDIT_EVIDENCE
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_RECEIPT_CONFLICT_RESOLUTION_INVALID"
MAX_RECONCILIATION_BYTES = 64 * 1024

RESOLUTION_STEPS = (
    "PRESERVE_DISPUTED_ORIGINALS_WITH_INDEPENDENT_CUSTODIAN",
    "FREEZE_ACCEPTANCE_AND_FLAG_CONFLICT_FOR_HUMAN_REVIEW",
    "AUTHENTICATE_INDEPENDENT_SENDER_AND_RECIPIENT",
    "COMPARE_CANONICAL_SIGNED_BYTES_AND_EXACT_DIGESTS",
    "VERIFY_NONCE_REPLAY_TRUSTED_TIME_AND_KEY_REVOCATION",
    "VERIFY_INDEPENDENT_AUDIT_INCLUSION_AND_LOG_CONSISTENCY",
    "OBTAIN_SEPARATE_AUTHORIZED_CONFLICT_REVIEW_DECISION",
    "REQUIRE_INDEPENDENT_POST_REVIEW_RELEASE_AUTHORIZATION",
)
ESCALATION_ROLES = (
    "INDEPENDENT_EVIDENCE_CUSTODIAN",
    "INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER",
    "AUTHORIZED_INDEPENDENT_CONFLICT_REVIEWER",
    "SEPARATE_RELEASE_AUTHORITY",
)
SAFETY_RULES = (
    "NO_AUTOMATIC_ACCEPTANCE_FROM_LOCAL_RECEIPT_CLAIM",
    "NO_AUTO_RETRY_OR_REPLAY_OF_DISPUTED_TRANSFER",
    "NO_MUTATION_OF_ORIGINAL_SIGNED_EVIDENCE",
    "NO_TRUST_ON_FIRST_USE_OR_UNVERIFIED_KEYS",
    "NO_ESCALATION_FROM_SELF_ASSERTED_REVIEWER_ROLE",
    "NO_DEPLOYMENT_FROM_RESOLUTION_OUTCOME_ALONE",
)


def prepare_receipt_conflict_resolution_protocol(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes, audit_contract_bytes: bytes,
    readiness_matrix_bytes: bytes, collection_plan_bytes: bytes,
    custody_contract_bytes: bytes, transfer_protocol_bytes: bytes,
    reconciliation_bytes: bytes,
) -> dict[str, object]:
    """Return an offline, non-resolving list of blocked conflict procedures."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        current = _loads(reconciliation_bytes, MAX_RECONCILIATION_BYTES)
        expected = prepare_transfer_receipt_reconciliation_contract(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
            review_dossier_bytes, decision_protocol_bytes, audit_contract_bytes,
            readiness_matrix_bytes, collection_plan_bytes,
            custody_contract_bytes, transfer_protocol_bytes,
        )
        if not _strict_equal(current, expected):
            raise ValueError
        if (current["reconciledReceiptPairs"] != 0
                or current["senderReceiptsReceived"] != 0
                or current["recipientAcknowledgementsReceived"] != 0
                or current["evidenceAcceptance"] != "PROHIBITED"
                or current["evidenceTransfer"] != "NOT_INITIATED"
                or current["trustedIssuerCount"] != 0
                or current["allowedAlgorithms"] != []
                or current["authorization"] != "HOLD"
                or current["accessDecision"] != "DENY"
                or len(current["receiptRows"]) != len(AUDIT_EVIDENCE)
                or len(current["requiredMatchChecks"]) != len(MATCH_REQUIREMENTS)
                or len(current["externalReviewGates"]) != len(EXTERNAL_GATES)
                or len(current["conflictPolicy"]) != len(CONFLICTS)):
            raise ValueError
        rows = []
        for i, row in enumerate(current["receiptRows"], 1):
            evidence_id, role = AUDIT_EVIDENCE[i-1]
            if (row["rowId"] != "AUD-E%02d" % i
                    or row["evidenceId"] != evidence_id
                    or row["requiredIndependentCustodianRole"] != role
                    or row["senderSignedReceipt"] != "NOT_AVAILABLE"
                    or row["recipientSignedAcknowledgement"] != "NOT_AVAILABLE"
                    or row["reconciliation"] != "NOT_PERFORMED"
                    or row["gate"] != "BLOCKED"
                    or row["decision"] != "DENY"):
                raise ValueError
            rows.append({
                "rowId": row["rowId"],
                "evidenceId": evidence_id,
                "custodianRoleRequired": role,
                "senderReceipt": "NOT_RECEIVED",
                "recipientAck": "NOT_RECEIVED",
                "conflictDetermination": "NOT_PERFORMED",
                "externalCaseCreation": "NOT_STARTED",
                "evidencePreservation": "REQUIRED_NOT_EXECUTED",
                "independentAdjudication": "NOT_COMPLETED",
                "disposition": "UNRESOLVED_DENY",
                "transfer": "NOT_INITIATED",
                "gate": "BLOCKED",
                "accessDecision": "DENY",
            })
        return {
            "schema": "palaco.pp.recovery-002-receipt-conflict-resolution.v0",
            "reference": "PP-RECOVERY-002",
            "reconciliationSha256": hashlib.sha256(reconciliation_bytes).hexdigest(),
            "transferProtocolSha256": current["transferProtocolSha256"],
            "custodyContractSha256": current["custodyContractSha256"],
            "binding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "scope": "UNSIGNED_CONFLICT_RESOLUTION_REQUIREMENTS_NOT_ADJUDICATION",
            "conflictCases": rows,
            "requiredReceiptPairs": len(rows),
            "externallyAdjudicatedConflicts": 0,
            "acceptedReceiptPairs": 0,
            "disputeConditions": [
                {"order": i, "reasonId": reason,
                 "classification": "POTENTIAL_CONFLICT_NOT_OBSERVED",
                 "disposition": "DENY_PENDING_INDEPENDENT_REVIEW"}
                for i, reason in enumerate(CONFLICTS, 1)
            ],
            "independentResolutionSteps": [
                {"order": i, "stepId": step, "status": "NOT_STARTED",
                 "gate": "BLOCKED"}
                for i, step in enumerate(RESOLUTION_STEPS, 1)
            ],
            "escalationRoles": [
                {"role": role, "authentication": "NOT_ESTABLISHED",
                 "authority": "NOT_ESTABLISHED"}
                for role in ESCALATION_ROLES
            ],
            "nonBypassRules": [
                {"ruleId": rule, "status": "ENFORCE_DENY_ONLY",
                 "authorityEffect": "NONE"}
                for rule in SAFETY_RULES
            ],
            "conflictIntake": "NOT_IMPLEMENTED",
            "signedReceiptVerification": "NOT_CONFIGURED",
            "trustedReplayLedger": "NOT_CONFIGURED",
            "externalAudit": "NOT_CONFIGURED",
            "independentConflictReview": "NOT_COMPLETED",
            "humanDecision": "NOT_COMPLETED",
            "evidenceAcceptance": "PROHIBITED",
            "evidenceTransfer": "NOT_INITIATED",
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
