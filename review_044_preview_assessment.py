"""Read-only, non-authoritative interpretation of a synthetic Review 044 report.

No file/network I/O, no cryptographic attestation, no approval or identity action.
Never treat an imported report as proof that the runner actually executed.
"""

import json
from typing import Any

from review_044_preview_fixtures import build_preview_fixtures


MAX_TECHNICAL_REPORT_BYTES = 32 * 1024
TOP_FIELDS = frozenset({
    "schema", "reference", "scope", "observations", "verification",
    "reviewDecision", "authorization", "accessDecision", "issuance",
})
ROW_FIELDS = frozenset({
    "scenario_id", "expected_result", "observed_result", "comparison",
    "evidence_kind", "authorization", "accessDecision",
})
RESULTS = frozenset({
    "HOLD_DENY_PREVIEW", "PP_REVIEW_044_PREVIEW_INVALID",
    "UNEXPECTED_AUTHORITY_STATE", "UNEXPECTED_ERROR",
})


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")
        result[key] = value
    return result


def assess_preview_report(raw: bytes) -> dict[str, object]:
    """Return only a claimed comparison summary, always HOLD/DENY."""
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_TECHNICAL_REPORT_BYTES:
        raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")
    try:
        report = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID") from exc
    if type(report) is not dict or set(report) != TOP_FIELDS:
        raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")
    required = {
        "schema": "palaco.pp.review-044-preview-technical-report.v0",
        "reference": "PP-RECOVERY-002", "scope": "SYNTHETIC_OFFLINE_ONLY",
        "verification": "NOT_INDEPENDENTLY_VERIFIED",
        "reviewDecision": "PENDING_OWNER_REVIEW", "authorization": "HOLD",
        "accessDecision": "DENY", "issuance": "NOT_AUTHORIZED",
    }
    if any(type(report[key]) is not str or report[key] != value
           for key, value in required.items()):
        raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")

    expected_cases = [(name, outcome) for name, (_, outcome)
                      in build_preview_fixtures().items()]
    rows = report["observations"]
    if type(rows) is not list or len(rows) != len(expected_cases):
        raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")
    mismatches = 0
    for row, (name, expected) in zip(rows, expected_cases):
        if type(row) is not dict or set(row) != ROW_FIELDS:
            raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")
        if (type(row["scenario_id"]) is not str or row["scenario_id"] != name
                or type(row["expected_result"]) is not str
                or row["expected_result"] != expected
                or type(row["observed_result"]) is not str
                or row["observed_result"] not in RESULTS
                or row["evidence_kind"] != "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION"
                or row["authorization"] != "HOLD" or row["accessDecision"] != "DENY"):
            raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")
        comparison = "MATCH" if row["observed_result"] == expected else "MISMATCH"
        if type(row["comparison"]) is not str or row["comparison"] != comparison:
            raise ValueError("PP_REVIEW_044_ASSESSMENT_INVALID")
        mismatches += comparison == "MISMATCH"

    return {
        "schema": "palaco.pp.review-044-preview-assessment.v0",
        "reference": "PP-RECOVERY-002",
        "sourceTrust": "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
        "reportedScenarios": len(rows),
        "claimedMismatches": mismatches,
        "technicalComparison": "ALL_MATCH_CLAIMED" if mismatches == 0 else "MISMATCH_CLAIMED",
        "executionProvenance": "NOT_INDEPENDENTLY_ESTABLISHED",
        "ownerReview": "PENDING",
        "identityBinding": "NOT_ESTABLISHED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
    }
