"""Fail-closed hypothetical change control for PP verifier trust policy.

Reconstructs the exact earlier policy from original bytes and produces a
non-applied risk assessment. No trust roots, issuers, algorithms, key material,
review decisions, tests, or account rights can be changed here.
"""
import hashlib

from review_044_verifier_trust_policy import (
    prepare_verifier_trust_policy_register, MAX_BLUEPRINT_BYTES,
    ISSUER_REQUIREMENTS, ALGORITHM_RULES, ROTATION_RULES,
    REVOCATION_RULES, DEFAULT_DENIALS,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_TRUST_POLICY_CHANGE_CONTROL_INVALID"
MAX_POLICY_BYTES = 64 * 1024

CHANGE_CATEGORIES = (
    ("ISSUER_POLICY", ISSUER_REQUIREMENTS),
    ("ALGORITHM_POLICY", ALGORITHM_RULES),
    ("KEY_ROTATION_POLICY", ROTATION_RULES),
    ("REVOCATION_POLICY", REVOCATION_RULES),
)
CHANGE_TYPES = (
    "PROPOSE_REQUIREMENT_REVISION", "PROPOSE_NEW_TRUST_ROOT",
    "PROPOSE_ALGORITHM_ALLOWLIST", "PROPOSE_KEY_ROTATION",
    "PROPOSE_REVOCATION_POLICY",
)
REASSESSMENT = (
    "ORIGINAL_SOURCE_AND_HANDOFF_BINDING",
    "INDEPENDENT_ISSUER_IDENTITY_AND_ROOT_ATTESTATION",
    "CRYPTOGRAPHIC_ALGORITHM_AND_KEY_USAGE",
    "KEY_ROTATION_OVERLAP_AND_ROLLBACK",
    "SIGNED_FRESH_REVOCATION_FEED",
    "NONCE_REPLAY_LEDGER_AND_TRUSTED_CLOCK",
    "EXTERNAL_AUDIT_AND_INCLUSION_PROOF",
    "INDEPENDENT_REVIEWER_ROLE_AND_SEPARATION_OF_DUTIES",
    "SEPARATE_AUTHORIZED_HUMAN_RELEASE_DECISION",
)
REQUIRED_REVIEW_ROLES = (
    "INDEPENDENT_SECURITY_REVIEWER",
    "AUTHORIZED_TRUST_POLICY_OWNER",
    "INDEPENDENT_RELEASE_ATTESTOR",
)


def prepare_trust_policy_change_control(
    source_bytes: tuple[bytes, ...],
    execution_plan_bytes: bytes,
    observation_register_bytes: bytes,
    evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes,
    receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes,
    trust_policy_bytes: bytes,
    change_category: str,
    change_type: str,
) -> dict[str, object]:
    """Build an unsigned *proposal*, with all gates and permissions DENY."""
    try:
        if (type(source_bytes) is not tuple or len(source_bytes) != 18
                or type(change_category) is not str
                or change_category not in dict(CHANGE_CATEGORIES)
                or type(change_type) is not str
                or change_type not in CHANGE_TYPES):
            raise ValueError
        supplied = _loads(trust_policy_bytes, MAX_POLICY_BYTES)
        expected = prepare_verifier_trust_policy_register(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes,
            receipt_protocol_bytes, verifier_blueprint_bytes,
        )
        if not _strict_equal(supplied, expected):
            raise ValueError
        if (supplied["policyMode"]
                != "DENY_ALL_UNTIL_EXTERNAL_TRUST_CONFIGURED_AND_VERIFIED"
                or supplied["trustedIssuerCount"] != 0
                or supplied["issuerRegistry"] != []
                or supplied["allowedAlgorithms"] != []
                or supplied["trustAnchorImport"] != "PROHIBITED_IN_THIS_MODULE"
                or supplied["authorization"] != "HOLD"
                or supplied["accessDecision"] != "DENY"):
            raise ValueError
        selected = dict(CHANGE_CATEGORIES)[change_category]
        return {
            "schema": "palaco.pp.recovery-002-trust-policy-change-control.v0",
            "reference": "PP-RECOVERY-002",
            "trustPolicySha256": hashlib.sha256(trust_policy_bytes).hexdigest(),
            "verifierBlueprintSha256": supplied["verifierBlueprintSha256"],
            "scope": "UNSIGNED_HYPOTHETICAL_POLICY_PROPOSAL_ONLY",
            "changeRequest": {
                "category": change_category,
                "changeType": change_type,
                "proposedTrustMaterial": "NOT_PROVIDED",
                "proposedPolicyBytes": "NOT_PROVIDED",
                "changeApplied": False,
                "externalReview": "NOT_STARTED",
            },
            "affectedPolicyRequirements": [
                {"order": i, "requirementId": item,
                 "assessment": "REASSESSMENT_REQUIRED",
                 "verification": "NOT_PERFORMED"}
                for i, item in enumerate(selected, 1)
            ],
            "transitiveImpact": [
                {"category": category,
                 "status": "REVALIDATION_REQUIRED",
                 "verification": "NOT_PERFORMED"}
                for category, _ in CHANGE_CATEGORIES
            ],
            "releaseReassessment": [
                {"order": i, "gate": item, "status": "BLOCKED",
                 "independentVerification": "NOT_PERFORMED"}
                for i, item in enumerate(REASSESSMENT, 1)
            ],
            "requiredIndependentReviewers": [
                {"role": role, "authentication": "NOT_ESTABLISHED",
                 "authority": "NOT_ESTABLISHED", "decision": "NOT_COMPLETED"}
                for role in REQUIRED_REVIEW_ROLES
            ],
            "defaultDenialReasons": [
                {"reason": reason, "decision": "DENY"}
                for reason in DEFAULT_DENIALS
            ],
            "changeAuthorization": "DENY",
            "deploymentAuthorization": "DENY",
            "issuerPromotion": "PROHIBITED",
            "algorithmPromotion": "PROHIBITED",
            "keyMaterial": "NOT_PRESENT",
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
