"""Explicit opt-in runner for synthetic Review 044 inspection import fixtures.

No tests are performed on import or without --run. No writes or network.
This runner checks code behavior on synthetic data; NEVER authorizes identities.
"""
import argparse
import json

from review_044_inspection_fixtures import build_inspection_fixtures
from review_044_owner_inspection import validate_owner_inspection


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Synthetic, offline inspection-import review")
    parser.add_argument("--run", action="store_true", help="Run the fixtures intentionally")
    parser.add_argument("--json", action="store_true", help="Print technical outcomes as JSON")
    args = parser.parse_args(argv)
    if not args.run:
        print("NOT EXECUTED / Pass --run during the owner's test session. HOLD / DENY.")
        return 2
    results = []
    for name, registry, inspection, expected in build_inspection_fixtures():
        try:
            actual = validate_owner_inspection(registry, inspection)["result"]
        except ValueError as exc:
            actual = str(exc)
        results.append({
            "scenario_id": name,
            "expected_result": expected,
            "observed_result": actual,
            "comparison": "MATCH" if expected == actual else "MISMATCH",
            "evidence_kind": "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION",
            "authorization": "HOLD",
            "accessDecision": "DENY",
        })
    if args.json:
        print(json.dumps({
            "schema": "palaco.pp.review-044-inspection-technical-report.v0",
            "reference": "PP-RECOVERY-002",
            "scope": "SYNTHETIC_OFFLINE_ONLY",
            "observations": results,
            "independentVerification": "NOT_VERIFIED",
            "reviewDecision": "PENDING_OWNER_REVIEW",
            "authorization": "HOLD",
            "accessDecision": "DENY",
            "issuance": "NOT_AUTHORIZED",
        }, ensure_ascii=False, indent=2))
    else:
        for row in results:
            print(f"{row['scenario_id']}: {row['comparison']} ({row['observed_result']})")
        print("SYNTHETIC ONLY / NOT_VERIFIED / HOLD / DENY")
    return 1 if any(row["comparison"] != "MATCH" for row in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
