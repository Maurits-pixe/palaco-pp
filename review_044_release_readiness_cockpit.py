"""PP-RECOVERY-002 read-only Release Readiness Cockpit snapshot.

Reconstructs the release evidence matrix from all 16 original documents and
demands exact typed equality with the 17th. This is local consistency only:
no external verification, execution, test, authentication or release.
"""
import hashlib

from review_044_release_evidence_matrix import (
    prepare_release_evidence_matrix, REQUIREMENTS,
)
from review_044_release_integrity import BLOCKERS, ARTIFACT_MAXIMA
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal
from review_044_recovery_decision import REQUIREMENTS as DECISION_REQUIREMENTS

ERROR = "PP_RECOVERY_002_READINESS_COCKPIT_INVALID"
MAX_MATRIX_BYTES = 32 * 1024


def prepare_release_readiness_cockpit(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes, manifest_bytes: bytes,
    protocol_bytes: bytes, auth_contract_bytes: bytes, blueprint_bytes: bytes,
    interface_bytes: bytes, transition_bytes: bytes, revocation_bytes: bytes,
    assurance_bytes: bytes, compatibility_bytes: bytes, impact_bytes: bytes,
    release_manifest_bytes: bytes, matrix_bytes: bytes,
) -> dict[str, object]:
    """Build a non-authoritative dashboard with every release gate blocked."""
    try:
        originals = (
            dossier_bytes, queue_bytes, intake_bytes, plan_bytes,
            observations_bytes, manifest_bytes, protocol_bytes,
            auth_contract_bytes, blueprint_bytes, interface_bytes,
            transition_bytes, revocation_bytes, assurance_bytes,
            compatibility_bytes, impact_bytes, release_manifest_bytes,
        )
        observed = _loads(matrix_bytes, MAX_MATRIX_BYTES)
        expected = prepare_release_evidence_matrix(*originals)
        if not _strict_equal(observed, expected):
            raise ValueError
        if (observed["releaseReadiness"] != "NOT_READY"
                or observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or observed["unmetReleaseGateCount"] != 6
                or observed["evidenceItemCount"] != 18
                or observed["externalEvidenceIncluded"] is not False):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-release-readiness-cockpit.v0",
            "reference": "PP-RECOVERY-002",
            "releaseEvidenceMatrixSha256": hashlib.sha256(matrix_bytes).hexdigest(),
            "releaseIntegrityManifestSha256": observed["releaseIntegrityManifestSha256"],
            "snapshotProvenance": "UNSIGNED_LOCAL_RECONSTRUCTION",
            "counts": {
                "sourceArtifacts": len(ARTIFACT_MAXIMA),
                "releaseGatesBlocked": len(REQUIREMENTS),
                "evidenceMissing": observed["evidenceItemCount"],
                "releaseBlockersOpen": len(BLOCKERS),
                "originalDecisionGatesBlocked": len(DECISION_REQUIREMENTS),
                "approvedGates": 0,
            },
            "releaseGateRows": [
                {
                    "order": row["order"],
                    "gateId": row["releaseGate"],
                    "requiredIndependentRole": row["requiredIndependentRole"],
                    "missingEvidenceIds": [
                        item["evidenceId"] for item in row["requiredEvidence"]
                    ],
                    "reviewerAuthority": "NOT_ESTABLISHED",
                    "gate": "BLOCKED",
                    "decision": "DENY",
                }
                for row in observed["evidenceMatrix"]
            ],
            "openReleaseBlockers": [
                {"blockerId": blocker, "status": "OPEN"}
                for blocker in BLOCKERS
            ],
            "handoffChecklist": [
                {"step": step, "status": "NOT_STARTED", "approvalEffect": "NONE"}
                for step in (
                    "COLLECT_EXTERNAL_SOURCE_ATTESTATIONS",
                    "VERIFY_INDEPENDENT_REVIEWER_CREDENTIALS",
                    "COLLECT_REPRODUCIBLE_TEST_AND_SBOM_EVIDENCE",
                    "VERIFY_SIGNED_RELEASE_PROVENANCE",
                    "COMPLETE_AUTHORIZED_HUMAN_RELEASE_REVIEW",
                )
            ],
            "dataRefresh": "MANUAL_OFFLINE_REBUILD_REQUIRED",
            "interactiveApproval": "PROHIBITED",
            "externalEvidenceVerification": "NOT_PERFORMED",
            "runtimeTests": "NOT_EXECUTED",
            "softwareBundle": "NOT_CREATED",
            "signing": "NOT_PERFORMED",
            "deployment": "NOT_EXECUTED",
            "releaseReadiness": "NOT_READY",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
