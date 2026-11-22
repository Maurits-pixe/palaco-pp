"""Compare two PP recovery boundary snapshots without granting authority.

This is an offline *consistency observation*, not provenance verification.
A match never changes HOLD / DENY and never authenticates the input.
"""
from __future__ import annotations

import hashlib
import hmac
import json

from review_044_release_boundary_snapshot import (
    BoundaryInputError, MAX_INPUT_BYTES, SCHEMA, _parse_json,
)

RECONCILIATION_SCHEMA = "palaco.pp.recovery-002-boundary-reconciliation.v1"
DENIAL_FIELDS = {
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
    "deployment": "BLOCKED",
    "releaseReadiness": "NOT_READY",
    "palacoOneHandoff": "BLOCKED",
    "palacoOneSession": "NOT_CREATED",
    "independentVerification": "NOT_VERIFIED",
    "humanReview": "NOT_COMPLETED",
    "inputValidation": "STRUCTURAL_DENIALS_CONFIRMED_NOT_SOURCE_AUTHENTICATION",
}
REQUIRED_KEYS = frozenset({
    "schema", "reference", "inputSha256", "blockedGateCount",
    *DENIAL_FIELDS.keys(),
})


def _validate_snapshot(raw: bytes) -> dict:
    if type(raw) is not bytes or not (1 <= len(raw) <= MAX_INPUT_BYTES):
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    source = _parse_json(raw)
    if set(source) != REQUIRED_KEYS:
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    if source["schema"] != SCHEMA or source["reference"] != "PP-RECOVERY-002":
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    if type(source["blockedGateCount"]) is not int or source["blockedGateCount"] < 1:
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    digest = source["inputSha256"]
    if (type(digest) is not str or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)):
        raise BoundaryInputError("PP_BOUNDARY_INVALID")
    for name, expected in DENIAL_FIELDS.items():
        if type(source[name]) is not str or source[name] != expected:
            raise BoundaryInputError("PP_BOUNDARY_INVALID")
    return source


def reconcile_boundary_snapshots(first_bytes: bytes, second_bytes: bytes) -> dict:
    """Compare independent serialized observations; never approve a recovery.

    The source JSON can be forged. Equality is only evidence of identical
    *claims*, not proof of trusted provenance or two independent reviewers.
    """
    first = _validate_snapshot(first_bytes)
    second = _validate_snapshot(second_bytes)
    matching_source = hmac.compare_digest(
        first["inputSha256"], second["inputSha256"]
    )
    matching_gates = first["blockedGateCount"] == second["blockedGateCount"]
    return {
        "schema": RECONCILIATION_SCHEMA,
        "reference": "PP-RECOVERY-002",
        "firstSnapshotSha256": hashlib.sha256(first_bytes).hexdigest(),
        "secondSnapshotSha256": hashlib.sha256(second_bytes).hexdigest(),
        "sourceDigestMatch": matching_source,
        "blockedGateCountMatch": matching_gates,
        "comparison": "MATCH_UNTRUSTED" if matching_source and matching_gates else "MISMATCH",
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "independentVerification": "NOT_VERIFIED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
        "palacoOneHandoff": "BLOCKED",
    }
