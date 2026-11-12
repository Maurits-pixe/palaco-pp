"""PP-RECOVERY-002 decision dossier: fail-closed evidence gaps and manual queue.

Pure, offline, read-only. Structural validity is never an identity decision.
The manual checklist records *requests*, not completed verification.
"""
import hashlib
import json
from collections.abc import Mapping

from review_044_recovery_coordination import compile_recovery_coordination

ERROR = "PP_RECOVERY_002_DECISION_DOSSIER_INVALID"
REQUIREMENTS = (
    ("SOURCE_ATTESTATION", "Independent attestation of input origin"),
    ("CROSS_SOURCE_SUBJECT", "Independent common-subject evidence"),
    ("OWNER_AUTHORITY", "Authenticated owner authority review"),
    ("RUNTIME_EXECUTION", "Independent execution provenance"),
    ("HUMAN_REVIEW", "Recorded authorized human review"),
)
MARKS = frozenset({"NOT_REVIEWED", "REVIEW_REQUESTED", "BLOCKER_REPORTED"})


def prepare_decision_dossier(
    handoff_bytes: bytes,
    technical_report_bytes: bytes,
    owner_worksheet_bytes: bytes,
    review_marks: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Prepare a non-authorizing decision record from original input bytes.

    Explicit marks are *self-reported planning annotations*, not completed
    checks. Nothing, including a perfect technical match, clears any gate.
    """
    try:
        marks = {} if review_marks is None else review_marks
        allowed = {name for name, _ in REQUIREMENTS}
        if (not isinstance(marks, Mapping) or len(marks) > len(REQUIREMENTS)
                or any(type(name) is not str or name not in allowed
                       or type(mark) is not str or mark not in MARKS
                       for name, mark in marks.items())):
            raise ValueError
        coordination = compile_recovery_coordination(
            handoff_bytes, technical_report_bytes, owner_worksheet_bytes
        )
        requirements = [
            {
                "requirementId": name,
                "description": description,
                "evidenceStatus": "NOT_ESTABLISHED",
                "ownerMark": marks.get(name, "NOT_REVIEWED"),
                "markProvenance": "SELF_REPORTED" if name in marks else "NO_OBSERVATION",
                "gate": "BLOCKED",
            }
            for name, description in REQUIREMENTS
        ]
        return {
            "schema": "palaco.pp.recovery-002-decision-dossier.v0",
            "reference": "PP-RECOVERY-002",
            "coordinationSha256": hashlib.sha256(
                # Digest a deterministic representation of the coordination
                # claims; this is not an external timestamp or attestation.
                json.dumps(
                    coordination, sort_keys=True, separators=(",",":"),
                    ensure_ascii=False
                ).encode("utf-8")
            ).hexdigest(),
            "handoffSha256": coordination["handoffSha256"],
            "technicalReportSha256": coordination["technicalReportSha256"],
            "ownerWorksheetSha256": coordination["ownerWorksheetSha256"],
            "localRegistrationStatus": coordination["localRegistrationStatus"],
            "technicalEvidence": coordination["review044Evidence"],
            "requirements": requirements,
            "openRequirementCount": len(REQUIREMENTS),
            "selfReportedMarkCount": len(marks),
            "crossSourceSubjectBinding": "NOT_ESTABLISHED",
            "ownerAuthority": "NOT_ESTABLISHED",
            "humanReview": "NOT_COMPLETED",
            "palacoOneHandoff": "BLOCKED",
            "palacoOneSession": "NOT_CREATED",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
            "nextPermittedStep": "MANUAL_SOURCE_AND_IDENTITY_REVIEW_ONLY",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
