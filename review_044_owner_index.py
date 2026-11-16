"""Bind a synthetic Review 044 technical report to an owner worksheet.

Offline-only. A consistent pair is untrusted evidence, never an attestation,
identity binding, authorization, or issuance permit.
"""

import hashlib
import hmac
import json

from review_044_owner_review import ALLOWED_OWNER_MARKS, make_owner_review_draft
from review_044_preview_assessment import assess_preview_report


MAX_OWNER_WORKSHEET_BYTES = 32 * 1024
_OWNER_FIELDS = frozenset({
    "schema", "reference", "technicalReportSha256", "sourceTrust",
    "technicalComparison", "executionProvenance", "ownerMarks",
    "ownerMarkedCount", "ownerDiscrepancyCount", "independentVerification",
    "reviewDecision", "identityBinding", "authorization", "accessDecision",
    "issuance",
})
_MARK_FIELDS = frozenset({"scenario_id", "owner_mark", "evidence_kind"})


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for name, value in pairs:
        if name in output:
            raise ValueError("PP_REVIEW_044_OWNER_INDEX_INVALID")
        output[name] = value
    return output


def make_owner_evidence_index(technical_report: bytes, worksheet: bytes) -> dict[str, object]:
    """Validate both original byte streams and return a non-authoritative index.

    The worksheet must exactly match the deterministic owner-review contract;
    missing or explicitly NOT_REVIEWED marks retain their distinct provenance.
    """
    try:
        if type(worksheet) is not bytes or not 0 < len(worksheet) <= MAX_OWNER_WORKSHEET_BYTES:
            raise ValueError
        assess_preview_report(technical_report)
        owner = json.loads(worksheet.decode("utf-8"), object_pairs_hook=_unique_pairs)
        if type(owner) is not dict or set(owner) != _OWNER_FIELDS:
            raise ValueError
        rows = owner["ownerMarks"]
        if type(rows) is not list or len(rows) != 13:
            raise ValueError
        marks: dict[str, str] = {}
        for row in rows:
            if type(row) is not dict or set(row) != _MARK_FIELDS:
                raise ValueError
            name, mark, provenance = (row["scenario_id"], row["owner_mark"],
                                      row["evidence_kind"])
            if type(name) is not str or type(mark) is not str or mark not in ALLOWED_OWNER_MARKS:
                raise ValueError
            if provenance == "SELF_REPORTED":
                if name in marks:
                    raise ValueError
                marks[name] = mark
            elif provenance != "NO_OBSERVATION" or mark != "NOT_REVIEWED":
                raise ValueError

        expected = make_owner_review_draft(technical_report, marks)
        # Compare all fields and row order; bools do not pass as integer counters.
        if owner != expected or any(type(owner[key]) is not int for key in (
                "ownerMarkedCount", "ownerDiscrepancyCount")):
            raise ValueError
        technical_digest = hashlib.sha256(technical_report).hexdigest()
        if not hmac.compare_digest(owner["technicalReportSha256"], technical_digest):
            raise ValueError
        worksheet_digest = hashlib.sha256(worksheet).hexdigest()
        return {
            "schema": "palaco.pp.review-044-owner-evidence-index.v0",
            "reference": "PP-RECOVERY-002",
            "technicalReportSha256": technical_digest,
            "ownerWorksheetSha256": worksheet_digest,
            "binding": "TWO_FILE_HASH_MATCH_UNTRUSTED",
            "technicalComparison": expected["technicalComparison"],
            "ownerMarkedCount": expected["ownerMarkedCount"],
            "ownerDiscrepancyCount": expected["ownerDiscrepancyCount"],
            "sourceTrust": "IMPORTED_UNATTESTED_TECHNICAL_REPORT",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "identityBinding": "NOT_ESTABLISHED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError) as exc:
        raise ValueError("PP_REVIEW_044_OWNER_INDEX_INVALID") from exc
