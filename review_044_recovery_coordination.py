"""Read-only PP-RECOVERY-002 coordination boundary.

It combines two *untrusted* pieces of input: a locally exported PALACO
PHONE handoff and a Review 044 Python evidence summary. Neither source
can prove the other's origin or their common subject. Never authorize.
"""
import hashlib
import json

from review_handoff import parse_review_handoff
from review_044_inspection_evidence import compile_inspection_owner_evidence
from review_044_inspection_owner_review import MAX_INSPECTION_TECHNICAL_BYTES
from review_044_inspection_owner_binding import MAX_INSPECTION_WORKSHEET_BYTES

MAX_COORDINATION_HANDOFF_BYTES = 16 * 1024
ERROR = "PP_RECOVERY_002_COORDINATION_INVALID"


def _read_handoff(raw: bytes) -> str:
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_COORDINATION_HANDOFF_BYTES:
        raise ValueError
    assessment = parse_review_handoff(raw)
    if assessment.structural_status != "STRUCTURE_ACCEPTED_UNTRUSTED":
        raise ValueError
    return assessment.registration_status


def compile_recovery_coordination(
    handoff_bytes: bytes, technical_report_bytes: bytes,
    owner_worksheet_bytes: bytes
) -> dict[str, object]:
    """Return an untrusted, identity-free recovery readiness summary.

    All original input bytes must be supplied; only after strict structural
    validation do their digests enter the output. No account references,
    PP numbers, usernames or tokens are copied into the summary.
    """
    try:
        status = _read_handoff(handoff_bytes)
        if (type(technical_report_bytes) is not bytes
                or not 0 < len(technical_report_bytes) <= MAX_INSPECTION_TECHNICAL_BYTES
                or type(owner_worksheet_bytes) is not bytes
                or not 0 < len(owner_worksheet_bytes) <= MAX_INSPECTION_WORKSHEET_BYTES):
            raise ValueError
        evidence = compile_inspection_owner_evidence(
            technical_report_bytes, owner_worksheet_bytes
        )
        if evidence["reference"] != "PP-RECOVERY-002" or evidence["authorization"] != "HOLD":
            raise ValueError
        return {
            "schema": "palaco.pp.recovery-002-coordination.v0",
            "reference": "PP-RECOVERY-002",
            "handoffSha256": hashlib.sha256(handoff_bytes).hexdigest(),
            "technicalReportSha256": evidence["sourceTechnicalReportSha256"],
            "ownerWorksheetSha256": evidence["sourceOwnerWorksheetSha256"],
            "localRegistrationStatus": status,
            "handoffStructure": "STRUCTURE_ACCEPTED_UNTRUSTED",
            "review044Evidence": "STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED",
            "reportedScenarios": evidence["reportedScenarios"],
            "claimedTechnicalMismatches": evidence["claimedTechnicalMismatches"],
            "ownerMarkedCount": evidence["ownerMarkedCount"],
            "ownerDiscrepancyCount": evidence["ownerDiscrepancyCount"],
            "crossSourceSubjectBinding": "NOT_ESTABLISHED",
            "ownerAuthority": "NOT_ESTABLISHED",
            "palacoOneSession": "NOT_CREATED",
            "externalAttestation": "ABSENT",
            "sourceTrust": "UNSIGNED_UNATTESTED_LOCAL_INPUTS",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
            "nextPermittedStep": "MANUAL_SOURCE_AND_IDENTITY_REVIEW_ONLY",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
