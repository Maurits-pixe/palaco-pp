"""Offline detached Ed25519 *mathematical* signature check for PP evidence.

A supplied public key is UNTRUSTED. A mathematically valid signature is NOT
issuer authentication, independent reviewer verification, or authorization.
No key enrollment, persistence, network, trusted clock, nonce consumption,
recovery action, or P.P. issuance occurs.
"""
from __future__ import annotations

import hashlib

from review_044_evidence_manifest import validate_evidence_manifest
from review_044_release_boundary_snapshot import BoundaryInputError

MAX_MANIFEST_BYTES = 512 * 1024
CONTEXT = b"PALACO-PP-RECOVERY-002-MANIFEST-ED25519-V1\x00"


def inspect_detached_signature(
    manifest_bytes: bytes, public_key_bytes: bytes, signature_bytes: bytes,
) -> dict:
    """Check signature over domain-separated exact bytes, always HOLD/DENY.

    cryptography is optional and deliberately imported only on invocation.
    Absence of the library, malformed input or invalid signature fails closed.
    """
    if (type(manifest_bytes) is not bytes
            or not (1 <= len(manifest_bytes) <= MAX_MANIFEST_BYTES)
            or type(public_key_bytes) is not bytes
            or len(public_key_bytes) != 32
            or type(signature_bytes) is not bytes
            or len(signature_bytes) != 64):
        raise BoundaryInputError("PP_SIGNATURE_INPUT_INVALID")
    # First validate the existing structural contract; this is not provenance.
    observation = validate_evidence_manifest(manifest_bytes)
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    except ImportError as exc:
        raise BoundaryInputError("PP_SIGNATURE_BACKEND_UNAVAILABLE") from exc
    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
            signature_bytes, CONTEXT + manifest_bytes
        )
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise BoundaryInputError("PP_SIGNATURE_INVALID") from exc
    return {
        "schema": "palaco.pp.recovery-002-detached-signature-observation.v1",
        "reference": "PP-RECOVERY-002",
        "algorithm": "Ed25519",
        "signedDomain": "PALACO-PP-RECOVERY-002-MANIFEST-ED25519-V1",
        "manifestSha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "suppliedPublicKeySha256": hashlib.sha256(public_key_bytes).hexdigest(),
        "signatureMathematics": "VALID_UNTRUSTED_KEY",
        "manifestHashChain": observation["hashChain"],
        "keyTrust": "NOT_ESTABLISHED",
        "issuerAuthentication": "NOT_ESTABLISHED",
        "keyRevocation": "NOT_CHECKED",
        "replayProtection": "NOT_IMPLEMENTED",
        "independentVerification": "NOT_VERIFIED",
        "palacoOneHandoff": "BLOCKED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
