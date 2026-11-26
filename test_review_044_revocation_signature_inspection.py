"""Synthetic tests of untrusted, signed revocation observations."""
import hashlib
import unittest

from review_044_release_boundary_snapshot import BoundaryInputError
from review_044_revocation_signature_inspection import (
    CONTEXT, inspect_revocation_signature,
)
from test_review_044_trust_anchor_preflight import encode, proposal
from test_review_044_unsigned_revocation_notice import notice

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None


@unittest.skipIf(Ed25519PrivateKey is None, "cryptography unavailable")
class RevocationSignatureTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        candidate = proposal()
        candidate["publicKeySha256"] = hashlib.sha256(self.public).hexdigest()
        self.proposal_bytes = encode(candidate)
        claimed = notice()
        claimed["publicKeySha256"] = candidate["publicKeySha256"]
        self.notice_bytes = encode(claimed)
        self.signature = self.key.sign(CONTEXT + self.notice_bytes)

    def inspect(self, *, p=None, n=None, k=None, s=None):
        return inspect_revocation_signature(
            self.proposal_bytes if p is None else p,
            self.notice_bytes if n is None else n,
            self.public if k is None else k,
            self.signature if s is None else s,
        )

    def test_mathematically_valid_signature_stays_blocked(self):
        result = self.inspect()
        self.assertEqual("VALID_UNTRUSTED_KEY", result["signatureMathematics"])
        self.assertEqual("NOT_ESTABLISHED", result["issuerAuthentication"])
        self.assertEqual("NOT_VERIFIED", result["trustedRevocation"])
        self.assertFalse(result["registryModified"])
        self.assertEqual("HOLD", result["authorization"])
        self.assertEqual("DENY", result["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", result["issuance"])

    def test_reject_signature_without_domain_separator(self):
        with self.assertRaises(BoundaryInputError):
            self.inspect(s=self.key.sign(self.notice_bytes))

    def test_reject_signature_for_other_domain(self):
        with self.assertRaises(BoundaryInputError):
            self.inspect(s=self.key.sign(b"OTHER-DOMAIN\x00" + self.notice_bytes))

    def test_reject_changed_notice_after_signing(self):
        changed = notice()
        changed["keyId"] = "other-key-0001"
        with self.assertRaises(BoundaryInputError):
            self.inspect(n=encode(changed))

    def test_reject_unrelated_candidate_key(self):
        another = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        with self.assertRaises(BoundaryInputError):
            self.inspect(k=another)

    def test_reject_wrong_signature_bytes(self):
        with self.assertRaises(BoundaryInputError):
            self.inspect(s=b"\x00" * 64)

    def test_reject_bad_types(self):
        for bad in ("not bytes", b"", b"\x00" * 20):
            with self.subTest(data_type=type(bad).__name__):
                with self.assertRaises(BoundaryInputError):
                    self.inspect(s=bad)


if __name__ == "__main__":
    unittest.main()
