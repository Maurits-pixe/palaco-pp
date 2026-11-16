"""Non-authoritative Review 044 inspection-runner report and owner worksheet.

Pure in-memory functions. No test invocation, filesystem, network, clock,
identity binding, account change, attestation or authorization transition.
"""
import hashlib
import json
from collections.abc import Mapping

from review_044_inspection_fixtures import build_inspection_fixtures


MAX_INSPECTION_TECHNICAL_BYTES = 64 * 1024
ERROR = "PP_REVIEW_044_INSPECTION_OWNER_REVIEW_INVALID"
MARKS = frozenset({"NOT_REVIEWED", "OBSERVED_AS_REPORTED", "DISCREPANCY_REPORTED"})
_RESULTS = frozenset({
    "REGISTER_ROW_HASH_BINDING_CONSISTENT_UNTRUSTED",
    "PP_REVIEW_044_OWNER_INSPECTION_INVALID",
})
_TOP = frozenset({
    "schema", "reference", "scope", "observations", "independentVerification",
    "reviewDecision", "authorization", "accessDecision", "issuance",
})
_ROW = frozenset({
    "scenario_id", "expected_result", "observed_result", "comparison",
    "evidence_kind", "authorization", "accessDecision",
})


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    obj: dict[str, object] = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(ERROR)
        obj[key] = value
    return obj


def assess_inspection_technical_report(raw: bytes) -> dict[str, object]:
    """Strictly parse the *claimed* 24-case technical report, not run the cases."""
    try:
        if type(raw) is not bytes or not 0 < len(raw) <= MAX_INSPECTION_TECHNICAL_BYTES:
            raise ValueError
        obj = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError(ERROR)),
        )
        fixed = {
            "schema": "palaco.pp.review-044-inspection-technical-report.v0",
            "reference": "PP-RECOVERY-002",
            "scope": "SYNTHETIC_OFFLINE_ONLY",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "PENDING_OWNER_REVIEW",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
        if (type(obj) is not dict or set(obj) != _TOP
                or any(type(obj[k]) is not str or obj[k] != v for k, v in fixed.items())):
            raise ValueError
        expected = tuple((name, result) for name, _, _, result in build_inspection_fixtures())
        rows = obj["observations"]
        if type(rows) is not list or len(rows) != len(expected):
            raise ValueError
        mismatches = 0
        for row, (name, result) in zip(rows, expected):
            if type(row) is not dict or set(row) != _ROW:
                raise ValueError
            if (type(row["scenario_id"]) is not str or row["scenario_id"] != name
                    or type(row["expected_result"]) is not str or row["expected_result"] != result
                    or type(row["observed_result"]) is not str or row["observed_result"] not in _RESULTS
                    or type(row["evidence_kind"]) is not str
                    or row["evidence_kind"] != "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION"
                    or type(row["authorization"]) is not str or row["authorization"] != "HOLD"
                    or type(row["accessDecision"]) is not str or row["accessDecision"] != "DENY"):
                raise ValueError
            comparison = "MATCH" if row["observed_result"] == result else "MISMATCH"
            if type(row["comparison"]) is not str or row["comparison"] != comparison:
                raise ValueError
            mismatches += comparison == "MISMATCH"
        return {
            "schema": "palaco.pp.review-044-inspection-technical-assessment.v0",
            "reference": "PP-RECOVERY-002",
            "technicalReportSha256": hashlib.sha256(raw).hexdigest(),
            "reportedScenarios": len(rows),
            "claimedMismatches": mismatches,
            "technicalComparison": "ALL_MATCH_CLAIMED" if mismatches == 0 else "MISMATCH_CLAIMED",
            "executionProvenance": "NOT_INDEPENDENTLY_ESTABLISHED",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc


def make_inspection_owner_worksheet(
    technical_report: bytes, owner_marks: Mapping[str, str],
) -> dict[str, object]:
    """Bind explicit owner annotations to report bytes; missing = NO_OBSERVATION.

    This is not an owner signature; the caller remains responsible for retaining
    the original technical report and recording actual human observations later.
    """
    try:
        assessment = assess_inspection_technical_report(technical_report)
        expected = tuple(name for name, _, _, _ in build_inspection_fixtures())
        if (not isinstance(owner_marks, Mapping) or len(owner_marks) > len(expected)
                or any(type(name) is not str or name not in expected
                       or type(mark) is not str or mark not in MARKS
                       for name, mark in owner_marks.items())):
            raise ValueError
        rows = [{
            "scenario_id": name,
            "owner_mark": owner_marks.get(name, "NOT_REVIEWED"),
            "evidence_kind": "SELF_REPORTED" if name in owner_marks else "NO_OBSERVATION",
        } for name in expected]
        return {
            "schema": "palaco.pp.review-044-inspection-owner-worksheet.v0",
            "reference": "PP-RECOVERY-002",
            "technicalReportSha256": assessment["technicalReportSha256"],
            "technicalComparison": assessment["technicalComparison"],
            "executionProvenance": "NOT_INDEPENDENTLY_ESTABLISHED",
            "ownerMarks": rows,
            "ownerMarkedCount": sum(row["owner_mark"] != "NOT_REVIEWED" for row in rows),
            "ownerDiscrepancyCount": sum(row["owner_mark"] == "DISCREPANCY_REPORTED" for row in rows),
            "ownerEvidence": "UNSIGNED_SELF_REPORTED_OR_NOT_OBSERVED",
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "HOLD",
            "identityBinding": "NOT_ESTABLISHED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
