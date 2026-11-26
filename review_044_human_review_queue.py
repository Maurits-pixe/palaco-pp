"""Offline, append-only-claim human review queue for PP-RECOVERY-002.

No external identity, reviewer authorization, timestamp or immutable storage
is established by this module. Each append returns new JSON bytes; caller
must explicitly save them. The five decision gates remain blocked.
"""
import hashlib
import json

from review_044_recovery_decision import REQUIREMENTS

ERROR = "PP_RECOVERY_002_REVIEW_QUEUE_INVALID"
MAX_DOSSIER_BYTES = 16 * 1024
MAX_QUEUE_BYTES = 128 * 1024
MAX_EVENTS = 128
_ACTIONS = frozenset({"REVIEW_REQUESTED", "BLOCKER_REPORTED", "EVIDENCE_REQUESTED"})
_REQ = tuple(name for name, _ in REQUIREMENTS)
_HEX = frozenset("0123456789abcdef")
_FIXED = {
    "schema": "palaco.pp.recovery-002-human-review-queue.v0",
    "reference": "PP-RECOVERY-002",
    "evidenceVerification": "NOT_VERIFIED",
    "crossSourceSubjectBinding": "NOT_ESTABLISHED",
    "ownerAuthority": "NOT_ESTABLISHED",
    "humanReview": "NOT_COMPLETED",
    "palacoOneHandoff": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
}
_DOSSIER_FIXED = {
    "schema": "palaco.pp.recovery-002-decision-dossier.v0",
    "reference": "PP-RECOVERY-002",
    "openRequirementCount": 5,
    "crossSourceSubjectBinding": "NOT_ESTABLISHED",
    "ownerAuthority": "NOT_ESTABLISHED",
    "humanReview": "NOT_COMPLETED",
    "palacoOneHandoff": "BLOCKED",
    "palacoOneSession": "NOT_CREATED",
    "independentVerification": "NOT_VERIFIED",
    "reviewDecision": "HOLD",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
    "nextPermittedStep": "MANUAL_SOURCE_AND_IDENTITY_REVIEW_ONLY",
}
_DOSSIER_KEYS = frozenset(_DOSSIER_FIXED) | {
    "coordinationSha256", "handoffSha256", "technicalReportSha256",
    "ownerWorksheetSha256", "localRegistrationStatus", "technicalEvidence",
    "requirements", "selfReportedMarkCount",
}
_EVENT_FIXED = {
    "provenance": "UNSIGNED_LOCAL_REVIEW_REQUEST",
    "verification": "NOT_VERIFIED",
    "gate": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
}
_EVENT_KEYS = frozenset(_EVENT_FIXED) | {
    "sequence", "requirementId", "action", "previousEventSha256", "eventSha256"
}


def _pairs(pairs):
    obj = {}
    for name, value in pairs:
        if name in obj:
            raise ValueError
        obj[name] = value
    return obj


def _load(raw, maximum):
    if type(raw) is not bytes or not 0 < len(raw) <= maximum:
        raise ValueError
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def _hex64(value):
    return type(value) is str and len(value) == 64 and set(value) <= _HEX


def _digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _dossier(raw):
    obj = _load(raw, MAX_DOSSIER_BYTES)
    if (type(obj) is not dict or set(obj) != _DOSSIER_KEYS
            or any(obj.get(k) != v for k, v in _DOSSIER_FIXED.items())
            or not all(_hex64(obj[k]) for k in (
                "coordinationSha256", "handoffSha256", "technicalReportSha256",
                "ownerWorksheetSha256"))
            or obj["localRegistrationStatus"] not in ("ACTIVE", "REVOKED")
            or obj["technicalEvidence"] != "STRICT_PYTHON_TWO_FILE_HASH_MATCH_UNTRUSTED"):
        raise ValueError
    rows = obj["requirements"]
    if type(rows) is not list or len(rows) != len(_REQ):
        raise ValueError
    marked = 0
    for row, name in zip(rows, _REQ):
        if (type(row) is not dict
                or set(row) != {"requirementId", "description", "evidenceStatus",
                                "ownerMark", "markProvenance", "gate"}
                or row["requirementId"] != name
                or row["description"] != dict(REQUIREMENTS)[name]
                or row["evidenceStatus"] != "NOT_ESTABLISHED"
                or row["gate"] != "BLOCKED"
                or row["ownerMark"] not in ("NOT_REVIEWED", "REVIEW_REQUESTED", "BLOCKER_REPORTED")
                or row["markProvenance"] not in ("SELF_REPORTED", "NO_OBSERVATION")
                or (row["markProvenance"] == "NO_OBSERVATION" and row["ownerMark"] != "NOT_REVIEWED")):
            raise ValueError
        marked += row["markProvenance"] == "SELF_REPORTED"
    if type(obj["selfReportedMarkCount"]) is not int or obj["selfReportedMarkCount"] != marked:
        raise ValueError
    return obj


def _queue(raw, dossier_hash):
    if raw is None:
        return {**_FIXED, "decisionDossierSha256": dossier_hash, "events": []}
    data = _load(raw, MAX_QUEUE_BYTES)
    if (type(data) is not dict or set(data) != set(_FIXED) | {"decisionDossierSha256", "events"}
            or any(data.get(k) != v for k, v in _FIXED.items())
            or data["decisionDossierSha256"] != dossier_hash):
        raise ValueError
    events = data["events"]
    if type(events) is not list or len(events) > MAX_EVENTS:
        raise ValueError
    previous = None
    for i, event in enumerate(events):
        if (type(event) is not dict or set(event) != _EVENT_KEYS
                or any(event.get(k) != v for k, v in _EVENT_FIXED.items())
                or type(event["sequence"]) is not int or event["sequence"] != i + 1
                or event["requirementId"] not in _REQ
                or event["action"] not in _ACTIONS
                or event["previousEventSha256"] != previous
                or not _hex64(event["eventSha256"])
                or event["eventSha256"] != _digest(
                    {k: v for k, v in event.items() if k != "eventSha256"})):
            raise ValueError
        previous = event["eventSha256"]
    return data


def append_review_request(
    dossier_bytes: bytes,
    previous_queue_bytes: bytes | None,
    requirement_id: str,
    action: str,
) -> bytes:
    """Append one *unverified request*, never a human sign-off or approval."""
    try:
        if type(requirement_id) is not str or requirement_id not in _REQ:
            raise ValueError
        if type(action) is not str or action not in _ACTIONS:
            raise ValueError
        dossier = _dossier(dossier_bytes)
        queue = _queue(previous_queue_bytes, _digest(dossier))
        events = queue["events"]
        if len(events) >= MAX_EVENTS:
            raise ValueError
        event = {
            "sequence": len(events) + 1,
            "requirementId": requirement_id,
            "action": action,
            "previousEventSha256": events[-1]["eventSha256"] if events else None,
            **_EVENT_FIXED,
        }
        event["eventSha256"] = _digest(event)
        events.append(event)
        raw = (json.dumps(queue, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
        if len(raw) > MAX_QUEUE_BYTES:
            raise ValueError
        return raw
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
