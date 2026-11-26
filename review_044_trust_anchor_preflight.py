"""Offline trust-anchor proposal preflight for PP-RECOVERY-002.

Untrusted proposals are inventoried for independent human review only.
This module NEVER enrolls a trusted key, authenticates an issuer/reviewer,
accepts a receipt, modifies a registry or grants access.
"""
from __future__ import annotations

import hashlib
import re

from review_044_release_boundary_snapshot import BoundaryInputError, _parse_json

MAX_PROPOSAL_BYTES = 16 * 1024
SCHEMA = "palaco.pp.recovery-002-trust-anchor-proposal.v1"
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
ISSUER_ID = re.compile(r"[a-z][a-z0-9.-]{2,63}\Z", re.ASCII)
KEY_ID = re.compile(r"[A-Za-z0-9_-]{8,64}\Z", re.ASCII)
PURPOSE = "RECOVERY_EVIDENCE_SIGNATURE_INSPECTION_ONLY"
ALGORITHM = "Ed25519"
FIELDS = frozenset({
    "schema", "reference", "issuerId", "keyId", "publicKeySha256",
    "algorithm", "purpose", "proposedState",
})
DENIALS = {
    "issuerAuthentication": "NOT_ESTABLISHED",
    "trustAnchorAdmission": "NOT_AUTHORIZED",
    "independentReview": "NOT_COMPLETED",
    "reviewerAuthority": "NOT_ESTABLISHED",
    "keyRevocation": "NOT_CHECKED",
    "palacoOneHandoff": "BLOCKED",
    "authorization": "HOLD",
    "accessDecision": "DENY",
    "issuance": "NOT_AUTHORIZED",
    "deployment": "BLOCKED",
}


def inspect_trust_anchor_proposal(raw: bytes) -> dict:
    """Validate proposal shape, not issuer identity or key ownership.

    A public key *fingerprint* cannot prove control or provenance. No key
    bytes are accepted. Even a structurally valid proposal is never trusted.
    """
    if type(raw) is not bytes or not (1 <= len(raw) <= MAX_PROPOSAL_BYTES):
        raise BoundaryInputError("PP_TRUST_PROPOSAL_INVALID")
    try:
        proposal = _parse_json(raw, max_bytes=MAX_PROPOSAL_BYTES)
        if (set(proposal) != FIELDS
                or proposal.get("schema") != SCHEMA
                or proposal.get("reference") != "PP-RECOVERY-002"
                or proposal.get("algorithm") != ALGORITHM
                or proposal.get("purpose") != PURPOSE
                or proposal.get("proposedState") != "PENDING_INDEPENDENT_REVIEW"
                or type(proposal.get("issuerId")) is not str
                or ISSUER_ID.fullmatch(proposal["issuerId"]) is None
                or type(proposal.get("keyId")) is not str
                or KEY_ID.fullmatch(proposal["keyId"]) is None
                or type(proposal.get("publicKeySha256")) is not str
                or HEX_SHA256.fullmatch(proposal["publicKeySha256"]) is None):
            raise BoundaryInputError("PP_TRUST_PROPOSAL_INVALID")
    except (ValueError, TypeError, KeyError) as exc:
        raise BoundaryInputError("PP_TRUST_PROPOSAL_INVALID") from exc
    return {
        "schema": "palaco.pp.recovery-002-trust-anchor-preflight.v1",
        "reference": "PP-RECOVERY-002",
        "proposalSha256": hashlib.sha256(raw).hexdigest(),
        "algorithm": ALGORITHM,
        "purpose": PURPOSE,
        "structuralInspection": "VALID_UNTRUSTED_PROPOSAL",
        "trustedIssuerCount": 0,
        "allowedSigningKeys": 0,
        "trustAnchorImported": False,
        "registryModified": False,
        **DENIALS,
    }
