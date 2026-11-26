"""Pure constructor for owner-reported, non-authoritative P.P. Review 044 notes.

No file access, runner invocation, authentication or approval. A self-report is
not the synthetic runner's technical evidence and cannot establish identity.
"""

from datetime import datetime, timezone
from typing import Mapping

from review_044_runner import EXPECTED


ALLOWED_RESULTS = frozenset({
    "FOUR_FILE_HASH_MATCH_UNTRUSTED", "PP_CHAIN_INVALID",
    "UNEXPECTED_ERROR", "NOT_OBSERVED",
})


def _utc_timestamp(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 40:
        raise ValueError("PP_REVIEW_044_OBSERVATION_INVALID")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("PP_REVIEW_044_OBSERVATION_INVALID") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("PP_REVIEW_044_OBSERVATION_INVALID")
    return parsed.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_self_report(
    observations: list[Mapping[str, str]], recorded_at: str,
) -> dict[str, object]:
    """Construct an unsigned HOLD report from explicit owner observations.

    Does not claim the values are independently witnessed or even correct.
    Missing scenarios remain explicitly NOT_OBSERVED, never inferred PASS.
    """
    invalid = ValueError("PP_REVIEW_044_OBSERVATION_INVALID")
    if not isinstance(observations, list) or len(observations) > len(EXPECTED):
        raise invalid
    report_time = _utc_timestamp(recorded_at)
    supplied: dict[str, dict[str, str]] = {}
    for row in observations:
        if not isinstance(row, Mapping) or set(row) != {"scenario_id", "observed_result", "observed_at"}:
            raise invalid
        scenario = row["scenario_id"]
        result = row["observed_result"]
        if (type(scenario) is not str or scenario not in EXPECTED or scenario in supplied
                or type(result) is not str or result not in ALLOWED_RESULTS):
            raise invalid
        observed_at = _utc_timestamp(row["observed_at"])
        if observed_at > report_time:
            raise invalid
        supplied[scenario] = {"observed_result": result, "observed_at": observed_at}

    rows = []
    for scenario, expected in EXPECTED.items():
        observed = supplied.get(scenario)
        rows.append({
            "scenario_id": scenario,
            "expected_result": expected,
            "observed_result": observed["observed_result"] if observed else "NOT_OBSERVED",
            "observed_at": observed["observed_at"] if observed else None,
            "evidence_kind": "SELF_REPORTED" if observed else "NO_OBSERVATION",
            "comparison": (
                "NOT_ASSESSED" if not observed or observed["observed_result"] == "NOT_OBSERVED"
                else "MATCH_CLAIMED" if observed["observed_result"] == expected
                else "MISMATCH_CLAIMED"
            ),
        })
    return {
        "schema": "palaco.pp.review-044-self-report.v0",
        "reference": "PP-RECOVERY-002",
        "recordedAt": report_time,
        "provenance": "UNSIGNED_OWNER_SELF_REPORT_NOT_INDEPENDENTLY_VERIFIED",
        "scenarios": rows,
        "verification": "NOT_VERIFIED",
        "reviewDecision": "HOLD",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
    }
