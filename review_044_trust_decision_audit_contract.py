"""Fail-closed Trust Decision Audit Contract, NOT an audit receipt.

Rebuilds all earlier contracts and binds an exact, unsigned decision protocol
to future independent audit requirements. Does not produce audit evidence,
verify signatures or timestamps, authenticate reviewers, or grant authority.
"""
import hashlib

from review_044_trust_change_decision_protocol import (
    prepare_trust_change_decision_protocol, STAGES, BOUNDARIES, NON_BYPASSABLE,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_TRUST_DECISION_AUDIT_CONTRACT_INVALID"
MAX_DECISION_PROTOCOL_BYTES = 64 * 1024

AUDIT_EVIDENCE = (
    ("EXACT_DECISION_PROTOCOL_AND_CHANGE_HASHES", "INDEPENDENT_AUDIT_VERIFIER"),
    ("SIGNED_EXTERNAL_EVIDENCE_RECEIPT", "INDEPENDENT_EVIDENCE_CUSTODIAN"),
    ("REVIEWER_IDENTITY_ROLE_AND_REVOCATION_ATTESTATION", "INDEPENDENT_IDENTITY_AUDITOR"),
    ("CANONICAL_SIGNED_HUMAN_DECISION", "AUTHORIZED_HUMAN_DECISION_AUDITOR"),
    ("TRUSTED_TIME_AND_NONCE_REPLAY_LEDGER_PROOF", "INDEPENDENT_REPLAY_AUDITOR"),
    ("IMMUTABLE_LOG_INCLUSION_AND_CONSISTENCY_PROOF", "INDEPENDENT_AUDIT_VERIFIER"),
    ("KEY_EPOCH_ROTATION_AND_REVOCATION_PROOF", "INDEPENDENT_CRYPTO_AUDITOR"),
    ("SEPARATE_DEPLOYMENT_DENIAL_AND_ROLLBACK_RECORD", "INDEPENDENT_RELEASE_ATTESTOR"),
)
RECONSTRUCTION = (
    "REBUILD_ORIGINAL_POLICY_AND_CHANGE_CONTROL_BYTES",
    "VERIFY_EXACT_DECISION_PROTOCOL_AND_EVIDENCE_SET_DIGESTS",
    "AUTHENTICATE_INDEPENDENT_ISSUER_AND_SIGNER_TRUST_CHAIN",
    "VERIFY_KEY_REVOCATION_AND_SIGNED_ROTATION_HISTORY",
    "VERIFY_REPLAY_NONCE_AND_TRUSTED_CLOCK_WINDOW",
    "VERIFY_APPEND_ONLY_EXTERNAL_LOG_INCLUSION_AND_CONSISTENCY",
    "RECONSTRUCT_REVIEWER_AUTHORITY_AND_SEPARATE_DECISION",
    "VERIFY_INDEPENDENT_DEPLOYMENT_AND_ROLLBACK_APPROVAL",
)
FAIL_CLOSED = (
    "MISSING_EXTERNAL_AUDIT_RECEIPT",
    "UNTRUSTED_LOG_ISSUER_OR_SIGNER",
    "INVALID_DECISION_OR_RECEIPT_SIGNATURE",
    "SOURCE_HASH_OR_SIGNED_PAYLOAD_MISMATCH",
    "NONCE_REPLAY_OR_UNTRUSTED_TIMESTAMP",
    "REVOKED_KEY_OR_REVIEWER_AUTHORITY",
    "AUDIT_LOG_FORK_OR_INCLUSION_FAILURE",
    "MISSING_SEPARATE_HUMAN_OR_DEPLOYMENT_DECISION",
)


def prepare_trust_decision_audit_contract(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
    decision_protocol_bytes: bytes,
) -> dict[str, object]:
    """Produce a non-authorizing audit evidence contract after strict rebuild."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        observed = _loads(decision_protocol_bytes, MAX_DECISION_PROTOCOL_BYTES)
        expected = prepare_trust_change_decision_protocol(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes,
            change_control_bytes, review_dossier_bytes,
        )
        if not _strict_equal(observed, expected):
            raise ValueError
        if (observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or observed["changeApplied"] is not False
                or observed["signedDecision"] != "NOT_AVAILABLE"
                or observed["reviewDossierDelivery"] != "NOT_SENT"
                or observed["independentVerification"] != "NOT_VERIFIED"
                or len(observed["decisionStages"]) != len(STAGES)
                or len(observed["trustBoundaryRules"]) != len(BOUNDARIES)
                or len(observed["nonBypassableControls"]) != len(NON_BYPASSABLE)):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-trust-decision-audit-contract.v0",
            "reference": "PP-RECOVERY-002",
            "decisionProtocolSha256": hashlib.sha256(decision_protocol_bytes).hexdigest(),
            "reviewDossierSha256": observed["reviewDossierSha256"],
            "changeControlSha256": observed["changeControlSha256"],
            "trustPolicySha256": observed["trustPolicySha256"],
            "binding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "auditScope": "FUTURE_EXTERNAL_AUDIT_REQUIREMENTS_NOT_EVIDENCE",
            "requiredExternalEvidence": [
                {"order": n, "evidenceId": name, "requiredIndependentRole": role,
                 "evidenceStatus": "NOT_PROVIDED",
                 "signatureVerification": "NOT_PERFORMED"}
                for n, (name, role) in enumerate(AUDIT_EVIDENCE, 1)
            ],
            "reconstructionSteps": [
                {"order": n, "stepId": step, "status": "NOT_PERFORMED",
                 "gate": "BLOCKED"}
                for n, step in enumerate(RECONSTRUCTION, 1)
            ],
            "decisionBoundaryAudit": [
                {"fromStage": source, "toStage": target, "ruleId": rule,
                 "externalProof": "NOT_AVAILABLE", "crossing": "PROHIBITED"}
                for source, target, rule in BOUNDARIES
            ],
            "failureRules": [
                {"reason": reason, "decision": "DENY", "authorityEffect": "NONE"}
                for reason in FAIL_CLOSED
            ],
            "sourceAuthenticity": "NOT_ATTESTED",
            "signedAuditReceipt": "NOT_AVAILABLE",
            "externalAuditLog": "NOT_CONFIGURED",
            "trustedClock": "NOT_CONFIGURED",
            "auditVerification": "NOT_PERFORMED",
            "independentReviewerAuthority": "NOT_ESTABLISHED",
            "humanDecision": "NOT_COMPLETED",
            "deploymentDecision": "NOT_AUTHORIZED",
            "changeApplied": False,
            "issuerPromotion": "PROHIBITED",
            "algorithmPromotion": "PROHIBITED",
            "trustedIssuerCount": 0,
            "allowedAlgorithms": [],
            "keyMaterial": "NOT_PRESENT",
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
