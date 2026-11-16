"""Synthetic, in-memory negative cases for the identity handoff preview.

Building these byte fixtures does NOT invoke the adapter or run tests.
The owner may execute a separate opt-in review at a later time.
"""

import copy
import json

from review_044_observations import make_self_report
from review_044_identity_preview import MAX_REPORT_BYTES


REPORT_TIME = "2026-11-11T10:00:00.000Z"
OBSERVED_TIME = "2026-11-11T09:59:00.000Z"


def _json_bytes(report: dict[str, object]) -> bytes:
    return json.dumps(report, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def build_preview_fixtures() -> dict[str, tuple[bytes, str]]:
    """Return named (raw bytes, expected outcome) without evaluating them."""
    baseline = make_self_report([], REPORT_TIME)
    cases: dict[str, tuple[bytes, str]] = {
        "baseline_unobserved_hold": (_json_bytes(baseline), "HOLD_DENY_PREVIEW"),
    }

    observed = make_self_report([{
        "scenario_id": "baseline_untrusted_hold",
        "observed_result": "FOUR_FILE_HASH_MATCH_UNTRUSTED",
        "observed_at": OBSERVED_TIME,
    }], REPORT_TIME)
    cases["baseline_self_reported_hold"] = (_json_bytes(observed), "HOLD_DENY_PREVIEW")

    changes = {
        "time_missing_z": ("recordedAt", "2026-11-11T10:00:00.000"),
        "time_noncanonical_offset": ("recordedAt", "2026-11-11T11:00:00.000+01:00"),
        "time_impossible_date": ("recordedAt", "2026-11-32T10:00:00.000Z"),
        "time_missing_milliseconds": ("recordedAt", "2026-11-11T10:00:00Z"),
        "authority_escalation": ("authorization", "ALLOW"),
        "verification_escalation": ("verification", "VERIFIED"),
    }
    for name, (key, value) in changes.items():
        candidate = copy.deepcopy(baseline)
        candidate[key] = value
        cases[name] = (_json_bytes(candidate), "PP_REVIEW_044_PREVIEW_INVALID")

    future = copy.deepcopy(observed)
    future["scenarios"][0]["observed_at"] = "2026-11-11T10:00:00.001Z"
    cases["observation_after_report"] = (_json_bytes(future), "PP_REVIEW_044_PREVIEW_INVALID")

    altered_comparison = copy.deepcopy(observed)
    altered_comparison["scenarios"][0]["comparison"] = "PASS"
    cases["forged_pass_label"] = (_json_bytes(altered_comparison), "PP_REVIEW_044_PREVIEW_INVALID")

    missing = copy.deepcopy(baseline)
    missing.pop("provenance")
    cases["missing_provenance"] = (_json_bytes(missing), "PP_REVIEW_044_PREVIEW_INVALID")

    duplicated = _json_bytes(baseline)
    duplicated = duplicated.replace(b'"authorization":"HOLD"',
                                    b'"authorization":"HOLD","authorization":"ALLOW"', 1)
    cases["duplicate_json_key"] = (duplicated, "PP_REVIEW_044_PREVIEW_INVALID")
    cases["oversized_report"] = (b" " * (MAX_REPORT_BYTES + 1), "PP_REVIEW_044_PREVIEW_INVALID")
    return cases
