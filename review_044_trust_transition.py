"""Offline PP-RECOVERY-002 trust transition *specification*, never a runtime.

This design validates all ten source layers through the existing strict
contract chain. No proof, nonce, reviewer assertion or local receipt can
advance a transition. In particular, it cannot create a PALACO ONE session.
"""
import hashlib

from review_044_reviewer_interface_contract import (
    prepare_reviewer_interface_contract,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_TRUST_TRANSITION_INVALID"
MAX_INTERFACE_BYTES = 32 * 1024
TRANSITIONS = (
    (
        "AUTHENTICATION_TO_AUTHORIZATION",
        "IDENTITY_ASSERTION",
        "REVIEWER_SCOPE_DECISION",
        (
            "EXTERNAL_IDENTITY_ASSERTION_SIGNATURE_VERIFIED",
            "ISSUER_AUDIENCE_PURPOSE_AND_NONCE_VERIFIED",
            "TRUSTED_TIME_AND_CREDENTIAL_REVOCATION_VERIFIED",
            "INDEPENDENT_REVIEWER_ROLE_ATTESTATION_REQUIRED",
        ),
    ),
    (
        "AUTHORIZATION_TO_AUDIT",
        "REVIEWER_SCOPE_DECISION",
        "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE",
        (
            "POLICY_SCOPE_AND_LEAST_PRIVILEGE_VERIFIED",
            "SEPARATION_OF_DUTIES_AND_ROLE_REVOCATION_VERIFIED",
            "EXACT_HANDOFF_MANIFEST_SHA256_BOUND",
            "INDEPENDENT_SIGNING_AND_EXTERNAL_AUDIT_REQUIRED",
        ),
    ),
    (
        "AUDIT_TO_MANUAL_REVIEW",
        "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE",
        "EXTERNAL_AUTHORIZED_HUMAN_REVIEW",
        (
            "RECEIPT_SIGNATURE_INDEPENDENTLY_VERIFIED",
            "EXTERNAL_AUDIT_ANCHOR_VERIFIED",
            "TRUSTED_TIMESTAMP_AND_REVOCATION_VERIFIED",
            "SEPARATE_HUMAN_REVIEW_DECISION_REQUIRED",
        ),
    ),
)
FAILURES = (
    "UNKNOWN_OR_MALFORMED_PROOF",
    "ISSUER_OR_AUDIENCE_MISMATCH",
    "EXPIRED_OR_REPLAYED_CHALLENGE",
    "CREDENTIAL_OR_ROLE_REVOKED",
    "INVALID_OR_MISSING_SIGNATURE",
    "SCOPE_OR_INDEPENDENCE_VIOLATION",
    "AUDIT_UNAVAILABLE_OR_UNVERIFIABLE",
    "TRUSTED_CLOCK_UNAVAILABLE",
    "DEPENDENCY_UNAVAILABLE",
)


def prepare_trust_transition_protocol(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes,
    manifest_bytes: bytes, protocol_bytes: bytes,
    auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes,
) -> dict[str, object]:
    """Return fixed BLOCKED transitions after strict source-chain validation."""
    try:
        observed = _loads(interface_bytes, MAX_INTERFACE_BYTES)
        expected = prepare_reviewer_interface_contract(
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes,
        )
        if not _strict_equal(observed, expected):
            raise ValueError
        if (observed["integrationState"] != "NOT_IMPLEMENTED"
                or observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or any(x["endpointEnabled"] is not False
                       or x["responseToday"] != "DENY_UNIMPLEMENTED"
                       for x in observed["interfaces"])):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-trust-transition.v0",
            "reference": "PP-RECOVERY-002",
            "interfaceContractSha256": hashlib.sha256(interface_bytes).hexdigest(),
            "handoffManifestSha256": observed["handoffManifestSha256"],
            "transitions": [
                {
                    "sequence": i,
                    "boundary": boundary,
                    "requiredInput": required_input,
                    "futureOutput": future_output,
                    "independentPreconditions": list(prerequisites),
                    "proofAcceptance": "NOT_IMPLEMENTED",
                    "status": "BLOCKED",
                    "decision": "DENY",
                }
                for i, (boundary, required_input, future_output, prerequisites)
                in enumerate(TRANSITIONS, 1)
            ],
            "failureBehavior": [
                {"failure": code, "effect": "DENY",
                 "releaseEffect": "NONE"}
                for code in FAILURES
            ],
            "replayState": "NOT_CONFIGURED",
            "revocationValidation": "NOT_PERFORMED",
            "independentEvidenceVerification": "NOT_PERFORMED",
            "crossBoundaryRule": "NO_CLAIM_ALONE_CAN_ADVANCE_ANY_TRANSITION",
            "implementation": "NOT_IMPLEMENTED",
            "reviewerAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "externalHumanReview": "NOT_COMPLETED",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
