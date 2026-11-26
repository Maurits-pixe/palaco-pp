"""Deterministic, offline evidence manifest for PP recovery comparisons.

An evidence *inventory*, not proof of origin, signature verification,
independent review, consent, authorization or a trusted audit ledger.
It never reads the database, filesystem, clock or network.
"""
from __future__ import annotations

import hashlib
import json

from review_044_boundary_reconciliation import (
    RECONCILIATION_SCHEMA, reconcile_boundary_snapshots,
)
from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json

MANIFEST_SCHEMA = "palaco.pp.recovery-002-evidence-manifest.v1"
MAX_ITEMS = 32
MAX_TOTAL_BYTES = 512 * 1024
DIGEST_KEYS = ("firstSnapshotSha256", "secondSnapshotSha256")


def _canonical(obj: dict) -> bytes:
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def build_evidence_manifest(pairs: tuple[tuple[bytes, bytes], ...]) -> dict:
    """Inventory unique pairs of structurally valid boundary snapshots.

    Duplicate source-pair evidence is rejected even if byte encodings differ.
    The output contains hashes and statuses only, never P.P. identifiers.
    """
    if type(pairs) is not tuple or not (1 <= len(pairs) <= MAX_ITEMS):
        raise BoundaryInputError("PP_MANIFEST_INVALID")
    if any(
        type(pair) is not tuple or len(pair) != 2
        or type(pair[0]) is not bytes or type(pair[1]) is not bytes
        for pair in pairs
    ):
        raise BoundaryInputError("PP_MANIFEST_INVALID")
    if sum(len(item) for pair in pairs for item in pair) > MAX_TOTAL_BYTES:
        raise BoundaryInputError("PP_MANIFEST_INVALID")

    entries = []
    seen = set()
    previous = "0" * 64
    for index, (first, second) in enumerate(pairs, 1):
        try:
            comparison = reconcile_boundary_snapshots(first, second)
        except (BoundaryInputError, ValueError, TypeError) as exc:
            raise BoundaryInputError("PP_MANIFEST_INVALID") from exc
        if (comparison.get("schema") != RECONCILIATION_SCHEMA
                or comparison.get("authorization") != "HOLD"
                or comparison.get("accessDecision") != "DENY"
                or comparison.get("issuance") != "NOT_AUTHORIZED"):
            raise BoundaryInputError("PP_MANIFEST_INVALID")
        # Reject semantically identical pairs even when JSON whitespace or
        # object key order differs. Raw byte digests remain in the manifest
        # for exact-input traceability. Neither digest authenticates a source.
        pair_key = tuple(sorted(comparison[key] for key in DIGEST_KEYS))
        try:
            semantic_pair_key = tuple(sorted(
                hashlib.sha256(_canonical(_parse_json(raw))).hexdigest()
                for raw in (first, second)
            ))
        except (BoundaryInputError, TypeError, ValueError) as exc:
            raise BoundaryInputError("PP_MANIFEST_INVALID") from exc
        if semantic_pair_key in seen:
            raise BoundaryInputError("PP_MANIFEST_DUPLICATE")
        seen.add(semantic_pair_key)
        record = {
            "index": index,
            "firstSnapshotSha256": pair_key[0],
            "secondSnapshotSha256": pair_key[1],
            "comparison": comparison["comparison"],
            "sourceDigestMatch": comparison["sourceDigestMatch"],
            "blockedGateCountMatch": comparison["blockedGateCountMatch"],
            "previousRecordSha256": previous,
            "sourceAuthenticity": "NOT_ESTABLISHED",
            "authorization": "HOLD",
            "accessDecision": "DENY",
        }
        previous = hashlib.sha256(_canonical(record)).hexdigest()
        entries.append(record)
    return {
        "schema": MANIFEST_SCHEMA,
        "reference": "PP-RECOVERY-002",
        "scope": "UNSIGNED_LOCAL_EVIDENCE_INVENTORY_ONLY",
        "entryCount": len(entries),
        "entries": entries,
        "headRecordSha256": previous,
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "independentVerification": "NOT_VERIFIED",
        "reviewerAuthority": "NOT_ESTABLISHED",
        "palacoOneHandoff": "BLOCKED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }


def validate_evidence_manifest(manifest_bytes: bytes) -> dict:
    """Check strict manifest structure and hash chain without trusting it."""
    if type(manifest_bytes) is not bytes or not (1 <= len(manifest_bytes) <= MAX_TOTAL_BYTES):
        raise BoundaryInputError("PP_MANIFEST_INVALID")
    source = _parse_json(manifest_bytes, max_bytes=MAX_TOTAL_BYTES)
    expected_keys = {
        "schema", "reference", "scope", "entryCount", "entries",
        "headRecordSha256", "sourceAuthenticity", "independentVerification",
        "reviewerAuthority", "palacoOneHandoff", "authorization",
        "accessDecision", "issuance", "deployment",
    }
    expected_states = {
        "scope": "UNSIGNED_LOCAL_EVIDENCE_INVENTORY_ONLY",
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "independentVerification": "NOT_VERIFIED",
        "reviewerAuthority": "NOT_ESTABLISHED",
        "palacoOneHandoff": "BLOCKED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
    if (set(source) != expected_keys or source.get("schema") != MANIFEST_SCHEMA
            or source.get("reference") != "PP-RECOVERY-002"
            or any(source.get(k) != v for k, v in expected_states.items())
            or type(source.get("entryCount")) is not int
            or not (1 <= source["entryCount"] <= MAX_ITEMS)
            or type(source.get("entries")) is not list
            or len(source["entries"]) != source["entryCount"]):
        raise BoundaryInputError("PP_MANIFEST_INVALID")
    seen = set()
    prev = "0" * 64
    expected_record_keys = {
        "index", "firstSnapshotSha256", "secondSnapshotSha256",
        "comparison", "sourceDigestMatch", "blockedGateCountMatch",
        "previousRecordSha256", "sourceAuthenticity", "authorization",
        "accessDecision",
    }
    for i, record in enumerate(source["entries"], 1):
        if type(record) is not dict or set(record) != expected_record_keys:
            raise BoundaryInputError("PP_MANIFEST_INVALID")
        first, second = record["firstSnapshotSha256"], record["secondSnapshotSha256"]
        if any(
            type(d) is not str or len(d) != 64
            or any(ch not in "0123456789abcdef" for ch in d)
            for d in (first, second)
        ):
            raise BoundaryInputError("PP_MANIFEST_INVALID")
        key = (first, second)
        if key in seen or first > second:
            raise BoundaryInputError("PP_MANIFEST_INVALID")
        seen.add(key)
        # Identical raw snapshot bytes necessarily imply identical source
        # content and blocked-gate counts. Reject impossible statements,
        # even if an attacker has recomputed the unsigned hash chain.
        if first == second and (
            record["sourceDigestMatch"] is not True
            or record["blockedGateCountMatch"] is not True
            or record["comparison"] != "MATCH_UNTRUSTED"
        ):
            raise BoundaryInputError("PP_MANIFEST_INVALID")
        if (type(record["index"]) is not int or record["index"] != i
                or type(record["sourceDigestMatch"]) is not bool
                or type(record["blockedGateCountMatch"]) is not bool
                or record["comparison"] not in ("MATCH_UNTRUSTED", "MISMATCH")
                or (record["comparison"] == "MATCH_UNTRUSTED") != (
                    record["sourceDigestMatch"] and record["blockedGateCountMatch"]
                )
                or record["previousRecordSha256"] != prev
                or record["sourceAuthenticity"] != "NOT_ESTABLISHED"
                or record["authorization"] != "HOLD"
                or record["accessDecision"] != "DENY"):
            raise BoundaryInputError("PP_MANIFEST_INVALID")
        prev = hashlib.sha256(_canonical(record)).hexdigest()
    if source["headRecordSha256"] != prev:
        raise BoundaryInputError("PP_MANIFEST_INVALID")
    return {
        "schema": "palaco.pp.recovery-002-manifest-observation.v1",
        "reference": "PP-RECOVERY-002",
        "manifestSha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "entryCount": source["entryCount"],
        "hashChain": "STRUCTURALLY_CONSISTENT_UNTRUSTED",
        "sourceAuthenticity": "NOT_ESTABLISHED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
