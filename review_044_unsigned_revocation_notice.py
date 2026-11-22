"""Offline inspection of an unsigned PP key-revocation claim.

A revocation notice is UNTRUSTED data. This code never treats a missing
notice as proof of non-revocation and never enrolls or re-enables keys.
Trusted signature validation, freshness and authenticated issuer controls
must be implemented independently before any operational use.
"""
from __future__ import annotations

import hashlib
import hmac

from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json
from review_044_trust_anchor_preflight import (
    MAX_PROPOSAL_BYTES, inspect_trust_anchor_proposal,
)

SCHEMA = "palaco.pp.recovery-002-unsigned-revocation-notice.v1"
MAX_NOTICE_BYTES = 8 * 1024
NOTICE_KEYS = frozenset({
    "schema", "reference", "issuerId", "keyId",
    "publicKeySha256", "claim", "evidenceState",
})


def inspect_unsigned_revocation_notice(
    proposal_bytes: bytes, notice_bytes: bytes,
) -> dict:
    """Bind an unsigned revocation *claim* to a pending key proposal.

    Returns blocked states only. A matching notice has no verified
    provenance and does not alter any real key/issuer registry.
    """
    preflight = inspect_trust_anchor_proposal(proposal_bytes)
    try:
        candidate = _parse_json(proposal_bytes, max_bytes=MAX_PROPOSAL_BYTES)
        notice = _parse_json(notice_bytes, max_bytes=MAX_NOTICE_BYTES)
        if (set(notice) != NOTICE_KEYS
                or notice.get("schema") != SCHEMA
                or notice.get("reference") != "PP-RECOVERY-002"
                or type(notice.get("issuerId")) is not str
                or type(notice.get("keyId")) is not str
                or type(notice.get("publicKeySha256")) is not str
                or notice.get("claim") != "REVOKED"
                or notice.get("evidenceState") != "UNSIGNED_UNVERIFIED"
                or not hmac.compare_digest(notice["issuerId"], candidate["issuerId"])
                or not hmac.compare_digest(notice["keyId"], candidate["keyId"])
                or not hmac.compare_digest(
                    notice["publicKeySha256"], candidate["publicKeySha256"]
                )
                or preflight["authorization"] != "HOLD"):
            raise BoundaryInputError("PP_REVOCATION_NOTICE_INVALID")
    except (TypeError, KeyError, ValueError) as exc:
        raise BoundaryInputError("PP_REVOCATION_NOTICE_INVALID") from exc
    return {
        "schema": "palaco.pp.recovery-002-revocation-observation.v1",
        "reference": "PP-RECOVERY-002",
        "proposalSha256": hashlib.sha256(proposal_bytes).hexdigest(),
        "noticeSha256": hashlib.sha256(notice_bytes).hexdigest(),
        "claim": "REVOKED_UNTRUSTED",
        "claimBinding": "MATCHES_UNTRUSTED_CANDIDATE",
        "trustedRevocation": "NOT_VERIFIED",
        "nonRevocation": "NOT_ESTABLISHED",
        "issuerAuthentication": "NOT_ESTABLISHED",
        "registryModified": False,
        "keyTrust": "NOT_ESTABLISHED",
        "independentVerification": "NOT_VERIFIED",
        "palacoOneHandoff": "BLOCKED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
