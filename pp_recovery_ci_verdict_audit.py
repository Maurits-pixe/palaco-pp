"""Independent offline consistency audit of a PP CI matrix verdict.

Does not trust either verdict or source receipts. Recomputes the expected
unsigned observation from the exact supplied files and current run metadata.
Matching data is not authentication, human approval, or permission to release.
"""
from __future__ import annotations

import argparse
import hmac
import json
import os
from pathlib import Path

from pp_recovery_ci_matrix_verdict import assess_matrix
from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json

MAX_VERDICT_BYTES = 8192


def audit_verdict(
    verdict_bytes: bytes, artifact_root: Path, *,
    expected_sha: str, expected_run_id: str,
    expected_attempt: str = "1",
) -> dict:
    """Reject structurally altered, stale or contradictory verdicts."""
    if type(verdict_bytes) is not bytes or not (1 <= len(verdict_bytes) <= MAX_VERDICT_BYTES):
        raise BoundaryInputError("PP_CI_VERDICT_INVALID")
    parsed = _parse_json(verdict_bytes, max_bytes=MAX_VERDICT_BYTES)
    if type(parsed) is not dict:
        raise BoundaryInputError("PP_CI_VERDICT_INVALID")
    expected = assess_matrix(
        artifact_root, expected_sha=expected_sha,
        expected_run_id=expected_run_id,
        expected_attempt=expected_attempt,
    )
    if parsed != expected:
        raise BoundaryInputError("PP_CI_VERDICT_MISMATCH")
    # Compare canonical bytes too: a verdict with altered encoding cannot
    # later be confused with the exact create-only artifact under review.
    canonical = (json.dumps(
        expected, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ) + "\n").encode("ascii")
    if not hmac.compare_digest(verdict_bytes, canonical):
        raise BoundaryInputError("PP_CI_VERDICT_NONCANONICAL")
    if (expected["authorization"] != "HOLD"
            or expected["accessDecision"] != "DENY"
            or expected["issuance"] != "NOT_AUTHORIZED"
            or expected["deployment"] != "BLOCKED"):
        raise BoundaryInputError("PP_CI_VERDICT_AUTHORITY_INVALID")
    return {
        "schema": "palaco.pp.recovery-002-ci-verdict-audit.v1",
        "reference": "PP-RECOVERY-002",
        "audit": "MATCHING_UNTRUSTED_EXACT_BYTES",
        "syntheticMatrixObservation": expected["syntheticMatrixObservation"],
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
        "externalCIConclusion": "NOT_INDEPENDENTLY_VERIFIED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit unsigned PP CI matrix verdict")
    parser.add_argument("--verdict", required=True, type=Path)
    parser.add_argument("--artifacts", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.verdict.is_symlink() or not args.verdict.is_file():
            raise BoundaryInputError("PP_CI_VERDICT_MISSING")
        with args.verdict.open("rb") as stream:
            raw = stream.read(MAX_VERDICT_BYTES + 1)
        result = audit_verdict(
            raw, args.artifacts,
            expected_sha=os.environ.get("GITHUB_SHA", ""),
            expected_run_id=os.environ.get("GITHUB_RUN_ID", ""),
            expected_attempt=os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        )
    except (BoundaryInputError, OSError, ValueError):
        print("PP_CI_VERDICT_AUDIT_REJECTED / HOLD / DENY")
        return 1
    print("PP_CI_VERDICT_AUDIT_MATCH_UNTRUSTED / HOLD / DENY")
    return 0 if result["syntheticMatrixObservation"] == "BOTH_RECORDED_SUCCESS_UNTRUSTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
