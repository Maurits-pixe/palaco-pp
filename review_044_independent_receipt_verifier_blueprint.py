"""Non-executing independent receipt verifier service blueprint.

Reconstructs the original 18-source chain, handoff and receipt protocol.
This is an architectural contract, not a signature validator, a receipt
processor, a trust store, a deployment plan, or proof of reviewer authority.
"""
import hashlib

from review_044_independent_receipt_protocol import (
    prepare_independent_review_receipt_protocol, VERIFY_STEPS, FAILURES,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_RECEIPT_VERIFIER_BLUEPRINT_INVALID"
MAX_RECEIPT_PROTOCOL_BYTES = 64 * 1024

SERVICE_COMPONENTS = (
    ("RECEIPT_FORMAT_GATE", "CANONICAL_SCHEMA_AND_BYTE_LIMIT_ENFORCEMENT"),
    ("HANDOFF_BINDING_GATE", "EXACT_HANDOFF_AND_EVIDENCE_SET_DIGEST_BINDING"),
    ("TRUST_ANCHOR_RESOLVER", "PINNED_EXTERNAL_ISSUER_AND_KEY_TRUST_POLICY"),
    ("SIGNATURE_VALIDATOR", "ALGORITHM_ALLOWLIST_AND_KEY_USAGE_VERIFICATION"),
    ("KEY_LIFECYCLE_GATE", "KEY_ROTATION_EPOCH_AND_REVOCATION_VALIDATION"),
    ("FRESHNESS_AND_REPLAY_GATE", "AUDIENCE_PURPOSE_NONCE_EXPIRY_AND_ATOMIC_REPLAY_LEDGER"),
    ("INDEPENDENT_REVIEWER_GATE", "IDENTITY_SCOPE_SEPARATION_OF_DUTIES_CHECKS"),
    ("AUDIT_ANCHOR_GATE", "EXTERNAL_IMMUTABLE_LOG_PROOF_AND_TRUSTED_TIME"),
    ("HUMAN_DECISION_GATE", "SEPARATE_AUTHORIZED_DECISION_BOUND_TO_RECEIPT"),
)
KEY_LIFECYCLE_REQUIREMENTS = (
    "TRUSTED_ISSUER_ROOT_PINNING",
    "KID_ISSUER_AND_AUDIENCE_SCOPING",
    "ALGORITHM_ALLOWLIST_NO_DOWNGRADE",
    "ROTATION_EPOCH_AND_OVERLAP_POLICY",
    "KEY_NOT_BEFORE_AND_NOT_AFTER_VALIDATION",
    "SIGNED_KEY_REVOCATION_FEED_AND_FRESHNESS",
    "COMPROMISED_KEY_DENY_AND_FORENSIC_ESCALATION",
)
REPLAY_REQUIREMENTS = (
    "CRYPTOSAFE_SINGLE_USE_CHALLENGE_NONCE",
    "NONCE_BOUND_TO_EXACT_HANDOFF_AND_PURPOSE",
    "TRUSTED_CLOCK_WITH_MAX_SKEW",
    "ATOMIC_CONSUME_ONCE_EXTERNAL_NONCE_STORE",
    "REPLAY_STORE_OUTAGE_FAIL_CLOSED",
    "EXPIRED_MISMATCHED_OR_REUSED_NONCE_DENY",
)
AUDIT_REQUIREMENTS = (
    "SIGNED_HASH_CHAINED_EXTERNAL_AUDIT_LOG",
    "INDEPENDENT_INCLUSION_AND_CONSISTENCY_PROOFS",
    "TRUSTED_TIMESTAMP_ANCHOR",
    "AUDIT_UNAVAILABILITY_FAIL_CLOSED",
    "LEAST_PRIVILEGE_AUDIT_READER",
    "NO_PII_OR_RAW_SECRET_IN_LOG",
)
TRUST_BOUNDARIES = (
    ("UNTRUSTED_LOCAL_HANDOFF", "EXTERNAL_INDEPENDENT_VERIFIER"),
    ("EXTERNAL_VERIFIER", "TRUSTED_ISSUER_KEY_REGISTRY"),
    ("EXTERNAL_VERIFIER", "ATOMIC_REPLAY_PROTECTION_STORE"),
    ("EXTERNAL_VERIFIER", "IMMUTABLE_AUDIT_SERVICE"),
    ("VERIFIED_TECHNICAL_RECEIPT", "SEPARATE_HUMAN_RELEASE_AUTHORITY"),
)


def prepare_independent_receipt_verifier_blueprint(
    source_bytes: tuple[bytes, ...],
    execution_plan_bytes: bytes,
    observation_register_bytes: bytes,
    evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes,
    receipt_protocol_bytes: bytes,
) -> dict[str, object]:
    """Strictly bind the unsigned protocol; emit requirements with zero authority."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        observed = _loads(receipt_protocol_bytes, MAX_RECEIPT_PROTOCOL_BYTES)
        expected = prepare_independent_review_receipt_protocol(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes,
        )
        if not _strict_equal(observed, expected):
            raise ValueError
        if (observed["signedReceipt"] != "NOT_AVAILABLE"
                or observed["receiptSubmission"] != "NOT_IMPLEMENTED"
                or observed["reviewerAuthority"] != "NOT_ESTABLISHED"
                or observed["releaseReadiness"] != "NOT_READY"
                or observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or len(observed["externalVerification"]) != len(VERIFY_STEPS)
                or len(observed["failureBehavior"]) != len(FAILURES)):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-independent-receipt-verifier-blueprint.v0",
            "reference": "PP-RECOVERY-002",
            "receiptProtocolSha256": hashlib.sha256(receipt_protocol_bytes).hexdigest(),
            "reviewHandoffSha256": observed["reviewHandoffSha256"],
            "contractBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "serviceComponents": [
                {"componentId": component, "responsibility": responsibility,
                 "implementation": "NOT_IMPLEMENTED", "runtimeState": "BLOCKED"}
                for component, responsibility in SERVICE_COMPONENTS
            ],
            "keyLifecycleControls": [
                {"requirementId": item, "implementation": "NOT_CONFIGURED",
                 "verification": "NOT_PERFORMED"}
                for item in KEY_LIFECYCLE_REQUIREMENTS
            ],
            "replayProtectionControls": [
                {"requirementId": item, "implementation": "NOT_CONFIGURED",
                 "verification": "NOT_PERFORMED"}
                for item in REPLAY_REQUIREMENTS
            ],
            "auditControls": [
                {"requirementId": item, "implementation": "NOT_CONFIGURED",
                 "verification": "NOT_PERFORMED"}
                for item in AUDIT_REQUIREMENTS
            ],
            "trustBoundaries": [
                {"from": source, "to": target,
                 "authentication": "NOT_ESTABLISHED",
                 "accessDecision": "DENY"}
                for source, target in TRUST_BOUNDARIES
            ],
            "verificationPipeline": [
                {"order": i, "step": step,
                 "execution": "NOT_PERFORMED", "gate": "BLOCKED"}
                for i, step in enumerate(VERIFY_STEPS, 1)
            ],
            "failurePolicy": [
                {"failure": failure, "decision": "DENY",
                 "authorityEffect": "NONE"}
                for failure in FAILURES
            ],
            "signingKeyMaterial": "NOT_PRESENT",
            "trustedIssuers": "NOT_CONFIGURED",
            "signatureValidation": "NOT_IMPLEMENTED",
            "nonceLedger": "NOT_CONFIGURED",
            "trustedClock": "NOT_CONFIGURED",
            "auditService": "NOT_CONFIGURED",
            "independentVerifier": "NOT_DEPLOYED",
            "humanReview": "NOT_COMPLETED",
            "receiptAcceptance": "NOT_PERFORMED",
            "receiptDelivery": "NOT_SENT",
            "reviewerAuthority": "NOT_ESTABLISHED",
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
