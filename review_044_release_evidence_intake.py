"""Release Verification Evidence Intake: untrusted, non-authorizing evidence index.

Validates the 18-source execution plan and complete observation chain before
indexing exact evidence bytes against an existing observation event. A hash
match is merely local byte consistency; NOT provenance or reviewer acceptance.
No I/O, external identity, signatures, tests, deployment, or release.
"""
import hashlib
import json

from review_044_release_observation_register import (
    _plan, _register, _digest, MAX_PLAN_BYTES, MAX_REGISTER_BYTES,
    MAX_EVIDENCE_BYTES,
)
from review_044_review_protocol import _loads
from review_044_observation_register import _strict_equal

ERROR = "PP_RECOVERY_002_RELEASE_EVIDENCE_INTAKE_INVALID"
MAX_INTAKE_BYTES = 64 * 1024
MAX_RECORDS = 64
KINDS = ("DOCUMENT", "SCREENSHOT", "LOG_EXCERPT", "OTHER_UNTRUSTED")
_FIXED = {
    "schema": "palaco.pp.recovery-002-release-evidence-intake.v0",
    "reference": "PP-RECOVERY-002",
    "provenance": "UNSIGNED_LOCAL_EVIDENCE_CLAIMS",
    "independentVerification": "NOT_VERIFIED",
    "sourceAuthenticity": "NOT_ESTABLISHED",
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
_ITEM_FIXED = {
    "provenance": "UNSIGNED_LOCAL_UNTRUSTED",
    "evidenceVerification": "NOT_VERIFIED",
    "signatureVerification": "NOT_PERFORMED",
    "submitterAuthentication": "NOT_ESTABLISHED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "gate": "BLOCKED",
    "decision": "DENY",
}


def _validate_register(
    prior: bytes | None, plan_sha: str, plan: dict,
    register_sha: str,
) -> dict:
    if prior is None:
        raise ValueError
    register = _register(prior, plan_sha, plan)
    if hashlib.sha256(prior).hexdigest() != register_sha:
        raise ValueError
    return register


def _intake(raw: bytes | None, plan_sha: str, observation_sha: str,
            observations: dict) -> dict:
    if raw is None:
        return {
            **_FIXED,
            "executionPlanSha256": plan_sha,
            "observationRegisterSha256": observation_sha,
            "records": [],
        }
    record = _loads(raw, MAX_INTAKE_BYTES)
    if (type(record) is not dict
            or set(record) != set(_FIXED) | {
                "executionPlanSha256", "observationRegisterSha256", "records"
            }
            or any(not _strict_equal(record.get(k), v) for k, v in _FIXED.items())
            or record["executionPlanSha256"] != plan_sha
            or record["observationRegisterSha256"] != observation_sha
            or type(record["records"]) is not list
            or len(record["records"]) > MAX_RECORDS):
        raise ValueError
    seen = set()
    previous = None
    events = observations["events"]
    for position, item in enumerate(record["records"], 1):
        if (type(item) is not dict
                or set(item) != set(_ITEM_FIXED) | {
                    "sequence", "observationSequence", "observationEventSha256",
                    "checkId", "gateId", "evidenceKind", "evidenceSha256",
                    "evidenceByteCount", "previousRecordSha256", "recordSha256",
                }
                or any(not _strict_equal(item.get(k), v)
                       for k, v in _ITEM_FIXED.items())
                or type(item["sequence"]) is not int or item["sequence"] != position
                or type(item["observationSequence"]) is not int
                or not 1 <= item["observationSequence"] <= len(events)
                or item["observationSequence"] in seen
                or item["observationEventSha256"] !=
                   events[item["observationSequence"] - 1]["eventSha256"]
                or item["checkId"] != events[item["observationSequence"] - 1]["checkId"]
                or item["gateId"] != events[item["observationSequence"] - 1]["gateId"]
                or type(item["evidenceKind"]) is not str
                or item["evidenceKind"] not in KINDS
                or type(item["evidenceSha256"]) is not str
                or len(item["evidenceSha256"]) != 64
                or any(c not in "0123456789abcdef" for c in item["evidenceSha256"])
                or item["evidenceSha256"] !=
                   events[item["observationSequence"] - 1]["evidenceSha256"]
                or type(item["evidenceByteCount"]) is not int
                or not 0 < item["evidenceByteCount"] <= MAX_EVIDENCE_BYTES
                or item["previousRecordSha256"] != previous
                or item["recordSha256"] != _digest({
                    k: v for k, v in item.items() if k != "recordSha256"
                })):
            raise ValueError
        seen.add(item["observationSequence"])
        previous = item["recordSha256"]
    return record


def append_release_evidence_intake(
    source_bytes: tuple[bytes, ...],
    execution_plan_bytes: bytes,
    observation_register_bytes: bytes,
    previous_intake_bytes: bytes | None,
    observation_sequence: int,
    evidence_kind: str,
    evidence_bytes: bytes,
) -> bytes:
    """Append one locally hash-matched, *unverified* evidence reference."""
    try:
        if (type(source_bytes) is not tuple or len(source_bytes) != 18
                or type(observation_sequence) is not int
                or type(evidence_kind) is not str or evidence_kind not in KINDS
                or type(evidence_bytes) is not bytes
                or not 0 < len(evidence_bytes) <= MAX_EVIDENCE_BYTES):
            raise ValueError
        plan = _plan(source_bytes, execution_plan_bytes)
        plan_sha = hashlib.sha256(execution_plan_bytes).hexdigest()
        observation_sha = hashlib.sha256(observation_register_bytes).hexdigest()
        observations = _validate_register(
            observation_register_bytes, plan_sha, plan, observation_sha
        )
        events = observations["events"]
        if not 1 <= observation_sequence <= len(events):
            raise ValueError
        event = events[observation_sequence - 1]
        evidence_sha = hashlib.sha256(evidence_bytes).hexdigest()
        if event["evidenceSha256"] != evidence_sha:
            raise ValueError
        intake = _intake(previous_intake_bytes, plan_sha, observation_sha, observations)
        records = intake["records"]
        if (len(records) >= MAX_RECORDS
                or any(x["observationSequence"] == observation_sequence for x in records)):
            raise ValueError
        item = {
            "sequence": len(records) + 1,
            "observationSequence": observation_sequence,
            "observationEventSha256": event["eventSha256"],
            "checkId": event["checkId"],
            "gateId": event["gateId"],
            "evidenceKind": evidence_kind,
            "evidenceSha256": evidence_sha,
            "evidenceByteCount": len(evidence_bytes),
            "previousRecordSha256": records[-1]["recordSha256"] if records else None,
            **_ITEM_FIXED,
        }
        item["recordSha256"] = _digest(item)
        records.append(item)
        result = (json.dumps(intake, sort_keys=True, indent=2,
                             ensure_ascii=False) + "\n").encode("utf-8")
        if len(result) > MAX_INTAKE_BYTES:
            raise ValueError
        return result
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError, OverflowError) as exc:
        raise ValueError(ERROR) from exc
