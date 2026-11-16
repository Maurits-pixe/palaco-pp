"""Independent Review Receipt Protocol: fail-closed design, not a receipt.

Rebuilds the local evidence handoff from 18 original sources plus execution
plan, observation register, and evidence intake. Strictly binds the handoff
bytes; specifies external verifiers and signed receipt fields, but creates
no signature, authenticates no reviewer, and accepts no receipt claim.
"""
import hashlib

from review_044_release_evidence_review_handoff import (
    prepare_release_evidence_review_handoff, REVIEW_REQUIREMENTS,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_INDEPENDENT_RECEIPT_PROTOCOL_INVALID"
MAX_HANDOFF_BYTES = 64 * 1024

RECEIPT_FIELDS = (
    "RECEIPT_SCHEMA_AND_PROTOCOL_VERSION",
    "EXACT_HANDOFF_SHA256",
    "INDEPENDENT_ISSUER_ID_AND_AUDIENCE",
    "REVIEWER_SUBJECT_AND_ROLE_SCOPE",
    "INDEPENDENCE_AND_SEPARATION_OF_DUTIES_ATTESTATION",
    "CHALLENGE_NONCE_AND_PURPOSE_BINDING",
    "TRUSTED_ISSUED_AT_AND_EXPIRES_AT",
    "SIGNED_EVIDENCE_REFERENCE_SET_SHA256",
    "EXTERNAL_IMMUTABLE_AUDIT_ANCHOR",
    "AUTHORIZED_REVIEW_DECISION_REFERENCE",
    "SIGNING_KEY_ID_AND_SIGNATURE_ALGORITHM",
    "DETACHED_CRYPTOGRAPHIC_SIGNATURE",
)
VERIFY_STEPS = (
    "VALIDATE_RECEIPT_SCHEMA_AND_CANONICAL_SIGNED_BYTES",
    "MATCH_HANDOFF_HASH_AND_EXACT_EVIDENCE_REFERENCE_SET",
    "VERIFY_TRUSTED_ISSUER_SIGNATURE_AND_KEY_ROTATION",
    "VERIFY_AUDIENCE_PURPOSE_FRESH_NONCE_AND_TRUSTED_TIME",
    "CHECK_REVIEWER_IDENTITY_ROLE_SCOPE_AND_INDEPENDENCE",
    "CHECK_CREDENTIAL_ROLE_AND_SIGNING_KEY_REVOCATION",
    "VERIFY_EXTERNAL_AUDIT_ANCHOR_AND_DECISION_PROVENANCE",
    "REQUIRE_SEPARATE_AUTHORIZED_HUMAN_DECISION",
)
FAILURES = (
    "RECEIPT_MISSING",
    "UNTRUSTED_ISSUER_OR_KEY",
    "INVALID_OR_UNSUPPORTED_SIGNATURE",
    "HANDOFF_OR_EVIDENCE_HASH_MISMATCH",
    "EXPIRED_OR_REPLAYED_CHALLENGE",
    "UNVERIFIED_REVIEWER_SCOPE_OR_INDEPENDENCE",
    "REVOKED_CREDENTIAL_OR_SIGNING_KEY",
    "EXTERNAL_AUDIT_NOT_VERIFIABLE",
    "TRUSTED_CLOCK_UNAVAILABLE",
    "AUTHORIZED_HUMAN_DECISION_ABSENT",
)


def prepare_independent_review_receipt_protocol(
    source_bytes: tuple[bytes, ...],
    execution_plan_bytes: bytes,
    observation_register_bytes: bytes,
    evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes,
) -> dict[str, object]:
    """Produce blocked external receipt requirements after exact handoff binding."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        actual = _loads(review_handoff_bytes, MAX_HANDOFF_BYTES)
        expected = prepare_release_evidence_review_handoff(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes,
        )
        if not _strict_equal(actual, expected):
            raise ValueError
        if (actual["delivery"] != "NOT_SENT"
                or actual["signedReceipt"] != "NOT_AVAILABLE"
                or actual["reviewerAuthority"] != "NOT_ESTABLISHED"
                or actual["releaseReadiness"] != "NOT_READY"
                or actual["authorization"] != "HOLD"
                or actual["accessDecision"] != "DENY"
                or len(actual["requiredExternalReview"]) != len(REVIEW_REQUIREMENTS)):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-independent-review-receipt-protocol.v0",
            "reference": "PP-RECOVERY-002",
            "reviewHandoffSha256": hashlib.sha256(review_handoff_bytes).hexdigest(),
            "executionPlanSha256": actual["executionPlanSha256"],
            "observationRegisterSha256": actual["observationRegisterSha256"],
            "evidenceIntakeSha256": actual["evidenceIntakeSha256"],
            "sourceBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "receiptProfile": {
                "requiredFormat": "CANONICAL_SIGNED_EXTERNAL_ENVELOPE",
                "signatureAlgorithm": "TRUST_POLICY_DEFINED_NOT_CONFIGURED",
                "keyTrustSource": "EXTERNAL_AUTHORITY_NOT_CONFIGURED",
                "requiredFields": [
                    {"fieldId": field, "status": "MISSING"}
                    for field in RECEIPT_FIELDS
                ],
                "receiptBytes": "NOT_PRESENT",
                "signatureVerification": "NOT_IMPLEMENTED",
            },
            "externalVerification": [
                {"order": i, "check": check,
                 "status": "NOT_PERFORMED", "gate": "BLOCKED"}
                for i, check in enumerate(VERIFY_STEPS, 1)
            ],
            "failureBehavior": [
                {"failure": failure, "decision": "DENY",
                 "authorityEffect": "NONE"}
                for failure in FAILURES
            ],
            "reviewRequirements": [
                {"requirement": item, "status": "NOT_STARTED"}
                for item in REVIEW_REQUIREMENTS
            ],
            "evidenceReferenceCount": actual["evidenceReferenceCount"],
            "evidenceAcceptance": "NOT_PERFORMED",
            "receiptSubmission": "NOT_IMPLEMENTED",
            "delivery": "NOT_SENT",
            "independentVerifier": "NOT_CONFIGURED",
            "trustedClock": "NOT_CONFIGURED",
            "revocationCheck": "NOT_PERFORMED",
            "auditAnchoring": "NOT_IMPLEMENTED",
            "reviewerAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "signedReceipt": "NOT_AVAILABLE",
            "humanReview": "NOT_COMPLETED",
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
