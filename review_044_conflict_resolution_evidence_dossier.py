"""Offline Conflict Resolution Evidence Dossier: requirements, not evidence.

Type-exactly reconstructs the full 18-source PP-RECOVERY-002 chain before
binding a prior conflict resolution protocol. Each possible conflict has
its own external proof requirements and independent reviewer roles.
No actual conflicts, proofs, signatures or decisions are admitted.
"""
import hashlib

from review_044_receipt_conflict_resolution import (
    prepare_receipt_conflict_resolution_protocol, RESOLUTION_STEPS,
    ESCALATION_ROLES, SAFETY_RULES,
)
from review_044_transfer_receipt_reconciliation import CONFLICTS
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_CONFLICT_EVIDENCE_DOSSIER_INVALID"
MAX_CONFLICT_PROTOCOL_BYTES = 64 * 1024

EVIDENCE_REQUIREMENTS = (
    ("ORIGINAL_SIGNED_SENDER_RECEIPT_AND_ISSUER_CHAIN", "INDEPENDENT_EVIDENCE_CUSTODIAN"),
    ("ORIGINAL_SIGNED_RECIPIENT_ACK_AND_RECEIVER_SCOPE", "INDEPENDENT_EVIDENCE_CUSTODIAN"),
    ("CANONICAL_ENVELOPE_AND_ORIGINAL_EVIDENCE_DIGESTS", "INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"),
    ("SENDER_RECEIVER_IDENTITY_AND_ROLE_SCOPE_ATTESTATIONS", "INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"),
    ("SIGNED_NONCE_REPLAY_LEDGER_AND_TRUSTED_TIME_PROOF", "INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"),
    ("SIGNER_KEY_EPOCH_AND_FRESH_REVOCATION_ATTESTATION", "INDEPENDENT_SIGNATURE_AND_REVOCATION_VERIFIER"),
    ("EXTERNAL_APPEND_ONLY_LOG_INCLUSION_AND_CONSISTENCY", "INDEPENDENT_EVIDENCE_CUSTODIAN"),
    ("SEPARATE_SIGNED_HUMAN_ACCEPTANCE_OR_DENIAL_DECISION", "AUTHORIZED_INDEPENDENT_CONFLICT_REVIEWER"),
)
REVIEW_CHECKPOINTS = (
    "EXACT_CONFLICT_PROTOCOL_AND_RECONCILIATION_HASHES",
    "TRUSTED_EXTERNAL_EVIDENCE_PROVENANCE_AND_ORIGINAL_BYTES",
    "INDEPENDENT_REVIEWER_IDENTITY_ROLE_SCOPE_AND_REVOCATION",
    "CANONICAL_SIGNATURE_DIGEST_AND_KEY_EPOCH_VALIDATION",
    "NONCE_REPLAY_TRUSTED_TIME_AND_AUDIENCE_VALIDATION",
    "IMMUTABLE_EXTERNAL_LOG_PROOF",
    "SEPARATE_AUTHORIZED_HUMAN_CONFLICT_DECISION",
    "SEPARATE_DEPLOYMENT_RELEASE_AUTHORIZATION",
)


def prepare_conflict_resolution_evidence_dossier(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes, audit_contract_bytes: bytes,
    readiness_matrix_bytes: bytes, collection_plan_bytes: bytes,
    custody_contract_bytes: bytes, transfer_protocol_bytes: bytes,
    reconciliation_bytes: bytes, conflict_protocol_bytes: bytes,
) -> dict[str, object]:
    """Build an unsigned request for independent review; all outcomes denied."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        actual = _loads(conflict_protocol_bytes, MAX_CONFLICT_PROTOCOL_BYTES)
        expected = prepare_receipt_conflict_resolution_protocol(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
            review_dossier_bytes, decision_protocol_bytes, audit_contract_bytes,
            readiness_matrix_bytes, collection_plan_bytes,
            custody_contract_bytes, transfer_protocol_bytes, reconciliation_bytes,
        )
        if not _strict_equal(actual, expected):
            raise ValueError
        if (actual["externallyAdjudicatedConflicts"] != 0
                or actual["acceptedReceiptPairs"] != 0
                or actual["conflictIntake"] != "NOT_IMPLEMENTED"
                or actual["evidenceAcceptance"] != "PROHIBITED"
                or actual["authorization"] != "HOLD"
                or actual["accessDecision"] != "DENY"
                or actual["allowedAlgorithms"] != []
                or len(actual["disputeConditions"]) != len(CONFLICTS)
                or len(actual["independentResolutionSteps"]) != len(RESOLUTION_STEPS)
                or len(actual["escalationRoles"]) != len(ESCALATION_ROLES)
                or len(actual["nonBypassRules"]) != len(SAFETY_RULES)):
            raise ValueError
        cases = []
        for i, condition in enumerate(actual["disputeConditions"], 1):
            evidence_id, reviewer = EVIDENCE_REQUIREMENTS[i - 1]
            if (condition["reasonId"] != CONFLICTS[i - 1]
                    or condition["classification"] != "POTENTIAL_CONFLICT_NOT_OBSERVED"
                    or condition["disposition"] != "DENY_PENDING_INDEPENDENT_REVIEW"):
                raise ValueError
            cases.append({
                "caseId": "CR-E%02d" % i,
                "potentialConflict": condition["reasonId"],
                "classification": "POTENTIAL_CONFLICT_NOT_OBSERVED",
                "requiredExternalEvidenceId": evidence_id,
                "requiredIndependentRole": reviewer,
                "originalEvidence": "NOT_RECEIVED",
                "sourceAuthenticity": "NOT_VERIFIED",
                "independentReviewerAuthority": "NOT_ESTABLISHED",
                "externalAuditProof": "NOT_AVAILABLE",
                "review": "NOT_STARTED",
                "decision": "DENY",
                "nextPermittedAction": "PREPARE_REQUEST_FOR_EXTERNAL_REVIEW_ONLY",
            })
        return {
            "schema": "palaco.pp.recovery-002-conflict-resolution-evidence-dossier.v0",
            "reference": "PP-RECOVERY-002",
            "conflictProtocolSha256": hashlib.sha256(conflict_protocol_bytes).hexdigest(),
            "reconciliationSha256": actual["reconciliationSha256"],
            "transferProtocolSha256": actual["transferProtocolSha256"],
            "sourceBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "dossierProvenance": "UNSIGNED_LOCAL_REQUIREMENTS_NOT_A_CONFLICT_CASE",
            "potentialConflictCases": cases,
            "potentialConflictCount": len(cases),
            "observedConflictCount": 0,
            "externalEvidenceReceivedCount": 0,
            "independentlyReviewedCount": 0,
            "reviewCheckpoints": [
                {"order": i, "checkpointId": step, "status": "NOT_PERFORMED",
                 "gate": "BLOCKED"}
                for i, step in enumerate(REVIEW_CHECKPOINTS, 1)
            ],
            "requiredReviewers": [
                {"role": role, "authentication": "NOT_ESTABLISHED",
                 "scope": "NOT_ATTESTED", "decision": "NOT_COMPLETED"}
                for role in ESCALATION_ROLES
            ],
            "independentResolutionSequence": [
                {"order": i, "stepId": step, "status": "NOT_STARTED",
                 "gate": "BLOCKED"}
                for i, step in enumerate(RESOLUTION_STEPS, 1)
            ],
            "nonBypassRules": [
                {"ruleId": rule, "status": "DENY_ONLY", "authorityEffect": "NONE"}
                for rule in SAFETY_RULES
            ],
            "externalRequestDelivery": "NOT_SENT",
            "evidenceIntake": "NOT_IMPLEMENTED",
            "conflictAdjudication": "NOT_PERFORMED",
            "independentConflictDecision": "NOT_AVAILABLE",
            "trustedAuditService": "NOT_CONFIGURED",
            "independentVerification": "NOT_VERIFIED",
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
