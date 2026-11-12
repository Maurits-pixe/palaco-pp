"""Offline PP-RECOVERY-002 observation register, never a verification authority.

All observation events are unsigned self-reports. Each append checks the
original three source contracts, reconstructs the verification plan, binds to
the exact plan bytes, and validates the complete prior event hash chain.
No observation can complete a check or release a gate.
"""
import hashlib
import json

from review_044_verification_plan import prepare_verification_plan
from review_044_human_review_queue import _digest

ERROR = "PP_RECOVERY_002_OBSERVATION_REGISTER_INVALID"
MAX_PLAN_BYTES = 128 * 1024
MAX_REGISTER_BYTES = 128 * 1024
MAX_EVENTS = 128
MARKS = frozenset({"OBSERVATION_REPORTED", "BLOCKER_REPORTED", "RECHECK_REQUESTED"})
_FIXED = {
    "schema": "palaco.pp.recovery-002-observation-register.v0",
    "reference": "PP-RECOVERY-002",
    "provenance": "UNSIGNED_OWNER_SELF_REPORT",
    "independentVerification": "NOT_VERIFIED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "humanReview": "NOT_COMPLETED",
    "palacoOneHandoff": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
}
_EVENT_FIXED = {
    "evidenceKind": "SELF_REPORTED_NOT_INDEPENDENTLY_VERIFIED",
    "checkStatus": "NOT_STARTED",
    "verification": "NOT_VERIFIED",
    "gate": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
}
_EVENT_KEYS = set(_EVENT_FIXED) | {
    "sequence", "intakeSequence", "checkOrder", "checkId", "mark",
    "previousEventSha256", "eventSha256",
}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _loads(raw, maximum):
    if type(raw) is not bytes or not 0 < len(raw) <= maximum:
        raise ValueError
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))


def _strict_equal(left, right):
    """Do not accept bool == 1 or numeric-string / float coercions."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (set(left) == set(right)
                and all(_strict_equal(left[key], right[key]) for key in right))
    if type(left) is list:
        return (len(left) == len(right)
                and all(_strict_equal(a, b) for a, b in zip(left, right)))
    return left == right


def _plan(raw, dossier_bytes, queue_bytes, intake_bytes):
    imported = _loads(raw, MAX_PLAN_BYTES)
    expected = prepare_verification_plan(dossier_bytes, queue_bytes, intake_bytes)
    if not _strict_equal(imported, expected):
        raise ValueError
    return expected


def _register(raw, plan_sha, plan):
    if raw is None:
        return {**_FIXED, "verificationPlanSha256": plan_sha, "events": []}
    register = _loads(raw, MAX_REGISTER_BYTES)
    if (type(register) is not dict
            or set(register) != set(_FIXED) | {"verificationPlanSha256", "events"}
            or any(register.get(key) != value for key, value in _FIXED.items())
            or register["verificationPlanSha256"] != plan_sha):
        raise ValueError
    events = register["events"]
    if type(events) is not list or len(events) > MAX_EVENTS:
        raise ValueError
    previous = None
    for index, event in enumerate(events):
        if (type(event) is not dict or set(event) != _EVENT_KEYS
                or any(event.get(key) != value for key, value in _EVENT_FIXED.items())
                or type(event["sequence"]) is not int or event["sequence"] != index + 1
                or type(event["intakeSequence"]) is not int
                or not 1 <= event["intakeSequence"] <= plan["intakeCount"]
                or type(event["checkOrder"]) is not int
                or not 1 <= event["checkOrder"] <= 6
                or event["checkId"] != plan["workItems"][event["intakeSequence"] - 1]
                   ["checks"][event["checkOrder"] - 1]["checkId"]
                or type(event["mark"]) is not str or event["mark"] not in MARKS
                or event["previousEventSha256"] != previous
                or type(event["eventSha256"]) is not str
                or event["eventSha256"] != _digest({
                    key: value for key, value in event.items()
                    if key != "eventSha256"
                })):
            raise ValueError
        previous = event["eventSha256"]
    return register


def append_observation(
    dossier_bytes: bytes, queue_bytes: bytes, intake_bytes: bytes,
    verification_plan_bytes: bytes, previous_register_bytes: bytes | None,
    intake_sequence: int, check_order: int, mark: str,
) -> bytes:
    """Create a new bounded, chained register snapshot; never approve."""
    try:
        if (type(intake_sequence) is not int or type(check_order) is not int
                or type(mark) is not str or mark not in MARKS):
            raise ValueError
        plan = _plan(verification_plan_bytes, dossier_bytes, queue_bytes, intake_bytes)
        if not 1 <= intake_sequence <= plan["intakeCount"] or not 1 <= check_order <= 6:
            raise ValueError
        plan_sha = hashlib.sha256(verification_plan_bytes).hexdigest()
        register = _register(previous_register_bytes, plan_sha, plan)
        events = register["events"]
        if len(events) >= MAX_EVENTS:
            raise ValueError
        event = {
            "sequence": len(events) + 1,
            "intakeSequence": intake_sequence,
            "checkOrder": check_order,
            "checkId": plan["workItems"][intake_sequence - 1]["checks"][check_order - 1]["checkId"],
            "mark": mark,
            "previousEventSha256": events[-1]["eventSha256"] if events else None,
            **_EVENT_FIXED,
        }
        event["eventSha256"] = _digest(event)
        events.append(event)
        encoded = (json.dumps(register, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
        if len(encoded) > MAX_REGISTER_BYTES:
            raise ValueError
        return encoded
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, IndexError) as exc:
        raise ValueError(ERROR) from exc
