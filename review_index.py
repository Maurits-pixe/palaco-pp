"""Fail-closed, offline assessment of a three-file P.P. HOLD evidence chain.

This module checks local file integrity and consistency only. It never proves an
identity, grants access, changes an account, or authorizes issuance.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import json
import re

from review_bundle import link_hold_evidence
from review_handoff import _unique_pairs


MAX_INDEX_BYTES = 16 * 1024
_SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = frozenset({
    "schema", "reference", "createdAt", "linkage", "handoffSha256",
    "reportSha256", "verification", "reviewDecision", "authorization",
    "accessDecision", "issuance", "note",
})
_EXPECTED = {
    "schema": "palaco.pp.evidence-index.v0",
    "reference": "PP-RECOVERY-002",
    "linkage": "HASH_MATCH_UNTRUSTED_CLIENT_OBSERVATION",
    "verification": "NOT_VERIFIED",
    "reviewDecision": "HOLD",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
    "note": "Geen digitale handtekening, onafhankelijke bronverificatie of accountkoppeling.",
}


@dataclass(frozen=True)
class IndexAssessment:
    linkage: str = "THREE_FILE_HASH_MATCH_UNTRUSTED"
    evidence_reference: str = "PP-RECOVERY-002"
    source_verification: str = "NOT_VERIFIED"
    human_review: str = "HOLD"
    authorization: str = "HOLD"
    access_decision: str = "DENY"
    issuance: str = "NOT_AUTHORIZED"


def link_hold_index(handoff: bytes, report: bytes, index: bytes) -> IndexAssessment:
    """Compare all three files without inferring independent source authenticity.

    All malformed or inconsistent inputs raise ``ValueError('PP_INDEX_INVALID')``.
    The returned assessment is deliberately incapable of representing approval.
    """
    try:
        if not isinstance(index, bytes) or not 0 < len(index) <= MAX_INDEX_BYTES:
            raise ValueError
        # The first two files must already form a valid, fail-closed pair.
        link_hold_evidence(handoff, report)
        payload = json.loads(index.decode("utf-8"), object_pairs_hook=_unique_pairs)
        if not isinstance(payload, dict) or payload.keys() != _FIELDS:
            raise ValueError
        for key, required in _EXPECTED.items():
            if type(payload[key]) is not str or payload[key] != required:
                raise ValueError
        timestamp = payload["createdAt"]
        if type(timestamp) is not str or not timestamp.endswith("Z"):
            raise ValueError
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        for key, content in (("handoffSha256", handoff), ("reportSha256", report)):
            digest = payload[key]
            if type(digest) is not str or _SHA256_HEX.fullmatch(digest) is None:
                raise ValueError
            if not hmac.compare_digest(digest, hashlib.sha256(content).hexdigest()):
                raise ValueError
        return IndexAssessment()
    except (ValueError, UnicodeError, TypeError, KeyError, OverflowError) as exc:
        raise ValueError("PP_INDEX_INVALID") from exc
