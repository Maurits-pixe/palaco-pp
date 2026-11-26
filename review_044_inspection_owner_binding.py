"""Fail-closed binding of a Review 044 inspection owner worksheet to report bytes.

Pure and offline. Matching input is only internally consistent, not verified.
"""
import hashlib
import hmac
import json

from review_044_inspection_owner_review import (
    MARKS, make_inspection_owner_worksheet,
)
from review_044_inspection_fixtures import build_inspection_fixtures


MAX_INSPECTION_WORKSHEET_BYTES = 48 * 1024
ERROR = "PP_REVIEW_044_INSPECTION_WORKSHEET_INVALID"


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(ERROR)
        output[key] = value
    return output


def validate_inspection_owner_worksheet(
    technical_report: bytes, worksheet_bytes: bytes,
) -> dict[str, object]:
    """Reject all deviations from the deterministic, unsigned owner worksheet."""
    try:
        if (type(worksheet_bytes) is not bytes
                or not 0 < len(worksheet_bytes) <= MAX_INSPECTION_WORKSHEET_BYTES):
            raise ValueError
        worksheet = json.loads(
            worksheet_bytes.decode("utf-8"), object_pairs_hook=_unique_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError(ERROR)),
        )
        names = tuple(name for name, _, _, _ in build_inspection_fixtures())
        rows = worksheet["ownerMarks"]
        if type(rows) is not list or len(rows) != len(names):
            raise ValueError
        marks: dict[str, str] = {}
        for name, row in zip(names, rows):
            if (type(row) is not dict
                    or set(row) != {"scenario_id", "owner_mark", "evidence_kind"}
                    or type(row["scenario_id"]) is not str or row["scenario_id"] != name
                    or type(row["owner_mark"]) is not str or row["owner_mark"] not in MARKS):
                raise ValueError
            provenance = row["evidence_kind"]
            if provenance == "SELF_REPORTED":
                marks[name] = row["owner_mark"]
            elif provenance != "NO_OBSERVATION" or row["owner_mark"] != "NOT_REVIEWED":
                raise ValueError
        expected = make_inspection_owner_worksheet(technical_report, marks)
        if (type(worksheet) is not dict
                or set(worksheet) != set(expected)
                or any(type(worksheet[k]) is not type(v) or worksheet[k] != v
                       for k, v in expected.items())
                or type(worksheet["ownerMarkedCount"]) is not int
                or type(worksheet["ownerDiscrepancyCount"]) is not int):
            raise ValueError
        if not hmac.compare_digest(
            worksheet["technicalReportSha256"], hashlib.sha256(technical_report).hexdigest()
        ):
            raise ValueError
        return {
            "schema": "palaco.pp.review-044-inspection-worksheet-binding.v0",
            "reference": "PP-RECOVERY-002",
            "technicalReportSha256": expected["technicalReportSha256"],
            "ownerWorksheetSha256": hashlib.sha256(worksheet_bytes).hexdigest(),
            "binding": "TWO_FILE_HASH_MATCH_UNTRUSTED",
            "ownerMarkedCount": expected["ownerMarkedCount"],
            "ownerDiscrepancyCount": expected["ownerDiscrepancyCount"],
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
