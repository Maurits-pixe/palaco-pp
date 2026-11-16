"""Unconfigured Verifier Trust Policy Register for PP-RECOVERY-002.

Specifies issuer, algorithm, rotation and revocation policy requirements only.
No issuer enrollment, key import, signature verification, trust promotion,
runtime execution or release authority is performed. Strictly reconstitutes
the preceding unsigned independent receipt verifier blueprint first.
"""
import hashlib

from review_044_independent_receipt_verifier_blueprint import (
    prepare_independent_receipt_verifier_blueprint, KEY_LIFECYCLE_REQUIREMENTS,
    TRUST_BOUNDARIES,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_VERIFIER_TRUST_POLICY_INVALID"
MAX_BLUEPRINT_BYTES = 64 * 1024

ISSUER_REQUIREMENTS = (
    "EXTERNALLY_APPROVED_ISSUER_ROOT",
    "ISSUER_ID_AND_RECEIPT_AUDIENCE_BINDING",
    "TRUST_ANCHOR_PROVENANCE_AND_OWNER_AUTHORIZATION",
    "INDEPENDENT_ISSUER_ONBOARDING_REVIEW",
    "ISSUER_REVOCATION_AND_EMERGENCY_DENY",
)
ALGORITHM_RULES = (
    "EXPLICIT_ALGORITHM_ALLOWLIST_NOT_WILDCARD",
    "NO_ALG_NONE_OR_SYMMETRIC_ASYMMETRIC_CONFUSION",
    "KEY_TYPE_CURVE_AND_USAGE_MATCH",
    "CANONICAL_SIGNED_BYTES_NO_REENCODING",
    "DOWNGRADE_AND_UNSUPPORTED_ALGORITHM_DENY",
)
ROTATION_RULES = (
    "ISSUER_SCOPED_KID_UNIQUENESS",
    "PINNED_ROOT_AND_SIGNED_KEYSET_UPDATES",
    "KEY_VALIDITY_WITH_TRUSTED_CLOCK",
    "ROTATION_EPOCH_AND_SIGNED_OVERLAP_POLICY",
    "HISTORICAL_KEY_VERIFICATION_ONLY_UNDER_AUTHORIZED_POLICY",
    "NO_KEY_MATERIAL_IN_LOCAL_REPORTS",
)
REVOCATION_RULES = (
    "SIGNED_FRESH_ISSUER_REVOCATION_FEED",
    "KEY_AND_REVIEWER_CREDENTIAL_REVOCATION",
    "TRUST_ROOT_REMOVAL_FAIL_CLOSED",
    "REVOCATION_FEED_OUTAGE_FAIL_CLOSED",
    "COMPROMISE_RESPONSE_REQUIRES_INDEPENDENT_REVIEW",
    "NO_OFFLINE_STALE_TRUST_FALLBACK",
)
DEFAULT_DENIALS = (
    "UNKNOWN_ISSUER", "UNPINNED_TRUST_ROOT", "MISSING_TRUSTED_KEY",
    "UNSUPPORTED_SIGNATURE_ALGORITHM", "EXPIRED_SIGNING_KEY",
    "REVOKED_KEY_OR_REVIEWER", "STALE_REVOCATION_FEED",
    "TRUSTED_CLOCK_UNAVAILABLE", "REPLAY_LEDGER_UNAVAILABLE",
    "INDEPENDENT_REVIEWER_UNAUTHENTICATED",
    "AUDIT_ANCHOR_UNVERIFIABLE", "HUMAN_RELEASE_DECISION_MISSING",
)


def prepare_verifier_trust_policy_register(
    source_bytes: tuple[bytes, ...],
    execution_plan_bytes: bytes,
    observation_register_bytes: bytes,
    evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes,
    receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes,
) -> dict[str, object]:
    """Return a fully blocked policy registry bound to the exact prior blueprint."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        blueprint = _loads(verifier_blueprint_bytes, MAX_BLUEPRINT_BYTES)
        expected = prepare_independent_receipt_verifier_blueprint(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
        )
        if not _strict_equal(blueprint, expected):
            raise ValueError
        if (blueprint["trustedIssuers"] != "NOT_CONFIGURED"
                or blueprint["signingKeyMaterial"] != "NOT_PRESENT"
                or blueprint["signatureValidation"] != "NOT_IMPLEMENTED"
                or blueprint["independentVerifier"] != "NOT_DEPLOYED"
                or blueprint["authorization"] != "HOLD"
                or blueprint["accessDecision"] != "DENY"
                or len(blueprint["keyLifecycleControls"])
                    != len(KEY_LIFECYCLE_REQUIREMENTS)
                or len(blueprint["trustBoundaries"]) != len(TRUST_BOUNDARIES)):
            raise ValueError
        def controls(items: tuple[str, ...]) -> list[dict[str, str]]:
            return [{"requirementId": item, "status": "NOT_CONFIGURED",
                     "verification": "NOT_PERFORMED"} for item in items]
        return {
            "schema": "palaco.pp.recovery-002-verifier-trust-policy.v0",
            "reference": "PP-RECOVERY-002",
            "verifierBlueprintSha256": hashlib.sha256(verifier_blueprint_bytes).hexdigest(),
            "receiptProtocolSha256": blueprint["receiptProtocolSha256"],
            "binding": "STRICT_INTERNAL_SOURCE_CONSISTENCY_ONLY",
            "policyMode": "DENY_ALL_UNTIL_EXTERNAL_TRUST_CONFIGURED_AND_VERIFIED",
            "issuerRegistry": [],
            "trustedIssuerCount": 0,
            "trustAnchorImport": "PROHIBITED_IN_THIS_MODULE",
            "issuerRequirements": controls(ISSUER_REQUIREMENTS),
            "algorithmRules": controls(ALGORITHM_RULES),
            "allowedAlgorithms": [],
            "rotationRules": controls(ROTATION_RULES),
            "revocationRules": controls(REVOCATION_RULES),
            "defaultDenialRules": [
                {"reason": item, "decision": "DENY", "authorityEffect": "NONE"}
                for item in DEFAULT_DENIALS
            ],
            "keyMaterial": "NOT_PRESENT",
            "trustAnchorVerification": "NOT_PERFORMED",
            "issuerOnboarding": "NOT_IMPLEMENTED",
            "signatureVerification": "NOT_IMPLEMENTED",
            "keyRotation": "NOT_IMPLEMENTED",
            "revocationFeed": "NOT_CONFIGURED",
            "independentVerifier": "NOT_DEPLOYED",
            "externalAudit": "NOT_VERIFIED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "receiptAcceptance": "NOT_PERFORMED",
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
