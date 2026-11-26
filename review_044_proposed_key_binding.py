"""Non-authorizing binding of untrusted issuer proposal to detached signature.

This records only a structural connection between a candidate key
fingerprint and the exact key used for mathematical Ed25519 verification.
It is NOT issuer authentication, a trusted key registry, proof of possession
by the named issuer, reviewer authorization, or a release decision.
"""
from __future__ import annotations

import hashlib
import hmac

from review_044_detached_signature_inspection import inspect_detached_signature
from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json
from review_044_trust_anchor_preflight import (
    MAX_PROPOSAL_BYTES, inspect_trust_anchor_proposal,
)

SCHEMA = "palaco.pp.recovery-002-key-proposal-signature-binding.v1"


def inspect_proposed_key_binding(
    proposal_bytes: bytes,
    manifest_bytes: bytes,
    public_key_bytes: bytes,
    signature_bytes: bytes,
) -> dict:
    """Fail closed on a mismatch; even a match has no authority."""
    preflight = inspect_trust_anchor_proposal(proposal_bytes)
    if type(public_key_bytes) is not bytes or len(public_key_bytes) != 32:
        raise BoundaryInputError("PP_KEY_BINDING_INVALID")
    proposed = _parse_json(proposal_bytes, max_bytes=MAX_PROPOSAL_BYTES)
    expected_fingerprint = hashlib.sha256(public_key_bytes).hexdigest()
    if not hmac.compare_digest(
        proposed["publicKeySha256"], expected_fingerprint
    ):
        raise BoundaryInputError("PP_KEY_BINDING_MISMATCH")

    signature = inspect_detached_signature(
        manifest_bytes, public_key_bytes, signature_bytes
    )
    if (preflight["trustAnchorImported"] is not False
            or preflight["trustedIssuerCount"] != 0
            or preflight["authorization"] != "HOLD"
            or signature["signatureMathematics"] != "VALID_UNTRUSTED_KEY"
            or signature["suppliedPublicKeySha256"] != expected_fingerprint
            or signature["authorization"] != "HOLD"
            or signature["accessDecision"] != "DENY"):
        raise BoundaryInputError("PP_KEY_BINDING_INVALID")
    return {
        "schema": SCHEMA,
        "reference": "PP-RECOVERY-002",
        "proposalSha256": hashlib.sha256(proposal_bytes).hexdigest(),
        "manifestSha256": signature["manifestSha256"],
        "publicKeySha256": expected_fingerprint,
        "candidateKeyBinding": "FINGERPRINT_MATCH_UNTRUSTED",
        "signatureMathematics": "VALID_UNTRUSTED_KEY",
        "issuerAuthentication": "NOT_ESTABLISHED",
        "keyTrust": "NOT_ESTABLISHED",
        "keyRevocation": "NOT_CHECKED",
        "independentVerification": "NOT_VERIFIED",
        "palacoOneHandoff": "BLOCKED",
        "authorization": "HOLD",
        "accessDecision": "DENY",
        "issuance": "NOT_AUTHORIZED",
        "deployment": "BLOCKED",
    }
