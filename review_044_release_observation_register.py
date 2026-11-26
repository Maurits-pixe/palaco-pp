"""Append-only, claims-only release verification observation register.

Future manual observations bind to the exact 18-source execution plan.
Local hashes and chain continuity are NOT signatures, external evidence,
reviewer authentication, independent verification, test results or approval.
Pure functions: no file access, tests, network, sessions or authorization.
"""
import hashlib
import json

from review_044_release_execution_plan import prepare_release_verification_execution_plan
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_RELEASE_OBSERVATION_INVALID"
MAX_PLAN_BYTES = 32 * 1024
MAX_REGISTER_BYTES = 128 * 1024
MAX_EVIDENCE_BYTES = 64 * 1024
MAX_EVENTS = 128
MAX_NOTE_CHARS = 500
MARKS = ("OBSERVATION_REPORTED", "BLOCKER_REPORTED", "RECHECK_REQUESTED")
_ROLES = ("OWNER_CLAIMED", "REVIEWER_CLAIMED", "SOURCE_CLAIMED")
_FIXED = {
    "schema": "palaco.pp.recovery-002-release-observation-register.v0",
    "reference": "PP-RECOVERY-002",
    "provenance": "UNSIGNED_LOCAL_SELF_REPORT",
    "independentVerification": "NOT_VERIFIED",
    "reviewerAuthentication": "NOT_ESTABLISHED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "humanReview": "NOT_COMPLETED",
    "releaseReadiness": "NOT_READY",
    "palacoOneHandoff": "BLOCKED",
    "palacoOneSession": "NOT_CREATED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
}
_EVENT_FIXED = {
    "observationProvenance": "SELF_REPORTED_UNAUTHENTICATED",
    "evidenceVerification": "NOT_VERIFIED",
    "executionEvidence": "NOT_ESTABLISHED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "releaseGate": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
}


def _digest(obj: dict[str, object]) -> str:
    encoded = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _plan(source_bytes: tuple[bytes, ...], plan_bytes: bytes) -> dict:
    supplied = _loads(plan_bytes, MAX_PLAN_BYTES)
    expected = prepare_release_verification_execution_plan(*source_bytes)
    if not _strict_equal(supplied, expected):
        raise ValueError
    if (supplied["authorization"] != "HOLD"
            or supplied["accessDecision"] != "DENY"
            or supplied["checkCount"] != 18):
        raise ValueError
    return expected


def _register(raw: bytes | None, plan_sha: str, plan: dict) -> dict:
    if raw is None:
        return {**_FIXED, "executionPlanSha256": plan_sha, "events": []}
    register = _loads(raw, MAX_REGISTER_BYTES)
    if (type(register) is not dict
            or set(register) != set(_FIXED) | {"executionPlanSha256", "events"}
            or any(not _strict_equal(register.get(k), v) for k, v in _FIXED.items())
            or register["executionPlanSha256"] != plan_sha):
        raise ValueError
    events = register["events"]
    if type(events) is not list or len(events) > MAX_EVENTS:
        raise ValueError
    known = {item["checkId"]: item for item in plan["verificationChecks"]}
    prev = None
    for idx, item in enumerate(events, 1):
        if (type(item) is not dict
                or set(item) != set(_EVENT_FIXED) | {
                    "sequence", "checkId", "gateId", "mark", "roleClaim",
                    "note", "evidenceSha256", "previousEventSha256", "eventSha256"
                }
                or any(not _strict_equal(item.get(k), v) for k, v in _EVENT_FIXED.items())
                or type(item["sequence"]) is not int or item["sequence"] != idx
                or type(item["checkId"]) is not str or item["checkId"] not in known
                or item["gateId"] != known[item["checkId"]]["releaseGate"]
                or type(item["mark"]) is not str or item["mark"] not in MARKS
                or type(item["roleClaim"]) is not str or item["roleClaim"] not in _ROLES
                or type(item["note"]) is not str or len(item["note"]) > MAX_NOTE_CHARS
                or any(ord(c) < 32 and c not in "\n\t" for c in item["note"])
                or (item["evidenceSha256"] is not None
                    and (type(item["evidenceSha256"]) is not str
                         or len(item["evidenceSha256"]) != 64
                         or any(c not in "0123456789abcdef"
                                for c in item["evidenceSha256"])))
                or item["previousEventSha256"] != prev
                or item["eventSha256"] != _digest({
                    k: v for k, v in item.items() if k != "eventSha256"
                })):
            raise ValueError
        prev = item["eventSha256"]
    return register


def append_release_observation(
    source_bytes: tuple[bytes, ...], plan_bytes: bytes,
    previous_register_bytes: bytes | None, check_id: str, mark: str,
    role_claim: str, note: str = "", evidence_bytes: bytes | None = None,
) -> bytes:
    """Return a new strictly validated local snapshot, never a PASS."""
    try:
        if (type(source_bytes) is not tuple or len(source_bytes) != 18
                or type(check_id) is not str or type(mark) is not str
                or mark not in MARKS or type(role_claim) is not str
                or role_claim not in _ROLES or type(note) is not str
                or len(note) > MAX_NOTE_CHARS
                or any(ord(c) < 32 and c not in "\n\t" for c in note)
                or (evidence_bytes is not None
                    and (type(evidence_bytes) is not bytes
                         or not 0 < len(evidence_bytes) <= MAX_EVIDENCE_BYTES))):
            raise ValueError
        plan = _plan(source_bytes, plan_bytes)
        checks = {item["checkId"]: item for item in plan["verificationChecks"]}
        if check_id not in checks:
            raise ValueError
        register = _register(
            previous_register_bytes, hashlib.sha256(plan_bytes).hexdigest(), plan
        )
        items = register["events"]
        if len(items) >= MAX_EVENTS:
            raise ValueError
        event = {
            "sequence": len(items) + 1,
            "checkId": check_id,
            "gateId": checks[check_id]["releaseGate"],
            "mark": mark,
            "roleClaim": role_claim,
            "note": note,
            "evidenceSha256": hashlib.sha256(evidence_bytes).hexdigest()
            if evidence_bytes is not None else None,
            "previousEventSha256": items[-1]["eventSha256"] if items else None,
            **_EVENT_FIXED,
        }
        event["eventSha256"] = _digest(event)
        items.append(event)
        result = (json.dumps(register, sort_keys=True, indent=2,
                             ensure_ascii=False) + "\n").encode("utf-8")
        if len(result) > MAX_REGISTER_BYTES:
            raise ValueError
        return result
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
