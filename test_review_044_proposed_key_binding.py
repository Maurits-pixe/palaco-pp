"""Synthetic checks for proposed-key binding; never enrolls a key."""
import hashlib
import unittest

from review_044_detached_signature_inspection import CONTEXT
from review_044_proposed_key_binding import inspect_proposed_key_binding
from review_044_release_boundary_snapshot import BoundaryInputError
from test_review_044_detached_signature_inspection import synthetic_manifest
from test_review_044_trust_anchor_preflight import encode, proposal

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None


def candidate(key_bytes: bytes) -> bytes:
    item = proposal()
    item["publicKeySha256"] = hashlib.sha256(key_bytes).hexdigest()
    return encode(item)


@unittest.skipIf(Ed25519PrivateKey is None, "cryptography unavailable")
class ProposedKeyBindingTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.manifest = synthetic_manifest()
        self.signed = self.key.sign(CONTEXT + self.manifest)

    def test_valid_mathematical_binding_still_denied(self):
        result = inspect_proposed_key_binding(
            candidate(self.public), self.manifest, self.public, self.signed,
        )
        self.assertEqual("FINGERPRINT_MATCH_UNTRUSTED", result["candidateKeyBinding"])
        self.assertEqual("NOT_ESTABLISHED", result["keyTrust"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", result["issuance"])
        self.assertEqual("BLOCKED", result["deployment"])

    def test_reject_other_public_key(self):
        alternate = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                candidate(alternate), self.manifest, self.public, self.signed,
            )

    def test_reject_wrong_signature(self):
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                candidate(self.public), self.manifest, self.public,
                self.key.sign(self.manifest),
            )

    def test_reject_proposal_promoted_to_approved(self):
        item = proposal()
        item["publicKeySha256"] = hashlib.sha256(self.public).hexdigest()
        item["proposedState"] = "APPROVED"
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                encode(item), self.manifest, self.public, self.signed,
            )

    def test_reject_modified_manifest(self):
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                candidate(self.public), self.manifest + b" ",
                self.public, self.signed,
            )

    def test_reject_untyped_key(self):
        with self.assertRaises(BoundaryInputError):
            inspect_proposed_key_binding(
                candidate(self.public), self.manifest, "not-bytes", self.signed,
            )


if __name__ == "__main__":
    unittest.main()
