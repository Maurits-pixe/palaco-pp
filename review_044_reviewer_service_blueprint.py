"""Three-boundary reviewer identity service blueprint for PP-RECOVERY-002.

Design-only, deterministic, fail-closed; NO identity provider integration,
credential validation, permission decision, signed audit entry, or HTTP API.
No attacker-controlled role claim can cross any trust boundary.
"""
import hashlib
import json

from review_044_reviewer_auth_contract import (
    prepare_reviewer_auth_contract, CONTROLS, GATES,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_REVIEWER_SERVICE_BLUEPRINT_INVALID"
MAX_CONTRACT_BYTES = 32 * 1024
BOUNDARIES = (
    ("AUTHENTICATION", "IDENTITY_ASSERTION", (
        "PINNED_TRUSTED_ISSUER", "AUDIENCE_AND_PURPOSE_BOUND_CHALLENGE",
        "SIGNATURE_AND_ALGORITHM_ALLOWLIST", "TRUSTED_CLOCK_EXPIRY",
        "NONCE_REPLAY_PREVENTION", "ISSUER_KEY_REVOCATION",
    )),
    ("AUTHORIZATION", "REVIEWER_SCOPE_DECISION", (
        "INDEPENDENT_ROLE_ATTESTATION", "EXPLICIT_PP_RECOVERY_002_SCOPE",
        "LEAST_PRIVILEGE_AND_SEPARATION", "REVOCATION_AND_CONFLICT_CHECK",
        "DENY_BY_DEFAULT", "NO_PALACO_ONE_SESSION_DELEGATION",
    )),
    ("AUDIT", "SIGNED_RECEIPT_AND_IMMUTABLE_AUDIT_REFERENCE", (
        "MANIFEST_BYTE_DIGEST_BOUND_RECEIPT", "REVIEWER_SIGNED_RECEIPT",
        "EXTERNALLY_ANCHORED_EVENT", "TRUSTED_TIMESTAMP",
        "INDEPENDENT_RECEIPT_VERIFICATION", "NO_LOCAL_CHAIN_AS_ATTESTATION",
    )),
)


def prepare_reviewer_service_blueprint(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes,
) -> dict[str, object]:
    """Validate all prior contracts and describe three still-unimplemented services."""
    try:
        supplied = _loads(auth_contract_bytes, MAX_CONTRACT_BYTES)
        expected = prepare_reviewer_auth_contract(
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes
        )
        if not _strict_equal(supplied, expected):
            raise ValueError
        if (supplied["identityProviderIntegration"] != "NOT_CONFIGURED"
                or supplied["reviewerAuthority"] != "NOT_ESTABLISHED"
                or supplied["authorization"] != "HOLD"
                or supplied["accessDecision"] != "DENY"):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-reviewer-service-blueprint.v0",
            "reference": "PP-RECOVERY-002",
            "reviewerAuthContractSha256": hashlib.sha256(auth_contract_bytes).hexdigest(),
            "handoffManifestSha256": supplied["handoffManifestSha256"],
            "reviewProtocolSha256": supplied["reviewProtocolSha256"],
            "services": [
                {"boundary": name, "futureOutput": output,
                 "requiredCapabilities": list(capabilities),
                 "implementation": "NOT_IMPLEMENTED",
                 "trustEvaluation": "NOT_PERFORMED",
                 "outboundAuthority": "NONE"}
                for name, output, capabilities in BOUNDARIES
            ],
            "requirements": [
                {"controlId": control_id, "status": "NOT_ESTABLISHED"}
                for control_id, _ in CONTROLS
            ],
            "decisionGates": [
                {"requirementId": name, "gate": "BLOCKED"}
                for name in GATES
            ],
            "crossBoundaryRule": "NO_SELF_REPORTED_CLAIM_CAN_GRANT_AUTHORITY",
            "identityProviderIntegration": "NOT_CONFIGURED",
            "credentialValidation": "NOT_PERFORMED",
            "authorizationService": "NOT_IMPLEMENTED",
            "auditService": "NOT_IMPLEMENTED",
            "reviewerAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "independentAudit": "NOT_ESTABLISHED",
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
