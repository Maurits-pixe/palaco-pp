"""Fail-closed, read-only Review 044 -> PALACO ONE handoff preview.

This module grants no session, identity, ownership, or issuance authority.
It performs no filesystem/network I/O and does not execute Review 044 tests.
"""

import json
from typing import Any

from review_044_runner import EXPECTED


MAX_REPORT_BYTES = 64 * 1024
TOP_FIELDS = frozenset({
    "schema", "reference", "recordedAt", "provenance", "scenarios",
    "verification", "reviewDecision", "authorization", "accessDecision", "issuance",
})
ROW_FIELDS = frozenset({
    "scenario_id", "expected_result", "observed_result", "observed_at",
    "evidence_kind", "comparison",
})
RESULTS = frozenset({
    "NOT_OBSERVED", "PP_CHAIN_INVALID", "FOUR_FILE_HASH_MATCH_UNTRUSTED",
    "UNEXPECTED_ERROR",
})


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
        result[key] = value
    return result


def preview_identity_handoff(raw_report: bytes) -> dict[str, object]:
    """Inspect an unsigned self-report; never promote it to identity evidence."""
    if type(raw_report) is not bytes or not 0 < len(raw_report) <= MAX_REPORT_BYTES:
        raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
    try:
        report = json.loads(raw_report.decode("utf-8"), object_pairs_hook=_unique_pairs)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise ValueError("PP_REVIEW_044_PREVIEW_INVALID") from exc

    if type(report) is not dict or set(report) != TOP_FIELDS:
        raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
    required = {
        "schema": "palaco.pp.review-044-self-report.v0",
        "reference": "PP-RECOVERY-002",
        "provenance": "UNSIGNED_OWNER_SELF_REPORT_NOT_INDEPENDENTLY_VERIFIED",
        "verification": "NOT_VERIFIED", "reviewDecision": "HOLD",
        "authorization": "HOLD", "accessDecision": "DENY", "issuance": "NOT_AUTHORIZED",
    }
    if any(report[key] != value for key, value in required.items()):
        raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
    if type(report["recordedAt"]) is not str or not report["recordedAt"].endswith("Z"):
        raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
    rows = report["scenarios"]
    if type(rows) is not list or len(rows) != len(EXPECTED):
        raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")

    claimed_matches = 0
    recorded = 0
    for row, (scenario, expected) in zip(rows, EXPECTED.items()):
        if type(row) is not dict or set(row) != ROW_FIELDS:
            raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
        if row["scenario_id"] != scenario or row["expected_result"] != expected:
            raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
        observed = row["observed_result"]
        if type(observed) is not str or observed not in RESULTS:
            raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
        timestamp = row["observed_at"]
        if timestamp is None:
            if (row["evidence_kind"] != "NO_OBSERVATION" or observed != "NOT_OBSERVED"
                    or row["comparison"] != "NOT_ASSESSED"):
                raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
        else:
            if type(timestamp) is not str or not timestamp.endswith("Z"):
                raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
            if row["evidence_kind"] != "SELF_REPORTED":
                raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
            comparison = ("NOT_ASSESSED" if observed == "NOT_OBSERVED" else
                          "MATCH_CLAIMED" if observed == expected else "MISMATCH_CLAIMED")
            if row["comparison"] != comparison:
                raise ValueError("PP_REVIEW_044_PREVIEW_INVALID")
            recorded += 1
            claimed_matches += comparison == "MATCH_CLAIMED"

    return {
        "schema": "palaco.one.identity-handoff-preview.v0",
        "sourceReference": "PP-RECOVERY-002",
        "sourceSchema": report["schema"],
        "sourceTrust": "UNSIGNED_SELF_REPORTED_UNVERIFIED",
        "recordedScenarios": recorded,
        "claimedMatches": claimed_matches,
        "identityBinding": "NOT_ESTABLISHED",
        "session": "NOT_CREATED",
        "verification": "NOT_VERIFIED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
    }
