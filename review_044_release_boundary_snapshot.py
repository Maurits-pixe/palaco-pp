"""PALACO-PP recovery: conservative, offline release boundary.

This module never authorizes recovery, identity linking, telecom activation,
number issuance, or deployment. It interprets review reports as untrusted
observations, not signed proof. No filesystem, network, database or clock access.
"""
from __future__ import annotations

import hashlib
import json

SCHEMA = "palaco.pp.recovery-002-boundary-snapshot.v1"
MAX_INPUT_BYTES = 64 * 1024
REQUIRED_DENIALS = {
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
}
EXPECTED_READINESS = "NOT_READY"
# Mirror the fixed gap-analysis contract without importing its dependency
# chain. If the producer changes, this gate fails closed until reviewed.
EXPECTED_GLOBAL_BLOCKERS = (
    "ORIGINAL_SOURCE_ATTESTATION_ABSENT",
    "SUBMITTER_AUTHENTICATION_ABSENT",
    "REVIEWER_IDENTITY_AND_AUTHORITY_ABSENT",
    "CROSS_SOURCE_SUBJECT_BINDING_ABSENT",
    "INDEPENDENT_HUMAN_REVIEW_NOT_COMPLETED",
    "IMMUTABLE_AUDIT_PROVENANCE_ABSENT",
)


class BoundaryInputError(ValueError):
    """An invalid, ambiguous or privilege-escalating review report."""


def _parse_json(data: bytes, *, max_bytes: int = MAX_INPUT_BYTES) -> dict:
    """Parse strict JSON with a caller-specific, bounded byte limit."""
    if (type(max_bytes) is not int or not (1 <= max_bytes <= 512 * 1024)
            or type(data) is not bytes
            or not (1 <= len(data) <= max_bytes)):
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    try:
        def reject_duplicates(pairs):
            value = {}
            for key, item in pairs:
                if key in value:
                    raise BoundaryInputError("PP_BOUNDARY_INVALID")
                value[key] = item
            return value
        result = json.loads(
            data.decode("utf-8"), object_pairs_hook=reject_duplicates,
            parse_constant=lambda _: (_ for _ in ()).throw(BoundaryInputError("PP_BOUNDARY_INVALID"))
        )
        if type(result) is not dict:
            raise BoundaryInputError("PP_BOUNDARY_INVALID")
        return result
    except (ValueError, UnicodeError, RecursionError, TypeError) as exc:
        raise BoundaryInputError("PP_BOUNDARY_INVALID") from exc


def review_boundary_snapshot(report_bytes: bytes) -> dict:
    """Fail closed on all submissions, including a syntactically valid report.

    The inspection result is explicitly *not* an authorization decision.
    No user-specific identifiers or source report content are copied to output.
    """
    source = _parse_json(report_bytes)
    if source.get("schema") != "palaco.pp.recovery-002-release-readiness.v0":
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    if source.get("reference") != "PP-RECOVERY-002":
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    for key, value in REQUIRED_DENIALS.items():
        if type(source.get(key)) is not str or source[key] != value:
            raise BoundaryInputError("PP_BOUNDARY_INVALID")
    # The canonical readiness producer always emits these explicit missing
    # prerequisites. Reject omitted or promoted trust claims, even when
    # the top-level authorization fields still say HOLD / DENY.
    required_missing = {
        "manualDecision": "REQUIRED_OUTSIDE_THIS_MODULE",
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "subjectBinding": "NOT_ESTABLISHED",
        "reviewerAuthority": "NOT_ESTABLISHED",
    }
    for key, expected in required_missing.items():
        if type(source.get(key)) is not str or source[key] != expected:
            raise BoundaryInputError("PP_BOUNDARY_INVALID")
    blockers = source.get("globalBlockers")
    if (type(blockers) is not list
            or len(blockers) != len(EXPECTED_GLOBAL_BLOCKERS)
            or any(type(item) is not str for item in blockers)
            or tuple(blockers) != EXPECTED_GLOBAL_BLOCKERS):
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    if (source.get("overallReadiness") != EXPECTED_READINESS
            or source.get("palacoOneHandoff") != "BLOCKED"
            or source.get("palacoOneSession") != "NOT_CREATED"
            or source.get("independentVerification") != "NOT_VERIFIED"
            or source.get("humanReview") != "NOT_COMPLETED"
            or type(source.get("blockedGateCount")) is not int
            or source["blockedGateCount"] < 1
            or type(source.get("gateReadiness")) is not list
            or len(source["gateReadiness"]) != source["blockedGateCount"]):
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    for gate in source["gateReadiness"]:
        if (type(gate) is not dict or gate.get("gate") != "BLOCKED"
                or gate.get("readiness") != "NOT_READY"):
            raise BoundaryInputError("PP_BOUNDARY_INVALID")
    return {
        "schema": SCHEMA,
        "reference": "PP-RECOVERY-002",
        "inputSha256": hashlib.sha256(report_bytes).hexdigest(),
        "inputValidation": "STRUCTURAL_DENIALS_CONFIRMED_NOT_SOURCE_AUTHENTICATION",
        "blockedGateCount": source["blockedGateCount"],
        "independentVerification": "NOT_VERIFIED",
        "humanReview": "NOT_COMPLETED",
        "palacoOneHandoff": "BLOCKED",
        "palacoOneSession": "NOT_CREATED",
        "releaseReadiness": "NOT_READY",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
