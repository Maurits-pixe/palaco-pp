"""Non-authorizing Ed25519 verification for unsigned revocation claims.

This validates a mathematical signature over exact notice bytes under a
distinct domain. Caller-provided key is UNTRUSTED; signature verification
never authenticates an issuer, proves current revocation or grants access.
"""
from __future__ import annotations

import hashlib
import hmac

from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json
from review_044_trust_anchor_preflight import MAX_PROPOSAL_BYTES
from review_044_unsigned_revocation_notice import (
    MAX_NOTICE_BYTES, inspect_unsigned_revocation_notice,
)

CONTEXT = b"PALACO-PP-RECOVERY-002-REVOCATION-ED25519-V1\x00"


def inspect_revocation_signature(
    proposal_bytes: bytes,
    notice_bytes: bytes,
    public_key_bytes: bytes,
    signature_bytes: bytes,
) -> dict:
    """Verify exact notice bytes with an untrusted candidate key; deny always.

    The candidate key's fingerprint must match the pending proposal. A
    signature can be self-produced: it is NOT authenticated revocation.
    """
    unsigned = inspect_unsigned_revocation_notice(proposal_bytes, notice_bytes)
    if (type(public_key_bytes) is not bytes or len(public_key_bytes) != 32
            or type(signature_bytes) is not bytes or len(signature_bytes) != 64):
        raise BoundaryInputError("PP_REVOCATION_SIGNATURE_INVALID")
    candidate = _parse_json(proposal_bytes, max_bytes=MAX_PROPOSAL_BYTES)
    digest = hashlib.sha256(public_key_bytes).hexdigest()
    if not hmac.compare_digest(candidate["publicKeySha256"], digest):
        raise BoundaryInputError("PP_REVOCATION_SIGNATURE_KEY_MISMATCH")
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise BoundaryInputError("PP_REVOCATION_CRYPTO_UNAVAILABLE") from exc
    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
            signature_bytes, CONTEXT + notice_bytes
        )
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise BoundaryInputError("PP_REVOCATION_SIGNATURE_INVALID") from exc
    if (unsigned["authorization"] != "HOLD"
            or unsigned["accessDecision"] != "DENY"
            or unsigned["registryModified"] is not False):
        raise BoundaryInputError("PP_REVOCATION_SIGNATURE_INVALID")
    return {
        "schema": "palaco.pp.recovery-002-revocation-signature-observation.v1",
        "reference": "PP-RECOVERY-002",
        "noticeSha256": hashlib.sha256(notice_bytes).hexdigest(),
        "proposalSha256": hashlib.sha256(proposal_bytes).hexdigest(),
        "candidatePublicKeySha256": digest,
        "signatureMathematics": "VALID_UNTRUSTED_KEY",
        "signedDomain": "PALACO-PP-RECOVERY-002-REVOCATION-ED25519-V1",
        "revocationClaim": "REVOKED_UNTRUSTED",
        "issuerAuthentication": "NOT_ESTABLISHED",
        "trustedRevocation": "NOT_VERIFIED",
        "freshness": "NOT_VERIFIED",
        "replayProtection": "NOT_IMPLEMENTED",
        "nonRevocation": "NOT_ESTABLISHED",
        "registryModified": False,
        "independentVerification": "NOT_VERIFIED",
        "palacoOneHandoff": "BLOCKED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
