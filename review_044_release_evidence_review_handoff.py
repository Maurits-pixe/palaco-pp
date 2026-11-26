"""Unsigned release evidence review handoff; never proof of delivery or authority.

Revalidates exact original execution plan, observation chain and evidence
intake records. Output only requests independent future review. A SHA-256
binding is local consistency, not identity, provenance or signed receipt.
"""
import hashlib

from review_044_release_observation_register import _plan, _register
from review_044_release_evidence_intake import _intake, MAX_INTAKE_BYTES
from review_044_release_observation_register import MAX_PLAN_BYTES, MAX_REGISTER_BYTES
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal
from review_044_release_evidence_matrix import REQUIREMENTS

ERROR = "PP_RECOVERY_002_RELEASE_EVIDENCE_HANDOFF_INVALID"

REVIEW_REQUIREMENTS = (
    "EXTERNAL_REVIEWER_IDENTITY_AUTHENTICATION",
    "INDEPENDENT_ROLE_AND_SCOPE_ATTESTATION",
    "REVOCATION_AND_SEPARATION_OF_DUTIES_CHECK",
    "ORIGINAL_EVIDENCE_BYTES_AND_PROVENANCE_VERIFICATION",
    "SIGNED_RECEIPT_BOUND_TO_EXACT_HANDOFF_SHA256",
    "EXTERNAL_AUDIT_ANCHOR_AND_TRUSTED_TIME",
    "AUTHORIZED_HUMAN_REVIEW_DECISION",
)


def prepare_release_evidence_review_handoff(
    source_bytes: tuple[bytes, ...],
    execution_plan_bytes: bytes,
    observation_register_bytes: bytes,
    evidence_intake_bytes: bytes,
) -> dict[str, object]:
    """Prepare only an unsigned, untransmitted independent-review request."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        plan = _plan(source_bytes, execution_plan_bytes)
        plan_sha = hashlib.sha256(execution_plan_bytes).hexdigest()
        observations = _register(
            observation_register_bytes, plan_sha, plan
        )
        observation_sha = hashlib.sha256(observation_register_bytes).hexdigest()
        intake = _intake(evidence_intake_bytes, plan_sha, observation_sha, observations)
        if (intake["authorization"] != "HOLD"
                or intake["accessDecision"] != "DENY"
                or intake["reviewerAuthority"] != "NOT_ESTABLISHED"
                or intake["releaseReadiness"] != "NOT_READY"):
            raise ValueError
        check_lookup = {
            x["checkId"]: x for x in plan["verificationChecks"]
        }
        evidence_rows = [
            {
                "sequence": x["sequence"],
                "checkId": x["checkId"],
                "releaseGate": x["gateId"],
                "evidenceId": check_lookup[x["checkId"]]["evidenceId"],
                "requiredIndependentRole": check_lookup[x["checkId"]]["requiredIndependentRole"],
                "observationEventSha256": x["observationEventSha256"],
                "evidenceSha256": x["evidenceSha256"],
                "evidenceByteCount": x["evidenceByteCount"],
                "evidenceKind": x["evidenceKind"],
                "externalAuthenticity": "NOT_VERIFIED",
                "reviewStatus": "NOT_STARTED",
                "decision": "DENY",
            }
            for x in intake["records"]
        ]
        return {
            "schema": "palaco.pp.recovery-002-release-evidence-review-handoff.v0",
            "reference": "PP-RECOVERY-002",
            "executionPlanSha256": plan_sha,
            "observationRegisterSha256": observation_sha,
            "evidenceIntakeSha256": hashlib.sha256(evidence_intake_bytes).hexdigest(),
            "sourceBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "handoffProvenance": "UNSIGNED_LOCAL_REQUEST_NOT_SENT",
            "evidenceReferences": evidence_rows,
            "evidenceReferenceCount": len(evidence_rows),
            "requiredExternalReview": [
                {"order": i, "requirement": x, "status": "NOT_STARTED"}
                for i, x in enumerate(REVIEW_REQUIREMENTS, 1)
            ],
            "releaseGateReview": [
                {"releaseGate": gate, "requiredIndependentRole": role,
                 "status": "BLOCKED", "reviewerAuthority": "NOT_ESTABLISHED",
                 "decision": "DENY"}
                for gate, _, role in REQUIREMENTS
            ],
            "delivery": "NOT_SENT",
            "recipientAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthentication": "NOT_ESTABLISHED",
            "reviewerAuthority": "NOT_ESTABLISHED",
            "signedReceipt": "NOT_AVAILABLE",
            "externalAudit": "NOT_VERIFIED",
            "humanReview": "NOT_COMPLETED",
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
