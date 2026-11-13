"""Change-impact planning for PP-RECOVERY-002, never an approval.

Strictly revalidates the original 12 contracts, assurance dossier and
compatibility register. A declared change is hypothetical; nothing is edited,
migrated, tested, merged, authorized, deployed or attested.
"""
import hashlib

from review_044_contract_compatibility import build_contract_compatibility_register
from review_044_security_assurance import SOURCE_ROLES
from review_044_recovery_decision import REQUIREMENTS
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_CHANGE_IMPACT_INVALID"
MAX_REGISTRY_BYTES = 64 * 1024
CHANGE_TYPES = ("SCHEMA_CHANGE", "VERSION_CHANGE", "CONTENT_CHANGE", "POLICY_CHANGE")
DOWNSTREAM_ARTIFACTS = ("SECURITY_ASSURANCE_DOSSIER", "CONTRACT_COMPATIBILITY_REGISTER")


def prepare_change_impact_register(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes, revocation_bytes: bytes,
    assurance_bytes: bytes, compatibility_bytes: bytes,
    changed_role: str, change_type: str,
) -> dict[str, object]:
    """Conservatively flag changed role and all transitive downstream contracts."""
    try:
        if (type(changed_role) is not str or changed_role not in SOURCE_ROLES
                or type(change_type) is not str or change_type not in CHANGE_TYPES):
            raise ValueError
        sources = (dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
                   observations_bytes, manifest_bytes, protocol_bytes,
                   auth_contract_bytes, blueprint_bytes, interface_bytes,
                   transition_bytes, revocation_bytes, assurance_bytes)
        expected = build_contract_compatibility_register(*sources)
        supplied = _loads(compatibility_bytes, MAX_REGISTRY_BYTES)
        if not _strict_equal(supplied, expected):
            raise ValueError
        if (supplied["authorization"] != "HOLD" or
                supplied["accessDecision"] != "DENY" or
                supplied["mixedVersionAcceptance"] != "DENY"):
            raise ValueError
        start = SOURCE_ROLES.index(changed_role)
        affected = list(SOURCE_ROLES[start:])
        return {
            "schema": "palaco.pp.recovery-002-change-impact.v0",
            "reference": "PP-RECOVERY-002",
            "compatibilityRegisterSha256": hashlib.sha256(compatibility_bytes).hexdigest(),
            "changeRequest": {
                "changedRole": changed_role,
                "changeType": change_type,
                "scope": "HYPOTHETICAL_NOT_APPLIED",
                "proposedBytes": "NOT_PROVIDED",
                "changeVerification": "NOT_PERFORMED",
            },
            "impactAnalysis": [
                {
                    "order": i + 1, "role": role,
                    "impact": "CHANGED_SOURCE" if i == start else "TRANSITIVE_DEPENDENCY",
                    "requiredAction": "REBUILD_AND_STRICTLY_REVALIDATE",
                    "verification": "NOT_PERFORMED",
                    "migration": "NOT_AUTHORIZED",
                }
                for i, role in enumerate(SOURCE_ROLES) if i >= start
            ],
            "affectedAggregateArtifacts": [
                {"artifact": name, "action": "REGENERATE_FROM_VALIDATED_SOURCES",
                 "status": "NOT_STARTED"}
                for name in DOWNSTREAM_ARTIFACTS
            ],
            "impactCount": len(affected),
            "gateReassessment": [
                {"requirementId": name, "reassessment": "REQUIRED",
                 "gate": "BLOCKED", "verification": "NOT_VERIFIED"}
                for name, _ in REQUIREMENTS
            ],
            "changePolicy": {
                "unknownSchema": "DENY",
                "mixedVersions": "DENY",
                "breakingChange": "INDEPENDENT_REVIEW_REQUIRED",
                "automaticMigration": "PROHIBITED",
                "unreviewedChange": "DENY",
                "releaseWithoutExternalEvidence": "DENY",
            },
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
