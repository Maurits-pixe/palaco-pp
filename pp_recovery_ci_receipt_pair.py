"""Offline, non-authorizing comparison of two unsigned GitHub CI receipts.

A pair of receipts is UNTRUSTED even when both claim success. Verification
of GitHub provenance, workflow conclusion and independent reviewers is
outside this module. Never promotes deployment or P.P. issuance.
"""
from __future__ import annotations

import hashlib

from pp_recovery_ci_receipt import (
    SCHEMA, STEPS, VERSIONS, build_receipt, encode_receipt,
)
from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json

MAX_RECEIPT_BYTES = 8192
EXPECTED_KEYS = frozenset(build_receipt(
    {name: "unknown" for name in STEPS}
))


def _parse_receipt(raw: bytes) -> dict:
    if type(raw) is not bytes or not (1 <= len(raw) <= MAX_RECEIPT_BYTES):
        raise BoundaryInputError("PP_CI_PAIR_INVALID")
    try:
        source = _parse_json(raw, max_bytes=MAX_RECEIPT_BYTES)
        if (set(source) != EXPECTED_KEYS
                or source.get("schema") != SCHEMA
                or source.get("reference") != "PP-RECOVERY-002"
                or type(source.get("steps")) is not dict
                or set(source["steps"]) != set(STEPS)):
            raise ValueError
        expected = build_receipt(
            source["steps"], commit_sha=source["commitSha"],
            run_id=source["workflowRunId"],
            python_version=source["pythonVersion"],
        )
        if source != expected:
            raise ValueError
        if (source["commitSha"] == "NOT_AVAILABLE"
                or source["workflowRunId"] == "NOT_AVAILABLE"
                or source["pythonVersion"] not in VERSIONS):
            raise ValueError
        return source
    except (ValueError, TypeError, KeyError) as exc:
        raise BoundaryInputError("PP_CI_PAIR_INVALID") from exc


def inspect_receipt_pair(first_bytes: bytes, second_bytes: bytes) -> dict:
    """Enforce exact Python-version pair and run/commit consistency."""
    first = _parse_receipt(first_bytes)
    second = _parse_receipt(second_bytes)
    if (first["pythonVersion"] == second["pythonVersion"]
            or {first["pythonVersion"], second["pythonVersion"]} != VERSIONS
            or first["commitSha"] != second["commitSha"]
            or first["workflowRunId"] != second["workflowRunId"]):
        raise BoundaryInputError("PP_CI_PAIR_MISMATCH")
    outcomes = (first["syntheticExecution"], second["syntheticExecution"])
    matched = all(
        value == "ALL_RECORDED_STEPS_SUCCESS" for value in outcomes
    )
    return {
        "schema": "palaco.pp.recovery-002-ci-receipt-pair-observation.v1",
        "reference": "PP-RECOVERY-002",
        "commitSha": first["commitSha"],
        "workflowRunId": first["workflowRunId"],
        "pythonVersions": ["3.11", "3.12"],
        "receiptSha256ByVersion": {
            first["pythonVersion"]: hashlib.sha256(first_bytes).hexdigest(),
            second["pythonVersion"]: hashlib.sha256(second_bytes).hexdigest(),
        },
        "pairConsistency": "MATCHING_UNTRUSTED_RUN_AND_COMMIT",
        "syntheticExecution": (
            "BOTH_RECORDED_SUCCESS_UNTRUSTED" if matched
            else "INCOMPLETE_OR_FAILED"
        ),
        "externalCIConclusion": "NOT_INDEPENDENTLY_VERIFIED",
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "humanReview": "NOT_COMPLETED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
