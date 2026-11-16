"""PP-RECOVERY-002 trust change decision protocol: DENY-only policy boundary.

Separates local review claims from independently authenticated evidence,
and both from a separate authorized human decision. This offline contract
has no trusted external input/decision implementation and cannot grant.
"""
import hashlib

from review_044_trust_change_review_dossier import (
    prepare_trust_change_review_dossier, EXTERNAL_EVIDENCE,
    DECISION_CHECKPOINTS, MAX_CHANGE_CONTROL_BYTES,
)
from review_044_trust_policy_change_control import REQUIRED_REVIEW_ROLES
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_TRUST_CHANGE_DECISION_PROTOCOL_INVALID"
MAX_REVIEW_DOSSIER_BYTES = 64 * 1024

STAGES = (
    ("LOCAL_CLAIM_INTAKE", "UNAUTHENTICATED_REQUEST_ONLY"),
    ("EXTERNAL_EVIDENCE_VERIFICATION", "INDEPENDENT_TRUSTED_VERIFIER_REQUIRED"),
    ("AUTHORIZED_HUMAN_DECISION", "SEPARATE_AUTHORITY_AND_SIGNED_DECISION_REQUIRED"),
)
BOUNDARIES = (
    ("LOCAL_CLAIM_INTAKE", "EXTERNAL_EVIDENCE_VERIFICATION",
     "LOCAL_CLAIM_CANNOT_ATTEST_EVIDENCE"),
    ("EXTERNAL_EVIDENCE_VERIFICATION", "AUTHORIZED_HUMAN_DECISION",
     "TECHNICAL_VERIFICATION_CANNOT_APPROVE_POLICY"),
    ("AUTHORIZED_HUMAN_DECISION", "TRUST_POLICY_ACTIVATION",
     "HUMAN_DECISION_ALONE_CANNOT_DEPLOY"),
)
NON_BYPASSABLE = (
    "EXACT_REVIEW_DOSSIER_AND_POLICY_HASH_BINDING",
    "INDEPENDENT_TRUST_ANCHOR_AND_RECEIPT_SIGNATURE",
    "ORIGINAL_EVIDENCE_PROVENANCE_AND_REVOCATION",
    "REVIEWER_AUTHENTICATION_ROLE_SCOPE_AND_INDEPENDENCE",
    "SIGNED_CANONICAL_POLICY_DIFF_AND_REPLAY_PROTECTION",
    "EXTERNAL_AUDIT_ANCHOR_AND_TRUSTED_TIME",
    "SEPARATE_AUTHORIZED_HUMAN_DECISION",
    "INDEPENDENT_DEPLOYMENT_APPROVAL_AND_ROLLBACK",
)


def prepare_trust_change_decision_protocol(
    source_bytes: tuple[bytes, ...], execution_plan_bytes: bytes,
    observation_register_bytes: bytes, evidence_intake_bytes: bytes,
    review_handoff_bytes: bytes, receipt_protocol_bytes: bytes,
    verifier_blueprint_bytes: bytes, trust_policy_bytes: bytes,
    change_control_bytes: bytes, review_dossier_bytes: bytes,
) -> dict[str, object]:
    """Bind the exact review dossier, then emit only blocked decision stages."""
    try:
        if type(source_bytes) is not tuple or len(source_bytes) != 18:
            raise ValueError
        observed = _loads(review_dossier_bytes, MAX_REVIEW_DOSSIER_BYTES)
        expected = prepare_trust_change_review_dossier(
            source_bytes, execution_plan_bytes, observation_register_bytes,
            evidence_intake_bytes, review_handoff_bytes, receipt_protocol_bytes,
            verifier_blueprint_bytes, trust_policy_bytes, change_control_bytes,
        )
        if not _strict_equal(observed, expected):
            raise ValueError
        if (observed["handoffDelivery"] != "NOT_SENT"
                or observed["signedReceipt"] != "NOT_AVAILABLE"
                or observed["independentReview"] != "NOT_COMPLETED"
                or observed["changeApplied"] is not False
                or observed["decision"] != "DENY"
                or observed["authorization"] != "HOLD"
                or observed["accessDecision"] != "DENY"
                or len(observed["externalEvidenceRequirements"])
                   != len(EXTERNAL_EVIDENCE)
                or len(observed["decisionCheckpoints"])
                   != len(DECISION_CHECKPOINTS)):
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-trust-change-decision-protocol.v0",
            "reference": "PP-RECOVERY-002",
            "reviewDossierSha256": hashlib.sha256(review_dossier_bytes).hexdigest(),
            "changeControlSha256": observed["changeControlSha256"],
            "trustPolicySha256": observed["trustPolicySha256"],
            "sourceBinding": "STRICT_INTERNAL_RECONSTRUCTION_ONLY",
            "decisionPolicy": "DENY_ALL_UNTIL_SEPARATE_VERIFIED_AUTHORITIES",
            "decisionStages": [
                {"order": i, "stageId": name, "requirement": requirement,
                 "status": "BLOCKED", "verification": "NOT_PERFORMED",
                 "decision": "DENY"}
                for i, (name, requirement) in enumerate(STAGES, 1)
            ],
            "trustBoundaryRules": [
                {"fromStage": source, "toStage": target, "ruleId": rule,
                 "crossing": "PROHIBITED", "authorityEffect": "NONE"}
                for source, target, rule in BOUNDARIES
            ],
            "evidenceChecks": [
                {"evidenceId": evidence, "requiredRole": role,
                 "externalAuthenticity": "NOT_VERIFIED",
                 "independentAssessment": "NOT_PERFORMED",
                 "maySatisfyDecision": False}
                for evidence, role in EXTERNAL_EVIDENCE
            ],
            "reviewerGates": [
                {"role": role, "authentication": "NOT_ESTABLISHED",
                 "authority": "NOT_ESTABLISHED",
                 "independence": "NOT_VERIFIED",
                 "decision": "NOT_COMPLETED"}
                for role in REQUIRED_REVIEW_ROLES
            ],
            "decisionCheckpoints": [
                {"checkpointId": checkpoint, "status": "BLOCKED",
                 "independentVerification": "NOT_PERFORMED"}
                for checkpoint in DECISION_CHECKPOINTS
            ],
            "nonBypassableControls": [
                {"controlId": control, "status": "NOT_SATISFIED",
                 "approvalEffect": "NONE"}
                for control in NON_BYPASSABLE
            ],
            "localClaimAuthority": "NONE",
            "externalVerificationService": "NOT_CONFIGURED",
            "humanDecisionService": "NOT_CONFIGURED",
            "signedDecision": "NOT_AVAILABLE",
            "decisionReceipt": "NOT_AVAILABLE",
            "reviewDossierDelivery": "NOT_SENT",
            "policyChangeExecution": "PROHIBITED",
            "issuerPromotion": "PROHIBITED",
            "algorithmPromotion": "PROHIBITED",
            "trustedIssuerCount": 0,
            "allowedAlgorithms": [],
            "keyMaterial": "NOT_PRESENT",
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
