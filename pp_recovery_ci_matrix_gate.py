"""Fail-closed CI artifact-pair gate for the synthetic PP recovery matrix.

Runs inside a separate GitHub Actions job after both matrix jobs.
This verifies unsigned receipt consistency against supplied workflow context.
Neither this check nor GitHub metadata establishes independent identity
authority or permits telecom/production actions.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from pp_recovery_ci_receipt_pair import inspect_receipt_pair
from review_044_release_boundary_snapshot import BoundaryInputError

EXPECTED_FILES = (
    Path("pp-recovery-receipt-py3.11/pp-recovery-ci-receipt.json"),
    Path("pp-recovery-receipt-py3.12/pp-recovery-ci-receipt.json"),
)
MAX_ARTIFACT_BYTES = 8192


def verify_matrix_artifacts(
    folder: Path, *, expected_sha: str, expected_run_id: str,
    expected_attempt: str = "1",
) -> dict:
    """Require two exact matrix artifacts from the expected current run.

    Missing files, invalid metadata and incomplete tests fail closed.
    No trusted attestations are claimed and no files are written.
    """
    if (not isinstance(folder, Path)
            or type(expected_sha) is not str
            or type(expected_run_id) is not str
            or type(expected_attempt) is not str):
        raise BoundaryInputError("PP_CI_MATRIX_INVALID")
    # The download directory must contain exactly the two known artifact
    # subdirectories and one receipt file inside each. Reject extras and
    # symlinked parents, rather than silently ignoring surprise evidence.
    expected_dirs = {relative.parts[0] for relative in EXPECTED_FILES}
    if (folder.is_symlink() or not folder.is_dir()
            or {child.name for child in folder.iterdir()} != expected_dirs):
        raise BoundaryInputError("PP_CI_MATRIX_UNEXPECTED_ARTIFACT")
    for dirname in expected_dirs:
        directory = folder / dirname
        if (directory.is_symlink() or not directory.is_dir()
                or {child.name for child in directory.iterdir()}
                != {"pp-recovery-ci-receipt.json"}):
            raise BoundaryInputError("PP_CI_MATRIX_UNEXPECTED_ARTIFACT")
    inputs = []
    for relative in EXPECTED_FILES:
        path = folder / relative
        if path.is_symlink() or not path.is_file():
            raise BoundaryInputError("PP_CI_MATRIX_MISSING_ARTIFACT")
        with path.open("rb") as stream:
            raw = stream.read(MAX_ARTIFACT_BYTES + 1)
        if not raw or len(raw) > MAX_ARTIFACT_BYTES:
            raise BoundaryInputError("PP_CI_MATRIX_INVALID_ARTIFACT")
        inputs.append(raw)
    observation = inspect_receipt_pair(*inputs)
    if (observation["commitSha"] != expected_sha
            or observation["workflowRunId"] != expected_run_id
            or observation["workflowRunAttempt"] != expected_attempt
            or observation["syntheticExecution"] !=
                "BOTH_RECORDED_SUCCESS_UNTRUSTED"
            or observation["authorization"] != "HOLD"
            or observation["accessDecision"] != "DENY"
            or observation["issuance"] != "NOT_AUTHORIZED"
            or observation["deployment"] != "BLOCKED"):
        raise BoundaryInputError("PP_CI_MATRIX_NOT_COMPLETE")
    return observation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify unsigned PP synthetic CI matrix; never authorize."
    )
    parser.add_argument("--artifacts", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = verify_matrix_artifacts(
            args.artifacts,
            expected_sha=os.environ.get("GITHUB_SHA", ""),
            expected_run_id=os.environ.get("GITHUB_RUN_ID", ""),
            expected_attempt=os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        )
    except (BoundaryInputError, OSError, ValueError) as exc:
        print(f"PP_CI_MATRIX_REJECTED: {type(exc).__name__} / HOLD / DENY")
        return 1
    print(
        "PP_CI_MATRIX_SYNTHETIC_COMPLETE_UNTRUSTED / "
        f"{result['commitSha']} / HOLD / DENY / NOT_AUTHORIZED"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
