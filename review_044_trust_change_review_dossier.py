"""Unsigned, unsent change review dossier. No approval or trust mutation.

Rebuilds all prior local contracts and type-exactly binds the hypothetical
change-control report. Lists required external evidence and reviewer roles,
without accepting evidence or escalating a local role claim to authority.
"""
import hashlib
from review_044_trust_policy_change_control import (
    prepare_trust_policy_change_control, CHANGE_CATEGORIES,
    REQUIRED_REVIEW_ROLES, REASSESSMENT,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_TRUST_CHANGE_REVIEW_DOSSIER_INVALID"
MAX_CHANGE_CONTROL_BYTES = 64 * 1024

EXTERNAL_EVIDENCE = (
    ("PINNED_TRUST_ROOT_AND_ISSUER_PROVENANCE", "INDEPENDENT_SECURITY_REVIEWER"),
    ("SIGNED_CANONICAL_POLICY_DIFF", "AUTHORIZED_TRUST_POLICY_OWNER"),
    ("KEY_AND_ALGORITHM_COMPATIBILITY_ASSESSMENT", "INDEPENDENT_SECURITY_REVIEWER"),
    ("ROTATION_AND_REVOKE_SIGNED_FEED_EVIDENCE", "INDEPENDENT_SECURITY_REVIEWER"),
    ("NONCE_REPLAY_TRUSTED_CLOCK_RECHECK", "INDEPENDENT_SECURITY_REVIEWER"),
    ("IMMUTABLE_EXTERNAL_AUDIT_INCLUSION_PROOF", "INDEPENDENT_RELEASE_ATTESTOR"),
    ("INDEPENDENT_IDENTITY_SCOPE_SEPARATION_OF_DUTIES", "AUTHORIZED_TRUST_POLICY_OWNER"),
    ("REPRODUCIBLE_NEGATIVE_AND_REGRESSION_TEST_PROVENANCE", "INDEPENDENT_RELEASE_ATTESTOR"),
    ("SEPARATE_SIGNED_HUMAN_DECISION", "AUTHORIZED_TRUST_POLICY_OWNER"),
)
DECISION_CHECKPOINTS = (
    "SOURCE_HASHES_REBUILT_AND_ATTESTED",
    "EXTERNAL_EVIDENCE_INDEPENDENTLY_AUTHENTICATED",
    "REVIEWER_IDENTITY_SCOPE_AND_REVOCATION_VERIFIED",
    "SIGNED_POLICY_DIFF_INDEPENDENTLY_APPROVED",
    "SECURITY_AND_REGRESSION_EVIDENCE_REVIEWED",
    "EXTERNAL_AUDIT_AND_TRUSTED_TIME_VERIFIED",
    "SEPARATE_HUMAN_RELEASE_DECISION_CONFIRMED",
)


def prepare_trust_change_review_dossier(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes,
) -> dict[str, object]:
    """Strictly bind the change request, returning blocked independent-review requirements."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        change = _loads(change_control_bytes, MAX_CHANGE_CONTROL_BYTES)
        request = change.get("changeRequest") if type(change) is dict else None
        if (type(request) is not dict
                or type(request.get("category")) is not str
                or request["category"] not in dict(CHANGE_CATEGORIES)
                or type(request.get("changeType")) is not str):
            raise ValueError
        expected = prepare_trust_policy_change_control(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes,
            request["category"], request["changeType"],
        )
        if not _strict_equal(change, expected):
            raise ValueError
        if (request["changeApplied"] is not False
                or change["trustedIssuerCount"] != 0
                or change["allowedAlgorithms"] != []
                or change["changeAuthorization"] != "DENY"
                or change["authorization"] != "HOLD"
                or change["accessDecision"] != "DENY"):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-trust-change-review-dossier.v0",
            "reference": "PP-RECOVERY-002",
            "changeControlSha256": hashlib.sha256(change_control_bytes).hexdigest(),
            "trustPolicySha256": change["trustPolicySha256"],
            "sourceBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "dossierProvenance": "UNSIGNED_LOCAL_REVIEW_REQUEST_NOT_SENT",
            "changeScope": {
                "category": request["category"],
                "changeType": request["changeType"],
                "changeApplied": False,
                "reviewStatus": "NOT_STARTED",
            },
            "affectedRequirements": [
                {"requirementId": row["requirementId"],
                 "reassessment": "REQUIRED", "verified": False}
                for row in change["affectedPolicyRequirements"]
            ],
            "externalEvidenceRequirements": [
                {"order": index, "evidenceId": evidence, "requiredRole": role,
                 "evidenceReceived": "NOT_PROVIDED",
                 "independentVerification": "NOT_PERFORMED"}
                for index, (evidence, role) in enumerate(EXTERNAL_EVIDENCE, 1)
            ],
            "requiredReviewers": [
                {"role": role, "authentication": "NOT_ESTABLISHED",
                 "authority": "NOT_ESTABLISHED",
                 "decision": "NOT_COMPLETED"}
                for role in REQUIRED_REVIEW_ROLES
            ],
            "reassessmentGates": [
                {"gate": name, "status": "BLOCKED",
                 "verification": "NOT_PERFORMED"}
                for name in REASSESSMENT
            ],
            "decisionCheckpoints": [
                {"order": index, "checkpointId": name,
                 "status": "BLOCKED"}
                for index, name in enumerate(DECISION_CHECKPOINTS, 1)
            ],
            "handoffDelivery": "NOT_SENT",
            "signedReceipt": "NOT_AVAILABLE",
            "externalAudit": "NOT_VERIFIED",
            "independentReview": "NOT_COMPLETED",
            "decision": "DENY",
            "issuerPromotion": "PROHIBITED",
            "algorithmPromotion": "PROHIBITED",
            "trustedIssuerCount": 0,
            "allowedAlgorithms": [],
            "keyMaterial": "NOT_PRESENT",
            "changeApplied": False,
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
