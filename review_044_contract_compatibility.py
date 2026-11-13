"""Strict version-compatibility register for 12 PP-RECOVERY-002 source contracts.

Read-only design-time verification. No schema migration, test execution,
runtime authorization, account mutation, or upgrade is performed.
"""
import hashlib
import json

from review_044_security_assurance import (
    prepare_security_assurance_dossier, SOURCE_ROLES, SOURCE_MAXIMA,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_COMPATIBILITY_INVALID"
MAX_ASSURANCE_BYTES = 64 * 1024
SCHEMAS = (
    "palaco.pp.recovery-002-decision-dossier.v0",
    "palaco.pp.recovery-002-human-review-queue.v0",
    "palaco.pp.recovery-002-review-intake.v0",
    "palaco.pp.recovery-002-verification-plan.v0",
    "palaco.pp.recovery-002-observation-register.v0",
    "palaco.pp.recovery-002-human-review-handoff.v0",
    "palaco.pp.recovery-002-review-protocol.v0",
    "palaco.pp.recovery-002-reviewer-auth-contract.v0",
    "palaco.pp.recovery-002-reviewer-service-blueprint.v0",
    "palaco.pp.recovery-002-reviewer-interface-contract.v0",
    "palaco.pp.recovery-002-trust-transition.v0",
    "palaco.pp.recovery-002-revocation-recovery.v0",
)
UPGRADE_RULES = (
    "UNKNOWN_SCHEMA_REJECT",
    "MIXED_VERSION_REJECT",
    "SILENT_MIGRATION_PROHIBITED",
    "FORWARD_VERSION_UNSUPPORTED",
    "STRICT_REVALIDATION_REQUIRED",
    "EXTERNAL_ATTESTATION_REQUIRED_FOR_AUTHORITY",
)


def build_contract_compatibility_register(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes, revocation_bytes: bytes,
    assurance_bytes: bytes,
) -> dict[str, object]:
    """Bind an exact assurance snapshot to the original twelve v0 contracts."""
    try:
        original = (
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes, interface_bytes,
            transition_bytes, revocation_bytes,
        )
        if len(original) != len(SCHEMAS) or len(original) != len(SOURCE_MAXIMA):
            raise ValueError
        assurance = _loads(assurance_bytes, MAX_ASSURANCE_BYTES)
        expected = prepare_security_assurance_dossier(*original)
        if not _strict_equal(assurance, expected):
            raise ValueError
        contracts = []
        for i, (raw, role, maximum, schema) in enumerate(
            zip(original, SOURCE_ROLES, SOURCE_MAXIMA, SCHEMAS), 1
        ):
            parsed = _loads(raw, maximum)
            if (type(parsed) is not dict or parsed.get("schema") != schema
                    or parsed.get("reference") != "PP-RECOVERY-002"):
                raise ValueError
            digest = hashlib.sha256(raw).hexdigest()
            if (assurance["sources"][i - 1]["role"] != role
                    or assurance["sources"][i - 1]["sha256"] != digest):
                raise ValueError
            contracts.append({
                "order": i,
                "role": role,
                "schema": schema,
                "majorVersion": 0,
                "sha256": digest,
                "compatibility": "INTERNALLY_MATCHED_V0_ONLY",
                "externalAttestation": "NOT_VERIFIED",
                "migration": "NOT_PERFORMED",
            })
        return {
            "schema": "palaco.pp.recovery-002-contract-compatibility.v0",
            "reference": "PP-RECOVERY-002",
            "securityAssuranceSha256": hashlib.sha256(assurance_bytes).hexdigest(),
            "contracts": contracts,
            "supportedVersion": "v0",
            "mixedVersionAcceptance": "DENY",
            "upgradeRules": list(UPGRADE_RULES),
            "migrationService": "NOT_IMPLEMENTED",
            "breakingChangeEvaluation": "REQUIRES_NEW_INDEPENDENT_REVIEW",
            "compatibilityScope": "STRICT_INTERNAL_SOURCE_CONSISTENCY_ONLY",
            "externallyVerifiedCompatibility": "NOT_VERIFIED",
            "decisionGates": [
                {"requirementId": gate["requirementId"], "gate": "BLOCKED",
                 "verification": "NOT_VERIFIED"}
                for gate in assurance["decisionGates"]
            ],
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
