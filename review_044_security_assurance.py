"""PP-RECOVERY-002 offline Security Assurance Dossier (non-authoritative).

Consolidates twelve original byte sources and previously defined security
requirements. Validates their internal chain using strict Python contracts,
but NEVER attests identity, proves external security controls, or grants access.
"""
import hashlib

from review_044_revocation_recovery import (
    prepare_revocation_recovery_contract, IMPACTS, RECOVERY_STEPS,
)
from review_044_reviewer_auth_contract import CONTROLS, GATES
from review_044_trust_transition import TRANSITIONS
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_SECURITY_ASSURANCE_INVALID"
MAX_REVOCATION_BYTES = 32 * 1024

SOURCE_ROLES = (
    "DECISION_DOSSIER", "REVIEW_QUEUE", "REVIEW_INTAKE",
    "VERIFICATION_PLAN", "OBSERVATION_REGISTER", "HANDOFF_MANIFEST",
    "RECEIPT_PROTOCOL", "REVIEWER_AUTH_REQUIREMENTS",
    "REVIEWER_SERVICE_BLUEPRINT", "REVIEWER_INTERFACE_CONTRACT",
    "TRUST_TRANSITION_PROTOCOL", "REVOCATION_RECOVERY_CONTRACT",
)
SOURCE_MAXIMA = (
    16 * 1024, 128 * 1024, 16 * 1024, 128 * 1024, 128 * 1024,
    32 * 1024, 64 * 1024, 32 * 1024, 32 * 1024, 32 * 1024,
    32 * 1024, MAX_REVOCATION_BYTES,
)
ASSURANCE_GAPS = (
    "SOURCE_AUTHENTICITY_NOT_ATTESTED",
    "SUBMITTER_IDENTITY_NOT_VERIFIED",
    "REVIEWER_AUTHENTICATION_NOT_ESTABLISHED",
    "REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "SUBJECT_BINDING_NOT_ESTABLISHED",
    "CRYPTOGRAPHIC_ASSERTIONS_NOT_VALIDATED",
    "SIGNED_RECEIPT_NOT_VERIFIED",
    "EXTERNAL_AUDIT_NOT_VERIFIED",
    "REVOCATION_PROPAGATION_NOT_IMPLEMENTED",
    "INDEPENDENT_HUMAN_REVIEW_NOT_COMPLETED",
    "PALACO_ONE_AUTHORIZATION_NOT_GRANTED",
)


def prepare_security_assurance_dossier(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes, revocation_bytes: bytes,
) -> dict[str, object]:
    """Return a bounded, fail-closed assurance gap inventory, never PASS."""
    try:
        all_sources = (
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes, interface_bytes,
            transition_bytes, revocation_bytes,
        )
        if any(type(raw) is not bytes or not 0 < len(raw) <= maximum
               for raw, maximum in zip(all_sources, SOURCE_MAXIMA)):
            raise ValueError
        observed = _loads(revocation_bytes, MAX_REVOCATION_BYTES)
        expected = prepare_revocation_recovery_contract(*all_sources[:-1])
        if not _strict_equal(observed, expected):
            raise ValueError
        if (observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or observed["revocationProcessing"] != "NOT_IMPLEMENTED"
                or observed["reviewerAuthority"] != "NOT_ESTABLISHED"
                or observed["palacoOneSession"] != "NOT_CREATED"
                or len(observed["revocationScenarios"]) != len(IMPACTS)
                or len(observed["recoveryChecklist"]) != len(RECOVERY_STEPS)):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-security-assurance.v0",
            "reference": "PP-RECOVERY-002",
            "sources": [
                {"order": i, "role": role, "sha256": hashlib.sha256(raw).hexdigest(),
                 "internalContract": "RECONSTRUCTED",
                 "externalAuthenticity": "NOT_ATTESTED"}
                for i, (role, raw) in enumerate(zip(SOURCE_ROLES, all_sources), 1)
            ],
            "contractBinding": "STRICT_INTERNAL_TWELVE_SOURCE_CONSISTENCY",
            "evidenceLimits": {
                "sourceByteDigests": "LOCAL_SHA256_ONLY",
                "cryptographicSignatures": "NOT_VERIFIED",
                "independentTimestamp": "ABSENT",
                "externalRevocationFeed": "NOT_CONFIGURED",
            },
            "reviewerControls": [
                {"controlId": control_id, "status": "NOT_ESTABLISHED"}
                for control_id, _ in CONTROLS
            ],
            "trustTransitions": [
                {"boundary": boundary, "status": "BLOCKED", "decision": "DENY"}
                for boundary, _, _, _ in TRANSITIONS
            ],
            "revocationRequirements": [
                {"event": event, "ownerService": owner,
                 "propagation": "NOT_EXECUTED", "decision": "DENY"}
                for event, owner, _ in IMPACTS
            ],
            "recoveryRequirements": [
                {"control": step, "status": "NOT_STARTED"}
                for step in RECOVERY_STEPS
            ],
            "decisionGates": [
                {"requirementId": name, "status": "BLOCKED",
                 "verification": "NOT_VERIFIED"}
                for name in GATES
            ],
            "unresolvedAssuranceGaps": [
                {"gapId": gap, "status": "OPEN",
                 "resolution": "INDEPENDENT_EXTERNAL_EVIDENCE_REQUIRED"}
                for gap in ASSURANCE_GAPS
            ],
            "independentVerification": "NOT_VERIFIED",
            "humanReview": "NOT_COMPLETED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
