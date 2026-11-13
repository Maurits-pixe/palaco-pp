"""Fail-closed assessment of the three-file Review 044 owner dossier.

Inputs are original local bytes: technical report, owner worksheet, index.
No files are written, no runner is executed and no authority is conveyed.
"""

import json

from review_044_owner_index import _unique_pairs, make_owner_evidence_index


MAX_OWNER_INDEX_BYTES = 16 * 1024


def assess_owner_dossier(
    technical_report: bytes, owner_worksheet: bytes, evidence_index: bytes,
) -> dict[str, object]:
    """Return only an untrusted consistency assessment; reject all mismatches.

    A freshly reconstructed index is compared with the supplied index,
    including both SHA-256 references and all non-authoritative status fields.
    """
    try:
        if (type(evidence_index) is not bytes
                or not 0 < len(evidence_index) <= MAX_OWNER_INDEX_BYTES):
            raise ValueError
        expected = make_owner_evidence_index(technical_report, owner_worksheet)
        actual = json.loads(evidence_index.decode("utf-8"), object_pairs_hook=_unique_pairs)
        if (type(actual) is not dict or set(actual) != set(expected)
                or actual != expected
                or any(type(actual[field]) is not int for field in (
                    "ownerMarkedCount", "ownerDiscrepancyCount"))):
            raise ValueError
        return {
            "schema": "palaco.pp.review-044-owner-dossier-assessment.v0",
            "reference": "PP-RECOVERY-002",
            "binding": "THREE_FILE_HASH_MATCH_UNTRUSTED",
            "technicalReportSha256": expected["technicalReportSha256"],
            "ownerWorksheetSha256": expected["ownerWorksheetSha256"],
            "technicalComparison": expected["technicalComparison"],
            "ownerMarkedCount": expected["ownerMarkedCount"],
            "ownerDiscrepancyCount": expected["ownerDiscrepancyCount"],
            "sourceTrust": "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
            "executionProvenance": "NOT_INDEPENDENTLY_ESTABLISHED",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "identityBinding": "NOT_ESTABLISHED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise ValueError("PP_REVIEW_044_OWNER_DOSSIER_INVALID") from exc
