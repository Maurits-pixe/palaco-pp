"""Offline, read-only evidence linkage between a handoff and HOLD review.

The SHA-256 comparison detects file mismatches; it does not authenticate the
sender or confer identity, account ownership, or authorization.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import json
import re

from review_handoff import parse_review_handoff, _unique_pairs


MAX_REPORT_BYTES = 16 * 1024


@dataclass(frozen=True)
class BundleAssessment:
    linkage: str = "HASH_MATCH_UNTRUSTED"
    evidence_reference: str = "PP-RECOVERY-002"
    source_verification: str = "NOT_VERIFIED"
    human_review: str = "HOLD"
    authorization: str = "HOLD"
    access_decision: str = "DENY"
    issuance: str = "NOT_AUTHORIZED"


def _reject():
    # Error is deliberately uniform; no user content or ID is disclosed.
    raise ValueError("PP_BUNDLE_INVALID")


def link_hold_evidence(handoff: bytes, report: bytes) -> BundleAssessment:
    """Check two untrusted bytestrings belong together, without persistence."""
    if not isinstance(report, bytes) or not 0 < len(report) <= MAX_REPORT_BYTES:
        _reject()
    try:
        parse_review_handoff(handoff)
        review = json.loads(report.decode("utf-8"),
                            object_pairs_hook=_unique_pairs,
                            parse_constant=lambda _: _reject())
    except (ValueError, UnicodeDecodeError, RecursionError):
        _reject()
    if not isinstance(review, dict) or set(review) != {
        "schema", "evidenceReference", "capturedAt", "fileSha256",
        "structuralStatus", "sourceEvidence", "verification", "reviewDecision",
        "authorization", "accessDecision", "issuance", "note", "noteClass",
    }:
        _reject()
    expected = {
        "schema": "palaco.pp.manual-review.v0",
        "evidenceReference": "PP-RECOVERY-002",
        "structuralStatus": "CLIENT_STRUCTURE_RECOGNIZED_UNTRUSTED",
        "sourceEvidence": "UNSIGNED_USER_SUPPLIED_FILE",
        "verification": "NOT_VERIFIED",
        "reviewDecision": "HOLD",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "noteClass": "LOCAL_ADMIN_NOTE_NOT_INDEPENDENTLY_VERIFIED",
    }
    if any(review.get(key) != value for key, value in expected.items()):
        _reject()
    if not isinstance(review["note"], str) or len(review["note"]) > 240:
        _reject()
    captured = review["capturedAt"]
    if not isinstance(captured, str) or len(captured) > 40:
        _reject()
    try:
        timestamp = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    except ValueError:
        _reject()
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        _reject()
    digest = review["fileSha256"]
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        _reject()
    if not hmac.compare_digest(digest, hashlib.sha256(handoff).hexdigest()):
        _reject()
    return BundleAssessment()
