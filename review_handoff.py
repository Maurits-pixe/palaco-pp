"""Side-effect-free draft parser for untrusted PALACO PHONE review handoffs.

Structural acceptance never verifies identity or grants rights.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from uuid import UUID


MAX_BYTES = 16 * 1024
CONSTRAINTS = frozenset((
    "NO_AUTOMATIC_ACCOUNT_LINK", "NO_AUTHENTICATION", "NO_AUTO_ISSUANCE",
))


@dataclass(frozen=True)
class ReviewAssessment:
    subject_reference: str
    option_reference: str
    registration_status: str
    structural_status: str = "STRUCTURE_ACCEPTED_UNTRUSTED"
    identity_verification: str = "NOT_VERIFIED"
    review_decision: str = "PENDING_HUMAN_REVIEW"
    authorization: str = "HOLD"
    access_decision: str = "DENY"
    issuance: str = "NOT_AUTHORIZED"


def _reject():
    # Never echo user-controlled JSON or sensitive references in errors.
    raise ValueError("PP_HANDOFF_INVALID")


def _object(value, keys):
    if not isinstance(value, dict) or set(value) != keys:
        _reject()
    return value


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _reject()
        result[key] = value
    return result


def _timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        _reject()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _reject()
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _reject()
    return parsed.astimezone(timezone.utc)


def _uuid(value):
    if not isinstance(value, str) or len(value) != 36:
        _reject()
    try:
        parsed = UUID(value)
    except ValueError:
        _reject()
    if str(parsed) != value.lower():
        _reject()
    return str(parsed)


def parse_review_handoff(raw: bytes) -> ReviewAssessment:
    """Validate exact v0 shape only; never authorize, import, or link accounts."""
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_BYTES:
        _reject()
    try:
        document = json.loads(raw.decode("utf-8"),
                              parse_constant=lambda _: _reject(),
                              object_pairs_hook=_unique_pairs)
    except (ValueError, UnicodeDecodeError, RecursionError):
        _reject()
    _object(document, {
        "schema", "reference", "createdAt", "source", "destination",
        "subjectReference", "registration", "provenance",
        "identityVerification", "reviewDecision", "authorization",
        "accessDecision", "issuance", "constraints",
    })
    expected = {
        "schema": "palaco.pp.one.review-handoff.v0",
        "reference": "PP-RECOVERY-002",
        "source": "LOCAL_PP_PROTOTYPE_USER_EXPORTED",
        "destination": "PALACO_ONE_MANUAL_REVIEW_ONLY",
        "provenance": "UNSIGNED_USER_CONTROLLED_FILE",
        "identityVerification": "NOT_VERIFIED",
        "reviewDecision": "PENDING_HUMAN_REVIEW",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
    }
    if any(document.get(key) != value for key, value in expected.items()):
        _reject()
    constraints = document["constraints"]
    if (not isinstance(constraints, list) or len(constraints) != 3
            or any(not isinstance(item, str) for item in constraints)
            or set(constraints) != CONSTRAINTS):
        _reject()
    created = _timestamp(document["createdAt"])
    subject = _object(document["subjectReference"], {"consumerId"})
    registration = _object(document["registration"], {
        "ppNumberId", "ppNumberLast4", "status", "selectedAt", "revokedAt",
    })
    consumer_id = _uuid(subject["consumerId"])
    option_id = _uuid(registration["ppNumberId"])
    last_four = registration["ppNumberLast4"]
    if not isinstance(last_four, str) or not re.fullmatch(r"[0-9]{4}", last_four):
        _reject()
    if registration["status"] not in ("ACTIVE", "REVOKED"):
        _reject()
    selected = _timestamp(registration["selectedAt"])
    if selected > created:
        _reject()
    if registration["status"] == "ACTIVE":
        if registration["revokedAt"] is not None:
            _reject()
    else:
        revoked = _timestamp(registration["revokedAt"])
        if revoked < selected or revoked > created:
            _reject()
    return ReviewAssessment(consumer_id, option_id, registration["status"])
