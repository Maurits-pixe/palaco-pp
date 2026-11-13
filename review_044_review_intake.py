"""Strict offline, untrusted evidence/reviewer intake for PP-RECOVERY-002.

Original decision dossier + request queue are validated before a bounded
evidence blob can be registered by SHA-256. This module does NOT establish
the submitter's identity, reviewer authority or the evidence's origin. It
never runs tests, reads files, persists data, or grants permissions.
"""
import hashlib
import json

from review_044_human_review_queue import (
    MAX_DOSSIER_BYTES, MAX_QUEUE_BYTES, _dossier, _queue, _digest,
)

ERROR = "PP_RECOVERY_002_REVIEW_INTAKE_INVALID"
MAX_EVIDENCE_BYTES = 64 * 1024
MAX_INTAKE_BYTES = 16 * 1024
MAX_INTAKE_RECORDS = 64
_ALLOWED_ACTIONS = frozenset({"EVIDENCE_REQUESTED", "REVIEW_REQUESTED", "BLOCKER_REPORTED"})
_ALLOWED_KIND = frozenset({"DOCUMENT", "SCREENSHOT", "LOG_EXCERPT", "OTHER_UNTRUSTED"})
_ALLOWED_ROLE = frozenset({"OWNER_CLAIMED", "REVIEWER_CLAIMED", "SOURCE_CLAIMED"})
_HEX = frozenset("0123456789abcdef")
_FIXED = {
    "schema": "palaco.pp.recovery-002-review-intake.v0",
    "reference": "PP-RECOVERY-002",
    "verification": "NOT_VERIFIED",
    "sourceAuthenticity": "NOT_ESTABLISHED",
    "reviewerAuthentication": "NOT_ESTABLISHED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "subjectBinding": "NOT_ESTABLISHED",
    "humanReview": "NOT_COMPLETED",
    "palacoOneHandoff": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
}
_ITEM_FIXED = {
    "provenance": "UNSIGNED_LOCAL_UNATTESTED_INTAKE",
    "verification": "NOT_VERIFIED",
    "gate": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
}
_ITEM_FIELDS = frozenset(_ITEM_FIXED) | {
    "sequence", "requestSequence", "requestEventSha256", "requirementId",
    "evidenceSha256", "evidenceKind", "submitterRoleClaim",
    "reviewerAuthority", "sourceAuthenticity", "previousItemSha256",
    "itemSha256",
}


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError
        obj[key] = value
    return obj


def _read_json(raw, max_bytes):
    if type(raw) is not bytes or not 0 < len(raw) <= max_bytes:
        raise ValueError
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def _hash(value):
    return type(value) is str and len(value) == 64 and set(value) <= _HEX


def _check_intake(raw, dossier_hash, queue_hash, requests):
    if raw is None:
        return {**_FIXED, "decisionDossierSha256": dossier_hash,
                "requestQueueSha256": queue_hash, "items": []}
    intake = _read_json(raw, MAX_INTAKE_BYTES)
    if (type(intake) is not dict
            or set(intake) != set(_FIXED) | {"decisionDossierSha256", "requestQueueSha256", "items"}
            or any(intake.get(k) != v for k, v in _FIXED.items())
            or intake["decisionDossierSha256"] != dossier_hash
            or intake["requestQueueSha256"] != queue_hash):
        raise ValueError
    items = intake["items"]
    if type(items) is not list or len(items) > MAX_INTAKE_RECORDS:
        raise ValueError
    previous = None
    for i, item in enumerate(items):
        if (type(item) is not dict or set(item) != _ITEM_FIELDS
                or any(item.get(k) != v for k, v in _ITEM_FIXED.items())
                or type(item["sequence"]) is not int or item["sequence"] != i + 1
                or type(item["requestSequence"]) is not int
                or item["requestSequence"] not in requests
                or item["requestEventSha256"] != requests[item["requestSequence"]]["eventSha256"]
                or item["requirementId"] != requests[item["requestSequence"]]["requirementId"]
                or not _hash(item["evidenceSha256"])
                or item["evidenceKind"] not in _ALLOWED_KIND
                or item["submitterRoleClaim"] not in _ALLOWED_ROLE
                or item["reviewerAuthority"] != "NOT_ESTABLISHED"
                or item["sourceAuthenticity"] != "NOT_ESTABLISHED"
                or item["previousItemSha256"] != previous
                or not _hash(item["itemSha256"])
                or item["itemSha256"] != _digest(
                    {k: v for k, v in item.items() if k != "itemSha256"})):
            raise ValueError
        previous = item["itemSha256"]
    return intake


def append_review_intake(
    decision_dossier_bytes: bytes,
    review_queue_bytes: bytes,
    previous_intake_bytes: bytes | None,
    request_sequence: int,
    evidence_bytes: bytes,
    evidence_kind: str,
    submitter_role_claim: str,
) -> bytes:
    """Produce one new intake snapshot; acceptance is NOT verification."""
    try:
        if (type(request_sequence) is not int or request_sequence < 1
                or type(evidence_bytes) is not bytes
                or not 0 < len(evidence_bytes) <= MAX_EVIDENCE_BYTES
                or type(evidence_kind) is not str or evidence_kind not in _ALLOWED_KIND
                or type(submitter_role_claim) is not str
                or submitter_role_claim not in _ALLOWED_ROLE):
            raise ValueError
        dossier = _dossier(decision_dossier_bytes)
        dossier_hash = _digest(dossier)
        queue = _queue(review_queue_bytes, dossier_hash)
        requests = {e["sequence"]: e for e in queue["events"]}
        if request_sequence not in requests or requests[request_sequence]["action"] not in _ALLOWED_ACTIONS:
            raise ValueError
        # JSON canonicalized digest binds to validated queue content, not its
        # non-canonical input formatting. No external immutable anchor exists.
        queue_hash = _digest(queue)
        intake = _check_intake(previous_intake_bytes, dossier_hash, queue_hash, requests)
        items = intake["items"]
        if len(items) >= MAX_INTAKE_RECORDS:
            raise ValueError
        item = {
            "sequence": len(items) + 1,
            "requestSequence": request_sequence,
            "requestEventSha256": requests[request_sequence]["eventSha256"],
            "requirementId": requests[request_sequence]["requirementId"],
            "evidenceSha256": hashlib.sha256(evidence_bytes).hexdigest(),
            "evidenceKind": evidence_kind,
            "submitterRoleClaim": submitter_role_claim,
            "reviewerAuthority": "NOT_ESTABLISHED",
            "sourceAuthenticity": "NOT_ESTABLISHED",
            "previousItemSha256": items[-1]["itemSha256"] if items else None,
            **_ITEM_FIXED,
        }
        # Prevent repeat intake records for identical content and request.
        if any(existing["requestSequence"] == request_sequence
               and existing["evidenceSha256"] == item["evidenceSha256"]
               for existing in items):
            raise ValueError
        item["itemSha256"] = _digest(item)
        items.append(item)
        result = (json.dumps(intake, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if len(result) > MAX_INTAKE_BYTES:
            raise ValueError
        return result
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
