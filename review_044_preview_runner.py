"""Owner-opt-in synthetic Review 044 identity preview runner (offline only).

No checks run on import or without --run. No file writes, network, account
binding, issuance, or authorization decisions are performed.
"""

import argparse
import json
import sys

from review_044_identity_preview import preview_identity_handoff
from review_044_preview_fixtures import build_preview_fixtures


def run_synthetic_preview_cases() -> list[dict[str, str]]:
    """Invoke the pure preview only for known in-memory synthetic bytes."""
    records: list[dict[str, str]] = []
    for case_name, (raw, expected) in build_preview_fixtures().items():
        try:
            result = preview_identity_handoff(raw)
            if (result.get("authorization") == "HOLD"
                    and result.get("accessDecision") == "DENY"
                    and result.get("identityBinding") == "NOT_ESTABLISHED"
                    and result.get("session") == "NOT_CREATED"
                    and result.get("issuance") == "NOT_AUTHORIZED"):
                actual = "HOLD_DENY_PREVIEW"
            else:
                actual = "UNEXPECTED_AUTHORITY_STATE"
        except ValueError as exc:
            actual = ("PP_REVIEW_044_PREVIEW_INVALID" if str(exc) ==
                      "PP_REVIEW_044_PREVIEW_INVALID" else "UNEXPECTED_ERROR")
        except Exception:
            actual = "UNEXPECTED_ERROR"
        records.append({
            "scenario_id": case_name,
            "expected_result": expected,
            "observed_result": actual,
            "comparison": "MATCH" if actual == expected else "MISMATCH",
            "evidence_kind": "SYNTHETIC_AUTOMATED_LOCAL_EXECUTION",
            "authorization": "HOLD",
            "accessDecision": "DENY",
        })
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PALACO P.P. Review 044 identity preview")
    parser.add_argument("--run", action="store_true", help="explicitly run the synthetic checks")
    parser.add_argument("--json", action="store_true", help="print the technical report as JSON")
    args = parser.parse_args(argv)
    if not args.run:
        parser.print_help()
        print("NOT EXECUTED — owner must explicitly select --run; HOLD / DENY")
        return 2

    rows = run_synthetic_preview_cases()
    report = {
        "schema": "palaco.pp.review-044-preview-technical-report.v0",
        "reference": "PP-RECOVERY-002",
        "scope": "SYNTHETIC_OFFLINE_ONLY",
        "observations": rows,
        "verification": "NOT_INDEPENDENTLY_VERIFIED",
        "reviewDecision": "PENDING_OWNER_REVIEW",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for row in rows:
            print(f"{row['scenario_id']}: {row['comparison']} ({row['observed_result']})")
        print("SYNTHETIC ONLY — HOLD / DENY — owner review required")
    return 0 if all(row["comparison"] == "MATCH" for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
