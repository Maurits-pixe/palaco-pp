"""Strict offline four-file consistency check for unsigned P.P. evidence.

The fourth file is a client observation, not an authorization or source proof.
No disk, network, identity, account, or issuance operation is performed here.
"""

from dataclasses import dataclass
from datetime import datetime
import hashlib
import hmac
import json
import re

from review_index import link_hold_index
from review_handoff import _unique_pairs


MAX_OBSERVATION_BYTES = 16 * 1024
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_FIELDS = frozenset({
    "schema", "reference", "capturedAt", "outcome", "handoffSha256",
    "reportSha256", "indexSha256", "verification", "reviewDecision",
    "authorization", "accessDecision", "issuance", "provenance",
})
_FIXED = {
    "schema": "palaco.pp.chain-observation.v0",
    "reference": "PP-RECOVERY-002",
    "outcome": "CLIENT_THREE_FILE_HASH_MATCH_UNTRUSTED",
    "verification": "NOT_VERIFIED",
    "reviewDecision": "HOLD",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
    "provenance": "UNSIGNED_LOCAL_BROWSER_OBSERVATION",
}


@dataclass(frozen=True)
class ChainAssessment:
    linkage: str = "FOUR_FILE_HASH_MATCH_UNTRUSTED"
    reference: str = "PP-RECOVERY-002"
    source_verification: str = "NOT_VERIFIED"
    authorization: str = "HOLD"
    access_decision: str = "DENY"
    issuance: str = "NOT_AUTHORIZED"


def link_hold_chain(
    handoff: bytes, report: bytes, index: bytes, observation: bytes,
) -> ChainAssessment:
    """Reject malformed files and any mismatch with ``PP_CHAIN_INVALID``.

    Passing only establishes content consistency among four untrusted files.
    """
    try:
        if not isinstance(observation, bytes) or not 0 < len(observation) <= MAX_OBSERVATION_BYTES:
            raise ValueError
        link_hold_index(handoff, report, index)
        data = json.loads(observation.decode("utf-8"), object_pairs_hook=_unique_pairs)
        if not isinstance(data, dict) or data.keys() != _FIELDS:
            raise ValueError
        for key, value in _FIXED.items():
            if type(data[key]) is not str or data[key] != value:
                raise ValueError
        captured_at = data["capturedAt"]
        if type(captured_at) is not str or not captured_at.endswith("Z"):
            raise ValueError
        parsed = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError
        for key, content in (
            ("handoffSha256", handoff),
            ("reportSha256", report),
            ("indexSha256", index),
        ):
            digest = data[key]
            if type(digest) is not str or _DIGEST.fullmatch(digest) is None:
                raise ValueError
            if not hmac.compare_digest(digest, hashlib.sha256(content).hexdigest()):
                raise ValueError
        return ChainAssessment()
    except (ValueError, UnicodeError, TypeError, KeyError, OverflowError) as exc:
        raise ValueError("PP_CHAIN_INVALID") from exc
