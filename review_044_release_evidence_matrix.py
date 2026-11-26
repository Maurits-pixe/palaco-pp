"""Release Evidence Matrix for PP-RECOVERY-002: requirements, not attestations.

Rebuilds the 15-source Release Integrity Manifest and demands exact typed
equality with the supplied original. All evidence gaps remain missing.
No reviewer credentials, original evidence, signatures or release are verified.
"""
import hashlib

from review_044_release_integrity import (
    prepare_release_integrity_manifest, ARTIFACT_MAXIMA, RELEASE_GATES,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_RELEASE_EVIDENCE_MATRIX_INVALID"
MAX_RELEASE_MANIFEST_BYTES = 64 * 1024

REQUIREMENTS = (
    ("SOURCE_PROVENANCE", (
        "ORIGINAL_SOURCE_BYTES_FROM_TRUSTED_CUSTODIAN",
        "INDEPENDENT_PROVENANCE_ATTESTATION",
        "SOURCE_HASH_AND_SIGNER_VALIDATION",
    ), "INDEPENDENT_SOURCE_CUSTODIAN"),
    ("VERSION_COMPATIBILITY", (
        "VERSION_LOCK_AND_DEPENDENCY_RECHECK",
        "INDEPENDENT_BREAKING_CHANGE_ASSESSMENT",
        "SUPPORTED_TARGET_RUNTIME_DECLARATION",
    ), "INDEPENDENT_COMPATIBILITY_REVIEWER"),
    ("INDEPENDENT_VERIFICATION", (
        "REPRODUCIBLE_TEST_RESULTS_WITH_PROVENANCE",
        "INDEPENDENT_IDENTITY_AND_SUBJECT_BINDING",
        "NONCE_REVOCATION_AND_CLOCK_CHECK",
    ), "INDEPENDENT_TECHNICAL_VERIFIER"),
    ("AUTHORIZED_HUMAN_REVIEW", (
        "INDEPENDENT_REVIEWER_AUTHENTICATION",
        "SIGNED_ROLE_SCOPE_AND_INDEPENDENCE_ATTESTATION",
        "RECORDED_HUMAN_DECISION_WITH_EXACT_MANIFEST_BINDING",
    ), "AUTHORIZED_INDEPENDENT_HUMAN_REVIEWER"),
    ("CRYPTOGRAPHIC_RELEASE_ATTESTATION", (
        "REPRODUCIBLE_SBOM_AND_BUILD_PROVENANCE",
        "TRUSTED_SIGNING_KEY_AND_SIGNATURE_VALIDATION",
        "EXTERNALLY_ANCHORED_TIMESTAMP_AND_AUDIT",
    ), "INDEPENDENT_RELEASE_ATTESTOR"),
    ("DEPLOYMENT_APPROVAL", (
        "APPROVED_RELEASE_POLICY_AND_ENVIRONMENT",
        "AUTHORIZED_SEPARATE_DEPLOYMENT_DECISION",
        "ROLLBACK_AND_REVOCATION_READINESS",
    ), "AUTHORIZED_RELEASE_OPERATOR"),
)


def prepare_release_evidence_matrix(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes, revocation_bytes: bytes,
    assurance_bytes: bytes, compatibility_bytes: bytes, impact_bytes: bytes,
    release_manifest_bytes: bytes,
) -> dict[str, object]:
    """Build six BLOCKED release evidence rows after strict 16-byte-source checks."""
    try:
        originals = (
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes, interface_bytes,
            transition_bytes, revocation_bytes, assurance_bytes,
            compatibility_bytes, impact_bytes,
        )
        if len(originals) != len(ARTIFACT_MAXIMA):
            raise ValueError
        observed = _loads(release_manifest_bytes, MAX_RELEASE_MANIFEST_BYTES)
        expected = prepare_release_integrity_manifest(*originals)
        if not _strict_equal(observed, expected):
            raise ValueError
        if (len(observed["releaseGates"]) != len(RELEASE_GATES)
                or observed["releaseReadiness"] != "NOT_READY"
                or observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or observed["signing"] != "NOT_PERFORMED"
                or observed["deployment"] != "NOT_EXECUTED"):
            raise ValueError
        if tuple(x[0] for x in REQUIREMENTS) != RELEASE_GATES:
            raise ValueError
        rows = []
        for order, (gate, evidence, reviewer) in enumerate(REQUIREMENTS, 1):
            existing = observed["releaseGates"][order - 1]
            if (existing["gate"] != gate or existing["status"] != "BLOCKED"
                    or existing["verification"] != "NOT_VERIFIED"):
                raise ValueError
            rows.append({
                "order": order,
                "releaseGate": gate,
                "requiredEvidence": [
                    {"evidenceId": evidence_id, "status": "MISSING",
                     "independentVerification": "NOT_PERFORMED"}
                    for evidence_id in evidence
                ],
                "requiredIndependentRole": reviewer,
                "reviewerAuthentication": "NOT_ESTABLISHED",
                "reviewerAuthority": "NOT_ESTABLISHED",
                "evidenceAcceptance": "NOT_PERFORMED",
                "reviewDecision": "NOT_COMPLETED",
                "gate": "BLOCKED",
                "decision": "DENY",
            })
        return {
            "schema": "palaco.pp.recovery-002-release-evidence-matrix.v0",
            "reference": "PP-RECOVERY-002",
            "releaseIntegrityManifestSha256": hashlib.sha256(release_manifest_bytes).hexdigest(),
            "integrityBinding": "STRICT_INTERNAL_SIXTEEN_SOURCE_CONSISTENCY",
            "evidenceMatrix": rows,
            "evidenceItemCount": sum(len(row["requiredEvidence"]) for row in rows),
            "unmetReleaseGateCount": len(rows),
            "externalEvidenceIncluded": False,
            "independentVerification": "NOT_VERIFIED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "releaseReadiness": "NOT_READY",
            "softwareBundle": "NOT_CREATED",
            "sbom": "NOT_GENERATED",
            "signing": "NOT_PERFORMED",
            "deployment": "NOT_EXECUTED",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
