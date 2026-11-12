"""Pure Review 044 owner-worksheet evidence compilation (offline, non-authoritative).

Consumes the *original bytes* of the synthetic technical report and owner
worksheet. Never runs the fixtures or technical runner, writes files, checks
identity, or grants any permission.
"""
from review_044_inspection_owner_binding import validate_inspection_owner_worksheet
from review_044_inspection_owner_review import assess_inspection_technical_report


def compile_inspection_owner_evidence(
    technical_report: bytes, owner_worksheet: bytes
) -> dict[str, object]:
    """Prepare a limited, untrusted technical consistency record.

    The strict Python validators fail closed before any evidence object exists.
    A valid object does not prove who generated either source or when.
    """
    try:
        technical = assess_inspection_technical_report(technical_report)
        binding = validate_inspection_owner_worksheet(technical_report, owner_worksheet)
        if technical["technicalReportSha256"] != binding["technicalReportSha256"]:
            raise ValueError
        return {
            "schema": "palaco.pp.review-044-inspection-owner-evidence.v0",
            "reference": "PP-RECOVERY-002",
            "sourceTechnicalReportSha256": binding["technicalReportSha256"],
            "sourceOwnerWorksheetSha256": binding["ownerWorksheetSha256"],
            "reportedScenarios": technical["reportedScenarios"],
            "claimedTechnicalMismatches": technical["claimedMismatches"],
            "technicalComparison": technical["technicalComparison"],
            "ownerMarkedCount": binding["ownerMarkedCount"],
            "ownerDiscrepancyCount": binding["ownerDiscrepancyCount"],
            "binding": "STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED",
            "evidenceKind": "UNSIGNED_LOCAL_PYTHON_VALIDATION_RESULT",
            "executionProvenance": "NOT_INDEPENDENTLY_ESTABLISHED",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "identityBinding": "NOT_ESTABLISHED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
            "historicalImmutability": "NOT_ESTABLISHED",
            "limitations": "Consistent input bytes are not attestation, origin, execution, time, identity or authority proof.",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError("PP_REVIEW_044_INSPECTION_EVIDENCE_INVALID") from exc
