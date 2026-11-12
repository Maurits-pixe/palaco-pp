"""Fail-closed reviewer-authentication prerequisites for PP-RECOVERY-002.

This is a SECURITY REQUIREMENTS CONTRACT, not an authentication provider.
It cannot turn unsigned role claims into a reviewer, receipt, signature,
authorization, PALACO ONE session, or completed human review.
"""
import hashlib
import json

from review_044_review_protocol import (
    _manifest, _protocol, MAX_PROTOCOL_BYTES, _loads,
)
from review_044_recovery_decision import REQUIREMENTS

ERROR = "PP_RECOVERY_002_REVIEWER_AUTH_CONTRACT_INVALID"

CONTROLS = (
    ("TRUSTED_IDENTITY_PROVIDER", "Independent trusted reviewer identity provider is configured."),
    ("CRYPTOGRAPHIC_CHALLENGE", "Fresh audience-bound challenge and phishing-resistant authentication are verified."),
    ("REVIEWER_ROLE_ATTESTATION", "An independent issuer attests the reviewer's role and scope."),
    ("POLICY_SCOPE_MATCH", "Role policy explicitly covers PP-RECOVERY-002 and the requested review purpose."),
    ("REPLAY_AND_EXPIRY", "Replay prevention, expiry and revocation are checked against a trusted clock and store."),
    ("SEPARATION_OF_DUTIES", "Reviewer independence and conflicts of interest have been assessed."),
    ("SIGNED_RECEIPT", "Receipt is authenticated and signed over exact handoff manifest bytes."),
    ("AUDIT_ANCHOR", "Outcome is recorded in a tamper-evident independent audit system."),
)
GATES = tuple(name for name, _ in REQUIREMENTS)


def prepare_reviewer_auth_contract(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes,
    manifest_bytes: bytes, protocol_bytes: bytes,
) -> dict[str, object]:
    """Validate internal contracts; list all missing external security controls."""
    try:
        manifest = _manifest(
            manifest_bytes, dossier_bytes, queue_bytes, intake_bytes,
            plan_bytes, observations_bytes
        )
        if type(protocol_bytes) is not bytes or not 0 < len(protocol_bytes) <= MAX_PROTOCOL_BYTES:
            raise ValueError
        protocol = _protocol(
            protocol_bytes, hashlib.sha256(manifest_bytes).hexdigest()
        )
        if (manifest["deliveryStatus"] != "NOT_DELIVERED"
                or manifest["receiptStatus"] != "NOT_ACKNOWLEDGED"
                or protocol["reviewerAuthority"] != "NOT_ESTABLISHED"):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-reviewer-auth-contract.v0",
            "reference": "PP-RECOVERY-002",
            "handoffManifestSha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "reviewProtocolSha256": hashlib.sha256(protocol_bytes).hexdigest(),
            "unsignedClaimCount": len(protocol["events"]),
            "requiredControls": [
                {"order": i, "controlId": key, "requirement": detail,
                 "status": "NOT_ESTABLISHED",
                 "validationMode": "EXTERNAL_AUTHENTICATED_VERIFICATION_REQUIRED"}
                for i, (key, detail) in enumerate(CONTROLS, 1)
            ],
            "decisionGates": [
                {"requirementId": name, "gate": "BLOCKED",
                 "verification": "NOT_VERIFIED"}
                for name in GATES
            ],
            "trustBoundary": "NO_TRUST_TRANSITION_FROM_UNSIGNED_CLAIMS",
            "identityProviderIntegration": "NOT_CONFIGURED",
            "credentialValidation": "NOT_PERFORMED",
            "recipientAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "reviewerIndependence": "NOT_ESTABLISHED",
            "receiptVerification": "NOT_VERIFIED",
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
