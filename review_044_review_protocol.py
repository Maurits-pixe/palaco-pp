"""Strict offline *claims-only* receipt/reviewer protocol for PP-RECOVERY-002.

A local receipt report is NOT actual receipt. Role claims cannot establish
identity, authority or completion. Requires the five original files and a
byte-exact handoff manifest matching the reconstructed reference. No I/O.
"""
import hashlib
import json

from review_044_human_review_handoff import prepare_human_review_handoff
from review_044_observation_register import _loads, _strict_equal
from review_044_human_review_queue import _digest

ERROR = "PP_RECOVERY_002_REVIEW_PROTOCOL_INVALID"
MAX_MANIFEST_BYTES = 32 * 1024
MAX_PROTOCOL_BYTES = 64 * 1024
MAX_EVENTS = 64
MARKS = frozenset({
    "RECEIPT_CLAIMED", "REVIEW_REQUESTED", "IDENTITY_CHECK_REQUESTED",
    "AUTHORITY_CHECK_REQUESTED", "AUTHENTICATION_BLOCKER_REPORTED",
    "EVIDENCE_GAP_REPORTED", "RECHECK_REQUESTED"
})
_FIXED = {
    "schema": "palaco.pp.recovery-002-review-protocol.v0",
    "reference": "PP-RECOVERY-002",
    "provenance": "UNSIGNED_LOCAL_ROLE_CLAIMS",
    "reviewerAuthentication": "NOT_ESTABLISHED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "recipientAuthentication": "NOT_ESTABLISHED",
    "receiptVerification": "NOT_VERIFIED",
    "humanReview": "NOT_COMPLETED",
    "deliveryVerification": "NOT_VERIFIED",
    "palacoOneHandoff": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
}
_ITEM_FIXED = {
    "claimProvenance": "SELF_REPORTED_UNAUTHENTICATED",
    "receiptVerification": "NOT_VERIFIED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "reviewStatus": "NOT_COMPLETED",
    "gate": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
}
_ITEM_KEYS = set(_ITEM_FIXED) | {
    "sequence", "mark", "roleClaim", "requirementId",
    "previousEventSha256", "eventSha256",
}
ROLES = frozenset({"OWNER_CLAIMED", "RECIPIENT_CLAIMED", "REVIEWER_CLAIMED"})
REQUIREMENTS = (
    "SOURCE_ATTESTATION", "CROSS_SOURCE_SUBJECT",
    "OWNER_AUTHORITY", "RUNTIME_EXECUTION", "HUMAN_REVIEW",
)


def _manifest(raw, dossier, queue, intake, plan, observations):
    obj = _loads(raw, MAX_MANIFEST_BYTES)
    expected = prepare_human_review_handoff(
        dossier, queue, intake, plan, observations
    )
    if not _strict_equal(obj, expected):
        raise ValueError
    return obj


def _protocol(raw, manifest_sha):
    if raw is None:
        return {**_FIXED, "handoffManifestSha256": manifest_sha, "events": []}
    record = _loads(raw, MAX_PROTOCOL_BYTES)
    if (type(record) is not dict
            or set(record) != set(_FIXED) | {"handoffManifestSha256", "events"}
            or any(record.get(key) != value for key, value in _FIXED.items())
            or record["handoffManifestSha256"] != manifest_sha):
        raise ValueError
    events = record["events"]
    if type(events) is not list or len(events) > MAX_EVENTS:
        raise ValueError
    last = None
    for i, event in enumerate(events):
        if (type(event) is not dict or set(event) != _ITEM_KEYS
                or any(event.get(key) != value for key, value in _ITEM_FIXED.items())
                or type(event["sequence"]) is not int or event["sequence"] != i + 1
                or type(event["mark"]) is not str or event["mark"] not in MARKS
                or type(event["roleClaim"]) is not str or event["roleClaim"] not in ROLES
                or type(event["requirementId"]) is not str
                or event["requirementId"] not in REQUIREMENTS
                or event["previousEventSha256"] != last
                or type(event["eventSha256"]) is not str
                or event["eventSha256"] != _digest({
                    key: value for key, value in event.items()
                    if key != "eventSha256"
                })):
            raise ValueError
        last = event["eventSha256"]
    return record


def append_review_protocol_claim(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    plan_bytes: bytes, observations_bytes: bytes,
    manifest_bytes: bytes, previous_protocol_bytes: bytes | None,
    mark: str, role_claim: str, requirement_id: str,
) -> bytes:
    """Append a claim; never authenticate receipt or reviewer identity."""
    try:
        if (type(mark) is not str or mark not in MARKS
                or type(role_claim) is not str or role_claim not in ROLES
                or type(requirement_id) is not str
                or requirement_id not in REQUIREMENTS):
            raise ValueError
        _manifest(manifest_bytes, dossier_bytes, queue_bytes, intake_bytes,
                  plan_bytes, observations_bytes)
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        record = _protocol(previous_protocol_bytes, manifest_sha)
        if len(record["events"]) >= MAX_EVENTS:
            raise ValueError
        events = record["events"]
        item = {
            "sequence": len(events) + 1,
            "mark": mark,
            "roleClaim": role_claim,
            "requirementId": requirement_id,
            "previousEventSha256": events[-1]["eventSha256"] if events else None,
            **_ITEM_FIXED,
        }
        item["eventSha256"] = _digest(item)
        events.append(item)
        result = (json.dumps(record, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        if len(result) > MAX_PROTOCOL_BYTES:
            raise ValueError
        return result
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
