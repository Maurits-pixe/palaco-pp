"""Synthetic tests for mathematical Ed25519 inspection, no trusted keys."""
import json
import unittest

from review_044_detached_signature_inspection import (
    CONTEXT, inspect_detached_signature,
)
from review_044_evidence_manifest import build_evidence_manifest
from review_044_release_boundary_snapshot import BoundaryInputError
from test_review_044_boundary_reconciliation import snapshot
from test_review_044_release_boundary_snapshot import encode

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    Ed25519PrivateKey = None


def synthetic_manifest():
    return encode(build_evidence_manifest(((snapshot(), snapshot()),)))


class DetachedSignatureTests(unittest.TestCase):
    def test_invalid_input_types_and_lengths(self):
        raw = synthetic_manifest()
        for item in (
            (raw, b"x", b"y" * 64),
            (raw, b"x" * 32, b"y"),
            ("text", b"x" * 32, b"y" * 64),
            (raw, None, b"y" * 64),
            (b"", b"x" * 32, b"y" * 64),
        ):
            with self.subTest(item=tuple(type(v).__name__ for v in item)):
                with self.assertRaises(BoundaryInputError):
                    inspect_detached_signature(*item)

    def test_invalid_manifest_fails_even_before_signature(self):
        with self.assertRaises(BoundaryInputError):
            inspect_detached_signature(b"{}", b"x" * 32, b"y" * 64)

    @unittest.skipIf(Ed25519PrivateKey is None, "optional cryptography dependency absent")
    def test_signature_valid_with_untrusted_ephemeral_key_is_still_denied(self):
        from cryptography.hazmat.primitives import serialization
        key = Ed25519PrivateKey.generate()
        public = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        raw = synthetic_manifest()
        signed = key.sign(CONTEXT + raw)
        report = inspect_detached_signature(raw, public, signed)
        self.assertEqual("VALID_UNTRUSTED_KEY", report["signatureMathematics"])
        self.assertEqual("NOT_ESTABLISHED", report["keyTrust"])
        self.assertEqual("NOT_VERIFIED", report["independentVerification"])
        self.assertEqual("HOLD", report["authorization"])
        self.assertEqual("DENY", report["accessDecision"])
        self.assertEqual("NOT_AUTHORIZED", report["issuance"])

    @unittest.skipIf(Ed25519PrivateKey is None, "optional cryptography dependency absent")
    def test_reject_wrong_domain_and_tampered_signature(self):
        from cryptography.hazmat.primitives import serialization
        key = Ed25519PrivateKey.generate()
        public = key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        raw = synthetic_manifest()
        for signature in (key.sign(raw), key.sign(b"wrong-context" + raw)):
            with self.subTest(signature=signature[:4].hex()):
                with self.assertRaises(BoundaryInputError):
                    inspect_detached_signature(raw, public, signature)

    @unittest.skipIf(Ed25519PrivateKey is None, "optional cryptography dependency absent")
    def test_other_key_cannot_verify_signature(self):
        from cryptography.hazmat.primitives import serialization
        key1 = Ed25519PrivateKey.generate()
        key2 = Ed25519PrivateKey.generate()
        other_public = key2.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        raw = synthetic_manifest()
        with self.assertRaises(BoundaryInputError):
            inspect_detached_signature(raw, other_public, key1.sign(CONTEXT + raw))


if __name__ == "__main__":
    unittest.main()
