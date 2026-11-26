"""Construct an unsigned owner-review worksheet for Review 044.

Offline/pure: no runner invocation, account operation, session or approval.
The digest identifies supplied bytes, not their origin or authenticity.
"""

import hashlib
from typing import Mapping

from review_044_preview_assessment import assess_preview_report
from review_044_preview_fixtures import build_preview_fixtures


ALLOWED_OWNER_MARKS = frozenset({
    "NOT_REVIEWED", "OBSERVED_AS_REPORTED", "DISCREPANCY_REPORTED",
})


def make_owner_review_draft(
    technical_report: bytes,
    owner_marks: Mapping[str, str],
) -> dict[str, object]:
    """Create a local, non-authoritative worksheet bound to input bytes."""
    assessment = assess_preview_report(technical_report)
    names = tuple(build_preview_fixtures())
    if (not isinstance(owner_marks, Mapping) or len(owner_marks) > len(names)
            or any(type(name) is not str or name not in names
                   or type(mark) is not str or mark not in ALLOWED_OWNER_MARKS
                   for name, mark in owner_marks.items())):
        raise ValueError("PP_REVIEW_044_OWNER_REVIEW_INVALID")

    observations = [
        {
            "scenario_id": name,
            "owner_mark": owner_marks.get(name, "NOT_REVIEWED"),
            "evidence_kind": "SELF_REPORTED" if name in owner_marks else "NO_OBSERVATION",
        }
        for name in names
    ]
    discrepancies = sum(row["owner_mark"] == "DISCREPANCY_REPORTED"
                        for row in observations)
    reviewed = sum(row["owner_mark"] != "NOT_REVIEWED"
                   for row in observations)
    return {
        "schema": "palaco.pp.review-044-owner-worksheet.v0",
        "reference": "PP-RECOVERY-002",
        "technicalReportSha256": hashlib.sha256(technical_report).hexdigest(),
        "sourceTrust": assessment["sourceTrust"],
        "technicalComparison": assessment["technicalComparison"],
        "executionProvenance": "NOT_INDEPENDENTLY_ESTABLISHED",
        "ownerMarks": observations,
        "ownerMarkedCount": reviewed,
        "ownerDiscrepancyCount": discrepancies,
        "independentVerification": "NOT_VERIFIED",
        "reviewDecision": "HOLD",
        "identityBinding": "NOT_ESTABLISHED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
    }
