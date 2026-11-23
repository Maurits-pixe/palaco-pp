"""Create-only, denial-only result for post-matrix CI verification.

Even on a missing/invalid receipt pair, emit a small unsigned machine-
readable verdict before exiting nonzero. This is an observation, NOT
an attestation or a release/identity authorization.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from pp_recovery_ci_matrix_gate import verify_matrix_artifacts
from pp_recovery_ci_receipt import COMMIT_SHA, RUN_ID, write_receipt
from review_044_release_boundary_snapshot import BoundaryInputError

SCHEMA = "palaco.pp.recovery-002-ci-matrix-verdict.v1"
REASONS = frozenset({
    "PAIR_REJECTED", "ARTIFACT_UNAVAILABLE",
    "INVALID_WORKFLOW_CONTEXT", "PAIR_RECORDER_INCOMPLETE",
})


def assess_matrix(
    folder: Path, *, expected_sha: str, expected_run_id: str,
) -> dict:
    """Return a bounded refusal or successful *synthetic* observation."""
    if (type(expected_sha) is not str
            or COMMIT_SHA.fullmatch(expected_sha) is None
            or type(expected_run_id) is not str
            or RUN_ID.fullmatch(expected_run_id) is None):
        status = "INCOMPLETE_OR_FAILED"
        reason = "INVALID_WORKFLOW_CONTEXT"
    else:
        try:
            observed = verify_matrix_artifacts(
                folder, expected_sha=expected_sha,
                expected_run_id=expected_run_id,
            )
        except (BoundaryInputError, OSError, ValueError):
            status = "INCOMPLETE_OR_FAILED"
            reason = "PAIR_REJECTED"
        else:
            status = observed["syntheticExecution"]
            reason = "PAIR_RECORDED_SUCCESS_UNTRUSTED"
    return {
        "schema": SCHEMA,
        "reference": "PP-RECOVERY-002",
        "commitSha": (
            expected_sha if type(expected_sha) is str
            and COMMIT_SHA.fullmatch(expected_sha) else "NOT_AVAILABLE"
        ),
        "workflowRunId": (
            expected_run_id if type(expected_run_id) is str
            and RUN_ID.fullmatch(expected_run_id) else "NOT_AVAILABLE"
        ),
        "syntheticMatrixObservation": status,
        "reason": reason,
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "externalCIConclusion": "NOT_INDEPENDENTLY_VERIFIED",
        "humanReview": "NOT_COMPLETED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Unsigned PP CI matrix verdict")
    parser.add_argument("--artifacts", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    verdict = assess_matrix(
        args.artifacts,
        expected_sha=os.environ.get("GITHUB_SHA", ""),
        expected_run_id=os.environ.get("GITHUB_RUN_ID", ""),
    )
    try:
        payload = (json.dumps(
            verdict, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ) + "\n").encode("ascii")
        write_receipt(args.output, payload)
    except (ValueError, OSError):
        print("PP_CI_MATRIX_VERDICT_EXPORT_FAILED / HOLD / DENY")
        return 1
    print(
        "PP_CI_MATRIX_VERDICT / "
        + verdict["syntheticMatrixObservation"]
        + " / HOLD / DENY / NOT_AUTHORIZED"
    )
    return (
        0 if verdict["syntheticMatrixObservation"]
        == "BOTH_RECORDED_SUCCESS_UNTRUSTED" else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
