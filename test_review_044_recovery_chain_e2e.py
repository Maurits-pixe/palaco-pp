"""End-to-end synthetic PP recovery boundary, evidence and key-denial tests.

No real P.P. identities, registrations, phone numbers, trust anchors,
network calls or persistent credentials. Ephemeral keys are TEST ONLY.
Mathematical cryptography never means issuer/owner authentication.
"""
from __future__ import annotations

import hashlib
import unittest

from review_044_release_boundary_snapshot import (
    BoundaryInputError, review_boundary_snapshot,
)
from review_044_boundary_reconciliation import reconcile_boundary_snapshots
from review_044_evidence_manifest import (
    build_evidence_manifest, validate_evidence_manifest,
)
from review_044_proposed_key_binding import inspect_proposed_key_binding
from review_044_revocation_signature_inspection import (
    CONTEXT as REVOCATION_CONTEXT, inspect_revocation_signature,
)
from review_044_detached_signature_inspection import (
    CONTEXT as MANIFEST_CONTEXT,
)
from test_review_044_release_boundary_snapshot import encode, valid_report
from test_review_044_trust_anchor_preflight import proposal
from test_review_044_unsigned_revocation_notice import notice

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None


def expect_denied(test: unittest.TestCase, outcome: dict) -> None:
    test.assertEqual("PP-RECOVERY-002", outcome["reference"])
    test.assertEqual("HOLD", outcome["authorization"])
    test.assertEqual("DENY", outcome["accessDecision"])
    test.assertEqual("NOT_AUTHORIZED", outcome["issuance"])
    test.assertEqual("BLOCKED", outcome["deployment"])


@unittest.skipIf(Ed25519PrivateKey is None, "cryptography unavailable")
class RecoveryChainEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.other_key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.report = encode(valid_report())
        self.boundary = review_boundary_snapshot(self.report)
        self.snapshot = encode(self.boundary)
        self.reconciliation = reconcile_boundary_snapshots(
            self.snapshot, self.snapshot
        )
        self.manifest = encode(
            build_evidence_manifest(((self.snapshot, self.snapshot),))
        )
        candidate = proposal()
        candidate["publicKeySha256"] = hashlib.sha256(self.public).hexdigest()
        self.proposal = encode(candidate)
        claimed = notice()
        claimed["publicKeySha256"] = candidate["publicKeySha256"]
        self.notice = encode(claimed)
        self.manifest_signature = self.key.sign(
            MANIFEST_CONTEXT + self.manifest
        )
        self.revocation_signature = self.key.sign(
            REVOCATION_CONTEXT + self.notice
        )

    def test_complete_synthetic_chain_never_grants_authority(self):
        inventory = validate_evidence_manifest(self.manifest)
        evidence = inspect_proposed_key_binding(
            self.proposal, self.manifest, self.public, self.manifest_signature
        )
        revocation = inspect_revocation_signature(
            self.proposal, self.notice, self.public, self.revocation_signature
        )
        for outcome in (
            self.boundary, self.reconciliation, inventory, evidence, revocation
        ):
            with self.subTest(schema=outcome["schema"]):
                expect_denied(self, outcome)
        self.assertEqual("MATCH_UNTRUSTED", self.reconciliation["comparison"])
        self.assertEqual("VALID_UNTRUSTED_KEY", evidence["signatureMathematics"])
        self.assertEqual("VALID_UNTRUSTED_KEY", revocation["signatureMathematics"])
        self.assertEqual("NOT_VERIFIED", revocation["trustedRevocation"])
        self.assertEqual("NOT_ESTABLISHED", evidence["keyTrust"])
        self.assertFalse(revocation["registryModified"])

    def test_false_readiness_cannot_enter_evidence_chain(self):
        modified = valid_report()
        modified["reviewerAuthority"] = "ESTABLISHED"
        with self.assertRaises(BoundaryInputError):
            review_boundary_snapshot(encode(modified))

    def test_manifest_change_invalidates_bound_signature(self):
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                self.proposal, self.manifest + b" ",
                self.public, self.manifest_signature
            )

    def test_cross_protocol_signature_reuse_fails(self):
        with self.assertRaises(BoundaryInputError):
            inspect_revocation_signature(
                self.proposal, self.notice, self.public,
                self.key.sign(MANIFEST_CONTEXT + self.notice),
            )
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                self.proposal, self.manifest, self.public,
                self.key.sign(REVOCATION_CONTEXT + self.manifest),
            )

    def test_other_signer_cannot_claim_candidate_binding(self):
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                self.proposal, self.manifest, self.public,
                self.other_key.sign(MANIFEST_CONTEXT + self.manifest),
            )
        with self.assertRaises(BoundaryInputError):
            inspect_revocation_signature(
                self.proposal, self.notice, self.public,
                self.other_key.sign(REVOCATION_CONTEXT + self.notice),
            )

    def test_valid_self_signed_claim_cannot_override_hold(self):
        evidence = inspect_proposed_key_binding(
            self.proposal, self.manifest, self.public, self.manifest_signature
        )
        revocation = inspect_revocation_signature(
            self.proposal, self.notice, self.public, self.revocation_signature
        )
        self.assertEqual("NOT_ESTABLISHED", evidence["issuerAuthentication"])
        self.assertEqual("NOT_ESTABLISHED", revocation["issuerAuthentication"])
        self.assertEqual("NOT_VERIFIED", revocation["independentVerification"])
        self.assertEqual("BLOCKED", evidence["palacoOneHandoff"])
        self.assertEqual("BLOCKED", revocation["palacoOneHandoff"])
        expect_denied(self, evidence)
        expect_denied(self, revocation)


if __name__ == "__main__":
    unittest.main()
