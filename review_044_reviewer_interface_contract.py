"""Design-only, deny-by-default interface contracts for three reviewer services.

This module validates the prior eight-file blueprint and returns machine-
readable future request/response envelopes, failure/revocation semantics,
and isolation rules. It cannot execute, authenticate, authorize or audit.
"""
import hashlib
import json

from review_044_reviewer_service_blueprint import (
    prepare_reviewer_service_blueprint, BOUNDARIES,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_REVIEWER_INTERFACE_INVALID"
MAX_BLUEPRINT_BYTES = 32 * 1024
ERROR_CODES = (
    "MALFORMED_REQUEST", "UNSUPPORTED_VERSION", "UNTRUSTED_ISSUER",
    "INVALID_SIGNATURE", "AUDIENCE_MISMATCH", "PURPOSE_MISMATCH",
    "CHALLENGE_EXPIRED", "REPLAY_DETECTED", "CREDENTIAL_REVOKED",
    "ROLE_ATTESTATION_MISSING", "SCOPE_DENIED", "CONFLICT_OF_INTEREST",
    "AUDIT_UNAVAILABLE", "ANCHOR_NOT_VERIFIED", "TRUSTED_TIME_UNAVAILABLE",
    "DEPENDENCY_UNAVAILABLE",
)
REVOCATION = (
    ("CREDENTIAL_REVOKED", "AUTHENTICATION", "DENY"),
    ("ROLE_REVOKED", "AUTHORIZATION", "DENY"),
    ("SIGNING_KEY_REVOKED", "AUDIT", "DENY"),
    ("AUDIT_ANCHOR_COMPROMISED", "AUDIT", "DENY"),
)
INTERFACES = (
    (
        "AUTHENTICATION", "POST", "/internal/reviewer-auth/assert",
        ("contractVersion", "challengeId", "audience", "purpose", "credentialProof", "manifestSha256"),
        ("assertionId", "subjectPseudonym", "issuer", "audience", "purpose", "issuedAt", "expiresAt", "challengeId", "verificationProof"),
        "IDENTITY_ASSERTION",
    ),
    (
        "AUTHORIZATION", "POST", "/internal/reviewer-auth/scope",
        ("contractVersion", "identityAssertionRef", "roleAttestation", "requestedScope", "manifestSha256"),
        ("decisionId", "scope", "policyVersion", "reviewerAssertionRef", "expiresAt", "decisionProof"),
        "REVIEWER_SCOPE_DECISION",
    ),
    (
        "AUDIT", "POST", "/internal/reviewer-auth/receipt",
        ("contractVersion", "reviewerDecisionRef", "manifestSha256", "signedReceipt", "auditNonce"),
        ("receiptRef", "manifestSha256", "signatureRef", "trustedTimestamp", "externalAnchorRef", "anchorProof"),
        "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE",
    ),
)


def prepare_reviewer_interface_contract(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
) -> dict[str, object]:
    """Validate source chain and emit unimplemented, non-operational APIs."""
    try:
        source = _loads(blueprint_bytes, MAX_BLUEPRINT_BYTES)
        expected = prepare_reviewer_service_blueprint(
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes,
        )
        if not _strict_equal(source, expected):
            raise ValueError
        if (len(source["services"]) != len(BOUNDARIES)
                or any(row["implementation"] != "NOT_IMPLEMENTED"
                       or row["outboundAuthority"] != "NONE"
                       for row in source["services"])):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-reviewer-interface-contract.v0",
            "reference": "PP-RECOVERY-002",
            "blueprintSha256": hashlib.sha256(blueprint_bytes).hexdigest(),
            "handoffManifestSha256": source["handoffManifestSha256"],
            "interfaces": [
                {
                    "service": service, "method": method, "proposedPath": path,
                    "requestFields": list(request), "futureSuccessFields": list(response),
                    "futureOutput": output, "implementation": "NOT_IMPLEMENTED",
                    "endpointEnabled": False, "acceptsSelfReportedRoleClaims": False,
                    "responseToday": "DENY_UNIMPLEMENTED",
                }
                for service, method, path, request, response, output in INTERFACES
            ],
            "errorPolicy": {
                "knownFailureCodes": list(ERROR_CODES),
                "unknownError": "DENY_UNKNOWN_FAILURE",
                "onSignatureFailure": "DENY",
                "onClockOrNonceFailure": "DENY",
                "onRevocationLookupFailure": "DENY",
                "onAuditUnavailable": "DENY",
                "onPolicyMismatch": "DENY",
                "errorDetails": "NO_CREDENTIALS_OR_PRIVATE_KEYS_IN_LOGS",
            },
            "revocationPolicy": [
                {"event": name, "ownerService": owner, "effect": effect,
                 "requiresFreshIndependentVerification": True}
                for name, owner, effect in REVOCATION
            ],
            "separation": {
                "authenticationCannotAuthorize": True,
                "authorizationCannotAuthenticate": True,
                "auditCannotGrant": True,
                "untrustedLocalClaimsNeverElevate": True,
                "singleServiceCannotReleaseHold": True,
                "palacoOneSessionCreation": "PROHIBITED",
            },
            "integrationState": "NOT_IMPLEMENTED",
            "independentVerification": "NOT_VERIFIED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "humanReview": "NOT_COMPLETED",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
