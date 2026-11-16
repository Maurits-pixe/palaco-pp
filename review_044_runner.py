"""Explicit opt-in, offline runner for synthetic P.P. Review 044 fixtures.

Nothing runs on import. No network calls, writes, identity decisions or issuance.
Execute only when the owner chooses to run the prepared review.
"""

import argparse
import json
import sys

from review_chain import link_hold_chain
from review_fixtures import build_review_fixtures


EXPECTED = {
    "baseline_untrusted_hold": "FOUR_FILE_HASH_MATCH_UNTRUSTED",
    "handoff_changed_without_rebinding": "PP_CHAIN_INVALID",
    "report_authority_escalation": "PP_CHAIN_INVALID",
    "index_wrong_report_digest": "PP_CHAIN_INVALID",
    "observation_wrong_index_digest": "PP_CHAIN_INVALID",
    "observation_authority_escalation": "PP_CHAIN_INVALID",
    "observation_duplicate_key": "PP_CHAIN_INVALID",
    "observation_truncated_json": "PP_CHAIN_INVALID",
    "observation_oversized": "PP_CHAIN_INVALID",
}


def review_synthetic_cases() -> list[dict[str, str]]:
    """Run only synthetic cases; record technical results, never approval."""
    fixtures = build_review_fixtures()
    result = []
    for name, expected in EXPECTED.items():
        try:
            actual = link_hold_chain(*fixtures[name]).linkage
        except ValueError as exc:
            # Deliberately expose only known, non-identifying failure codes.
            actual = "PP_CHAIN_INVALID" if str(exc) == "PP_CHAIN_INVALID" else "UNEXPECTED_ERROR"
        except Exception:
            actual = "UNEXPECTED_ERROR"
        result.append({
            "scenario_id": name,
            "expected_result": expected,
            "observed_result": actual,
            "comparison": "MATCH" if actual == expected else "MISMATCH",
            "evidence_kind": "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION",
            "authorization": "HOLD",
            "access_decision": "DENY",
        })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PALACO PHONE Review 044 (synthetic, offline)")
    parser.add_argument("--run", action="store_true", help="run the nine prepared local cases")
    parser.add_argument("--json", action="store_true", help="print JSON instead of concise text")
    args = parser.parse_args(argv)
    if not args.run:
        parser.print_help()
        print("NOT EXECUTED — explicit --run required; HOLD / DENY")
        return 2
    observations = review_synthetic_cases()
    report = {
        "schema": "palaco.pp.review-044-technical-observation.v0",
        "reference": "PP-RECOVERY-002",
        "scope": "SYNTHETIC_OFFLINE_ONLY",
        "observations": observations,
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "reviewDecision": "PENDING_OWNER_REVIEW",
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for item in observations:
            print(f"{item['scenario_id']}: {item['comparison']} ({item['observed_result']})")
        print("SYNTHETIC ONLY — HOLD / DENY — human review remains pending")
    return 0 if all(item["comparison"] == "MATCH" for item in observations) else 1


if __name__ == "__main__":
    sys.exit(main())
