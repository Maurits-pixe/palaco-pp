"""Fail-closed reviewer revocation and recovery specification.

No actual revocation is performed or proved. The returned controls describe
how future trusted services must invalidate derived authority. A local
unsigned record can never restore a reviewer, PALACO ONE session or release.
"""
import hashlib

from review_044_trust_transition import prepare_trust_transition_protocol
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal
from review_044_reviewer_interface_contract import REVOCATION

ERROR = "PP_RECOVERY_002_REVOCATION_RECOVERY_INVALID"
MAX_TRANSITION_BYTES = 32 * 1024

IMPACTS = (
    ("CREDENTIAL_REVOKED", "AUTHENTICATION", ("IDENTITY_ASSERTION", "REVIEWER_SCOPE_DECISION", "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE")),
    ("ROLE_REVOKED", "AUTHORIZATION", ("REVIEWER_SCOPE_DECISION", "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE")),
    ("SIGNING_KEY_REVOKED", "AUDIT", ("SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE",)),
    ("AUDIT_ANCHOR_COMPROMISED", "AUDIT", ("SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE",)),
)
RECOVERY_STEPS = (
    "INDEPENDENT_REVOCATION_EVENT_ATTESTATION",
    "QUARANTINE_DERIVED_ASSERTIONS_AND_DECISIONS",
    "INVALIDATE_NONCES_AND_EXPIRED_CREDENTIALS",
    "REVERIFY_ISSUER_KEYS_AND_FRESH_CREDENTIAL",
    "RECHECK_ROLE_SCOPE_AND_SEPARATION_OF_DUTIES",
    "VERIFY_NEW_RECEIPT_SIGNATURE_AND_EXTERNAL_AUDIT_ANCHOR",
    "REQUIRE_NEW_INDEPENDENT_HUMAN_REVIEW",
    "KEEP_HOLD_UNTIL_EXTERNAL_AUTHORIZED_DECISION",
)


def prepare_revocation_recovery_contract(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes,
) -> dict[str, object]:
    """Validate eleven source layers; only emit a permanently blocked recovery plan."""
    try:
        observed = _loads(transition_bytes, MAX_TRANSITION_BYTES)
        expected = prepare_trust_transition_protocol(
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes, interface_bytes,
        )
        if not _strict_equal(observed, expected):
            raise ValueError
        if (observed["implementation"] != "NOT_IMPLEMENTED"
                or observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or len(observed["transitions"]) != 3
                or any(t["status"] != "BLOCKED" or t["decision"] != "DENY"
                       for t in observed["transitions"])):
            raise ValueError
        if tuple(item[0] for item in IMPACTS) != tuple(item[0] for item in REVOCATION):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-revocation-recovery.v0",
            "reference": "PP-RECOVERY-002",
            "trustTransitionSha256": hashlib.sha256(transition_bytes).hexdigest(),
            "handoffManifestSha256": observed["handoffManifestSha256"],
            "revocationScenarios": [
                {
                    "event": event, "ownerService": owner,
                    "invalidates": list(invalidated),
                    "propagation": "REQUIRED_ACROSS_DEPENDENT_SERVICES",
                    "detection": "NOT_IMPLEMENTED",
                    "invalidationExecution": "NOT_EXECUTED",
                    "effectiveDecision": "DENY",
                    "restorePermission": "NONE",
                }
                for event, owner, invalidated in IMPACTS
            ],
            "recoveryChecklist": [
                {"order": i, "control": step, "status": "NOT_STARTED",
                 "independentVerification": "REQUIRED_EXTERNALLY",
                 "authorityEffect": "NONE"}
                for i, step in enumerate(RECOVERY_STEPS, 1)
            ],
            "trustTransitionOutcomes": [
                {"boundary": item["boundary"], "status": "BLOCKED",
                 "decision": "DENY"}
                for item in observed["transitions"]
            ],
            "revocationFeed": "NOT_CONFIGURED",
            "trustedClock": "NOT_CONFIGURED",
            "credentialAndRoleValidation": "NOT_PERFORMED",
            "auditAnchoring": "NOT_IMPLEMENTED",
            "revocationProcessing": "NOT_IMPLEMENTED",
            "reinstatement": "NOT_AUTHORIZED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "independentVerification": "NOT_VERIFIED",
            "humanReview": "NOT_COMPLETED",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
