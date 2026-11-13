"""Release integrity inventory for PP-RECOVERY-002 — NOT a releasable package.

Strictly rebuilds the 15-file contract chain, then emits original-byte
SHA-256 references, version locks, dependencies and explicit HOLD blockers.
No signing, SBOM attestation, release approval, software packaging, tests,
network I/O, authentication or PALACO ONE session creation.
"""
import hashlib

from review_044_change_impact import (
    prepare_change_impact_register, MAX_REGISTRY_BYTES, CHANGE_TYPES,
)
from review_044_contract_compatibility import (
    SCHEMAS, MAX_ASSURANCE_BYTES,
)
from review_044_security_assurance import SOURCE_ROLES, SOURCE_MAXIMA
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal
from review_044_recovery_decision import REQUIREMENTS

ERROR = "PP_RECOVERY_002_RELEASE_INTEGRITY_INVALID"
MAX_IMPACT_BYTES = 64 * 1024

ARTIFACT_ROLES = SOURCE_ROLES + (
    "SECURITY_ASSURANCE_DOSSIER",
    "CONTRACT_COMPATIBILITY_REGISTER",
    "CHANGE_IMPACT_REGISTER",
)
ARTIFACT_SCHEMAS = SCHEMAS + (
    "palaco.pp.recovery-002-security-assurance.v0",
    "palaco.pp.recovery-002-contract-compatibility.v0",
    "palaco.pp.recovery-002-change-impact.v0",
)
ARTIFACT_MAXIMA = SOURCE_MAXIMA + (
    MAX_ASSURANCE_BYTES, MAX_REGISTRY_BYTES, MAX_IMPACT_BYTES,
)
BLOCKERS = (
    "INDEPENDENT_EVIDENCE_NOT_VERIFIED",
    "SOURCE_AUTHENTICITY_NOT_ATTESTED",
    "REVIEWER_AUTHORITY_NOT_ESTABLISHED",
    "HUMAN_REVIEW_NOT_COMPLETED",
    "SIGNATURE_AND_RELEASE_PROVENANCE_NOT_ESTABLISHED",
    "COMPATIBILITY_NOT_EXTERNALLY_VERIFIED",
    "TRUST_TRANSITIONS_BLOCKED",
    "REVOCATION_PROCESSING_NOT_IMPLEMENTED",
    "PALACO_ONE_HANDOFF_BLOCKED",
)
RELEASE_GATES = (
    "SOURCE_PROVENANCE", "VERSION_COMPATIBILITY",
    "INDEPENDENT_VERIFICATION", "AUTHORIZED_HUMAN_REVIEW",
    "CRYPTOGRAPHIC_RELEASE_ATTESTATION", "DEPLOYMENT_APPROVAL",
)


def prepare_release_integrity_manifest(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes, revocation_bytes: bytes,
    assurance_bytes: bytes, compatibility_bytes: bytes, impact_bytes: bytes,
) -> dict[str, object]:
    """Bind all 15 original byte snapshots without authorizing a release."""
    try:
        original = (
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes, interface_bytes,
            transition_bytes, revocation_bytes,
            assurance_bytes, compatibility_bytes, impact_bytes,
        )
        if (len(original) != len(ARTIFACT_ROLES)
                or any(type(raw) is not bytes or not 0 < len(raw) <= maximum
                       for raw, maximum in zip(original, ARTIFACT_MAXIMA))):
            raise ValueError
        impact = _loads(impact_bytes, MAX_IMPACT_BYTES)
        request = impact.get("changeRequest") if type(impact) is dict else None
        if (type(request) is not dict
                or type(request.get("changedRole")) is not str
                or request["changedRole"] not in SOURCE_ROLES
                or type(request.get("changeType")) is not str
                or request["changeType"] not in CHANGE_TYPES):
            raise ValueError
        expected_impact = prepare_change_impact_register(
            *original[:-1], request["changedRole"], request["changeType"]
        )
        if not _strict_equal(impact, expected_impact):
            raise ValueError
        artifacts = []
        for i, (raw, role, schema, maximum) in enumerate(zip(
            original, ARTIFACT_ROLES, ARTIFACT_SCHEMAS, ARTIFACT_MAXIMA
        ), 1):
            decoded = _loads(raw, maximum)
            if (type(decoded) is not dict
                    or decoded.get("schema") != schema
                    or decoded.get("reference") != "PP-RECOVERY-002"):
                raise ValueError
            artifacts.append({
                "order": i,
                "role": role,
                "schema": schema,
                "version": "v0",
                "sha256": hashlib.sha256(raw).hexdigest(),
                "maxBytes": maximum,
                "externalAuthenticity": "NOT_ATTESTED",
                "signature": "NOT_VERIFIED",
            })
        return {
            "schema": "palaco.pp.recovery-002-release-integrity.v0",
            "reference": "PP-RECOVERY-002",
            "artifactCount": len(artifacts),
            "artifacts": artifacts,
            "dependencyEdges": [
                {"fromRole": ARTIFACT_ROLES[i - 1],
                 "toRole": ARTIFACT_ROLES[i],
                 "relationship": "REQUIRES_UPSTREAM_STRICT_REVALIDATION"}
                for i in range(1, len(ARTIFACT_ROLES))
            ],
            "impactScope": {
                "changedRole": request["changedRole"],
                "changeType": request["changeType"],
                "changeApplied": False,
                "reassessment": "REQUIRED",
            },
            "integrityScope": "LOCAL_BYTES_AND_STRICT_INTERNAL_CHAIN_ONLY",
            "rebuildPolicy": "ALL_DOWNSTREAM_ARTIFACTS_REQUIRE_REGENERATION",
            "supportedSchemaVersion": "v0",
            "mixedVersions": "DENY",
            "releaseBlockers": [
                {"blocker": item, "status": "OPEN"} for item in BLOCKERS
            ],
            "releaseGates": [
                {"gate": gate, "status": "BLOCKED",
                 "verification": "NOT_VERIFIED"}
                for gate in RELEASE_GATES
            ],
            "originalDecisionGates": [
                {"requirementId": name, "gate": "BLOCKED",
                 "verification": "NOT_VERIFIED"}
                for name, _ in REQUIREMENTS
            ],
            "softwareBundle": "NOT_CREATED",
            "sbom": "NOT_GENERATED",
            "provenanceAttestation": "NOT_ESTABLISHED",
            "signing": "NOT_PERFORMED",
            "runtimeTests": "NOT_EXECUTED",
            "deployment": "NOT_EXECUTED",
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
