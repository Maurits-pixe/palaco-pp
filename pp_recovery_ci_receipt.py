"""Offline CI execution receipt for PP-RECOVERY-002 (not an attestation).

Designed to run after synthetic tests via GitHub Actions if: always().
It records observed *step outcomes*, never signs evidence, verifies
identity or grants permission. Create-only export prevents overwrite.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

SCHEMA = "palaco.pp.recovery-002-ci-execution-receipt.v1"
STEPS = ("syntax", "policy", "regressions", "boundary")
OUTCOMES = frozenset({"success", "failure", "cancelled", "skipped", "unknown"})
COMMIT_SHA = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
RUN_ID = re.compile(r"[0-9]{1,20}\Z", re.ASCII)
VERSIONS = frozenset({"3.11", "3.12"})


def build_receipt(
    outcomes: dict[str, str], *,
    commit_sha: str = "NOT_AVAILABLE",
    run_id: str = "NOT_AVAILABLE",
    python_version: str = "NOT_AVAILABLE",
) -> dict:
    """Accept only explicit step outcomes; never infer an unobserved PASS."""
    if (type(outcomes) is not dict or set(outcomes) != set(STEPS)
            or any(type(v) is not str or v not in OUTCOMES
                   for v in outcomes.values())
            or type(commit_sha) is not str
            or (commit_sha != "NOT_AVAILABLE"
                and COMMIT_SHA.fullmatch(commit_sha) is None)
            or type(run_id) is not str
            or (run_id != "NOT_AVAILABLE"
                and RUN_ID.fullmatch(run_id) is None)
            or type(python_version) is not str
            or (python_version != "NOT_AVAILABLE"
                and python_version not in VERSIONS)):
        raise ValueError("PP_CI_RECEIPT_INVALID")
    complete = all(outcomes[name] == "success" for name in STEPS)
    return {
        "schema": SCHEMA,
        "reference": "PP-RECOVERY-002",
        "commitSha": commit_sha,
        "workflowRunId": run_id,
        "pythonVersion": python_version,
        "steps": {name: outcomes[name] for name in STEPS},
        "syntheticExecution": (
            "ALL_RECORDED_STEPS_SUCCESS" if complete
            else "INCOMPLETE_OR_FAILED"
        ),
        "provenance": "UNSIGNED_WORKFLOW_LOCAL_OBSERVATION",
        "externalCIConclusion": "NOT_INDEPENDENTLY_VERIFIED",
        "humanReview": "NOT_COMPLETED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }


def encode_receipt(receipt: dict) -> bytes:
    return (json.dumps(
        receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ) + "\n").encode("ascii")


def write_receipt(target: Path, payload: bytes) -> None:
    """Create only, never overwrite a prior or symlinked receipt."""
    if (not isinstance(target, Path) or type(payload) is not bytes
            or len(payload) > 8192):
        raise ValueError("PP_CI_RECEIPT_INVALID")
    with target.open("xb") as stream:
        stream.write(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write unsigned HOLD/DENY CI receipt")
    parser.add_argument("--output", required=True)
    for name in STEPS:
        parser.add_argument(f"--{name}", required=True, choices=sorted(OUTCOMES))
    args = parser.parse_args(argv)
    try:
        receipt = build_receipt(
            {name: getattr(args, name) for name in STEPS},
            commit_sha=os.environ.get("GITHUB_SHA", "NOT_AVAILABLE"),
            run_id=os.environ.get("GITHUB_RUN_ID", "NOT_AVAILABLE"),
            python_version=os.environ.get("PP_PYTHON_VERSION", "NOT_AVAILABLE"),
        )
        write_receipt(Path(args.output), encode_receipt(receipt))
    except (ValueError, OSError) as exc:
        print(f"PP_CI_RECEIPT_WRITE_REJECTED: {type(exc).__name__}")
        return 1
    print(
        "PP_CI_RECEIPT_WRITTEN / "
        + receipt["syntheticExecution"] + " / HOLD / DENY"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
